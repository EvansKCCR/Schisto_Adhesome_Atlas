"""Connect the family map to the local adhesion-matrix simulator."""
from html import escape
import json
from design_system import network_style


NODE_SCENARIOS = {
    'collagen': {'controls': {'ligand':.1}, 'stage':'ECM anchoring', 'note':'Reduced candidate collagen-like availability lowers the ligand-anchoring probability.'},
    'laminin': {'controls': {'ligand':.1}, 'stage':'ECM anchoring', 'note':'Reduced candidate laminin-like availability lowers the ligand-anchoring probability.'},
    'vascular_context': {'controls': {'load':.05}, 'stage':'Mechanical input', 'note':'Reduced external force loading tests the host-interface input as a normalized mechanics hypothesis.'},
    'inta': {'controls': {'integrinAvailability':.2}, 'stage':'Receptor availability', 'note':'Reduced availability of the putative αβ receptor lowers initialization of local integrin roots.'},
    'intb': {'controls': {'integrinAvailability':.2}, 'stage':'Receptor availability', 'note':'Reduced availability of the putative αβ receptor lowers initialization of local integrin roots; the matrix uses its β-tail interface.'},
    'integrin_ab': {'controls': {'integrinAvailability':.2}, 'stage':'Receptor availability', 'note':'Reduced αβ receptor availability lowers ligand-anchored matrix initialization.'},
    'talin': {'controls': {'talinAvailability':.15}, 'stage':'I–T recruitment', 'note':'Reduced talin availability lowers topology-driven I–T recruitment and subsequent T–V assembly.'},
    'kindlin': {'controls': {'integrinAvailability':.5}, 'stage':'Integrin activation proxy', 'note':'Kindlin is represented through receptor availability; it is not an extra component of the I–T–V matrix.'},
    'vinculin': {'controls': {'vinculinAvailability':.15}, 'stage':'Force-dependent T–V recruitment', 'note':'Reduced vinculin availability lowers T–V recruitment despite talin exposure.'},
    'actinin': {'controls': {'feedback':.02}, 'stage':'Actin force transfer', 'note':'Reduced force feedback is an α-actinin-associated cytoskeletal coupling proxy.'},
    'filamin': {'controls': {'feedback':.02}, 'stage':'Actin force transfer', 'note':'Reduced force feedback is a filamin-associated cytoskeletal coupling proxy.'},
    'actin': {'controls': {'feedback':.02,'actinProbability':.1}, 'stage':'Actin attachment and feedback', 'note':'Reduced actin attachment and force feedback interrupt the assembly–tension loop.'},
    'ilk': {'controls': {'bridgeGate':.15}, 'stage':'ILK–PINCH–Nck2 projection', 'note':'The bridge gate reduces downstream coupling from assembled sites. The I–T–V structural matrices remain governed by their own parameters.'},
    'pinch': {'controls': {'bridgeGate':.15}, 'stage':'ILK–PINCH–Nck2 projection', 'note':'The bridge gate tests reduced coupling through the ILK–PINCH–Nck2 module.'},
    'nck': {'controls': {'bridgeGate':.15}, 'stage':'ILK–PINCH–Nck2 projection', 'note':'The bridge gate tests reduced coupling through the ILK–PINCH–Nck2 module to VKR1.'},
    'fak': {'controls': {'fakGate':.15}, 'stage':'FAK/Src mechanosensing', 'note':'Reduced FAK/Src coupling lowers the force-dependent receptor-signalling projection and its growth/migration outputs.'},
    'src': {'controls': {'fakGate':.15}, 'stage':'FAK/Src mechanosensing', 'note':'Reduced FAK/Src coupling lowers the force-dependent receptor-signalling projection and its growth/migration outputs.'},
    'paxillin': {'controls': {'migrationGate':.15}, 'stage':'Migration and traction', 'note':'Reduced paxillin-associated migration coupling lowers the protrusion and traction projections.'},
    'ptppest': {'controls': {'migrationGate':.15}, 'stage':'Adhesion turnover projection', 'note':'The migration gate probes PTP-PEST-associated turnover coupling as a functional projection.'},
    'grb2': {'controls': {'growthGate':.15}, 'stage':'Growth and survival', 'note':'Reduced adaptor coupling lowers ERK/Akt/survival projections; these are module readouts rather than fitted growth rates.'},
    'shc': {'controls': {'growthGate':.15}, 'stage':'Growth and survival', 'note':'Reduced Shc-associated adaptor coupling lowers growth and survival projections.'},
    'cofilin': {'controls': {'cytoskeletonGate':.15}, 'stage':'Actin regulation', 'note':'The actin-regulation gate probes cofilin-associated remodelling output.'},
    'profilin': {'controls': {'cytoskeletonGate':.15}, 'stage':'Actin regulation', 'note':'The actin-regulation gate probes profilin-associated polymerization coupling.'},
    'zyxin': {'controls': {'cytoskeletonGate':.15}, 'stage':'Actin regulation', 'note':'The actin-regulation gate probes zyxin-associated cytoskeletal organization.'},
    'vkr1': {'controls': {'vkrGate':.15}, 'stage':'VKR1 projection', 'note':'The S. mansoni receptor-context gate reduces the VKR1 readout downstream of the ILK–PINCH–Nck2 bridge.'},
}

