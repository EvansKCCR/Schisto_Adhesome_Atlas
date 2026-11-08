"""Tree alias, tip schema, companion export and mismatch-only presentation checks."""
from bootstrap import ATLAS_ROOT
from contextlib import nullcontext
from io import BytesIO
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
import zipfile
from urllib.parse import parse_qs,urlsplit

import pandas as pd

from data import ROOT, fingerprint
from phylogeny_view import (companion_path, companion_bundle, discover_trees, read_group,
    tree_figure, tree_collection, family_run_metadata, FAMILY_COLLECTION,
    FAMILY_VIEW, ORTHOGROUP_VIEW, tree_records, linked_tree_candidates, parse_newick)
from research_priorities import feature_card, research_priorities_panel


class Presentation:
    """Capture actual priority-panel output without opening server sockets."""
    def __init__(self): self.tables=[]; self.warnings=[]; self.expanders=[]; self.html=[]
    def markdown(self, value, **kwargs): self.html.append(value)
    def caption(self, *args, **kwargs): pass
    def warning(self, value): self.warnings.append(value)
    def tabs(self, names): return [nullcontext() for _ in names]
    def expander(self, name): self.expanders.append(name); return nullcontext()
    def radio(self, *args, **kwargs): return 'Side by side'
    def dataframe(self, frame, **kwargs): self.tables.append(frame)
    def download_button(self, *args, **kwargs): pass


def priorities():
    candidates=pd.DataFrame([dict(sequence_id='Sman__protein',family='example',
        orthogroup='OG_TEST',audit_classification='Supported')])
    feature=dict(key='example',label='Example',objective='Explore',next='Evaluate',
        families=('example',),orthogroups=[],proteins=[],evidence=[],assignments=[],
        metrics=[dict(label='Supported candidates',count=1,families=('example',),classification='Supported')])
    brief=dict(features=[feature],additional=[],framework=[],roadmap=[],references=[])
    with tempfile.TemporaryDirectory() as temp:
        source=Path(temp)/'brief.md';source.write_text('brief',encoding='utf-8')
        for count in (1,2):
            feature['metrics'][0]['count']=count
            ui=Presentation()
            with patch.dict(sys.modules,{'streamlit':ui}), patch('research_priorities.load_brief',return_value=brief):
                research_priorities_panel(candidates,'',source)
            if count==1:
                assert not ui.tables and not ui.warnings
                assert ui.expanders[-1]=='Research references'
                assert 'research-difference' not in feature_card(feature,candidates,'')
            else:
                assert len(ui.tables)==1 and len(ui.warnings)==1
                assert ui.tables[0].to_dict('records')==[{'Research category':'Example',
                    'Measure':'Supported candidates','Research brief':2,'Live catalogue':1}]
                assert 'differs from brief' in feature_card(feature,candidates,'')
    print('PASS matching counts produce no flags/table; mismatches retain both counts and alerts')


def formats():
    candidates=pd.DataFrame([dict(sequence_id='Sman__a',family='example',module='Signalling')])
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp)
        for layout in ('Phylogeny/family_phylogeny','family_phylogeny'):
            for i,alignment in enumerate(('trimmed.faa','trimmed.fasta','trimed.fasta')):
                folder=base/layout/f'family_{i}'
                inference=folder/'inference';inference.mkdir(parents=True)
                (inference/'tree.treefile').write_text('(Sman__a:1,Ref__b:2)90:0;',encoding='utf-8')
                (inference/'tree.iqtree').write_text('report',encoding='utf-8')
                (inference/alignment).write_text('>Sman__a\nAA\n>Ref__b\nAA\n',encoding='utf-8')
                (folder/'tips.tsv').write_text('sequence_id\tpanel_label\tlength_aa\tsource_orthogroup\nSman__a\tSman\t2\tOG_TEST\nRef__b\tRef\t2\tOG_TEST\n',encoding='utf-8')
                root,tips,branches=read_group(folder,candidates)
                assert tips.species.tolist()==['Sman','Ref'] and tips.candidate.tolist()==['1','0']
                assert tips.length.tolist()==['2','2']
                fig,_=tree_figure(root,tips,branches)
                assert sum(len(t.x) for t in fig.data[2:])==2
                assert tree_collection(folder)==FAMILY_COLLECTION
                metadata,_=family_run_metadata(folder,candidates)
                assert metadata['source_orthogroups']==['OG_TEST']
                assert len(family_run_metadata(folder,candidates)[1])==1,'Folder/family spellings must not hide exact candidates'
                with zipfile.ZipFile(BytesIO(companion_bundle(folder,folder.name))) as archive:
                    names=archive.namelist()
                    assert f'{folder.name}/inference/tree.treefile' in names
                    assert f'{folder.name}/inference/tree.iqtree' in names
                    assert f'{folder.name}/inference/{alignment}' in names
                assert companion_path(folder,'inference/trimmed.faa').name==alignment
        folders,incomplete,trees=discover_trees(base)
        assert len(folders)==6 and len(incomplete)==6 and len(trees)==6
        signature=fingerprint(base)
        new=base/'family_phylogeny'/'flat';new.mkdir()
        (new/'tree.treefile').write_text('(a:1,b:1);',encoding='utf-8')
        assert fingerprint(base)!=signature and len(discover_trees(base)[0])==7
        _,tips,branches=read_group(new)
        assert len(tips)==2 and branches.empty
        assert family_run_metadata(new,candidates)[0]['families']==['flat']
        # If both naming conventions exist, show one run with legacy precedence.
        (new/'gene_tree.treefile').write_text('(a:2,b:2);',encoding='utf-8')
        assert len(discover_trees(base)[0])==7
        assert companion_path(new,'inference/gene_tree.treefile').name=='gene_tree.treefile'
        assert read_group(new)[0].children[0].length==2
    print('PASS both roots/layouts, all alignment aliases, tip schema, downloads, partial runs, refresh and duplicate precedence')


