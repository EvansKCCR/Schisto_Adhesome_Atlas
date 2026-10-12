"""Reproducible unweighted community and dense-complex exploration."""
import hashlib
import json
from datetime import datetime, timezone

import networkx as nx
import numpy as np
import pandas as pd

METHODS = ['Greedy modularity', 'MCODE', 'MCL']
REFERENCES = {
    'MCODE': 'https://doi.org/10.1186/1471-2105-4-2',
    'MCL': 'https://doi.org/10.1137/040608635',
    'Greedy modularity': 'https://doi.org/10.1103/PhysRevE.70.066111',
}
VERSION = '1.0'


def clean_graph(graph):
    if graph.is_directed():
        raise ValueError('Topological clustering requires an undirected graph.')
    result = nx.Graph()
    result.add_nodes_from(sorted(graph, key=str))
    result.add_edges_from(sorted((tuple(sorted((a, b), key=str)) for a, b in graph.edges if a != b), key=str))
    return result


def graph_payload(graph):
    return {'nodes': sorted(graph, key=str),
            'edges': sorted((sorted((a, b), key=str) for a, b in graph.edges if a != b), key=str)}


def graph_digest(graph):
    return hashlib.sha256(json.dumps(graph_payload(graph), sort_keys=True).encode()).hexdigest()


def mcode(graph, node_score_cutoff=.2, degree_cutoff=2, haircut=True, fluff=False, fluff_density=.1):
    """Bader–Hogue core-density weighting, seed growth and optional refinement.

    Seed-grown clusters are disjoint. Fluff adds one shell without marking those
    nodes as visited, so final memberships may overlap. Complexes need a 2-core.
    """
    graph = clean_graph(graph)
    if not 0 <= node_score_cutoff <= 1 or not 0 <= fluff_density <= 1 or degree_cutoff < 1:
        raise ValueError('Invalid MCODE thresholds.')
    weights = {}
    neighborhoods = {}
    for node in graph:
        local = graph.subgraph({node} | set(graph[node]))
        neighborhoods[node] = nx.density(local)
        if graph.degree(node) < degree_cutoff:
            weights[node] = 0.
            continue
        cores = nx.core_number(local)
        highest = max(cores.values(), default=0)
        core = local.subgraph([v for v, value in cores.items() if value == highest])
        weights[node] = highest * nx.density(core)
    visited = set()
    clusters = []
    for seed in sorted(graph, key=lambda v: (-weights[v], str(v))):
        if seed in visited or weights[seed] <= 0:
            continue
        cutoff = (1 - node_score_cutoff) * weights[seed]
        pending = [seed]
        members = set()
        while pending:
            node = pending.pop()
            if node in visited or weights[node] < cutoff or weights[node] <= 0:
                continue
            visited.add(node)
            members.add(node)
            pending.extend(sorted(set(graph[node]) - visited, key=str))
        local = graph.subgraph(members)
        if not members or not nx.k_core(local, k=2).number_of_nodes():
            continue
        if fluff:
            boundary = set().union(*(set(graph[v]) for v in members)) - members - visited
            members |= {v for v in boundary if neighborhoods[v] >= fluff_density}
        if haircut:
            members = set(nx.k_core(graph.subgraph(members), k=2))
        if members:
            clusters.append(frozenset(members))
    clusters = sorted(set(clusters), key=lambda group: (-len(group) * nx.density(graph.subgraph(group)), sorted(map(str, group))))
    return clusters, weights


