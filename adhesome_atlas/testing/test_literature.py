"""Validate source reconciliation, scoped evidence and normal Atlas destinations."""
from bootstrap import ATLAS_ROOT

from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pandas as pd

from data import CANDIDATE_FILE, CANDIDATE_SHEET, ROOT, adapt_candidate_library
from candidate_profiles import candidate_map_html
from library_refresh import _data_span
from literature import CROSSWALK, MODEL_DIR, SHEETS, build_registry, evidence_for, named_reference_ids
from research_priorities import comparisons, load_brief, priority_trace
from simulator import SIMULATOR_FILE, SimulatorAssetsError, refresh_simulator_assets, simulator_html


def main():
    inputs = [ROOT/CANDIDATE_FILE, ROOT/CROSSWALK]
    before = {p:sha256(p.read_bytes()).hexdigest() for p in inputs}
    raw = pd.read_excel(inputs[0],sheet_name=CANDIDATE_SHEET)
    candidates = adapt_candidate_library(raw)
    assert len(candidates) == candidates.sequence_id.nunique() == 4359
    pd.testing.assert_series_equal(candidates.family, raw.putative_audited_family_new, check_names=False)
    pd.testing.assert_series_equal(candidates.grade, raw.grade)
    pd.testing.assert_series_equal(candidates.annotation_notes, raw.annotation_notes)
    assert candidates.support_category.value_counts().to_dict() == raw.family_support_level.value_counts().to_dict()
    assert candidates.species.nunique() == 7

    sheets = pd.read_excel(inputs[1],sheet_name=None)
    assert tuple(sheets) == SHEETS
    registry = build_registry(ROOT,candidates,sheets)
    assert len(registry['family_index']) == 19
    assert len(registry['mapping_audit']) == 27
    assert all(row['mapping_status'] == 'exact' for row in registry['mapping_audit'])
    assert {row['source_protein_id']:row['changes'] for row in registry['mapping_audit'] if row['changes']} == {
        'Sman__Smp_167010':['family'], 'Sman__Smp_330190':['grade'],
    }
    assert set(registry['references']) == {f'R{i:02d}' for i in range(1,22)}
    assert len({ref['doi'].casefold() for ref in registry['references'].values()}) == 21
    for i, row in sheets[SHEETS[0]].iterrows():
        ref = registry['references'][row['Ref ID']]
        assert ref['source_crosswalk_row'] == i+2 and ref['doi'] == row['DOI']
        assert ref['experimental_finding'] == row['What was shown in Schistosoma']
    assert registry['references']['R10']['pubmed_url'].endswith('/41397983/')
    assert registry['references']['R10']['source_pubmed_url'].endswith('/40909773/')
    assert named_reference_ids(registry,'R02') == {'Sman__Smp_089700','Sman__Smp_079760',
        'Sman__Smp_020540','Sman__Smp_014850'}
    assert named_reference_ids(registry,'R11') == {'Sman__Smp_214190','Sman__Smp_137410'}
    assert not named_reference_ids(registry,'R07')
    assert not named_reference_ids(registry,'R08')
    parvin = next(row for row in evidence_for(registry,'Parvin_like','Sman__Smp_310240') if row['reference_id']=='R02')
    assert parvin['match_level']=='pathway_level' and not parvin['assayed_identity']
    assert all(not row['assayed_identity'] for row in evidence_for(registry,'calpain-like','Sjap__unlinked'))
    assert next(row for row in registry['protein_links']
                if row['protein_id']=='Sman__Smp_047900')['match_level']=='genomic_candidate_mentioned'

    modified = {**sheets,SHEETS[1]:sheets[SHEETS[1]].copy()}
    modified[SHEETS[1]].loc[0,'Library protein ID']='Sman__missing'
    remapped = build_registry(ROOT,candidates,modified)
    missing = remapped['mapping_audit'][0]
    assert missing['mapping_status']=='missing' and missing['protein_id']==''
    assert all(link['source_protein_id']!='Sman__missing' or not link['assayed_identity']
               for link in remapped['protein_links'])
    revised = {**sheets,SHEETS[0]:sheets[SHEETS[0]].copy()}
    revised[SHEETS[0]].loc[0,'DOI']='10.0000/revised'
    unverified = build_registry(ROOT,candidates,revised)
    assert unverified['references']['R01']['reference_verification_status']=='unverified'
    assert '23300694' not in unverified['pmid_index']
    assert not named_reference_ids(unverified,'R01')

    mechanisms = registry['mechanisms']
    assert {layer['id'] for layer in mechanisms['layers']} == {'L1','L2','L3'}
    rules = {rule['rule_id']:rule for rule in mechanisms['rules']}
    assert {'R17','R18','R19'} <= set(rules['M10']['reference_ids'])
    assert rules['M13']['reference_ids'] == ['R02']
    assert 'R16' in rules['M05']['reference_ids']
    assert len({row['interaction_id'] for row in registry['interactions']}) == len(registry['interactions'])
    for edge in registry['interactions']:
        assert set(edge['literature_reference_ids']) <= registry['references'].keys()
        assert not edge['simulator_rule_id'] or edge['simulator_rule_id'] in rules
        if edge['is_reference_projected']:
            assert not edge['source_protein_id'] and not edge['target_protein_id'] and not edge['is_directed']

    brief = load_brief(ROOT/'notes/Target_prioritization.md')
    assert all(check['matches'] for check in comparisons(brief,candidates))
    trace = priority_trace(brief,candidates,registry)
    assert {row['protein_id'] for row in trace} <= set(candidates.sequence_id)
    assert any(row['protein_id']=='Sman__Smp_214190' and row['reference_id']=='R11' and
               row['match_level']=='exact_protein_id' for row in trace)
    assert len(brief['roadmap'])==14 and len(brief['framework'])==6
    assert before == {p:sha256(p.read_bytes()).hexdigest() for p in inputs}

    stored = json.loads((ROOT/MODEL_DIR/'literature_registry.json').read_text(encoding='utf-8'))
    assert stored == registry
    html = (ROOT/'adhesome_network/Schistosome_adhesome_rebuilt.html').read_text(encoding='utf-8')
    model = _data_span(html)[2]
    assert {row['id'] for row in model['candidates']} == set(candidates.sequence_id)
    assert all(row['evidence_origin']=='reference_projected_interaction' for row in model['edges'])
    assert all(edge['reference_ids']==['R02'] for edge in model['special'])
    assert not (ROOT/'adhesome_network/Schistosome_Pfam_CDD_family_hypotheses.html').exists()
    deployment_asset_checks(candidates, registry)
    print(f"PASS {len(candidates):,} unchanged workbook rows and support labels, 14 imported and 7 added references, "
          f"27 scoped source mappings, 19 family categories, {len(registry['interactions'])} interaction records, "
          f"{len(trace):,} priority trace rows, current offline map and provenance.")

    if '--app' in sys.argv:
        app_checks()


