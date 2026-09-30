"""Evidence-aware layered reconstruction and exploratory prioritization."""
import math
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from data import ROOT, SPECIES

LAYERS = ['Extracellular','Membrane','Membrane-proximal','Actin-coupling','Scaffolding','Signalling','Unresolved']
COLORS = dict(zip(LAYERS,['#cb8e46','#377eb8','#26a69a','#7b62a3','#da6d98','#c85b4b','#9ba8b2']))
MODULES = dict(zip(['extracellular_matrix','integrin_receptors','membrane_proximal_adaptors','actin_linking','focal_adhesion_scaffolds','downstream_signalling'],LAYERS))
EVIDENCE_DIR = ROOT/'adhesome_network'/'curation'
FEATURES = ['conservation','domain_architecture','motif_conservation','topology_compatibility','phylogenetic_support','network_connectivity','host_divergence']

def read_optional(name,columns):
    path=EVIDENCE_DIR/name
    if not path.exists():
        return pd.DataFrame(columns=columns)
    frame=pd.read_csv(path,sep='\t').fillna('')
    missing=set(columns)-set(frame.columns)
    if missing:
        raise ValueError(f'{name}: missing columns {sorted(missing)}')
    return frame


def network_source_signature():
    """Invalidate cached graph assembly whenever a supplied network file changes."""
    root=ROOT/'adhesome_network'
    return tuple((p.relative_to(root).as_posix(),p.stat().st_mtime_ns,p.stat().st_size)
                 for p in sorted(root.rglob('*')) if p.is_file())


@st.cache_data(show_spinner=False)
def cached_assemble(candidates,threshold,signature,_loader):
    return assemble(candidates,_loader,threshold)


@st.cache_data(show_spinner=False)
def cached_topology(nodes,edges):
    return topology(nodes,edges)

