"""No remote requests: imported graph coverage, exact metrics, batch isolation and UI sections."""
from bootstrap import ATLAS_ROOT
import io
import json
import sys
import zipfile
from unittest.mock import patch

import networkx as nx
import numpy as np
import pandas as pd

from string_analysis import (analyze_network,analysis_graph,all_clusterings,matrices,bundle,
    register_network,migrate_networks,network_id,NODE_METRICS)
from string_workbench import parse_network


def fixture(kind='functional',source='fixture.tsv',taxon=6183,code='Sman',scale=1):
    rows=[('A','B',.2),('B','C',.8),('C','A',.7),('C','D',.9),('D','E',.6),('E','F',.85),('F','D',.75)]
    raw='stringId_A\tstringId_B\tpreferredName_A\tpreferredName_B\tscore\n'+''.join(
        f'{taxon}.{a}\t{taxon}.{b}\t{a}\t{b}\t{score*scale}\n' for a,b,score in rows)
    raw+=f'{taxon}.B\t{taxon}.A\tB\tA\t{.1*scale}\n{taxon}.A\t{taxon}.A\tA\tA\t{scale}\n'
    edges=parse_network(raw,taxon,scale)
    plan=pd.DataFrame([{'sequence_id':code+'__'+letter,'query_id':letter,'query_family':'Adaptor','query_orthogroup':'OG_TEST'} for letter in 'ABCDEFG'])
    candidates=pd.DataFrame([{'sequence_id':code+'__'+letter,'species':'Schistosoma mansoni','family':'Adaptor',
        'reviewed_family':'Adaptor','orthogroup':'OG_TEST','candidate_annotation':'Candidate '+letter,
        'grade':'A','assignment_confidence':'strong','audit_classification':'Supported'} for letter in 'ABCDEFG'])
    state={'code':code,'taxon':taxon,'network_type':kind,'source':source,'raw':raw,'edges':edges,
        'resolved':{code+'__'+letter:f'{taxon}.{letter}' for letter in 'ABCDEFG'},'plan':plan,
        'provenance':{'source_file':source,'score_scale':scale}}
    return state,candidates


def stationary(graph,weighted=False):
    nodes=list(graph);n=len(nodes);matrix=nx.to_numpy_array(graph,nodelist=nodes,weight='confidence' if weighted else None)
    totals=matrix.sum(axis=1)
    for i in range(n):matrix[i]=matrix[i]/totals[i] if totals[i] else np.full(n,1/n)
    rank=np.linalg.solve(np.eye(n)-.85*matrix.T,np.full(n,.15/n))
    return dict(zip(nodes,rank))


