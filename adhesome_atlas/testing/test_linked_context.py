"""Node-driven candidate/path synchronization and persistent simulation profiles."""
from bootstrap import ATLAS_ROOT
import json,re,shutil,subprocess
from pathlib import Path
from linked_explorer import _SIMULATOR_BRIDGE,_VIEWER_HTML,NODE_SCENARIOS


def main():
    node=shutil.which('node')
    assert node,'Node is needed for browser-side integration checks'
    simulator=re.search(r'<script>(.*?)</script>',_SIMULATOR_BRIDGE,re.S).group(1).replace('__SCENARIOS__',json.dumps(NODE_SCENARIOS))
    outer=re.findall(r'<script>(.*?)</script>',_VIEWER_HTML,re.S)[-1]
    for name,script in [('simulator bridge',simulator),('persistent viewer',outer)]:
        result=subprocess.run([node,'--check'],input=script,text=True,capture_output=True);assert result.returncode==0,(name,result.stderr)
    engine=(Path(__file__).resolve().parents[1]/'main/simulator_engine.js').read_text(encoding='utf-8')
    fixture=r'''
const vm=require('vm'),assert=require('assert');
let scenario=null,received=null;const simulatorParent={postMessage(){}};
const sim={console,selection:null,render(){},resize(){},inspectMechanism(){},$(){return {value:''}},document:{getElementById(){return null}},applyMapSelection(value,mapping){received=value;scenario=mapping},window:{parent:simulatorParent,addEventListener(type,callback){this.listener=callback}}};
vm.createContext(sim);vm.runInContext(__SIM__,sim);
const path={root:'ILK',mode:'2',target:'',route:[],nodes:['ILK','PINCH_like','Nck'],edges:[{id:'e1',a:'ILK',b:'PINCH_like'}],unreachable:false};
let value={node:'ILK',title:'ILK',candidate:'Sman__Smp_079760',species:'Schistosoma mansoni',highlighted_path:path,path_enabled:true};
sim.window.listener({source:simulatorParent,data:{...value,type:'schisto-adhesome-scenario'}});
assert.equal(scenario.path_controls.bridgeGate,1);assert.equal(scenario.controls.bridgeGate,1);assert.equal(scenario.controls.ilkProbability,.15);assert.equal(scenario.controls.fakGate,0);assert.equal(scenario.controls.vkrGate,0);assert.equal(received.candidate,'Sman__Smp_079760');
value={...value,highlighted_path:{...path,nodes:['ILK','PINCH_like']}};sim.window.listener({source:simulatorParent,data:{...value,type:'schisto-adhesome-scenario'}});assert.equal(scenario.controls.bridgeGate,0);
value={...value,path_enabled:false};sim.window.listener({source:simulatorParent,data:{...value,type:'schisto-adhesome-scenario'}});assert.equal(scenario.controls.ilkProbability,.15);assert.equal(Object.keys(scenario.path_controls).length,0);
value={...value,path_enabled:true,highlighted_path:{...path,nodes:['ILK','PINCH_like','Nck','SmVKR1']},species:'Schistosoma bovis'};sim.window.listener({source:simulatorParent,data:{...value,type:'schisto-adhesome-scenario'}});assert.equal(scenario.controls.vkrGate,0);
value.species='Schistosoma mansoni';sim.window.listener({source:simulatorParent,data:{...value,type:'schisto-adhesome-scenario'}});assert.equal(scenario.controls.vkrGate,1);
const engineContext={};vm.createContext(engineContext);vm.runInContext(__ENGINE__+';globalThis.engine=AdhesionMatrix',engineContext);const engine=engineContext.engine;
const parameters={...engine.defaults,grid:3,integrins:9,steps:10,seed:7,ligand:1,off:0,load:0,threshold:.1,ruptureForce:100,feedback:0,actinProbability:1,layeredMechanics:false};
const base=engine.simulate({...parameters,...scenario.path_controls},engine.matrix(1,1,0)),perturbed=engine.simulate({...parameters,...scenario.controls},engine.matrix(1,1,0));
assert.equal(base.snapshots.at(-1).metrics.mature,perturbed.snapshots.at(-1).metrics.mature);assert(base.snapshots.at(-1).metrics.bridge>perturbed.snapshots.at(-1).metrics.bridge);

class Element{constructor(){this.children=[];this.hidden=false;this.disabled=false;this.checked=true;this.value='';this.innerHTML='';this.classList={toggle(){}};this.handlers={};this.contentWindow={messages:[],postMessage(value){this.messages.push(value)}}}setAttribute(){}addEventListener(type,callback){this.handlers[type]=callback}appendChild(child){this.children.push(child)}replaceChildren(){this.children=[]}}
const elements=new Map();for(const id of ['mapFrame','simulatorFrame','visuals','showMap','showSimulator','showBoth','linkedCandidate','status','selectionHint','candidateCounts','pathSummary','candidateProfile','simulateSelection','usePath'])elements.set(id,new Element());
let listener=null;const timers=[];const viewer={console,URL,Blob,setTimeout(callback){timers.push(callback)},clearTimeout(){},document:{getElementById:id=>elements.get(id),createElement:()=>new Element()},window:{addEventListener(type,callback){listener=callback}}};
vm.createContext(viewer);vm.runInContext(__VIEWER__,viewer);elements.get('simulatorFrame').handlers.load();
let context={type:'schisto-candidate-context',node:'ILK',title:'ILK',candidate:'Sman__Smp_079760',candidate_annotation:'ILK-like',species:'Schistosoma mansoni',orthogroup:'OG_ACTIVE',candidates:[{id:'Sman__Smp_079760',species:'Schistosoma mansoni',grade:'A'},{id:'Sman__other',species:'Schistosoma mansoni',grade:'C'}],profile_html:'<h3>ILK candidate profile</h3>',profile:{candidate:{sequence_id:'Sman__Smp_079760'},sources:{candidates:'active workbook'}},highlighted_path:path,network_filters:{grade:'all'}};
listener({source:elements.get('mapFrame').contentWindow,data:context});assert.equal(elements.get('candidateProfile').innerHTML,context.profile_html);
elements.get('simulateSelection').onclick();assert.equal(elements.get('mapFrame').hidden,true);assert.equal(elements.get('simulatorFrame').hidden,false);assert.equal(elements.get('candidateProfile').hidden,false);assert.equal(elements.get('candidateProfile').innerHTML,context.profile_html);
let outgoing=elements.get('simulatorFrame').contentWindow.messages.at(-1);assert.equal(outgoing.candidate,context.candidate);assert.equal(outgoing.highlighted_path.root,'ILK');assert.equal(outgoing.candidate_profile.sequence_id,context.candidate);
elements.get('linkedCandidate').value='Sman__other';elements.get('linkedCandidate').onchange();assert.equal(elements.get('mapFrame').contentWindow.messages.at(-1).candidate,'Sman__other');
context={...context,candidate:'Sman__other',profile_html:'<h3>Other candidate</h3>',profile:{...context.profile,candidate:{sequence_id:'Sman__other'}}};listener({source:elements.get('mapFrame').contentWindow,data:context});timers.at(-1)();assert.equal(elements.get('candidateProfile').innerHTML,context.profile_html);assert.equal(elements.get('simulatorFrame').contentWindow.messages.at(-1).candidate,'Sman__other');
elements.get('showBoth').onclick();assert.equal(elements.get('mapFrame').hidden,false);assert.equal(elements.get('simulatorFrame').hidden,false);
elements.get('usePath').checked=false;elements.get('usePath').onchange();assert.equal(elements.get('simulatorFrame').contentWindow.messages.at(-1).path_enabled,false);
const before=elements.get('candidateProfile').innerHTML;listener({source:{},data:{...context,profile_html:'untrusted'}});assert.equal(elements.get('candidateProfile').innerHTML,before);listener({source:elements.get('mapFrame').contentWindow,data:{type:'schisto-candidate-context',cleared:true}});assert.equal(elements.get('simulateSelection').disabled,true);
console.log('PASS node-driven persistent profiles, candidate switching, highlighted-path export, path gates, species restriction, split view and source checks');
'''
    fixture=fixture.replace('__SIM__',json.dumps(simulator)).replace('__VIEWER__',json.dumps(outer)).replace('__ENGINE__',json.dumps(engine))
    result=subprocess.run([node,'-'],input=fixture,text=True,capture_output=True)
    assert result.returncode==0,result.stderr
    print(result.stdout.strip(),flush=True)
if __name__=='__main__':main()
