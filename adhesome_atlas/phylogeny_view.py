from atlas_paths import phylogeny_root
"""Source-preserving IQ-TREE viewer; internal annotations join by tip sets."""
from dataclasses import dataclass, field
from html import escape
from io import BytesIO
import json
import re
import zipfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data import ROOT
from identifier_labels import annotate_tips, identifier_annotations

KEEP = ('tips.tsv', 'inference/gene_tree.treefile', 'inference/trimmed.faa',
        'inference/gene_tree.iqtree', 'inference/branch_evidence.tsv', 'inference/run.json')
COLORS = {'Shae':'#008b8b','Sjap':'#d98632','Sman':'#7665bc','Hsap':'#b65179','Cele':'#628049','Mmus':'#3975b5','Xlae':'#a56b23','Dmel':'#cf4750'}
NAMES = {'Shae':'S. haematobium','Sjap':'S. japonicum','Sman':'S. mansoni',
         'Hsap':'H. sapiens','Cele':'C. elegans','Mmus':'M. musculus','Xlae':'X. laevis','Dmel':'D. melanogaster'}

@dataclass(eq=False)
class Node:
    name: str = ''
    length: float = 0.0
    children: list = field(default_factory=list)

def parse_newick(text):
    # IQ-TREE Newick: quoted/unquoted labels, support pairs, scientific lengths.
    tokens = re.findall(r"'(?:[^']|'')*'|\[[^\]]*\]|[(),:;]|[^\s(),:;\[\]]+", text)
    tokens = [t for t in tokens if not t.startswith('[')]
    pos = 0
    def subtree():
        nonlocal pos
        node = Node()
        if tokens[pos] == '(':
            pos += 1
            node.children.append(subtree())
            while tokens[pos] == ',':
                pos += 1
                node.children.append(subtree())
            if tokens[pos] != ')':
                raise ValueError('Invalid Newick closing bracket')
            pos += 1
        if tokens[pos] not in (':', ',', ')', ';'):
            node.name = tokens[pos].strip("'").replace("''", "'")
            pos += 1
        if tokens[pos] == ':':
            pos += 1
            node.length = float(tokens[pos])
            pos += 1
        return node
    root = subtree()
    if tokens[pos:] != [';']:
        raise ValueError('Expected one complete Newick tree')
    return root

def layout(root, cladogram=False):
    positions, descendants = {}, {}
    leaves = []
    def visit(node, x):
        if node.children:
            for child in node.children:
                visit(child, x + (1 if cladogram else child.length))
            y = sum(positions[c][1] for c in node.children) / len(node.children)
            descendants[node] = frozenset().union(*(descendants[c] for c in node.children))
        else:
            y = len(leaves)
            leaves.append(node)
            descendants[node] = frozenset([node.name])
        positions[node] = (x, y)
    visit(root, 0)
    return positions, descendants, leaves

def discover_trees(root=ROOT):
    """Discover tree files by name; report incomplete runs instead of hiding them."""
    base=phylogeny_root(root)
    trees=sorted(p for p in base.rglob('gene_tree.treefile') if p.is_file())
    folders=[]; incomplete=[]
    for tree in trees:
        folder=tree.parent.parent if tree.parent.name=='inference' else tree.parent
        missing=[name for name in KEEP if not companion_path(folder,name).is_file()]
        if missing: incomplete.append({'tree':str(tree),'missing':', '.join(missing)})
        else: folders.append(folder)
    return sorted(set(folders)),incomplete,trees


def companion_path(folder, relative):
    expected=folder/relative
    if expected.is_file(): return expected
    # Also accept exports where the six retained files sit together in OG…/.
    return folder/relative.split('/')[-1]


def read_group(folder):
    root = parse_newick(companion_path(folder,'inference/gene_tree.treefile').read_text(encoding='utf-8'))
    tips = pd.read_csv(companion_path(folder,'tips.tsv'), sep='\t', dtype=str).fillna('')
    branches = pd.read_csv(companion_path(folder,'inference/branch_evidence.tsv'), sep='\t', dtype=str).fillna('')
    return root, annotate_tips(tips), branches

