"""Function-first catalogue grouping, independent of localization predictions.

The reference workbook defines family/module correspondence. Counts are always
recalculated from the active catalogue, on unique protein IDs; no source rows
or original annotations are changed.
"""
from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re

import pandas as pd

SUMMARY_FILE='files/Schisto_adhesome_functional_localization_summary.xlsx'
UNASSIGNED='Unassigned/unresolved'
CATEGORIES=['Extracellular','Membrane and receptors','Membrane-actin clutch',
    'Kinase and phosphatase','Adaptors and small GTPases','Actin and regulator',UNASSIGNED]
SUPPORT_STATES=['specific supported','broad supported','provisional','ambiguous','unresolved']
COLORS=dict(zip(CATEGORIES,['#207950','#26779b','#b08224','#855098','#526ca0','#b85e48','#738079']))


def key(value):
    return '' if pd.isna(value) else re.sub(r'[\W_]+',' ',str(value).casefold()).strip()


@lru_cache(maxsize=4)
def _reference(body):
    frame=pd.read_excel(BytesIO(body),sheet_name='Family breakdown',header=4)
    required={'Functional module','Library family label','Specific supported','Broad supported'}
    if not required<=set(frame):raise ValueError('Functional summary: Family breakdown headers are missing.')
    selected=frame[(pd.to_numeric(frame['Specific supported'],errors='coerce').fillna(0)+
        pd.to_numeric(frame['Broad supported'],errors='coerce').fillna(0)).gt(0)]
    mapping={}
    for row in selected.to_dict('records'):
        family=key(row['Library family label']);module=row['Functional module']
        if module not in CATEGORIES[:-1]:raise ValueError('Unknown functional category: '+str(module))
        if family in mapping and mapping[family]!=module:raise ValueError('Conflicting functional modules for '+family)
        mapping[family]=module
    return mapping


def reference_mapping(root):
    path=Path(root)/SUMMARY_FILE
    return dict(_reference(path.read_bytes())) if path.exists() else {}


def support_state(frame):
    if 'family_support_level' in frame:
        state=frame.family_support_level.fillna('').astype(str).str.strip().str.casefold().str.replace(r'[-_]+',' ',regex=True).str.replace(r'\s+',' ',regex=True)
        return state.where(state.isin(SUPPORT_STATES),'unresolved')
    # Compatibility for historical imports without an explicit family-support field.
    return frame.grade.map({'A':'specific supported','B':'broad supported','C':'provisional'}).fillna('unresolved')


def supported_mask(frame):
    return support_state(frame).isin(SUPPORT_STATES[:2])


def assign_modules(frame,annotations):
    modules=frame.family.map(annotations).fillna(UNASSIGNED)
    return modules.where(supported_mask(frame),UNASSIGNED)


def summary_tables(candidates):
    """Reproduce the reference definitions using the filtered, live inventory."""
    frame=candidates.drop_duplicates('sequence_id',keep='first').copy()
    frame['_support']=support_state(frame)
    frame['module']=frame.module.where(frame.module.isin(CATEGORIES),UNASSIGNED)
    frame.loc[~supported_mask(frame),'module']=UNASSIGNED
    local=frame.get('DeepLoc_2.1',pd.Series('',index=frame.index)).fillna('').astype(str).str.strip()
    topology=frame.get('DeepTMHMM',pd.Series('',index=frame.index)).fillna('').astype(str)
    signal=frame.get('SignalP.v6.0',pd.Series('',index=frame.index)).fillna('').astype(str).str.strip()
    frame['_single']=local.ne('')&~local.str.contains('|',regex=False)
    frame['_tm']=topology.str.contains(r'\bTM\s*\d',regex=True)
    frame['_sp']=signal.eq('SP')&topology.str.contains(r'\bSP\s*\d',regex=True)
    membrane=local.str.split('|').map(lambda values:'Cell membrane' in [v.strip() for v in values])
    frame['_memtm']=membrane&frame._tm
    frame['_strictmem']=local.eq('Cell membrane')&frame._tm
    frame['_strictec']=local.eq('Extracellular')&frame._sp&~frame._tm

    def count(group):
        state=group._support
        return {'Unique proteins':len(group),**{label:int(state.eq(value).sum()) for value,label in zip(
            SUPPORT_STATES,['Specific supported','Broad supported','Provisional','Ambiguous','Unresolved'])},
            'Supported family labels':group.loc[supported_mask(group),'family'].nunique(),
            'Unique orthogroups':group.loc[group.orthogroup.fillna('').str.fullmatch(r'OG\d+'),'orthogroup'].nunique(),
            **{label:int(group[col].sum()) for col,label in [('_single','Single-location DeepLoc'),('_tm','TM prediction'),
                ('_sp','SignalP+DeepTMHMM SP'),('_memtm','Membrane+TM (any label)'),
                ('_strictmem','Strict membrane+TM'),('_strictec','Strict extracellular+SP')]}}

    modules=pd.DataFrame([{'Category':category,**count(frame[frame.module.eq(category)])} for category in CATEGORIES])
    total=pd.DataFrame([{'Category':'ALL UNIQUE PROTEINS',**count(frame)}])
    families=pd.DataFrame([{'Category':module,'Family':family,**count(group)}
        for (module,family),group in frame.groupby(['module','family'],sort=True)])
    species=frame.groupby(['species','module']).size().reset_index(name='Unique proteins')
    return modules,total,families,species
