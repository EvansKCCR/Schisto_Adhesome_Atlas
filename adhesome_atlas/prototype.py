"""Family-level prototype map and evidence-stratified hypothesis exports."""
import json
import re
from pathlib import Path

import pandas as pd


FAMILY_NODES = {
    'collagen_like': 'collagen', 'C_type_lectin_Ig_FN3_like': 'fn3',
    'laminin_like': 'laminin', 'integrin_alpha': 'inta', 'integrin_beta': 'intb',
    'talin': 'talin', 'kindlin': 'kindlin', 'PINCH_like': 'pinch', 'ILK': 'ilk', 'vinculin': 'vinculin',
    'alpha_actinin': 'actinin', 'filamin': 'filamin', 'paxillin_like': 'paxillin',
    'zyxin_like': 'zyxin', 'FAK': 'fak', 'Src': 'src', 'actin': 'actin',
    'cofilin': 'cofilin', 'PTP_PEST': 'ptppest', 'profilin': 'profilin',
    'Shc': 'shc', 'Grb2': 'grb2', 'Nck': 'nck',
}
COMPLEX_NODE = 'integrin_ab'
COMPLEX_LABEL = 'Putative integrin αβ heterodimer'
REFERENCE_ONLY_NODES = {'parvin': 'Parvin (unassigned reference family)'}
CONTEXT_ONLY_NODES = {
    'vascular_context': 'Host-vascular context (hypothesis)',
    'vkr1': 'SmVKR1 membrane receptor (S. mansoni evidence context)',
}

def read_map_edges(path: Path):
    """Read edge evidence from the diagram so exports track its architecture."""
    if not path.is_file():
        return []
    match = re.search(r'const edges=(\[.*?\]);', path.read_text(encoding='utf-8'), re.S)
    if not match:
        return []
    block = match.group(1)
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        pass
    records = []
    for match in re.finditer(r"\{a:'[^']+',b:'[^']+',kind:'[^']+'[^{}]*\}", block):
        record = {}
        for field in re.finditer(r"(\w+):(?:'([^']*)'|(true|false))", match.group()):
            record[field.group(1)] = (field.group(3) == 'true' if field.group(3) else field.group(2))
        records.append(record)
    return records


MAP_EDGE_RECORDS = read_map_edges(Path(__file__).with_name('Schistosome_adhesome_interactive.html'))
MAP_EDGES = [(edge['a'], edge['b'], edge['kind'], edge['relation']) for edge in MAP_EDGE_RECORDS]


def candidate_rows(adhesome, fn3):
    """Keep audited families and the separately reviewed FN3 ligand screen."""
    retained = adhesome[adhesome.audit_classification.isin(['Supported','Provisional'])].copy()
    retained['prototype_family'] = retained.reviewed_family
    retained['evidence_tier'] = retained.audit_classification.map({'Supported':'Core family-retained','Provisional':'Provisional'})
    retained.loc[retained.family_decision.eq('Retain provisionally'),'evidence_tier'] = 'Parasite-specific supported cluster'
    retained['source_collection'] = 'Adhesome candidates'
    combined = retained
    combined['map_node'] = combined.prototype_family.map(FAMILY_NODES)
    return combined[combined.map_node.notna()].copy()


def map_payload(rows, focus_family=None, focus_candidate=None):
    fields = ['sequence_id','species','family','assigned_family','prototype_family','map_node','evidence_tier','grade',
              'family_decision','assignment_interpretation','orthogroup','domain_evidence','topology_evidence',
              'motif_context_evidence','source_collection']
    displayed = rows.reindex(columns=fields).fillna('').astype(str)
    return {
        'candidates': displayed.to_dict('records'),
        'focus_node': FAMILY_NODES.get(focus_family,''),
        'focus_candidate': focus_candidate or '',
    }


