"""Connect the curated family map to the qualitative signalling simulator."""

from html import escape
import json


# A map node can select a perturbation only when the simulator has a defensible
# proxy control for it. Other nodes retain the baseline and an explicit note.
NODE_SCENARIOS = {
    'collagen': {'controls': {'ligandClass': 'collagen', 'ligand': 20},
                 'stage': 'Extracellular input', 'note': 'Reduced candidate collagen-like input is an availability proxy; binding to the displayed integrin is unconfirmed.'},
    'laminin': {'controls': {'ligandClass': 'laminin', 'ligand': 20},
                'stage': 'Extracellular input', 'note': 'Reduced candidate laminin-like input is an availability proxy; binding to the displayed integrin is unconfirmed.'},
    'vascular_context': {'controls': {'ligandClass': 'vascular', 'ligand': 20},
                         'stage': 'Host-interface input', 'note': 'Reduced host-interface input is a conceptual proxy, not a measured vascular force or confirmed receptor ligand.'},
    'inta': {'controls': {'affinity': 0}, 'stage': 'Integrin activation',
             'note': 'A bent, low-affinity receptor state probes the putative αβ receptor; no particular α–β protein pair is assigned.'},
    'intb': {'controls': {'affinity': 0}, 'stage': 'Integrin activation',
             'note': 'A bent, low-affinity receptor state probes the putative αβ receptor; no particular α–β protein pair is assigned.'},
    'integrin_ab': {'controls': {'affinity': 0}, 'stage': 'Integrin activation',
                    'note': 'A bent, low-affinity state probes the virtual αβ receptor; its physiological subunit pairing is unresolved.'},
    'talin': {'controls': {'talin': 15}, 'stage': 'Adaptor coupling',
              'note': 'Reduced talin–kindlin recruitment is a module-level proxy, not a fitted talin loss-of-function phenotype.'},
    'kindlin': {'controls': {'talin': 15}, 'stage': 'Adaptor coupling',
                'note': 'Reduced talin–kindlin recruitment is a module-level proxy, not a fitted kindlin loss-of-function phenotype.'},
    'vinculin': {'controls': {'tension': 15}, 'stage': 'Force maturation',
                 'note': 'Reduced actomyosin tension is a force-coupling proxy, not a specific vinculin perturbation model.'},
    'actinin': {'controls': {'tension': 15}, 'stage': 'Force maturation',
                'note': 'Reduced actomyosin tension is a force-coupling proxy, not a specific α-actinin perturbation model.'},
    'filamin': {'controls': {'tension': 15}, 'stage': 'Force maturation',
                'note': 'Reduced actomyosin tension is a force-coupling proxy, not a specific filamin perturbation model.'},
    'actin': {'controls': {'tension': 15}, 'stage': 'Force maturation',
              'note': 'Reduced actomyosin tension is a cytoskeletal proxy, not a protein-specific actin perturbation model.'},
    'ilk': {'controls': {'perturbation': 'ilk-disruption'}, 'stage': 'ILK–PINCH–Nck2 coupling',
            'note': 'The shared ILK-coupling switch represents disruption of the modelled bridge, not a measured single-protein effect.'},
    'pinch': {'controls': {'perturbation': 'ilk-disruption'}, 'stage': 'ILK–PINCH–Nck2 coupling',
              'note': 'The shared ILK-coupling switch represents disruption of the modelled bridge, not a measured single-protein effect.'},
    'nck': {'controls': {'perturbation': 'ilk-disruption'}, 'stage': 'ILK–PINCH–Nck2 coupling',
            'note': 'The shared ILK-coupling switch represents disruption of the modelled bridge, not a measured single-protein effect.'},
    'fak': {'controls': {'perturbation': 'fak-inhibitor'}, 'stage': 'FAK/Src signalling',
            'note': 'The FAK/Src inhibitor switch tests the module; it is not a calibrated FAK-specific effect.'},
    'src': {'controls': {'perturbation': 'fak-inhibitor'}, 'stage': 'FAK/Src signalling',
            'note': 'The FAK/Src inhibitor switch tests the module; it is not a calibrated Src-specific effect.'},
    'vkr1': {'controls': {'perturbation': 'vkr1-inhibitor'}, 'stage': 'VKR1-associated output',
             'note': 'The VKR1 branch switch tests the S. mansoni reproductive-coupling hypothesis; it does not infer a family-wide kinetic effect.'},
}

