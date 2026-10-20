"""Link current candidate evidence profiles to the self-contained family map."""
from html import escape
import json
import re
from urllib.parse import urlencode,urlsplit,urlunsplit

PROFILE_FIELDS=['sequence_id','species','family','candidate_annotation','grade','audit_classification',
 'assignment_confidence','family_support_level','family_decision','annotation_resolution',
 'protein_name_scope','length','orthogroup','orthology_scope','architecture','NCBI_CDD_architecture',
 'DeepLoc_2.1','DeepTMHMM','SignalP.v6.0','domain_score_0_4','orthology_raw_score_0_3',
 'orthology_score_0_3','motif_score_0_2','localization_score_0_1','total_score_0_10',
 'orthology_reference_species_count','Orthology_direct_reference_count','Orthology_reference_support',
 'Orthology_benchmark_status','Orthology_benchmark_weight','family_specific_CDD_support',
 'identity_rule','identity_competitors','alternative_family_hypotheses','equally_ranked_hypotheses','source']
DOMAIN_FIELDS=['accession','short_name','start','end','evalue','bitscore','interpretation']
MOTIF_FIELDS=['motif_function','start','end','representative_peptide','source_ELM_classes',
 'reassessed_context_tier','context_explanation','topology','overlapping_domains']
ORTHOLOGY_FIELDS=['reference_species','orthologues','relationship','source_group_size','target_group_size']
START='<!-- ATLAS_CANDIDATE_PROFILES_START -->'
END='<!-- ATLAS_CANDIDATE_PROFILES_END -->'

# Remember the hit before SVG pointer capture retargets pointerup to the canvas.
# This repair is also applied when the atlas re-embeds an authored HTML snapshot.
_POINTER_HANDLERS=r'''let panning=null;
$('network').addEventListener('pointerdown',e=>{
 if(e.button!==0||panning)return;
 const family=e.target.closest('[data-family]'),edge=e.target.closest('[data-edge-id]');
 panning={pointerId:e.pointerId,clientX:e.clientX,clientY:e.clientY,x:zoom.x,y:zoom.y,moved:false,
  family:family?.getAttribute('data-family')||null,edge:edge?.getAttribute('data-edge-id')||null};
 $('network').setPointerCapture(e.pointerId);
});
$('network').addEventListener('pointermove',e=>{
 if(!panning||e.pointerId!==panning.pointerId)return;
 const dx=e.clientX-panning.clientX,dy=e.clientY-panning.clientY;
 panning.moved=panning.moved||Math.abs(dx)>5||Math.abs(dy)>5;
 if(!panning.moved)return;
 zoom.x=panning.x-dx*(zoom.w/$('network').getBoundingClientRect().width);
 zoom.y=panning.y-dy*(zoom.h/$('network').getBoundingClientRect().height);applyView();
});
$('network').addEventListener('pointerup',e=>{
 if(!panning||e.pointerId!==panning.pointerId)return;
 const hit=panning;panning=null;
 if($('network').hasPointerCapture(e.pointerId))$('network').releasePointerCapture(e.pointerId);
 if(hit.moved||Math.abs(e.clientX-hit.clientX)>5||Math.abs(e.clientY-hit.clientY)>5)return;
 if(hit.family)setNode(hit.family);else if(hit.edge)setEdge(hit.edge);
 else{current={family:null,edge:null};draw()}
});
for(const type of ['pointercancel','lostpointercapture'])$('network').addEventListener(type,e=>{
 if(panning?.pointerId===e.pointerId)panning=null;
});
'''

def _repair_pointer_selection(html):
    pattern=r"let panning=null;.*?(?=\$\('network'\)\.addEventListener\('wheel')"
    return re.sub(pattern,lambda _: _POINTER_HANDLERS,html,count=1,flags=re.S)

def atlas_url(base,view,protein):
    parts=urlsplit(base or '')
    return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode({'view':view,'protein':protein}),''))

def _records(frame,fields):
    return json.loads(frame.reindex(columns=fields).to_json(orient='values'))