for node, scenario in NODE_SCENARIOS.items():
    scenario['module'] = ('reproduction' if node in {'ilk','pinch','nck','vkr1'} else
                          'migration' if node in {'fak','src','paxillin','ptppest'} else
                          'growth' if node in {'shc','grb2'} else
                          'cytoskeleton' if node in {'actin','actinin','filamin','cofilin','profilin','zyxin'} else 'mechanics')

for family,node in {'integrin_alpha':'inta','integrin_beta':'intb','PINCH_like':'pinch','ILK':'ilk','FAK':'fak','Src':'src','alpha_actinin':'actinin','PTP_PEST':'ptppest','Grb2':'grb2','Shc':'shc','Nck':'nck','zyxin_like':'zyxin'}.items():
    NODE_SCENARIOS[family]=NODE_SCENARIOS[node]

# Current catalogue aliases use the same explicitly defined mechanism proxies.
for family,node in {'actin_conventional':'actin','zyxin_ajuba_like':'zyxin','SmVKR1':'vkr1'}.items():
    NODE_SCENARIOS[family]=NODE_SCENARIOS[node]

_MAP_BRIDGE = r'''
<style>
body.atlas-linked-profile main{grid-template-columns:minmax(0,1fr)!important;padding:0;gap:0}
body.atlas-linked-profile .sidebar,body.atlas-linked-profile>header{display:none!important}
body.atlas-linked-profile .paper{border:0;border-radius:0}
body.atlas-linked-profile .atlas-profiles-bar{border-top:0}
body.atlas-linked-profile #network{height:clamp(440px,calc(100dvh - 270px),850px)!important;min-height:440px!important}
body.atlas-linked-profile .graphheader .help{max-width:520px}
body.atlas-linked-profile .metric small{display:none}
body.atlas-linked-profile .metric b{font-size:19px}
body.atlas-linked-profile .atlas-profiles-bar label[for="atlas-path-target"],body.atlas-linked-profile #atlas-path-target{max-width:160px}
body.atlas-linked-profile .atlas-profiles-bar{position:relative;flex-wrap:nowrap;padding:11px 14px}
body.atlas-linked-profile .atlas-profiles-bar>label,body.atlas-linked-profile #atlas-profile-status{display:none}
body.atlas-linked-profile .atlas-profiles-bar>input{min-width:120px}
body.atlas-linked-profile .graphheader{justify-content:flex-end;padding:8px 12px}
body.atlas-linked-profile .graphheader>div:first-child{display:none}
.atlas-display-options{flex:none}.atlas-display-options>summary{padding:9px;border-radius:8px;background:#f1f6f2;font-size:12px;font-weight:650;color:#164a34;white-space:nowrap}
.atlas-display-options>div{position:absolute;z-index:100;right:12px;top:55px;display:grid;grid-template-columns:130px minmax(170px,1fr);gap:9px;align-items:center;background:#fff;padding:17px;border:1px solid #c7d9cb;border-radius:12px;box-shadow:0 12px 30px #163b2926}
.atlas-display-options select{width:100%;max-width:230px!important}.atlas-display-options input[type=range]{width:150px}
</style>
<script>
document.body.classList?.add('atlas-linked-profile');
// Fold supplementary controls/evidence; original controls and their handlers stay intact.
for(const [selector,label,className] of [['.controlbar','Network filters · species, confidence & reference evidence','atlas-filter-drawer'],['.networktable','Reference interaction evidence table','atlas-evidence-drawer']]){
 const section=document.querySelector(selector);if(!section)continue;const drawer=document.createElement('details'),summary=document.createElement('summary');drawer.className=className;summary.textContent=label;section.before(drawer);drawer.appendChild(summary);drawer.appendChild(section);
}
const displayBar=document.querySelector('.atlas-profiles-bar');if(displayBar){
 const options=document.createElement('details'),summary=document.createElement('summary'),content=document.createElement('div');options.className='atlas-display-options';summary.textContent='Path & display';options.appendChild(summary);options.appendChild(content);
 for(const id of ['atlas-node-font','atlas-path-scope','atlas-path-target']){const label=document.querySelector('label[for="'+id+'"]'),control=document.getElementById(id);if(label)content.appendChild(label);if(control)content.appendChild(control)}displayBar.appendChild(options);
}
const filterDrawer=document.querySelector('.atlas-filter-drawer'),filteredStats=document.querySelector('.topstats');if(filterDrawer&&filteredStats)filterDrawer.appendChild(filteredStats);
window.addEventListener('atlas-candidate-context',event=>window.parent.postMessage({type:'schisto-candidate-context',...event.detail},'*'));
const atlasNodeDetails=nodeDetails;
nodeDetails=function(id){atlasNodeDetails(id);
 const panel=document.getElementById('sidebar');if(!panel)return;
 const button=document.createElement('button');button.textContent='Simulate candidate and highlighted path';
 button.style.cssText='padding:10px;background:#ffe34d;color:#000;border:2px solid #064c2c;border-radius:8px;font-weight:bold';
 button.onclick=()=>{const context=window.atlasCandidateContext?.();if(context)window.parent.postMessage({type:'schisto-adhesome-node',...context},'*')};panel.prepend(button);
};
window.addEventListener('message',event=>{if(event.source!==window.parent||!event.data)return;
 if(event.data.type==='schisto-select-candidate')window.atlasSelectCandidate?.(event.data.candidate,false);
 if(event.data.type==='schisto-map-visible')applyView();
 if(event.data.type==='schisto-request-context')window.atlasPublishContext?.(true);
});
window.atlasPublishContext?.(true);
</script>
'''

