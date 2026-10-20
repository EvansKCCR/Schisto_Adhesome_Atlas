"""Curated metazoan evidence projected onto current candidate orthogroups."""
import hashlib
import json
from itertools import product
import networkx as nx
import pandas as pd
import plotly.express as px
import streamlit as st
from data import ROOT
from figure_exports import plotly_chart
from reconstruction import topology,network_matrices
from vector_network import vector_network_html
from topological_clustering import clustering_panel

NET=ROOT/'adhesome_network'

def build_consensus(candidates,reference=None):
    reference=pd.read_csv(NET/'Schistosome_human_reference_family_edges.csv').fillna('') if reference is None else reference.copy()
    members=candidates[candidates.orthogroup.str.fullmatch(r'OG\d+',na=False)].copy()
    join=lambda values:' | '.join(sorted(set(values.dropna().astype(str))-{''}))
    nodes=members.groupby('orthogroup').agg(Family=('family',join),species=('species',join),
      member_count=('sequence_id','nunique'),species_count=('species','nunique'),
      member_ids=('sequence_id',join),annotation=('candidate_annotation',join),layer=('module',join),
      grades=('grade',join)).reset_index().rename(columns={'orthogroup':'identifier'})
    nodes['node']=nodes.identifier
    membership=members.groupby(['family','orthogroup']).sequence_id.agg(lambda values:' | '.join(sorted(set(values)))).to_dict()
    mapping=members.groupby('family').orthogroup.agg(lambda values:sorted(set(values))).to_dict()
    records=[]
    for row in reference.to_dict('records'):
        for left,right in product(mapping.get(row['family_A'],[]),mapping.get(row['family_B'],[])):
            if left==right: continue
            a,b=sorted([left,right])
            records.append(dict(node1_string_id=a,node2_string_id=b,source_family=row['family_A'] if a==left else row['family_B'],target_family=row['family_B'] if a==left else row['family_A'],
              evidence='Metazoan reference family projection',relation=row['interaction_types'],effects=row['effects'],
              reference_pairs=row['human_reference_pairs'],reference_rows=row['original_rows'],PMIDs=row['PMIDs'],
              sources=row['data_sources'],reference_symbols=row['human_symbol_pairs'],source_candidates=membership[(row['family_A'] if a==left else row['family_B'],a)],target_candidates=membership[(row['family_B'] if a==left else row['family_A'],b)]))
    edges=pd.DataFrame(records,columns=['node1_string_id','node2_string_id','source_family','target_family','evidence','relation','effects','reference_pairs','reference_rows','PMIDs','sources','reference_symbols','source_candidates','target_candidates']).drop_duplicates()
    return nodes,edges,members