def profile_links():
    root=parse_newick('(Sman__a:1,Ref__b:2);')
    tips=pd.DataFrame([dict(sequence_id='Sman__a',candidate='0'),
        dict(sequence_id='Sman__absent',candidate='1')])
    candidates=pd.DataFrame([
        dict(sequence_id='Sman__a',family='Src',grade='A'),
        dict(sequence_id='Sman__a',family='Other hypothesis',grade='C'),
        dict(sequence_id='Sman__absent',family='unassigned',grade='D'),
        dict(sequence_id='Ref__b',family='Other family',grade='B'),
        dict(sequence_id='Unrelated',family='Src',grade='A')])
    linked=linked_tree_candidates(root,tips,candidates,'https://example.org/atlas?view=Phylogeny')
    assert len(linked)==4 and linked.sequence_id.nunique()==3
    assert 'Unrelated' not in set(linked.sequence_id)
    assert linked.sequence_id.tolist()==candidates.sequence_id.tolist()[:4]
    assert linked.grade.tolist()==['A','C','D','B']
    assert linked.in_tree.tolist()==[True,True,False,True]
    for row in linked.itertuples(index=False,name=None):
        url=urlsplit(row[-1])
        assert url.path=='/atlas'
        assert parse_qs(url.query)=={'view':['Protein dossier'],'protein':[row[0]]}
    assert linked_tree_candidates(root,tips,candidates.iloc[0:0]).empty
    print('PASS exact dossier links, duplicate records, original grades, absent tips, unannotated leaves and no family-based false matches')