_SIMULATOR_BRIDGE = r'''
<script>
const atlasNodeScenarios=__SCENARIOS__;
function candidateScenario(value){
 const origin=atlasNodeScenarios[value.node]||{controls:{},module:'mechanics',stage:'Family context',note:'No family-specific perturbation is present in the current library. The structural baseline is displayed.'};
 let originControls={...origin.controls},notes=[];const nodes=new Set(value.highlighted_path?.nodes||[]),pathControls={};
 const usePath=value.path_enabled!==false&&value.highlighted_path;
 if(usePath){
  const hasAny=names=>names.some(name=>nodes.has(name));
  const rules=[['fakGate',['FAK','Src'],'all'],['bridgeGate',['ILK','PINCH_like','Nck'],'all'],['migrationGate',['FAK','Src','paxillin_like','PTP_PEST'],'any'],['growthGate',['Shc','Grb2','AKT_like','MAPK_like'],'any'],['cytoskeletonGate',['actin','actin_conventional','talin','vinculin','alpha_actinin','filamin','cofilin','profilin','zyxin_like','zyxin_ajuba_like'],'any']];
  for(const [key,required,mode] of rules){const available=!value.highlighted_path.unreachable&&(mode==='all'?required.every(name=>nodes.has(name)):hasAny(required));pathControls[key]=available?1:0;notes.push(key+' = '+pathControls[key]+' ('+required.join(mode==='all'?' + ':' / ')+')')}
  pathControls.vkrGate=!value.highlighted_path.unreachable&&nodes.has('SmVKR1')&&['Schistosoma mansoni','S. mansoni','all','pan',''].includes(value.species||'')?1:0;
 }
 const controls={...pathControls};for(const [key,weight] of Object.entries(originControls))controls[key]=Object.hasOwn(pathControls,key)?Math.min(pathControls[key],weight):weight;
 return {...origin,controls,path_controls:pathControls,path_rule:usePath?'Highlighted families select downstream projection gates; I–T–V structural assembly retains its model.':'Family mechanism only; highlighted path retained as context.',path_notes:notes,
  note:origin.note+(usePath?' Downstream gates follow the highlighted association path.':'')};
}
function atlasRenderSimulationPath(){const context=document.getElementById('linkedContext');if(!context||!selection)return;
 const old=document.getElementById('atlas-simulation-path');if(old)old.remove();const box=document.createElement('div');box.id='atlas-simulation-path';box.style.cssText='padding:10px;background:#fff9d8;border:1px solid #b69f42;border-radius:7px';
 const title=document.createElement('strong');title.textContent='Candidate-linked path projection';box.appendChild(title);
 const path=selection.highlighted_path,p=document.createElement('p');p.textContent=path?(path.unreachable?'Target is disconnected under the active map filters.':path.route?.length?path.route.join(' ↔ '):path.nodes.join(' · ')):'No highlighted network path selected.';box.appendChild(p);
 const note=document.createElement('p');note.textContent=scenario?.path_rule||'';box.appendChild(note);
 if(scenario?.path_notes?.length){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Path gate assumptions';details.appendChild(summary);scenario.path_notes.forEach(text=>{const row=document.createElement('p');row.textContent=text;details.appendChild(row)});box.appendChild(details)}context.appendChild(box);
}
const atlasSimulationRender=render;
render=function(){atlasSimulationRender();atlasRenderSimulationPath()};
window.addEventListener('message',event=>{
 if(event.source!==window.parent||!event.data)return;
 if(event.data.type==='schisto-adhesome-visible'){resize();return}
 if(event.data.type==='schisto-adhesome-scenario')applyMapSelection(event.data,candidateScenario(event.data));
});
window.parent.postMessage({type:'schisto-simulator-ready'},'*');
</script>
'''


