"""Verify every supplied tree and its annotations, plus the explorer controls."""
import json
from streamlit.testing.v1 import AppTest
from phylogeny_view import ROOT, KEEP, read_group, layout, tree_figure, parse_newick

def test_library():
    folders = sorted((ROOT/'phylogeny').glob('OG*'))
    assert len(folders) == 120
    for folder in folders:
        assert all((folder/p).is_file() for p in KEEP), folder
        root,tips,branches = read_group(folder)
        positions,descendants,leaves = layout(root)
        assert len(tips) == len(leaves) == len(set(n.name for n in leaves))
        assert set(tips.sequence_id) == {n.name for n in leaves}
        assert set(tips.candidate) <= {'0','1'}
        assert json.loads((folder/'inference/run.json').read_text())['status'] == 'complete'
        for row in branches.itertuples():
            node = next(n for n,ids in descendants.items() if ids == frozenset(row.tip_ids.split(',')))
            assert node.name == row.support_label, (folder,row)
        alignment_ids = {line[1:].split()[0] for line in (folder/'inference/trimmed.faa').read_text().splitlines() if line.startswith('>')}
        assert alignment_ids == set(tips.sequence_id)
    root = parse_newick("('tip A':1e-3,(b:2,c:3)95/99:4);")
    positions,_,leaves = layout(root)
    assert [n.name for n in leaves] == ['tip A','b','c']
    assert positions[leaves[1]][0] == 6
    print('All 120 trees, tip metadata, branch support and alignment identifiers verified.')

def test_page():
    app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=120).run()
    app.sidebar.radio[0].set_value('Phylogeny').run()
    assert not app.exception, app.exception
    app.text_input(key='phylo_search').set_value('OG0000089').run()
    assert not app.exception
    assert next(s for s in app.selectbox if s.label == 'Phylogenetic orthogroup').value.name == 'OG0000089'
    for checkbox in app.checkbox:
        checkbox.set_value(not checkbox.value)
    app.run()
    assert not app.exception
    app.text_input(key='phylo_search').set_value('no_such_tip').run()
    assert not app.exception
    print('Phylogeny page, search, empty results and display controls passed.')

if __name__ == '__main__':
    test_library()
    test_page()

