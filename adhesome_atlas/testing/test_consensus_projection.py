"""Reference fidelity, family formatting, species gating and exact edge provenance."""
from bootstrap import ATLAS_ROOT
from itertools import product
import hashlib
import json
from pathlib import Path
import sys

import networkx as nx
import pandas as pd

from data import ROOT,adapt_candidate_library
from curated_network import build_consensus
from library_refresh import (family_key,module_annotations,reference_family_edges,refresh_derived,
    refresh_family_html,_data_span)
from reconstruction import topology
from consensus_view import build_view_model,member_region
from functional_categories import supported_mask


def candidate(identifier,family,group,species='Shae',grade='A'):
    return dict(sequence_id=identifier,family=family,orthogroup=group,species=species,grade=grade,
        candidate_annotation=family,assignment_confidence='test',family_decision='test',
        architecture='PF_TEST',module='Test context')


def reference(left,right):
    return dict(family_A=left,family_B=right,interaction_types='{"Binding":1}',effects='{"0":1}',
        human_reference_pairs=1,original_rows=1,PMIDs='123',data_sources='Test reference',human_symbol_pairs=left+' — '+right)


def fixtures():
    rows=[candidate('I_H','integrin beta','OG0000009'),
        candidate('I_M','integrin beta','OG0000009','Sman'),
        candidate('T_H','talin','OG0000002'),
        candidate('T_D','talin','OG0000002','Sman','D'),
        candidate('Mixed','unassigned','OG0000002','Shae','D'),
        candidate('P_H','PINCH-like','OG0000004'),
        candidate('ILK_M','ILK','OG0000005','Sman'),
        candidate('ILK_H','ILK','OG0000006'),
        candidate('Rho','Rho GTPase-like','OG0000007'),
        candidate('Ras','Ras GTPase-like','OG0000008'),
        candidate('No_group','talin','')]
    c=pd.DataFrame(rows)
    ref=pd.DataFrame([reference('integrin_beta','talin'),reference('PINCH_like','ILK'),
        reference('Ras_GTPase_like','talin'),reference('PINCH_like','PINCH-like')])
    n,e,m=build_consensus(c,ref)
    assert set(n.identifier)==set(c.orthogroup)-{''}
    assert set(zip(e.node1_string_id,e.node2_string_id))=={
        ('OG0000002','OG0000009'),('OG0000004','OG0000006'),('OG0000002','OG0000008')}
    edge=e[e.node2_string_id.eq('OG0000009')].iloc[0]
    assert edge.source_candidates=='T_H' and edge.target_candidates=='I_H'
    assert edge.reference_source_family=='talin' and edge.reference_target_family=='integrin_beta'
    assert edge.source_family=='talin' and edge.target_family=='integrin beta'
    assert edge.shared_species=='Shae' and edge.shared_species_count==1
    assert {'T_D','Mixed'}<=set(m.sequence_id),'Node membership must retain unassigned input records'
    assert not build_consensus(c[c.grade.eq('D')],ref)[1].shape[0]
    assert build_consensus(c,ref.iloc[0:0])[1].empty
    assert build_consensus(c.iloc[0:0],ref)[0].empty
    metrics,graph=topology(n,e);model=build_view_model(metrics,e,m)
    assert model['totals']['pairs']==3
    pd.testing.assert_frame_equal(pd.DataFrame(model['evidence']),e.reset_index(drop=True),check_dtype=False)
    assert member_region({'family':'PINCH-like','DeepLoc_2.1':'Cytoplasm'})=='proximal'
    assert member_region({'family':'alpha actinin','DeepLoc_2.1':'Cytoplasm'})=='cytoskeleton'
    print('PASS formatting aliases, exact endpoint orientation/IDs, shared-species gating, A/B/C versus D, distinct Ras/Rho, self-loop exclusion and empty networks',flush=True)


