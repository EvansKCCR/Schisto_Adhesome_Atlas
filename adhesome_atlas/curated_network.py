"""Curated metazoan evidence projected onto current candidate orthogroups."""
import hashlib
import json
from itertools import product
import pandas as pd
import plotly.express as px
import streamlit as st
from data import ROOT
from figure_exports import plotly_chart
from reconstruction import topology,network_matrices
from consensus_view import build_view_model,consensus_network_html,layout_table,layout_signature
from topological_clustering import clustering_panel
from library_refresh import reference_family_edges

NET=ROOT/'adhesome_network'

def build_consensus(candidates,reference=None):
    reference=reference_family_edges(ROOT) if reference is None else reference.copy()
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
    grades=a.multiselect('Network candidate grades',['A','B','C','D'],default=['A','B','C','D'],help='A/B supported; C provisional; D unassigned. D records are retained as unassigned and do not acquire a family through reference transfer.')
    species=b.multiselect('Network species',sorted(candidates.species.unique()),default=sorted(candidates.species.unique()))
    selected=candidates[candidates.grade.isin(grades)&candidates.species.isin(species)]
    families=st.multiselect('Network families',sorted(selected.family.unique()))
    if families: selected=selected[selected.family.isin(families)]
    missing_groups=int((~selected.orthogroup.str.fullmatch(r'OG\d+',na=False)).sum())
    if missing_groups:st.caption(f'{missing_groups:,} selected catalogue records have no assigned orthogroup. They remain available in Components and Protein dossier; no artificial orthogroup nodes are created.')
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
    section=st.selectbox('Network analysis section',['Interactive network','Centrality & matrices','Topological clustering','Evidence & downloads'])
    if section=='Interactive network':
        @st.cache_data(show_spinner='Organizing annotation-informed network regions…',max_entries=8)
        def presentation(metrics,edges,members,rules_signature):return build_view_model(metrics,edges,members)
        model=presentation(metrics,edges,members,layout_signature())
        html=consensus_network_html(model,st.context.url or '')
        st.iframe(html,height=1200)
        st.caption(f'All {len(metrics):,} filtered orthogroups and {graph.number_of_edges():,} original projected pairs are retained. Layout, module focus and local hiding affect presentation only. Select a node for its complete filtered candidate membership, prediction evidence and recorded neighbors. Read labels, zoom or search for detailed exploration; overview labels suppress collisions.')
        a,b,c=st.columns(3)
        a.download_button('Download interactive consensus HTML',html,'orthogroup_consensus_interactive.html','text/html')
        b.download_button('Download spatial annotation & coordinates',layout_table(model).to_csv(index=False),'orthogroup_spatial_layouts.csv','text/csv')
        c.download_button('Download layout annotation rules',json.dumps({'rule_version':model['rule_version'],'graph_sha256':model['graph_sha256'],'rules':model['rules']},indent=2),'orthogroup_layout_rules.json','application/json')
    if section=='Centrality & matrices':
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
    if section=='Topological clustering': clustering_panel(graph,metrics,'curated_clusters','Orthogroup consensus')
    if section=='Evidence & downloads':
        st.dataframe(edges,width='stretch',hide_index=True)
        for label,frame,name in [('Orthogroup centrality',metrics,'orthogroup_centrality.csv'),('Projected reference evidence',edges,'orthogroup_reference_edges.csv'),('Candidate membership',members[members.orthogroup.isin(nodes.identifier)],'orthogroup_members.csv')]:st.download_button('Download '+label,frame.to_csv(index=False),name)
        files=[NET/'Schistosome_human_reference_family_edges.csv',NET/'Schistosome_human_gene_family_crosswalk.csv',NET/'interactions.csv',ROOT/'files/adhesome_candidates_list.xlsx']
        st.download_button('Download projection provenance',json.dumps({'model':'Metazoan family projection onto current orthogroups','grades':grades,'species':species,'families':families,'inputs':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2),'consensus_provenance.json')