def deployment_asset_checks(candidates, registry):
    sim=ROOT/SIMULATOR_FILE
    template=sim.read_text(encoding='utf-8')
    expected=simulator_html(sim,candidates,registry)
    read_text=Path.read_text
    missing={'literature_browser.js','simulator_engine.js','simulator_evidence.js'}

    def deployed_read(path,*args,**kwargs):
        if path.name in missing:
            raise FileNotFoundError(path)
        return read_text(path,*args,**kwargs)

    with patch.object(Path,'read_text',deployed_read):
        map_html=candidate_map_html('<html><body></body></html>',{})
        assert 'function renderLiteratureEvidence' in map_html
        assert simulator_html(sim,candidates,registry)==expected
        outdated={**registry,'mechanisms':{**registry['mechanisms'],'version':'test-new-version'}}
        try:
            refresh_simulator_assets(template,candidates,outdated)
        except SimulatorAssetsError:
            pass
        else:
            raise AssertionError('Outdated embedded simulator scripts should be rejected.')
    print('PASS map renderer and simulator work with all three JavaScript sidecars absent.')


def app_checks():
    from streamlit.testing.v1 import AppTest

    atlas = AppTest.from_file(str(ROOT/'app.py'),default_timeout=300).run()
    assert not atlas.exception, [e.message for e in atlas.exception]
    atlas.sidebar.radio[0].set_value('Components').run()
    sections = next(widget for widget in atlas.selectbox if widget.label=='Component section')
    assert all('reclassification' not in option.lower() for option in sections.options)
    sections.set_value('Family literature evidence').run()
    next(widget for widget in atlas.selectbox if widget.label=='Explore literature by family').set_value('calpain-like').run()
    assert not atlas.exception and any('R11' in item.value for item in atlas.markdown)
    for pid,ref in [('Sman__Smp_089700','R01'),('Sman__Smp_214190','R11'),('Sman__Smp_310240','R02')]:
        atlas.query_params['view']='Protein dossier'
        atlas.query_params['protein']=pid
        atlas.run()
        assert not atlas.exception, [e.message for e in atlas.exception]
        assert 'Literature and biological evidence' in [tab.label for tab in atlas.tabs]
        assert any(ref in item.value for item in atlas.markdown)
    atlas.sidebar.radio[0].set_value('Citations').run()
    assert not atlas.exception and any('Literature and biological evidence'==item.value for item in atlas.header)
    atlas.sidebar.radio[0].set_value('Interactions').run()
    assert not atlas.exception, [e.message for e in atlas.exception]
    next(widget for widget in atlas.selectbox if widget.label=='Network workspace').set_value('Literature & mechanism evidence').run()
    assert not atlas.exception
    print('PASS live Components family evidence, three accession dossiers, Citations registry and Interactions evidence workspace.')


if __name__ == '__main__':
    main()
