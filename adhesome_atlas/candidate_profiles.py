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
</style>
'''

_SCRIPT=r'''
<script>
const atlasProfiles=__PROFILES__;
const atlasProfileConfig=__CONFIG__;
const atlasProfileIndex=new Map(atlasProfiles.candidates.map(values=>{const record=Object.fromEntries(atlasProfiles.fields.map((key,i)=>[key,values[i]]));return [record.sequence_id,record]}));
let atlasCandidateId='';
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
function atlasProfileDownload(id){const record=atlasProfileIndex.get(id);if(!record)return;
 const rows=section=>(section.rows[id]||[]).map(values=>Object.fromEntries(section.fields.map((field,index)=>[field,values[index]])));
 const profile={candidate:record,domains:rows(atlasProfiles.domains),motifs:rows(atlasProfiles.motifs),orthologues:rows(atlasProfiles.orthology),sources:atlasProfiles.sources};
 const blob=new Blob([JSON.stringify(profile,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=id+'_candidate_profile.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
function atlasRenderProfile(parent,id){parent.replaceChildren();const record=atlasProfileIndex.get(id);if(!record)return;
 atlasElement('h3',record.candidate_annotation,parent);atlasElement('p',record.sequence_id+' · '+record.species,parent);
 const actions=atlasElement('div',undefined,parent);actions.className='atlas-actions';const url=atlasDossierURL(id);
 if(url){const link=atlasElement('a','Open complete Protein dossier ↗',actions);link.href=url;link.target='_blank';link.rel='noopener'}
 const button=atlasElement('button','Download candidate profile · JSON',actions);button.onclick=()=>atlasProfileDownload(id);
 atlasKeyValues(parent,record,['family','grade','audit_classification','assignment_confidence','family_decision','annotation_resolution','length','orthogroup','orthology_scope']);
 const architecture=atlasElement('details',undefined,parent);architecture.open=true;atlasElement('summary','Architecture & localization',architecture);atlasKeyValues(architecture,record,['architecture','NCBI_CDD_architecture','DeepLoc_2.1','DeepTMHMM','SignalP.v6.0']);
 const evidence=atlasElement('details',undefined,parent);atlasElement('summary','Integrated evidence & family decision',evidence);atlasKeyValues(evidence,record,['total_score_0_10','domain_score_0_4','orthology_raw_score_0_3','orthology_score_0_3','motif_score_0_2','localization_score_0_1','Orthology_benchmark_status','Orthology_benchmark_weight','Orthology_reference_support','identity_rule','identity_competitors','alternative_family_hypotheses','equally_ranked_hypotheses']);
 atlasEvidenceTable(parent,atlasProfiles.domains,id,'CDD domain hits');atlasEvidenceTable(parent,atlasProfiles.motifs,id,'Motif context evidence');atlasEvidenceTable(parent,atlasProfiles.orthology,id,'Reference orthologues');
 atlasElement('small','Profile sources: '+Object.values(atlasProfiles.sources).join(' · '),parent)
}
function atlasFamilyRecords(family){const o=settings();return [...atlasProfileIndex.values()].filter(p=>p.family===family&&(o.species==='all'||p.species===o.species)&&(o.grade==='all'||o.grade==='AB'&&['A','B'].includes(p.grade)||o.grade==='A'&&p.grade==='A'))}
function atlasFamilyProfiles(family){const panel=document.getElementById('sidebar');if(!panel)return;const records=atlasFamilyRecords(family);
 const headings=[...panel.querySelectorAll('h3')],old=headings.find(h=>h.textContent==='Candidate protein accessions');if(old){while(old.nextSibling)old.nextSibling.remove();old.remove()}
 const partnerIds=[...new Set(activeEdges.filter(e=>e.a===family||e.b===family).map(e=>e.a===family?e.b:e.a))];
 if(partnerIds.length){const partners=atlasElement('div',undefined,panel);partners.className='atlas-profile';atlasElement('label','Explore a potential linked partner family',partners);const partner=atlasElement('select',undefined,partners);partner.setAttribute('aria-label','Linked partner families');atlasElement('option','Select a partner family',partner).value='';for(const id of partnerIds.sort())atlasElement('option',id,partner).value=id;partner.onchange=()=>{if(partner.value){atlasCandidateId='';setNode(partner.value)}}}
 const section=atlasElement('section',undefined,panel);section.className='atlas-profile';atlasElement('h3','Explore candidate profiles ('+records.length+')',section);
 if(!records.length){atlasElement('p','No candidate profiles in this selection.',section);return}
 const label=atlasElement('label','Find a candidate in this family',section),search=atlasElement('input',undefined,section);search.type='search';search.placeholder='Accession, annotation or orthogroup';search.setAttribute('aria-label',label.textContent);
 const select=atlasElement('select',undefined,section);select.size=6;select.setAttribute('aria-label','Candidate profiles for '+family);
 const detail=atlasElement('div',undefined,section);
 function refresh(){const query=search.value.trim().toLowerCase();select.replaceChildren();for(const p of records.filter(p=>[p.sequence_id,p.candidate_annotation,p.species,p.orthogroup].join(' ').toLowerCase().includes(query))){const option=atlasElement('option',p.sequence_id+' · '+p.species+' · '+p.grade,select);option.value=p.sequence_id}if(records.some(p=>p.sequence_id===atlasCandidateId)&&[...select.options].some(o=>o.value===atlasCandidateId))select.value=atlasCandidateId;else select.selectedIndex=-1}
 search.oninput=refresh;select.onchange=()=>{atlasCandidateId=select.value;atlasRenderProfile(detail,atlasCandidateId)};refresh();
 if(records.some(p=>p.sequence_id===atlasCandidateId))atlasRenderProfile(detail,atlasCandidateId)
}
const atlasProfileNodeDetails=nodeDetails;
nodeDetails=function(family){atlasProfileNodeDetails(family);atlasFamilyProfiles(family)};
window.atlasSelectedCandidate=()=>{const record=atlasProfileIndex.get(atlasCandidateId);return record&&current.family===record.family&&atlasFamilyRecords(record.family).some(p=>p.sequence_id===record.sequence_id)?record:null};
window.atlasSelectCandidate=function(id,locate=true){const record=atlasProfileIndex.get(id);if(!record)return false;
 if(!DATA.families.some(f=>f.id===record.family)){document.getElementById('atlas-profile-status').textContent='Candidate family is not represented on this map: '+record.family;return false}
 atlasCandidateId=id;if(locate){document.getElementById('species').value=record.species;document.getElementById('grade').value='all';document.getElementById('scope').value='all';document.getElementById('search').value=''}
 setNode(record.family);const search=document.getElementById('atlas-profile-search');if(search)search.value=id;
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
function atlasLocateFromSearch(){const query=atlasGlobalSearch.value.trim();if(atlasProfileIndex.has(query)){window.atlasSelectCandidate(query);return}
 const matches=[...atlasProfileIndex.values()].filter(p=>[p.sequence_id,p.candidate_annotation,p.species,p.family,p.orthogroup].join(' ').toLowerCase().includes(query.toLowerCase()));
 if(matches.length===1)window.atlasSelectCandidate(matches[0].sequence_id);else atlasStatus.textContent=matches.length+' matching candidates. Choose a protein accession from the suggestions.'}
const atlasHeader=document.querySelector('header');if(atlasHeader)atlasHeader.after(atlasBar);else document.body.prepend(atlasBar);
atlasLocate.onclick=atlasLocateFromSearch;atlasGlobalSearch.onchange=()=>{if(atlasProfileIndex.has(atlasGlobalSearch.value.trim()))atlasLocateFromSearch()};atlasGlobalSearch.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();atlasLocateFromSearch()}});
if(atlasProfileConfig.focus_candidate)window.atlasSelectCandidate(atlasProfileConfig.focus_candidate);
</script>
'''
