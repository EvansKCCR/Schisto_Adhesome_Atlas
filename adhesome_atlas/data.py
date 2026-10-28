"""Read primary annotations and refresh derived multi-species Atlas inventories."""
from pathlib import Path
import re
import pandas as pd
from library_refresh import DERIVED_FILES,module_annotations,refresh_derived
ROOT=Path(__file__).resolve().parent
SCHEMA_VERSION='atlas-data-2'
SPECIES={'Sbovis':'Schistosoma bovis','Scura':'Schistosoma curassoni','Shae':'Schistosoma haematobium','Sinter':'Schistosoma intercalatum','Sjap':'Schistosoma japonicum','Sman':'Schistosoma mansoni','Srhoda':'Schistosoma rodhaini'}

AUDIT_COLUMNS=['sequence_id','species','family','protein_name','grade','assignment_confidence',
    'family_support_level','annotation_resolution','family_decision','identity_rule',
    'identity_competitors','alternative_family_hypotheses','equally_ranked_hypotheses',
    'stage1_family_hypothesis']


def normalize_audit_columns(frame):
    """Expose canonical audit headers while retaining original columns and values."""
    result=frame.copy()
    for canonical in AUDIT_COLUMNS:
        aliases=[column for column in frame.columns if column!=canonical and
            re.sub(r'[\s_]+','_',str(column).strip()).casefold()==canonical.casefold()]
        for alias in aliases:
            if canonical not in result:result[canonical]=frame[alias]
            else:
                missing=result[canonical].isna() | result[canonical].astype(str).str.strip().eq('')
                result[canonical]=result[canonical].where(~missing,frame[alias])
    return result


def family_audit_table(frame):
    normalized=normalize_audit_columns(frame)
    available=[column for column in AUDIT_COLUMNS if column in normalized]
    missing=[column for column in AUDIT_COLUMNS if column not in normalized]
    return normalized.loc[:,available].copy(),missing

def annotate_motif_sites(sites,candidates):
    """Attach every distinct label per protein without expanding or dropping motif rows."""
    fields=['family','species','candidate_annotation']
    def labels(values):
        return ' | '.join(dict.fromkeys(str(value) for value in values
            if pd.notna(value) and str(value).strip()))
    grouped=candidates.groupby('sequence_id',sort=False)
    annotation=grouped[fields].agg(labels).reset_index()
    # Retain original motif columns if a future motif library has its own annotations.
    used=set(sites.columns);renames={}
    for field in fields:
        target=field
        while target in used:target='catalogue_'+target
        renames[field]=target;used.add(target)
    annotation=annotation.rename(columns=renames)
    result=sites.merge(annotation,on='sequence_id',how='left',validate='many_to_one',sort=False)
    counts=grouped.size()
    repeated=counts[(counts>1)&counts.index.isin(sites.sequence_id)]
    result.attrs['motif_annotation_summary']={
        'repeated_protein_ids':repeated.index.tolist(),
        'catalogue_records_for_repeated_ids':int(repeated.sum())}
    return result


def source_files():
    folders=['files','family_specific_candidate_fasta','resource_library','adhesome_network','orthology','Phylogeny','family_phylogeny']
    library=[p for folder in folders for p in (ROOT/folder).rglob('*') if p.is_file() and not p.name.startswith('~$') and p.suffix.lower() not in {'.pyc','.tmp'}]
    documents=[p for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in {'.md','.jpeg','.png','.pptx','.html'}]
    return sorted(library+documents)

def fingerprint(root=None):
    base=Path(root) if root is not None else ROOT
    files=source_files() if base==ROOT else [p for folder in ['files','family_specific_candidate_fasta','resource_library','adhesome_network','orthology','Phylogeny','family_phylogeny'] for p in (base/folder).rglob('*') if p.is_file()]+[p for p in base.glob('*.md')]
    # Generated mirrors cannot trigger a self-refresh cycle; primary inputs still do.
    return tuple((p.relative_to(base).as_posix(),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted(files)
        if not (p.parent.name=='adhesome_network' and p.name in DERIVED_FILES) and not p.name.startswith('~$') and p.suffix.lower() not in {'.tmp','.pyc'})

def fasta(path):
    records={};key=None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('>'): key=line[1:].split()[0];records[key]=''
        elif key: records[key]+=line.strip()
    return records

def load():
    books={p.relative_to(ROOT).as_posix():pd.read_excel(p,sheet_name=None) for p in (ROOT/'files').glob('*.xlsx') if not p.name.startswith('~$')}
    df=normalize_audit_columns(books['files/adhesome_candidates_list.xlsx']['Audited_family_assignment'])
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
    df['module']=df.family.map(module_annotations(ROOT)).fillna('Unassigned / unresolved families')
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
    derived=refresh_derived(df,ROOT)
    df.attrs['library_refresh']=derived['provenance']
    df.attrs['library_storage_error']=derived['storage_error']
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
