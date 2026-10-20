"""Read-only adapters for the current multi-species atlas library."""
from pathlib import Path
import re
import pandas as pd
ROOT=Path(__file__).resolve().parent
SPECIES={'Sbovis':'Schistosoma bovis','Scura':'Schistosoma curassoni','Shae':'Schistosoma haematobium','Sinter':'Schistosoma intercalatum','Sjap':'Schistosoma japonicum','Sman':'Schistosoma mansoni','Srhoda':'Schistosoma rodhaini'}

def source_files():
    folders=['files','family_specific_candidate_fasta','resource_library','adhesome_network','orthology','Phylogeny']
    library=[p for folder in folders for p in (ROOT/folder).rglob('*') if p.is_file() and not p.name.startswith('~$') and p.suffix.lower() not in {'.pyc','.tmp'}]
    documents=[p for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in {'.md','.jpeg','.png','.pptx'}]
    return sorted(library+documents)

def fingerprint():
    return tuple((p.relative_to(ROOT).as_posix(),p.stat().st_mtime_ns,p.stat().st_size) for p in source_files())

def fasta(path):
    records={};key=None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('>'): key=line[1:].split()[0];records[key]=''
        elif key: records[key]+=line.strip()
    return records

def load():
    books={p.relative_to(ROOT).as_posix():pd.read_excel(p,sheet_name=None) for p in (ROOT/'files').glob('*.xlsx') if not p.name.startswith('~$')}
    df=books['files/adhesome_candidates_list.xlsx']['Audited_family_assignment'].copy()
    df['sequence_id']=df.protein_id.astype(str)
    df['species']=df.Specie
    df['family']=df.putative_audited_family.fillna('Unassigned')
    df['reviewed_family']=df.family
    df['catalogue_family']=df.family
    df['candidate_annotation']=df.protein_name.fillna(df.family)
    df['audit_classification']=df.grade.map({'A':'Supported','B':'Supported','C':'Provisional','D':'Unassigned'}).fillna('Unassigned')
    df['status']=df.family_support_level.fillna(df.family_decision)
    df['architecture']=df.Pfam_architecture
    df['orthogroup']=df.Orthology_Orthogroup.fillna('')
    df['orthology_scope']=df.Orthology_HOG_status.fillna('Not recorded')
    df['source']='files/adhesome_candidates_list.xlsx / Audited_family_assignment'
    df['family_assignment_basis']=df.family_decision
    df['assignment_interpretation']=df.protein_name.fillna(df.family)
    inventory=pd.read_csv(ROOT/'adhesome_network/Schistosome_adhesome_family_inventory.csv').fillna('')
    df['module']=df.family.map(inventory.set_index('family').visual_group).fillna('Other family context')
    motifs=books['files/Motif_annotations.xlsx']['Motif_annotations'].copy()
    motifs['motif_id']=motifs.motif_function
    motifs['motif_name']=motifs.motif_function
    motifs['motif_label']=motifs.motif_function
    motifs['peptide']=motifs.representative_peptide
    motifs['candidate_tier']=motifs.reassessed_context_tier
    motifs['context_state']=motifs.reassessed_context_tier
    motifs['functional_hypothesis']=motifs.context_explanation
    motifs['source']='files/Motif_annotations.xlsx / Motif_annotations'
    df['motif_context_evidence']=df.sequence_id.map(motifs.groupby('sequence_id').reassessed_context_tier.agg(lambda x:' | '.join(sorted(set(x.dropna()))))).fillna('No additional motif information present in the current library')
    sequences={};members=[];conflicts=[]
    for p in (ROOT/'family_specific_candidate_fasta').rglob('*'):
        if p.suffix.lower() not in {'.fasta','.faa','.fa'}: continue
        for key,seq in fasta(p).items():
            if key in sequences and sequences[key]!=seq: conflicts.append({'sequence_id':key,'source':p.relative_to(ROOT).as_posix()})
            else: sequences[key]=seq
            members.append({'sequence_id':key,'source':p.relative_to(ROOT).as_posix(),'length':len(seq)})
    raw={sheet:frame for name,sheets in books.items() for sheet,frame in sheets.items() if 'candidate' not in name.lower()}
    return {'Adhesome candidates':df},books,motifs,sequences,pd.DataFrame(members),raw,{},conflicts

def intervals(text):
    return [(m.group(1), int(m.group(2)), int(m.group(3)))
            for m in re.finditer(r'([^;]+):(\d+)-(\d+)', str(text))]

def state_intervals(states):
    return [(m.group()[0], m.start()+1, m.end()) for m in re.finditer(r'(.)\1*', states)]

def fasta_export(ids, sequences):
    return ''.join(f'>{key}\n' + '\n'.join(sequences[key][i:i+80] for i in range(0, len(sequences[key]), 80)) + '\n'
                   for key in dict.fromkeys(ids) if key in sequences)
