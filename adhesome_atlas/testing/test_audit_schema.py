"""Regression coverage for changing optional family-audit workbook headers."""
from bootstrap import ATLAS_ROOT
import hashlib
import sys

import pandas as pd

from data import ROOT,load,normalize_audit_columns,family_audit_table


def main():
    legacy=pd.DataFrame({'sequence_id':['one','two'],'identity rule':['domain rule','motif rule'],
        'grade':['A','D']})
    original=legacy.copy(deep=True)
    normalized=normalize_audit_columns(legacy)
    pd.testing.assert_frame_equal(legacy,original)
    assert normalized.identity_rule.tolist()==legacy['identity rule'].tolist()
    assert normalized['identity rule'].tolist()==legacy['identity rule'].tolist()
    pd.testing.assert_frame_equal(normalize_audit_columns(normalized),normalized)
    mixed=legacy.assign(identity_rule=['canonical rule',None])
    assert normalize_audit_columns(mixed).identity_rule.tolist()==['canonical rule','motif rule']
    spaced=legacy.rename(columns={'identity rule':'  Identity\u00a0rule  '})
    assert normalize_audit_columns(spaced).identity_rule.tolist()==legacy['identity rule'].tolist()
    table,missing=family_audit_table(legacy)
    assert len(table)==2 and table.identity_rule.tolist()==legacy['identity rule'].tolist()
    assert 'identity_rule' not in missing and 'identity_competitors' in missing
    minimal=pd.DataFrame({'sequence_id':['one'],'grade':['D']})
    table,missing=family_audit_table(minimal)
    assert table.columns.tolist()==['sequence_id','grade'] and 'identity_rule' in missing
    empty,_=family_audit_table(minimal.iloc[:0]);assert empty.empty

    source=ROOT/'files/adhesome_candidates_list.xlsx'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    cohorts,books,motifs,*_=load()
    candidates=cohorts['Adhesome candidates']
    raw=books['files/adhesome_candidates_list.xlsx']['Audited_family_assignment']
    expected=normalize_audit_columns(raw)
    pd.testing.assert_series_equal(candidates.identity_rule,expected.identity_rule)
    audit,missing=family_audit_table(candidates)
    assert len(audit)==len(raw) and not missing
    assert audit.grade.tolist()==raw.grade.tolist()
    assert audit.sequence_id.tolist()==raw.protein_id.tolist()
    from candidate_profiles import profile_payload
    payload=profile_payload(candidates,books,motifs)
    # Profile rows use exactly the same normalized field values as the audit table.
    exported=pd.DataFrame(payload['candidates'],columns=payload['fields'])
    assert exported.identity_rule.fillna('').tolist()==candidates.identity_rule.fillna('').tolist()
    assert before==hashlib.sha256(source.read_bytes()).hexdigest()
    print(f'PASS audit header aliases, canonical precedence, absent optional fields, empty filters, '
          f'{len(audit)} complete current audit records and unchanged workbook',flush=True)

    if '--app' in sys.argv:
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=300)
        app.session_state['atlas_page']='Components'
        app.session_state['component_section']='Family assignment audit'
        app.run()
        assert not app.exception,[e.message for e in app.exception]
        shown=app.dataframe[0].value
        pd.testing.assert_frame_equal(shown.fillna('').astype(str),audit.fillna('').astype(str))
        app.session_state['catalogue_classification']='Unassigned'
        app.run()
        assert not app.exception,[e.message for e in app.exception]
        shown=app.dataframe[0].value
        assert set(shown.grade)=={'D'} and len(shown)==candidates.audit_classification.eq('Unassigned').sum()
        print('PASS live Components / Family assignment audit and Unassigned filtering',flush=True)


if __name__=='__main__':main()