def interactive_html(path: Path, rows, focus_family=None, focus_candidate=None):
    """Enhance the supplied standalone HTML without changing its source layout."""
    html = path.read_text(encoding='utf-8')
    payload = json.dumps(map_payload(rows, focus_family, focus_candidate), ensure_ascii=False).replace('<', '\\u003c')
    enhancement = r"""
<style>
.node.atlas-focus rect{fill:#fff3b0;stroke-width:5}.node.atlas-neighbor rect{fill:#f0fdf4;stroke-width:3}
.node.provisional rect{stroke-dasharray:6 4;fill:#fffbeb}.chip.provisional{background:#fef3c7;color:#92400e}
.edge.atlas-dim{opacity:.13}.node.atlas-dim{opacity:.36}
#info select{width:100%;padding:7px;border:1px solid #94a3b8;border-radius:6px;background:white;color:#0f172a}
#info .atlas-candidate{padding:8px;background:#f7f9fc;border-left:4px solid #16a34a;margin-top:9px}
</style>
<script>
const atlasPayload = __ATLAS_PAYLOAD__;
const atlasOriginalShowNode = showNode;
const atlasOriginalDrawEdges = drawEdges, atlasOriginalDrawNodes = drawNodes;
let atlasFocusNode = null;
drawEdges=function(){atlasOriginalDrawEdges();if(atlasFocusNode)atlasFocus(atlasFocusNode)};
drawNodes=function(){atlasOriginalDrawNodes();if(atlasFocusNode)atlasFocus(atlasFocusNode)};
function atlasFocus(n){
  const neighbors=new Set(edges.filter(e=>e.a===n.id||e.b===n.id).map(e=>e.a===n.id?e.b:e.a));
  if(n.id==='inta'||n.id==='intb')edges.filter(e=>e.b==='integrin_ab'&&e.class==='ligand').forEach(e=>neighbors.add(e.a));
  if(edges.some(e=>e.a===n.id&&e.b==='integrin_ab'&&e.class==='ligand')){neighbors.add('inta');neighbors.add('intb')}
  document.querySelectorAll('.node').forEach(g=>{
    g.classList.toggle('atlas-focus',g.dataset.id===n.id);
    g.classList.toggle('atlas-neighbor',neighbors.has(g.dataset.id));
    g.classList.toggle('atlas-dim',g.dataset.id!==n.id&&!neighbors.has(g.dataset.id));
  });
  document.querySelectorAll('.edge').forEach((line,i)=>{
    const e=edges[i];
    const viaComplex=(['inta','intb'].includes(n.id)&&e.b==='integrin_ab'&&e.class==='ligand')||
      (neighbors.has('integrin_ab')&&e.a==='integrin_ab'&&['inta','intb'].includes(e.b));
    line.classList.toggle('atlas-dim',e.a!==n.id&&e.b!==n.id&&!viaComplex);
  });
}
function atlasText(parent,tag,text){const el=document.createElement(tag);el.textContent=text;parent.appendChild(el);return el}
function atlasCandidateDetail(parent,record){
  const box=document.createElement('div');box.className='atlas-candidate';parent.appendChild(box);
  atlasText(box,'strong',record.sequence_id+' · '+record.species);
  atlasText(box,'p',record.evidence_tier+' · '+(record.assignment_interpretation||record.family_decision||record.grade||'FN3 architecture screen'));
  if(record.family&&record.family!==record.prototype_family)atlasText(box,'p','Screening family: '+record.family+' → reviewed family: '+record.prototype_family);
  if(record.orthogroup)atlasText(box,'p','Orthogroup: '+record.orthogroup);
  if(record.domain_evidence)atlasText(box,'p','Domains: '+record.domain_evidence);
  if(record.topology_evidence)atlasText(box,'p','Topology: '+record.topology_evidence);
  if(record.motif_context_evidence)atlasText(box,'p','Motifs: '+record.motif_context_evidence);
}
showNode=function(n){
  atlasFocusNode=n;atlasOriginalShowNode(n);atlasFocus(n);
  const connected=edges.filter(e=>e.a===n.id||e.b===n.id);
  atlasText(info,'h3','Potential linked families');
  if(connected.length){const list=document.createElement('ul');info.appendChild(list);connected.forEach(e=>{
    const other=nodes.find(x=>x.id===(e.a===n.id?e.b:e.a));
    atlasText(list,'li',other.title+' · '+(e.evidence_class||e.kind)+(e.class==='ligand'?' · putative ligand–αβ heterodimer':''));
  })}else atlasText(info,'p','No explicit partner edge in the supplied prototype.');
  if(connected.some(e=>e.a===n.id&&e.b==='integrin_ab'&&e.class==='ligand'))
    atlasText(info,'p','This ligand class is linked to the putative receptor containing both integrin α and β families. The participating protein pair is unresolved.');
  if(n.id==='inta'||n.id==='intb'){
    atlasText(info,'h3','Putative ligands via the αβ heterodimer');
    const ligands=document.createElement('ul');info.appendChild(ligands);
    edges.filter(e=>e.b==='integrin_ab'&&e.class==='ligand').forEach(e=>atlasText(ligands,'li',nodes.find(x=>x.id===e.a).title));
  }
  const records=atlasPayload.candidates.filter(r=>n.id==='integrin_ab'?['inta','intb'].includes(r.map_node):r.map_node===n.id);
  if(n.id==='integrin_ab')atlasText(info,'p','Constituent family candidates are listed below; specific α–β protein pairings are not assigned.');
  atlasText(info,'h3',(n.id==='integrin_ab'?'Constituent family candidates':'Candidate proteins')+' ('+records.length+')');
  if(records.length){
    const select=document.createElement('select');select.setAttribute('aria-label','Select candidate protein');info.appendChild(select);
    const prompt=document.createElement('option');prompt.value='';prompt.textContent='Select a protein';select.appendChild(prompt);
    records.forEach(r=>{const option=document.createElement('option');option.value=r.sequence_id;option.textContent=r.sequence_id+' · '+r.evidence_tier;select.appendChild(option)});
    const detail=document.createElement('div');info.appendChild(detail);
    select.onchange=()=>{detail.innerHTML='';const record=records.find(r=>r.sequence_id===select.value);if(record)atlasCandidateDetail(detail,record)};
    if(atlasPayload.focus_candidate&&records.some(r=>r.sequence_id===atlasPayload.focus_candidate)){
      select.value=atlasPayload.focus_candidate;select.onchange();
    }
  }else atlasText(info,'p','No current candidate record is linked to this node.');
};
const initialFocus=nodes.find(n=>n.id===atlasPayload.focus_node)||
  nodes.find(n=>atlasPayload.candidates.some(r=>r.sequence_id===atlasPayload.focus_candidate&&r.map_node===n.id));
if(initialFocus)showNode(initialFocus);
</script>
""".replace('__ATLAS_PAYLOAD__', payload)
    return html.replace('</body>', enhancement + '</body>')


