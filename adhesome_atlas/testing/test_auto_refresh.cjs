/* Live primary-file polling, unassigned status and refreshed network/profile checks. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const cp=require('node:child_process'),net=require('node:net');
const ATLAS_ROOT=path.resolve(module.path,'..');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
async function freePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port))})})}
async function main(){
 let browser,server,base=process.env.ATLAS_PREVIEW_URL,logs='';
 const probe=path.join(ATLAS_ROOT,'resource_library',`atlas_refresh_probe_${process.pid}.txt`),report=[];
 try{
  if(!base){
   const port=await freePort();base='http://127.0.0.1:'+port+'/';
   const python=process.platform==='win32'?path.join(ATLAS_ROOT,'.venv/Scripts/python.exe'):path.join(ATLAS_ROOT,'.venv/bin/python');
   server=cp.spawn(python,['-X','utf8','-m','streamlit','run','app.py','--server.address=127.0.0.1','--server.port='+port,'--server.headless=true','--server.fileWatcherType=none','--browser.gatherUsageStats=false'],{cwd:ATLAS_ROOT,windowsHide:true,stdio:['ignore','pipe','pipe']});
   server.stdout.on('data',d=>logs=(logs+d).slice(-8000));server.stderr.on('data',d=>logs=(logs+d).slice(-8000));
   let ready=false;for(let i=0;i<90;i++){try{ready=(await fetch(base+'_stcore/health')).ok}catch(_){}if(ready)break;if(server.exitCode!==null)throw Error(logs);await new Promise(r=>setTimeout(r,500))}assert(ready,'Server did not become ready: '+logs);
  }
  browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});
  const page=await browser.newPage({viewport:{width:1920,height:1200}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{timeout:60000});
  await expect(page.locator('.research-grid')).toBeVisible({timeout:240000});
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  const provenance=JSON.parse(fs.readFileSync(path.join(ATLAS_ROOT,'.atlas_cache/library_refresh.json'),'utf8'));
  await expect(page.locator('.atlas-hero-stat strong').first()).toHaveText(provenance.assignment_records.toLocaleString('en-US'));
  await expect(page.locator('[data-testid="stStatusWidget"]')).toBeHidden({timeout:240000});
  const outer=page.frameLocator('iframe').first(),map=outer.frameLocator('#mapFrame');
  await map.locator('#atlas-profile-search').fill('Sman__Smp_170280');
  await map.getByRole('button',{name:'Locate protein',exact:true}).click();
  const currentCandidate=await map.locator('#network').evaluate(()=>DATA.candidates.find(row=>row.id==='Sman__Smp_170280'));
  assert(currentCandidate);
  await expect(outer.locator('#profileFamily')).toHaveText(currentCandidate.f,{timeout:60000});
  await expect(outer.locator('#candidateProfile')).toContainText('Sman__Smp_170280');
  const mapData=await map.locator('#network').evaluate(()=>({families:DATA.families.length,candidates:DATA.candidates.length,counts:DATA.meta.grade_counts,edges:DATA.edges.length}));
  assert.equal(mapData.candidates,provenance.assignment_records);assert.deepEqual(mapData.counts,provenance.grade_counts);
  report.push({family_map:mapData});
  const status=page.locator('#atlas-source-status');
  await expect(status).toHaveAttribute('data-auto-refresh','true');
  await page.getByText('Automatically update inventory',{exact:true}).click();
  await expect(status).toHaveAttribute('data-auto-refresh','false',{timeout:120000});
  await expect(status).toContainText('paused');
  await page.getByText('Automatically update inventory',{exact:true}).click();
  await expect(status).toHaveAttribute('data-auto-refresh','true',{timeout:120000});
  // A temporary library entry exercises the real timer, without altering scientific inputs.
  const before=await status.getAttribute('data-source-version');
  assert(!fs.existsSync(probe));fs.writeFileSync(probe,'Temporary automatic-refresh browser test.\n');
  const start=Date.now();
  await expect.poll(async()=>page.locator('#atlas-source-status').getAttribute('data-source-version'),{timeout:150000,intervals:[1000]}).not.toBe(before);
  await expect(page.locator('.research-grid')).toBeVisible({timeout:180000});
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  report.push({automatic_refresh_seconds:(Date.now()-start)/1000});
  await page.getByText('Interactions',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Orthogroup consensus adhesome network'})).toBeVisible({timeout:180000});
  const consensus=page.frameLocator('iframe').first();
  await expect(consensus.locator('#layout')).toBeVisible({timeout:180000});
  const current=await consensus.locator('#network').evaluate(()=>({totals:atlasConsensus.totals,nodes:data.nodes.map(n=>({id:n.id,grades:n.grades,member_ids:n.member_ids}))}));
  const target=current.nodes.find(n=>n.member_ids.includes('Sman__Smp_170280'));assert(target&&target.grades[currentCandidate.g]>0);
  await consensus.locator('#search').fill('Smp_170280');await consensus.locator('#search').press('Enter');
  await expect(consensus.locator('#candidateProfile')).toContainText('Sman__Smp_170280');
  await expect(consensus.locator('#nodeProfile>.tags .grade.'+currentCandidate.g)).toBeVisible();
  for(const mode of ['cellular','functional','community','free']){await consensus.locator('#layout').selectOption(mode);await expect(consensus.locator('#candidateProfile')).toContainText('Sman__Smp_170280')}
  assert.deepEqual(errors,[]);
  report.push({consensus:current.totals,candidate_target:target.id,candidate_grade:currentCandidate.g});
  const dir=path.join(ATLAS_ROOT,'.ui_review');fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'automatic-refresh-browser.json'),JSON.stringify(report,null,2));
  await page.screenshot({path:path.join(dir,'automatic-refresh-consensus.png'),animations:'disabled'});
  console.log('PASS current workbook record counts/grades, auto-update default/pause/resume, real timer-driven refresh, both network profiles, four layouts and no page errors',JSON.stringify(report));
 }finally{
  if(fs.existsSync(probe))fs.unlinkSync(probe);
  if(browser)await browser.close();
  if(server){if(process.platform==='win32')cp.spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM')}
 }
}
main().catch(error=>{console.error(error);process.exitCode=1});