def _inject_before_body(html, extension):
    if '</body>' not in html:
        raise ValueError('Visualization HTML is missing its closing body tag')
    return html.replace('</body>', extension + '</body>', 1)


def linked_explorer_html(map_html, simulator_html):
    map_html=_inject_before_body(map_html,_MAP_BRIDGE)
    scenarios=json.dumps(NODE_SCENARIOS,ensure_ascii=False).replace('<','\\u003c')
    simulator_html=_inject_before_body(simulator_html,_SIMULATOR_BRIDGE.replace('__SCENARIOS__',scenarios))
    return _VIEWER_HTML.replace('</head>',network_style()+'</head>').replace('__MAP_FRAME__',escape(map_html,quote=True)).replace('__SIM_FRAME__',escape(simulator_html,quote=True))


_VIEWER_HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;font:14px Arial,sans-serif;background:#f4f6f2;color:#000;display:flex;flex-direction:column;height:100vh;height:100dvh;overflow:hidden}
header{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#eef6ef;border-top:4px solid #064c2c;flex-wrap:wrap}header strong{font-size:16px;margin-right:auto}
button,select{padding:8px;border:1px solid #08743f;border-radius:6px;background:#fff;color:#000;font:700 14px Arial,sans-serif;cursor:pointer}header button.active{background:#ffe34d}
button:focus-visible,a:focus-visible,select:focus-visible{outline:3px solid #b91c1c;outline-offset:2px}button:disabled{opacity:.5;cursor:default}
#status{padding:7px 12px;background:#fff9d8;border-bottom:1px solid #c2b26a;line-height:1.4}
.workspace{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,380px);gap:8px;padding:8px}
.visuals{min-width:0;min-height:0;overflow:auto;border:1px solid #bac8bc;background:white;border-radius:9px}
iframe{width:100%;height:100%;min-height:480px;border:0;display:block;background:#fff}iframe[hidden]{display:none}.visuals.compare iframe{height:560px}
.profile-rail{min-width:0;min-height:0;overflow:auto;border:2px solid #08743f;border-radius:9px;background:#fff;padding:12px}.profile-rail h2{font-size:19px;margin:0 0 10px}.profile-rail h3{font-size:17px;margin:8px 0;color:#000}.profile-rail p{line-height:1.5;color:#000}
.profile-rail select{width:100%;font-weight:400;margin:5px 0 10px}.profile-rail label{display:block;margin:8px 0;font-weight:bold}.profile-rail label input{margin-right:6px}.profile-rail a{color:#064c2c;font-weight:bold;overflow-wrap:anywhere}
.profile-rail table{border-collapse:collapse;width:100%;font-size:13px}.profile-rail td,.profile-rail th{border:1px solid #ccd4cc;padding:6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}.profile-rail th{background:#eef6ef;color:#000}.profile-rail .atlas-scroll{overflow:auto;max-height:270px}.profile-rail summary{cursor:pointer;padding:8px 0;font-weight:bold}.profile-rail .atlas-actions{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin:8px 0}.profile-rail small{font-size:12px;line-height:1.5;color:#222}
#pathSummary{padding:8px;background:#fff9d8;border:1px solid #d0be67;border-radius:6px;margin:8px 0;line-height:1.5;overflow-wrap:anywhere}#candidateProfile{margin-top:12px}
@media(max-width:760px){header strong{width:100%}.workspace{grid-template-columns:minmax(0,1fr);grid-template-rows:minmax(240px,1fr) minmax(180px,38vh)}.profile-rail{padding:10px}iframe{min-height:0}.visuals.compare iframe{height:500px}}
</style><style>
body{font-family:var(--atlas-font);background:#edf3ef}
header{background:#fff;padding:12px 16px;gap:6px;border-top:0;border-bottom:1px solid #dce5df}
header strong{font-size:15px;letter-spacing:-.02em;color:#103f2e}
header button{border:0;border-radius:8px;font-size:12px;font-weight:650;padding:9px 12px;color:#436052;min-height:36px}
header button.active{background:#e2efe7;color:#103f2e;box-shadow:inset 0 0 0 1px #c6dccd}
#workspaceFullscreen{margin-left:6px;border:1px solid #d2e0d6}
#status{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap;border:0}
.workspace{grid-template-columns:minmax(0,1fr) clamp(290px,25%,365px);gap:1px;padding:0;background:#dce5df}
.visuals{border:0;border-radius:0;background:white;overscroll-behavior:contain}
.profile-rail{border:0;border-radius:0;background:#fcfdfb;padding:21px 20px;scrollbar-width:thin;scrollbar-color:#bbcfc0 transparent}
.profile-rail h2{font-size:23px;line-height:1.25;letter-spacing:-.04em;color:#113f2c;margin-bottom:8px;overflow-wrap:anywhere}
.profile-rail h3{font-size:18px;line-height:1.35;letter-spacing:-.02em}
.profile-rail p{font-size:13px;line-height:1.6}.profile-rail small{font-size:12px;line-height:1.5}
#selectionHint{font-family:ui-monospace,Consolas,monospace;font-size:12px;overflow-wrap:anywhere;color:#526760}
#candidateCounts{color:#28563e;background:#eaf3ed;border-radius:8px;padding:10px;font-size:12px}
.profile-rail label{font-size:12px;color:#42604e;margin-top:16px}.profile-rail label:has(input){line-height:1.5;font-size:12px;font-weight:500}
.profile-rail select{border-color:#c4d5c9;border-radius:8px;font-size:13px;line-height:1.5;padding:10px;margin-bottom:6px}
.profile-rail table{font-size:13px;line-height:1.5}.profile-rail th,.profile-rail td{border:0;border-bottom:1px solid #e0e9e3;padding:9px 7px}.profile-rail th{width:38%;background:#f1f6f2;font-weight:600}
.profile-rail details{border-top:1px solid #dce5df;margin-top:15px}.profile-rail summary{color:#164a34;font-size:14px;padding:13px 0}
.profile-rail .atlas-actions button{font-size:12px;font-weight:600;border-color:#c7d9cc;background:#edf5ef;color:#143c2d;padding:8px 10px}
.profile-rail .atlas-profile-id{font-size:12px;color:#314b3d}
#simulateSelection{width:100%;background:#104c38;color:#fff;border-color:#104c38;padding:12px;font-size:13px}
#pathSummary{background:#f6f4e9;border:0;border-left:3px solid #ceb56b;border-radius:0 8px 8px 0;font-size:12px;padding:11px;color:#51482d}
#candidateProfile{padding-top:18px;border-top:1px solid #dce5df;margin-top:20px}
iframe{min-height:500px}.visuals.compare iframe{height:640px}
@media(max-width:1050px) and (min-width:761px){.workspace{grid-template-columns:minmax(0,1fr) 290px}.profile-rail{padding:16px 13px}header strong{width:100%;margin-bottom:4px}}
@media(max-width:760px){.workspace{grid-template-columns:1fr;grid-template-rows:minmax(360px,1fr) minmax(250px,40vh)}header{padding:10px}header strong{font-size:14px}header button{font-size:11px;padding:8px}#status{padding:7px 10px;font-size:11px}.profile-rail{padding:16px}.profile-rail h2{font-size:20px}iframe{min-height:0}}
:fullscreen{height:100dvh;background:#fff}
</style></head><body>
<header><strong>Interactive integrin-adhesome hypothesis</strong><button id="showMap" class="active" aria-pressed="true">Adhesome map</button><button id="showSimulator" aria-pressed="false">Downstream simulation</button><button id="showBoth" aria-pressed="false">Map + simulation</button><button id="workspaceFullscreen" title="Expand the map and dossier workspace">Full screen ↗</button></header>
<div id="status" role="status">Click any map node to open its linked candidates. The candidate profile stays visible during simulation.</div>
<main class="workspace">
<section id="visuals" class="visuals"><iframe id="mapFrame" title="Interactive schistosome adhesome map" srcdoc="__MAP_FRAME__"></iframe><iframe id="simulatorFrame" title="Candidate and path-linked simulator" srcdoc="__SIM_FRAME__" hidden></iframe></section>
<aside class="profile-rail" aria-label="Persistent candidate profile"><h2 id="profileFamily">Candidate dossier</h2><p id="selectionHint">Click a node on the map to explore its linked candidate proteins.</p><p id="candidateCounts" role="status"></p><label for="linkedCandidate">Candidates linked to this node</label><select id="linkedCandidate" disabled aria-label="Candidates linked to selected node"><option>Select a map node</option></select><div id="pathSummary">No path selected.</div><label><input id="usePath" type="checkbox" checked>Use highlighted path for downstream coupling</label><button id="simulateSelection" disabled>Simulate candidate and path</button><div id="candidateProfile"></div></aside>
</main>
<script>
const mapFrame=document.getElementById('mapFrame'),simulatorFrame=document.getElementById('simulatorFrame'),visuals=document.getElementById('visuals');
const mapButton=document.getElementById('showMap'),simButton=document.getElementById('showSimulator'),bothButton=document.getElementById('showBoth'),candidateSelect=document.getElementById('linkedCandidate');
let selectedContext=null,simulatorReady=false,scenarioPending=false,viewMode='map',renderedProfile='',debounce=null;
function selectionForSimulation(){if(!selectedContext)return null;return {node:selectedContext.node,title:selectedContext.title,candidate:selectedContext.candidate,candidate_annotation:selectedContext.candidate_annotation,orthogroup:selectedContext.orthogroup,species:selectedContext.species,module:selectedContext.module,candidate_profile:selectedContext.profile?.candidate||null,evidence_sources:selectedContext.profile?.sources||{},highlighted_path:selectedContext.highlighted_path,network_filters:selectedContext.network_filters,path_enabled:document.getElementById('usePath').checked}}
function sendScenario(){if(!selectedContext||!simulatorReady||viewMode==='map'||!scenarioPending)return;simulatorFrame.contentWindow.postMessage({...selectionForSimulation(),type:'schisto-adhesome-scenario'},'*');scenarioPending=false}
function view(which){viewMode=which;mapFrame.hidden=which==='simulation';simulatorFrame.hidden=which==='map';visuals.classList.toggle('compare',which==='both');
 for(const [button,mode] of [[mapButton,'map'],[simButton,'simulation'],[bothButton,'both']]){button.classList.toggle('active',mode===which);button.setAttribute('aria-pressed',String(mode===which))}
 if(which!=='map'&&simulatorReady){if(selectedContext&&scenarioPending)sendScenario();else simulatorFrame.contentWindow.postMessage({type:'schisto-adhesome-visible'},'*')}
 if(which!=='simulation')mapFrame.contentWindow.postMessage({type:'schisto-map-visible'},'*');
}
function updateCandidate(context){if(context.cleared){const heading=document.getElementById('profileFamily');if(heading)heading.textContent='Candidate dossier';selectedContext=null;scenarioPending=false;candidateSelect.replaceChildren();candidateSelect.disabled=true;document.getElementById('candidateCounts').textContent='';document.getElementById('simulateSelection').disabled=true;document.getElementById('candidateProfile').replaceChildren();renderedProfile='';document.getElementById('pathSummary').textContent='No path selected.';document.getElementById('selectionHint').textContent='Click a map node to explore its candidates.';document.getElementById('status').textContent='Selection cleared. Select another node to link its candidate and path to the simulation.';clearTimeout(debounce);return}selectedContext=context;scenarioPending=true;
 candidateSelect.replaceChildren();for(const candidate of context.candidates||[]){const option=document.createElement('option');option.value=candidate.id;option.textContent=candidate.id+' · '+candidate.species+' · '+candidate.grade;candidateSelect.appendChild(option)}candidateSelect.disabled=!(context.candidates||[]).length;candidateSelect.value=context.candidate||'';
 const counts=context.candidate_counts||Object.fromEntries(['A','B','C'].map(grade=>[grade,(context.candidates||[]).filter(p=>p.grade===grade).length]));document.getElementById('candidateCounts').textContent=(context.candidates||[]).length+' candidates · A = '+counts.A+' · B = '+counts.B+' · C = '+counts.C;
 document.getElementById('selectionHint').textContent=context.node+(context.candidate?' · '+context.candidate:' · no associated candidates in this selection');
 const heading=document.getElementById('profileFamily');if(heading)heading.textContent=context.node;
 const path=context.highlighted_path;document.getElementById('pathSummary').textContent=path?(path.unreachable?'Target is disconnected under the current filters.':!path.edges.length?'No recorded connections for '+context.node+' in the active topology.':path.route?.length?path.route.join(' ↔ '):path.nodes.length+' highlighted families · '+path.edges.length+' relationships · '+(path.mode==='component'?'connected component':path.mode+'-step neighborhood')):'No highlighted path.';
 const key=context.candidate||context.node;if(key!==renderedProfile){document.getElementById('candidateProfile').innerHTML=context.profile_html||'<p>No candidate profiles are associated with this node under the selected species and confidence filters. No additional information present in the current library.</p>';renderedProfile=key}
 document.getElementById('simulateSelection').disabled=false;document.getElementById('status').textContent='Selected '+context.node+(context.candidate?' · '+context.candidate:'')+' · profile remains visible with the simulation.';
 clearTimeout(debounce);if(viewMode!=='map')debounce=setTimeout(sendScenario,150)
}
window.addEventListener('message',event=>{if(event.source===simulatorFrame.contentWindow&&event.data?.type==='schisto-simulator-ready'){simulatorReady=true;if(scenarioPending)sendScenario();return}if(event.source!==mapFrame.contentWindow||!event.data)return;
 if(event.data.type==='schisto-candidate-context')updateCandidate(event.data);
 if(event.data.type==='schisto-adhesome-node'){updateCandidate(event.data);view('simulation')}
});
mapFrame.addEventListener('load',()=>mapFrame.contentWindow.postMessage({type:'schisto-request-context'},'*'));
simulatorFrame.addEventListener('load',()=>{simulatorReady=true;if(scenarioPending&&viewMode!=='map')sendScenario()});
candidateSelect.onchange=()=>mapFrame.contentWindow.postMessage({type:'schisto-select-candidate',candidate:candidateSelect.value},'*');
document.getElementById('simulateSelection').onclick=()=>{scenarioPending=true;view('simulation')};
document.getElementById('usePath').onchange=()=>{scenarioPending=true;if(viewMode!=='map')sendScenario()};
document.getElementById('candidateProfile').addEventListener('click',event=>{if(!event.target.closest('[data-atlas-profile-download]')||!selectedContext?.profile)return;const blob=new Blob([JSON.stringify({...selectedContext.profile,highlighted_path:selectedContext.highlighted_path,network_filters:selectedContext.network_filters},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=selectedContext.candidate+'_candidate_path_profile.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});
mapButton.onclick=()=>view('map');simButton.onclick=()=>view('simulation');bothButton.onclick=()=>view('both');
document.getElementById('workspaceFullscreen')?.addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch(error){document.getElementById('status').textContent='Full screen is unavailable in this embedded browser. Use the standalone HTML download for an expanded workspace.'}});
</script></body></html>'''