def assemble(candidates,loader,threshold):
    frames=[]; links=[]
    mapping=read_optional('node_mapping.tsv',['string_id','sequence_id','orthogroup','reference'])
    if mapping.string_id.duplicated().any():
        raise ValueError('node_mapping.tsv contains duplicate STRING IDs')
    if len(mapping) and (mapping.reference.eq('').any() or not set(mapping.sequence_id)<=set(candidates.sequence_id)):
        raise ValueError('Every node mapping requires a reference and an existing candidate sequence_id')
    candidates=candidates.copy()
    candidates['display_family']=candidates.reviewed_family.fillna('Unassigned') if 'reviewed_family' in candidates else candidates.family
    catalogue=candidates.groupby('sequence_id').agg(module=('module',lambda x:' | '.join(sorted(set(x)))),family=('display_family',lambda x:' | '.join(sorted(set(x)))))
    for code in SPECIES:
        nodes,edges,_=loader(code,candidates)
        nodes['species']=code
        if 'sequence_id' not in nodes:
            nodes['sequence_id']=nodes.node.map(lambda name:code+'__'+name if code+'__'+name in catalogue.index else '')
        orthology=candidates.groupby('sequence_id')['orthogroup'].agg(lambda x:' | '.join(sorted(set(x.dropna())-{''}))) if 'orthogroup' in candidates else pd.Series(dtype=str)
        nodes['orthogroup']=nodes.sequence_id.map(orthology).fillna('')
        # Conflicting source group assignments must not create an automatic merge.
        nodes.loc[nodes.orthogroup.str.contains(' | ',regex=False),'orthogroup']=''
        nodes['orthology_basis']=nodes.orthogroup.map(lambda x:'Candidate workbook orthology results' if x else 'Unresolved')
        if 'schistosome_species_in_HOG' in candidates:
            coverage=candidates.groupby('sequence_id').schistosome_species_in_HOG.agg(lambda x: x.dropna().iloc[0] if x.dropna().nunique()==1 else float('nan'))
            nodes['source_HOG_species_count']=nodes.sequence_id.map(coverage)
        for row in mapping.itertuples():
            if row.string_id in set(nodes.identifier):
                if not row.sequence_id.startswith(code+'__'):
                    raise ValueError(f'Species mismatch in mapping for {row.string_id}')
                nodes.loc[nodes.identifier.eq(row.string_id),['sequence_id','orthogroup']]=[row.sequence_id,row.orthogroup]
                nodes.loc[nodes.identifier.eq(row.string_id),'orthology_basis']='Curated mapping: '+row.reference
                nodes.loc[nodes.identifier.eq(row.string_id),'source_HOG_species_count']=float('nan')
        nodes['Family']=nodes.sequence_id.map(catalogue.family).fillna('Unmapped')
        def layer(row):
            if row.sequence_id in catalogue.index:
                modules=catalogue.loc[row.sequence_id,'module'].split(' | ')
                layers=set(MODULES.get(m,'Unresolved') for m in modules)
                if len(layers)==1:
                    return next(iter(layers)),'Catalogue module'
                return 'Unresolved','Multiple catalogue modules'
            terms=set(row['STRING localization'].split(' | '))
            if terms & {'Extracellular matrix','Extracellular region','Basement membrane'}:
                return 'Extracellular','STRING compartment (display assignment)'
            if 'Plasma membrane' in terms:
                return 'Membrane','STRING compartment (display assignment)'
            if terms & {'Actin cytoskeleton','Cytoskeleton'}:
                return 'Actin-coupling','STRING compartment (display assignment)'
            return 'Unresolved','No supported layer assignment'
        assignments=nodes.apply(layer,axis=1)
        nodes['layer']=[x[0] for x in assignments];nodes['layer_basis']=[x[1] for x in assignments]
        for field in ['audit_classification','family_assignment_basis','evidence_review_stage','domain_evidence','topology_evidence','motif_context_evidence','adhesome_interpretation','host_orthology_flag','priority_group']:
            if field in candidates:
                summary=candidates.groupby('sequence_id')[field].agg(lambda x:' | '.join(sorted(set(x.dropna()))))
                nodes[field]=nodes.sequence_id.map(summary).fillna('Unmapped')
        for field in ['domain_architecture','motif_conservation','topology_compatibility','phylogenetic_support','host_divergence']:
            if field in candidates:
                values=candidates.groupby('sequence_id')[field].min()
                nodes[field]=nodes.sequence_id.map(values)
            basis=field+'_basis'
            if basis in candidates:
                values=candidates.groupby('sequence_id')[basis].agg(lambda x:' | '.join(sorted(set(x.dropna()))))
                nodes[basis]=nodes.sequence_id.map(values).fillna('No unique catalogue mapping')
        for field in ['motif_hit_details','motif_assignment_tiers','motif_functional_assignment','assignment_evidence_summary']:
            if field in candidates:
                values=candidates.groupby('sequence_id')[field].agg(lambda x:' | '.join(sorted(set(x.dropna()))))
                nodes[field]=nodes.sequence_id.map(values).fillna('No unique catalogue mapping')
        frames.append(nodes)
        edges=edges[edges.combined_score.ge(threshold)].copy()
        edges['species']=code
        edges['relation']='Functional association (STRING)'
        channels=['neighborhood_on_chromosome','gene_fusion','phylogenetic_cooccurrence','homology','coexpression','experimentally_determined_interaction','database_annotated','automated_textmining']
        edges['evidence']=edges.apply(lambda r:'; '.join(c for c in channels if pd.to_numeric(r.get(c,0),errors='coerce')>0),axis=1)
        edges['support']=edges.combined_score.map(lambda x:'STRING score ≥ 0.7' if x>=.7 else 'STRING score < 0.7')
        edges['reference']=f'adhesome_network/{code}/{code}_string_interactions.tsv'
        links.append(edges)
    nodes=pd.concat(frames,ignore_index=True); edges=pd.concat(links,ignore_index=True)
    known=set(nodes.identifier)
    if not set(mapping.string_id)<=known:
        raise ValueError('node_mapping.tsv references unknown STRING nodes')
    columns=['source','target','relation','orthology_transfer','domain_compatibility','motif_compatibility','topology_compatibility','family_relationship','phylogenetic_support','reference']
    transfer=read_optional('reference_interactions.tsv',columns)
    accepted=[]; excluded=[]
    allowed={'Predicted physical interaction','Domain-mediated association','Motif-dependent interaction','Regulatory relationship','Functional coupling'}
    for r in transfer.to_dict('records'):
        required=['orthology_transfer','domain_compatibility','motif_compatibility','topology_compatibility','family_relationship']
        valid=r['source'] in known and r['target'] in known and r['source']!=r['target'] and r['relation'] in allowed and bool(r['reference']) and all(r[x]=='supported' for x in required)
        if valid:
            a=nodes.set_index('identifier').loc[r['source']]; b=nodes.set_index('identifier').loc[r['target']]
            valid=a.species==b.species
        if not valid:
            excluded.append(r); continue
        accepted.append(dict(node1=a.node,node2=b.node,node1_string_id=r['source'],node2_string_id=r['target'],combined_score=float('nan'),species=a.species,relation=r['relation'],evidence='; '.join(x for x in required+['phylogenetic_support'] if r[x]=='supported'),support='Gated reference transfer',reference=r['reference']))
    if accepted:
        edges=pd.concat([edges,pd.DataFrame(accepted)],ignore_index=True)
    return nodes,edges,pd.DataFrame(excluded)

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


