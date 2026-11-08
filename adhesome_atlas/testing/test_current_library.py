"""Current seven-species library and Streamlit regression checks."""
from bootstrap import ATLAS_ROOT
import sys,time
import tempfile,re,subprocess,shutil,json
from pathlib import Path
import pandas as pd
from data import ROOT,load,fingerprint
from curated_network import build_consensus
from phylogeny_view import discover_trees,read_group,tree_figure
from family_merges import atlas_group

def main():
    started=time.monotonic()
    cohorts,books,motifs,sequences,*_=load();c=cohorts['Adhesome candidates']
    original=books['files/adhesome_candidates_list.xlsx']['Audited_family_assignment']
    assert set(c.sequence_id)==set(original.protein_id) and len(c)==len(original)
    assert c.grade.value_counts().to_dict()==original.grade.value_counts().to_dict()
    assert c.support_category.value_counts().to_dict()==original.family_support_level.value_counts().to_dict()
    assert len(motifs)==len(books['files/Motif_annotations.xlsx']['Motif_annotations'])
    assert atlas_group('OG0000401')=='OG0000401' and atlas_group('OG0001220')=='OG0001220'
    nodes,edges,members=build_consensus(c)
    assert set(nodes.identifier)==set(c.loc[c.orthogroup.ne(''),'orthogroup'])
    assert edges.evidence.eq('Metazoan reference family projection').all()
    assert set(edges.node1_string_id)|set(edges.node2_string_id)<=set(nodes.identifier)
    folders,pending,tree_files=discover_trees()
    assert len(folders)==len(set(p.parent.parent if p.parent.name=='inference' else p.parent for p in tree_files))
    with tempfile.TemporaryDirectory(prefix='atlas_phylo_test_',dir=ROOT) as temp:
        folder=Path(temp)/'Phylogeny'/'new_collection'/'OG_NEW';folder.mkdir(parents=True)
        (folder/'gene_tree.treefile').write_text('(a:1,b:1)90/100:0;')
        discovered,missing,_=discover_trees(Path(temp));assert discovered==[folder] and missing
        synthetic,tips_missing,branches_missing=read_group(folder)
        assert len(tips_missing)==2 and branches_missing.empty
    if folders:
        root,tips,branches=read_group(folders[0]);fig,matched=tree_figure(root,tips,branches)
        assert matched and len(tips)>0
    print(f'PASS {len(c)} candidates, {len(sequences)} sequences, {len(nodes)} orthogroups, {len(edges)} projection evidence records, {len(folders)} trees; {time.monotonic()-started:.1f}s',flush=True)
    from simulator import simulator_html,SIMULATOR_FILE
    from linked_explorer import linked_explorer_html
    simulator=simulator_html(ROOT/SIMULATOR_FILE,c)
    assert 'Mapped STRING + explicit fallbacks' not in simulator
    assert all(name in simulator for name in c.species.unique())
    from library_refresh import refresh_family_html
    map_html=refresh_family_html((ROOT/'adhesome_network/Schistosome_adhesome_rebuilt.html').read_text(encoding='utf-8'),c,ROOT)
    linked=linked_explorer_html(map_html,simulator)
    assert 'nodeDetails=function' in linked or 'nodeDetails=function' in __import__('html').unescape(linked)
    node=shutil.which('node')
    if node:
        for title,html in [('map',map_html),('simulator',simulator)]:
            script='\n'.join(re.findall(r'<script(?![^>]*application/json)[^>]*>(.*?)</script>',html,re.S))
            result=subprocess.run([node,'--check'],input=script,text=True,capture_output=True)
            assert result.returncode==0,(title,result.stderr)
    print('PASS auto-discovery of a partial new tree, linked map API, seven-species simulation and JavaScript syntax',flush=True)
    if '--app' in sys.argv:
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=300).run()
        assert not app.exception,[e.message for e in app.exception]
        for page in ['Components','Motif explorer','Protein dossier','Orthology','Phylogeny','Interactions','Source Library','Citations','Comments & feedback']:
            app.sidebar.radio[0].set_value(page).run()
            assert not app.exception,[(page,e.message) for e in app.exception]
            print('PASS '+page,flush=True)
        app.sidebar.radio[0].set_value('Interactions').run()
        next(r for r in app.selectbox if r.label=='Network workspace').set_value('STRING query & import').run()
        assert not app.exception,[e.message for e in app.exception]
        next(widget for widget in app.selectbox if widget.label=='STRING query species').set_value('Sman').run()
        assert not app.exception,[e.message for e in app.exception]
        next(widget for widget in app.multiselect if widget.label=='Protein families for STRING').set_value(['integrin beta']).run()
        assert not app.exception,[e.message for e in app.exception]
        assert any('taxon 6183' in cap.value for cap in app.caption)
        print('PASS user STRING workspace and S. mansoni family query planning',flush=True)
if __name__=='__main__':main()
