"""One analysis workspace for API-fetched, single-upload and batch-upload STRING graphs."""
import hashlib
import io
import json
import zipfile

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from data import SPECIES
from figure_exports import plotly_chart
from networks import mapping_export
from string_analysis import (VERSION,PATH_LIMIT,NODE_METRICS,analyze_network,analysis_graph,
    all_clusterings,matrices,bundle,json_ready,network_id,migrate_networks)
from topological_clustering import clustering_panel
from vector_network import vector_network_html

SECTIONS=['Interactive network','Network overview','Centrality & clusters','Topological clustering',
          'Components & robustness','Interactions & mapping','Matrices','Query provenance']


def prepare_nodes(state,candidates):
    from string_workbench import annotations_for_nodes,TAXA
    code=state['code'];taxon=state.get('taxon') or TAXA.get(code,0);edges=state['edges']
    ids=set(edges.node1_string_id)|set(edges.node2_string_id)|set(state.get('resolved',{}).values())
    nodes=annotations_for_nodes(ids,candidates,mapping_export(code),state['plan'],state.get('resolved',{}),code,taxon)
    labels=dict(zip(edges.node1_string_id,edges.node1))|dict(zip(edges.node2_string_id,edges.node2))
    nodes['node']=nodes.identifier.map(labels).fillna(nodes.identifier)
    return nodes


@st.cache_data(show_spinner='Computing STRING network topology…',max_entries=16)
def measured(nodes,edges,exact_paths):return analyze_network(nodes,edges,exact_paths)


@st.cache_data(show_spinner='Comparing applicable clustering algorithms…',max_entries=12)
def compared(nodes,edges):
    graph=nx.Graph();graph.add_nodes_from(nodes)
    graph.add_edges_from(edges)
    return all_clusterings(graph)


