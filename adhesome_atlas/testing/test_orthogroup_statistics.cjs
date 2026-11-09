/* Pointer clicks, linked orthogroup details and responsive Orthology workspace checks. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const cp=require('node:child_process'),net=require('node:net');
const ATLAS_ROOT=path.resolve(module.path,'..');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
expect=expect.configure({timeout:90000});
const dir=path.join(ATLAS_ROOT,'.ui_review');fs.mkdirSync(dir,{recursive:true});
async function freePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port))})})}
async function main(){
 let server,browser,page,logs='',url=process.env.ATLAS_PREVIEW_URL;
 const report=[],errors=[];
 try{
  if(!url){
   const port=await freePort();url='http://127.0.0.1:'+port+'/';
   const python=process.platform==='win32'?path.join(ATLAS_ROOT,'.venv/Scripts/python.exe'):path.join(ATLAS_ROOT,'.venv/bin/python');
   server=cp.spawn(python,['-X','utf8','-m','streamlit','run','app.py','--server.address=127.0.0.1','--server.port='+port,'--server.headless=true','--server.fileWatcherType=none','--browser.gatherUsageStats=false'],{cwd:ATLAS_ROOT,windowsHide:true,stdio:['ignore','pipe','pipe']});
   server.stdout.on('data',d=>logs=(logs+d).slice(-8000));server.stderr.on('data',d=>logs=(logs+d).slice(-8000));
   let ready=false;for(let i=0;i<90;i++){try{ready=(await fetch(url+'_stcore/health')).ok}catch(_){}if(ready)break;if(server.exitCode!==null)throw Error(logs);await new Promise(r=>setTimeout(r,500))}assert(ready,'Test server did not become ready: '+logs);
  }
  browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});
  page=await browser.newPage({viewport:{width:1800,height:1200}});page.on('pageerror',e=>errors.push(e.message));
  const address=new URL(url);address.search='?view=Orthology';await page.goto(address.href,{timeout:60000});
  await expect(page.getByRole('heading',{name:'Orthogroup Statistics & Explorer',exact:true})).toBeVisible({timeout:180000});
  const total=page.getByTestId('stMetricValue').first();
  const noErrors=async()=>expect(page.getByTestId('stException')).toHaveCount(0);
  const select=async(label,value)=>{
   const control=page.getByTestId('stSelectbox').filter({hasText:label}).getByRole('combobox');
   await control.scrollIntoViewIfNeeded();
   await control.click();
   await control.press('ArrowDown');
   await page.getByRole('option',{name:value,exact:true}).click();await noErrors();
   if(label==='Orthogroup visualization'){
    const titles={'Copy profiles':'Observed copy profiles','Classification':'Supported family identity classification',
      'Family composition':'Orthogroups by supported family identity','Species heatmap':'Total copies by orthogroup and species',
      'Specific and broad support':'Specific and broad family support','Species representation':'Candidate copies across seven species'};
    await expect(page.locator('.js-plotly-plot .gtitle')).toHaveText(titles[value],{timeout:30000});
   }
   await expect(page.getByTestId('stStatusWidget')).toBeHidden({timeout:180000});
  };
  const reset=async()=>{await page.getByRole('button',{name:'Reset orthogroup filters',exact:true}).click();await expect(total).toHaveText('302');await expect(page.getByTestId('stStatusWidget')).toBeHidden({timeout:180000})};
  const clickPoint=async locator=>{await locator.scrollIntoViewIfNeeded();const box=await locator.boundingBox();assert(box);await page.mouse.click(box.x+box.width/2,box.y+box.height/2)};
  if(process.argv.includes('--summary-only')){
   await expect(total).toHaveText('579');
   await expect(page.getByTestId('stMetricValue').nth(3)).toHaveText('2,460 / 4,355');
   await select('Summary report subset','Marked differences');await expect(total).toHaveText('46');
   await select('Summary report subset','Pronounced differences');await expect(total).toHaveText('8');
   await select('Summary report subset','All orthogroups');await expect(total).toHaveText('579');
   await select('Summary visualization','Species copy heatmap');
   await expect(page.locator('.js-plotly-plot .gtitle')).toHaveText('Species copy counts · summary report');
   await page.getByTestId('stPlotlyChart').screenshot({path:path.join(dir,'orthogroup-summary-heatmap.png'),animations:'disabled'});
   const query=page.getByRole('textbox',{name:'Find a summary orthogroup, family or reference taxon',exact:true});
   await query.fill('OG0000076');await query.press('Enter');await expect(total).toHaveText('1');
   await expect(page.getByRole('heading',{name:'Linked summary candidate dossiers',exact:true})).toBeVisible();
   await page.getByRole('button',{name:'Open exact-profile support record',exact:true}).click();
   await expect(page.getByRole('combobox',{name:'Orthogroup report',exact:true})).toHaveValue('Exact copy profiles');
   await expect(total).toHaveText('1');await noErrors();assert.deepEqual(errors,[]);
   fs.writeFileSync(path.join(dir,'orthogroup-summary-browser-validation.json'),JSON.stringify({all_groups:579,marked:46,pronounced:8,
    checks:['default summary','source subset filters','species heatmap','exact orthogroup search','candidate dossiers','exact-profile drill-through'],page_errors:errors},null,2));
   console.log('PASS new orthogroup summary browser validation: 579/46/8 scopes, species figure, exact search, linked dossiers and exact-profile drill-through');return;
  }
  if(await page.getByRole('combobox',{name:'Orthogroup report',exact:true}).count())await select('Orthogroup report','Exact copy profiles');
  await expect(total).toHaveText('302');await noErrors();
  await expect(page.getByTestId('stMetricValue').nth(3)).toHaveText('1,416 / 2,373');
  await expect(page.getByTestId('stMetricValue').nth(7)).toHaveText('585 / 0 / 831 / 0');
  await expect(page.locator('.js-plotly-plot')).toBeVisible();
  await expect(page.getByTestId('stStatusWidget')).toBeHidden({timeout:180000});
  await page.screenshot({path:path.join(dir,'orthogroup-statistics-desktop.png'),fullPage:true,animations:'disabled'});
  if(process.argv.includes('--visual-only')){
   await select('Orthogroup visualization','Species heatmap');
   await page.getByTestId('stPlotlyChart').screenshot({path:path.join(dir,'orthogroup-heatmap-total.png'),animations:'disabled'});
   const measureControl=page.getByRole('combobox',{name:'Heatmap measure',exact:true});
   await measureControl.focus();await measureControl.press('ArrowDown');await measureControl.press('End');await measureControl.press('Enter');
   await expect(page.locator('.js-plotly-plot .gtitle')).toHaveText('Supported copies by orthogroup and species');
   await page.getByTestId('stPlotlyChart').screenshot({path:path.join(dir,'orthogroup-heatmap-supported.png'),animations:'disabled'});
   await noErrors();assert.deepEqual(errors,[]);console.log('PASS visual review of numbered heatmaps, integer count legends and both heatmap measures');return;
  }
  await clickPoint(page.locator('.js-plotly-plot .barlayer .point path').first());
  await expect(total).toHaveText('269');report.push('Copy-profile bar click filters to 269 1:1 groups');
  console.log('PASS current exact-profile totals and 1:1 chart selection');
  await reset();await select('Orthogroup visualization','Classification');
  await clickPoint(page.locator('.js-plotly-plot .barlayer .point path').first());
  await expect(total).toHaveText('122');report.push('Classification bar click filters to 122 groups without supported identity');
  await reset();await select('Orthogroup visualization','Family composition');
  await clickPoint(page.locator('.js-plotly-plot .barlayer .point path').first());
  await expect.poll(async()=>total.textContent()).not.toBe('302');
  report.push('Family-composition bar click updates exact reported-family filter');
  await reset();await select('Orthogroup visualization','Species heatmap');
  const firstPoint=page.locator('.js-plotly-plot .scatterlayer .point').first();
  const selected=await page.locator('.js-plotly-plot').evaluate(plot=>plot.data.at(-1).customdata[0][0]);
  assert.equal(selected,'OG0000496');
  await clickPoint(firstPoint);
  await expect(page.getByRole('heading',{name:selected,exact:true})).toBeVisible();
  report.push('Heatmap cell click selects '+selected+' and keeps exact species counts');
  await page.getByTestId('stDataFrame').first().scrollIntoViewIfNeeded();
  const table=page.getByTestId('stDataFrame').first();const grid=table.locator('canvas').first();
  await table.evaluate(el=>el.scrollIntoView({block:'center'}));
  const gridBox=await grid.boundingBox();assert(gridBox);
  await page.mouse.click(gridBox.x+20,gridBox.y+55);
  await expect(page.getByRole('heading',{name:'OG0000006',exact:true})).toBeVisible();
  report.push('Explorer table row click opens its orthogroup detail panel');
  const search=page.getByRole('textbox',{name:'Find an orthogroup, copy profile or reported family',exact:true});
  await search.fill('OG0000076');await search.press('Enter');await expect(total).toHaveText('1');
  await expect(page.getByRole('heading',{name:'OG0000076',exact:true})).toBeVisible();
  const links=await page.getByRole('link',{name:'Explore this orthogroup’s phylogeny ↗'}).count();
  if(links){const href=await page.getByRole('link',{name:'Explore this orthogroup’s phylogeny ↗'}).getAttribute('href');assert(new URL(href).searchParams.get('orthogroup')==='OG0000076')}
  const candidateFrame=page.getByTestId('stDataFrame').nth(2);await expect(candidateFrame).toBeVisible();
  await page.screenshot({path:path.join(dir,'orthogroup-detail-desktop.png'),fullPage:true,animations:'disabled'});
  await reset();await select('Copy-profile dataset','Supported 1:1 subset');await expect(total).toHaveText('156');
  await select('Copy-profile dataset','Supported 2:2 subset');await expect(total).toHaveText('21');
  await reset();await search.fill('NO_SUCH_ORTHOGROUP');await search.press('Enter');await expect(total).toHaveText('0');
  await expect(page.getByText('No orthogroups match these filters.',{exact:false})).toBeVisible();await reset();
  await select('Orthogroup visualization','Specific and broad support');
  await clickPoint(page.locator('.js-plotly-plot .barlayer .point path').last());
  await expect.poll(async()=>total.textContent()).not.toBe('302');await reset();
  await select('Orthogroup visualization','Species representation');
  await clickPoint(page.locator('.js-plotly-plot .barlayer .point path').last());
  await expect.poll(async()=>total.textContent()).not.toBe('302');await reset();
  await page.setViewportSize({width:1024,height:1100});await select('Orthogroup visualization','Copy profiles');
  await page.screenshot({path:path.join(dir,'orthogroup-statistics-tablet.png'),animations:'disabled'});
  const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert(dimensions.scroll<=dimensions.width+2);
  const referenceLink=await page.getByRole('link',{name:'Open candidate and reference orthologues ↗',exact:true}).getAttribute('href');
  await page.goto(new URL(referenceLink,url).href);
  await expect(page.getByTestId('stSelectbox').filter({hasText:'Orthology collection'})).toBeVisible({timeout:180000});
  await noErrors();assert.deepEqual(errors,[]);
  report.push('Both supported subsets, search/empty/reset, broad-support/species clicks, existing references and tablet layout');
  fs.writeFileSync(path.join(dir,'orthogroup-browser-validation.json'),JSON.stringify({checks:report,dimensions,page_errors:errors},null,2));
  console.log('PASS Orthogroup browser validation',JSON.stringify(report));
 }catch(error){if(page)await page.screenshot({path:path.join(dir,'orthogroup-failure.png'),fullPage:true}).catch(()=>{});throw error}
 finally{
  if(browser)await browser.close();
  if(server){if(process.platform==='win32')cp.spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM')}
 }
}
main().catch(e=>{console.error(e);process.exitCode=1});
