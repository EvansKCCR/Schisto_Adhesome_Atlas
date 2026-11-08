"""Algorithm fixtures and interactive clustering regression checks; no remote calls."""
from bootstrap import ATLAS_ROOT
import sys
import networkx as nx
from topological_clustering import cluster_network, mcl, mcode, graph_digest


def main():
    graph = nx.relabel_nodes(nx.barbell_graph(5, 1), lambda node: f'protein_{node:02d}')
    graph.add_node('isolate')
    original_edges = set(graph.edges)
    expected = {frozenset(f'protein_{node:02d}' for node in range(start, start + 5)) for start in [0, 6]}
    groups, weights = mcode(graph)
    assert set(groups) == expected
    assert weights['isolate'] == 0 and weights['protein_00'] == 4
    members, summary, diagnostics = cluster_network(graph, 'MCODE')
    assert len(summary) == 2 and summary.density.eq(1).all() and summary.density_size_score.eq(5).all()
    assert members.set_index('identifier').loc['isolate', 'cluster'] == 'Unclustered'
    assert diagnostics['assigned_nodes'] == 10
    flow_graph = nx.relabel_nodes(nx.barbell_graph(5, 0), lambda node: f'protein_{node:02d}')
    flow_graph.add_node('isolate')
    flow_expected = {frozenset(f'protein_{node:02d}' for node in range(start, start + 5)) for start in [0, 5]}
    for method in ['MCL', 'Greedy modularity']:
        members, summary, diagnostics = cluster_network(flow_graph, method)
        assert len(summary) == 3 and summary.nodes.sum() == len(flow_graph), method
        assert members.cluster_count.eq(1).all() and diagnostics['assigned_nodes'] == len(flow_graph), method
        detected = {frozenset(members.loc[members.cluster.eq(cluster), 'identifier']) for cluster in summary.cluster}
        assert flow_expected <= detected, method
    members, summary, diagnostics = cluster_network(graph, 'MCL')
    assert len(summary) == 3 and members.set_index('identifier').loc['protein_05', 'cluster_count'] == 2
    assert set(graph.edges) == original_edges  # analysis cannot change source associations
    reverse = nx.Graph()
    reverse.add_nodes_from(reversed(list(graph)))
    reverse.add_edges_from(reversed(list(graph.edges)))
    for method in ['MCODE', 'MCL', 'Greedy modularity']:
        a, _, _ = cluster_network(graph, method)
        b, _, _ = cluster_network(reverse, method)
        assert a.equals(b), method
    assert graph_digest(graph) == graph_digest(reverse)
    reverse.add_edge('isolate', 'isolate')
    assert graph_digest(graph) == graph_digest(reverse)
    # MCODE excludes chains; optional fluff can capture overlapping peripheral nodes.
    assert not mcode(nx.path_graph(6))[0]
    overlap = nx.Graph([('a', 'b'), ('b', 'c'), ('c', 'a'), ('d', 'e'), ('e', 'f'), ('f', 'd'), ('a', 'x'), ('d', 'x')])
    members, _, diagnostics = cluster_network(overlap, 'MCODE', fluff=True, haircut=False)
    assert members.set_index('identifier').loc['x', 'cluster_count'] == 2
    assert diagnostics['overlapping_nodes'] == 1 and 'unweighted_modularity' not in diagnostics
    groups, _ = mcode(overlap, fluff=True, haircut=True)
    assert all('x' not in group for group in groups)
    for method in ['MCODE', 'MCL', 'Greedy modularity']:
        members, summary, diagnostics = cluster_network(nx.empty_graph(3), method)
        assert len(members) == 3
        assert len(summary) == (0 if method == 'MCODE' else 3)
        members, summary, _ = cluster_network(nx.Graph(), method)
        assert members.empty and summary.empty
    # Never publish assignments from an unconverged flow matrix.
    groups, diagnostics = mcl(graph, max_iterations=1)
    assert not groups and not diagnostics['converged']
    for graph, method, settings in [(nx.DiGraph([(1, 2)]), 'MCODE', {}),
                                    (nx.empty_graph(401), 'MCL', {}),
                                    (nx.path_graph(3), 'MCL', {'inflation': 1}),
                                    (nx.path_graph(3), 'MCODE', {'node_score_cutoff': -1})]:
        try:
            cluster_network(graph, method, **settings)
            raise AssertionError('Invalid graph or settings accepted')
        except ValueError:
            pass
    print('PASS dense-complex recovery, MCL partition/convergence, overlaps, isolates, deterministic IDs and input preservation', flush=True)
    if '--app' not in sys.argv:
        return
    from streamlit.testing.v1 import AppTest
    source = '''
import networkx as nx
import pandas as pd
import streamlit as st
from topological_clustering import clustering_panel
variant = st.radio('Test network', ['Dense modules', 'Isolates'])
graph = nx.relabel_nodes(nx.barbell_graph(5, 1), str) if variant == 'Dense modules' else nx.Graph()
graph.add_node('isolate')
nodes = pd.DataFrame([{'identifier': node, 'node': node, 'Family': 'Adaptor', 'layer': 'Membrane-proximal', 'candidate_annotation': 'Candidate adaptor'} for node in graph])
clustering_panel(graph, nodes, 'fixture', 'Test adhesion network')
'''
    app = AppTest.from_string(source, default_timeout=90).run()
    next(widget for widget in app.checkbox if widget.label == 'Explore clustering algorithms').set_value(True).run()
    assert not app.exception, [item.message for item in app.exception]
    method = next(widget for widget in app.selectbox if widget.label == 'Clustering algorithm')
    method.set_value('MCODE').run()
    assert not app.exception, [item.message for item in app.exception]
    assert any('MCODE clusters' in getattr(item.proto, 'srcdoc', '') for item in app.get('iframe'))
    assert any('Download cluster memberships' in str(item.proto) for item in app.get('download_button'))
    next(widget for widget in app.multiselect if widget.label == 'Display clusters').set_value(['C001']).run()
    next(widget for widget in app.radio if widget.label == 'Cluster visualization').set_value('Cluster islands').run()
    next(widget for widget in app.checkbox if widget.label == 'Compare cluster overlap with greedy modularity').set_value(True).run()
    assert not app.exception, [item.message for item in app.exception]
    assert any('Download cluster overlap matrix' in str(item.proto) for item in app.get('download_button'))
    next(widget for widget in app.slider if widget.label == 'MCODE node-score cutoff').set_value(.8).run()
    assert not app.exception
    assert next(widget for widget in app.multiselect if widget.label == 'Display clusters').value == []
    next(widget for widget in app.selectbox if widget.label == 'Clustering algorithm').set_value('MCL').run()
    assert not app.exception, [item.message for item in app.exception]
    assert any('MCL clusters' in getattr(item.proto, 'srcdoc', '') for item in app.get('iframe'))
    next(widget for widget in app.checkbox if widget.label == 'Hide unclustered nodes').set_value(True).run()
    next(widget for widget in app.radio if widget.label == 'Test network').set_value('Isolates').run()
    assert not app.exception
    next(widget for widget in app.selectbox if widget.label == 'Clustering algorithm').set_value('MCODE').run()
    next(widget for widget in app.checkbox if widget.label == 'Hide unclustered nodes').set_value(True).run()
    assert not app.exception
    assert any('No nodes match' in item.value for item in app.info)
    print('PASS clustering controls, SVG rendering, parameter-change reset, overlap matrix and empty selection handling', flush=True)


if __name__ == '__main__':
    main()
