"""Reproducible topology for every undirected STRING import; no SciPy dependency."""
import hashlib
import io
import json
import math
import zipfile

import networkx as nx
import numpy as np
import pandas as pd

from topological_clustering import cluster_network

VERSION='string-analysis-1'
PATH_LIMIT=2000
CLUSTER_LIMITS={'Greedy modularity':5000,'MCODE':1200,'MCL':400}
NODE_METRICS=['degree','degree_centrality','strength','betweenness','closeness','harmonic_centrality',
    'pagerank','confidence_pagerank','component_eigenvector','clustering_coefficient','triangles',
    'k_core','average_neighbor_degree','component','component_size','farness','reachable_nodes',
    'component_eccentricity','articulation_point','bridge_connections','interface_connections']


def network_id(state):
    scores=state['edges'][['node1_string_id','node2_string_id','combined_score']].to_csv(index=False)
    return hashlib.sha256(json.dumps([state['code'],state.get('taxon'),state.get('network_type'),
        state['raw'],scores],sort_keys=True).encode()).hexdigest()[:16]


def register_network(session,state):
    """Retain independent imports; exact reimports refresh metadata rather than double-counting."""
    registry=dict(session.get('atlas_string_networks',{}));identifier=network_id(state)
    registry[identifier]=state
    session['atlas_string_networks']=registry
    session['atlas_string_selected_network']=identifier
    session['atlas_string_network']=state  # Compatibility with existing sessions/tools.
    return identifier


def migrate_networks(session):
    if not session.get('atlas_string_networks') and session.get('atlas_string_network'):
        register_network(session,session['atlas_string_network'])
    return session.get('atlas_string_networks',{})


def graph_digest(graph):
    payload={'nodes':sorted(graph),'edges':sorted((min(a,b),max(a,b),float(d['confidence'])) for a,b,d in graph.edges(data=True))}
    return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def _pagerank(graph,weighted=False,alpha=.85,tolerance=1e-10,iterations=1000):
    order=list(graph);n=len(order)
    if not n:return {},True
    index={node:i for i,node in enumerate(order)};source=[];target=[];weights=[]
    for a,b,metadata in graph.edges(data=True):
        weight=float(metadata['confidence']) if weighted else 1.
        source.extend([index[a],index[b]]);target.extend([index[b],index[a]]);weights.extend([weight,weight])
    source=np.array(source,dtype=int);target=np.array(target,dtype=int);weights=np.array(weights,dtype=float)
    strength=np.bincount(source,weights=weights,minlength=n)
    transition=np.divide(weights,strength[source],out=np.zeros_like(weights),where=strength[source]>0)
    rank=np.full(n,1/n)
    for _ in range(iterations):
        update=np.full(n,(1-alpha)/n+alpha*rank[strength==0].sum()/n)
        update+=np.bincount(target,weights=alpha*rank[source]*transition,minlength=n)
        if np.abs(update-rank).sum()<n*tolerance:return dict(zip(order,update)),True
        rank=update
    return {node:float('nan') for node in order},False


