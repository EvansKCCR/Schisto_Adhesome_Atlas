"""Deterministic presentation metadata for the unmodified orthogroup consensus graph."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from candidate_profiles import PROFILE_FIELDS
from design_system import network_style

REGIONS = [
    ('extracellular','Extracellular environment','#3e7b69','#edf6f1'),
    ('membrane','Plasma membrane & receptors','#316b9a','#edf4fa'),
    ('proximal','Membrane-proximal adhesome','#a27221','#fcf5e7'),
    ('signaling','Intracellular signaling','#77519c','#f4eff9'),
    ('cytoskeleton','Actin / cytoskeletal context','#b75b41','#fcf0eb'),
    ('unresolved','Unresolved / Multiple Localizations','#64746d','#f0f3f1'),
]
REGION_LABELS={key:label for key,label,_,_ in REGIONS}
PALETTE=['#327566','#316b9a','#94651a','#7950a0','#af573f','#546f39','#8a526b','#3e7d87','#6d6754','#5270a4','#985f23','#607a62']
PROXIMAL={'talin','kindlin','ILK','PINCH_like'}
CYTOSKELETAL={'vinculin','alpha_actinin','filamin','PDLIM_family','actin','actin_conventional',
    'cofilin','profilin','coronin_like','spectrin_like','tubulin_like','arp1_like','arp2_like',
    'arp3_like','arp10_like','zyxin_like','zyxin_ajuba_like'}
DISCLAIMER=('Network organization represents a comparative, annotation-informed adhesome hypothesis. '
    'Spatial placement and transferred interactions do not establish experimentally validated protein '
    'localization or physical interactions in schistosomes.')
RULES = [
    'Functional annotations retain all module labels from the active family inventory. Different annotated modules are not collapsed into a new biological assignment.',
    'Functional neighborhoods are connected components within each primary annotated module, using the existing undirected projected edges. Isolated orthogroups remain isolated neighborhoods.',
    'A singleton DeepLoc Extracellular prediction maps to the extracellular region; singleton Cell membrane maps to the membrane region.',
    'For singleton Cytoplasm predictions, annotated talin/kindlin/ILK/PINCH families define membrane-proximal context; annotated cytoskeletal families define cytoskeletal context; inventory kinase/phosphatase or adaptor/GTPase modules define signaling context.',
    'Missing, multiple, other-organelle or conflicting member predictions, and cytoplasmic families lacking one of those functional contexts, remain in Unresolved / Multiple Localizations. All member-level predictions remain visible.',
    'An orthogroup receives a resolved region only when every filtered member yields the same resolved region. Grades are preserved independently and are not interaction confidence scores.',
    'Circle radius = 12 + 4 × log2(1 + unique candidate count), in layout units. Label controls never change the quantitative circle radius.',
    'Layout coordinates, region assignments and neighborhoods are presentation metadata only. Communities are the existing greedy-modularity topology result, not annotated biological modules.',
]


def _clean(value):
    return '' if pd.isna(value) else str(value).strip()


def member_region(row):
    """Strict prediction agreement; a family role alone is never localization evidence."""
    prediction=_clean(row.get('DeepLoc_2.1',''))
    locations=[v.strip() for v in prediction.split('|') if v.strip()]
    if len(locations)!=1:return 'unresolved'
    if locations[0]=='Extracellular':return 'extracellular'
    if locations[0]=='Cell membrane':return 'membrane'
    if locations[0]!='Cytoplasm':return 'unresolved'
    family=_clean(row.get('family',''));module=_clean(row.get('module',''))
    if family in PROXIMAL:return 'proximal'
    if family in CYTOSKELETAL:return 'cytoskeleton'
    if module in {'Kinase & phosphatase signalling','Adaptors & small GTPases'}:return 'signaling'
    return 'unresolved'


def _ordered(ids,graph,lookup):
    """Breadth-first ordering keeps existing connected neighbors in nearby grid cells."""
    ids=set(ids);remaining=set(ids);order=[]
    while remaining:
        root=min(remaining,key=lambda n:(-graph.degree(n),lookup[n]['family'],n))
        queue=[root];remaining.remove(root)
        while queue:
            node=queue.pop(0);order.append(node)
            neighbors=sorted(set(graph[node])&remaining,key=lambda n:(lookup[n]['community'],-graph.degree(n),lookup[n]['family'],n))
            for other in neighbors:remaining.remove(other);queue.append(other)
    return order


def _band_layout(groups,lookup,graph):
    columns=min(28,max(4,math.ceil(math.sqrt(max(1,len(lookup))*2.3))))
    width=columns*154+168;positions={};bands=[];top=24
    for key,label,ids,color,fill in groups:
        order=_ordered(ids,graph,lookup)
        rows=max(1,math.ceil(len(order)/columns));height=230+(rows-1)*118 if order else 130
        bands.append(dict(id=key,label=label,x=24,y=top,width=width-48,height=height,color=color,fill=fill,count=len(ids)))
        for i,node in enumerate(order):positions[node]=dict(x=114+(i%columns)*154,y=top+145+(i//columns)*118)
        top+=height+28
    return dict(positions=positions,regions=bands,width=width,height=top+24)


def _functional_layout(nodes,graph,lookup,module_colors):
    """Pack biological module cards, each retaining its distinct connected neighborhoods."""
    positions={};regions=[];tiles=[]
    width=max(1000,min(5400,math.ceil(math.sqrt(max(1,len(nodes))*2.3))*190+80))
    outer_x=24;outer_y=24;outer_height=0
    modules=sorted({n['primary_module'] for n in nodes},key=lambda m:(-sum(n['primary_module']==m for n in nodes),m))
    for module in modules:
        ids={n['id'] for n in nodes if n['primary_module']==module}
        components=sorted(nx.connected_components(graph.subgraph(ids)),key=lambda g:(-len(g),sorted(g)))
        module_columns=min(20,max(3,math.ceil(math.sqrt(len(ids)*2.4))))
        module_width=min(width-48,module_columns*154+120)
        local_positions={};local_tiles=[];x=24;y=140;row_height=0
        for component in components:
            order=_ordered(component,graph,lookup)
            columns=min(len(order),13,max(1,(module_width-72)//154),max(1,math.ceil(math.sqrt(len(order)*1.7))))
            rows=math.ceil(len(order)/columns);tw=columns*154+24;th=rows*118+64
            if x+tw>module_width-24:x=24;y+=row_height+20;row_height=0
            cid=lookup[order[0]]['module_component']
            local_tiles.append(dict(id=cid,label=cid+(' · unconnected' if len(order)==1 else ' · connected neighborhood'),x=x,y=y,width=tw,height=th))
            for i,node in enumerate(order):local_positions[node]=dict(x=x+88+(i%columns)*154,y=y+86+(i//columns)*118)
            x+=tw+20;row_height=max(row_height,th)
        module_height=y+row_height+24
        if outer_x+module_width>width-24:outer_x=24;outer_y+=outer_height+28;outer_height=0
        regions.append(dict(id=module,label=module,x=outer_x,y=outer_y,width=module_width,height=module_height,color=module_colors[module],fill='#f5f8f6',count=len(ids)))
        for node,p in local_positions.items():positions[node]=dict(x=p['x']+outer_x,y=p['y']+outer_y)
        for tile in local_tiles:tiles.append({**tile,'x':tile['x']+outer_x,'y':tile['y']+outer_y})
        outer_x+=module_width+28;outer_height=max(outer_height,module_height)
    return dict(positions=positions,regions=regions,tiles=tiles,width=width,height=outer_y+outer_height+24)


def _free_layout(graph,lookup):
    """Seeded force initialization followed by collision-free nearest-grid placement."""
    if len(graph)<500:
        raw=nx.spring_layout(graph,seed=20,iterations=120,weight=None,k=1.7/math.sqrt(max(1,len(graph))))
    else:
        # NetworkX automatically requires SciPy at 500 nodes. Keep the existing
        # NumPy-only deployment usable as the inventory grows; forces use original
        # edges only, with blockwise repulsion to bound intermediate memory.
        identifiers=sorted(graph);index={node:i for i,node in enumerate(identifiers)}
        points=np.random.default_rng(20).random((len(identifiers),2));k=1.7/math.sqrt(len(graph));temperature=.12
        pairs=np.array([(index[a],index[b]) for a,b in graph.edges],dtype=int).reshape(-1,2)
        for _ in range(60):
            displacement=np.zeros_like(points)
            for start in range(0,len(points),128):
                delta=points[start:start+128,None,:]-points[None,:,:]
                distance=np.maximum(np.linalg.norm(delta,axis=2),.02)
                displacement[start:start+128]=(delta*(k*k/(distance*distance))[:,:,None]).sum(axis=1)
            if len(pairs):
                delta=points[pairs[:,0]]-points[pairs[:,1]]
                force=delta*(np.linalg.norm(delta,axis=1)/k)[:,None]
                np.add.at(displacement,pairs[:,0],-force);np.add.at(displacement,pairs[:,1],force)
            norm=np.maximum(np.linalg.norm(displacement,axis=1),1e-8)
            points+=displacement/norm[:,None]*np.minimum(norm,temperature)[:,None];temperature*=.95
        points-=points.mean(axis=0);points/=max(float(np.abs(points).max()),1e-8)
        raw=dict(zip(identifiers,points))
    columns=max(1,math.ceil(math.sqrt(len(graph)*1.6)));rows=math.ceil(len(graph)/columns)
    cells={(x,y) for y in range(rows) for x in range(columns)};positions={}
    xs=[float(p[0]) for p in raw.values()];ys=[float(p[1]) for p in raw.values()]
    dx=max(xs,default=1)-min(xs,default=0);dy=max(ys,default=1)-min(ys,default=0)
    for node in sorted(graph,key=lambda n:(-graph.degree(n),n)):
        x=(float(raw[node][0])-min(xs))/(dx or 1)*(columns-1);y=(float(raw[node][1])-min(ys))/(dy or 1)*(rows-1)
        cell=min(cells,key=lambda c:((c[0]-x)**2+(c[1]-y)**2,c[1],c[0]));cells.remove(cell)
        positions[node]=dict(x=110+cell[0]*154,y=100+cell[1]*118)
    return dict(positions=positions,regions=[],width=columns*154+80,height=rows*118+80)


def _community_layout(nodes,graph,lookup):
    positions={};regions=[];width=min(4480,max(900,math.ceil(math.sqrt(max(1,len(nodes))*2.3))*154+168));x=24;y=24;row_height=0
    groups=sorted({n['community'] for n in nodes},key=lambda c:(-sum(n['community']==c for n in nodes),c))
    for community in groups:
        order=_ordered([n['id'] for n in nodes if n['community']==community],graph,lookup)
        columns=min(len(order),13,max(1,math.ceil(math.sqrt(len(order)*1.7))))
        rows=math.ceil(len(order)/columns);w=columns*154+36;h=rows*118+110
        if x+w>width-24:x=24;y+=row_height+24;row_height=0
        regions.append(dict(id=str(community),label=f'Community {community}',x=x,y=y,width=w,height=h,
            color=PALETTE[(community-1)%len(PALETTE)],fill='#f4f7fa',count=len(order)))
        for i,node in enumerate(order):positions[node]=dict(x=x+95+(i%columns)*154,y=y+110+(i//columns)*118)
        x+=w+24;row_height=max(row_height,h)
    return dict(positions=positions,regions=regions,width=width,height=y+row_height+24)


def build_view_model(metrics,edges,members):
    """All nodes, candidate records and unique pairs; raw analytical inputs are untouched."""
    members=members[members.orthogroup.isin(metrics.identifier)].copy()
    graph=nx.Graph();graph.add_nodes_from(sorted(metrics.identifier))
    graph.add_edges_from(sorted({tuple(sorted(pair)) for pair in zip(edges.node1_string_id,edges.node2_string_id)}))
    records=json.loads(members.reindex(columns=list(dict.fromkeys(PROFILE_FIELDS+['module','DeepLoc_2.1','DeepTMHMM','SignalP.v6.0']))).to_json(orient='records'))
    by_protein={row['sequence_id']:row for row in records}
    nodes=[]
    for row in metrics.sort_values('identifier').to_dict('records'):
        group=members[members.orthogroup.eq(row['identifier'])].drop_duplicates('sequence_id')
        functional=sorted({_clean(v) for v in group.module if _clean(v) and _clean(v)!='Other family context'})
        module=functional[0] if len(functional)==1 else 'Multiple / unresolved functional annotations'
        votes=Counter(member_region(m) for m in group.to_dict('records'))
        region=next(iter(votes)) if len(votes)==1 else 'unresolved'
        predicted=Counter(_clean(v) or 'Not recorded' for v in group.get('DeepLoc_2.1',pd.Series('',index=group.index)))
        grades=Counter(group.grade)
        node=dict(id=row['identifier'],label=row['identifier'],short_label='…'+row['identifier'][4:],
            family=row['Family'],families=sorted(set(group.family)),modules=functional,primary_module=module,
            compartment=region,compartment_label=REGION_LABELS[region],location_votes=dict(sorted(votes.items())),
            predicted_localizations=dict(sorted(predicted.items())),grades={k:int(grades[k]) for k in ('A','B','C','D')},
            member_ids=sorted(set(group.sequence_id)),member_count=int(group.sequence_id.nunique()),
            species=sorted(set(group.species)),community=int(row['community']),degree=int(row['degree']),
            betweenness=float(row['betweenness']),closeness=float(row['closeness']),
            radius=12+4*math.log2(1+group.sequence_id.nunique()))
        node['search_text']=' '.join([node['id'],node['family']]+node['member_ids']+[str(by_protein[p].get('candidate_annotation','')) for p in node['member_ids']]).lower()
        nodes.append(node)
    lookup={n['id']:n for n in nodes}
    modules=sorted({n['primary_module'] for n in nodes})
    module_colors={m:PALETTE[i%len(PALETTE)] for i,m in enumerate(modules)}
    for index,module in enumerate(modules,1):
        ids={n['id'] for n in nodes if n['primary_module']==module}
        components=sorted(nx.connected_components(graph.subgraph(ids)),key=lambda g:(-len(g),sorted(g)))
        for ci,component in enumerate(components,1):
            for identifier in component:lookup[identifier]['module_component']=f'M{index:02}-C{ci:03}'
    cellular=_band_layout([(key,label,[n['id'] for n in nodes if n['compartment']==key],color,fill) for key,label,color,fill in REGIONS],lookup,graph)
    # Every evidence row remains accessible on the corresponding unique pair.
    evidence_columns=[c for c in edges if c not in {'source_candidates','target_candidates'}]
    evidence=json.loads(edges[evidence_columns].to_json(orient='records'))
    pair_rows={}
    for i,row in enumerate(evidence):pair_rows.setdefault(tuple(sorted((row['node1_string_id'],row['node2_string_id']))),[]).append(i)
    visual_edges=[dict(id='::'.join(pair),source=pair[0],target=pair[1],evidence_rows=indices) for pair,indices in sorted(pair_rows.items())]
    return dict(nodes=nodes,edges=visual_edges,evidence=evidence,candidates=by_protein,
        layouts=dict(cellular=cellular,functional=_functional_layout(nodes,graph,lookup,module_colors),community=_community_layout(nodes,graph,lookup),free=_free_layout(graph,lookup)),
        module_colors=module_colors,regions=[dict(id=k,label=l,color=c,fill=f) for k,l,c,f in REGIONS],
        rules=RULES,disclaimer=DISCLAIMER,rule_version='consensus-spatial-1',
        graph_sha256=hashlib.sha256(json.dumps(dict(nodes=sorted(graph),edges=sorted(sorted(pair) for pair in graph.edges)),sort_keys=True).encode()).hexdigest(),
        totals=dict(nodes=len(nodes),pairs=graph.number_of_edges(),evidence_rows=len(edges),candidates=len(by_protein)))


def consensus_network_html(model,app_url=''):
    payload={**model,'app_url':app_url}
    template=Path(__file__).with_name('consensus_view.html').read_text(encoding='utf-8')
    return template.replace('__ATLAS_STYLE__',network_style()).replace('__PAYLOAD__',json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<','\\u003c'))


def layout_signature():
    """Invalidate saved presentation coordinates when any annotation/layout rule changes."""
    return hashlib.sha256(Path(__file__).read_bytes()+json.dumps(PROFILE_FIELDS).encode()).hexdigest()


def layout_table(model):
    """Inspectable presentation metadata, separate from centrality/evidence downloads."""
    rows=[]
    for mode,layout in model['layouts'].items():
        for node in model['nodes']:
            rows.append(dict(orthogroup=node['id'],layout=mode,**layout['positions'][node['id']],
                conceptual_region=node['compartment_label'],functional_annotations=' | '.join(node['modules']),
                primary_module=node['primary_module'],connected_neighborhood=node['module_component'],
                algorithmic_community=node['community'],predicted_localizations=json.dumps(node['predicted_localizations']),
                radius=node['radius'],rule_version=model['rule_version']))
    return pd.DataFrame(rows)
