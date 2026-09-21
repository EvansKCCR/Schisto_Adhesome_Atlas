"""Read-only, provenance-preserving adapters for the supplied annotation library."""
from pathlib import Path
import re
import pandas as pd
from evidence import annotate

ROOT = Path(__file__).resolve().parent
SPECIES = {'Shae': 'S. haematobium', 'Sjap': 'S. japonicum', 'Sman': 'S. mansoni'}

def fingerprint():
    return tuple((p.relative_to(ROOT).as_posix(), p.stat().st_mtime_ns, p.stat().st_size)
                 for p in source_files())

def source_files():
    folders = ['files','family_specific_candidate_fasta','topology_localization_cdd','resource_library','adhesome_network','phylogeny']
    return [p for folder in folders for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and not p.name.startswith('~$') and p.suffix.lower() in {'.xlsx','.fasta','.faa','.csv','.tsv','.txt','.3line','.xml','.all','.treefile','.iqtree','.json'}]

def fasta(path):
    records = {}
    key = None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('>'):
            key = line[1:].split()[0]
            records[key] = ''
        elif key:
            records[key] += line.strip()
    return records

def load():
    books = {p.relative_to(ROOT).as_posix(): pd.read_excel(p, sheet_name=None)
             for p in source_files() if p.suffix == '.xlsx'}
    cohorts = {}
    for label, name, sheet in [
        ('Adhesome candidates', 'adhesome_candidates_list.xlsx', 'Sheet1'),
        ('FN3 / fibronectin-like review', 'fibronectin_like_candidate.xlsx', 'library'),
        ('All screening hypotheses', 'all_candidate_protein_list.xlsx', 'candidates')]:
        name = 'files/' + name
        if sheet not in books[name]:
            choices=[s for s,t in books[name].items() if {'protein_id','family','length'} <= set(t.columns)]
            if len(choices)!=1:
                raise ValueError(f'{name}: cannot uniquely identify candidate worksheet')
            sheet=choices[0]
        df = books[name][sheet].copy()
        if 'standardized_id' in df:
            df['sequence_id'] = df.standardized_id + '__' + df.protein_id
        else:
            df['sequence_id'] = df.protein_id
        df['species'] = df.sequence_id.str.split('__').str[0].map(SPECIES).fillna('Unknown')
        df['source'] = name + ' / ' + sheet
        if 'Pfam_architecture' in df:
            df['architecture'] = df.Pfam_architecture
        cohorts[label] = annotate(df)
    motifs = pd.concat([books['files/adhesome_candidates_list.xlsx']['MotifScan_hits'].assign(source='files/adhesome_candidates_list.xlsx / MotifScan_hits'),
                        books['files/fibronectin_like_candidate.xlsx']['motif_scan_hits'].assign(source='files/fibronectin_like_candidate.xlsx / motif_scan_hits')], ignore_index=True)
    from prioritization_evidence import enrich
    for label in ['Adhesome candidates','FN3 / fibronectin-like review']:
        cohorts[label] = enrich(cohorts[label], motifs, ROOT)
    sequences, memberships, conflicts = {}, [], []
    for p in (p for p in source_files() if p.suffix == '.fasta'):
        for key, sequence in fasta(p).items():
            if key in sequences and sequence != sequences[key]:
                conflicts.append({'sequence_id': key, 'source': p.relative_to(ROOT).as_posix()})
            else:
                sequences[key] = sequence
            memberships.append({'sequence_id': key, 'source': p.relative_to(ROOT).as_posix(), 'length': len(sequence)})
    raw = {}
    topologies = {}
    for p in sorted((ROOT / 'topology_localization_cdd').iterdir()):
        name = p.name
        if p.suffix == '.csv':
            table = pd.read_csv(p)
            table['sequence_id'] = table.iloc[:, 0]
            raw[name] = table
        elif 'CDD' in name:
            table = pd.read_csv(p, sep='\t', comment='#')
            table['sequence_id'] = table.Query.str.extract(r'>(\S+)')
            raw[name] = table
        elif 'SignalP' in name or 'SiganP' in name:
            table = pd.read_csv(p, sep='\t', comment='#', names=['sequence_id', 'Prediction', 'OTHER', 'SP(Sec/SPI)', 'CS Position'])
            raw[name] = table
        elif p.suffix == '.3line':
            lines = [s.strip() for s in p.read_text().splitlines() if s.strip()]
            records = []
            for i in range(0, len(lines), 3):
                header, sequence, states = lines[i:i+3]
                key = header[1:].split()[0]
                if len(sequence) != len(states):
                    raise ValueError(f'Topology length mismatch: {key}')
                topologies[key] = states
                records.append({'sequence_id': key, 'class': header.split('|')[-1].strip(), 'length': len(sequence), 'states': states})
            raw[name] = pd.DataFrame(records)
    return cohorts, books, motifs, sequences, pd.DataFrame(memberships), raw, topologies, conflicts

def intervals(text):
    return [(m.group(1), int(m.group(2)), int(m.group(3)))
            for m in re.finditer(r'([^;]+):(\d+)-(\d+)', str(text))]

def state_intervals(states):
    return [(m.group()[0], m.start()+1, m.end()) for m in re.finditer(r'(.)\1*', states)]

def fasta_export(ids, sequences):
    return ''.join(f'>{key}\n' + '\n'.join(sequences[key][i:i+80] for i in range(0, len(sequences[key]), 80)) + '\n'
                   for key in dict.fromkeys(ids) if key in sequences)