def main():
    from string_analysis_view import prepare_nodes,_positions,SECTIONS
    state,candidates=fixture();original=state['edges'].copy(deep=True)
    nodes=prepare_nodes(state,candidates);result=analyze_network(nodes,state['edges']);graph=analysis_graph(result)
    expected=nx.barbell_graph(3,0);expected=nx.relabel_nodes(expected,dict(enumerate(['6183.'+c for c in 'ABCDEF'])));expected.add_node('6183.G')
    assert set(graph)==set(expected) and {frozenset(e) for e in graph.edges}=={frozenset(e) for e in expected.edges}
    assert result['summary']['nodes']==7 and result['summary']['edges']==7
    assert result['summary']['components']==2 and result['summary']['isolates']==1
    assert result['summary']['triangles']==2 and result['summary']['bridges']==1
    metrics=result['nodes'].set_index('identifier')
    for field,reference in [('betweenness',nx.betweenness_centrality(expected)),('closeness',nx.closeness_centrality(expected)),
        ('harmonic_centrality',nx.harmonic_centrality(expected)),('clustering_coefficient',nx.clustering(expected)),
        ('k_core',nx.core_number(expected)),('average_neighbor_degree',nx.average_neighbor_degree(expected))]:
        for node,value in reference.items():assert np.isclose(metrics.loc[node,field],value),field
    for node in graph:
        assert bool(metrics.loc[node,'articulation_point'])==(node in set(nx.articulation_points(graph)))
    weighted=nx.Graph(graph)
    for row in state['edges'].itertuples():weighted[row.node1_string_id][row.node2_string_id]['confidence']=row.combined_score
    for metric,use_confidence in [('pagerank',False),('confidence_pagerank',True)]:
        for node,value in stationary(weighted,use_confidence).items():assert np.isclose(metrics.loc[node,metric],value,atol=1e-8)
    assert pd.isna(metrics.loc['6183.G','component_eigenvector']) and metrics.loc['6183.G','closeness']==0
    assert np.isclose(result['summary']['global_efficiency'],nx.global_efficiency(graph))
    for row in result['components'].itertuples():
        local=graph.subgraph(metrics[metrics.component.eq(row.component)].index)
        assert row.diameter==nx.diameter(local) and row.radius==nx.radius(local)
    selected=['6183.A','6183.F','6183.G'];values=matrices(graph,selected,result['edges'])
    assert values['Hop distances'].loc['6183.A','6183.F']==3
    assert pd.isna(values['Hop distances'].loc['6183.A','6183.G'])
    assert values['Adjacency'].loc['6183.A','6183.F']==0
    assert len(values)==5 and np.allclose(values['Induced Laplacian'].sum(axis=1),0)
    assert pd.isna(values['Neighbor Jaccard'].loc['6183.G','6183.G'])
    reference=nx.edge_betweenness_centrality(graph)
    for row in result['edges'].itertuples():
        assert np.isclose(row.edge_betweenness,reference.get((row.node1_string_id,row.node2_string_id),reference.get((row.node2_string_id,row.node1_string_id))))
    clusters,comparison=all_clusterings(graph)
    assert set(clusters)=={'MCODE','MCL','Greedy modularity'} and comparison.Status.eq('Complete').all()
    data=bundle(result,clusters,{'source':'fixture'},values,source_raw=state['raw'])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.read('source_network_original.tsv').decode()==state['raw']
        raw=archive.read('analysis.json').decode();assert 'NaN' not in raw
        assert json.loads(raw)['summary']['nodes']==7
        assert len([name for name in archive.namelist() if name.startswith('matrices/')])==5
        assert 'MCODE/members.csv' in archive.namelist()
    session={};first=register_network(session,state);register_network(session,state)
    assert len(session['atlas_string_networks'])==1
    physical,_=fixture(kind='physical',source='physical.tsv');second=register_network(session,physical)
    other,_=fixture(taxon=6182,code='Sjap',source='japonicum.tsv');third=register_network(session,other)
    assert len({first,second,third})==len(session['atlas_string_networks'])==3
    from string_analysis_view import network_labels
    renamed,_=fixture(source='fixture.tsv');renamed['raw']+='\n'
    fourth=register_network(session,renamed)
    assert first!=fourth and len(set(network_labels(session['atlas_string_networks']).values()))==4
    legacy={'atlas_string_network':state};assert len(migrate_networks(legacy))==1
    for kind in ['functional','physical']:
        for scale in [1,1000]:
            current,c=fixture(kind=kind,scale=scale);analysis=analyze_network(prepare_nodes(current,c),current['edges'])
            assert analysis['summary']==result['summary']
    website=state['edges'].assign(experimental=.123).to_csv(sep='\t',index=False)
    site_edges=parse_network(website,6183)
    assert 'experimental' in site_edges and len(site_edges)==len(state['edges'])
    assert analyze_network(nodes,site_edges)['summary']==result['summary']
    empty_edges=state['edges'].iloc[:0];isolates=analyze_network(nodes,empty_edges)
    assert isolates['summary']['isolates']==7 and isolates['nodes'].degree.eq(0).all()
    assert isolates['nodes'].closeness.eq(0).all()
    assert np.allclose(isolates['nodes'].pagerank,1/7)
    zero=state['edges'].copy();zero.combined_score=0
    zero_result=analyze_network(nodes,zero)
    assert zero_result['nodes'].strength.eq(0).all() and np.allclose(zero_result['nodes'].confidence_pagerank,1/7)
    # Cross the old spring-layout SciPy threshold without dropping nodes or importing SciPy.
    big=nx.star_graph(500);big=nx.relabel_nodes(big,lambda i:'6183.'+str(i))
    big_nodes=pd.DataFrame({'identifier':list(big)})
    big_edges=pd.DataFrame([(a,b,.8) for a,b in big.edges],columns=['node1_string_id','node2_string_id','combined_score'])
    with patch.dict(sys.modules,{'scipy':None}):
        full=analyze_network(big_nodes,big_edges);positions=_positions(analysis_graph(full),'Component islands')
    assert len(full['nodes'])==len(positions)==501 and full['edges'].edge_betweenness.isna().all()
    assert any('edge betweenness' in note for note in full['provenance']['notes'])
    with patch('string_analysis.PATH_LIMIT',4):
        limited=analyze_network(nodes,state['edges'])
        assert not limited['provenance']['exact_path_metrics'] and limited['nodes'].closeness.isna().all()
        assert 'sampled' in limited['provenance']['betweenness']
    pd.testing.assert_frame_equal(state['edges'],original)
    print('PASS functional/physical imports, both score scales, exact node/edge/component metrics, '
          'independent PageRank oracle, five matrices, all clustering methods, strict ZIP provenance, '
          'multiple species/import retention, isolates, zero confidence and 501-node SciPy-free analysis',flush=True)
    if '--app' in sys.argv:ui_tests()