def analyze_network(nodes,edges,exact_paths=None):
    """Keep all nodes; mark undefined/size-limited metrics instead of fabricating zeros."""
    if nodes.identifier.duplicated().any():raise ValueError('STRING node metadata requires unique identifiers.')
    graph=nx.Graph();graph.add_nodes_from(sorted(nodes.identifier))
    for a,b,score in edges[['node1_string_id','node2_string_id','combined_score']].itertuples(index=False,name=None):
        if a not in graph or b not in graph:raise ValueError('A STRING edge endpoint is missing from the node metadata.')
        if not math.isfinite(float(score)) or not 0<=float(score)<=1:raise ValueError('STRING analysis requires normalized confidence scores in [0,1].')
        if a!=b:graph.add_edge(a,b,confidence=max(float(score),graph.get_edge_data(a,b,{}).get('confidence',0.)))
    n=len(graph);m=graph.number_of_edges();notes=[]
    paths=n<=PATH_LIMIT if exact_paths is None else bool(exact_paths)
    if paths and n>5000:raise ValueError('Exact all-node path metrics are bounded to 5,000 nodes; filter the network first.')
    degree=dict(graph.degree());strength=dict(graph.degree(weight='confidence'))
    components=sorted(nx.connected_components(graph),key=lambda c:(-len(c),sorted(c)))
    component_id={node:i+1 for i,c in enumerate(components) for node in c}
    sizes={node:len(c) for c in components for node in c}
    if n<=CLUSTER_LIMITS['Greedy modularity']:
        communities=nx.community.greedy_modularity_communities(graph,weight=None) if m else [{node} for node in graph]
        communities=sorted(communities,key=lambda c:sorted(c)[0])
        labels={node:i+1 for i,c in enumerate(communities) for node in c}
    else:
        communities=[];labels={};notes.append('Greedy modularity not computed above 5,000 nodes.')
    sample=None if n<=PATH_LIMIT or exact_paths else min(256,n)
    betweenness=nx.betweenness_centrality(graph,k=sample,normalized=True,weight=None,seed=23) if n else {}
    betweenness_mode='exact' if sample is None else f'sampled {sample} source nodes; seed 23'
    farness={};harmonic={};closeness={};eccentricity={}
    if paths:
        for node,lengths in nx.all_pairs_shortest_path_length(graph):
            reach=len(lengths)-1;distance=sum(lengths.values())
            farness[node]=distance;harmonic[node]=sum(1/value for value in lengths.values() if value)
            closeness[node]=(reach/distance)*(reach/(n-1)) if distance and n>1 else 0.
            eccentricity[node]=max(lengths.values(),default=0)
    else:notes.append('All-node exact closeness, harmonic centrality, farness, eccentricity and distance summaries await exact path analysis or a smaller filtered graph.')
    bridges={tuple(sorted(edge)) for edge in nx.bridges(graph)}
    articulation=set(nx.articulation_points(graph));bridge_degree={node:0 for node in graph}
    for a,b in bridges:bridge_degree[a]+=1;bridge_degree[b]+=1
    rank,rank_ok=_pagerank(graph);weighted_rank,weighted_rank_ok=_pagerank(graph,weighted=True)
    if not rank_ok or not weighted_rank_ok:notes.append('A PageRank power iteration did not converge; its values are unavailable.')
    eigen={};eigen_failures=0
    for group in components:
        if len(group)==1:continue  # Eigenvector scores are undefined for an edgeless component.
        try:eigen.update(nx.eigenvector_centrality(graph.subgraph(group),max_iter=1000,tol=1e-8,weight=None))
        except nx.PowerIterationFailedConvergence:eigen_failures+=1
    if eigen_failures:notes.append(f'Component eigenvector centrality did not converge for {eigen_failures} component(s).')
    metrics=nodes.copy()
    values={'degree':degree,'degree_centrality':{node:degree[node]/(n-1) if n>1 else 0. for node in graph},
        'strength':strength,'betweenness':betweenness,'closeness':closeness,'harmonic_centrality':harmonic,
        'pagerank':rank,'confidence_pagerank':weighted_rank,'component_eigenvector':eigen,
        'clustering_coefficient':nx.clustering(graph),'triangles':nx.triangles(graph),
        'k_core':nx.core_number(graph) if n else {},'average_neighbor_degree':nx.average_neighbor_degree(graph),
        'component':component_id,'component_size':sizes,'farness':farness,
        'reachable_nodes':{node:sizes[node]-1 for node in graph},'component_eccentricity':eccentricity,
        'articulation_point':{node:node in articulation for node in graph},'bridge_connections':bridge_degree,
        'community':labels}
    layers=nodes.set_index('identifier')['layer'].fillna('Unresolved').to_dict() if 'layer' in nodes else {node:'Unresolved' for node in graph}
    interfaces={frozenset(['Extracellular','Membrane']),frozenset(['Membrane','Membrane-proximal']),frozenset(['Membrane-proximal','Actin-coupling'])}
    values['interface_connections']={node:sum(layers[node]!='Unresolved' and layers[other]!='Unresolved'
        and layers[node]!=layers[other] and (frozenset([layers[node],layers[other]]) in interfaces
        or 'Signalling' in [layers[node],layers[other]]) for other in graph[node]) for node in graph}
    for column,mapping in values.items():metrics[column]=metrics.identifier.map(mapping)
    edge_bet=nx.edge_betweenness_centrality(graph,normalized=True,weight=None) if n<=500 and m<=5000 else {}
    if m and not edge_bet:notes.append('Exact edge betweenness is available for up to 500 nodes / 5,000 edges; filter the network to inspect it.')
    edge_rows=[]
    for a,b,metadata in sorted(graph.edges(data=True)):
        common=set(graph[a])&set(graph[b]);union=(set(graph[a])|set(graph[b]))-{a,b}
        edge_rows.append({'node1_string_id':a,'node2_string_id':b,'combined_score':metadata['confidence'],
            'bridge':tuple(sorted((a,b))) in bridges,'common_neighbors':len(common),
            'neighborhood_overlap':len(common)/len(union) if union else float('nan'),
            'edge_betweenness':edge_bet.get((a,b),edge_bet.get((b,a),float('nan')))})
    edge_metrics=pd.DataFrame(edge_rows,columns=['node1_string_id','node2_string_id','combined_score','bridge',
        'common_neighbors','neighborhood_overlap','edge_betweenness'])
    component_rows=[]
    for i,c in enumerate(components):
        local=graph.subgraph(c);size=len(c)
        component_rows.append({'component':i+1,'nodes':size,'edges':local.number_of_edges(),'density':nx.density(local),
            'diameter':max((eccentricity[node] for node in c),default=0) if paths else float('nan'),
            'radius':min((eccentricity[node] for node in c),default=0) if paths else float('nan'),
            'mean_shortest_path':sum(farness[node] for node in c)/(size*(size-1)) if paths and size>1 else 0. if paths else float('nan')})
    component_metrics=pd.DataFrame(component_rows,columns=['component','nodes','edges','density','diameter','radius','mean_shortest_path'])
    reachable_pairs=sum(sizes[node]-1 for node in graph)
    assort=float('nan')
    if m>1 and len({degree[node] for node in graph if degree[node]})>1:
        assort=nx.degree_assortativity_coefficient(graph)
    summary={'nodes':n,'edges':m,'density':nx.density(graph),'components':len(components),
        'isolates':nx.number_of_isolates(graph),'communities':len(communities) if n<=5000 else None,
        'mean_degree':2*m/n if n else 0.,'mean_clustering':nx.average_clustering(graph) if n else 0.,
        'transitivity':nx.transitivity(graph),'triangles':sum(values['triangles'].values())//3,
        'largest_component':len(components[0]) if components else 0,'articulation_points':len(articulation),
        'bridges':len(bridges),'degree_assortativity':assort,
        'global_efficiency':sum(harmonic.values())/(n*(n-1)) if paths and n>1 else 0. if paths else float('nan'),
        'mean_reachable_distance':sum(farness.values())/reachable_pairs if paths and reachable_pairs else 0. if paths else float('nan')}
    provenance={'version':VERSION,'graph_sha256':graph_digest(graph),'graph_type':'undirected simple graph; no self-loops',
        'shortest_paths':'unweighted hop counts','betweenness':betweenness_mode,'exact_path_metrics':paths,
        'eigenvector':'unweighted; unit normalization separately within each nontrivial connected component',
        'confidence':'STRING score in [0,1]; used for node strength and confidence-weighted PageRank, not binding affinity or path length',
        'pagerank':{'alpha':.85,'tolerance':1e-10,'max_iterations':1000,'unweighted_converged':rank_ok,'confidence_converged':weighted_rank_ok},
        'notes':notes}
    return {'nodes':metrics,'edges':edge_metrics,'components':component_metrics,'summary':summary,'provenance':provenance}


