from atlas_paths import phylogeny_root
"""Source-preserving IQ-TREE viewer; internal annotations join by tip sets."""
from dataclasses import dataclass, field
from html import escape
from io import BytesIO
from pathlib import Path
import json
import re
import zipfile
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data import ROOT,SPECIES
from candidate_profiles import atlas_url


from figure_exports import plotly_chart, selected_export_config



KEEP = ('tips.tsv', 'inference/gene_tree.treefile', 'inference/trimmed.faa',
        'inference/gene_tree.iqtree', 'inference/branch_evidence.tsv', 'inference/run.json')
COMPANION_ALIASES = {
    'gene_tree.treefile': ('gene_tree.treefile', 'tree.treefile'),
    'gene_tree.iqtree': ('gene_tree.iqtree', 'tree.iqtree'),
    'trimmed.faa': ('trimmed.faa', 'trimmed.fasta', 'trimed.fasta'),
}
COLORS = {'Shae':'#008b8b','Sjap':'#d98632','Sman':'#7665bc','Hsap':'#b65179','Cele':'#628049','Mmus':'#3975b5','Xlae':'#a56b23','Dmel':'#cf4750'}
NAMES = {'Shae':'S. haematobium','Sjap':'S. japonicum','Sman':'S. mansoni',
         'Hsap':'H. sapiens','Cele':'C. elegans','Mmus':'M. musculus','Xlae':'X. laevis','Dmel':'D. melanogaster'}
FAMILY_COLLECTION = 'Family-level phylogeny'
FAMILY_VIEW = 'Family-level phylogenies'
ORTHOGROUP_VIEW = 'Orthogroup trees'
FAMILY_NAMES = {'integrin_alpha':'Integrin α','integrin_beta':'Integrin β',
                'alpha_actinin':'α-actinin','paxillin_like':'Paxillin','PINCH_like':'PINCH',
                'PTP_PEST':'PTP-PEST','collagen_like':'Collagen-like','laminin_like':'Laminin-like',
                'zyxin_like':'Zyxin','kindlin':'Kindlin','cofilin':'Cofilin','filamin':'Filamin',
                'talin':'Talin','vinculin':'Vinculin','fes_fps_like':'Fes/Fps-like',
                'rho_gtpase_like':'Rho GTPase-like','src_like':'Src-like',
                'spectrin_like':'Spectrin-like','tubulin_like':'Tubulin-like',
                'adf_cofilin':'ADF/cofilin','profilin_like':'Profilin-like',
                'actin':'Actin','hsp70_like':'HSP70-like'}

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
    bases=[phylogeny_root(root), Path(root)/'family_phylogeny']
    names=COMPANION_ALIASES['gene_tree.treefile']
    found={p for base in bases for name in names for p in base.rglob(name) if p.is_file()}
    folders=sorted({p.parent.parent if p.parent.name=='inference' else p.parent for p in found})
    trees=[]; incomplete=[]
    for folder in folders:
        tree=companion_path(folder,'inference/gene_tree.treefile')
        trees.append(tree)
        missing=[name for name in KEEP if not companion_path(folder,name).is_file()]
        if missing: incomplete.append({'tree':str(tree),'missing':', '.join(missing)})
    return folders,incomplete,trees


def companion_path(folder, relative):
    """Resolve legacy and family-run filenames in nested or flat layouts."""
    folder=Path(folder)
    requested=Path(relative)
    names=COMPANION_ALIASES.get(requested.name,(requested.name,))
    for name in names:
        for parent in dict.fromkeys((requested.parent,Path('.'),Path('inference'))):
            path=folder/parent/name
            if path.is_file(): return path
    return folder/requested


def companion_bundle(folder, export_name):
    """Package only the six original visualization and reproducibility files."""
    bundle=BytesIO()
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        for relative in KEEP:
            path=companion_path(folder,relative)
            if path.is_file():
                # Preserve actual filenames and the original flat/nested layout.
                archive.write(path,f'{export_name}/{path.relative_to(folder).as_posix()}')
    return bundle.getvalue()


