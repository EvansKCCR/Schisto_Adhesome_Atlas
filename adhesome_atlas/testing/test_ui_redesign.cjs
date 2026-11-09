/* Desktop/tablet browser review against the real Streamlit application. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const cp=require('node:child_process'),net=require('node:net');
const ATLAS_ROOT=path.resolve(module.path,'..');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
async function freePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port))})})}
function contrast(a,b){const luminance=color=>{const values=color.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return values[0]*.2126+values[1]*.7152+values[2]*.0722};const l=[luminance(a),luminance(b)].sort((x,y)=>y-x);return (l[0]+.05)/(l[1]+.05)}
async function validateFunctionalDashboard(page,output){
 await page.getByRole('combobox',{name:'Component section',exact:true}).click();
 await page.getByRole('option',{name:'Supported families by functional category',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Supported families by functional category',exact:true})).toBeVisible({timeout:120000});
 for(const value of ['4,359','2,460','87','3,258'])await expect(page.getByTestId('stMetricValue').filter({hasText:value})).toBeVisible({timeout:120000});
 await expect(page.getByRole('button',{name:'Download category summary',exact:true})).toBeVisible({timeout:120000});
 await expect(page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot').first()).toBeVisible({timeout:120000});
 await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
 await page.screenshot({path:path.join(output,'functional-category-summary.png'),animations:'disabled'});
 await page.getByRole('tab',{name:'Family breakdown',exact:true}).click();
 await expect(page.getByRole('combobox',{name:'Functional categories',exact:true})).toBeVisible({timeout:30000});
 await page.getByRole('tab',{name:'Localization evidence',exact:true}).click();
 await expect(page.getByText(/Single-location DeepLoc means one recorded location label/)).toBeVisible();
 console.log('PASS functional summary metrics, family breakdown, localization evidence and retained downloads');
}
async function main(){
 const output=process.env.ATLAS_REVIEW_DIR||path.join(ATLAS_ROOT,'.ui_review');fs.mkdirSync(output,{recursive:true});
 let browser,server,base=process.env.ATLAS_PREVIEW_URL,logs='';const report=[];
 try{
  if(!base){
   const port=await freePort();base='http://127.0.0.1:'+port+'/';
   const python=process.platform==='win32'?path.join(ATLAS_ROOT,'.venv/Scripts/python.exe'):path.join(ATLAS_ROOT,'.venv/bin/python');
   server=cp.spawn(python,['-X','utf8','-m','streamlit','run',process.env.ATLAS_APP_SCRIPT||'app.py','--server.address=127.0.0.1','--server.port='+port,'--server.headless=true','--server.fileWatcherType=none','--browser.gatherUsageStats=false'],{cwd:ATLAS_ROOT,windowsHide:true,stdio:['ignore','pipe','pipe']});
   server.stdout.on('data',d=>logs=(logs+d).slice(-8000));server.stderr.on('data',d=>logs=(logs+d).slice(-8000));
   let ready=false;for(let i=0;i<90;i++){try{ready=(await fetch(base+'_stcore/health')).ok}catch(_){}if(ready)break;if(server.exitCode!==null)throw Error(logs);await new Promise(r=>setTimeout(r,500))}assert(ready,'Server did not become ready: '+logs);
  }
  browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});
  const page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+(process.argv.includes('--components-only')?'?view=Components':''),{timeout:60000});
  if(process.argv.includes('--components-only')){
   await expect(page.getByRole('heading',{name:'Components',exact:true})).toBeVisible({timeout:240000});
   await validateFunctionalDashboard(page,output);assert.deepEqual(errors,[]);return;
  }
  await expect(page.locator('.atlas-hero')).toBeVisible({timeout:240000});
  await expect(page.locator('[data-testid="stStatusWidget"]')).toBeHidden({timeout:240000});
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await expect(page.locator('.atlas-hero .eyebrow,.research-card-kicker,.research-intro .atlas-section-kicker,.atlas-sidebar-brand small')).toHaveCount(0);
  const theme=await page.evaluate(()=>{
   const hero=getComputedStyle(document.querySelector('.atlas-hero')),button=getComputedStyle(document.querySelector('.atlas-hero-meta a'));
   const labels=[...document.querySelectorAll('[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label')];
   const icons=labels.map(label=>{const icon=getComputedStyle(label,'::before');return {background:icon.backgroundColor,image:icon.backgroundImage,radius:icon.borderRadius}});
   return {labelMarkup:labels[0]?.innerHTML,page:getComputedStyle(document.querySelector('[data-testid="stAppViewContainer"]')).backgroundColor,
    hero:hero.backgroundColor,heroImage:hero.backgroundImage,line:hero.borderBottomColor,
    text:getComputedStyle(document.querySelector('.atlas-hero p')).color,
    button:{background:button.backgroundColor,color:button.color},icons};
  });
  fs.writeFileSync(path.join(output,'synergy-theme-initial.json'),JSON.stringify(theme,null,2));
  await page.screenshot({path:path.join(output,'synergy-theme-initial.png'),animations:'disabled'});
  assert.equal(theme.page,'rgb(255, 255, 255)');assert.equal(theme.hero,'rgb(17, 19, 56)');
  assert.match(theme.heroImage,/^linear-gradient/);
  assert.equal(theme.line,'rgb(189, 45, 119)');assert(contrast(theme.text,theme.hero)>=7);
  assert.equal(theme.button.background,'rgb(105, 233, 255)');
  assert(contrast(theme.button.background,theme.button.color)>=4.5);
  assert.equal(theme.icons.length,11);assert(theme.icons.every(icon=>icon.image.includes('data:image/svg+xml')&&icon.radius==='50%'));
  assert.equal(new Set(theme.icons.map(icon=>icon.image)).size,11,'Each section must have its own icon');
  for(const name of ['Introduction','Interactive hypothesis','Components','Interactions','Orthology','Phylogeny','Protein dossier','Motif explorer','Comments & feedback','Source Library','Citations']){
   await expect(page.getByTestId('stSidebar').getByText(name,{exact:true})).toBeVisible();
  }
  report.push({theme});
  await expect(page.locator('iframe')).toHaveCount(0);
  assert(new URL(await page.locator('.atlas-hero-meta a').getAttribute('href')).searchParams.get('view')==='Interactive hypothesis');
  await page.getByTestId('stSidebar').getByText('Interactive hypothesis',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Interactive integrin-adhesome hypothesis',exact:true})).toBeVisible({timeout:120000});
  const outer=page.frameLocator('iframe').first(),map=outer.frameLocator('#mapFrame');
  try {
   await Promise.race([
    map.locator('[data-family="ILK"]').waitFor({timeout:240000}),
    page.getByTestId('stException').waitFor({timeout:240000}).then(async()=>{throw Error(await page.getByTestId('stException').innerText())}),
   ]);
  } catch (error) {
   console.error('Atlas frame diagnostics', JSON.stringify({
    frames:page.frames().map(frame=>({name:frame.name(),url:frame.url().slice(0,200)})),
    errors,server:logs,
   }));
   throw error;
  }
  await map.locator('[data-family="Parvin_like"]').click();
  await expect(outer.locator('#profileFamily')).toHaveText('Parvin_like');
  await expect(outer.locator('#linkedCandidate option')).toHaveCount(14);
  await expect(outer.locator('#candidateCounts')).toHaveText('14 candidates · A = 14 · B = 0 · C = 0 · D = 0 (unassigned)');
  const drawer=map.locator('.atlas-filter-drawer');
  await map.locator('.atlas-display-options>summary').click();
  await map.locator('#atlas-path-scope').selectOption('1');
  await map.locator('.atlas-display-options>summary').click();
  const parvin=await map.locator('body').evaluate(()=>({context:window.atlasCandidateContext(),family:DATA.families.find(f=>f.id==='Parvin_like')}));
  assert.equal(parvin.family.zone,'Membrane-actin clutch');assert.equal(parvin.family.supported_n,14);
  assert(parvin.context.highlighted_path.nodes.includes('ILK')&&parvin.context.highlighted_path.nodes.includes('PINCH-like'));
  await outer.locator('#linkedCandidate').selectOption('Sman__Smp_171530');
  await expect(outer.locator('#candidateProfile')).toContainText('Membrane-actin clutch');
  await expect(outer.locator('#candidateProfile')).toContainText('specific supported');
  await page.screenshot({path:path.join(output,'parvin-linked-profiles.png'),animations:'disabled'});
  console.log('PASS Parvin node, 14 specific-supported profiles, direct ILK/PINCH links and independent localization evidence');
  await drawer.locator('summary').click();
  await map.locator('#species').selectOption('Schistosoma mansoni');
  await map.locator('#scope').selectOption('all');
  await drawer.locator('summary').click();
  await map.locator('[data-family="ILK"]').click();
  await expect(outer.locator('#profileFamily')).toHaveText('ILK');
  await expect(outer.locator('#candidateProfile')).toContainText('Sman__Smp_079760');
  await outer.locator('#candidateProfile summary').filter({hasText:'Literature and biological evidence'}).click();
  await expect(outer.locator('#candidateProfile')).toContainText('R02');
  for(const [name,width,height] of [['desktop',1920,1080],['tablet',1024,1366],['mobile',600,1000]]){
   await page.setViewportSize({width,height});
   // Streamlit's native sidebar can be collapsed without replacing navigation.
   if(name==='tablet'){
    const collapse=page.locator('[data-testid="stSidebar"] button').filter({hasText:'keyboard_double_arrow_left'});
    if(await collapse.isVisible())await collapse.click();
   }
   await page.getByRole('heading',{name:'Interactive integrin-adhesome hypothesis',exact:true}).scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(output,name+'-overview.png'),fullPage:false,animations:'disabled'});
   await page.locator('iframe').first().scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(output,name+'-workspace.png'),fullPage:false,animations:'disabled'});
   const dimensions=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,main:document.querySelector('[data-testid="stMainBlockContainer"]').getBoundingClientRect().width,hero:document.querySelector('h2').getBoundingClientRect().toJSON()}));
   assert(dimensions.document<=width+2,'no application-level horizontal overflow at '+name);
   const frame=await page.locator('iframe').first().elementHandle().then(e=>e.contentFrame());
   const panels=await frame.evaluate(()=>({workspace:document.querySelector('.workspace').getBoundingClientRect().toJSON(),visual:document.querySelector('.visuals').getBoundingClientRect().toJSON(),profile:document.querySelector('.profile-rail').getBoundingClientRect().toJSON(),scroll:document.documentElement.scrollWidth,width:innerWidth}));
   assert(panels.scroll<=panels.width+2,'no linked-workspace horizontal overflow');
   if(width>760)assert(panels.visual.width>=panels.width*.6,'network is the primary workspace');
   assert(panels.profile.width>=280,'candidate dossier remains usable');
   report.push({name,...dimensions,panels});
   console.log('PASS '+name+' white layout and linked workspace bounds');
  }
  await outer.locator('#linkedCandidate').selectOption({index:0});
  await outer.locator('#simulateSelection').click();
  await expect(outer.locator('#candidateProfile')).toBeVisible();
  await expect(outer.locator('#simulatorFrame')).toBeVisible();
  const simulation=outer.frameLocator('#simulatorFrame');
  await expect(simulation.locator('#zoneCards .zoneCard')).toHaveCount(3);
  await expect(simulation.locator('#mechanismRule')).toHaveValue('M09');
  await outer.locator('#showMap').click();
  await page.setViewportSize({width:1920,height:1080});
  const expand=page.getByRole('button',{name:/open sidebar|expand sidebar|show sidebar/i}).or(page.locator('[data-testid="stSidebarCollapsedControl"] button')).or(page.locator('button').filter({hasText:'keyboard_double_arrow_right'})).first();
  if(await expand.isVisible())await expand.click();
  fs.writeFileSync(path.join(output,'layout-review.json'),JSON.stringify(report,null,2));
  await page.getByText('Components',{exact:true}).click();await expect(page.getByRole('heading',{name:'Components',exact:true})).toBeVisible({timeout:120000});
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await page.screenshot({path:path.join(output,'desktop-components.png')});
  await validateFunctionalDashboard(page,output);
  assert.equal(await page.locator('[data-testid="stAppViewContainer"]').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(255, 255, 255)');
  await page.getByText('Interactions',{exact:true}).click();
  await expect(page.getByRole('heading',{name:'Orthogroup consensus adhesome network',exact:true})).toBeVisible({timeout:120000});
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
  await page.screenshot({path:path.join(output,'desktop-interactions.png')});
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(output,'layout-review.json'),JSON.stringify(report,null,2));
  assert.equal(await page.locator('[data-testid="stAppViewContainer"]').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(255, 255, 255)');
  await page.getByRole('radio',{name:'Interactions',exact:true}).focus();
  await page.getByRole('radio',{name:'Interactions',exact:true}).press('ArrowUp');
  await expect(page.getByRole('heading',{name:'Components',exact:true})).toBeVisible({timeout:120000});
  console.log('PASS SYNERGY-NGS theme, white workspaces, readable contrast, desktop/tablet/mobile layout, candidate selection, linked simulator, Components and Interactions; screenshots in '+output);
 }finally{
  if(browser)await browser.close();
  if(server){if(process.platform==='win32')cp.spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM')}
 }
}
main().catch(e=>{console.error(e);process.exitCode=1});