_MAP_BRIDGE = r"""
<style>
#info .atlas-simulate{margin-top:14px;padding:10px 14px;border:2px solid #075d32;border-radius:8px;background:#ffe34d;color:#111;font-weight:800;cursor:pointer}
#info .atlas-simulate:focus-visible{outline:3px solid #b91c1c;outline-offset:2px}
</style>
<script>
const atlasMapShowNode = showNode;
showNode = function(node) {
  atlasMapShowNode(node);
  const button=document.createElement('button');
  button.className='atlas-simulate';
  button.textContent='Explore downstream simulation →';
  button.addEventListener('click', () => {
    const candidate=atlasPayload.candidates.find(r => r.sequence_id===atlasPayload.focus_candidate && r.map_node===node.id);
    window.parent.postMessage({type:'schisto-adhesome-node',node:node.id,title:node.title,
      candidate:candidate ? candidate.sequence_id : '',species:candidate ? candidate.species : ''}, '*');
  });
  const heading=info.querySelector('h2');
  if (heading) heading.insertAdjacentElement('afterend',button); else info.prepend(button);
  const caption=document.createElement('p');
  caption.textContent='Opens a qualitative module-level scenario. Nodes without a direct simulator control show the baseline with an explicit mapping note.';
  button.insertAdjacentElement('afterend',caption);
};
const atlasInitialLinkedNode=nodes.find(n => n.id===atlasPayload.focus_node);
if (atlasInitialLinkedNode) showNode(atlasInitialLinkedNode);
</script>
"""

_SIMULATOR_BRIDGE = r"""
<style>
#atlas-linked-context{margin:0 0 14px;padding:15px 18px;background:#fff9d8;color:#111;border:2px solid #c69c00;border-left:6px solid #075d32;border-radius:10px;line-height:1.45}
#atlas-linked-context strong{font-size:16px}#atlas-linked-context p{margin:6px 0 0}
</style>
<script>
const atlasNodeScenarios=__SCENARIOS__;
const atlasModelDefaults={ligand:75,affinity:2,talin:75,tension:70,ligandClass:'mixed',adaptation:'parasite',perturbation:'none'};
const atlasContext=document.createElement('div');
atlasContext.id='atlas-linked-context';
atlasContext.innerHTML='<strong>Linked map simulation</strong><p>Select a node on the map to load its qualitative scenario.</p>';
document.querySelector('.app').prepend(atlasContext);
function atlasSetControls(values) {
  for (const [key,value] of Object.entries(values)) {
    if (key==='perturbation') document.querySelector(`input[name="perturbation"][value="${value}"]`).checked=true;
    else $(key).value=value;
  }
}
function atlasFinals() {
  const result=model();
  return {maturation:Math.round(result.M.at(-1)),signalling:Math.round(result.S.at(-1))};
}
window.addEventListener('message', event => {
  if (event.source!==window.parent || !event.data) return;
  if (event.data.type==='schisto-adhesome-visible') { resize(); resizeReference(); return; }
  if (event.data.type!=='schisto-adhesome-scenario') return;
  const selection=event.data;
  const scenario=atlasNodeScenarios[selection.node];
  atlasSetControls(atlasModelDefaults);
  $('species').value=selection.species==='S. haematobium'?'sh':selection.species==='S. japonicum'?'sj':
    selection.species==='S. mansoni' || selection.node==='vkr1'?'sm':'pan';
  const baseline=atlasFinals();
  if (scenario) atlasSetControls(scenario.controls);
  const selected=atlasFinals();
  update();
  resize(); resizeReference();
  atlasContext.replaceChildren();
  const heading=document.createElement('strong');
  heading.textContent=selection.title+(selection.candidate?' · '+selection.candidate:'');
  atlasContext.appendChild(heading);
  const interpretation=document.createElement('p');
  interpretation.textContent=scenario ? scenario.stage+' — '+scenario.note :
    'No family-specific control is defined for this node. The baseline model is shown without an invented perturbation.';
  atlasContext.appendChild(interpretation);
  const numbers=document.createElement('p');
  numbers.textContent=`Illustrative schistosome baseline → selected scenario: adhesion maturation ${baseline.maturation}% → ${selected.maturation}%; combined signalling ${baseline.signalling}% → ${selected.signalling}%. Shared settings also drive the canonical reference panel.`;
  atlasContext.appendChild(numbers);
});
</script>
"""


