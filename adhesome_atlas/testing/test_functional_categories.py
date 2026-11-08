"""Reference-summary reconciliation and evidence-supported IPP projection."""
from bootstrap import ATLAS_ROOT
import hashlib
from pathlib import Path

import pandas as pd

from functional_categories import (CATEGORIES,SUMMARY_FILE,assign_modules,reference_mapping,
    summary_tables,supported_mask)
from library_refresh import module_annotations,reference_family_edges,refresh_family_html,_data_span

ROOT=Path(__file__).resolve().parents[1]


def catalogue():
    raw=pd.read_excel(ROOT/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    from data import adapt_candidate_library
    return adapt_candidate_library(raw)


def source_summary():
    paths=[ROOT/SUMMARY_FILE,ROOT/'files/adhesome_candidates_list.xlsx',ROOT/'adhesome_network/interactions.csv']
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    c=catalogue();modules,total,families,species=summary_tables(c)
    assert modules.Category.tolist()==CATEGORIES
    raw=pd.read_excel(paths[1],sheet_name='Audited_family_assignment')
    assert total.iloc[0]['Unique proteins']==raw.protein_id.nunique()
    for label in ['Specific supported','Broad supported','Ambiguous','Provisional','Unresolved']:
        assert total.iloc[0][label]==raw.family_support_level.eq(label.lower()).sum()
        assert modules[label].sum()==total.iloc[0][label]
    assert len(reference_mapping(ROOT)) and len(species.species.unique())==7
    for row in families.to_dict('records'):
        matching=c[c.module.eq(row['Category'])&c.family.eq(row['Family'])]
        assert row['Unique proteins']==matching.sequence_id.nunique()
        assert row['Unique orthogroups']==matching.loc[matching.orthogroup.ne(''),'orthogroup'].nunique()
    # Duplicate assignment records must never inflate the functional summary.
    duplicate=pd.concat([c,c.iloc[[0]]],ignore_index=True)
    for left,right in zip(summary_tables(c),summary_tables(duplicate)):pd.testing.assert_frame_equal(left,right)
    parvin=c[c.family.eq('Parvin_like')]
    assert len(parvin)==14 and supported_mask(parvin).all()
    assert set(parvin.loc[supported_mask(parvin),'module'])=={'Membrane-actin clutch'}
    assert c.loc[c.orthogroup.eq('OG0000818')&c.support_category.eq('broad supported'),'sequence_id'].nunique()==2
    assert set(c.loc[c.family.eq('MMP-like'),'module'])=={'Extracellular'}
    reference=reference_family_edges(ROOT)
    pairs={frozenset([r.family_A,r.family_B]):r for r in reference.itertuples()}
    for partner in ['ILK','PINCH_like']:
        edge=pairs[frozenset(['Parvin_like',partner])]
        assert 'PARVA' in edge.human_symbol_pairs and 'PARVB' in edge.human_symbol_pairs
        assert edge.PMIDs and edge.data_sources
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    print('PASS current family, support, module and species counts; stable unique-ID aggregation and source hashes.')
    return c


def networks(c):
    from curated_network import build_consensus
    from reconstruction import topology
    from consensus_view import build_view_model,consensus_network_html
    from candidate_profiles import candidate_map_html,profile_payload
    n,e,m=build_consensus(c);metrics,graph=topology(n,e);model=build_view_model(metrics,e,m)
    node=next(v for v in model['nodes'] if v['id']=='OG0000818')
    assert node['compartment']=='proximal' and node['primary_module']=='Membrane-actin clutch'
    assert node['member_count']==16 and node['support_counts']=={'specific supported':14,'broad supported':2}
    source=ROOT/'adhesome_network/Schistosome_adhesome_rebuilt.html'
    html=refresh_family_html(source.read_text(encoding='utf-8'),c,ROOT)
    data=_data_span(html)[2]
    parvin=next(f for f in data['families'] if f['id']=='Parvin_like')
    assert parvin['zone']=='Membrane-actin clutch' and parvin['supported_n']==14 and parvin['n']==14
    assert 'Parvin_like' in data['core']
    for partner in ['ILK','PINCH-like']:
        from library_refresh import family_key
        edges=[edge for edge in data['edges'] if {family_key(edge['a']),family_key(edge['b'])}=={family_key(partner),'parvin like'}]
        assert len(edges)==1 and len(edges[0]['shared_species'])==7
        incident=e[((e.source_family.eq('Parvin_like'))&(e.target_family.map(family_key).eq(family_key(partner))))|
            ((e.target_family.eq('Parvin_like'))&(e.source_family.map(family_key).eq(family_key(partner))))]
        assert len(incident)>0
        for row in incident.to_dict('records'):
            field='source_candidates' if row['source_family']=='Parvin_like' else 'target_candidates'
            assert len(row[field].split(' | '))==14 and row['shared_species_count']==7
            assert not set(row[field].split(' | '))&set(c.loc[~supported_mask(c),'sequence_id'])
    output=ROOT/'.ui_review';output.mkdir(exist_ok=True)
    (output/'consensus-after.html').write_text(consensus_network_html(model,'http://127.0.0.1:8511/'),encoding='utf-8')
    # Complete standalone profiles without depending on an app URL or a service.
    from data import load
    cohorts,books,motifs,*_=load()
    payload=profile_payload(cohorts['Adhesome candidates'],books,motifs,root=ROOT)
    (output/'functional-family-map.html').write_text(candidate_map_html(html,payload),encoding='utf-8')
    print(f'PASS Parvin: 14 specific family profiles and two broad CH-domain orthogroup members; clutch placement and seven-species ILK/PINCH source-supported projections. Consensus: {len(n)} nodes, {graph.number_of_edges()} pairs.')


if __name__=='__main__':
    import sys
    c=source_summary()
    if '--networks' in sys.argv:networks(c)
