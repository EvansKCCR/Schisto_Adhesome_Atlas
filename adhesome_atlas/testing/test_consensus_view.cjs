/* Browser checks for the complete orthogroup network; --before captures the old viewer. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ATLAS_ROOT=path.resolve(module.path,'..');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
async function main(){
 const dir=path.join(ATLAS_ROOT,'.ui_review');fs.mkdirSync(dir,{recursive:true});
 const browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1200}});
  if(!process.argv.includes('--offline')){
  await page.goto(process.env.ATLAS_PREVIEW_URL||'http://127.0.0.1:8511/',{timeout:60000});
  await expect(page.getByText('Interactions',{exact:true})).toBeVisible({timeout:240000});
  await page.getByText('Interactions',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Orthogroup consensus adhesome network'})).toBeVisible({timeout:240000});
  const frame=page.frameLocator('iframe').first();
  await expect(frame.locator('#network')).toBeVisible({timeout:240000});
  await expect(page.locator('[data-testid="stStatusWidget"]')).toBeHidden({timeout:240000});
  await page.locator('iframe').first().scrollIntoViewIfNeeded();
  if(process.argv.includes('--before')){
   await page.screenshot({path:path.join(dir,'consensus-before.png'),animations:'disabled'});
   await frame.locator('#network').screenshot({path:path.join(dir,'consensus-before-network.png')});
   console.log('Captured original consensus network');return;
  }
  await expect(frame.locator('#layout')).toBeVisible({timeout:240000});
  await expect(frame.locator('.node').first()).toBeVisible();
  await page.screenshot({path:path.join(dir,'consensus-after.png'),animations:'disabled'});
  }
  // The exported file is tested independently, with every external request blocked.
  const fixture=path.join(dir,'consensus-after.html'),html=fs.readFileSync(fixture,'utf8');
  const model=JSON.parse(html.match(/const data=(.*);\r?\n/)[1]);
  const offline=await browser.newPage({viewport:{width:1600,height:1100}}),requests=[],errors=[];
  offline.on('pageerror',e=>errors.push(e.message));
  await offline.route(/^https?:/,route=>{requests.push(route.request().url());route.abort()});
  await offline.goto(require('node:url').pathToFileURL(fixture).href);
  await expect(offline.locator('.node')).toHaveCount(model.nodes.length);
  const neighbor=new Map(model.nodes.map(n=>[n.id,new Set()]));
  for(const edge of model.edges){neighbor.get(edge.source).add(edge.target);neighbor.get(edge.target).add(edge.source)}
  const report=[];
  // Actual pointer clicks, including all upstream/intermediate/terminal/unconnected orthogroups.
  for(const n of model.nodes){
   await offline.locator(`.node[data-id="${n.id}"] circle`).click();
   const actual=await offline.evaluate(()=>({state:atlasConsensus.getState(),heading:document.querySelector('#nodeProfile h2').textContent,ids:[...document.querySelectorAll('#candidateList [data-candidate]')].map(e=>e.dataset.candidate),grades:[...document.querySelectorAll('#nodeProfile>.tags .grade')].map(e=>e.textContent),active:document.querySelectorAll('.edge.active').length,muted:document.querySelectorAll('.node.muted').length}));
   assert.equal(actual.state.selected,n.id);assert.equal(actual.heading,n.id);
   assert.deepEqual(actual.ids,n.member_ids);assert.equal(actual.active,n.degree);
   assert.deepEqual(actual.grades,['A','B','C','D'].map(g=>`${g} = ${n.grades[g]}`));
   assert.equal(actual.muted,model.nodes.length-1-n.degree);
  }
  console.log('PASS actual independent clicks and complete candidate/neighbor mapping for all '+model.nodes.length+' orthogroups');
  for(const region of model.regions){const n=model.nodes.find(n=>n.compartment===region.id);if(!n)continue;await offline.locator(`.node[data-id="${n.id}"] circle`).click();await expect(offline.locator('#nodeProfile')).toContainText(region.label);report.push({region:region.id,selected:n.id,candidates:n.member_count,grades:n.grades})}
  const chosen=model.nodes.find(n=>n.member_count>1&&n.degree>0),candidate=chosen.member_ids[1];
  await offline.locator(`.node[data-id="${chosen.id}"] circle`).click();
  await offline.locator(`[data-candidate="${candidate}"]`).click();
  await expect(offline.locator('#candidateProfile')).toContainText(candidate);
  for(const mode of ['cellular','functional','community','free']){
   await offline.locator('#layout').selectOption(mode);
   const state=await offline.evaluate(()=>atlasConsensus.getState());
   assert.equal(state.mode,mode);assert.equal(state.selected,chosen.id);assert.equal(state.candidate,candidate);assert.equal(state.visible.length,model.nodes.length);
   await expect(offline.locator('#candidateProfile')).toContainText(candidate);
   await offline.screenshot({path:path.join(dir,'consensus-after-'+mode+'.png'),animations:'disabled'});
  }
  await offline.locator('#layout').selectOption('cellular');
  await offline.locator('#hops').selectOption('2');
  const expected=new Set([chosen.id,...neighbor.get(chosen.id)]);for(const id of neighbor.get(chosen.id))for(const other of neighbor.get(id))expected.add(other);
  assert.deepEqual((await offline.evaluate(()=>atlasConsensus.getState().neighborhood)).sort(),[...expected].sort());
  await offline.locator('#focusModule').click();
  assert.deepEqual((await offline.evaluate(()=>atlasConsensus.getState().visible)).sort(),model.nodes.filter(n=>n.module_component===chosen.module_component).map(n=>n.id).sort());
  await offline.locator('#restore').click();await offline.locator('#hideIsolates').check();
  assert.equal((await offline.evaluate(()=>atlasConsensus.getState().visible)).length,model.nodes.filter(n=>n.degree>0).length);
  await offline.locator('#restore').click();
  const beta=model.nodes.find(n=>n.member_ids.includes('Sman__Smp_089700'));
  await offline.locator('#search').fill('Smp_089700');await offline.locator('#search').press('Enter');
  assert.equal((await offline.evaluate(()=>atlasConsensus.getState().selected)),beta.id);
  await expect(offline.locator('#candidateProfile')).toContainText('Sman__Smp_089700');
  const profileHref=await offline.locator('.dossier-link').getAttribute('href');assert(new URL(profileHref).searchParams.get('protein')==='Sman__Smp_089700');
  await offline.locator('#fontSize').fill('24');await offline.locator('#centerLabels').check();
  await expect(offline.locator('#fontValue')).toHaveText('24');
  await offline.locator('#centerLabels').uncheck();
  await offline.locator('.edge.active').first().dispatchEvent('click');
  await expect(offline.locator('#nodeProfile .edge-record').first()).toContainText('Reference interactions');
  await expect(offline.locator('#nodeProfile')).toContainText('Source candidates');
  const selectedEvidence=await offline.evaluate(()=>{
   const edge=data.edges.find(e=>e.id===document.querySelector('.edge.selected-edge').dataset.edge);
   return edge.evidence_rows.map(i=>data.evidence[i]);
  });
  const cards=await offline.locator('#nodeProfile .edge-record').allTextContents();
  for(let i=0;i<selectedEvidence.length;i++){
   assert(cards[i].includes(selectedEvidence[i].source_candidates));
   assert(cards[i].includes(selectedEvidence[i].target_candidates));
   assert(cards[i].includes(selectedEvidence[i].shared_species));
  }
  await offline.getByRole('button',{name:'← Candidate profiles',exact:true}).click();
  await expect(offline.locator('#candidateProfile')).toContainText('Sman__Smp_089700');
  const circle=offline.locator(`.node[data-id="${beta.id}"] circle`),before=await circle.locator('..').getAttribute('transform'),box=await circle.boundingBox();
  await offline.mouse.move(box.x+box.width/2,box.y+box.height/2);await offline.mouse.down();await offline.mouse.move(box.x+box.width/2+45,box.y+box.height/2+30,{steps:8});await offline.mouse.up();
  assert.notEqual(await circle.locator('..').getAttribute('transform'),before);
  await offline.locator('#reset').click();await offline.locator('#readable').click();
  const viewBefore=await offline.locator('#network').getAttribute('viewBox');await offline.locator('#zoomIn').click();assert.notEqual(await offline.locator('#network').getAttribute('viewBox'),viewBefore);
  await offline.locator('#fit').click();
  const labels=await offline.evaluate(()=>[...document.querySelectorAll('.node text')].filter(e=>getComputedStyle(e).visibility!=='hidden'&&getComputedStyle(e).display!=='none').map(e=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height}}));
  for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++){const a=labels[i],b=labels[j];assert(!(a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y),'visible labels must not collide')}
  const downloadPromise=offline.waitForEvent('download');await offline.locator('#svgExport').click();const download=await downloadPromise,svgText=fs.readFileSync(await download.path(),'utf8');assert(svgText.includes('width="3600"')&&svgText.includes(beta.id));
  assert.deepEqual(requests,[],'standalone viewer must not fetch external resources');assert.deepEqual(errors,[]);
  await offline.setViewportSize({width:1024,height:1100});await offline.locator('#fit').click();
  await offline.screenshot({path:path.join(dir,'consensus-after-tablet.png'),animations:'disabled'});
  const widths=await offline.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth}));assert(widths.scroll<=widths.viewport+2);
  await offline.locator('#resetView').click();
  const reset=await offline.evaluate(()=>atlasConsensus.getState());assert.equal(reset.selected,null);assert.equal(reset.visible.length,model.nodes.length);
  await expect(offline.locator('#nodeProfile')).toContainText('Select an orthogroup');
  fs.writeFileSync(path.join(dir,'consensus-browser-validation.json'),JSON.stringify({nodes:model.nodes.length,layouts:4,region_samples:report,all_independent_clicks:true,external_requests:requests,tablet:widths},null,2));
  console.log('PASS 4 layouts with selection/profile retention, all 6 regions, 2-step traversal, connected module focus, hide/restore, exact candidate search, label control/collision avoidance, dragging, zoom, vector export, offline rendering and desktop/tablet layout');
 }finally{await browser.close()}
}
main().catch(error=>{console.error(error);process.exitCode=1});
