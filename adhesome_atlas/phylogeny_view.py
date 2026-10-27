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
from data import ROOT,SPECIES


from figure_exports import plotly_chart, selected_export_config



KEEP = ('tips.tsv', 'inference/gene_tree.treefile', 'inference/trimmed.faa',
        'inference/gene_tree.iqtree', 'inference/branch_evidence.tsv', 'inference/run.json')
COLORS = {'Shae':'#008b8b','Sjap':'#d98632','Sman':'#7665bc','Hsap':'#b65179','Cele':'#628049','Mmus':'#3975b5','Xlae':'#a56b23','Dmel':'#cf4750'}
NAMES = {'Shae':'S. haematobium','Sjap':'S. japonicum','Sman':'S. mansoni',
         'Hsap':'H. sapiens','Cele':'C. elegans','Mmus':'M. musculus','Xlae':'X. laevis','Dmel':'D. melanogaster'}
FAMILY_COLLECTION = 'Family-level phylogeny'
FAMILY_NAMES = {'integrin_alpha':'Integrin α','integrin_beta':'Integrin β',
                'alpha_actinin':'α-actinin','paxillin_like':'Paxillin','PINCH_like':'PINCH',
                'PTP_PEST':'PTP-PEST','collagen_like':'Collagen-like','laminin_like':'Laminin-like',
                'zyxin_like':'Zyxin','kindlin':'Kindlin','cofilin':'Cofilin','filamin':'Filamin',
                'talin':'Talin','vinculin':'Vinculin'}

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
        folders.append(folder)
    return sorted(set(folders)),incomplete,trees


def companion_path(folder, relative):
    expected=folder/relative
    if expected.is_file(): return expected
    # Also accept exports where the six retained files sit together in OG…/.
    return folder/relative.split('/')[-1]


def companion_bundle(folder, export_name):
    """Package only the six original visualization and reproducibility files."""
    bundle=BytesIO()
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        for relative in KEEP:
            path=companion_path(folder,relative)
            if path.is_file():
                archive.write(path,f'{export_name}/{relative}')
    return bundle.getvalue()


def read_group(folder):
    root = parse_newick(companion_path(folder,'inference/gene_tree.treefile').read_text(encoding='utf-8'))
    tip_path=companion_path(folder,'tips.tsv')
    tips=pd.read_csv(tip_path,sep='\t',dtype=str).fillna('') if tip_path.exists() else pd.DataFrame([{'sequence_id':node.name,'species':node.name.partition('__')[0],'candidate':'0'} for node in layout(root)[2]])
    tips['display_label']=tips.sequence_id
    branch_path=companion_path(folder,'inference/branch_evidence.tsv')
    branches=pd.read_csv(branch_path,sep='\t',dtype=str).fillna('') if branch_path.exists() else pd.DataFrame(columns=['branch_id','support_label','tip_ids','interpretation'])
    return root,tips,branches

def tree_collection(folder):
    """Use recorded analysis provenance, not candidate names, to group trees."""
    try:
        project = json.loads(companion_path(folder,'inference/run.json').read_text(encoding='utf-8')).get('settings', {}).get('project', '')
    except (OSError, ValueError):
        return 'Unclassified runs'
    project = str(project).replace('\\', '/').rstrip('/').split('/')[-1]
    if project.startswith('family_phylogeny') or 'family_phylogeny' in folder.parts:
        return FAMILY_COLLECTION
    return {'fibronectin': 'Fibronectin-like', 'fibronectin_8species': 'Fibronectin-like', 'all_candidates': 'All-candidate analysis', 'all_candidates_8species': 'All-candidate analysis'}.get(project, 'Unclassified runs')


def family_run_metadata(folder, candidates=None):
    """Label jointly inferred family trees using their tips and audited candidates."""
    tips=pd.read_csv(companion_path(folder,'tips.tsv'),sep='\t',dtype=str).fillna('')
    families=sorted(set(tips.family)-{''}) if 'family' in tips else [folder.name.removeprefix('family_')]
    groups=sorted({group for value in tips.get('source_groups',pd.Series(dtype=str))
                   for group in re.split(r'[,;|\s]+',value) if group})
    matches=pd.DataFrame()
    if candidates is not None and 'sequence_id' in candidates:
        ids=set(tips.loc[tips.candidate.eq('1'),'sequence_id'].map(canonical_sequence_id))
        matches=candidates[candidates.sequence_id.map(canonical_sequence_id).isin(ids)]
        if 'reviewed_family' in matches:
            matches=matches[matches.reviewed_family.isin(families)]
        elif 'family' in matches:
            matches=matches[matches.family.isin(families)]
    modules=sorted(set(matches.module.dropna().astype(str))) if not matches.empty and 'module' in matches else []
    return {'folder':folder,'orthogroup':folder.name,'families':[FAMILY_NAMES.get(f,f) for f in families],
            'modules':modules or ['Unassigned module'],'collection':FAMILY_COLLECTION,
            'source_orthogroups':groups,'tree_level':'Joint family tree'}, matches

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
                            textfont=dict(size=14,color='#000000'),marker=dict(size=5,color='#516779'),showlegend=False,cliponaxis=False))
    for sp in sorted(set(metadata.get(n.name,{}).get('species','Unknown') for n in leaves)):
        group = [n for n in leaves if metadata.get(n.name,{}).get('species','Unknown') == sp]
        candidate = [metadata.get(n.name,{}).get('candidate') == '1' for n in group]
        fig.add_trace(go.Scatter(x=[positions[n][0] for n in group],y=[positions[n][1] for n in group],
            mode='markers+text',name=NAMES.get(sp,sp),
            text=[escape(('★ ' if c else '')+metadata.get(n.name,{}).get('display_label',n.name)) for n,c in zip(group,candidate)],textposition='middle right',textfont=dict(size=16,color='#000000'),
            hovertext=[escape(f'{metadata.get(n.name,{}).get("display_label",n.name)} | Gene/tree ID: {n.name} | {NAMES.get(sp,sp)} | Candidate: {c} | {metadata.get(n.name,{}).get("candidate_annotation","")} | {metadata.get(n.name,{}).get("candidate_lineage","")} | Length: {metadata.get(n.name,{}).get("length","unknown")} aa') for n,c in zip(group,candidate)],hoverinfo='text',
            marker=dict(color=COLORS.get(sp,'#999999'),symbol=['diamond' if c else 'circle' for c in candidate],
                        size=[14 if focus and (focus.lower() in n.name.lower() or focus.lower() in metadata.get(n.name,{}).get('display_label','').lower()) else 8 for n in group]),cliponaxis=False))
    xmax = max(x for x,y in positions.values()) or 1
    label_length=max((len(metadata.get(node.name,{}).get('display_label',node.name)) for node in leaves),default=20)
    fig.update_layout(height=max(500,len(leaves)*30+170),margin=dict(l=90,r=min(600,max(300,label_length*9+40)),t=85,b=70),
        xaxis=dict(title='Topological depth (equal branch lengths)' if cladogram else 'Branch length · substitutions per site',range=[-xmax*.02,xmax*1.08]),
        yaxis=dict(visible=False,range=[-1,len(leaves)]),plot_bgcolor='white',
        legend=dict(orientation='h',y=1.03),dragmode='pan')
    return fig, matched


