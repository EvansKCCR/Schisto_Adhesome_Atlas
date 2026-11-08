"""Mutation tests for primary-source regeneration, cache invalidation and scientific joins."""
from bootstrap import ATLAS_ROOT
import json
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import patch,Mock

import pandas as pd

from data import ROOT,fingerprint
from library_refresh import (refresh_derived,refresh_family_html,reference_family_edges,_data_span,
    EDGE_FILE,INVENTORY_FILE,MEMBERS_FILE,MODULE_FILE)
from curated_network import build_consensus
from candidate_profiles import profile_payload,DOMAIN_FIELDS,MOTIF_FIELDS,ORTHOLOGY_FIELDS
from source_watch import reconcile_selections,watch_sources
from simulator import supported_inventory


def candidate(identifier,family,grade='A',group='OG0000001'):
    return dict(sequence_id=identifier,family=family,grade=grade,orthogroup=group,species='Schistosoma test',
        candidate_annotation=family+' test',assignment_confidence='strong' if grade=='A' else 'unassigned',
        audit_classification='Supported' if grade=='A' else 'Unassigned',family_support_level='specific-supported' if grade=='A' else 'unassigned',
        family_decision='family supported' if grade=='A' else 'architecture gate failed',architecture='PF_TEST:1-80',
        module='Test module',stage1_family_hypothesis='integrin_alpha' if grade=='D' else family)


