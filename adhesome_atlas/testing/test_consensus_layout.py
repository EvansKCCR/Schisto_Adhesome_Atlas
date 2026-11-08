"""Full-graph integrity, evidence reconstruction and deterministic layout checks."""
from bootstrap import ATLAS_ROOT
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import networkx as nx
import pandas as pd

from data import ROOT,adapt_candidate_library
from curated_network import build_consensus
from reconstruction import topology
from consensus_view import build_view_model,consensus_network_html,member_region,layout_table
from library_refresh import family_key
from functional_categories import assign_modules,supported_mask


def main():
    start=time.monotonic()
    inputs=[ROOT/'files/adhesome_candidates_list.xlsx',ROOT/'adhesome_network/Schistosome_human_reference_family_edges.csv',ROOT/'adhesome_network/Schistosome_adhesome_family_inventory.csv']
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    candidates=pd.read_excel(inputs[0],sheet_name='Audited_family_assignment')
    candidates=adapt_candidate_library(candidates)
    nodes,edges,members=build_consensus(candidates);metrics,graph=topology(nodes,edges)
    original=[frame.copy(deep=True) for frame in (metrics,edges,members)]
    model=build_view_model(metrics,edges,members)
    repeat=build_view_model(metrics,edges,members)
    assert model==repeat,'Layout and payload must be reproducible'
    lookup={n['id']:n for n in model['nodes']}
    assert set(lookup)==set(nodes.identifier) and len(lookup)==len(nodes)
    assert model['totals']['pairs']==graph.number_of_edges()
    assert model['totals']['evidence_rows']==len(edges)
    assert {tuple(sorted((e['source'],e['target']))) for e in model['edges']}=={tuple(sorted(p)) for p in graph.edges}
    assert sorted(i for e in model['edges'] for i in e['evidence_rows'])==list(range(len(edges)))
    reconstructed=pd.DataFrame(model['evidence'])
    pd.testing.assert_frame_equal(reconstructed,edges[reconstructed.columns].reset_index(drop=True),check_dtype=False)
    for n in model['nodes']:
        group=members[members.orthogroup.eq(n['id'])].drop_duplicates('sequence_id')
        assert set(n['member_ids'])==set(group.sequence_id)
        assert n['member_count']==group.sequence_id.nunique()
        assert n['grades']=={g:int(group.grade.eq(g).sum()) for g in ('A','B','C','D')}
        supported=group[supported_mask(group)]
        placed=supported[supported.module.ne('Unassigned/unresolved')]
        context=placed if len(placed) else supported if len(supported) else group
        votes={member_region(row) for row in context.to_dict('records')}
        assert n['compartment']==(next(iter(votes)) if len(votes)==1 else 'unresolved')
        assert set(n['modules'])==set(context.module)-{'','Other family context'}
        same_component=[v['id'] for v in model['nodes'] if v['module_component']==n['module_component']]
        assert nx.is_connected(graph.subgraph(same_component))
    # Candidate support is family-, grade- and species-specific within each OG.
    for row in edges.to_dict('records'):
        for endpoint,family,target in [('node1_string_id','source_family','source_candidates'),('node2_string_id','target_family','target_candidates')]:
            key='reference_source_family' if endpoint=='node1_string_id' else 'reference_target_family'
            support=members[members.orthogroup.eq(row[endpoint])&members.family.map(family_key).eq(family_key(row[key]))
                &supported_mask(members)&members.species.isin(row['shared_species'].split(' | '))]
            ids=sorted(set(support.sequence_id))
            assert ' | '.join(sorted(ids))==row[target]
    assert member_region({'DeepLoc_2.1':'Cytoplasm|Cell membrane','family':'talin'})=='unresolved'
    assert member_region({'DeepLoc_2.1':'','family':'integrin_beta','DeepTMHMM':'TM 100-120'})=='unresolved'
    assert member_region({'DeepLoc_2.1':'Cytoplasm','family':'HSP70_like','module':'Actin & other regulators'})=='unresolved'
    for mode,layout in model['layouts'].items():
        assert set(layout['positions'])==set(lookup)
        positions=layout['positions']
        for i,n in enumerate(model['nodes']):
            p=positions[n['id']]
            assert 0<p['x']<layout['width'] and 0<p['y']<layout['height']
            for other in model['nodes'][i+1:]:
                q=positions[other['id']]
                assert ((p['x']-q['x'])**2+(p['y']-q['y'])**2)**.5>n['radius']+other['radius']+8,(mode,n['id'],other['id'])
    assert len(layout_table(model))==len(nodes)*4
    small=candidates[candidates.species.eq('Schistosoma mansoni')&candidates.grade.eq('A')&candidates.family.map(family_key).isin(
        {family_key(value) for value in ['integrin_alpha','integrin_beta','talin','ILK','PINCH_like']})]
    sn,se,sm=build_consensus(small);sx,sg=topology(sn,se);filtered=build_view_model(sx,se,sm)
    assert set(filtered['candidates'])==set(sm.sequence_id)
    assert filtered['totals']['pairs']==sg.number_of_edges()
    for n in filtered['nodes']:
        assert set(n['member_ids'])==set(sm.loc[sm.orthogroup.eq(n['id']),'sequence_id'])
        assert n['grades']['B']==n['grades']['C']==0
    lone=candidates[candidates.orthogroup.eq(nodes.iloc[0].identifier)].iloc[:1]
    ln,le,lm=build_consensus(lone);lx,lg=topology(ln,le);single=build_view_model(lx,le,lm)
    assert single['totals']['nodes']==1 and single['totals']['pairs']==0
    for before_frame,after_frame in zip(original,(metrics,edges,members)):pd.testing.assert_frame_equal(before_frame,after_frame)
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    output=ROOT/'.ui_review';output.mkdir(exist_ok=True)
    (output/'consensus-after.html').write_text(consensus_network_html(model,'http://127.0.0.1:8511/'),encoding='utf-8')
    (output/'consensus-integrity.json').write_text(json.dumps(dict(totals=model['totals'],graph_sha256=model['graph_sha256'],regions=dict(Counter(n['compartment'] for n in model['nodes'])),source_hashes={p.relative_to(ROOT).as_posix():h for p,h in before.items()},layouts={k:{'width':v['width'],'height':v['height']} for k,v in model['layouts'].items()}),indent=2),encoding='utf-8')
    print('PASS %s nodes, %s pairs, %s evidence records; exact memberships/grades/reference fields; supported functional placement; connected module neighborhoods; 4 deterministic collision-free layouts; unchanged sources; %.1fs'%(len(nodes),graph.number_of_edges(),len(edges),time.monotonic()-start),flush=True)
    print('Region counts:',dict(Counter(n['compartment'] for n in model['nodes'])),flush=True)


if __name__=='__main__':main()
