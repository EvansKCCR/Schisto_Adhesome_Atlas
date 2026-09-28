"""Family-level prototype map and evidence-stratified hypothesis exports."""
import json
from pathlib import Path

import pandas as pd


FAMILY_NODES = {
    'collagen_like': 'collagen', 'C_type_lectin_Ig_FN3_like': 'fn3',
    'laminin_like': 'laminin', 'integrin_alpha': 'inta', 'integrin_beta': 'intb',
    'talin': 'talin', 'kindlin': 'kindlin', 'PINCH_like': 'pinch', 'ILK': 'ilk', 'vinculin': 'vinculin',
    'alpha_actinin': 'actinin', 'filamin': 'filamin', 'paxillin_like': 'paxillin',
    'zyxin_like': 'zyxin', 'FAK': 'fak', 'Src': 'src', 'actin': 'actin',
    'cofilin': 'cofilin', 'PTP_PEST': 'ptp_pest', 'profilin': 'profilin',
}
COMPLEX_NODE = 'integrin_ab'
COMPLEX_LABEL = 'Putative integrin αβ heterodimer'

# These are the relationships drawn in the supplied HTML, at family level.
MAP_EDGES = [
    ('collagen',COMPLEX_NODE,'inferred','putative ligand–αβ heterodimer'),
    ('fn3',COMPLEX_NODE,'inferred','putative ligand–αβ heterodimer'),
    ('laminin',COMPLEX_NODE,'inferred','putative ligand–αβ heterodimer'),
    (COMPLEX_NODE,'inta','structural','putative αβ complex constituent family'),
    (COMPLEX_NODE,'intb','structural','putative αβ complex constituent family'),
    ('intb','talin','inferred','predicted association'),
    ('intb','kindlin','inferred','predicted association'),
    ('kindlin','pinch','exploratory','exploratory adaptor association'),
    ('pinch','ilk','correctedEdge','audit-corrected PINCH–ILK association'),
    ('kindlin','paxillin','inferred','predicted association'),
    ('talin','vinculin','inferred','predicted association'),
    ('talin','actinin','inferred','predicted association'),
    ('talin','filamin','inferred','predicted association'),
    ('vinculin','actin','structural','predicted structural association'),
    ('actinin','actin','structural','predicted structural association'),
    ('filamin','actin','structural','predicted structural association'),
    ('paxillin','fak','inferred','predicted association'),
    ('fak','src','structural','predicted structural association'),
    ('cofilin','actin','exploratory','exploratory pathway relationship'),
]


def candidate_rows(adhesome, fn3):
    """Keep audit-retained rows; separate the FN3 ligand screen from the 189/43 counts."""
    retained = adhesome[adhesome.audit_classification.isin(['Supported','Provisional'])].copy()
    retained['prototype_family'] = retained.reviewed_family
    retained['evidence_tier'] = retained.audit_classification.map({'Supported':'Core family-retained','Provisional':'Provisional'})
    retained['source_collection'] = 'Adhesome candidates'
    exploratory = fn3[fn3.reviewed_family.eq('C_type_lectin_Ig_FN3_like')].copy()
    exploratory['prototype_family'] = 'C_type_lectin_Ig_FN3_like'
    exploratory['evidence_tier'] = 'Exploratory FN3 screen'
    exploratory['source_collection'] = 'FN3 / fibronectin-like review'
    combined = pd.concat([retained, exploratory], ignore_index=True)
    combined['map_node'] = combined.prototype_family.map(FAMILY_NODES)
    return combined[combined.map_node.notna()].copy()