def tip_metadata(folder, candidates=None, root=None):
    """Read either tip-table schema, retaining every original annotation column."""
    tip_path=companion_path(folder,'tips.tsv')
    tips=pd.read_csv(tip_path,sep='\t',dtype=str).fillna('') if tip_path.exists() else pd.DataFrame(
        [{'sequence_id':node.name} for node in layout(root)[2]] if root is not None else [],columns=['sequence_id'])
    if 'species' not in tips:
        tips['species']=tips['panel_label'] if 'panel_label' in tips else tips.sequence_id.map(lambda name:name.partition('__')[0])
    if 'length' not in tips and 'length_aa' in tips: tips['length']=tips.length_aa
    if 'candidate' not in tips:
        ids=set(candidates.sequence_id) if candidates is not None else set()
        tips['candidate']=tips.sequence_id.isin(ids).astype(int).astype(str)
    if 'display_label' not in tips: tips['display_label']=tips.sequence_id
    return tips


def read_group(folder, candidates=None):
    root = parse_newick(companion_path(folder,'inference/gene_tree.treefile').read_text(encoding='utf-8'))
    tips=tip_metadata(folder,candidates,root)
    tips['in_tree']=tips.sequence_id.isin({node.name for node in layout(root)[2]})
    branch_path=companion_path(folder,'inference/branch_evidence.tsv')
    branches=pd.read_csv(branch_path,sep='\t',dtype=str).fillna('') if branch_path.exists() else pd.DataFrame(columns=['branch_id','support_label','tip_ids','interpretation'])
    return root,tips,branches

def tree_collection(folder):
    """Use recorded analysis provenance, not candidate names, to group trees."""
    if 'family_phylogeny' in folder.parts: return FAMILY_COLLECTION
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
    tips=tip_metadata(folder,candidates)
    families=sorted(set(tips.family)-{''}) if 'family' in tips else [folder.name.removeprefix('family_')]
    groups=sorted({group for value in tips.get('source_groups',tips.get('source_orthogroup',pd.Series(dtype=str)))
                   for group in re.split(r'[,;|\s]+',value) if group})
    matches=pd.DataFrame()
    if candidates is not None and 'sequence_id' in candidates:
        ids=set(tips.sequence_id)
        matches=candidates[candidates.sequence_id.isin(ids)]
    modules=sorted(set(matches.module.dropna().astype(str))) if not matches.empty and 'module' in matches else []
    return {'folder':folder,'orthogroup':folder.name,'families':[FAMILY_NAMES.get(f,f) for f in families],
            'modules':modules or ['Unassigned module'],'collection':FAMILY_COLLECTION,
            'source_orthogroups':groups,'tree_level':'Joint family tree'}, matches


def tree_records(folders, candidates=None):
    """Keep family inference runs separate from source orthogroup trees."""
    records=[]
    for folder in folders:
        family_run=tree_collection(folder)==FAMILY_COLLECTION
        if family_run:
            metadata,_=family_run_metadata(folder,candidates)
            families=metadata['families'];groups=metadata['source_orthogroups']
        else:
            families=sorted(set(candidates.loc[candidates.orthogroup.eq(folder.name),'family'].dropna())) if candidates is not None else []
            groups=[folder.name]
        records.append(dict(folder=folder,orthogroup=folder.name,families=' | '.join(families),
            source_orthogroups=groups,level=FAMILY_VIEW if family_run else ORTHOGROUP_VIEW))
    return records


def linked_tree_candidates(root,tips,candidates,app_url=''):
    """Join exact tree/input IDs to every catalogue record, without family guessing."""
    leaves={node.name for node in layout(root)[2]}
    ids=leaves|set(tips.sequence_id)
    linked=candidates[candidates.sequence_id.isin(ids)].copy()
    linked['in_tree']=linked.sequence_id.isin(leaves)
    linked['Protein dossier']=linked.sequence_id.map(lambda protein:atlas_url(app_url,'Protein dossier',protein))
    return linked


