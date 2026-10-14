"""Exact orthogroup dictionary lookup and curator FN3 refinements."""
from functools import lru_cache
from pathlib import Path
import re
import pandas as pd
ROOT = Path(__file__).resolve().parent
COLUMNS = {'Putative_Orthogroup_identity':'orthogroup_identity','Orthology_status':'orthogroup_evolution',
 'Known_binding_partners':'reference_binding_partners','Putative_function':'putative_function',
 'References':'annotation_references','Annotation_confidence':'annotation_confidence','Evidence_notes':'annotation_evidence_notes'}
FIELDS = list(COLUMNS.values()) + ['orthogroup_annotation_source']
FN3_SUMMARY = ('The orthogroup-mapped FN3 repertoire comprises 86 candidates (28 S. haematobium / 29 S. japonicum / 29 S. mansoni) across 25 orthogroups: 17 shared and eight Schistosoma-restricted within the sampled taxa. The workbook additionally retains Sjap__EWB00_004938, a secreted FN3 candidate without an orthogroup assignment, giving 87 inventory records.')
# The curator narrative refines biological identity independently of audit membership.
FN3 = {
 'OG0007305': ('ROBO-like receptor','Five N-terminal Ig-like domains followed by two FN3 domains.','Schistosoma-restricted; conserved 1:1:1 copy profile.','ROBO-family axon guidance receptor-like; provisional subfamily assignment.'),
 'OG0007310': ('UNC-89/obscurin/SPEG-related giant kinase','Extended Ig/FN3 repeats, two predicted kinase regions and long intervening sequences.','Schistosoma-restricted; conserved 1:1:1 copy profile.','Giant cytoskeletal kinase-related protein. EWB00_007901 and Smp_153170 are predicted cytoplasmic; MS3_00010298 topology is unresolved.'),
 'OG0007352': ('Giant FN3-containing kinase-related protein','Extensive Ig-FN3 repeats and a kinase catalytic domain.','Shared orthogroup.','Giant FN3-containing cytoskeletal kinase repertoire.'),
 'OG0010555': ('Putative Eph receptor-like protein','FN3 domains and C-terminal kinase regions; Shae/Sman signal peptide and transmembrane region; Sjap transmembrane region without detected signal peptide.','Schistosoma-restricted; conserved 1:1:1 copy profile.','Receptor-like protein. Diagnostic Eph ligand-binding and cysteine-rich domains are not consistently identified; precise receptor family remains unresolved.'),
 'OG0013755': ('Type IIa receptor protein tyrosine phosphatase-like','N-terminal Ig-like domains, multiple FN3 domains and two C-terminal PTP catalytic regions.','Schistosoma-restricted; conserved 1:1:1 copy profile.','LAR/PTPRD/PTPRS-related receptor phosphatase.'),
}
for group in ['OG0012358','OG0013645','OG0013657']:
 FN3[group]=('Putative Ig-FN3 adhesion receptor-like protein','Variable combinations of Ig-like and FN3 domains.','Schistosoma-restricted; conserved 1:1:1 copy profile.','DCC/neogenin-related architectural affinity; subfamily-specific characterization remains open.')
for group in ['OG0000665','OG0000212']:
 FN3[group]=('FN3-associated receptor PTP-like protein','FN3-associated architecture with one or two PTP catalytic domains.','Shared orthogroup.','Receptor protein tyrosine phosphatase-related repertoire.')

@lru_cache(maxsize=2)
def _dictionary(path,mtime,size):
 frame=pd.read_excel(path,sheet_name=0).fillna('')
 return {str(row['Row Labels']).strip():{out:str(row[col]).strip() for col,out in COLUMNS.items()} for _,row in frame.iterrows()}

def dictionary():
 path=ROOT/'orthology/Orthogroup_dictionary.xlsx'
 if not path.exists(): return {}
 stat=path.stat()
 return _dictionary(str(path),stat.st_mtime_ns,stat.st_size)

def annotate_dictionary(frame):
 out=frame.copy(); lookup=dictionary(); records=[]
 for _,row in out.iterrows():
  groups=next((re.findall(r'OG\d+',str(row[f])) for f in ['orthogroup','Orthogroup','Orthology_Orthogroup','source_groups'] if f in row and re.findall(r'OG\d+',str(row[f]))),[])
  groups=list(dict.fromkeys(groups)); group=groups[0] if len(groups)==1 else ''
  identifier=next((str(row[f]) for f in ['sequence_id','protein_id','candidate_id'] if f in row),'')
  record=dict(lookup.get(identifier,lookup.get(group,{})))
  record['orthogroup_annotation_source']='orthology/Orthogroup_dictionary.xlsx' if record else ''
  if group in FN3:
   title,architecture,evolution,function=FN3[group]
   record.update(orthogroup_identity=title,orthogroup_evolution=evolution,putative_function=function,
    annotation_evidence_notes=architecture,annotation_confidence='Putative family assignment',
    orthogroup_annotation_source='Curator FN3 narrative (2026-10-14)')
  records.append(record)
 for field in FIELDS: out[field]=[record.get(field,'') for record in records]
 return out