def main():
    with tempfile.TemporaryDirectory(prefix='refresh_test_',dir=ROOT) as temporary:
        root=Path(temporary).resolve();assert root.is_relative_to(ROOT.resolve())
        net=root/'adhesome_network';net.mkdir();(root/'files').mkdir()
        (root/'files/adhesome_candidates_list.xlsx').write_bytes(b'candidate-input-version-1')
        pd.DataFrame([dict(Source='ITGB',Target='TLN',Effect='0',Type='Binding',PMID='123',data_source='curated'),
                      dict(Source='TLN',Target='ITGB',Effect='0',Type='Binding',PMID='124',data_source='curated'),
                      dict(Source='UNKNOWN',Target='ITGB',Effect='0',Type='Binding',PMID='',data_source='curated')]).to_csv(net/'interactions.csv',index=False)
        cross=pd.DataFrame([dict(human_symbol='ITGB',candidate_family='integrin_beta'),dict(human_symbol='TLN',candidate_family='talin')])
        cross.to_csv(net/'Schistosome_human_gene_family_crosswalk.csv',index=False)
        pd.DataFrame([dict(family='integrin_beta',visual_group='Membrane & receptors'),dict(family='talin',visual_group='Membrane–actin clutch')]).to_csv(net/MODULE_FILE,index=False)
        c=pd.DataFrame([candidate('Test__I','integrin_beta'),candidate('Test__T','talin',group='OG0000002')])
        snapshot=refresh_derived(c,root);edges=snapshot['reference']
        assert len(edges)==1 and int(edges.iloc[0].original_rows)==2 and int(edges.iloc[0].human_reference_pairs)==1
        assert set(edges.iloc[0].PMIDs.split('; '))=={'123','124'}
        assert snapshot['provenance']['unmapped_symbols']==[dict(symbol='UNKNOWN',rows=1)]
        assert all((net/f).exists() for f in [EDGE_FILE,INVENTORY_FILE,MEMBERS_FILE])
        stats={p:p.stat().st_mtime_ns for p in net.iterdir()};signature=fingerprint(root)
        # Some file-copy workflows preserve size and modification time.
        candidate_path=root/'files/adhesome_candidates_list.xlsx';original_stat=candidate_path.stat()
        candidate_path.write_bytes(b'candidate-input-version-2')
        os.utime(candidate_path,ns=(original_stat.st_atime_ns,original_stat.st_mtime_ns))
        assert candidate_path.stat().st_size==original_stat.st_size
        assert candidate_path.stat().st_mtime_ns==original_stat.st_mtime_ns
        assert fingerprint(root)!=signature,'Candidate content changes must invalidate inventory/profile caches'
        signature=fingerprint(root)
        refresh_derived(c,root)
        assert stats=={p:p.stat().st_mtime_ns for p in stats},'Repeated refresh must not rewrite identical mirrors'
        assert signature==fingerprint(root),'Generated outputs must not cause source-refresh loops'
        # Crosswalk revisions must also invalidate caches when copying
        # preserves the timestamp and file size.
        review=root/'files/Schisto_adhesome_focused_literature_crosswalk.xlsx'
        review.write_bytes(b'reclassification-1');saved=review.stat();with_review=fingerprint(root)
        review.write_bytes(b'reclassification-2');os.utime(review,ns=(saved.st_atime_ns,saved.st_mtime_ns))
        assert fingerprint(root)!=with_review
        signature=fingerprint(root)
        # Deliberately stale generated file cannot override fresh primary reference data.
        (net/EDGE_FILE).write_text('stale\n',encoding='utf-8');assert signature==fingerprint(root)
        assert len(reference_family_edges(root))==1
        raw=pd.read_csv(net/'interactions.csv',keep_default_na=False)
        raw.loc[len(raw)]=['ITGB','SRC','+','Activation','125','new_source'];raw.to_csv(net/'interactions.csv',index=False)
        assert signature!=fingerprint(root)
        cross.loc[len(cross)]=['SRC','Src'];cross.to_csv(net/'Schistosome_human_gene_family_crosswalk.csv',index=False)
        c=pd.concat([c,pd.DataFrame([candidate('Test__S','Src',group='OG0000003'),candidate('Test__U','unassigned','D','OG0000004')])],ignore_index=True)
        changed=refresh_derived(c,root)
        assert len(changed['reference'])==2 and len(pd.read_csv(net/EDGE_FILE))==2
        assert changed['inventory'].total.sum()==4
        assert changed['inventory'].assignment_records.sum()==4
        duplicate=refresh_derived(pd.concat([c,c.iloc[[0]]],ignore_index=True),root,persist=False)
        assert duplicate['inventory'].assignment_records.sum()==5
        assert duplicate['inventory'].total.sum()==4
        assert duplicate['provenance']['assignment_records']==5 and duplicate['provenance']['candidates']==4
        assert sum(duplicate['provenance']['grade_counts'].values())==5
        assert sum(duplicate['provenance']['unique_grade_counts'].values())==4
        simulator_rows=pd.DataFrame([
            dict(sequence_id='I_alpha',reviewed_family='integrin alpha',species='Schistosoma mansoni',audit_classification='Supported'),
            dict(sequence_id='I_beta',reviewed_family='integrin beta',species='Schistosoma mansoni',audit_classification='Supported'),
            dict(sequence_id='I_beta',reviewed_family='integrin beta',species='Schistosoma mansoni',audit_classification='Supported'),
            dict(sequence_id='Unassigned_alpha',reviewed_family='integrin alpha',species='Schistosoma mansoni',audit_classification='Unassigned')])
        simulator_inventory=supported_inventory(simulator_rows)
        assert simulator_inventory['pan']['integrin_alpha']==simulator_inventory['sm']['integrin_alpha']==1
        assert simulator_inventory['pan']['integrin_beta']==simulator_inventory['sm']['integrin_beta']==1
        assert simulator_inventory['sh']['integrin_alpha']==0
        assert changed['inventory'].set_index('family').loc['unassigned','grade_D']==1
        assert changed['inventory'].set_index('family').loc['Src','visual_group']=='Unassigned/unresolved'
        nodes,pairs,members=build_consensus(c,changed['reference'])
        assert len(nodes)==4 and len(pairs)==2
        assert not pairs.node1_string_id.eq('OG0000004').any() and not pairs.node2_string_id.eq('OG0000004').any()
        old=dict(meta={},families=[],candidates=[],edges=[],special=[],zones=['Membrane & receptors'],core=['integrin_beta'])
        authored='<html><body><button id="custom">Keep control</button><script>const DATA='+json.dumps(old)+';\n</script></body></html>'
        generated=refresh_family_html(authored,c,root);model=_data_span(generated)[2]
        assert 'id="custom"' in generated and model['meta']['proteins']==4
        assert model['meta']['grade_counts']['D']==1 and len(model['edges'])==2
        assert next(p for p in model['candidates'] if p['id']=='Test__U')['f']=='unassigned'
        assert len(next(f for f in model['families'] if f['id']=='unassigned')['human_symbols'])==0
        assert 'unassigned' not in model['core'],'Unassigned records must not be promoted to core membership'
        reduced=c[c.family.ne('talin')]
        fewer=_data_span(refresh_family_html(authored,reduced,root))[2]
        assert 'talin' not in {f['id'] for f in fewer['families']} and len(fewer['edges'])==1
        with patch('library_refresh._write_changed',side_effect=PermissionError('read-only mirror')):
            memory=refresh_derived(c,root)
        assert memory['storage_error'] and len(memory['reference'])==2
        # Orthology profiles must prefer the updated reports rather than stale XLSX exports.
        reports=root/'orthology/new_collection';reports.mkdir(parents=True)
        direct=pd.DataFrame([dict(candidate_id='Test__I',reference_species='Reference species',orthologues='REF_NEW',relationship='one-to-one',source_group_size='1',target_group_size='1')])
        direct.to_csv(reports/'direct_orthologues.tsv',sep='\t',index=False)
        books={'files/NCBI_CDD.xlsx':{'NCBI_CDD_selected_hits':pd.DataFrame(columns=['sequence_id']+DOMAIN_FIELDS)}}
        payload=profile_payload(c,books,pd.DataFrame(columns=['sequence_id']+MOTIF_FIELDS),root)
        assert payload['orthology']['rows']['Test__I'][0][1]=='REF_NEW'
        direct['orthologues']='REF_UPDATED';direct.to_csv(reports/'direct_orthologues.tsv',sep='\t',index=False)
        assert profile_payload(c,books,pd.DataFrame(columns=['sequence_id']+MOTIF_FIELDS),root)['orthology']['rows']['Test__I'][0][1]=='REF_UPDATED'
        state={'catalogue_families':['removed_family','Src'],'catalogue_species':['Schistosoma test'],'map_candidate':'removed_protein'}
        reconcile_selections(state,c);assert state['catalogue_families']==['Src'] and state['map_candidate']==''
    print('PASS reference/crosswalk/candidate mutations, automatic mirror regeneration, exact evidence, D/unassigned isolation, dynamic family map, stale-output immunity, no refresh loops, read-only fallback, latest orthology profiles and retained filters')


