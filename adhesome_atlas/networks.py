"""STRING export integration. No inferred identifier aliases or interaction edges."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data import ROOT, SPECIES

def node_links(code,nodes,candidates):
    """Exact, species-scoped identifier tokens only; ambiguous aliases stay unresolved."""
    path=ROOT/'adhesome_network'/code/f'{code}_string_protein_annotations.tsv'
    aliases={}
    if path.exists():
        source=pd.read_csv(path,sep='\t').fillna('')
        aliases=source.set_index('identifier').other_names_and_aliases.to_dict()
    known=set(candidates.sequence_id)
    rows=[]
    for r in nodes.itertuples():
        direct=code+'__'+r.node
        matches={code+'__'+token.strip() for token in aliases.get(r.identifier,'').split(',') if code+'__'+token.strip() in known}
        if direct in known:matches.add(direct)
        seq=next(iter(matches)) if len(matches)==1 else ''
        rows.append({'identifier':r.identifier,'sequence_id':seq,'mapping_basis':('Exact node identifier' if seq==direct else 'Exact STRING alias token') if seq else ('Ambiguous alias matches' if matches else 'Unmapped'), 'mapping_candidates':' | '.join(sorted(matches))})
    return pd.DataFrame(rows)

def load_network(code, candidates):
    folder = ROOT / 'adhesome_network' / code
    nodes = pd.read_csv(folder / f'{code}_string_coordinates.tsv', sep='\t').rename(columns={'#node':'node'})
    nodes=nodes.merge(node_links(code,nodes,candidates),on='identifier',validate='one_to_one')
    edges = pd.read_csv(folder / f'{code}_string_interactions.tsv', sep='\t').rename(columns={'#node1':'node1'})
    annotations = pd.read_csv(folder / f'{code}_string_functional_annotations.tsv', sep='\t').rename(columns={'#node':'node'})
    edges['pair'] = [tuple(sorted((a,b))) for a,b in zip(edges.node1_string_id, edges.node2_string_id)]
    edges = edges.sort_values('combined_score',ascending=False).drop_duplicates('pair').drop(columns='pair')
    exact = candidates[candidates.sequence_id.str.startswith(code+'__')].copy()
    exact['node'] = exact.sequence_id.str.split('__').str[-1]
    family = exact.groupby('node').family.agg(lambda x:' | '.join(sorted(set(x.dropna()))))
    nodes['Family'] = nodes.sequence_id.str.removeprefix(code+'__').map(family).fillna('Unmapped')
    if 'DeepLoc_2.1' in exact:
        loc = exact.groupby('node')['DeepLoc_2.1'].agg(lambda x:' | '.join(sorted(set(x.dropna()))))
        nodes['DeepLoc localization'] = nodes.sequence_id.str.removeprefix(code+'__').map(loc).replace('',pd.NA).fillna('Unmapped')
    compartment = annotations[annotations.category.eq('COMPARTMENTS')].groupby('identifier')['term description'].agg(lambda x:' | '.join(sorted(set(x.dropna()))))
    nodes['STRING localization'] = nodes.identifier.map(compartment).fillna('Unannotated')
    return nodes, edges, annotations

def network_panel(candidates, key, detailed=False):
    st.caption('STRING associations from the supplied exports. These can include functional associations and transferred evidence; they do not by themselves establish direct physical binding in schistosomes. Network controls are independent of component filters.')
    a,b,c = st.columns(3)
    code = a.selectbox('Network species', list(SPECIES), format_func=SPECIES.get, key=key+'species')
    color_by = b.selectbox('Node colors', ['STRING localization','Family','DeepLoc localization','Original STRING colors'], key=key+'color')
    threshold = c.slider('Minimum combined score', 0.0,1.0,0.4,0.01,key=key+'score')
    nodes, edges, annotations = load_network(code,candidates)
    color_field = color_by
    if color_by == 'STRING localization':
        terms = sorted(annotations.loc[annotations.category.eq('COMPARTMENTS'),'term description'].dropna().unique())
        if terms:
            default_term = terms.index('Cytoskeleton') if 'Cytoskeleton' in terms else 0
            term = st.selectbox('Highlight a reported compartment',terms,index=default_term,key=key+'compartment')
            annotated_ids = set(annotations.loc[annotations.category.eq('COMPARTMENTS') & annotations['term description'].eq(term),'identifier'])
            nodes['Compartment highlight'] = nodes.identifier.map(lambda identifier: term if identifier in annotated_ids else 'Other / not annotated for this term')
            color_field = 'Compartment highlight'
    edges = edges[edges.combined_score.ge(threshold)].copy()
    focus = st.selectbox('Focus on a protein and its neighbors', ['All nodes']+sorted(nodes.node), key=key+'focus')
    if focus != 'All nodes':
        edges = edges[edges.node1.eq(focus)|edges.node2.eq(focus)]
        names = set(edges.node1)|set(edges.node2)|{focus}
        nodes = nodes[nodes.node.isin(names)].copy()
    show_isolates = st.checkbox('Show isolated nodes',value=True,key=key+'isolates')
    degree = pd.concat([edges.node1_string_id,edges.node2_string_id]).value_counts()
    nodes['filtered_degree'] = nodes.identifier.map(degree).fillna(0).astype(int)
    if not show_isolates:
        nodes = nodes[nodes.filtered_degree.gt(0)]
    labels = st.checkbox('Show node labels',value=False,key=key+'labels')
    for col,label,value in zip(st.columns(4),['Displayed proteins','Unique associations','Isolated proteins','Exact family matches'],[len(nodes),len(edges),int(nodes.filtered_degree.eq(0).sum()),int(nodes.Family.ne('Unmapped').sum())]):
        col.metric(label,value)
    if nodes.empty:
        st.info('No network nodes remain at these settings. Lower the score or show isolated nodes.')
    else:
        positions = nodes.set_index('identifier')[['x_position','y_position']].to_dict('index')
        xs,ys=[],[]
        for r in edges.itertuples():
            if r.node1_string_id in positions and r.node2_string_id in positions:
                p,q=positions[r.node1_string_id],positions[r.node2_string_id]
                xs.extend([p['x_position'],q['x_position'],None]); ys.extend([p['y_position'],q['y_position'],None])
        fig=go.Figure(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color='#bdcbd4',width=1),hoverinfo='skip',showlegend=False))
        grouping = nodes.assign(group='Source colors') if color_by=='Original STRING colors' else nodes.assign(group=nodes[color_field])
        all_categories = sorted(grouping.group.unique())
        colors = {name:px.colors.qualitative.Alphabet[i%26] for i,name in enumerate(all_categories)}
        for category,group in grouping.groupby('group'):
            fig.add_trace(go.Scatter(x=group.x_position,y=group.y_position,mode='markers+text' if labels else 'markers',text=group.node,textposition='top center',name=category,marker=dict(size=9+group.filtered_degree.pow(.5)*2,color=group.color.tolist() if color_by=='Original STRING colors' else ('#9aa5ae' if category in ['Unmapped','Unannotated'] else colors[category]),line=dict(color='white',width=1)),customdata=group[['node','identifier','Family','STRING localization','filtered_degree','annotation']].fillna('').values,hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>Family: %{customdata[2]}<br>Compartment: %{customdata[3]}<br>Degree: %{customdata[4]}<br>%{customdata[5]}<extra></extra>'))
        fig.update_layout(height=650,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis=dict(visible=False),yaxis=dict(visible=False,autorange='reversed',scaleanchor='x'),margin=dict(l=0,r=0,t=10,b=0),legend=dict(orientation='h',y=-.05),hoverlabel=dict(namelength=-1))
        st.plotly_chart(fig,width='stretch',key=key+'graph',config={'displaylogo':False})
    st.caption('Positions retain the supplied STRING layout; node size reflects degree after filtering. Family and DeepLoc labels require an exact species-qualified catalogue ID or unique exact STRING alias match. STRING localization highlights membership in the chosen reported compartment; all compartment terms remain in hover details and the protein table. An unreported term is not evidence of biological absence. Gray family/DeepLoc nodes are unmapped. Full and short edge exports are not combined.')
    if detailed:
        tabs=st.tabs(['Interaction table','Protein table','Functional annotations','Network statistics'])
        with tabs[0]:
            st.dataframe(edges,width='stretch',hide_index=True)
            st.download_button('↓ Filtered interactions · CSV',edges.to_csv(index=False),code+'_interactions.csv',key=key+'edges')
        with tabs[1]:
            st.dataframe(nodes,width='stretch',hide_index=True)
            st.download_button('↓ Displayed proteins · CSV',nodes.to_csv(index=False),code+'_nodes.csv',key=key+'nodes')
        with tabs[2]:
            st.dataframe(annotations[annotations.identifier.isin(nodes.identifier)],width='stretch',hide_index=True)
            extra_resources(code,nodes,key)
        with tabs[3]:
            n=len(nodes); m=len(edges)
            st.write(f'Undirected density: {2*m/(n*(n-1)) if n>1 else 0:.3f} · Mean degree: {nodes.filtered_degree.mean() if n else 0:.2f}')
            if n:
                st.plotly_chart(px.bar(nodes.nlargest(15,'filtered_degree'),x='node',y='filtered_degree',title='Most connected displayed proteins'),width='stretch',key=key+'degree')

def extra_resources(code,nodes,key):
    folder=ROOT/'adhesome_network'/code
    protein=folder/f'{code}_string_protein_annotations.tsv'
    if protein.exists():
        st.markdown('#### Protein annotations and identifier aliases')
        data=pd.read_csv(protein,sep='\t')
        st.caption('Original export columns are preserved. In these files, annotation text and domain-summary URLs appear under swapped headers; identifier mapping uses only exact alias tokens.')
        st.dataframe(data[data.identifier.isin(nodes.identifier)],width='stretch',hide_index=True)
    enrichment=list(folder.glob('*.all'))
    if enrichment:
        st.markdown('#### Supplied network enrichment')
        st.caption('Statistics describe the original exported network and background. They are not recomputed for the displayed subnetwork and do not establish individual protein membership.')
        for path in enrichment:
            data=pd.read_csv(path,sep='\t')
            cutoff=st.slider('Maximum reported FDR',0.0,1.0,.05,.01,key=key+path.name+'fdr')
            selected=data[pd.to_numeric(data['false discovery rate'],errors='coerce').le(cutoff)]
            st.dataframe(selected,width='stretch',hide_index=True)
    xml=folder/f'{code}_string_interactions_psimi.xml'
    if xml.exists():
        from xml.etree import ElementTree as ET
        tree=ET.parse(xml);ns={'mi':'net:sf:psidev:mi'}
        rows=[]
        for exp in tree.findall('.//mi:experimentDescription',ns):
            rows.append({'experiment_id':exp.get('id'),'channel':exp.findtext('mi:names/mi:shortLabel',namespaces=ns),'description':exp.findtext('mi:names/mi:fullName',namespaces=ns),'references':'; '.join(f"{ref.get('db')}:{ref.get('id')}" for ref in exp.findall('mi:bibref/mi:xref/*',ns))})
        st.markdown('#### PSI-MI export evidence channels')
        st.caption('Alternative serialization of the supplied STRING evidence; XML interactions are not added again as new graph edges.')
        st.dataframe(pd.DataFrame(rows),width='stretch',hide_index=True)
        st.download_button('Download original PSI-MI XML',xml.read_bytes(),xml.name,key=key+'xml')