def current_library():
    book=pd.read_excel(ROOT/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    candidates=book.rename(columns={'protein_id':'sequence_id','putative_audited_family_new':'family'})
    folders,_,_=discover_trees()
    family_folders=[f for f in folders if 'family_phylogeny' in f.parts]
    expected=sorted(p.parent.parent for p in (ROOT/'Phylogeny/family_phylogeny').rglob('tree.treefile'))
    assert family_folders==expected
    records=tree_records(folders,candidates.assign(orthogroup=candidates.Orthology_Orthogroup.fillna('')))
    assert all((record['level']==FAMILY_VIEW)==('family_phylogeny' in record['folder'].parts) for record in records)
    total=0
    for folder in family_folders:
        root,tips,branches=read_group(folder,candidates)
        leaf_ids={node.name for node in __import__('phylogeny_view').layout(root)[2]}
        assert leaf_ids<=set(tips.sequence_id)
        assert tips.sequence_id.is_unique
        assert set(tips.loc[tips.candidate.eq('1'),'sequence_id'])==set(tips.sequence_id)&set(candidates.sequence_id)
        tree_figure(root,tips,branches)
        _,matched=family_run_metadata(folder,candidates)
        linked=linked_tree_candidates(root,tips,candidates)
        assert len(linked)==len(candidates[candidates.sequence_id.isin(set(tips.sequence_id)|leaf_ids)])
        assert set(matched.sequence_id)==set(tips.sequence_id)&set(candidates.sequence_id)
        assert linked.sequence_id.nunique()>0
        total+=len(leaf_ids)
        print(f'  {folder.name}: {len(leaf_ids)} tree tips, {tips.candidate.eq("1").sum()} catalogue candidates')
    print(f'PASS {len(family_folders)} new family trees ({total} tips) alongside {len(folders)-len(family_folders)} original trees')


def app_checks():
    from streamlit.testing.v1 import AppTest
    source='''
import pandas as pd
import streamlit as st
from data import ROOT
from phylogeny_view import phylogeny_panel
@st.cache_data
def fixture():
    book=pd.read_excel(ROOT/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    c=book.rename(columns={'protein_id':'sequence_id','putative_audited_family_new':'family','Orthology_Orthogroup':'orthogroup'})
    c['candidate_annotation']=c.protein_name.fillna('')
    c['species']=c.Specie
    c['audit_classification']=c.grade.map({'A':'Supported','B':'Supported','C':'Provisional','D':'Unassigned'})
    return c
c=fixture()
phylogeny_panel(c)
'''
    app=AppTest.from_string(source,default_timeout=120)
    app.session_state['phylogeny_family_query']='src_like'
    app.run()
    assert not app.exception,[e.message for e in app.exception]
    from phylogeny_view import read_group
    book=pd.read_excel(ROOT/'files/adhesome_candidates_list.xlsx',sheet_name='Audited_family_assignment')
    _,tips,_=read_group(ROOT/'Phylogeny/family_phylogeny/src_like',book.rename(columns={'protein_id':'sequence_id'}))
    expected=['167',str(tips.loc[tips.in_tree,'candidate'].eq('1').sum())]
    assert [m.value for m in app.metric][:2]==expected,[m.value for m in app.metric]
    assert len(app.get('plotly_chart'))==1
    assert any('tree.treefile' in c.value for c in app.caption)
    assert app.radio(key='phylogeny_level').value==FAMILY_VIEW
    assert app.selectbox(key='phylogeny_family_tree').options==['Src-like · src_like']
    tables=[table.value for table in app.dataframe if 'Protein dossier' in table.value.columns]
    assert len(tables)==1
    linked=tables[0]
    assert linked.sequence_id.nunique()==tips.candidate.eq('1').sum()
    protein=tips.loc[tips.in_tree & tips.candidate.eq('1'),'sequence_id'].iloc[0]
    selector=next(widget for widget in app.selectbox if widget.label=='Highlight a linked candidate')
    selector.select(protein).run()
    assert not app.exception,[e.message for e in app.exception]
    button=next(widget for widget in app.get('link_button') if widget.proto.label=='Open selected candidate dossier ↗')
    assert parse_qs(urlsplit(button.proto.url).query)=={'view':['Protein dossier'],'protein':[protein]}
    assert any(value==14 for trace in __import__('json').loads(app.get('plotly_chart')[0].proto.spec)['data'][2:] for value in trace['marker']['size'])
    # Switching collections does not carry the family's search into orthogroups.
    app.radio(key='phylogeny_level').set_value(ORTHOGROUP_VIEW).run()
    assert not app.exception,[e.message for e in app.exception]
    assert app.text_input(key='phylogeny_orthogroup_query').value==''
    assert all(option.startswith('OG') for option in app.selectbox(key='phylogeny_orthogroup_tree').options)
    app.text_input(key='phylogeny_orthogroup_query').set_value('OG0009857').run()
    assert not app.exception,[e.message for e in app.exception]
    assert len(app.get('plotly_chart'))==1
    assert any('gene_tree.treefile' in c.value and 'Tree source:' in c.value for c in app.caption)
    app.radio(key='phylogeny_level').set_value(FAMILY_VIEW).run()
    assert app.text_input(key='phylogeny_family_query').value=='src_like'
    selector=next(widget for widget in app.selectbox if widget.label=='Highlight a linked candidate')
    assert selector.value==protein
    # Incoming orthogroup links select the correct collection before widgets render.
    app.session_state['phylogeny_route_group']='OG0009857'
    app.run()
    assert app.radio(key='phylogeny_level').value==ORTHOGROUP_VIEW
    assert not app.exception,[e.message for e in app.exception]
    app.text_input(key='phylogeny_orthogroup_query').set_value('NO_MATCH_TEST').run()
    assert not app.exception and len(app.get('plotly_chart'))==0
    print('PASS Streamlit separate collections, complete profile links, selected candidate highlighting, retained searches/selections, incoming routes and empty search')


if __name__=='__main__':
    priorities();formats();profile_links();current_library()
    if '--app' in sys.argv: app_checks()