def retained_subgraph(nodes,edges,identifiers):
    """Return the induced subgraph after interactive node filtering."""
    retained=set(identifiers)
    return (nodes[nodes.identifier.isin(retained)].copy(),
            edges[edges.node1_string_id.isin(retained) & edges.node2_string_id.isin(retained)].copy())

def prioritize(nodes,graph,all_nodes):
    result=nodes[['identifier','node','species','Family','layer','interface_connections','degree','betweenness','closeness']].copy()
    for f in FEATURES: result[f]=float('nan')
    orth=all_nodes[all_nodes.orthogroup.ne('')].groupby('orthogroup').species.nunique().to_dict()
    result['conservation']=[orth.get(g,float('nan'))/3 for g in nodes.orthogroup]
    if 'source_HOG_species_count' in nodes:
        result['conservation']=pd.to_numeric(nodes.source_HOG_species_count,errors='coerce').div(3).where(nodes.orthogroup.ne('')).combine_first(result.conservation)
    result['network_connectivity']=result.identifier.map(nx.degree_centrality(graph))
    for feature in ['domain_architecture','motif_conservation','topology_compatibility','phylogenetic_support','host_divergence']:
        if feature in nodes: result[feature]=pd.to_numeric(nodes[feature],errors='coerce').values
        basis=feature+'_basis'
        if basis in nodes: result[basis]=nodes[basis].values
    result['host_similarity_flag']=result.host_divergence.map(lambda x:'Aligned human homologue available' if pd.notna(x) else 'No comparable human alignment')

    reviewed=read_optional('candidate_evidence.tsv',['string_id','domain_architecture','motif_conservation','topology_compatibility','phylogenetic_support','host_divergence','host_similarity_flag','reference'])
    if reviewed.string_id.duplicated().any() or not set(reviewed.string_id)<=set(all_nodes.identifier):
        raise ValueError('candidate_evidence.tsv needs unique, known STRING IDs')
    for r in reviewed.to_dict('records'):
        if not r['reference']: raise ValueError('Candidate evidence requires a reference')
        mask=result.identifier.eq(r['string_id'])
        for f in FEATURES:
            if f in r and r[f]!='':
                value=float(r[f])
                if not math.isfinite(value) or not 0<=value<=1: raise ValueError(f'{f} must be between 0 and 1')
                result.loc[mask,f]=value
        result.loc[mask,'host_similarity_flag']=r['host_similarity_flag'] or 'Not assessed'
    result['available_features']=result[FEATURES].notna().sum(axis=1)
    result['integrated_score']=result[FEATURES].mean(axis=1).where(result.available_features.eq(7))
    result['assessment']=result.available_features.map(lambda n:'Complete exploratory score' if n==7 else f'Incomplete: {7-n} features missing')
    for field in ['evidence_review_stage','domain_evidence','topology_evidence','motif_context_evidence','adhesome_interpretation','host_orthology_flag','priority_group']:
        if field in nodes: result[field]=nodes[field].values
    return result.sort_values(['integrated_score','interface_connections','betweenness','degree'],ascending=False,na_position='last')

