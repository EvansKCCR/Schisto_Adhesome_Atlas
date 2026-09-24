"""Exact prepared-ID to representative-protein annotations."""
from functools import lru_cache
from pathlib import Path
import pandas as pd
from data import ROOT

@lru_cache(maxsize=2)
def _read(path,mtime,size,tip_signature,supplement_signature):
    data=pd.read_csv(path,sep='\t',dtype=str).fillna('')
    tree_ids=set()
    for tip_path,_,_ in tip_signature:
        with open(tip_path,encoding='utf-8') as stream:
            next(stream,None)
            tree_ids.update(line.split('\t')[0] for line in stream if line.strip())
    data=data[data.prepared_id.isin(tree_ids)].copy()
    data['identifier_mapping_source']='identifier_map.tsv'
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
    if not path.exists(): return pd.DataFrame(columns=['sequence_id','protein_annotation_id','original_gene_id','identifier_mapping_status','alternative_protein_ids'])
    stat=path.stat()
    signature=tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted((ROOT/'phylogeny').rglob('tips.tsv')))
    supplement=ROOT/'identifier_map_expanded8.tsv.gz'
    if not supplement.exists(): supplement=ROOT/'identifier_map_expanded8.tsv'
    extra=(str(supplement),supplement.stat().st_mtime_ns,supplement.stat().st_size) if supplement.exists() else ()
    return _read(str(path),stat.st_mtime_ns,stat.st_size,signature,extra)


def annotate_tips(tips):
    annotations=identifier_annotations()
    subset=annotations.reindex(tips.sequence_id).drop(columns='sequence_id').reset_index() if not annotations.empty else annotations
    result=tips.merge(subset,on='sequence_id',how='left',validate='one_to_one').fillna('')
    result['display_label']=[species+'__'+protein if protein else key for species,protein,key in zip(result.species,result.protein_annotation_id,result.sequence_id)]
    result.loc[result.identifier_mapping_status.eq(''),'identifier_mapping_status']='No mapping entry'
    return result