def profile_payload(candidates,books,motifs):
    """Keep exact IDs and original evidence; encode table headings only once."""
    candidates=candidates.drop_duplicates('sequence_id')
    ids=set(candidates.sequence_id)
    def grouped(frame,key,fields):
        frame=frame[frame[key].isin(ids)]
        return {'fields':fields,'rows':{str(identifier):_records(group,fields) for identifier,group in frame.groupby(key,sort=False)}}
    domains=books['files/NCBI_CDD.xlsx']['NCBI_CDD_selected_hits'].drop_duplicates(['sequence_id','accession','start','end'])
    direct=books['files/Direct_orthologues.xlsx']['Direct_orthologues']
    return {'fields':PROFILE_FIELDS,'candidates':_records(candidates,PROFILE_FIELDS),
      'domains':grouped(domains,'sequence_id',DOMAIN_FIELDS),
      'motifs':grouped(motifs,'sequence_id',MOTIF_FIELDS),
      'orthology':grouped(direct,'candidate_id',ORTHOLOGY_FIELDS),
      'sources':{'candidates':'files/adhesome_candidates_list.xlsx / Audited_family_assignment',
       'domains':'files/NCBI_CDD.xlsx / NCBI_CDD_selected_hits',
       'motifs':'files/Motif_annotations.xlsx / Motif_annotations',
       'orthology':'files/Direct_orthologues.xlsx / Direct_orthologues',
       'topology':'files/Topology_predictions.xlsx / Topology_predictions'}}

