"""Curator narrative refinements, separate from the original family audit."""
from functools import lru_cache
import json
from pathlib import Path
import re

import pandas as pd

RESOURCE = Path(__file__).parent/'resource_library/candidate_annotation_calibration'
FIELDS = ['candidate_annotation','candidate_lineage','candidate_architecture_context',
          'candidate_evolutionary_context','candidate_annotation_basis','candidate_annotation_source']


@lru_cache(maxsize=2)
def _rules(path,mtime,size):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def calibration_rules():
    path=RESOURCE/'annotation_rules.json'
    stat=path.stat()
    return _rules(str(path),stat.st_mtime_ns,stat.st_size)


def protein_key(identifier):
    match=re.search(r'(?:MS3_\d+|EWB00_\d+|Smp_\d+)',str(identifier))
    return match.group() if match else str(identifier)


def calibrate_candidates(frame):
    """Match explicit proteins before family-scoped orthogroups; keep audit fields."""
    data=calibration_rules()
    by_protein={key:rule for rule in data['rules'] for key in rule.get('proteins',[])}
    by_group={(rule['family'],group):rule for rule in data['rules']
              for group in rule.get('orthogroups',[])}
    rows=[]
    for _,row in frame.iterrows():
        families=[str(row[field]) for field in ['reviewed_family','family','assigned_family']
                  if field in row and pd.notna(row[field]) and str(row[field]) not in {'','unassigned'}]
        family=families[0] if families else 'Unassigned'
        identifier=next((row[field] for field in ['sequence_id','protein_id'] if field in row),'')
        group=next((str(row[field]) for field in ['orthogroup','Orthology_Orthogroup','Orthogroup','source_groups']
                    if field in row and pd.notna(row[field]) and str(row[field])),'')
        groups=re.findall(r'OG\d+',group)
        group=groups[0] if len(set(groups))==1 else ''
        candidate='candidate' not in row or str(row.candidate)=='1'
        rule=by_protein.get(protein_key(identifier)) if candidate else None
        basis='Protein ID in curator narrative' if rule else 'Orthogroup and family in curator narrative'
        if not rule and candidate: rule=next((by_group[(family,group)] for family in families if (family,group) in by_group),None)
        if rule:
            rows.append(dict(zip(FIELDS,[rule['annotation'],rule['lineage'],rule['architecture'],
                          rule['evolution'],basis,data['source']])))
        else:
            rows.append(dict(zip(FIELDS,[family.replace('_',' '),'', '', '',
                                         'Catalogue family assignment',''])))
    out=frame.copy()
    for field in FIELDS:
        out[field]=[record[field] for record in rows]
    if 'adhesome_interpretation' in out:
        out['audit_adhesome_interpretation']=out.adhesome_interpretation
        matched=out.candidate_annotation_source.ne('')
        out.loc[matched,'adhesome_interpretation']=(out.loc[matched,'candidate_annotation']+' · '+
            out.loc[matched,'candidate_lineage']+'. '+out.loc[matched,'candidate_architecture_context']+' '+
            out.loc[matched,'candidate_evolutionary_context'])
    return out


def family_summaries():
    return calibration_rules()['family_summaries']