def consensus_panel(candidates):
    st.subheader('Orthogroup consensus adhesome network')
    st.write('Curated metazoan adhesome interactions are projected through the family crosswalk onto orthogroups in the active catalogue. Each edge retains its reference symbols, interaction types, effects, sources and PMIDs. An edge describes a family-supported orthogroup relationship; it does not resolve individual parasite binding partners.')
    a,b=st.columns(2)
    grades=a.multiselect('Network candidate grades',['A','B','C'],default=['A','B','C'])
    species=b.multiselect('Network species',sorted(candidates.species.unique()),default=sorted(candidates.species.unique()))
    selected=candidates[candidates.grade.isin(grades)&candidates.species.isin(species)]
    families=st.multiselect('Network families',sorted(selected.family.unique()))
    if families: selected=selected[selected.family.isin(families)]
    signature=tuple((p.name,p.stat().st_mtime_ns,p.stat().st_size) for p in NET.glob('*.csv'))
    @st.cache_data(show_spinner=False,max_entries=8)
    def cached_projection(rows,signature): return build_consensus(rows)
    nodes,edges,members=cached_projection(selected,signature)
    if nodes.empty: st.info('No orthogroup members match these filters.'); return
    focus=st.selectbox('Orthogroup neighborhood',['All orthogroups']+sorted(nodes.identifier))
    if focus!='All orthogroups':
        pairs=edges[edges.node1_string_id.eq(focus)|edges.node2_string_id.eq(focus)]
        ids={focus}|set(pairs.node1_string_id)|set(pairs.node2_string_id)
        nodes=nodes[nodes.identifier.isin(ids)]
        edges=edges[edges.node1_string_id.isin(ids)&edges.node2_string_id.isin(ids)]
    if st.checkbox('Hide unconnected consensus nodes',value=False):
        nodes=nodes[nodes.identifier.isin(set(edges.node1_string_id)|set(edges.node2_string_id))]
    if nodes.empty: st.info('No connected orthogroups in this selection.'); return
    @st.cache_data(show_spinner=False,max_entries=8)
    def measured(nodes,edges): return topology(nodes,edges)
    metrics,graph=measured(nodes,edges)
    for col,label,value in zip(st.columns(4),['Orthogroups','Candidate proteins','Projected pairs','Communities'],[len(nodes),members[members.orthogroup.isin(nodes.identifier)].sequence_id.nunique(),graph.number_of_edges(),metrics.community.nunique()]): col.metric(label,value)
    tabs=st.tabs(['Interactive network','Centrality & matrices','Topological clustering','Evidence & downloads'])
    with tabs[0]:
        color=st.selectbox('Consensus node colors',['Family','layer','community'])
        categories=sorted(metrics[color].astype(str).unique());palette=px.colors.qualitative.Dark24
        colors={v:palette[i%len(palette)] for i,v in enumerate(categories)}
        limit=st.slider('Maximum nodes drawn',25,500,200,25)
        visible=metrics.sort_values(['degree','identifier'],ascending=[False,True]).head(limit)
        ids=set(visible.identifier);sub=graph.subgraph(ids)
        positions=nx.spring_layout(sub,seed=20) if len(sub)<=300 else nx.circular_layout(sub)
        vnodes=[dict(id=r.identifier,label=r.identifier,annotation=r.Family,x=float(positions[r.identifier][0]),y=float(positions[r.identifier][1]),radius=12+min(15,r.degree),color=colors[str(getattr(r,color))],category=str(getattr(r,color)),detail={'Families':r.Family,'Candidate count':r.member_count,'Species':r.species,'Grades':r.grades}) for r in visible.itertuples()]
        vedges=[dict(source=a,target=b,detail={'Evidence':'Metazoan reference projection'}) for a,b in sub.edges()]
        st.iframe(vector_network_html(vnodes,vedges,'Orthogroup consensus adhesome',label_mode='centered'),height=810)
        st.caption(f'Drawing {len(visible)} of {len(metrics)} filtered orthogroups, ordered by degree. Centrality, clustering and downloads use the full filtered graph. Drag nodes, adjust label size, center names and export SVG in the viewer.')
    with tabs[1]:
        st.caption('Unweighted undirected topology of the filtered projected graph. Reference evidence row counts are not binding affinities. Closeness uses the disconnected-graph correction; betweenness measures shortest-path brokerage. Centrality supports prioritization and does not establish essentiality.')
        st.dataframe(metrics.sort_values('betweenness',ascending=False),hide_index=True,width='stretch')
        metric=st.selectbox('Rank orthogroups by',['betweenness','closeness','degree','clustering_coefficient','k_core'])
        plotly_chart(px.bar(metrics.nlargest(25,metric),x='identifier',y=metric,color='Family'),width='stretch')
        chosen=st.multiselect('Matrix orthogroups (up to 60)',sorted(graph),default=list(metrics.nlargest(12,'degree').identifier),max_selections=60)
        if chosen:
            distance,adjacency=network_matrices(graph,chosen)
            plotly_chart(px.imshow(adjacency,aspect='auto',title='Adjacency matrix'),width='stretch')
            st.dataframe(distance,width='stretch');st.caption('Shortest-path distances use the full filtered graph; unreachable pairs are blank.')
            st.download_button('Download distances CSV',distance.to_csv(),'orthogroup_distances.csv')
    with tabs[2]: clustering_panel(graph,metrics,'curated_clusters','Orthogroup consensus')
    with tabs[3]:
        st.dataframe(edges,width='stretch',hide_index=True)
        for label,frame,name in [('Orthogroup centrality',metrics,'orthogroup_centrality.csv'),('Projected reference evidence',edges,'orthogroup_reference_edges.csv'),('Candidate membership',members[members.orthogroup.isin(nodes.identifier)],'orthogroup_members.csv')]:st.download_button('Download '+label,frame.to_csv(index=False),name)
        files=[NET/'Schistosome_human_reference_family_edges.csv',NET/'Schistosome_human_gene_family_crosswalk.csv',NET/'interactions.csv',ROOT/'files/adhesome_candidates_list.xlsx']
        st.download_button('Download projection provenance',json.dumps({'model':'Metazoan family projection onto current orthogroups','grades':grades,'species':species,'families':families,'inputs':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2),'consensus_provenance.json')