def candidate_map_html(html,payload,*,app_url='',focus_candidate=''):
    """Idempotent overlay; preserve the authored map's nodes and edge evidence."""
    html=re.sub(re.escape(START)+r'.*?'+re.escape(END),'',html,flags=re.S)
    html=_repair_pointer_selection(html)
    config={'app_url':app_url,'focus_candidate':focus_candidate}
    block=START+_STYLE+_SCRIPT.replace('__PROFILES__',json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c')).replace('__CONFIG__',json.dumps(config,ensure_ascii=False).replace('<','\\u003c'))+END
    return html.replace('</body>',block+'</body>',1)

_STYLE=r'''
<style>
.atlas-profiles-bar{padding:12px 20px;background:#fffbe6;color:#000;border-block:1px solid #d1b13b;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.atlas-profiles-bar input{flex:1;min-width:240px;padding:9px;font-size:15px;border:1px solid #08743f;border-radius:6px;color:#000;background:white}
.atlas-profiles-bar button,.atlas-profile button{padding:8px 12px;border:1px solid #064c2c;background:#fff;color:#000;border-radius:6px;cursor:pointer;font-weight:700}
.atlas-profile{padding:12px;margin:12px 0;border:2px solid #08743f;border-radius:10px;background:#fff;color:#000;font:14px Arial,sans-serif}
.atlas-profile h3,.atlas-profile p,.atlas-profile summary,.atlas-profile label{color:#000}.atlas-profile h3{margin:6px 0;font-size:18px}.atlas-profile summary{font-weight:700;cursor:pointer;padding:8px 0;font-size:15px}
.atlas-profile select,.atlas-profile input{width:100%;padding:8px;margin:5px 0;background:#fff;color:#000;border:1px solid #65776b;border-radius:5px;font-size:14px}
.atlas-profile .atlas-scroll{max-height:300px;overflow:auto;margin:6px 0}.atlas-profile table{border-collapse:collapse;width:100%;font-size:13px;color:#000}
.atlas-profile td,.atlas-profile th{border:1px solid #c4cfc5;padding:6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}.atlas-profile th{background:#eef6ef;color:#000}.atlas-profile .atlas-actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.atlas-profile a{color:#064c2c;text-decoration:underline;font-weight:bold}.atlas-profile small{font-size:12px;color:#222}.atlas-profile button:focus-visible,.atlas-profile a:focus-visible{outline:3px solid #b91c1c;outline-offset:2px}

.atlas-connected-info{padding:9px;background:#fff8ce;border:1px solid #c4a731;border-radius:6px;margin:8px 0;color:#000;font-size:14px}
.atlas-panel-close{display:none}
@media(min-width:760px){main{grid-template-columns:minmax(0,1fr) minmax(300px,370px)!important}.sidebar{position:sticky;top:12px;max-height:calc(100vh - 24px)!important;min-height:0!important;overflow:auto!important}#network{min-height:420px!important}}
@media(max-width:759px){.sidebar{position:fixed!important;right:0;top:0;width:min(94vw,430px);height:100vh;max-height:100vh!important;min-height:0!important;z-index:10000;box-shadow:-5px 0 24px #0005;transform:translateX(110%);transition:transform .16s ease}.atlas-side-open .sidebar{transform:translateX(0)}.atlas-panel-close{display:inline-block!important;margin-bottom:8px}.atlas-profiles-bar input{min-width:180px}}
</style>
''' 

_SCRIPT=r'''
<script>
const atlasProfiles=__PROFILES__;
const atlasProfileConfig=__CONFIG__;
const atlasProfileIndex=new Map(atlasProfiles.candidates.map(values=>{const record=Object.fromEntries(atlasProfiles.fields.map((key,i)=>[key,values[i]]));return [record.sequence_id,record]}));
let atlasCandidateId='';
let atlasLastContextKey='';
function atlasElement(tag,text,parent){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text??'');if(parent)parent.appendChild(e);return e}
function atlasTextValue(value){return value===null||value===undefined||value===''?'No additional information present in the current library':String(value)}
function atlasLabel(key){return ({sequence_id:'Protein accession',candidate_annotation:'Protein annotation',architecture:'Pfam architecture',orthogroup:'Orthogroup',orthology_scope:'Evolutionary scope','DeepLoc_2.1':'Localization',DeepTMHMM:'Transmembrane topology','SignalP.v6.0':'Signal peptide',total_score_0_10:'Integrated evidence score (0–10)',domain_score_0_4:'Domain score (0–4)',orthology_score_0_3:'Benchmark-adjusted orthology score (0–3)',motif_score_0_2:'Motif score (0–2)',localization_score_0_1:'Localization score (0–1)'})[key]||key.replaceAll('_',' ')}
function atlasKeyValues(parent,record,fields){const table=atlasElement('table',undefined,parent);for(const key of fields){const row=atlasElement('tr',undefined,table);atlasElement('th',atlasLabel(key),row);atlasElement('td',atlasTextValue(record[key]),row)}}
function atlasEvidenceTable(parent,section,id,title){const details=atlasElement('details',undefined,parent);const rows=section.rows[id]||[];atlasElement('summary',title+' ('+rows.length+')',details);
 if(!rows.length){atlasElement('p','No additional information present in the current library. To be updated when additional information is available.',details);return}
 const scroller=atlasElement('div',undefined,details);scroller.className='atlas-scroll';const table=atlasElement('table',undefined,scroller),head=atlasElement('tr',undefined,table);
 section.fields.forEach(key=>atlasElement('th',atlasLabel(key),head));for(const record of rows){const tr=atlasElement('tr',undefined,table);record.forEach(value=>atlasElement('td',atlasTextValue(value),tr))}
}
function atlasDossierURL(id){if(!atlasProfileConfig.app_url)return '';const u=new URL(atlasProfileConfig.app_url);u.search='';u.hash='';u.searchParams.set('view','Protein dossier');u.searchParams.set('protein',id);return u.href}
function atlasCandidateEvidence(id){const record=atlasProfileIndex.get(id);if(!record)return null;
 const rows=section=>(section.rows[id]||[]).map(values=>Object.fromEntries(section.fields.map((field,index)=>[field,values[index]])));
 return {candidate:record,domains:rows(atlasProfiles.domains),motifs:rows(atlasProfiles.motifs),orthologues:rows(atlasProfiles.orthology),sources:atlasProfiles.sources};
}
function atlasProfileDownload(id){const profile=atlasCandidateEvidence(id);if(!profile)return;
 const blob=new Blob([JSON.stringify(profile,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=id+'_candidate_profile.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
function atlasRenderProfile(parent,id){parent.replaceChildren();const record=atlasProfileIndex.get(id);if(!record)return;
 atlasElement('h3',record.candidate_annotation,parent);atlasElement('p',record.sequence_id+' · '+record.species,parent);
 const actions=atlasElement('div',undefined,parent);actions.className='atlas-actions';const url=atlasDossierURL(id);
 if(url){const link=atlasElement('a','Open complete Protein dossier ↗',actions);link.href=url;link.target='_blank';link.rel='noopener'}
 const button=atlasElement('button','Download candidate profile · JSON',actions);button.setAttribute('data-atlas-profile-download','true');button.onclick=()=>atlasProfileDownload(id);
 atlasKeyValues(parent,record,['family','grade','audit_classification','assignment_confidence','family_decision','annotation_resolution','length','orthogroup','orthology_scope']);
 const architecture=atlasElement('details',undefined,parent);architecture.open=true;atlasElement('summary','Architecture & localization',architecture);atlasKeyValues(architecture,record,['architecture','NCBI_CDD_architecture','DeepLoc_2.1','DeepTMHMM','SignalP.v6.0']);
 const evidence=atlasElement('details',undefined,parent);atlasElement('summary','Integrated evidence & family decision',evidence);atlasKeyValues(evidence,record,['total_score_0_10','domain_score_0_4','orthology_raw_score_0_3','orthology_score_0_3','motif_score_0_2','localization_score_0_1','Orthology_benchmark_status','Orthology_benchmark_weight','Orthology_reference_support','identity_rule','identity_competitors','alternative_family_hypotheses','equally_ranked_hypotheses']);
 atlasEvidenceTable(parent,atlasProfiles.domains,id,'CDD domain hits');atlasEvidenceTable(parent,atlasProfiles.motifs,id,'Motif context evidence');atlasEvidenceTable(parent,atlasProfiles.orthology,id,'Reference orthologues');
 atlasElement('small','Profile sources: '+Object.values(atlasProfiles.sources).join(' · '),parent)
}
function atlasFamilyRecords(family){const o=settings();return [...atlasProfileIndex.values()].filter(p=>p.family===family&&(o.species==='all'||p.species===o.species)&&(o.grade==='all'||o.grade==='AB'&&['A','B'].includes(p.grade)||o.grade==='A'&&p.grade==='A'))}
function atlasGradeCounts(records){return Object.fromEntries(['A','B','C'].map(grade=>[grade,records.filter(p=>p.grade===grade).length]))}
function atlasFamilyProfiles(family){const panel=document.getElementById('sidebar');if(!panel)return;const records=atlasFamilyRecords(family),grades=atlasGradeCounts(records);
 const headings=[...panel.querySelectorAll('h3')],old=headings.find(h=>h.textContent==='Candidate protein accessions');if(old){while(old.nextSibling)old.nextSibling.remove();old.remove()}
 const partnerIds=[...new Set(activeEdges.filter(e=>e.a===family||e.b===family).map(e=>e.a===family?e.b:e.a))];
 if(partnerIds.length){const partners=atlasElement('div',undefined,panel);partners.className='atlas-profile';atlasElement('label','Explore a potential linked partner family',partners);const partner=atlasElement('select',undefined,partners);partner.setAttribute('aria-label','Linked partner families');atlasElement('option','Select a partner family',partner).value='';for(const id of partnerIds.sort())atlasElement('option',id,partner).value=id;partner.onchange=()=>{if(partner.value)setNode(partner.value)}}
 const section=atlasElement('section',undefined,panel);section.className='atlas-profile';atlasElement('h3','Explore candidate profiles ('+records.length+')',section);
 const counts=atlasElement('p',records.length+' candidates · A = '+grades.A+' · B = '+grades.B+' · C = '+grades.C,section);counts.id='atlas-family-counts';
 const pathInfo=atlasElement('div',undefined,section);pathInfo.id='atlas-connected-info';pathInfo.className='atlas-connected-info';section.prepend(pathInfo);
 panel.prepend(section);panel.scrollTop=0;
 const close=atlasElement('button','Close candidate panel',section);close.className='atlas-panel-close';close.onclick=()=>document.body.classList?.remove('atlas-side-open');section.prepend(close);
 panel.setAttribute('aria-label','Candidate profiles and connected network paths');document.body.classList?.add('atlas-side-open');
 if(!records.length){atlasCandidateId='';atlasElement('p','No candidate profiles are associated with '+family+' under the selected species and confidence filters. No additional information present in the current library.',section);atlasHighlightConnections();return}
 const label=atlasElement('label','Find a candidate in this family',section),search=atlasElement('input',undefined,section);search.type='search';search.placeholder='Accession, annotation or orthogroup';search.setAttribute('aria-label',label.textContent);
 const select=atlasElement('select',undefined,section);select.size=6;select.setAttribute('aria-label','Candidate profiles for '+family);
 const detail=atlasElement('div',undefined,section);detail.id='atlas-profile-detail';
 function refresh(){const query=search.value.trim().toLowerCase();select.replaceChildren();for(const p of records.filter(p=>[p.sequence_id,p.candidate_annotation,p.species,p.orthogroup].join(' ').toLowerCase().includes(query))){const option=atlasElement('option',p.sequence_id+' · '+p.species+' · '+p.grade,select);option.value=p.sequence_id}if(records.some(p=>p.sequence_id===atlasCandidateId)&&[...select.options].some(o=>o.value===atlasCandidateId))select.value=atlasCandidateId;else select.selectedIndex=-1}
 search.oninput=refresh;select.onchange=()=>setNode(family,select.value);refresh();
 if(!records.some(p=>p.sequence_id===atlasCandidateId))atlasCandidateId=[...records].sort((a,b)=>(a.grade||'Z').localeCompare(b.grade||'Z')||a.sequence_id.localeCompare(b.sequence_id))[0].sequence_id;
 select.value=atlasCandidateId;atlasRenderProfile(detail,atlasCandidateId);
 const caption=atlasElement('p','Showing '+atlasCandidateId+'. All '+records.length+' candidates are available in the list above.',section);caption.style.fontWeight='700';
 atlasHighlightConnections()
}

function atlasConnectedPath(start,edges,mode='component',target=''){
 const adjacency=new Map();for(const e of edges){if(!adjacency.has(e.a))adjacency.set(e.a,[]);if(!adjacency.has(e.b))adjacency.set(e.b,[]);adjacency.get(e.a).push({node:e.b,edge:e.id});adjacency.get(e.b).push({node:e.a,edge:e.id})}
 const distance=new Map([[start,0]]),parents=new Map(),queue=[start],limit=target||mode==='component'?Infinity:Number(mode);
 for(let i=0;i<queue.length;i++){const node=queue[i];if(distance.get(node)>=limit)continue;const links=[...(adjacency.get(node)||[])].sort((a,b)=>a.node.localeCompare(b.node)||String(a.edge).localeCompare(String(b.edge)));for(const link of links){if(distance.has(link.node))continue;distance.set(link.node,distance.get(node)+1);parents.set(link.node,{node,edge:link.edge});queue.push(link.node)}}
 if(target){if(!distance.has(target))return {nodes:new Set([start]),edges:new Set(),path:[],distance,unreachable:true};const path=[target],ids=new Set();let next=target;while(next!==start){const parent=parents.get(next);ids.add(parent.edge);next=parent.node;path.unshift(next)}return {nodes:new Set(path),edges:ids,path,distance,unreachable:false}}
 const nodes=new Set(distance.keys()),ids=new Set(edges.filter(e=>nodes.has(e.a)&&nodes.has(e.b)).map(e=>e.id));return {nodes,edges:ids,path:[],distance,unreachable:false}
}
window.atlasConnectedPath=atlasConnectedPath;
function atlasHighlightConnections(){if(!current.family)return;
 const mode=document.getElementById('atlas-path-scope')?.value||'component',target=document.getElementById('atlas-path-target')?.value||'';
 const result=atlasConnectedPath(current.family,activeEdges,mode,target);
 document.querySelectorAll('[data-edge-id]').forEach(path=>{const included=result.edges.has(path.getAttribute('data-edge-id'));path.setAttribute('opacity',included?'1':'.045');if(included){path.setAttribute('stroke','#08743f');path.setAttribute('stroke-width','4')}});
 document.querySelectorAll('[data-family]').forEach(group=>{const id=group.getAttribute('data-family');group.setAttribute('opacity',result.nodes.has(id)?'1':'.25');if(result.nodes.has(id)){const rect=group.querySelector('rect');if(rect){rect.setAttribute('stroke',id===current.family?'#b91c1c':'#08743f');rect.setAttribute('stroke-width',id===current.family?'4':'3')}}});
 const info=document.getElementById('atlas-connected-info');if(info){info.replaceChildren();atlasElement('strong','Connected path from '+current.family,info);
 atlasElement('p',result.unreachable?'Target '+target+' is not connected under the selected network filters.':!result.edges.size?'No recorded connections for '+current.family+' in the active topology.':target?result.path.join(' ↔ '):result.nodes.size+' families · '+result.edges.size+' relationships · '+(mode==='component'?'connected component':mode+'-step neighborhood'),info);
 atlasElement('small','Paths follow recorded, undirected family associations and active evidence filters; they do not assign a causal direction.',info)}
 const status=document.getElementById('atlas-profile-status');if(status)status.textContent=current.family+' · '+result.nodes.size+' connected families · candidate profiles open in the side panel';
 atlasPublishContext();
}

window.atlasCandidateContext=function(){if(!current.family)return null;
 const candidate=window.atlasSelectedCandidate?.(),mode=document.getElementById('atlas-path-scope')?.value||'component',target=document.getElementById('atlas-path-target')?.value||'';
 const highlighted=atlasConnectedPath(current.family,activeEdges,mode,target),filters=settings();
 return {node:current.family,title:current.family,candidate:candidate?.sequence_id||'',candidate_annotation:candidate?.candidate_annotation||'',orthogroup:candidate?.orthogroup||'',species:candidate?.species||filters.species,module:'all',
  profile:candidate?atlasCandidateEvidence(candidate.sequence_id):null,profile_html:document.getElementById('atlas-profile-detail')?.innerHTML||'',
  candidates:atlasFamilyRecords(current.family).map(p=>({id:p.sequence_id,annotation:p.candidate_annotation,species:p.species,grade:p.grade})),
  candidate_counts:atlasGradeCounts(atlasFamilyRecords(current.family)),
  highlighted_path:{root:current.family,mode,target,nodes:[...highlighted.nodes],edges:activeEdges.filter(e=>highlighted.edges.has(e.id)),route:highlighted.path,unreachable:highlighted.unreachable},network_filters:filters};
};
function atlasPublishContext(force=false){const context=window.atlasCandidateContext();if(!context){if(atlasLastContextKey||force){atlasLastContextKey='';window.dispatchEvent(new CustomEvent('atlas-candidate-context',{detail:{cleared:true}}))}return;}
 const key=JSON.stringify([context.node,context.candidate,context.highlighted_path.mode,context.highlighted_path.target,context.highlighted_path.nodes,context.highlighted_path.edges.map(e=>e.id),context.network_filters]);
 if(!force&&key===atlasLastContextKey)return;atlasLastContextKey=key;
 window.dispatchEvent(new CustomEvent('atlas-candidate-context',{detail:context}));
}
window.atlasPublishContext=atlasPublishContext;

function atlasActivateNodes(){document.querySelectorAll('[data-family]').forEach(group=>{const family=group.getAttribute('data-family');group.setAttribute('role','button');group.setAttribute('tabindex','0');group.setAttribute('aria-label',family+': open linked candidates and connected paths');group.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();setNode(family)}}})}
const atlasPathDraw=draw;
draw=function(){atlasPathDraw();
 if(!current.family&&!current.edge)document.body.classList?.remove('atlas-side-open');
 else {const panel=document.getElementById('sidebar');document.body.classList?.add('atlas-side-open');if(panel&&!panel.querySelector('button.atlas-panel-close')){const button=atlasElement('button','Close side panel');button.className='atlas-panel-close';button.onclick=()=>document.body.classList?.remove('atlas-side-open');panel.prepend(button)}}
 atlasActivateNodes();atlasHighlightConnections();if(!current.family)atlasPublishContext()};

const atlasProfileNodeDetails=nodeDetails;
nodeDetails=function(family){atlasProfileNodeDetails(family);atlasFamilyProfiles(family)};
window.atlasSelectedCandidate=()=>{const record=atlasProfileIndex.get(atlasCandidateId);return record&&current.family===record.family&&atlasFamilyRecords(record.family).some(p=>p.sequence_id===record.sequence_id)?record:null};
// One selection transaction for pointer, keyboard, partner and candidate controls.
function atlasSelectNode(family,candidateId=''){
 const records=atlasFamilyRecords(family),requested=candidateId||atlasCandidateId;
 atlasCandidateId=records.some(p=>p.sequence_id===requested)?requested:([ ...records ].sort((a,b)=>(a.grade||'Z').localeCompare(b.grade||'Z')||a.sequence_id.localeCompare(b.sequence_id))[0]?.sequence_id||'');
 current={family,edge:null};draw();return current.family===family;
}
setNode=atlasSelectNode;window.atlasSelectNode=atlasSelectNode;
window.atlasSelectCandidate=function(id,locate=true){const record=atlasProfileIndex.get(id);if(!record)return false;
 if(!DATA.families.some(f=>f.id===record.family)){document.getElementById('atlas-profile-status').textContent='Candidate family is not represented on this map: '+record.family;return false}
 if(locate){document.getElementById('species').value=record.species;document.getElementById('grade').value='all';document.getElementById('scope').value='all';document.getElementById('search').value=''}
 setNode(record.family,id);const search=document.getElementById('atlas-profile-search');if(search)search.value=id;
 document.getElementById('atlas-profile-status').textContent=record.sequence_id+' · '+record.family+' · '+record.orthogroup;
 if(locate){const element=[...document.querySelectorAll('[data-family]')].find(e=>e.getAttribute('data-family')===record.family);if(element&&typeof element.getBBox==='function'){const b=element.getBBox();zoom={x:Math.max(0,b.x-420),y:Math.max(0,b.y-240),w:1100,h:720};applyView()}}
 return true
};
const atlasBar=atlasElement('section');atlasBar.className='atlas-profiles-bar';
const atlasGlobalLabel=atlasElement('label','Locate a candidate',atlasBar);atlasGlobalLabel.htmlFor='atlas-profile-search';
const atlasGlobalSearch=atlasElement('input',undefined,atlasBar);atlasGlobalSearch.id='atlas-profile-search';atlasGlobalSearch.setAttribute('list','atlas-profile-options');atlasGlobalSearch.placeholder='Protein ID, annotation, family or orthogroup';
const atlasOptions=atlasElement('datalist',undefined,atlasBar);atlasOptions.id='atlas-profile-options';
for(const p of atlasProfileIndex.values()){const option=atlasElement('option',undefined,atlasOptions);option.value=p.sequence_id;option.label=[p.candidate_annotation,p.species,p.family,p.orthogroup].join(' · ')}
const atlasLocate=atlasElement('button','Locate protein',atlasBar);const atlasStatus=atlasElement('span','Select an identifier to highlight its family and open the candidate profile.',atlasBar);atlasStatus.id='atlas-profile-status';atlasStatus.setAttribute('role','status');

const atlasPathLabel=atlasElement('label','Connected path',atlasBar);atlasPathLabel.htmlFor='atlas-path-scope';
const atlasPathScope=atlasElement('select',undefined,atlasBar);atlasPathScope.id='atlas-path-scope';
for(const [value,label] of [['1','Direct partners'],['2','2-step neighborhood'],['component','Connected component']]){const option=atlasElement('option',label,atlasPathScope);option.value=value}atlasPathScope.value='component';atlasPathScope.onchange=()=>draw();
const atlasPathTargetLabel=atlasElement('label','Shortest path to',atlasBar);atlasPathTargetLabel.htmlFor='atlas-path-target';
const atlasPathTarget=atlasElement('select',undefined,atlasBar);atlasPathTarget.id='atlas-path-target';atlasElement('option','Choose a target family (optional)',atlasPathTarget).value='';
for(const id of new Set([...DATA.families.map(f=>f.id),...(DATA.special||[]).flatMap(e=>[e.a,e.b])])){const option=atlasElement('option',id,atlasPathTarget);option.value=id}atlasPathTarget.onchange=()=>draw();

function atlasLocateFromSearch(){const query=atlasGlobalSearch.value.trim();if(atlasProfileIndex.has(query)){window.atlasSelectCandidate(query);return}
 const matches=[...atlasProfileIndex.values()].filter(p=>[p.sequence_id,p.candidate_annotation,p.species,p.family,p.orthogroup].join(' ').toLowerCase().includes(query.toLowerCase()));
 if(matches.length===1)window.atlasSelectCandidate(matches[0].sequence_id);else atlasStatus.textContent=matches.length+' matching candidates. Choose a protein accession from the suggestions.'}
const atlasHeader=document.querySelector('header');if(atlasHeader)atlasHeader.after(atlasBar);else document.body.prepend(atlasBar);
atlasLocate.onclick=atlasLocateFromSearch;atlasGlobalSearch.onchange=()=>{if(atlasProfileIndex.has(atlasGlobalSearch.value.trim()))atlasLocateFromSearch()};atlasGlobalSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();atlasLocateFromSearch()}});
atlasActivateNodes();
if(atlasProfileConfig.focus_candidate)window.atlasSelectCandidate(atlasProfileConfig.focus_candidate);
</script>
'''