def tree_collection(folder):
    """Use recorded analysis provenance, not candidate names, to group trees."""
    try:
        project = json.loads(companion_path(folder,'inference/run.json').read_text(encoding='utf-8')).get('settings', {}).get('project', '')
    except (OSError, ValueError):
        return 'Unclassified runs'
    project = str(project).replace('\\', '/').rstrip('/').split('/')[-1]
    return {'fibronectin': 'Fibronectin-like', 'fibronectin_8species': 'Fibronectin-like', 'all_candidates': 'All-candidate analysis', 'all_candidates_8species': 'All-candidate analysis'}.get(project, 'Unclassified runs')

def tree_figure(root, tips, branches, supports=True, cladogram=False, focus=''):
    positions, descendants, leaves = layout(root, cladogram)
    metadata = tips.set_index('sequence_id').to_dict('index')
    evidence = {frozenset(r.tip_ids.split(',')): r for r in branches.itertuples()}
    fig = go.Figure()
    xs, ys, bx, by, labels, hover = [], [], [], [], [], []
    matched = set()
    for node, (x,y) in positions.items():
        if not node.children:
            continue
        xs.extend([x,x,None]); ys.extend([min(positions[c][1] for c in node.children),max(positions[c][1] for c in node.children),None])
        for c in node.children:
            xs.extend([x,positions[c][0],None]); ys.extend([positions[c][1],positions[c][1],None])
        row = evidence.get(descendants[node])
        if row is not None:
            matched.add(row.branch_id)
        if node is not root:
            bx.append(x); by.append(y); labels.append(escape(node.name))
            hover.append(escape(f'{row.branch_id}: {row.support_label}\n{row.interpretation}' if row else f'Tree support: {node.name}; no matching branch-evidence row').replace('\n','<br>'))
    fig.add_trace(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color='#8b9aaa',width=1.3),hoverinfo='skip',showlegend=False))
    fig.add_trace(go.Scatter(x=bx,y=by,text=labels,hovertext=hover,hoverinfo='text',
                            mode='markers+text' if supports else 'markers',textposition='top left',
                            textfont=dict(size=10),marker=dict(size=5,color='#516779'),showlegend=False))
    for sp in sorted(set(metadata.get(n.name,{}).get('species','Unknown') for n in leaves)):
        group = [n for n in leaves if metadata.get(n.name,{}).get('species','Unknown') == sp]
        candidate = [metadata.get(n.name,{}).get('candidate') == '1' for n in group]
        fig.add_trace(go.Scatter(x=[positions[n][0] for n in group],y=[positions[n][1] for n in group],
            mode='markers+text',name=NAMES.get(sp,sp),
            text=[escape(('★ ' if c else '')+metadata.get(n.name,{}).get('display_label',n.name)) for n,c in zip(group,candidate)],textposition='middle right',
            hovertext=[escape(f'{metadata.get(n.name,{}).get("display_label",n.name)} | Gene/tree ID: {n.name} | {NAMES.get(sp,sp)} | Candidate: {c} | Length: {metadata.get(n.name,{}).get("length","unknown")} aa') for n,c in zip(group,candidate)],hoverinfo='text',
            marker=dict(color=COLORS.get(sp,'#999999'),symbol=['diamond' if c else 'circle' for c in candidate],
                        size=[14 if focus and (focus.lower() in n.name.lower() or focus.lower() in metadata.get(n.name,{}).get('display_label','').lower()) else 8 for n in group]),cliponaxis=False))
    xmax = max(x for x,y in positions.values()) or 1
    fig.update_layout(height=max(500, min(12000,len(leaves)*24+150)),margin=dict(l=20,r=260,t=50,b=60),
        xaxis=dict(title='Topological depth (equal branch lengths)' if cladogram else 'Branch length · substitutions per site',range=[-xmax*.02,xmax*1.08]),
        yaxis=dict(visible=False,range=[-1,len(leaves)]),plot_bgcolor='white',
        legend=dict(orientation='h',y=1.03),dragmode='pan')
    return fig, matched

def tree_groups(folders, candidates=None):
    """Group original runs by catalogue annotations and explicit family assignments."""
    explicit=ROOT/'phylogeny_family_groups.tsv'
    curated=pd.read_csv(explicit,sep='\t').fillna('') if explicit.exists() else pd.DataFrame(columns=['family','orthogroup'])
    rows=[]
    for folder in folders:
        og=folder.name.removesuffix('_fib')
        collection=tree_collection(folder)
        matches=pd.DataFrame()
        if candidates is not None and 'orthogroup' in candidates:
            matches=candidates[candidates.orthogroup.eq(og)]
            if 'source' in matches:
                token='fibronectin_like_candidate' if collection=='Fibronectin-like' else 'adhesome_candidates_list'
                matches=matches[matches.source.str.contains(token,regex=False,na=False)]
        names=sorted(set(curated.loc[curated.orthogroup.eq(og),'family']))
        if not names and not matches.empty:
            names=sorted(set(matches.family.dropna().astype(str)))
        modules=sorted(set(matches.module.dropna().astype(str))) if not matches.empty and 'module' in matches else []
        rows.append({'folder':folder,'orthogroup':og,'families':names or ['Unassigned family'],'modules':modules or ['Unassigned module'],'collection':collection})
    return rows


