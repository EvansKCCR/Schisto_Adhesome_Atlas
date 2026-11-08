"""Candidate-map identity/evidence joins, offline profiles and navigation checks."""
from bootstrap import ATLAS_ROOT
import json,re,shutil,subprocess,sys
from html import unescape
from data import ROOT,load
from candidate_profiles import profile_payload,candidate_map_html,atlas_url,START
from linked_explorer import _MAP_BRIDGE


def main():
    cohorts,books,motifs,*_=load();candidates=cohorts['Adhesome candidates']
    payload=profile_payload(candidates,books,motifs)
    records={row[0]:dict(zip(payload['fields'],row)) for row in payload['candidates']}
    assert set(records)==set(candidates.sequence_id)
    target='Sman__Smp_079760';record=records[target]
    assert record['family']=='ILK' and record['grade']=='A'
    assert record['orthogroup']==candidates.set_index('sequence_id').loc[target,'orthogroup']
    for kind,key in [('domains','sequence_id'),('motifs','sequence_id'),('orthology','candidate_id')]:
        assert set(payload[kind]['rows'])<=set(records)
        assert len(payload[kind]['rows'][target])>0,kind
    from library_refresh import refresh_family_html
    source=refresh_family_html((ROOT/'adhesome_network/Schistosome_adhesome_rebuilt.html').read_text(encoding='utf-8'),candidates,ROOT)
    assert refresh_family_html(source,candidates,ROOT)==source,'Source regeneration must be idempotent'
    html=candidate_map_html(source,payload,app_url='https://atlas.example/app',focus_candidate=target)
    # Selection repairs must leave the authored inventory/topology byte-for-byte intact.
    assert re.search(r'const DATA=(.*?);\s*const \$',source,re.S)[1]==re.search(r'const DATA=(.*?);\s*const \$',html,re.S)[1]
    assert html.count(START)==1
    assert candidate_map_html(html,payload,app_url='https://atlas.example/app',focus_candidate=target)==html
    assert atlas_url('https://atlas.example/app?old=1','Protein dossier',target)=='https://atlas.example/app?view=Protein+dossier&protein=Sman__Smp_079760'
    node=shutil.which('node')
    if node:
        script=next(s for s in re.findall(r'<script[^>]*>(.*?)</script>',html,re.S) if 'const atlasProfiles=' in s)
        check=subprocess.run([node,'--check'],input=script,text=True,capture_output=True);assert check.returncode==0,check.stderr
        # Selection/evidence unit checks; real pointer events are covered by --browser.
        stub=r'''
const vm=require('vm'),assert=require('assert');
class Element{
 constructor(tag){this.tag=tag;this.children=[];this.style={};this.value='';this.textContent='';this.attributes={}}
 appendChild(e){this.children.push(e);e.parent=this;return e}append(e){return this.appendChild(e)}prepend(e){this.children.unshift(e)}after(e){this.afterElement=e}
 setAttribute(k,v){this.attributes[k]=v}getAttribute(k){return this.attributes[k]}
 replaceChildren(){this.children=[]}addEventListener(){}remove(){if(this.parent)this.parent.children=this.parent.children.filter(e=>e!==this)}
 get options(){return this.tag==='select'?this.children:[]}get nextSibling(){if(!this.parent)return null;return this.parent.children[this.parent.children.indexOf(this)+1]}
 querySelectorAll(tag){return this.children.flatMap(e=>[...((tag==='*'||e.tag===tag)?[e]:[]),...e.querySelectorAll(tag)])}
 querySelector(tag){return tag==='button.atlas-panel-close'?this.querySelectorAll('button').find(e=>e.className==='atlas-panel-close'):this.querySelectorAll(tag)[0]}
}
const elements=new Map(),header=new Element('header'),body=new Element('body');
for(const id of ['sidebar','species','grade','scope','search'])elements.set(id,new Element(id==='sidebar'?'div':'select'));
elements.get('species').value='all';elements.get('grade').value='all';
const events=new Map();
const ctx={console,URL,URLSearchParams,Blob,setTimeout,CustomEvent:class{constructor(type,options){this.type=type;this.detail=options.detail}},document:{createElement:t=>new Element(t),body,
 getElementById(id){if(elements.has(id))return elements.get(id);const all=[...(header.afterElement?[header.afterElement,...header.afterElement.querySelectorAll('*')]:[]),...elements.get('sidebar').querySelectorAll('*')];return all.find(e=>e.id===id)},
 querySelector:q=>q==='header'?header:null,querySelectorAll:()=>[]},
 DATA:{families:__FAMILIES__},current:{family:null},needsFit:false,activeEdges:[{id:'e1',a:'ILK',b:'PINCH_like'},{id:'e2',a:'PINCH_like',b:'Nck'},{id:'e3',a:'Nck',b:'Src'}],zoom:{},applyView(){},
 settings(){return {species:elements.get('species').value,grade:elements.get('grade').value}},
 edgeDetails(){},nodeDetails(id){elements.get('sidebar').replaceChildren()},draw(){if(ctx.current.family)ctx.nodeDetails(ctx.current.family)},setNode(id){ctx.current.family=id;ctx.draw()},window:{addEventListener(type,callback){if(!events.has(type))events.set(type,[]);events.get(type).push(callback)},dispatchEvent(event){for(const callback of events.get(event.type)||[])callback(event)}}};
vm.createContext(ctx);vm.runInContext(__SCRIPT__,ctx);assert.equal(ctx.window.atlasSelectedCandidate().sequence_id,'Sman__Smp_079760');
assert.equal(ctx.current.family,'ILK');assert.equal(elements.get('species').value,'Schistosoma mansoni');
assert.equal(ctx.window.atlasSelectCandidate('missing-id'),false);
const sidebar=elements.get('sidebar');assert(sidebar.querySelectorAll('summary').some(e=>e.textContent.startsWith('Motif context evidence')));
assert(sidebar.querySelectorAll('a').some(e=>e.href.includes('view=Protein+dossier')||e.href.includes('view=Protein+dossier'.replace('+','%20'))));
ctx.setNode('PINCH-like');assert.equal(ctx.window.atlasSelectedCandidate().family,'PINCH-like');assert(elements.get('sidebar').querySelectorAll('h3').some(e=>e.textContent.startsWith('Explore candidate profiles')));
const direct=ctx.window.atlasConnectedPath('ILK',ctx.activeEdges,'1');assert.deepEqual([...direct.nodes].sort(),['ILK','PINCH_like']);
const two=ctx.window.atlasConnectedPath('ILK',ctx.activeEdges,'2');assert.deepEqual([...two.nodes].sort(),['ILK','Nck','PINCH_like']);
const shortest=ctx.window.atlasConnectedPath('ILK',ctx.activeEdges,'2','Src');assert.deepEqual([...shortest.path],['ILK','PINCH_like','Nck','Src']);assert.equal(shortest.edges.size,3);
assert(ctx.window.atlasConnectedPath('ILK',ctx.activeEdges,'2','missing').unreachable);
const other=__OTHER__;assert(ctx.window.atlasSelectCandidate(other));assert.notEqual(ctx.current.family,'ILK');
assert.equal(ctx.window.atlasSelectedCandidate().sequence_id,other);
let message=null;ctx.window.parent={postMessage(value){message=value}};vm.runInContext(__BRIDGE__,ctx);ctx.window.atlasSelectCandidate('Sman__Smp_079760');elements.get('sidebar').children[0].onclick();assert.equal(message.candidate,'Sman__Smp_079760');assert.equal(message.node,'ILK');assert(message.orthogroup);assert.equal(message.highlighted_path.root,'ILK');assert(message.profile.candidate.sequence_id===message.candidate);assert(message.candidates.length>0);
console.log('PASS JavaScript selection API, connected neighborhoods, shortest paths, candidate switching and simulation context');
'''
        families=[{'id':family} for family in sorted(candidates.family.unique())]
        other=candidates.loc[candidates.family.eq('integrin beta'),'sequence_id'].iloc[0]
        stub=stub.replace('__FAMILIES__',json.dumps(families)).replace('__SCRIPT__',json.dumps(script)).replace('__OTHER__',json.dumps(other)).replace('__BRIDGE__',json.dumps(re.search(r'<script>(.*?)</script>',_MAP_BRIDGE,re.S).group(1)))
        check=subprocess.run([node,'-'],input=stub,text=True,capture_output=True)
        assert check.returncode==0,check.stderr
        print(check.stdout.strip(),flush=True)
    print(f'PASS {len(candidates)} exact candidate profiles, domain/motif/orthologue joins and idempotent offline embedding',flush=True)
    if '--browser' in sys.argv:
        import tempfile
        from pathlib import Path
        from linked_explorer import linked_explorer_html
        from simulator import simulator_html,SIMULATOR_FILE
        with tempfile.TemporaryDirectory(prefix='atlas-node-browser-') as folder:
            linked=Path(folder)/'linked.html'
            linked.write_text(linked_explorer_html(html,simulator_html(ROOT/SIMULATOR_FILE,candidates)),encoding='utf-8')
            result=subprocess.run([node,str(ROOT/'test_node_interactivity.cjs'),'--linked',str(linked)],text=True,capture_output=True,encoding='utf-8')
            assert result.returncode==0,result.stdout+'\n'+result.stderr
            print(result.stdout.strip(),flush=True)
    if '--app' in sys.argv:
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=300).run()
        assert not app.exception,[e.message for e in app.exception]
        app.sidebar.radio[0].set_value('Interactive hypothesis').run()
        next(widget for widget in app.selectbox if widget.label=='Locate a candidate on the map').set_value(target).run()
        assert not app.exception,[e.message for e in app.exception]
        app.query_params['view']='Protein dossier';app.query_params['protein']=target;app.run()
        assert app.sidebar.radio[0].value=='Protein dossier'
        assert next(widget for widget in app.selectbox if widget.label=='Protein').value==target
        assert not app.exception,[e.message for e in app.exception]
        app.query_params['view']='Introduction';app.run()
        assert next(widget for widget in app.selectbox if widget.label=='Locate a candidate on the map').value==target
        app.sidebar.radio[0].set_value('Components').run()
        for section in ['Summary statistics','Summary graphs','Candidate catalogue','Family assignment audit','Comparative lab','Candidate prioritization']:
            next(widget for widget in app.selectbox if widget.label=='Component section').set_value(section).run()
            assert not app.exception,[(section,e.message) for e in app.exception]
        app.sidebar.radio[0].set_value('Interactions').run()
        for section in ['Interactive network','Centrality & matrices','Topological clustering','Evidence & downloads']:
            next(widget for widget in app.selectbox if widget.label=='Network analysis section').set_value(section).run()
            assert not app.exception,[(section,e.message) for e in app.exception]
        print('PASS map/dossier deep links, all component sections and all consensus-network sections',flush=True)
if __name__=='__main__':main()