def mcl(graph, inflation=2., max_iterations=200, tolerance=1e-6, pruning=1e-7):
    """Column-stochastic MCL with unit loops, expansion 2 and inflation.

    Dense NumPy implementation is bounded to 400 vertices. Nonzero diagonal
    attractor rows define memberships; tied boundary nodes may occur in multiple
    groups. Identical groups are merged; isolates remain singleton communities.
    No assignments are returned for an unconverged run.
    """
    graph = clean_graph(graph)
    if len(graph) > 400:
        raise ValueError('MCL supports up to 400 displayed nodes. Filter to a family or neighborhood first.')
    if not 1 < inflation <= 10 or max_iterations < 1 or tolerance <= 0 or not 0 < pruning < tolerance:
        raise ValueError('Invalid MCL settings.')
    if not graph:
        return [], {'converged': True, 'iterations': 0, 'residual': 0.}
    order = list(graph)
    matrix = nx.to_numpy_array(graph, nodelist=order, weight=None, dtype=float)
    np.fill_diagonal(matrix, 1.)
    matrix /= matrix.sum(axis=0)
    converged = False
    for iteration in range(1, max_iterations + 1):
        previous = matrix
        matrix = np.power(matrix @ matrix, inflation)
        matrix /= matrix.sum(axis=0)
        # Preserve each column's maximum so pruning cannot empty a column.
        maxima = np.argmax(matrix, axis=0)
        keep = matrix[maxima, np.arange(len(order))].copy()
        matrix[matrix < pruning] = 0.
        matrix[maxima, np.arange(len(order))] = keep
        matrix /= matrix.sum(axis=0)
        residual = float(np.max(np.abs(matrix - previous)))
        if residual <= tolerance:
            converged = True
            break
    diagnostics = {'converged': converged, 'iterations': iteration, 'residual': residual,
                   'expansion': 2, 'loop_weight': 1., 'tolerance': tolerance, 'pruning': pruning,
                   'extraction': 'Diagonal attractor rows and memberships > 1e-5; identical groups merged'}
    if not converged:
        return [], diagnostics
    attractors = np.flatnonzero(np.diag(matrix) > 1e-5)
    groups = sorted({frozenset(order[i] for i in np.flatnonzero(matrix[attractor] > 1e-5)) for attractor in attractors}, key=lambda group: sorted(map(str, group)))
    return groups, diagnostics


def cluster_network(graph, method, **parameters):
    graph = clean_graph(graph)
    diagnostics = {}
    weights = {}
    if method == 'MCODE':
        groups, weights = mcode(graph, **parameters)
    elif method == 'MCL':
        groups, diagnostics = mcl(graph, **parameters)
    elif method == 'Greedy modularity':
        resolution = parameters.get('resolution', 1.)
        if resolution <= 0:
            raise ValueError('Resolution must be positive.')
        groups = list(nx.community.greedy_modularity_communities(graph, weight=None, resolution=resolution)) if graph.number_of_edges() else [{node} for node in graph]
    else:
        raise ValueError('Unknown clustering method.')
    groups = sorted((frozenset(group) for group in groups), key=lambda group: (
        -len(group) * nx.density(graph.subgraph(group)) if method == 'MCODE' else -len(group), sorted(map(str, group))))
    memberships = {node: [] for node in graph}
    rows = []
    for index, group in enumerate(groups, 1):
        cluster = f'C{index:03d}'
        local = graph.subgraph(group)
        boundary = sum(1 for a, b in graph.edges if (a in group) != (b in group))
        rows.append({'cluster': cluster, 'nodes': len(group), 'internal_edges': local.number_of_edges(),
                     'density': nx.density(local), 'density_size_score': len(group) * nx.density(local),
                     'boundary_edges': boundary, 'max_k_core': max(nx.core_number(local).values(), default=0)})
        for node in group:
            memberships[node].append(cluster)
    members = pd.DataFrame([{'identifier': node, 'cluster': ' | '.join(memberships[node]) or 'Unclustered',
                             'cluster_count': len(memberships[node]), 'mcode_vertex_weight': weights.get(node, np.nan)} for node in graph],
                           columns=['identifier', 'cluster', 'cluster_count', 'mcode_vertex_weight'])
    summary = pd.DataFrame(rows, columns=['cluster', 'nodes', 'internal_edges', 'density', 'density_size_score', 'boundary_edges', 'max_k_core'])
    partition = len(groups) > 0 and all(len(value) == 1 for value in memberships.values())
    if partition and graph.number_of_edges():
        diagnostics['unweighted_modularity'] = nx.community.modularity(graph, groups, weight=None)
    diagnostics['assigned_nodes'] = sum(bool(value) for value in memberships.values())
    diagnostics['overlapping_nodes'] = sum(len(value) > 1 for value in memberships.values())
    return members, summary, diagnostics


