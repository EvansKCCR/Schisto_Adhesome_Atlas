/* Real browser validation of research navigation, controls and responsive cards. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const cp=require('node:child_process'),net=require('node:net');
const ATLAS_ROOT=path.resolve(module.path,'..');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
async function freePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port))})})}
async function main(){
 const dir=path.join(ATLAS_ROOT,'.ui_review');fs.mkdirSync(dir,{recursive:true});
 let browser,server,base=process.env.ATLAS_PREVIEW_URL,logs='';
 try{
  if(!base){
   const port=await freePort();base='http://127.0.0.1:'+port+'/';
   const python=process.platform==='win32'?path.join(ATLAS_ROOT,'.venv/Scripts/python.exe'):path.join(ATLAS_ROOT,'.venv/bin/python');
   server=cp.spawn(python,['-X','utf8','-m','streamlit','run','app.py','--server.address=127.0.0.1','--server.port='+port,'--server.headless=true','--server.fileWatcherType=none','--browser.gatherUsageStats=false'],{cwd:ATLAS_ROOT,windowsHide:true,stdio:['ignore','pipe','pipe']});
   server.stdout.on('data',d=>logs=(logs+d).slice(-8000));server.stderr.on('data',d=>logs=(logs+d).slice(-8000));
   let ready=false;for(let i=0;i<90;i++){try{ready=(await fetch(base+'_stcore/health')).ok}catch(_){}if(ready)break;if(server.exitCode!==null)throw Error(logs);await new Promise(r=>setTimeout(r,500))}assert(ready,'Test server did not become ready: '+logs);
  }
  browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});
  const page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base,{timeout:60000});
  await expect(page.locator('.research-grid')).toBeVisible({timeout:240000});
  await expect(page.locator('[data-testid="stStatusWidget"]')).toBeHidden({timeout:240000});
  assert.equal(await page.locator('.research-card').count(),3);
  await expect(page.locator('.research-intro')).toContainText('three categories');
  await expect(page.getByText('Library-based prioritization context.',{exact:true})).toBeVisible();
  assert.equal(await page.locator('.research-difference').count(),0);
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await page.locator('.research-card').first().locator('summary').click();
  await expect(page.locator('.research-evidence').first()).toContainText('tetraspanin-family candidates for antigen screening');
  assert.equal(await page.locator('.research-unavailable').count(),0);
  const dimensions=[];
  for(const [name,width,height] of [['desktop',1920,1080],['tablet',1024,1366],['mobile',600,1000]]){
   await page.setViewportSize({width,height});
   await page.locator('.research-intro').scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(dir,'research-'+name+'.png'),animations:'disabled'});
   const result=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,cards:[...document.querySelectorAll('.research-card')].map(e=>({width:e.getBoundingClientRect().width,scroll:e.scrollWidth}))}));
   assert(result.scroll<=width+2,'page must not overflow at '+name);
   assert(result.cards.every(c=>c.scroll<=c.width+2&&c.width>230),'readable cards at '+name);dimensions.push({name,...result});
  }
  await page.setViewportSize({width:1920,height:1080});
  await page.getByRole('tab',{name:'Target-selection framework',exact:true}).click();
  await expect(page.locator('.research-matrix tbody tr')).toHaveCount(6);
  await page.getByText('Vaccine / antibody candidates',{exact:true}).click();
  await expect(page.locator('.research-matrix thead th')).toHaveCount(2,{timeout:120000});
  await expect(page.locator('.research-matrix')).not.toContainText('Small-molecule drug candidate');
  await page.getByRole('tab',{name:'Experimental roadmap',exact:true}).click();
  await expect(page.locator('.research-step')).toHaveCount(14);
  await expect(page.locator('.research-step').last()).toContainText('Surface metalloprotease activity and channel electrophysiology');
  assert.equal(await page.locator('.research-step').filter({hasText:'Sm-p80'}).count(),1);
  await expect(page.locator('.research-roadmap')).toContainText('Smp_170280');
  await page.getByRole('tab',{name:'Featured priorities',exact:true}).click();
  await page.getByText('Additional Adhesome Targets for Functional Investigation',{exact:true}).click();
  await expect(page.locator('.research-additional')).toHaveCount(21);
  await expect(page.getByRole('link',{name:'Smp_020540.2',exact:true}).first()).toHaveAttribute('href',/protein=Sman__Smp_020540$/);
  const additionalCard=name=>page.locator('.research-additional').filter({has:page.getByRole('heading',{name,exact:true})});
  for(const [name,dois] of [
   ['PINCH-like adaptors',['10.1371/journal.ppat.1006147']],
   ['Parvin-like actin adaptors',['10.1242/jcs.155879']],
   ['Rho GTPase-like proteins',['10.1371/journal.pone.0006998']],
   ['KCNH-like potassium channels',[]],
   ['MAPK-like kinases',['10.1371/journal.pntd.0002924']],
   ['Fatty-acid-binding proteins',['10.1073/pnas.93.1.269','10.3390/vaccines13030316']],
  ]){
   const card=additionalCard(name);
   await expect(card).toBeVisible();
   await expect(card).not.toContainText('Principal validation challenge');
   await expect(card).not.toContainText('https://doi.org/');
   for(const doi of dois)await expect(card.locator(`a[href="https://doi.org/${doi}"]`)).toHaveCount(1);
  }
  await expect(additionalCard('FAK')).toContainText('Principal validation challenge');
  await page.getByText(/^Research references(?: & count mismatches)?$/).click();
  await expect(page.getByRole('link',{name:/R10 · de Oliveira et al/}).last()).toBeVisible();
  // Follow the actual in-page links, exercising the application router and widgets.
  const kindlin=await page.locator('.research-additional a.research-family').filter({hasText:'kindlin'}).getAttribute('href');
  const orthogroup=await page.getByRole('link',{name:'OG0006637',exact:true}).first().getAttribute('href');
  await page.getByRole('link',{name:'Smp_089700',exact:true}).first().click();
  await expect(page.getByRole('heading',{name:'Protein dossier',exact:true})).toBeVisible({timeout:240000});
  await expect(page.getByRole('combobox',{name:'Protein',exact:true})).toHaveValue(/Sman__Smp_089700/);
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await page.goto(new URL(kindlin,base).href);
  await expect(page.getByRole('heading',{name:'Components',exact:true})).toBeVisible({timeout:240000});
  await expect(page.getByRole('combobox',{name:'Component section',exact:true})).toHaveValue('Candidate catalogue');
  await expect(page.getByTestId('stSidebar').getByText('kindlin',{exact:true})).toBeVisible();
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await page.goto(new URL(orthogroup,base).href);
  await expect(page.getByRole('heading',{name:'Orthology',exact:true})).toBeVisible({timeout:240000});
  await expect(page.getByRole('combobox',{name:/^Inspect (summary )?orthogroup$/})).toHaveValue('OG0006637');
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await page.getByText('Components',{exact:true}).first().click();
  await expect(page.getByRole('heading',{name:'Components',exact:true})).toBeVisible();
  assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(dir,'research-layout-review.json'),JSON.stringify(dimensions,null,2));
  console.log('PASS 3 responsive featured cards, library context, 21 additional families, 6 qualitative criteria, 14 roadmap steps, references and protein/family/orthogroup navigation');
 }finally{
  if(browser)await browser.close();
  if(server){if(process.platform==='win32')cp.spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM')}
 }
}
main().catch(error=>{console.error(error);process.exitCode=1});