def watcher_controls():
    class Rerun(Exception):pass
    for enabled in (True,False):
        ui=Mock();intervals=[]
        def fragment(**kwargs):
            intervals.append(kwargs['run_every']);return lambda function:function
        ui.fragment=fragment;ui.rerun.side_effect=Rerun
        with patch.dict(sys.modules,{'streamlit':ui}),patch('data.fingerprint',return_value=('updated',)) as checked:
            if enabled:
                try:watch_sources(('loaded',),enabled=True)
                except Rerun:pass
                else:raise AssertionError('Changed sources must trigger a full rerun')
                ui.rerun.assert_called_once();checked.assert_called_once()
            else:
                watch_sources(('loaded',),enabled=False)
                ui.rerun.assert_not_called();checked.assert_not_called()
                assert 'data-auto-refresh="false"' in ui.markdown.call_args.args[0]
        assert intervals==['30s' if enabled else None]
    print('PASS content-based candidate changes with preserved metadata, record/protein counts, enabled polling and paused background checks')


def app_checks():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=180).run()
    assert not app.exception,[error.message for error in app.exception]
    control=next(widget for widget in app.toggle if widget.label=='Automatically update inventory')
    assert control.value is True
    assert any('data-auto-refresh="true"' in item.value for item in app.markdown)
    control.set_value(False).run()
    assert not app.exception,[error.message for error in app.exception]
    assert any('data-auto-refresh="false"' in item.value and 'paused' in item.value for item in app.markdown)
    next(widget for widget in app.toggle if widget.label=='Automatically update inventory').set_value(True).run()
    assert not app.exception,[error.message for error in app.exception]
    assert any('data-auto-refresh="true"' in item.value for item in app.markdown)
    assert any(widget.label=='Reload source files' for widget in app.button)
    print('PASS Streamlit auto-update default, pause/resume and retained manual reload')


if __name__=='__main__':
    main();watcher_controls()
    if '--app' in sys.argv:app_checks()