def clustering_panel(graph, nodes, key, title='Network'):
    """Shared explorer for reconstructed, orthogroup and imported STRING graphs."""
    import streamlit as st
    import plotly.express as px
    from figure_exports import plotly_chart
    from vector_network import vector_network_html

    st.markdown('#### Topological clustering algorithms')
    if not st.checkbox('Explore clustering algorithms', key=key + '_enabled'):
        st.caption('Compare MCODE dense complexes, MCL random-walk communities and greedy modularity on the current filtered network.')
        return
    graph = clean_graph(graph)
    if not graph:
        st.info('No nodes remain to cluster. Broaden the network filters.')
        return
    key += '_' + graph_digest(graph)[:12]
    method = st.selectbox('Clustering algorithm', METHODS, key=key + '_method')
    parameters = {}
    if method == 'MCODE':
        a, b = st.columns(2)
        parameters['node_score_cutoff'] = a.slider('MCODE node-score cutoff', 0., 1., .2, .05, key=key + '_score')
        parameters['degree_cutoff'] = b.slider('MCODE minimum node degree', 1, 10, 2, key=key + '_degree')
        parameters['haircut'] = a.checkbox('MCODE haircut (retain 2-core)', value=True, key=key + '_haircut')
        parameters['fluff'] = b.checkbox('MCODE fluff (one-shell expansion)', value=False, key=key + '_fluff')
        if parameters['fluff']:
            parameters['fluff_density'] = st.slider('MCODE fluff neighborhood density', 0., 1., .1, .05, key=key + '_fluff_density')
        st.caption('Vertex weight = highest neighborhood k-core × its density. Growth retains weights ≥ (1 − cutoff) × seed weight. A 2-core is required; fluff may produce overlapping memberships. Larger cutoffs permit broader seed growth.')
    elif method == 'MCL':
        a, b = st.columns(2)
        parameters['inflation'] = a.slider('MCL inflation (granularity)', 1.2, 5., 2., .1, key=key + '_inflation')
        parameters['max_iterations'] = b.slider('MCL iteration limit', 50, 400, 200, 50, key=key + '_iterations')
        st.caption('Column-normalized adjacency + unit self-loops; expansion M² alternates with inflation and normalization. Higher inflation favors finer communities. Numerical convergence and iteration counts are reported.')
    else:
        parameters['resolution'] = st.slider('Modularity resolution', .2, 3., 1., .1, key=key + '_resolution')
        st.caption('Greedy modularity partitions the whole graph. Higher resolution favors smaller communities.')
    if len(graph) > (400 if method == 'MCL' else 1200):
        st.info(f'{method} is available for up to {400 if method == "MCL" else 1200} displayed nodes. Use the network family, species or neighborhood filters first.')
        return

    @st.cache_data(show_spinner=False, max_entries=32)
    def calculate(payload, algorithm, settings):
        current = nx.Graph()
        current.add_nodes_from(payload['nodes'])
        current.add_edges_from(payload['edges'])
        return cluster_network(current, algorithm, **settings)

    with st.spinner('Computing topological clusters…'):
        memberships, summary, diagnostics = calculate(graph_payload(graph), method, parameters)
    # Parameter changes may change cluster IDs/counts; never carry stale selections.
    key += '_' + hashlib.sha256(json.dumps([method, parameters], sort_keys=True).encode()).hexdigest()[:10]
    st.caption('Clustering uses unweighted, undirected associations after the current network filters. Confidence scores select edges; they are not binding probabilities. Cluster membership is independent of catalogue family assignment.')
    st.markdown(f'[Method reference · {method}]({REFERENCES[method]})')
    provenance = {'implementation': 'Schisto-Adhesome Atlas topological_clustering', 'version': VERSION,
                  'method': method, 'parameters': parameters, 'diagnostics': diagnostics,
                  'graph_sha256': graph_digest(graph), 'nodes': len(graph), 'edges': graph.number_of_edges(),
                  'graph_type': 'unweighted undirected; self-loops removed', 'reference': REFERENCES[method],
                  'generated_utc': datetime.now(timezone.utc).isoformat()}
    st.download_button('Download clustering run · JSON', json.dumps(provenance, indent=2), 'clustering_run.json', 'application/json', key=key + '_run')
    with st.expander('Run diagnostics and reproducibility'):
        st.json(provenance)
        st.download_button('Download clustering input graph · JSON', json.dumps(graph_payload(graph), indent=2), 'clustering_graph.json', 'application/json', key=key + '_graph')
    if method == 'MCL':
        st.caption(f'MCL: {diagnostics["iterations"]} iterations · maximum matrix change {diagnostics["residual"]:.2g} · converged: {diagnostics["converged"]}')
        if not diagnostics['converged']:
            st.warning('MCL did not converge within the iteration limit. Increase the limit or filter the network; no cluster assignments are reported for this run.')
            return
    metadata = nodes.drop_duplicates('identifier').copy()
    metadata = metadata.drop(columns=['cluster', 'cluster_count', 'mcode_vertex_weight'], errors='ignore')
    members = memberships.merge(metadata, on='identifier', how='left', validate='one_to_one')
    a, b, c = st.columns(3)
    a.metric('Detected clusters', len(summary))
    b.metric('Assigned nodes', diagnostics['assigned_nodes'])
    c.metric('Unclustered nodes', len(graph) - diagnostics['assigned_nodes'])
    st.dataframe(summary, hide_index=True, width='stretch')
    a, b = st.columns(2)
    a.download_button('Download cluster summary · CSV', summary.to_csv(index=False), 'cluster_summary.csv', key=key + '_summary')
    b.download_button('Download cluster memberships · CSV', members.to_csv(index=False), 'cluster_memberships.csv', key=key + '_members')
    if summary.empty:
        st.info('No dense complexes meet these parameters. Try a broader score cutoff or switch to MCL for flow-based communities.')
    selected = st.multiselect('Display clusters', summary.cluster.tolist(), key=key + '_' + method + '_selection', help='No selection shows all clusters and any unclustered nodes.')
    keep = set(memberships.identifier) if not selected else {row.identifier for row in memberships.itertuples() if set(row.cluster.split(' | ')) & set(selected)}
    if st.checkbox('Hide unclustered nodes', value=False, key=key + '_' + method + '_unclustered'):
        keep &= set(memberships.loc[memberships.cluster_count.gt(0), 'identifier'])
    current = graph.subgraph(keep).copy()
    visible = members[members.identifier.isin(current)].copy()
    st.caption('Display controls select nodes from this run; clustering is calculated on the upstream filtered network, before cluster display selection.')
    st.dataframe(visible, hide_index=True, width='stretch')
    if not current:
        st.info('No nodes match the cluster display settings.')
        return
    layout_choices = ['Force-directed', 'Cluster islands', 'Circular'] if len(current) <= 400 else ['Cluster islands', 'Circular']
    layout = st.radio('Cluster visualization', layout_choices, horizontal=True, key=key + '_layout')
    if len(current) > 400:
        st.caption('Force-directed layout is available for up to 400 displayed nodes. Larger cluster islands use circular layouts within each island.')
    labels = memberships.set_index('identifier').cluster.to_dict()
    positions = nx.spring_layout(current, seed=42, weight=None, iterations=40) if layout == 'Force-directed' else nx.circular_layout(current)
    if layout == 'Cluster islands':
        # Overlapping nodes occupy a distinct labeled island; all original links survive.
        buckets = sorted({labels[node] for node in current})
        for index, label in enumerate(buckets):
            local = current.subgraph([node for node in current if labels[node] == label])
            center = np.array([3 * (index % 4), -3 * (index // 4)])
            local_positions = nx.spring_layout(local, seed=42, weight=None) if len(local) <= 400 else nx.circular_layout(local)
            for node, position in local_positions.items():
                positions[node] = center + .85 * position
    categories = sorted({labels[node] for node in current})
    colors = {label: '#8a9390' if label == 'Unclustered' else px.colors.qualitative.Alphabet[i % 26] for i, label in enumerate(categories)}
    vector_nodes = []
    for row in visible.fillna('').to_dict('records'):
        identifier = row['identifier']
        detail = {field: row[field] for field in ['identifier', 'cluster', 'sequence_id', 'Family', 'species', 'orthogroup', 'layer', 'candidate_annotation', 'degree', 'betweenness', 'closeness', 'mcode_vertex_weight'] if field in row}
        vector_nodes.append({'id': identifier, 'label': row.get('node') or identifier,
                             'annotation': row.get('candidate_annotation') or row.get('Family', ''),
                             'x': float(positions[identifier][0]), 'y': float(positions[identifier][1]),
                             'radius': 10 + graph.degree(identifier) ** .5 * 2,
                             'category': labels[identifier], 'color': colors[labels[identifier]], 'detail': detail})
    vector_edges = [{'source': a, 'target': b, 'color': '#a9b6ae' if labels[a] == labels[b] else '#d13d35'} for a, b in current.edges]
    st.iframe(vector_network_html(vector_nodes, vector_edges, title + ' · ' + method + ' clusters', label_mode='centered'), height=810)
    st.caption('Drag individual nodes; adjust label size and circle autofit in the vector viewer. Red edges connect different cluster labels. SVG download preserves the displayed layout; statistical charts support high-resolution PNG or SVG.')
    if len(summary):
        plotly_chart(px.scatter(summary, x='nodes', y='density', size=summary.internal_edges.clip(lower=1), color='cluster',
                                hover_data=['boundary_edges', 'max_k_core', 'density_size_score'],
                                title=method + ' · cluster size and density'), width='stretch', key=key + '_density')
    composition_choices = {label: field for label, field in [('Protein family', 'Family'), ('Adhesion layer', 'layer'), ('Species', 'species')]
                           if field in visible and visible[field].notna().any()}
    if composition_choices:
        default = 'Adhesion layer' if 'layer' in visible and visible.layer.fillna('Unresolved').ne('Unresolved').any() else next(iter(composition_choices))
        composition_label = st.selectbox('Cluster composition by', list(composition_choices), index=list(composition_choices).index(default), key=key + '_composition_field')
        composition_field = composition_choices[composition_label]
        long = visible.assign(cluster=visible.cluster.str.split(' | ', regex=False)).explode('cluster').reset_index(drop=True)
        composition = pd.crosstab(long.cluster, long[composition_field].fillna('Unassigned'))
        if not composition.empty:
            plotly_chart(px.imshow(composition, text_auto=True, aspect='auto', color_continuous_scale='YlGn',
                                    title='Cluster × ' + composition_label.lower() + ' composition'), width='stretch', key=key + '_composition')
            st.caption('Overlapping memberships contribute to each cluster’s composition; cluster counts need not sum to distinct nodes.')
    if st.checkbox('Compare cluster overlap with greedy modularity', key=key + '_compare'):
        baseline, _, _ = cluster_network(graph, 'Greedy modularity')
        sets = {cluster: set(memberships.loc[memberships.cluster.str.split(' | ', regex=False).map(lambda values: cluster in values), 'identifier']) for cluster in summary.cluster}
        other = {cluster: set(baseline.loc[baseline.cluster.eq(cluster), 'identifier']) for cluster in baseline.cluster.unique()}
        overlap = pd.DataFrame({label: {cluster: len(group & group2) / len(group | group2) for cluster, group in sets.items()} for label, group2 in other.items()})
        if not overlap.empty:
            plotly_chart(px.imshow(overlap, aspect='auto', color_continuous_scale='YlGn', zmin=0, zmax=1,
                                    labels={'x': 'Greedy community', 'y': method + ' cluster', 'color': 'Jaccard overlap'}, title='Membership overlap with greedy modularity'), width='stretch', key=key + '_overlap')
            st.download_button('Download cluster overlap matrix · CSV', overlap.to_csv(), 'cluster_overlap.csv', key=key + '_overlap_csv')
        st.caption('Jaccard overlap = shared nodes / union of nodes; agreement measures shared membership, not independent biological evidence.')
