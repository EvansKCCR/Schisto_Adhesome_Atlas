"""Preserve motif hits when a protein has multiple catalogue records."""
from bootstrap import ATLAS_ROOT
import ast
import hashlib

import pandas as pd
import plotly.express as px

from data import ROOT,annotate_motif_sites


def fixtures():
    candidates=pd.DataFrame({'sequence_id':['one','one','one','two'],
        'family':['A','A','B','C'],'species':['Species']*4,
        'candidate_annotation':['Alpha','Alpha','Beta','Gamma']})
    sites=pd.DataFrame({'sequence_id':['one','one','two','unknown','one'],
        'start':[3,7,9,11,3],'motif_function':['f','g','f','f','f']})
    original=candidates.copy(deep=True);original_sites=sites.copy(deep=True)
    joined=annotate_motif_sites(sites,candidates)
    assert len(joined)==len(sites)
    pd.testing.assert_frame_equal(joined[sites.columns],sites)
    assert joined.loc[0,'family']=='A | B' and joined.loc[0,'candidate_annotation']=='Alpha | Beta'
    assert joined.loc[3,['family','species','candidate_annotation']].isna().all()
    assert joined.attrs['motif_annotation_summary']['repeated_protein_ids']==['one']
    assert joined.attrs['motif_annotation_summary']['catalogue_records_for_repeated_ids']==3
    pd.testing.assert_frame_equal(candidates,original);pd.testing.assert_frame_equal(sites,original_sites)
    empty=annotate_motif_sites(sites.iloc[:0],candidates)
    assert empty.empty and 'candidate_annotation' in empty
    no_candidates=annotate_motif_sites(sites,candidates.iloc[:0])
    assert len(no_candidates)==len(sites) and no_candidates.family.isna().all()
    source_annotations=sites.assign(family='Motif source family',catalogue_family='Earlier metadata')
    collision=annotate_motif_sites(source_annotations,candidates)
    pd.testing.assert_frame_equal(collision[source_annotations.columns],source_annotations)
    assert collision.loc[0,'catalogue_catalogue_family']=='A | B'
    print('PASS repeated IDs, distinct annotations, identical motif rows, missing candidates, empty data, '
          'source-column collisions and unchanged inputs',flush=True)


class Display:
    """Capture the actual shared motif renderer without Streamlit socket initialization."""
    def __init__(self,filters=None):
        self.filters=filters or {};self.metrics={};self.captions=[];self.frames=[];self.downloads=[]
    def subheader(self,*args):pass
    def caption(self,text):self.captions.append(text)
    def columns(self,count):return [self]*count
    def multiselect(self,label,options,**kwargs):return self.filters.get(label,[])
    def metric(self,label,value):self.metrics[label]=value


def renderer():
    source=ast.parse((ROOT/'main/app.py').read_text(encoding='utf-8'))
    function=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='motif_view')
    return compile(ast.Module(body=[function],type_ignores=[]),'app.py::motif_view','exec')


def check_view(code,sites,candidates,key,filters=None):
    display=Display(filters)
    namespace={'st':display,'all_candidates':candidates,'annotate_motif_sites':annotate_motif_sites,
        'px':px,'plotly_chart':lambda *a,**k:None,
        'table':lambda frame:display.frames.append(frame.copy()),
        'download':lambda frame,name:display.downloads.append((frame.copy(),name))}
    exec(code,namespace)
    namespace['motif_view'](sites,key)
    expected=sites.copy()
    for label,column in [('Motif function','motif_function'),('Motif context tier','reassessed_context_tier')]:
        if filters and filters.get(label):expected=expected[expected[column].isin(filters[label])]
    shown=display.frames[0];download,name=display.downloads[0]
    assert len(shown)==len(expected)==display.metrics['Motif sites']
    assert display.metrics['Proteins']==expected.sequence_id.nunique()
    assert name==key+'_sites.csv'
    pd.testing.assert_frame_equal(shown[sites.columns].reset_index(drop=True),expected.reset_index(drop=True))
    pd.testing.assert_frame_equal(download,shown)
    return display


def main():
    fixtures()
    paths=[ROOT/'files/adhesome_candidates_list.xlsx',ROOT/'files/Motif_annotations.xlsx']
    hashes={path:hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    raw=pd.read_excel(paths[0],sheet_name='Audited_family_assignment')
    candidates=raw.assign(sequence_id=raw.protein_id,species=raw.Specie,
        family=raw.putative_audited_family_new,candidate_annotation=raw.protein_name.fillna(raw.putative_audited_family_new))
    sites=pd.read_excel(paths[1],sheet_name='Motif_annotations')
    active=sites[sites.sequence_id.isin(candidates.sequence_id)]
    code=renderer();view=check_view(code,active,candidates,'motifs')
    assert view.captions and len(active)==len(view.frames[0])
    repeated=candidates[candidates.sequence_id.duplicated(keep=False)]
    for protein in repeated.sequence_id.unique():
        subset=sites[sites.sequence_id.eq(protein)]
        shown=check_view(code,subset,candidates,'dossier_motifs')
        assert set(shown.frames[0].sequence_id)=={protein} if len(subset) else shown.frames[0].empty
        expected_families=set(candidates.loc[candidates.sequence_id.eq(protein),'family'].dropna())
        actual=set(' | '.join(shown.frames[0].family.dropna().unique()).split(' | '))
        if len(subset):assert actual==expected_families
        print(f'PASS dossier {protein}: {len(subset)} motif sites, no row multiplication',flush=True)
    functions=active.motif_function.dropna().unique()
    tiers=active.reassessed_context_tier.dropna().unique()
    if len(functions):check_view(code,active,candidates,'motifs',{'Motif function':[functions[0]]})
    if len(tiers):check_view(code,active,candidates,'motifs',{'Motif context tier':[tiers[0]]})
    check_view(code,active.iloc[:0],candidates,'dossier_motifs')
    assert hashes=={path:hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    print(f'PASS shared motif renderer: {len(active)} motif sites, {len(candidates)} catalogue records, '
          f'{candidates.sequence_id.nunique()} unique proteins; filters, empty views and full table downloads; '
          'scientific workbooks unchanged',flush=True)


if __name__=='__main__':main()
