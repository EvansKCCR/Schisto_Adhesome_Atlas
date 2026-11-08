"""Read-only summary workbook parsing, scope preservation and explorer integration."""
from bootstrap import ATLAS_ROOT
import hashlib
import sys
from pathlib import Path

import pandas as pd

from data import ROOT
from orthogroup_statistics import catalogue_statistics, GRADE_COLUMNS, SPECIES_FULL
from orthogroup_variation import (WORKBOOK,MARKED_TSV,DELTA,SPECIES,load_variation,filter_variation,
    family_labels,support_breakdown,variation_signature,REPORT_VARIATION,REPORT_EXACT,catalogue_variation)


def main():
    folder=ROOT/'orthology';files=[folder/WORKBOOK,folder/MARKED_TSV]
    hashes={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    master,frames,checks,notes=load_variation(folder)
    assert checks.empty,checks.to_dict('records')
    assert len(master)==master.Orthogroup.nunique()==579
    assert len(frames['Marked differences'])==len(frames['Marked TSV'])==46
    assert len(frames['Pronounced differences'])==8
    assert master['Supported n'].sum()==1050 and master['Total candidates'].sum()==4355
    assert master['Unresolved n'].sum()==3278
    assert master['Support state: ambiguous'].sum()==25 and master['Support state: provisional'].sum()==2
    assert master.filter(like='Support state: ').sum().sum()==master['Total candidates'].sum()
    assert master[SPECIES].sum().sum()==4355 and len(SPECIES)==7
    assert len(filter_variation(master,'Marked differences'))==46
    assert len(filter_variation(master,'Pronounced differences'))==8
    assert filter_variation(master,families=['tetraspanin-like']).apply(lambda r:'tetraspanin-like' in family_labels(r),axis=1).all()
    assert filter_variation(master,coverage=['All copies supported']).apply(lambda r:r['Supported n']==r['Total candidates'],axis=1).all()
    for sp in SPECIES:assert filter_variation(master,species=[sp])[sp].gt(0).all()
    assert filter_variation(master,query='NO_SUCH_GROUP').empty
    assert set(filter_variation(master,query='OG0000303').Orthogroup)=={'OG0000303'}
    exact=pd.read_csv(folder/'orthogroups_all_exact_copyprofiles.tsv',sep='\t').set_index('Orthogroup')
    shared=master[master.Orthogroup.isin(exact.index)].set_index('Orthogroup')
    assert len(shared)==298
    assert shared['Supported n'].eq(exact.loc[shared.index,'Supported copies']).all()
    assert all(len(value)>0 for value in notes.values()) and len(variation_signature(folder))==2
    try:support_breakdown('ambiguous: unknown')
    except ValueError:pass
    else:raise AssertionError('Malformed support-state counts were accepted')
    assert hashes=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    from test_orthogroup_statistics import candidates_from_workbook
    candidates=candidates_from_workbook()
    assigned=candidates[candidates.orthogroup.ne('')]
    live=catalogue_variation(catalogue_statistics(candidates),master)
    assert len(live)==579 and live['Total candidates'].sum()==4355 and live['Supported n'].sum()==2460
    assert live[GRADE_COLUMNS].sum().tolist()==[1123,0,1337,0]
    assert live.filter(like='Support state: ').sum(axis=1).eq(live['Total candidates']).all()
    assert live[DELTA].ge(2).sum()==46 and live[DELTA].ge(3).sum()==8
    for species in SPECIES:
        subset=assigned[assigned.species.eq(SPECIES_FULL[species])]
        assert live[species].sum()==subset.sequence_id.nunique()
        assert live[species+' supported'].sum()==subset[subset.audit_classification.eq('Supported')].sequence_id.nunique()
    pd.testing.assert_series_equal(live.set_index('Orthogroup')['Reference species support'].sort_index(),
        master.set_index('Orthogroup')['Reference species support'].sort_index())
    print('PASS current 579/46/8 scopes, 2,460/4,355 copies, seven species and separate archived reference evidence',flush=True)
    print('PASS 579/46/8 report scopes, 1050/4355 supported/total, seven-species sums, '
          '3278 unresolved + 25 ambiguous + 2 provisional retained separately, source/TSV consistency, '
          '298 exact-profile overlaps, filtering and unchanged workbook hashes',flush=True)
    if '--app' in sys.argv:ui_tests()


def ui_tests():
    from streamlit.testing.v1 import AppTest
    source='''
import streamlit as st
from test_orthogroup_statistics import candidates_from_workbook
from orthogroup_dashboard import statistics_panel
statistics_panel(candidates_from_workbook())
'''
    app=AppTest.from_string(source,default_timeout=120).run()
    assert not app.exception,[e.message for e in app.exception]
    assert [m.value for m in app.metric][:4]==['579','46','8','2,460 / 4,355']
    def select(label,value):
        next(w for w in app.selectbox if w.label==label).set_value(value).run()
        assert not app.exception,[(label,e.message) for e in app.exception]
    for view in ['Species copy heatmap','Support states','Copy-number spread']:select('Summary visualization',view)
    select('Summary report subset','Marked differences');assert app.metric[0].value=='46'
    select('Summary report subset','Pronounced differences');assert app.metric[0].value=='8'
    select('Summary report subset','All orthogroups')
    next(w for w in app.text_input if w.label=='Find a summary orthogroup, family or reference taxon').set_value('OG0000076').run()
    assert app.metric[0].value=='1' and not app.exception
    next(w for w in app.button if w.label=='Open exact-profile support record').click().run()
    assert next(w for w in app.selectbox if w.label=='Orthogroup report').value==REPORT_EXACT
    assert not app.exception,[e.message for e in app.exception]
    select('Orthogroup report',REPORT_VARIATION)
    next(w for w in app.text_input if w.label=='Find a summary orthogroup, family or reference taxon').set_value('NO_SUCH_GROUP').run()
    assert not app.exception and app.metric[0].value=='0'
    print('PASS summary explorer default, three figures, marked/pronounced filters, selected group, '
          'exact-profile drill-through, report switching and empty results',flush=True)


if __name__=='__main__':main()
