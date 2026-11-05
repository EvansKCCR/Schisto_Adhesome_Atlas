"""Reconcile local Pfam/CDD family hypotheses with the audited catalogue.

Exact protein IDs join the two sources. Review tiers are independent of catalogue
grades/support; neither broad domains nor orthogroup hints transfer a family edge.
"""
from pathlib import Path
import pandas as pd

FILE='files/adhesome_unassigned_Pfam_CDD_classification.xlsx'
SHEET='All unassigned candidates'
REPORT='Schistosome_Pfam_CDD_reconciliation.csv'
MAP_LABEL='Pfam–CDD family/class map'
COLUMNS={
    'Suggested family / class':'reclassification_family',
    'Evidence tier':'reclassification_evidence_tier',
    'Functional module':'reclassification_module',
    'Priority':'reclassification_priority',
    'Evidence rationale':'reclassification_rationale',
    'Supported-family orthogroup context':'reclassification_orthogroup_context',
    'Pfam architecture (full)':'reclassification_pfam',
    'CDD architecture (full)':'reclassification_cdd',
}
PROFILE_FIELDS=list(COLUMNS.values())+['reclassification_tier','reclassification_alignment',
    'reclassification_current','reclassification_source','catalogue_family','catalogue_annotation','classification_basis']
TIER_LABELS={'A':'Concordant diagnostic domains','B':'Family-associated architecture',
    'C':'Domain / catalytic class','D':'Unclassified'}


def _text(series):return series.fillna('').astype(str).str.strip()


def reconcile(candidates,classified=None):
    """Attach all evidence without multiplying rows or replacing audited assignments."""
    from functional_categories import supported_mask
    result=candidates.copy()
    if classified is None:classified=pd.DataFrame(columns=['Protein ID','Species','Orthogroup',*COLUMNS])
    missing=set(['Protein ID','Species','Orthogroup',*COLUMNS])-set(classified)
    if missing:raise ValueError('Pfam–CDD classification is missing columns: '+', '.join(sorted(missing)))
    source=classified.copy().fillna('')
    source['Protein ID']=_text(source['Protein ID'])
    if source['Protein ID'].eq('').any():raise ValueError('Pfam–CDD classification contains an empty protein ID.')
    source=source.drop_duplicates()
    if source['Protein ID'].duplicated().any():raise ValueError('Pfam–CDD classification has conflicting rows for the same protein ID.')
    source=source.set_index('Protein ID')
    ids=result.sequence_id
    present=ids.isin(source.index)
    for original,target in COLUMNS.items():result[target]=ids.map(source[original]).fillna('')
    result['reclassification_tier']=result.reclassification_evidence_tier.str.extract(r'^([ABCD]):',expand=False).fillna('')
    if (present&result.reclassification_tier.eq('')).any():raise ValueError('Pfam–CDD evidence tiers must start with A:, B:, C: or D:.')
    checks=[('Species','species','species'),('Orthogroup','orthogroup','orthogroup'),
        ('Pfam architecture (full)','architecture','Pfam architecture'),('CDD architecture (full)','NCBI_CDD_architecture','CDD architecture')]
    reasons=pd.Series('',index=result.index)
    for original,target,label in checks:
        if target not in result:continue
        mismatch=present&_text(ids.map(source[original])).ne(_text(result[target]))
        reasons.loc[mismatch]=reasons.loc[mismatch].map(lambda value:(value+'; ') if value else '')+label+' differs'
    result['reclassification_alignment']='No reclassification record'
    result.loc[present,'reclassification_alignment']='Matched current library'
    result.loc[present&reasons.ne(''),'reclassification_alignment']=reasons[present&reasons.ne('')]
    overlap=present&supported_mask(result)
    result.loc[overlap,'reclassification_alignment']=result.loc[overlap,'reclassification_alignment']+'; supported catalogue assignment retained'
    result['reclassification_current']=present&reasons.eq('')
    result['reclassification_source']=pd.Series('',index=result.index).where(~present,FILE+' / '+SHEET)
    result['catalogue_annotation']=result.candidate_annotation
    result['classification_basis']='Catalogue family assignment'
    result['display_annotation']=result.candidate_annotation
    contextual=present&result.reclassification_current&result.reclassification_tier.isin(['A','B','C'])&~supported_mask(result)
    result.loc[contextual,'display_annotation']=result.loc[contextual,'reclassification_family']
    unique=result.drop_duplicates('sequence_id')
    matched=unique[unique.sequence_id.isin(source.index)]
    diagnostics=dict(source=FILE,source_records=len(source),matched_proteins=len(matched),
        unmatched_ids=sorted(set(source.index)-set(ids)),stale_proteins=int((~matched.reclassification_current).sum()),
        supported_catalogue_overlaps=int(supported_mask(matched).sum()),
        tiers={tier:int(matched.reclassification_tier.eq(tier).sum()) for tier in TIER_LABELS})
    result.attrs.update(candidates.attrs)
    result.attrs['reclassification']=diagnostics
    return result


def load_table(root):
    path=Path(root)/FILE
    return pd.read_excel(path,sheet_name=SHEET) if path.exists() else None


def priority_order(candidates):
    """Use the reported priority/tier directly, without inventing numeric scores."""
    return candidates[candidates.reclassification_tier.ne('')].drop_duplicates('sequence_id').sort_values(
        ['reclassification_priority','reclassification_tier','sequence_id'],kind='stable').reset_index(drop=True)


def classification_view(candidates):
    """Presentation-only grouping. Original grades/support and family remain explicit."""
    from functional_categories import supported_mask,CATEGORIES,UNASSIGNED
    result=candidates.copy()
    result['catalogue_family']=result.family
    if 'reclassification_current' not in result:return result
    mask=result.reclassification_current&result.reclassification_tier.isin(['A','B','C'])&~supported_mask(result)
    result.loc[mask,'family']=result.loc[mask,'reclassification_family']
    result.loc[mask,'candidate_annotation']=result.loc[mask,'display_annotation']
    modules=result.reclassification_module.str.replace('–','-',regex=False).replace({'Unassigned/other':UNASSIGNED})
    result.loc[mask,'module']=modules[mask].where(modules[mask].isin(CATEGORIES),UNASSIGNED)
    result.loc[mask,'module_basis']='Pfam–CDD functional context; catalogue support retained independently'
    result.loc[mask,'classification_basis']='Pfam–CDD '+result.loc[mask,'reclassification_tier']+' · '+result.loc[mask,'reclassification_evidence_tier'].str.split(': ',n=1).str[-1]
    return result


def reconciliation_table(candidates,classified):
    """All source rows, including unmatched IDs, with baseline decisions side by side."""
    if classified is None:return pd.DataFrame()
    fields=['sequence_id','family','grade','family_support_level','species','orthogroup','architecture',
        'NCBI_CDD_architecture','reclassification_alignment','reclassification_current']
    baseline=candidates.drop_duplicates('sequence_id').reindex(columns=fields).rename(columns={
        'sequence_id':'Protein ID','family':'Catalogue family','grade':'Catalogue grade','family_support_level':'Catalogue family support',
        'species':'Catalogue species','orthogroup':'Catalogue orthogroup','architecture':'Catalogue Pfam','NCBI_CDD_architecture':'Catalogue CDD'})
    result=classified.drop_duplicates().merge(baseline,on='Protein ID',how='left',validate='one_to_one')
    result['reclassification_alignment']=result.reclassification_alignment.fillna('No matching candidate in current catalogue')
    return result
