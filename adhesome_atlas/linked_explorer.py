"""Connect the family map to the local adhesion-matrix simulator."""
from html import escape
import json


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

_MAP_BRIDGE = r'''
<script>
const atlasNodeDetails=nodeDetails;
nodeDetails=function(id){atlasNodeDetails(id);
 const panel=document.getElementById('sidebar');if(!panel)return;
 const button=document.createElement('button');button.textContent='Explore downstream simulation →';
 button.style.cssText='padding:10px;background:#ffe34d;color:#000;border:2px solid #064c2c;border-radius:8px;font-weight:bold';
 button.onclick=()=>{const selected=window.atlasSelectedCandidate?.();window.parent.postMessage({type:'schisto-adhesome-node',node:id,title:id,candidate:selected?.sequence_id||'',candidate_annotation:selected?.candidate_annotation||'',orthogroup:selected?.orthogroup||'',species:selected?.species||({'Schistosoma haematobium':'S. haematobium','Schistosoma japonicum':'S. japonicum','Schistosoma mansoni':'S. mansoni'}[document.getElementById('species')?.value]||document.getElementById('species')?.value||''),module:'all'},'*')};panel.prepend(button);
};
</script>
'''

_SIMULATOR_BRIDGE = r'''
<script>
const atlasNodeScenarios=__SCENARIOS__;
function candidateScenario(value){let scenario=atlasNodeScenarios[value.node];const annotation=value.candidate_annotation||'';
  const distinct=(value.node==='talin'&&annotation.startsWith('HIP1R'))||
    (value.node==='vinculin'&&annotation.startsWith('Catenin-related'))||
    (value.node==='ilk'&&/^(GS-domain|MAPK-activated|OSR1-like|ILK-screened)/.test(annotation));
  if(distinct)scenario={controls:{},module:scenario?.module||'cytoskeleton',stage:'Calibrated lineage context',note:annotation+' is distinct from the canonical family component represented by this scenario. The baseline I–T–V model is displayed.'};
  return scenario||{controls:{},module:'mechanics',stage:'Family context',note:'No family-specific simulation mechanism is present in the current library. The baseline model is displayed; additional coupling will be added when information is available.'};
}
window.addEventListener('message',event=>{
  if(event.source!==window.parent||!event.data)return;
  if(event.data.type==='schisto-adhesome-visible'){resize();return}
  if(event.data.type==='schisto-adhesome-scenario')applyMapSelection(event.data,candidateScenario(event.data));
});
</script>
'''


def _inject_before_body(html, extension):
    if '</body>' not in html:
        raise ValueError('Visualization HTML is missing its closing body tag')
    return html.replace('</body>', extension + '</body>', 1)


def linked_explorer_html(map_html, simulator_html):
    map_html = _inject_before_body(map_html, _MAP_BRIDGE)
    scenarios = json.dumps(NODE_SCENARIOS, ensure_ascii=False).replace('<', '\\u003c')
    simulator_html = _inject_before_body(simulator_html, _SIMULATOR_BRIDGE.replace('__SCENARIOS__', scenarios))
    map_srcdoc, simulator_srcdoc = escape(map_html, quote=True), escape(simulator_html, quote=True)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,sans-serif;background:#f4f6f2;color:#111}}
header{{height:62px;display:flex;align-items:center;gap:10px;padding:8px 14px;background:#eef6ef;color:#000000;border-top:4px solid #064c2c}}
header strong{{font-size:16px;margin-right:auto}}header button{{padding:8px 13px;border:2px solid #ffe34d;border-radius:8px;background:#fff;color:#000000;font-weight:750;cursor:pointer}}
header button.active{{background:#ffe34d}}header button:focus-visible{{outline:3px solid #e11d48;outline-offset:2px}}
#status{{padding:6px 14px;background:#fff9d8;color:#000000;font-size:14px;border-bottom:1px solid #d4c069}}
iframe{{width:100%;height:calc(100vh - 91px);border:0;display:block;background:#fff}}iframe[hidden]{{display:none}}
@media(max-width:680px){{header{{height:auto;flex-wrap:wrap}}header strong{{width:100%}}iframe{{height:calc(100vh - 130px)}}}}
</style></head><body>
<header><strong>Interactive integrin-adhesome hypothesis</strong><button id="showMap" class="active" aria-pressed="true">Adhesome map</button><button id="showSimulator" aria-pressed="false">Linked matrix simulator</button></header>
<div id="status" role="status">Select a map node, then choose “Explore downstream simulation” in its evidence panel.</div>
<iframe id="mapFrame" title="Interactive schistosome adhesome map" srcdoc="{map_srcdoc}"></iframe>
<iframe id="simulatorFrame" title="Linked schistosome and reference matrix simulator" srcdoc="{simulator_srcdoc}" hidden></iframe>
<script>
const mapFrame=document.getElementById('mapFrame'),simulatorFrame=document.getElementById('simulatorFrame');
const mapButton=document.getElementById('showMap'),simButton=document.getElementById('showSimulator');
let selectedNode=null,simulatorReady=false,scenarioPending=false;
function view(which){{const showMap=which==='map';mapFrame.hidden=!showMap;simulatorFrame.hidden=showMap;
  mapButton.classList.toggle('active',showMap);simButton.classList.toggle('active',!showMap);mapButton.setAttribute('aria-pressed',String(showMap));simButton.setAttribute('aria-pressed',String(!showMap));
  if(!showMap&&simulatorReady){{if(selectedNode&&scenarioPending){{simulatorFrame.contentWindow.postMessage({{...selectedNode,type:'schisto-adhesome-scenario'}},'*');scenarioPending=false}}else simulatorFrame.contentWindow.postMessage({{type:'schisto-adhesome-visible'}},'*')}}}}
window.addEventListener('message',event=>{{if(event.source!==mapFrame.contentWindow||!event.data||event.data.type!=='schisto-adhesome-node')return;selectedNode=event.data;scenarioPending=true;document.getElementById('status').textContent='Selected '+selectedNode.title+(selectedNode.candidate?' · '+selectedNode.candidate:'')+' — seeded local adhesion-matrix scenario.';view('simulator')}});
simulatorFrame.addEventListener('load',()=>{{simulatorReady=true;if(selectedNode&&!simulatorFrame.hidden)view('simulator')}});
mapButton.addEventListener('click',()=>view('map'));simButton.addEventListener('click',()=>view('simulator'));
</script></body></html>'''