def candidate_profiles_panel(root,tips,candidates,app_url,folder,expanded=False):
    if candidates is None: return ''
    linked=linked_tree_candidates(root,tips,candidates,app_url)
    with st.expander(f'Linked candidate profiles ({linked.sequence_id.nunique():,})',expanded=expanded):
        if linked.empty:
            st.info('No candidate protein identifiers in this tree or its tip table match the Atlas catalogue. To be updated when additional information is available.')
            return ''
        st.caption(f'{len(linked):,} catalogue records / {linked.sequence_id.nunique():,} proteins linked by exact sequence IDs. '
            'Family annotations and grades retain their catalogue values. Open a dossier to explore domains, motifs, topology, orthology and sequences.')
        columns=[name for name in ['sequence_id','species','family','grade','audit_classification',
            'candidate_annotation','in_tree','Protein dossier'] if name in linked]
        st.dataframe(linked[columns],hide_index=True,width='stretch',height=min(440,len(linked)*35+40),
            column_config={'Protein dossier':st.column_config.LinkColumn('Protein dossier',display_text='Open dossier ↗'),
                'in_tree':st.column_config.CheckboxColumn('In displayed tree')})
        key='phylogeny_candidate_'+folder.as_posix()
        choices=['']+sorted(linked.sequence_id.unique())
        if st.session_state.get(key,'') not in choices:st.session_state.pop(key,None)
        protein=st.selectbox('Highlight a linked candidate',choices,key=key,
            format_func=lambda value:value or 'Choose a candidate')
        if protein:
            records=linked[linked.sequence_id.eq(protein)]
            st.link_button('Open selected candidate dossier ↗',atlas_url(app_url,'Protein dossier',protein))
            if not records.in_tree.any():
                st.info('This candidate is recorded in tips.tsv but is absent from the inferred tree. Its complete catalogue profile is available.')
        st.download_button('Download linked candidate profiles',linked.to_csv(index=False),
            folder.name+'_candidate_profiles.csv','text/csv',key='phylogeny_candidates_download_'+folder.as_posix())
        return protein

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


