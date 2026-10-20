"""Topology and matrices shared by reference projections and user STRING networks."""
import pandas as pd
import networkx as nx

def topology(nodes,edges):
    graph=nx.Graph()
    graph.add_nodes_from(sorted(nodes.identifier))
    graph.add_edges_from(zip(edges.node1_string_id,edges.node2_string_id))
    graph.remove_edges_from(nx.selfloop_edges(graph))
    degree=dict(graph.degree()); bet=nx.betweenness_centrality(graph,normalized=True,weight=None)
    close=nx.closeness_centrality(graph,wf_improved=True)
    groups=nx.community.greedy_modularity_communities(graph,weight=None) if graph.number_of_edges() else [{n} for n in graph]
    communities={node:i+1 for i,group in enumerate(sorted(groups,key=lambda g:sorted(g)[0])) for node in group}
    result=nodes.copy()
    components=sorted(nx.connected_components(graph),key=lambda group:(-len(group),sorted(group)[0]))
    component_id={node:i+1 for i,group in enumerate(components) for node in group}
    component_size={node:len(group) for group in components for node in group}
    cores=nx.core_number(graph) if graph.number_of_nodes() else {}
    clustering=nx.clustering(graph)
    farness={}; reachable={}
    for node,lengths in nx.all_pairs_shortest_path_length(graph):
        farness[node]=sum(lengths.values())
        reachable[node]=len(lengths)-1
    result['degree']=result.identifier.map(degree);result['betweenness']=result.identifier.map(bet);result['closeness']=result.identifier.map(close);result['community']=result.identifier.map(communities)
    result['clustering_coefficient']=result.identifier.map(clustering)
    result['k_core']=result.identifier.map(cores)
    result['component']=result.identifier.map(component_id)
    result['component_size']=result.identifier.map(component_size)
    result['farness']=result.identifier.map(farness)
    result['reachable_nodes']=result.identifier.map(reachable)
    layer=nodes.set_index('identifier').layer.to_dict()
    interfaces={frozenset(['Extracellular','Membrane']),frozenset(['Membrane','Membrane-proximal']),frozenset(['Membrane-proximal','Actin-coupling'])}
    result['interface_connections']=result.identifier.map(lambda n:sum(layer[n]!='Unresolved' and layer[v]!='Unresolved' and layer[n]!=layer[v] and (frozenset([layer[n],layer[v]]) in interfaces or 'Signalling' in [layer[n],layer[v]]) for v in graph[n]))
    return result,graph


def network_matrices(graph, identifiers):
    """Distances use the whole displayed graph; adjacency describes direct selected pairs."""
    selected=list(dict.fromkeys(identifiers))
    if not set(selected) <= set(graph):
        raise ValueError('Matrix selection contains a node outside the displayed network')
    distances=pd.DataFrame(float('nan'),index=selected,columns=selected)
    adjacency=pd.DataFrame(0,index=selected,columns=selected,dtype=int)
    for node in selected:
        lengths=nx.single_source_shortest_path_length(graph,node)
        for other in selected:
            if other in lengths: distances.loc[node,other]=lengths[other]
            if graph.has_edge(node,other): adjacency.loc[node,other]=1
    return distances,adjacency

