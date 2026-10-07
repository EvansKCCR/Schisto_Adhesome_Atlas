from atlas_paths import phylogeny_root
"""Exact prepared-ID to representative-protein annotations."""
from functools import lru_cache
from pathlib import Path
import pandas as pd
import re
from data import ROOT

SPECIES_ALIASES = {
    'Schistosoma_haematobium':'Shae', 'Schistosoma_japonicum':'Sjap',
    'Schistosoma_mansoni':'Sman', 'Homo_sapiens':'Hsap',
    'Mus_musculus':'Mmus', 'Xenopus_laevis':'Xlae',
    'Drosophila_melanogaster':'Dmel', 'Caenorhabditis_elegans':'Cele',
}


def canonical_sequence_id(identifier):
    """Normalize species aliases for annotation joins; preserve source tree IDs."""
    species, separator, protein = str(identifier).partition('__')
    return SPECIES_ALIASES.get(species, species) + separator + protein

@lru_cache(maxsize=2)
def _read(path,mtime,size,tip_signature,supplement_signature):
    data=pd.read_csv(path,sep='\t',dtype=str).fillna('')
    tree_ids=set()
    for source_path,_,_ in tip_signature:
        text=Path(source_path).read_text(encoding='utf-8')
        tree_ids.update(canonical_sequence_id(key) for key in
                        re.findall(r'[A-Za-z][A-Za-z_]*__[A-Za-z0-9_.-]+',text))
    data=data[data.prepared_id.isin(tree_ids)].copy()
    data['identifier_mapping_source']=Path(path).name
    if supplement_signature:
        supplement=pd.read_csv(supplement_signature[0],sep='\t',dtype=str).fillna('')
        supplement=supplement[supplement.prepared_id.isin(tree_ids) & ~supplement.prepared_id.isin(data.prepared_id)].copy()
        supplement['identifier_mapping_source']=Path(supplement_signature[0]).name
        data=pd.concat([data,supplement],ignore_index=True)

    join=lambda values:' | '.join(sorted(set(values)-{''}))
    grouped=data.groupby('prepared_id',sort=False).agg(protein_annotation_id=('representative_id',join),original_gene_id=('gene_id',join),alternative_protein_ids=('original_id',join),identifier_mapping_source=('identifier_mapping_source',join))
    selected=data[data.selected.eq('1')].groupby('prepared_id').original_id.agg(join).reindex(grouped.index).fillna('')
    valid=grouped.protein_annotation_id.ne('') & ~grouped.protein_annotation_id.str.contains(' | ',regex=False) & (selected.eq('') | selected.eq(grouped.protein_annotation_id))
    grouped['identifier_mapping_status']=valid.map({True:'Mapped representative',False:'Conflicting representatives'})
    grouped.loc[~valid,'protein_annotation_id']=''
    grouped.index.name='sequence_id'
    grouped['sequence_id']=grouped.index
    return grouped



def identifier_annotations():
    path=ROOT/'identifier_map.tsv'
    if not path.exists(): path=ROOT/'identifier_map_expanded8.tsv.gz'
    if not path.exists(): return pd.DataFrame(columns=['sequence_id','protein_annotation_id','original_gene_id','identifier_mapping_status','alternative_protein_ids'])
    stat=path.stat()
    signature=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted(list(phylogeny_root(ROOT).rglob('tips.tsv'))+list((ROOT/'orthology').rglob('*.tsv'))))
    supplement=ROOT/'identifier_map_expanded8.tsv.gz'
    if not supplement.exists(): supplement=ROOT/'identifier_map_expanded8.tsv'
    extra=(str(supplement),supplement.stat().st_mtime_ns,supplement.stat().st_size) if supplement.exists() else ()
    return _read(str(path),stat.st_mtime_ns,stat.st_size,signature,extra)


def annotate_tips(tips):
    tips=tips.copy()
    tips['source_species']=tips.species
    tips['species']=tips.species.map(lambda species:SPECIES_ALIASES.get(species,species))
    tips['identifier_lookup_id']=tips.sequence_id.map(canonical_sequence_id)
    annotations=identifier_annotations()
    subset=annotations.reset_index(drop=True).rename(columns={'sequence_id':'identifier_lookup_id'})
    result=tips.merge(subset,on='identifier_lookup_id',how='left',validate='many_to_one').fillna('')
    result['display_label']=[species+'__'+protein if protein else key for species,protein,key in zip(result.species,result.protein_annotation_id,result.sequence_id)]
    result.loc[result.identifier_mapping_status.eq(''),'identifier_mapping_status']='No mapping entry'
    return result