def ui_tests():
    from streamlit.testing.v1 import AppTest
    source='''
import streamlit as st
from test_string_analysis import fixture
from string_analysis import register_network
from string_analysis_view import saved_networks_panel
state,candidates=fixture()
if not st.session_state.get('_fixture_initialized'):
    st.session_state['_fixture_initialized']=True
    register_network(st.session_state,state)
    second,_=fixture(kind='physical',source='physical.tsv')
    register_network(st.session_state,second)
saved_networks_panel(candidates)
'''
    app=AppTest.from_string(source,default_timeout=120).run()
    assert not app.exception,[e.message for e in app.exception]
    def select(label,value):
        next(widget for widget in app.selectbox if widget.label==label).set_value(value).run()
        assert not app.exception,[(label,e.message) for e in app.exception]
    assert next(s for s in app.slider if s.label=='Imported minimum combined score').value==0
    from string_analysis_view import SECTIONS
    for section in SECTIONS:select('Imported network section',section)
    select('Imported network section','Matrices')
    for matrix in ['Confidence adjacency','Hop distances','Neighbor Jaccard','Induced Laplacian']:select('Imported matrix',matrix)
    select('Imported network section','Topological clustering')
    for method in ['MCODE','MCL','Greedy modularity']:select('Clustering algorithm',method)
    next(b for b in app.button if b.label=='Analyze all imported STRING networks').click().run()
    assert not app.exception,[e.message for e in app.exception]
    assert len(app.session_state['atlas_string_batch']['summary'])==2
    for identifier in app.session_state['atlas_string_networks']:select('Imported STRING network',identifier)
    next(s for s in app.slider if s.label=='Imported minimum combined score').set_value(1.).run()
    assert not app.exception
    assert any(m.label=='Unique pairs' and m.value=='0' for m in app.metric)
    next(c for c in app.checkbox if c.label=='Hide unconnected imported nodes').set_value(True).run()
    assert not app.exception and any('No nodes remain' in i.value for i in app.info)
    next(b for b in app.button if b.label=='Clear imported STRING workspace').click().run()
    assert not app.exception and len(app.session_state['atlas_string_networks'])==1
    next(b for b in app.button if b.label=='Clear all imported STRING networks').click().run()
    assert not app.exception and 'atlas_string_networks' not in app.session_state
    print('PASS every imported analysis section, five matrices, three clustering viewers, all-import batch report, '
          'network switching, confidence filtering and no-edge/empty views',flush=True)


if __name__=='__main__':main()