def phylogeny_panel(candidates=None):
    st.subheader('Phylogenetic evidence explorer')
    st.caption('Reference proteomes: H. sapiens (GRCh38.p14) · M. musculus (GRCm39) · X. laevis (Xenopus_laevis_v10.1) · D. melanogaster (GCF_000001215.4) · C. elegans (PRJNA13758).')
    st.write('Inspect gene_tree.treefile with representative protein identifiers from identifier_map.tsv, species colors and ★ / diamond candidate tips from tips.tsv. Branch annotations are matched to branch_evidence.tsv by their exact descendant tip sets.')
    st.info('The supplied trees are unrooted. The rectangular display uses the Newick serialization origin, not an inferred ancestor. Phylogenetic support contributes to assignment confidence alongside domain architecture, topology/localization and motif context.')
    folders,incomplete,tree_files = discover_trees()
    if incomplete:
        st.warning(f'{len(incomplete)} tree runs have missing companion files.')
        with st.expander('Incomplete phylogeny files'): st.dataframe(pd.DataFrame(incomplete),hide_index=True)
    if not folders:
        st.error('No complete phylogeny runs are available in this app environment.')
        st.code(str(phylogeny_root(ROOT)),language=None)
        st.write(f'Tree files found: {len(tree_files)}. The phylogeny directory must be deployed alongside app.py, including gene_tree.treefile, tips.tsv, trimmed.faa, gene_tree.iqtree, branch_evidence.tsv and run.json for each run.')
        st.code('app.py\nphylogeny/\n  adhesome_candidates_list/OG…/tips.tsv\n  adhesome_candidates_list/OG…/inference/gene_tree.treefile\n  fibronectin_like_candidate/OG…/tips.tsv\n  fibronectin_like_candidate/OG…/inference/gene_tree.treefile',language=None)
        return
    with st.expander('Phylogeny source location'):
        st.code(str(phylogeny_root(ROOT)),language=None)
        st.caption(f'{len(tree_files)} tree files found; {len(folders)} complete runs.')
    collections = {p: tree_collection(p) for p in folders}
    collection = st.selectbox('Phylogeny collection', ['All trees'] + sorted(set(collections.values())), key='phylo_collection')
    selected = [p for p in folders if collection == 'All trees' or collections[p] == collection]
    metadata=tree_groups(selected,candidates)
    browse=st.radio('Browse trees by',['Protein family','Functional module','Orthogroup'],horizontal=True,key='phylo_browse')
    field='families' if browse=='Protein family' else 'modules'
    if browse!='Orthogroup':
        categories=sorted({value for row in metadata for value in row[field]})
        category=st.selectbox(browse,['All groups']+categories,key='phylo_group_'+field,format_func=lambda value:value.replace('_',' '))
        if category!='All groups':
            selected=[row['folder'] for row in metadata if category in row[field]]
        st.caption('Family and module groups collect existing orthogroup trees. Each tree retains its own topology, branch lengths and support values.')
        if browse=='Protein family' and category!='All groups':
            group_file=ROOT/'phylogeny_family_groups.tsv'
            if group_file.exists():
                requested=pd.read_csv(group_file,sep='\t')
                expected=set(requested.loc[requested.family.eq(category),'orthogroup'])
                available={row['orthogroup'] for row in metadata}
                missing=sorted(expected-available)
                if missing: st.info('Tree unavailable in this collection: '+', '.join(missing))

    info={row['folder']:row for row in metadata}
    query = st.text_input('Find an orthogroup or protein', key='phylo_search')
    lookup=identifier_annotations()
    matched_ids=set(lookup.loc[lookup.apply(lambda col:col.astype(str).str.contains(query,case=False,regex=False)).any(axis=1),'sequence_id']) if query else set()
    options=[]
    for p in selected:
        text=companion_path(p,'tips.tsv').read_text(encoding='utf-8')
        if not query or query.lower() in p.name.lower() or query.lower() in text.lower() or any(line.split('\t')[0] in matched_ids for line in text.splitlines()[1:]): options.append(p)

    st.caption(f'{len(options)} of {len(folders)} trees · independent of the catalogue sidebar filters')
    with st.expander('Trees in this group'):
        inventory=pd.DataFrame([{'Family':' / '.join(info[p]['families']),'Functional module':' / '.join(info[p]['modules']),'Orthogroup':info[p]['orthogroup'],'Collection':collections[p]} for p in options])
        st.dataframe(inventory,width='stretch',hide_index=True)

    if not options:
        st.info('No matching phylogenetic groups.'); return
    folder = st.selectbox('Phylogenetic orthogroup', options, format_func=lambda p:f'{" / ".join(info[p]["families"])} · {p.name} · {collections[p]}')
    st.caption(f'Analysis collection: {collections[folder]} · Source folder: {folder.relative_to(ROOT).as_posix()}')
    export_name=folder.relative_to(phylogeny_root(ROOT)).as_posix().replace('/','_')
    try:
        root,tips,branches = read_group(folder)
        run = json.loads(companion_path(folder,'inference/run.json').read_text(encoding='utf-8'))
    except (ValueError, OSError, IndexError) as exc:
        st.error(f'Unable to read this phylogeny: {exc}'); return
    a,b,c = st.columns(3)
    a.metric('Tree tips',len(layout(root)[2])); b.metric('Candidate tips',tips.candidate.eq('1').sum()); c.metric('Species',tips.species.nunique())
    supports = st.checkbox('Show branch support labels',value=True)
    cladogram = st.checkbox('Equal branch lengths (cladogram)',value=False)
    focus = st.text_input('Highlight a tip ID',key='phylo_focus')
    fig,matched = tree_figure(root,tips,branches,supports,cladogram,focus)
    report = companion_path(folder,'inference/gene_tree.iqtree').read_text(encoding='utf-8')
    if 'SH-aLRT support (%) / ultrafast bootstrap support (%)' in report:
        st.caption('Support labels: SH-aLRT (%) / ultrafast bootstrap (%), as documented in gene_tree.iqtree. Neither value is a probability of adhesome membership.')
    else:
        st.caption('Support labels are reproduced verbatim; consult the IQ-TREE report for their definition.')
    st.plotly_chart(fig,width='stretch',config={'scrollZoom':True,'displaylogo':False})
    if len(matched) != len(branches):
        st.warning(f'{len(branches)-len(matched)} branch-evidence rows could not be joined to the displayed tree; see the original table below.')
    st.download_button('Download interactive tree · HTML',fig.to_html(include_plotlyjs=True),f'{export_name}_tree.html','text/html')
    tabs = st.tabs(['Tip annotations','Branch evidence','Reproducibility'])
    with tabs[0]:
        st.dataframe(tips[['display_label','protein_annotation_id']+[c for c in tips if c not in ['display_label','protein_annotation_id']]],width='stretch',hide_index=True)
        st.download_button('Download mapped tip annotations',tips.to_csv(index=False),export_name+'_mapped_tips.csv','text/csv')
    with tabs[1]:
        display_branches=branches.copy()
        labels=tips.set_index('sequence_id').display_label.to_dict()
        display_branches.insert(0,'protein_tip_ids',display_branches.tip_ids.map(lambda value:', '.join(labels.get(key.strip(),key.strip()) for key in value.split(','))))
        st.dataframe(display_branches,width='stretch',hide_index=True)
    with tabs[2]:
        st.caption('Original tree and tip IDs are preserved. Display labels use the representative protein ID; mapped tip annotations are downloadable separately.')
        st.caption('The retained trimmed alignment supports rerunning tree inference. run.json preserves original commands and hashes, including references to removed intermediate files; it is not a promise that upstream alignment can be rerun from this reduced library.')
        st.json(run,expanded=False)
        with st.expander('IQ-TREE report'): st.text(report)
        bundle = BytesIO()
        with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
            for relative in KEEP:
                path = companion_path(folder,relative)
                if path.exists():
                    archive.write(path,f'{export_name}/{relative}')
                    st.download_button(f'Download {path.name}',path.read_bytes(),path.name,key=f'phylo_{relative}')
        st.download_button('Download tree and companions · ZIP',bundle.getvalue(),f'{export_name}_phylogeny.zip','application/zip')