def current_library():
    inputs=[ROOT/'files/adhesome_candidates_list.xlsx',ROOT/'adhesome_network/interactions.csv',
        ROOT/'adhesome_network/Schistosome_human_gene_family_crosswalk.csv',ROOT/'adhesome_network/family_module_annotations.csv']
    before={path:hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    raw=pd.read_excel(inputs[0],sheet_name='Audited_family_assignment')
    c=adapt_candidate_library(raw)
    ref=reference_family_edges(ROOT);n,e,m=build_consensus(c,ref)
    # Independent reconstruction: construct species networks separately, then union OG pairs.
    expected=set()
    for species,frame in m[supported_mask(m)].groupby('species'):
        mapping=frame.assign(key=frame.family.map(family_key)).groupby('key').orthogroup.agg(set).to_dict()
        for row in ref.itertuples():
            left,right=family_key(row.family_A),family_key(row.family_B)
            if left==right:continue
            expected.update(tuple(sorted((a,b))) for a,b in product(mapping.get(left,()),mapping.get(right,())) if a!=b)
    actual=set(zip(e.node1_string_id,e.node2_string_id))
    assert actual==expected
    for row in e.itertuples():
        for endpoint,reference_family,ids in [(row.node1_string_id,row.reference_source_family,row.source_candidates),
                (row.node2_string_id,row.reference_target_family,row.target_candidates)]:
            support=m[m.orthogroup.eq(endpoint)&m.family.map(family_key).eq(family_key(reference_family))&supported_mask(m)]
            support=support[support.species.isin(row.shared_species.split(' | '))]
            assert set(ids.split(' | '))==set(support.sequence_id)
        assert row.shared_species_count==len(row.shared_species.split(' | '))
    # Formatting-only changes cannot change connectivity.
    legacy=c.copy();legacy['family']=legacy.family.map(lambda value:value.replace('-','_').replace(' ','_'))
    assert set(zip(*[build_consensus(legacy,ref)[1][name] for name in ['node1_string_id','node2_string_id']]))==expected
    metrics,graph=topology(n,e)
    assert nx.number_of_selfloops(graph)==0 and set(graph)==set(n.identifier)
    snapshot=refresh_derived(c,ROOT,persist=False)
    inventory=snapshot['inventory'].set_index('family')
    assert inventory.loc['integrin alpha','visual_group']=='Membrane and receptors'
    assert inventory.loc['PINCH-like','visual_group']=='Membrane-actin clutch'
    assert inventory.loc['integrin beta','human_mapping_symbols']
    model=build_view_model(metrics,e,m)
    assert {tuple(sorted((row['source'],row['target']))) for row in model['edges']}==expected
    assert {row['id'] for row in model['nodes']}==set(n.identifier)
    pd.testing.assert_frame_equal(pd.DataFrame(model['evidence']),e.reset_index(drop=True),check_dtype=False)
    family_model=_data_span(refresh_family_html((ROOT/'adhesome_network/Schistosome_adhesome_rebuilt.html').read_text(encoding='utf-8'),c,ROOT))[2]
    assert any({row['a'],row['b']}=={'ILK','PINCH-like'} for row in family_model['edges'])
    assert any({row['a'],row['b']}=={'integrin alpha','integrin beta'} for row in family_model['edges'])
    assert before=={path:hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}
    report=dict(nodes=len(n),pairs=len(actual),evidence_rows=len(e),connected_nodes=sum(d>0 for _,d in graph.degree()),
        isolates=nx.number_of_isolates(graph),reference_family_count=len(set(e.reference_source_family)|set(e.reference_target_family)),
        inputs={str(path.relative_to(ROOT)):value for path,value in before.items()})
    (ROOT/'.ui_review').mkdir(exist_ok=True)
    (ROOT/'.ui_review/consensus-projection-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS independent per-species reconstruction and union:',report,flush=True)
    print('PASS every source candidate/grade/reference field, formatting invariance, restored family roles and interactive family-map references; primary files unchanged',flush=True)


def app_checks():
    from streamlit.testing.v1 import AppTest
    source='''
import pandas as pd
import streamlit as st
from data import ROOT,adapt_candidate_library
from curated_network import consensus_panel
from library_refresh import module_annotations
@st.cache_data
def fixture():
    raw=pd.read_excel(ROOT/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    c=adapt_candidate_library(raw)
    return c
consensus_panel(fixture())
'''
    app=AppTest.from_string(source,default_timeout=120).run()
    assert not app.exception,[error.message for error in app.exception]
    values={metric.label:metric.value for metric in app.metric}
    report=json.loads((ROOT/'.ui_review/consensus-projection-validation.json').read_text())
    assert int(values['Projected pairs'])==report['pairs']
    assert int(values['Orthogroups'])==report['nodes']
    next(widget for widget in app.checkbox if widget.label=='Hide unconnected consensus nodes').check().run()
    assert not app.exception,[error.message for error in app.exception]
    assert int(next(metric.value for metric in app.metric if metric.label=='Orthogroups'))==report['connected_nodes']
    assert int(next(metric.value for metric in app.metric if metric.label=='Projected pairs'))==report['pairs']
    next(widget for widget in app.selectbox if widget.label=='Network analysis section').select('Centrality & matrices').run()
    assert not app.exception,[error.message for error in app.exception]
    table=app.dataframe[0].value
    assert table.identifier.nunique()==report['connected_nodes']
    assert int(table.degree.sum())==2*report['pairs']
    next(widget for widget in app.selectbox if widget.label=='Network analysis section').select('Evidence & downloads').run()
    assert not app.exception,[error.message for error in app.exception]
    assert len(app.dataframe[0].value)==report['evidence_rows']
    assert {'source_candidates','target_candidates','shared_species','reference_source_family'}<=set(app.dataframe[0].value)
    print('PASS Streamlit graph counts, isolate filter, centrality/adjacency and complete edge evidence/downloads',flush=True)


if __name__=='__main__':
    fixtures();current_library()
    if '--app' in sys.argv:app_checks()
