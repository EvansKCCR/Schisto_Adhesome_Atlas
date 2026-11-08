"""Regression tests for the retained offline Pfam/CDD reconciliation workflow."""
from bootstrap import ATLAS_ROOT
import pandas as pd

from reclassification import COLUMNS, classification_view, reconcile, reconciliation_table


def main():
    candidate = dict(sequence_id='Sman__test1', species='Schistosoma mansoni',
        family='Unassigned', catalogue_family='Unassigned', candidate_annotation='Candidate',
        architecture='PF00001:1-100', NCBI_CDD_architecture='CDD1:1-95',
        orthogroup='OG0000001', family_support_level='unresolved', grade='D')
    catalogue = pd.DataFrame([candidate])
    evidence = {key:'' for key in COLUMNS}
    evidence.update({'Protein ID':candidate['sequence_id'],'Species':candidate['species'],
        'Orthogroup':candidate['orthogroup'],'Suggested family / class':'Local hypothesis',
        'Evidence tier':'A: Concordant diagnostic domains','Pfam architecture (full)':candidate['architecture'],
        'CDD architecture (full)':candidate['NCBI_CDD_architecture']})
    source = pd.DataFrame([evidence])
    joined = reconcile(catalogue,source)
    assert joined.reclassification_current.iloc[0]
    pd.testing.assert_frame_equal(joined.loc[:,catalogue.columns],catalogue)
    assert len(reconciliation_table(joined,source))==1
    assert classification_view(joined).family.iloc[0]=='Local hypothesis'
    stale = source.assign(**{'Pfam architecture (full)':'PF_CHANGED:1-95'})
    assert not reconcile(catalogue,stale).reclassification_current.iloc[0]
    unknown = source.assign(**{'Protein ID':'Sman__missing'})
    assert reconcile(catalogue,unknown).attrs['reclassification']['unmatched_ids']==['Sman__missing']
    conflict = source.assign(**{'Suggested family / class':'Different class'})
    try:
        reconcile(catalogue,pd.concat([source,conflict]))
    except ValueError as error:
        assert 'conflicting rows' in str(error)
    else:
        raise AssertionError('Conflicting offline evidence must be rejected')
    print('PASS offline reconciliation retains catalogue fields and detects stale, missing and conflicting evidence.')


if __name__=='__main__':
    main()