def analysis_graph(result):
    graph=nx.Graph();graph.add_nodes_from(result['nodes'].identifier)
    graph.add_edges_from(result['edges'][['node1_string_id','node2_string_id']].itertuples(index=False,name=None))
    return graph


def all_clusterings(graph):
    results={};rows=[]
    for method,limit in CLUSTER_LIMITS.items():
        if len(graph)>limit:
            rows.append({'Method':method,'Status':f'Filter to ≤ {limit:,} nodes','Clusters':None,'Assigned nodes':None,'Modularity':None});continue
        members,clusters,diagnostics=cluster_network(graph,method)
        status='Not converged' if diagnostics.get('converged') is False else 'Complete'
        results[method]={'members':members,'summary':clusters,'diagnostics':diagnostics}
        rows.append({'Method':method,'Status':status,'Clusters':len(clusters) if status=='Complete' else None,
            'Assigned nodes':diagnostics.get('assigned_nodes'),'Modularity':diagnostics.get('unweighted_modularity')})
    return results,pd.DataFrame(rows)


def matrices(graph,ids,edge_metrics):
    ids=list(dict.fromkeys(ids))
    if not set(ids)<=set(graph):raise ValueError('Matrix identifiers must belong to the displayed graph.')
    adjacency=nx.to_numpy_array(graph,nodelist=ids,weight=None) if set(ids)==set(graph) else nx.to_numpy_array(graph.subgraph(ids),nodelist=ids,weight=None)
    confidence=np.zeros_like(adjacency);lookup={node:i for i,node in enumerate(ids)}
    for row in edge_metrics.itertuples():
        if row.node1_string_id in lookup and row.node2_string_id in lookup:
            a,b=lookup[row.node1_string_id],lookup[row.node2_string_id];confidence[a,b]=confidence[b,a]=row.combined_score
    distances=np.full(adjacency.shape,np.nan);overlap=np.zeros_like(adjacency)
    for i,a in enumerate(ids):
        lengths=nx.single_source_shortest_path_length(graph,a)
        for j,b in enumerate(ids):
            distances[i,j]=lengths.get(b,float('nan'))
            neighbors_a=set(graph[a]);neighbors_b=set(graph[b]);union=neighbors_a|neighbors_b
            overlap[i,j]=len(neighbors_a&neighbors_b)/len(union) if union else float('nan')
    values={'Adjacency':adjacency,'Confidence adjacency':confidence,'Hop distances':distances,
        'Neighbor Jaccard':overlap,'Induced Laplacian':np.diag(adjacency.sum(axis=1))-adjacency}
    return {name:pd.DataFrame(value,index=ids,columns=ids) for name,value in values.items()}