def _inject_before_body(html, extension):
    if '</body>' not in html:
        raise ValueError('Visualization HTML is missing its closing body tag')
    return html.replace('</body>', extension + '</body>', 1)


def linked_explorer_html(map_html, simulator_html):
    """Render both existing HTML tools inside one message-routed atlas workspace."""
    map_html = _inject_before_body(map_html, _MAP_BRIDGE)
    scenarios = json.dumps(NODE_SCENARIOS, ensure_ascii=False).replace('<', '\\u003c')
    simulator_html = _inject_before_body(simulator_html, _SIMULATOR_BRIDGE.replace('__SCENARIOS__', scenarios))
    map_srcdoc = escape(map_html, quote=True)
    simulator_srcdoc = escape(simulator_html, quote=True)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:#f4f6f2;color:#111}}
header{{height:62px;display:flex;align-items:center;gap:10px;padding:8px 14px;background:#064c2c;color:#fff}}
header strong{{font-size:15px;margin-right:auto}}header button{{padding:8px 13px;border:2px solid #ffe34d;border-radius:8px;background:#fff;color:#111;font-weight:750;cursor:pointer}}
header button.active{{background:#ffe34d}}header button:focus-visible{{outline:3px solid #e11d48;outline-offset:2px}}
#status{{padding:6px 14px;background:#fff9d8;color:#111;font-size:12px;border-bottom:1px solid #d4c069}}
iframe{{width:100%;height:calc(100vh - 91px);border:0;display:block;background:#fff}}iframe[hidden]{{display:none}}
@media(max-width:680px){{header{{height:auto;flex-wrap:wrap}}header strong{{width:100%}}iframe{{height:calc(100vh - 130px)}}}}
</style></head><body>
<header><strong>Interactive integrin-adhesome hypothesis</strong><button id="showMap" class="active" aria-pressed="true">Adhesome map</button><button id="showSimulator" aria-pressed="false">Linked simulator</button></header>
<div id="status" role="status">Select a map node, then choose “Explore downstream simulation” in its evidence panel.</div>
<iframe id="mapFrame" title="Interactive schistosome adhesome map" srcdoc="{map_srcdoc}"></iframe>
<iframe id="simulatorFrame" title="Linked schistosome and reference simulator" srcdoc="{simulator_srcdoc}" hidden></iframe>
<script>
const mapFrame=document.getElementById('mapFrame'),simulatorFrame=document.getElementById('simulatorFrame');
const mapButton=document.getElementById('showMap'),simButton=document.getElementById('showSimulator');
let selectedNode=null, simulatorReady=false, scenarioPending=false;
function view(which){{
  const showMap=which==='map';
  mapFrame.hidden=!showMap;simulatorFrame.hidden=showMap;
  mapButton.classList.toggle('active',showMap);simButton.classList.toggle('active',!showMap);
  mapButton.setAttribute('aria-pressed',String(showMap));simButton.setAttribute('aria-pressed',String(!showMap));
  if(!showMap&&simulatorReady){{
    if(selectedNode&&scenarioPending){{
      simulatorFrame.contentWindow.postMessage({{...selectedNode,type:'schisto-adhesome-scenario'}},'*');
      scenarioPending=false;
    }} else simulatorFrame.contentWindow.postMessage({{type:'schisto-adhesome-visible'}},'*');
  }}
}}
window.addEventListener('message',event=>{{
  if(event.source!==mapFrame.contentWindow||!event.data||event.data.type!=='schisto-adhesome-node')return;
  selectedNode=event.data;
  scenarioPending=true;
  document.getElementById('status').textContent='Selected '+selectedNode.title+(selectedNode.candidate?' · '+selectedNode.candidate:'')+' — qualitative model scenario.';
  view('simulator');
}});
simulatorFrame.addEventListener('load',()=>{{simulatorReady=true;if(selectedNode&&!simulatorFrame.hidden)view('simulator')}});
mapButton.addEventListener('click',()=>view('map'));
simButton.addEventListener('click',()=>view('simulator'));
</script></body></html>'''