def phylogeny_panel(candidates=None,app_url=None):
    # Retain controls from the inactive collection when Streamlit cleans up
    # widgets that are not rendered during this run.
    for key in list(st.session_state):
        if key.startswith(('phylogeny_family_','phylogeny_orthogroup_','phylogeny_candidate_')):
            st.session_state[key]=st.session_state[key]
    st.subheader('Phylogenetic evidence explorer')
    st.caption('Trees are discovered recursively from Phylogeny and family_phylogeny on every refresh. Add gene_tree.treefile or tree.treefile and available companions; completed trees appear automatically. Partial runs remain visible with missing companions listed. Source orthogroups are preserved exactly.')
    folders,incomplete,trees=discover_trees()
    if not folders: st.info('No gene_tree.treefile or tree.treefile is present yet. To be updated when additional phylogeny files are available.'); return
    info=tree_records(folders,candidates)
    route_group=st.session_state.pop('phylogeny_route_group',None)
    if route_group:
        routed=next((r for r in info if r['orthogroup']==route_group),None)
        level=routed['level'] if routed else ORTHOGROUP_VIEW
        st.session_state['phylogeny_level']=level
        scope='family' if level==FAMILY_VIEW else 'orthogroup'
        st.session_state['phylogeny_'+scope+'_query']=route_group
    if st.session_state.get('phylogeny_level') not in {FAMILY_VIEW,ORTHOGROUP_VIEW}:
        st.session_state['phylogeny_level']=FAMILY_VIEW if any(r['level']==FAMILY_VIEW for r in info) else ORTHOGROUP_VIEW
    level=st.radio('Tree collection',[FAMILY_VIEW,ORTHOGROUP_VIEW],horizontal=True,key='phylogeny_level')
    scope='family' if level==FAMILY_VIEW else 'orthogroup'
    counts={name:sum(r['level']==name for r in info) for name in (FAMILY_VIEW,ORTHOGROUP_VIEW)}
    st.caption(f'{counts[FAMILY_VIEW]} family-level trees · {counts[ORTHOGROUP_VIEW]} orthogroup trees. Each collection has its own search and tree selection.')
    active=[record for record in info if record['level']==level]
    active_trees={str(companion_path(r['folder'],'inference/gene_tree.treefile')) for r in active}
    pending=[record for record in incomplete if record['tree'] in active_trees]
    if pending:
        with st.expander('Companion files awaiting addition'):st.dataframe(pd.DataFrame(pending),hide_index=True,width='stretch')
    if not active:
        st.info('No completed '+('family-level' if level==FAMILY_VIEW else 'orthogroup')+' tree is present yet. New tree files will appear automatically.');return
    query=st.text_input('Find a family, source orthogroup or protein' if level==FAMILY_VIEW else 'Find an orthogroup, protein family or protein',key='phylogeny_'+scope+'_query')
    filtered=[]
    for record in active:
        tips_path=companion_path(record['folder'],'tips.tsv')
        text=record['orthogroup']+' '+record['families']
        if tips_path.exists(): text+=' '+tips_path.read_text(encoding='utf-8')
        if not query or query.casefold() in text.casefold(): filtered.append(record)
    st.caption(f'{len(filtered)} of {len(active)} trees in this collection')
    if not filtered: st.info('No matching phylogenetic groups.');return
    choices={str(record['folder']):record for record in filtered}
    key='phylogeny_'+scope+'_tree'
    if st.session_state.get(key) not in choices:st.session_state.pop(key,None)
    chosen=st.selectbox('Family-level phylogeny' if level==FAMILY_VIEW else 'Phylogenetic orthogroup',list(choices),
        key=key,format_func=lambda path:choices[path]['families']+' · '+choices[path]['orthogroup'] if level==FAMILY_VIEW else choices[path]['orthogroup']+' · '+choices[path]['families'])
    record=choices[chosen];folder=record['folder']
    st.subheader(record['families'] or record['orthogroup'])
    if level==FAMILY_VIEW and record['source_orthogroups']:
        st.caption('Source orthogroups: '+', '.join(record['source_orthogroups']))
    try: root,tips,branches=read_group(folder,candidates)
    except (OSError,ValueError,IndexError) as error: st.info('This tree is being prepared: '+str(error));return
    if candidates is not None:
        annotations=candidates.set_index('sequence_id').candidate_annotation.to_dict()
        tips['candidate_annotation']=tips.sequence_id.map(annotations).fillna('')
    st.caption('Tree source: '+str(companion_path(folder,'inference/gene_tree.treefile').relative_to(ROOT)))
    visible_tips=tips[tips.in_tree]
    for col,label,value in zip(st.columns(3),['Tree tips','Candidate tips','Species'],[len(layout(root)[2]),visible_tips.candidate.eq('1').sum(),visible_tips.species.nunique()]):col.metric(label,int(value))
    if not tips.in_tree.all():
        st.caption(f'{int((~tips.in_tree).sum())} tip-table records are absent from the inferred tree. All records are retained below with their in_tree status; summary counts describe the visible tree.')
    selected_candidate=candidate_profiles_panel(root,tips,candidates,
        (st.context.url or '') if app_url is None else app_url,folder,expanded=level==FAMILY_VIEW)
    supports=st.checkbox('Show branch support labels',value=True)
    cladogram=st.checkbox('Equal branch lengths (cladogram)')
    focus=st.text_input('Highlight a tip ID')
    if selected_candidate:focus=selected_candidate
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