def json_ready(value):
    if value is pd.NA or value is pd.NaT:return None
    if isinstance(value,dict):return {str(k):json_ready(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_ready(v) for v in value]
    if isinstance(value,np.generic):value=value.item()
    if isinstance(value,float) and not math.isfinite(value):return None
    return value


def bundle(result,clusters=None,source=None,matrix_data=None,source_raw=None,cluster_comparison=None):
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in ['nodes','edges','components']:archive.writestr(name+'.csv',result[name].to_csv(index=False))
        archive.writestr('analysis.json',json.dumps(json_ready({'summary':result['summary'],'methods':result['provenance'],'source':source or {}}),indent=2,allow_nan=False))
        for method,data in (clusters or {}).items():
            archive.writestr(method+'/members.csv',data['members'].to_csv(index=False))
            archive.writestr(method+'/clusters.csv',data['summary'].to_csv(index=False))
            archive.writestr(method+'/diagnostics.json',json.dumps(json_ready(data['diagnostics']),indent=2,allow_nan=False))
        for name,frame in (matrix_data or {}).items():archive.writestr('matrices/'+name+'.csv',frame.to_csv())
        if source_raw is not None:archive.writestr('source_network_original.tsv',source_raw)
        if cluster_comparison is not None:archive.writestr('clustering_comparison.csv',cluster_comparison.to_csv(index=False))
    return memory.getvalue()