def phylogeny_panel(candidates=None):
    st.subheader('Phylogenetic evidence explorer')
    st.caption('Trees are discovered recursively from Phylogeny on every refresh. Add a new gene_tree.treefile and its available companions; completed trees appear automatically. Partial runs remain visible with their missing companions listed. Source orthogroups are preserved exactly.')
    folders,incomplete,trees=discover_trees()
    if incomplete:
        with st.expander('Companion files awaiting addition'): st.dataframe(pd.DataFrame(incomplete),hide_index=True,width='stretch')
    if not folders: st.info('No gene_tree.treefile is present yet. To be updated when additional phylogeny files are available.'); return
    info=[]
    for folder in folders:
        og=folder.name
        families=sorted(set(candidates.loc[candidates.orthogroup.eq(og),'family'])) if candidates is not None else []
        info.append({'folder':folder,'orthogroup':og,'families':' | '.join(families)})
    route_group=st.session_state.pop('phylogeny_route_group',None)
    if route_group:st.session_state['phylogeny_query']=route_group
    query=st.text_input('Find a tree, orthogroup or protein family',key='phylogeny_query')
    filtered=[]
    for record in info:
        tips_path=companion_path(record['folder'],'tips.tsv')
        text=record['orthogroup']+' '+record['families']
        if tips_path.exists(): text+=' '+tips_path.read_text(encoding='utf-8')
        if not query or query.casefold() in text.casefold(): filtered.append(record)
    st.caption(f'{len(filtered)} of {len(info)} available trees')
    if not filtered: st.info('No matching phylogenetic groups.');return
    chosen=st.selectbox('Phylogenetic orthogroup',range(len(filtered)),format_func=lambda index:filtered[index]['orthogroup']+' · '+filtered[index]['families'])
    folder=filtered[chosen]['folder']
    try: root,tips,branches=read_group(folder)
    except (OSError,ValueError,IndexError) as error: st.info('This tree is being prepared: '+str(error));return
    if candidates is not None:
        annotations=candidates.set_index('sequence_id').candidate_annotation.to_dict()
        tips['candidate_annotation']=tips.sequence_id.map(annotations).fillna('')
    for col,label,value in zip(st.columns(3),['Tree tips','Candidate tips','Species'],[len(tips),tips.candidate.eq('1').sum(),tips.species.nunique()]):col.metric(label,int(value))
    supports=st.checkbox('Show branch support labels',value=True)
    cladogram=st.checkbox('Equal branch lengths (cladogram)')
    focus=st.text_input('Highlight a tip ID')
    palette=['#08743f','#d08b00','#b91c1c','#1d4ed8','#7e22ce','#db2777','#0891b2','#4d7c0f','#a16207','#4338ca','#0f766e','#be123c','#64748b','#c2410c','#6d28d9','#0369a1','#65a30d','#9f1239','#475569','#9333ea','#713f12']
    for i,sp in enumerate(sorted(tips.species.unique())):
        COLORS[sp]=palette[i%len(palette)]
        parts=sp.removeprefix('Bench_').split('_')
        NAMES[sp]=SPECIES.get(sp,' '.join(parts[:2]) if sp.startswith('Bench_') else sp)
    fig,matched=tree_figure(root,tips,branches,supports,cladogram,focus)
    plotly_chart(fig,width='stretch')
    st.caption('Species colors and candidate diamonds/stars follow tips.tsv. Branch evidence is matched by exact descendant tip sets. The unrooted-tree origin is a display convention. Support labels retain the source IQ-TREE values.')
    st.dataframe(tips,width='stretch',hide_index=True)
    st.dataframe(branches,width='stretch',hide_index=True)
    st.download_button('Download available tree and reproducibility companions',companion_bundle(folder,folder.name),folder.name+'_phylogeny.zip','application/zip')