def _positions(graph,layout):
    if layout=='Force-directed':return nx.spring_layout(graph,seed=23,weight=None)
    if layout=='Circular':return nx.circular_layout(graph)
    positions={}
    for index,component in enumerate(sorted(nx.connected_components(graph),key=lambda g:(-len(g),sorted(g)))):
        local=graph.subgraph(component)
        local_positions=nx.spring_layout(local,seed=23,weight=None) if len(local)<=400 else nx.circular_layout(local)
        center=np.array([3*(index%4),-3*(index//4)])
        positions.update({node:center+.9*coordinate for node,coordinate in local_positions.items()})
    return positions


def analysis_panel(state,candidates,key='string_import_'):
    code=state['code'];key+=network_id(state)+'_'
    st.markdown('### Imported STRING network · topology and communities')
    st.caption('Source: '+state['source']+' · '+SPECIES[code]+' · '+state.get('network_type','User-declared network type')+
        '. All imported scores are retained initially. Original source files remain unchanged.')
    a,b,c=st.columns(3)
    threshold=a.slider('Imported minimum combined score',0.,1.,0.,.01,key=key+'threshold')
    hide=b.checkbox('Hide unconnected imported nodes',value=False,key=key+'isolates')
    color_by=c.selectbox('Imported node colors',['Family','orthogroup','community','component','articulation_point'],key=key+'color')
    nodes=prepare_nodes(state,candidates);edges=state['edges']
    options=sorted(nodes.Family.unique());family_key=key+'families'
    if family_key in st.session_state:st.session_state[family_key]=[f for f in st.session_state[family_key] if f in options]
    families=st.multiselect('Filter imported families',options,key=family_key)
    if families:nodes=nodes[nodes.Family.isin(families)]
    focus_options=['All proteins']+sorted(nodes.identifier)
    if st.session_state.get(key+'focus','All proteins') not in focus_options:st.session_state[key+'focus']='All proteins'
    focus=st.selectbox('Imported protein neighborhood',focus_options,key=key+'focus')
    edges=edges[edges.combined_score.ge(threshold)&edges.node1_string_id.isin(nodes.identifier)&edges.node2_string_id.isin(nodes.identifier)].copy()
    if focus!='All proteins':
        ids={focus}|set(edges.loc[edges.node1_string_id.eq(focus),'node2_string_id'])|set(edges.loc[edges.node2_string_id.eq(focus),'node1_string_id'])
        nodes=nodes[nodes.identifier.isin(ids)];edges=edges[edges.node1_string_id.isin(ids)&edges.node2_string_id.isin(ids)]
    if hide:nodes=nodes[nodes.identifier.isin(set(edges.node1_string_id)|set(edges.node2_string_id))]
    if nodes.empty:st.info('No nodes remain. Lower the score or show unconnected nodes.');return
    exact=None
    if len(nodes)>PATH_LIMIT:
        exact=st.checkbox('Calculate exact path metrics on this large network',value=False,key=key+'exact',
            disabled=len(nodes)>5000,help='Above 2,000 nodes, default betweenness uses 256 sampled sources. Exact path metrics may take time; filter first. The exact option is bounded to 5,000 nodes.')
    result=measured(nodes,edges,exact);metrics=result['nodes'];graph=analysis_graph(result);counts=result['summary']
    source_info={'source':state['source'],'species':code,'network_type':state.get('network_type'),
        'input_sha256':hashlib.sha256(state['raw'].encode()).hexdigest(),'query':state.get('provenance',{}),
        'filters':{'minimum_score':threshold,'families':families,'neighborhood':focus,'hide_isolates':hide}}
    for column,label,value in zip(st.columns(4),['Proteins','Unique pairs','Components','Communities'],
            [counts['nodes'],counts['edges'],counts['components'],counts['communities'] if counts['communities'] is not None else 'Unavailable']):column.metric(label,value)
    section=st.selectbox('Imported network section',SECTIONS,key=key+'section')
    if result['provenance']['notes']:
        with st.expander('Metric availability and computation limits'):
            for note in result['provenance']['notes']:st.write(note)
    st.caption('All sections recalculate on the same filtered undirected graph. STRING confidence is used for strength and confidence-weighted PageRank; shortest paths use hops. Component eigenvector values are comparable within each component.')
    if section=='Interactive network':
        layouts=['Force-directed','Component islands','Circular'] if len(graph)<=400 else ['Component islands','Circular']
        layout=st.selectbox('Imported layout',layouts,key=key+'layout')
        positions=_positions(graph,layout);categories=metrics[color_by].fillna('Unavailable').astype(str)
        colors={value:px.colors.qualitative.Alphabet[i%26] for i,value in enumerate(sorted(categories.unique()))}
        vector_nodes=[]
        for row,category in zip(metrics.to_dict('records'),categories):
            node=row['identifier'];detail={field:row[field] for field in ['Family','orthogroup','sequence_id','mapping_status']+NODE_METRICS if field in row}
            vector_nodes.append({'id':node,'label':row['node'],'annotation':row['candidate_annotation'],
                'x':float(positions[node][0]),'y':float(positions[node][1]),'radius':9+math_sqrt(row['degree'])*2,
                'color':colors[category],'category':category,'detail':json_ready(detail)})
        vector_edges=[{'source':row.node1_string_id,'target':row.node2_string_id,'width':1+2*row.combined_score,
            'color':'#b91c1c' if row.bridge else '#9bad9f'} for row in result['edges'].itertuples()]
        html=vector_network_html(vector_nodes,vector_edges,SPECIES[code]+' · imported STRING',label_mode='centered')
        st.iframe(html,height=950)
        st.download_button('Download imported interactive network',html,'string_imported_network.html','text/html',key=key+'html')
        st.caption('Red edges are graph bridges. All displayed nodes are retained; large graphs use component/circular layouts without a SciPy dependency.')
    elif section=='Network overview':
        st.dataframe(pd.DataFrame([{'Metric':name,'Value':value} for name,value in counts.items()]).astype({'Value':str}),hide_index=True,width='stretch')
        degree_counts=metrics.degree.value_counts().sort_index().rename_axis('Degree').reset_index(name='Proteins')
        plotly_chart(px.bar(degree_counts,x='Degree',y='Proteins',title='Degree distribution'),width='stretch',key=key+'degree')
        plotly_chart(px.scatter(metrics,x='degree',y='clustering_coefficient',hover_name='node',color=metrics.community.astype(str),
            hover_data=['Family','orthogroup'],title='Connectivity and local clustering'),width='stretch',key=key+'degree_clustering')
    elif section=='Centrality & clusters':
        rankable=[name for name in NODE_METRICS if pd.api.types.is_numeric_dtype(metrics[name]) and metrics[name].notna().any()
            and name not in ['component','component_size','articulation_point']]
        if counts['components']>1 and 'component_eigenvector' in rankable:rankable.remove('component_eigenvector')
        rank=st.selectbox('Rank imported proteins by',rankable,index=rankable.index('betweenness'),key=key+'rank')
        ranked=metrics.sort_values([rank,'identifier'],ascending=[False,True]);st.dataframe(ranked,width='stretch',hide_index=True)
        st.download_button('Download imported centrality and clusters',ranked.to_csv(index=False),'string_imported_topology.csv',key=key+'metrics')
        plotly_chart(px.bar(ranked.head(30),x='identifier',y=rank,color='Family',hover_data=['node','orthogroup'],
            title='Top 30 displayed proteins · '+rank),width='stretch',key=key+'ranking')
        available=metrics.dropna(subset=['closeness','betweenness'])
        if len(available):plotly_chart(px.scatter(available,x='closeness',y='betweenness',color=available.community.astype(str),
            size=available.degree.clip(lower=1),hover_name='node',hover_data=['Family','orthogroup','clustering_coefficient'],
            title='Closeness and betweenness'),width='stretch',key=key+'centrality')
        cols=[c for c in ['degree','strength','betweenness','closeness','harmonic_centrality','pagerank','confidence_pagerank',
            'component_eigenvector','clustering_coefficient','k_core'] if metrics[c].notna().sum()>1 and metrics[c].nunique()>1]
        if counts['components']>1 and 'component_eigenvector' in cols:cols.remove('component_eigenvector')
        if len(cols)>1:
            correlation=metrics[cols].corr(method='spearman')
            plotly_chart(px.imshow(correlation,zmin=-1,zmax=1,color_continuous_scale='RdYlGn',title='Centrality rank correlation · Spearman'),width='stretch',key=key+'correlation')
            st.download_button('Download centrality rank correlations',correlation.to_csv(),'string_centrality_correlations.csv',key=key+'correlation_csv')
    elif section=='Topological clustering':
        clusters,comparison=compared(tuple(graph),tuple(graph.edges))
        st.dataframe(comparison,hide_index=True,width='stretch')
        st.caption('Comparison uses default parameters on this entire filtered graph. Detailed controls below run the selected algorithm with its displayed parameters; MCL nonconvergence and size limits are explicit.')
        st.download_button('Download all applicable default cluster analyses',bundle(result,clusters,source_info,source_raw=state['raw'],cluster_comparison=comparison),
            'string_all_cluster_analyses.zip','application/zip',key=key+'all_clusters')
        clustering_panel(graph,metrics,key+'clustering',SPECIES[code]+' · imported STRING',enabled=True)
    elif section=='Components & robustness':
        st.dataframe(result['components'],hide_index=True,width='stretch')
        st.subheader('Articulation proteins')
        st.dataframe(metrics[metrics.articulation_point],hide_index=True,width='stretch')
        st.subheader('Bridge interactions')
        st.dataframe(result['edges'][result['edges'].bridge],hide_index=True,width='stretch')
        st.caption('Removing an articulation node or bridge edge increases the number of graph components. These are topological vulnerabilities, not experimental evidence of essentiality. Diameter/radius are reported per component; unreachable paths are not assigned finite distances.')
    elif section=='Interactions & mapping':
        annotations=result['edges'].drop(columns='combined_score')
        pairs=edges.copy();pairs['_pair']=[tuple(sorted(pair)) for pair in zip(pairs.node1_string_id,pairs.node2_string_id)]
        annotations['_pair']=[tuple(sorted(pair)) for pair in zip(annotations.node1_string_id,annotations.node2_string_id)]
        detailed=pairs.merge(annotations.drop(columns=['node1_string_id','node2_string_id']),on='_pair',validate='one_to_one').drop(columns='_pair')
        st.dataframe(detailed,width='stretch',hide_index=True)
        st.download_button('Download filtered STRING interactions · TSV',detailed.to_csv(sep='\t',index=False),'string_imported_filtered.tsv','text/tab-separated-values',key=key+'edges')
        st.caption('Original evidence channels are retained. Shared STRING representatives retain all exact mapped candidate IDs; no paralogue is selected automatically.')
        st.dataframe(metrics[['identifier','node','sequence_id','Family','orthogroup','mapping_status']],width='stretch',hide_index=True)
    elif section=='Matrices':
        ordered=metrics.sort_values(['degree','identifier'],ascending=[False,True]).identifier.tolist()
        matrix_key=key+'matrix'
        if matrix_key in st.session_state:st.session_state[matrix_key]=[i for i in st.session_state[matrix_key] if i in graph]
        defaults={} if matrix_key in st.session_state else {'default':ordered[:min(20,len(ordered))]}
        ids=st.multiselect('Matrix proteins (maximum 60)',ordered,max_selections=60,key=matrix_key,**defaults)
        if ids:
            matrix_data=matrices(graph,ids,result['edges'])
            matrix_name=st.selectbox('Imported matrix',list(matrix_data),key=key+'matrix_type')
            plotly_chart(px.imshow(matrix_data[matrix_name],aspect='auto',color_continuous_scale='YlGn',title=matrix_name),width='stretch',key=key+'matrix_plot')
            st.caption('Hop distances and neighbor overlap use the full filtered graph. Unreachable pairs are blank. Adjacency/confidence describe selected direct pairs. The Laplacian belongs to the selected induced subgraph; confidence is never treated as distance.')
            st.download_button('Download selected matrix',matrix_data[matrix_name].to_csv(),'string_'+matrix_name.lower().replace(' ','_')+'.csv',key=key+'matrix_download')
            st.download_button('Download all five matrices and topology',bundle(result,source=source_info,matrix_data=matrix_data,source_raw=state['raw']),
                'string_matrices_and_topology.zip','application/zip',key=key+'matrix_bundle')
    else:
        st.json(json_ready({'source':state.get('provenance',{}),'analysis':result['provenance'],
            'filters':{'minimum_score':threshold,'families':families,'neighborhood':focus,'hide_isolates':hide}}))
        st.download_button('Download original STRING response · TSV',state['raw'],'string_network_original.tsv','text/tab-separated-values',key=key+'raw')
    st.download_button('Download displayed topology metrics and provenance',bundle(result,source=source_info,source_raw=state['raw']),
        'string_network_analysis.zip','application/zip',key=key+'bundle')


def math_sqrt(value):return float(value)**.5


def network_labels(registry):
    base={identifier:state['source']+' · '+SPECIES[state['code']]+' · '+state.get('network_type','') for identifier,state in registry.items()}
    return {identifier:label+(' · '+identifier[:6] if list(base.values()).count(label)>1 else '') for identifier,label in base.items()}


def saved_networks_panel(candidates):
    registry=migrate_networks(st.session_state)
    if not registry:return
    st.subheader('Saved STRING imports')
    ids=list(registry)
    labels=network_labels(registry)
    if st.session_state.get('atlas_string_selected_network') not in ids:st.session_state['atlas_string_selected_network']=ids[-1]
    chosen=st.selectbox('Imported STRING network',ids,key='atlas_string_selected_network',
        format_func=labels.get)
    st.session_state['atlas_string_network']=registry[chosen]
    with st.expander('Analyze and compare all saved imports'):
        st.caption('Each source graph is analyzed independently, using all its imported edges and resolved isolates. No species or interaction types are merged. Selected-network filters do not affect this batch comparison.')
        signature=hashlib.sha256((VERSION+json.dumps([(i,s.get('resolved',{}),s['source'],s.get('provenance',{})) for i,s in registry.items()],sort_keys=True)+
            pd.util.hash_pandas_object(candidates[['sequence_id','family','orthogroup','candidate_annotation']].astype(str),index=False).values.tobytes().hex()).encode()).hexdigest()
        if st.button('Analyze all imported STRING networks',key='string_analyze_all'):
            rows=[];output=io.BytesIO()
            with st.spinner('Analyzing each saved source network independently…'),zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
                for identifier,state in registry.items():
                    result=measured(prepare_nodes(state,candidates),state['edges'],None)
                    graph=analysis_graph(result);clusters,cluster_comparison=compared(tuple(graph),tuple(graph.edges))
                    row={'Network':state['source'],'Species':SPECIES[state['code']],**result['summary']}
                    for record in cluster_comparison.to_dict('records'):
                        row[record['Method']+' clusters']=record['Clusters'];row[record['Method']+' status']=record['Status']
                    rows.append(row)
                    archive.writestr(identifier+'.zip',bundle(result,clusters,{'source':state['source'],'species':state['code'],
                        'query':state.get('provenance'),'filters':'All imported edges and resolved isolates'},source_raw=state['raw'],cluster_comparison=cluster_comparison))
                comparison=pd.DataFrame(rows);archive.writestr('network_comparison.csv',comparison.to_csv(index=False))
            st.session_state['atlas_string_batch']={'signature':signature,'summary':comparison,'zip':output.getvalue()}
        batch=st.session_state.get('atlas_string_batch',{})
        if batch.get('signature')==signature:
            st.dataframe(batch['summary'],hide_index=True,width='stretch')
            st.download_button('Download analysis for every saved STRING import',batch['zip'],'all_string_network_analyses.zip','application/zip',key='string_all_download')
    analysis_panel(registry[chosen],candidates)
    a,b=st.columns(2)
    if a.button('Clear imported STRING workspace',key='string_remove_selected'):
        del registry[chosen];st.session_state['atlas_string_networks']=registry
        st.session_state.pop('atlas_string_network',None);st.session_state.pop('atlas_string_selected_network',None);st.rerun()
    if b.button('Clear all imported STRING networks',key='string_remove_all'):
        for key in ['atlas_string_networks','atlas_string_network','atlas_string_selected_network','atlas_string_batch']:st.session_state.pop(key,None)
        st.rerun()