def hypothesis(rows, families, tiers, edge_kinds):
    edge_records = read_map_edges(Path(__file__).with_name('Schistosome_adhesome_interactive.html'))
    subset = rows[rows.prototype_family.isin(families) & rows.evidence_tier.isin(tiers)].copy()
    nodes = set(subset.map_node)
    counts = subset.groupby('map_node').sequence_id.nunique().to_dict()
    active_nodes = nodes | ({COMPLEX_NODE} if {'inta', 'intb'} <= nodes else set())
    if 'ilk' in nodes and 'referenceUnresolved' in edge_kinds:
        active_nodes.add('parvin')
    # The revised map includes evidence-context nodes without audited family rows.
    # Retain them when a selected relationship links to an active family/complex.
    for edge in edge_records:
        if edge['kind'] not in edge_kinds:
            continue
        if edge['a'] in CONTEXT_ONLY_NODES and edge['b'] in active_nodes:
            active_nodes.add(edge['a'])
        if edge['b'] in CONTEXT_ONLY_NODES and edge['a'] in active_nodes:
            active_nodes.add(edge['b'])
    node_names = {node: family for family, node in FAMILY_NODES.items()}
    node_names[COMPLEX_NODE] = COMPLEX_LABEL
    node_names.update(REFERENCE_ONLY_NODES)
    node_names.update(CONTEXT_ONLY_NODES)
    relations = [dict(source_family=node_names[edge['a']],
                      target_family=node_names[edge['b']],
                      source_candidate_count=counts.get(edge['a']),
                      target_candidate_count=counts.get(edge['b']),
                      relationship_class=edge['kind'],
                      evidence_class=edge.get('evidence_class',''),
                      relation=edge.get('relation',''),
                      reference=edge.get('reference',''),
                      transfer_basis=edge.get('transfer_basis',''),
                      species_support=edge.get('species_support',''),
                      interpretation=edge.get('interpretation',''),
                      directional=edge.get('directional',False),
                      reference_only=edge['kind']=='referenceUnresolved',
                      context_only=edge['a'] in CONTEXT_ONLY_NODES or edge['b'] in CONTEXT_ONLY_NODES,
                      source='Schistosome_adhesome_interactive.html')
                 for edge in edge_records if edge['a'] in active_nodes and edge['b'] in active_nodes
                 and edge['kind'] in edge_kinds]
    columns = ['sequence_id','species','family','assigned_family','prototype_family','map_node','module','evidence_tier',
               'grade','family_decision','assignment_interpretation','orthogroup','domain_evidence','topology_evidence',
               'motif_context_evidence','host_orthology_flag','source_collection']
    candidates = subset.reindex(columns=columns).fillna('').astype(str).to_dict('records')
    return {'title':'Evidence-stratified schistosome adhesome hypothesis',
    'interpretation':'Family-level hypotheses from the interactive architecture. The S. mansoni ILK–PINCH–Nck2 complex has experimental support from Gelmedin et al. (2017), DOI 10.1371/journal.ppat.1006147. Ligand relationships target an integrin αβ heterodimer only when both subunit families are selected. Reference-unresolved edges are marked reference_only; host-vascular and SmVKR1 nodes are marked context_only and have no audited candidate count. No specific α–β protein pairing is inferred.',
            'selection':{'families':list(families),'evidence_tiers':list(tiers),'relationship_classes':list(edge_kinds)},
            'candidate_count':len(candidates),'relationship_count':len(relations),
            'candidates':candidates,'family_relationships':relations}