def map_payload(rows, focus_family=None, focus_candidate=None):
    fields = ['sequence_id','species','family','assigned_family','prototype_family','map_node','evidence_tier','grade',
              'family_decision','orthogroup','domain_evidence','topology_evidence',
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
.edge.atlas-dim{opacity:.13}.node.atlas-dim{opacity:.36}
#info select{width:100%;padding:7px;border:1px solid #94a3b8;border-radius:6px;background:white;color:#0f172a}
#info .atlas-candidate{padding:8px;background:#f7f9fc;border-left:4px solid #16a34a;margin-top:9px}
</style>
<script>
const atlasPayload = __ATLAS_PAYLOAD__;
const atlasOriginalShow = show;
const atlasExtras = [
  {id:'ptp_pest',x:990,y:625,w:135,h:60,title:'PTP-PEST-like',count:'4 / 3 / 3',color:'#7e22ce',status:'explore',extra:'Family retained; functional placement exploratory',detail:'Ten family-retained hypotheses. No explicit partner edge was provided in the prototype diagram.'},
  {id:'profilin',x:20,y:740,w:120,h:60,title:'Profilin',count:'0 / 0 / 0',color:'#d97706',status:'prov',extra:'One S. mansoni provisional hypothesis',detail:'One provisional family hypothesis. No explicit partner edge was provided in the prototype diagram.'}
];
atlasExtras.forEach(n=>{nodes.push(n);initial.push(JSON.parse(JSON.stringify(n)))});
drawNodes();drawEdges();
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
  atlasText(box,'p',record.evidence_tier+' · '+(record.family_decision||record.grade||'FN3 architecture screen'));
  if(record.family&&record.family!==record.prototype_family)atlasText(box,'p','Screening family: '+record.family+' → reviewed family: '+record.prototype_family);
  if(record.orthogroup)atlasText(box,'p','Orthogroup: '+record.orthogroup);
  if(record.domain_evidence)atlasText(box,'p','Domains: '+record.domain_evidence);
  if(record.topology_evidence)atlasText(box,'p','Topology: '+record.topology_evidence);
  if(record.motif_context_evidence)atlasText(box,'p','Motifs: '+record.motif_context_evidence);
}
show=function(n){
  atlasOriginalShow(n);atlasFocus(n);
  const connected=edges.filter(e=>e.a===n.id||e.b===n.id);
  atlasText(info,'h3','Potential linked families');
  if(connected.length){const list=document.createElement('ul');info.appendChild(list);connected.forEach(e=>{
    const other=nodes.find(x=>x.id===(e.a===n.id?e.b:e.a));
    atlasText(list,'li',other.title+' · '+e.kind+(e.class==='ligand'?' · putative ligand–αβ heterodimer':''));
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
if(initialFocus)show(initialFocus);
</script>
""".replace('__ATLAS_PAYLOAD__', payload)
    return html.replace('</body>', enhancement + '</body>')


def hypothesis(rows, families, tiers, edge_kinds):
    subset = rows[rows.prototype_family.isin(families) & rows.evidence_tier.isin(tiers)].copy()
    nodes = set(subset.map_node)
    counts = subset.groupby('map_node').sequence_id.nunique().to_dict()
    active_nodes = nodes | ({COMPLEX_NODE} if {'inta', 'intb'} <= nodes else set())
    node_names = {node: family for family, node in FAMILY_NODES.items()}
    node_names[COMPLEX_NODE] = COMPLEX_LABEL
    relations = [dict(source_family=node_names[a],
                      target_family=node_names[b],
                      source_candidate_count=counts.get(a), target_candidate_count=counts.get(b),
                      evidence_class=kind, interpretation=label,
                      source='Schistosome_adhesome_interactive.html')
                 for a,b,kind,label in MAP_EDGES if a in active_nodes and b in active_nodes and kind in edge_kinds]
    columns = ['sequence_id','species','family','assigned_family','prototype_family','map_node','module','evidence_tier',
               'grade','family_decision','orthogroup','domain_evidence','topology_evidence',
               'motif_context_evidence','host_orthology_flag','source_collection']
    candidates = subset.reindex(columns=columns).fillna('').astype(str).to_dict('records')
    return {'title':'Evidence-stratified schistosome adhesome hypothesis',
            'interpretation':'Family-level computational hypotheses. Ligand relationships target a putative integrin αβ heterodimer only when both subunit families are selected; no specific α–β protein pairing or experimentally established interaction is inferred.',
            'selection':{'families':list(families),'evidence_tiers':list(tiers),'relationship_classes':list(edge_kinds)},
            'candidate_count':len(candidates),'relationship_count':len(relations),
            'candidates':candidates,'family_relationships':relations}