def reconstruction_panel(candidates,loader,key):
    st.subheader('Reconstruction of the unified schistosome adhesion network')
    st.write('An integrated adhesion network linking extracellular proteins to integrin–actin coupling and signalling. Assignments draw confidence from convergence across orthology, domain architecture, topology/localization and motif context. The evidence tables distinguish convergent assignments, missing evidence and conflicting signals.')
    with st.expander('Evidence rules and current reconstruction status',expanded=True):
        st.write('Reference transfers require supported orthology, domain, motif, topology and family compatibility plus a cited reference. Generic STRING homology, co-occurrence and experimental-channel scores are not relabeled as orthology, phylogenetic or direct schistosome experimental proof. Missing evidence remains unassessed. The proposed reference-transfer workflow is not claimed as completed merely because a STRING export is present.')
    a,b=st.columns(2)
    view=a.selectbox('Reconstruction view',['Pan-schistosome · separate proteins','Orthogroup consensus']+list(SPECIES),format_func=lambda x:SPECIES.get(x,x),key=key+'view')
    threshold=b.slider('STRING score threshold',0.,1.,.4,.01,key=key+'threshold')
    try:
        all_nodes,all_edges,excluded=cached_assemble(candidates,threshold,network_source_signature(),loader)
    except (ValueError,KeyError) as exc:
        st.error(f'Curation data could not be applied: {exc}');return
    nodes=all_nodes.copy();edges=all_edges.copy()
    if view in SPECIES:
        nodes=nodes[nodes.species.eq(view)]; edges=edges[edges.species.eq(view)]
    if view=='Orthogroup consensus':
        orthogroup_view(all_nodes,all_edges,key);return
    selected=st.multiselect('Relationship types',sorted(edges.relation.unique()),default=sorted(edges.relation.unique()),key=key+'relation')
    edges=edges[edges.relation.isin(selected)]
    support=st.multiselect('Evidence support',sorted(edges.support.unique()),default=sorted(edges.support.unique()),key=key+'support')
    edges=edges[edges.support.isin(support)]
    with st.expander('Filter proteins and subnetworks',expanded=True):
        a,b=st.columns(2)
        selected_families=a.multiselect('Protein families',sorted(nodes.Family.fillna('Unmapped').unique()),key=key+'families',
                                        help='No selection keeps every family, including unmapped nodes.')
        selected_layers=b.multiselect('Adhesion layers',LAYERS,key=key+'layers',
                                      help='No selection keeps every layer.')
        query=st.text_input('Find a protein or identifier',key=key+'query',placeholder='Protein ID, STRING ID or family')
        if selected_families: nodes=nodes[nodes.Family.isin(selected_families)].copy()
        if selected_layers: nodes=nodes[nodes.layer.isin(selected_layers)].copy()
        if query:
            matches=nodes[['identifier','node','sequence_id','Family']].fillna('').astype(str).apply(
                lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)
            nodes=nodes[matches].copy()
        nodes,edges=retained_subgraph(nodes,edges,nodes.identifier)
        if nodes.empty:
            st.info('No proteins match these filters. Broaden the family, layer or identifier selection.')
            return
        degree=pd.concat([edges.node1_string_id,edges.node2_string_id]).value_counts()
        minimum=st.slider('Minimum displayed degree',0,20,0,key=key+'min_degree')
        if minimum:
            nodes,edges=retained_subgraph(nodes,edges,nodes.loc[nodes.identifier.map(degree).fillna(0).ge(minimum),'identifier'])
        if nodes.empty:
            st.info('No proteins remain at this degree threshold.')
            return
        labels_by_id=nodes.set_index('identifier').apply(
            lambda row:f"{row['node']} · {SPECIES.get(row['species'],row['species'])} · {row['Family']}",axis=1).to_dict()
        focus=st.selectbox('Focus on a protein neighborhood',['All proteins']+sorted(nodes.identifier),
                           format_func=lambda identifier:labels_by_id.get(identifier,identifier),key=key+'focus')
        if focus!='All proteins':
            hops=st.radio('Neighborhood radius',[1,2],horizontal=True,key=key+'hops')
            focus_graph=nx.Graph()
            focus_graph.add_nodes_from(nodes.identifier)
            focus_graph.add_edges_from(zip(edges.node1_string_id,edges.node2_string_id))
            neighbors=nx.single_source_shortest_path_length(focus_graph,focus,cutoff=hops)
            nodes,edges=retained_subgraph(nodes,edges,neighbors)
        preliminary,graph=cached_topology(nodes,edges)
        selected_communities=st.multiselect('Topological communities',sorted(preliminary.community.dropna().unique()),
                                             key=key+'communities',help='Choose communities from the current family/layer/neighborhood network. Centralities and displayed community IDs are then recalculated on the selected subgraph.')
        if selected_communities:
            nodes,edges=retained_subgraph(nodes,edges,preliminary.loc[preliminary.community.isin(selected_communities),'identifier'])
            if nodes.empty:
                st.info('No proteins remain in the selected communities.')
                return
            metrics,graph=cached_topology(nodes,edges)
        else:
            metrics=preliminary
    for col,label,value in zip(st.columns(4),['Proteins','Unique protein pairs','Mapped orthogroups','Excluded reference transfers'],[len(nodes),graph.number_of_edges(),nodes.loc[nodes.orthogroup.ne(''),'orthogroup'].nunique(),len(excluded)]):col.metric(label,value)
    st.caption('The separate-protein pan view retains species nodes. The orthogroup view uses source workbook results after unique STRING query mapping, exact identifier/alias mapping, or cited curated mappings. Layers organize functional roles; unresolved nodes remain visible.')
    colors=st.radio('Color nodes by',['Adhesion layer','Species','Community','Protein family'],horizontal=True,key=key+'colors')
    layout=st.radio('Network layout',['Layered architecture','Force-directed'],horizontal=True,key=key+'layout')
    if layout=='Force-directed' and graph.number_of_nodes()>400:
        st.info('Force-directed layout is available for up to 400 displayed proteins. Filter to a family, community or neighborhood; showing the layered architecture meanwhile.')
        layout='Layered architecture'
    size_by=st.selectbox('Size nodes by',['Degree','Betweenness','Closeness','Uniform'],key=key+'size')
    labels=st.checkbox('Label proteins',key=key+'labels')
    pos={}
    if layout=='Layered architecture':
        for li,layer in enumerate(LAYERS):
            for si,species in enumerate(SPECIES):
                sub=metrics[(metrics.layer==layer)&(metrics.species==species)].sort_values('identifier')
                for j,identifier in enumerate(sub.identifier):pos[identifier]=(si*3+(j+1)/(len(sub)+1)*2,li)
    else:
        pos=nx.spring_layout(graph,seed=23,iterations=35)
    fig=go.Figure()
    for i,(relation,group) in enumerate(edges.groupby('relation')):
        x=[];y=[]
        for r in group.itertuples():
            p,q=pos[r.node1_string_id],pos[r.node2_string_id];x += [p[0],q[0],None];y += [p[1],q[1],None]
        fig.add_trace(go.Scatter(x=x,y=y,mode='lines',name=relation,line=dict(color='#bbc8d1' if relation.startswith('Functional association') else '#d67b31',width=1 if relation.startswith('Functional association') else 2,dash='solid' if relation.startswith('Functional association') else 'dash'),hoverinfo='skip'))
    column={'Adhesion layer':'layer','Species':'species','Community':'community','Protein family':'Family'}[colors]
    size_field={'Degree':'degree','Betweenness':'betweenness','Closeness':'closeness'}.get(size_by)
    largest_size=metrics[size_field].max() if size_field else 1
    for i,(category,group) in enumerate(metrics.groupby(column)):
        sizes=12 if size_field is None else 10+24*(group[size_field]/(largest_size or 1)).pow(.5)
        fig.add_trace(go.Scatter(x=[pos[n][0] for n in group.identifier],y=[pos[n][1] for n in group.identifier],mode='markers+text' if labels else 'markers',text=group.node,textposition='top center',name=str(category),marker=dict(color=COLORS.get(category,px.colors.qualitative.Alphabet[i%26]),size=sizes,line=dict(color='white',width=1)),customdata=group[['identifier','Family','layer_basis','degree','betweenness','closeness','community','clustering_coefficient','k_core']].values,hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}<br>Degree %{customdata[3]} · Betweenness %{customdata[4]:.3f}<br>Closeness %{customdata[5]:.3f} · Community %{customdata[6]}<br>Local clustering %{customdata[7]:.3f} · k-core %{customdata[8]}<extra></extra>'))
    axes=(dict(tickvals=[1,4,7],ticktext=list(SPECIES.values()),range=[-.3,8.5]),
          dict(tickvals=list(range(7)),ticktext=LAYERS,autorange='reversed')) if layout=='Layered architecture' else (dict(visible=False),dict(visible=False,scaleanchor='x'))
    fig.update_layout(height=680,xaxis=axes[0],yaxis=axes[1],legend=dict(orientation='h',y=-.15),margin=dict(l=10,r=10,t=10,b=10),plot_bgcolor='#f3f7fa',dragmode='pan')
    event=st.plotly_chart(fig,width='stretch',key=key+'layered',on_select='rerun',selection_mode='points',config={'displaylogo':False,'scrollZoom':True})
    selected_points=event.selection.points if event else []
    if selected_points:
        selected_id=selected_points[0].get('customdata',[None])[0]
        selected=metrics[metrics.identifier.eq(selected_id)]
        if not selected.empty:
            row=selected.iloc[0]
            st.info(f"Selected {row['node']} · {SPECIES.get(row['species'],row['species'])} · {row['Family']} · degree {row['degree']} · betweenness {row['betweenness']:.3f} · closeness {row['closeness']:.3f} · community {row['community']}")
    tabs=st.tabs(['Edge evidence','Topology & communities','Candidate prioritization','Reconstruction inputs'])
    with tabs[0]:
        st.dataframe(edges,width='stretch',hide_index=True)
        st.download_button('Download edge evidence',edges.to_csv(index=False),'reconstruction_edges.csv',key=key+'edge_csv')
        if len(excluded):st.warning(f'{len(excluded)} reference transfers failed the evidence gate.');st.dataframe(excluded)
    with tabs[1]:
        st.caption('Every metric is recalculated on the displayed, undirected, unweighted simple graph after filtering. Isolates remain when selected. Cross-species centralities depend on graph size; compare species in their separate views. Centrality does not establish biological essentiality.')
        a,b,c,d=st.columns(4)
        a.metric('Connected components',metrics.component.nunique())
        b.metric('Communities',metrics.community.nunique())
        c.metric('Mean local clustering',f'{metrics.clustering_coefficient.mean():.3f}')
        d.metric('Maximum k-core',int(metrics.k_core.max()))
        centrality_tab,matrix_tab,cluster_tab=st.tabs(['Centrality analysis','Distance & adjacency matrices','Topological clustering'])
        with centrality_tab:
            st.markdown('**Betweenness** measures the fraction of shortest paths passing through a protein. **Closeness** is inverse farness, adjusted for the number of reachable proteins when the graph is disconnected.')
            st.latex(r'C_C(i)=\frac{r_i-1}{N-1}\,\frac{r_i-1}{\sum_{j\in R_i,\,j\ne i}d(i,j)}')
            st.caption('N = displayed proteins; rᵢ = proteins reachable from i, including i; farness is the sum of finite shortest-path distances. Betweenness uses NetworkX normalized undirected shortest-path centrality.')
            first=[c for c in ['node','sequence_id','Family','species','identifier','orthogroup','layer','degree','betweenness','closeness','farness','reachable_nodes','clustering_coefficient','k_core','component','component_size','community'] if c in metrics]
            st.dataframe(metrics[first],width='stretch',hide_index=True)
            centrality_metric=st.selectbox('Rank proteins by',['betweenness','closeness','degree','clustering_coefficient','k_core'],key=key+'rank_metric')
            top=metrics.nlargest(20,centrality_metric)
            st.plotly_chart(px.bar(top,x='node',y=centrality_metric,color='species',hover_data=['identifier','Family','community'],title=f'Top 20 by {centrality_metric.replace("_"," ")}'),width='stretch',key=key+'centrality_rank')
            st.plotly_chart(px.scatter(metrics,x='degree',y='betweenness',color='community',hover_name='node',hover_data=['sequence_id','Family','orthogroup','layer','closeness','clustering_coefficient'],size='closeness',title='Hubs and potential bottlenecks'),width='stretch',key=key+'centrality')
        with matrix_tab:
            st.caption('Shortest-path distances are calculated through the full displayed graph, even when intermediate proteins are outside the selected matrix rows. Blank cells mean no connecting path. Adjacency shows direct retained associations only.')
            default_ids=metrics.sort_values(['betweenness','degree'],ascending=False).identifier.head(20).tolist()
            labels_by_id={row.identifier:f'{row.node} · {row.species} · {row.identifier}' for row in metrics.itertuples()}
            matrix_ids=st.multiselect('Proteins in matrices',sorted(graph),default=default_ids,max_selections=40,
                                      format_func=lambda identifier:labels_by_id.get(identifier,identifier),key=key+'matrix_nodes')
            if matrix_ids:
                distances,adjacency=network_matrices(graph,matrix_ids)
                by_id=metrics.set_index('identifier')
                short_labels=[f"{by_id.loc[n,'node']} · {by_id.loc[n,'species']}" for n in matrix_ids]
                path_fig=go.Figure(go.Heatmap(z=distances.values,x=short_labels,y=short_labels,colorscale='YlGnBu',
                                              colorbar=dict(title='Hops'),hovertemplate='%{y} → %{x}<br>Distance: %{z}<extra></extra>'))
                path_fig.update_layout(title='Shortest-path distance matrix',height=max(480,22*len(matrix_ids)+140),xaxis_tickangle=-55)
                st.plotly_chart(path_fig,width='stretch',key=key+'distance_matrix')
                adjacency_fig=go.Figure(go.Heatmap(z=adjacency.values,x=short_labels,y=short_labels,zmin=0,zmax=1,
                                                   colorscale=[[0,'#ffffff'],[1,'#08743f']],showscale=False,
                                                   hovertemplate='%{y} ↔ %{x}<br>Direct edge: %{z}<extra></extra>'))
                adjacency_fig.update_layout(title='Direct-association adjacency matrix',height=max(480,22*len(matrix_ids)+140),xaxis_tickangle=-55)
                st.plotly_chart(adjacency_fig,width='stretch',key=key+'adjacency_matrix')
                a,b=st.columns(2)
                a.download_button('Download distance matrix · CSV',distances.to_csv().encode('utf-8-sig'),'network_shortest_paths.csv',key=key+'distance_csv')
                b.download_button('Download adjacency matrix · CSV',adjacency.to_csv().encode('utf-8-sig'),'network_adjacency.csv',key=key+'adjacency_csv')
            else:
                st.info('Select at least one protein to display the matrices.')
        with cluster_tab:
            st.caption('Communities use greedy modularity on the displayed graph. Local clustering measures triangles among a protein’s neighbors; k-core records the largest minimum-degree core containing it. These are complementary topological partitions, not protein-family assignments.')
            summary=metrics.groupby('community').agg(proteins=('identifier','size'),species=('species','nunique'),
                mean_degree=('degree','mean'),mean_betweenness=('betweenness','mean'),
                mean_clustering=('clustering_coefficient','mean'),max_k_core=('k_core','max')).reset_index()
            st.dataframe(summary,width='stretch',hide_index=True)
            composition=pd.crosstab(metrics.community,metrics.layer).reindex(columns=LAYERS,fill_value=0)
            st.plotly_chart(px.imshow(composition,labels=dict(x='Adhesion layer',y='Community',color='Proteins'),
                                      text_auto=True,color_continuous_scale='YlGn',title='Community × adhesion-layer matrix'),
                            width='stretch',key=key+'community_matrix')
            st.plotly_chart(px.scatter(metrics,x='k_core',y='clustering_coefficient',color='community',size='degree',
                                       hover_name='node',hover_data=['Family','layer','betweenness'],title='Dense cores and local clustering'),
                            width='stretch',key=key+'cluster_scatter')
            if st.checkbox('Compare a Girvan–Newman edge-betweenness split',key=key+'girvan'):
                if graph.number_of_nodes()>60:
                    st.info('Girvan–Newman is available for at most 60 displayed proteins. Use the neighborhood or family filters to define a smaller subnetwork.')
                elif graph.number_of_edges():
                    partition=next(nx.community.girvan_newman(graph))
                    membership={node:i+1 for i,group in enumerate(partition) for node in group}
                    comparison=metrics[['node','identifier','Family','community','k_core']].copy()
                    comparison['girvan_newman_group']=comparison.identifier.map(membership)
                    st.dataframe(comparison,width='stretch',hide_index=True)
                else:
                    st.info('The displayed network has no edges to split.')
        st.download_button('Download topology analysis',metrics.to_csv(index=False),'network_topology.csv',key=key+'metrics_csv')
    with tabs[2]:
        try: ranking=prioritize(metrics,graph,all_nodes)
        except ValueError as exc:st.error(str(exc));ranking=pd.DataFrame()
        st.caption('Workbook domain coverage and topology agreement, aligned motif residue conservation, branch support and aligned host divergence populate the evidence features. Calculation details are retained in the basis columns. Exploratory integrated score = equal-weight mean of seven 0–1 features, calculated only for complete records. Conservation uses source HOG species coverage / 3 where available, otherwise mapped network orthogroup coverage / 3; connectivity is degree centrality. Source-derived values can be overridden by cited curated values. Motif conservation measures aligned peptide residue identity; host divergence is one minus identity to the closest aligned human homologue over paired amino-acid sites. Phylogenetic support uses the smaller SH-aLRT/UFBoot value for the smallest multispecies Schistosoma clade; it is branch support, not an orthology probability. Missing values are not zero. The evidence-convergence assessment complements the numerical score. Incomplete records are listed by interface connections, betweenness and degree. Host orthologues flag selectivity review but do not measure sequence similarity or exclude proteins.')
        st.dataframe(ranking,width='stretch',hide_index=True)
        st.download_button('Download prioritization and missing evidence',ranking.to_csv(index=False),'candidate_prioritization.csv',key=key+'rank_csv')
    with tabs[3]:
        st.write('Populate the TSV templates in adhesome_network/curation. No illustrative biological records are prefilled. Reload source files after editing. References must identify the evidence supporting each assessment.')
        st.dataframe(metrics[[c for c in ['identifier','sequence_id','mapping_basis','mapping_candidates','mapping_source','mapping_identity_percent','mapping_bitscore','mapping_query_evidence','mapping_review','user_nominated_sequence_ids','user_mapping_interpretation','user_mapping_note','orthogroup','orthology_basis','source_HOG_species_count','Family','layer','layer_basis','evidence_review_stage'] if c in metrics]],width='stretch',hide_index=True)
        for name in ['node_mapping.tsv','reference_interactions.tsv','candidate_evidence.tsv','node_interpretations.tsv']:
            p=EVIDENCE_DIR/name
            if p.exists():st.download_button('Download '+name,p.read_bytes(),name,key=key+name)

def orthogroup_view(nodes,edges,key):
    mapped=nodes[nodes.orthogroup.ne('')]
    if mapped.empty:
        st.info('Orthology-merged reconstruction is not yet available: add cited node-to-orthogroup assignments in node_mapping.tsv. Workbook orthogroups also require a resolved network-to-candidate identifier. Shared family names alone are not treated as orthology.');return
    lookup=mapped.set_index('identifier').orthogroup.to_dict();rows=[]
    for r in edges.itertuples():
        if r.node1_string_id in lookup and r.node2_string_id in lookup:
            a,b=sorted([lookup[r.node1_string_id],lookup[r.node2_string_id]])
            rows.append(dict(source=a,target=b,species=r.species,relation=r.relation,evidence=r.evidence,reference=r.reference))
    if not rows:st.info('Mapped orthogroups have no retained associations.');return
    summary=pd.DataFrame(rows).groupby(['source','target','relation']).agg(species=('species',lambda x:' | '.join(sorted(set(x)))),species_count=('species','nunique'),evidence=('evidence',lambda x:' | '.join(sorted(set(x)))),references=('reference',lambda x:' | '.join(sorted(set(x))))).reset_index()
    summary['conservation']=summary.species_count.map(lambda n:'Observed in all three species' if n==3 else 'Observed in two species' if n==2 else 'Observed in one species; specificity unproven')
    st.caption(f'{len(mapped)} of {len(nodes)} proteins have source-supported orthogroup assignments. Absence of an exported edge does not establish species specificity. Conservation labels describe retained, mapped associations only. Within-orthogroup associations remain in the table.')
    graph=nx.from_pandas_edgelist(summary,'source','target');pos=nx.spring_layout(graph,seed=42)
    fig=go.Figure()
    for category,group in summary.groupby('conservation'):
        x=[];y=[]
        for r in group.itertuples():x += [pos[r.source][0],pos[r.target][0],None];y += [pos[r.source][1],pos[r.target][1],None]
        fig.add_trace(go.Scatter(x=x,y=y,mode='lines',name=category))
    fig.add_trace(go.Scatter(x=[pos[n][0] for n in graph],y=[pos[n][1] for n in graph],text=list(graph),mode='markers+text',textposition='top center',name='Orthogroups'))
    fig.update_layout(height=550,xaxis_visible=False,yaxis_visible=False)
    st.plotly_chart(fig,width='stretch',key=key+'orthograph');st.dataframe(summary,width='stretch',hide_index=True)
    st.download_button('Download orthogroup associations',summary.to_csv(index=False),'orthogroup_associations.csv',key=key+'ortho_csv')
