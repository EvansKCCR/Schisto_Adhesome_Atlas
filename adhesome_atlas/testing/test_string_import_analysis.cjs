/* Real multi-file uploads; no STRING API requests or primary-library edits. */
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),net=require('node:net'),assert=require('node:assert/strict');
const ATLAS_ROOT=path.resolve(module.path,'..');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const p=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(p);({expect}=require(path.join(p,'test')))}
expect=expect.configure({timeout:30000});
async function port(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p))})})}
async function main(){
 const dir=path.join(ATLAS_ROOT,'.ui_review');fs.mkdirSync(dir,{recursive:true});
 const file=path.join(dir,'string_import_fixture.py');
 fs.writeFileSync(file,'import sys\nsys.path[:0] = ['+JSON.stringify(path.join(ATLAS_ROOT,'main'))+', '+JSON.stringify(path.join(ATLAS_ROOT,'branding'))+', '+JSON.stringify(path.join(ATLAS_ROOT,'maintenance_directories'))+', '+JSON.stringify(path.join(ATLAS_ROOT,'testing'))+']\nfrom atlas_styles import apply_style\nfrom test_string_analysis import fixture\nfrom string_workbench import string_panel\napply_style()\nstate,candidates=fixture()\nstring_panel(candidates)\n');
 let server,browser,page,log='';
 try{
  const p=await port(),url='http://127.0.0.1:'+p+'/';
  const python=path.join(ATLAS_ROOT,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
  server=cp.spawn(python,['-X','utf8','-m','streamlit','run',file,'--server.address=127.0.0.1','--server.port='+p,'--server.headless=true','--server.fileWatcherType=none','--browser.gatherUsageStats=false'],{cwd:ATLAS_ROOT,windowsHide:true,stdio:['ignore','pipe','pipe']});
  server.stdout.on('data',d=>log=(log+d).slice(-5000));server.stderr.on('data',d=>log=(log+d).slice(-5000));
  let ready=false;for(let i=0;i<90;i++){try{ready=(await fetch(url+'_stcore/health')).ok}catch(_){}if(ready)break;await new Promise(r=>setTimeout(r,500))}assert(ready,log);
  browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});
  page=await browser.newPage({viewport:{width:1600,height:1100}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);await expect(page.getByRole('combobox',{name:'STRING query species',exact:true})).toBeVisible({timeout:120000});
  const choose=async(label,option)=>{
   await expect(page.getByTestId('stStatusWidget')).toBeHidden({timeout:120000});
   const box=page.getByRole('combobox',{name:label,exact:true});
   await expect(async()=>{await expect(box).toBeVisible();await box.focus();await box.press('ArrowDown');await page.getByRole('option',{name:option,exact:true}).click({timeout:5000})}).toPass({timeout:30000});
   await expect(box).toHaveValue(option);
   await expect(page.getByTestId('stException')).toHaveCount(0);await expect(page.getByTestId('stStatusWidget')).toBeHidden({timeout:120000});
  };
  await choose('STRING query species','Schistosoma mansoni');
  const pairs=[['A','B',.2],['B','C',.8],['C','A',.7],['C','D',.9],['D','E',.6],['E','F',.85],['F','D',.75]];
  const api='stringId_A\tstringId_B\tpreferredName_A\tpreferredName_B\tscore\n'+pairs.map(([a,b,s])=>`6183.${a}\t6183.${b}\t${a}\t${b}\t${s}`).join('\n')+'\n';
  const website='node1_string_id\tnode2_string_id\tnode1\tnode2\tcombined_score\texperimental\n'+pairs.map(([a,b,s])=>`6183.${a}\t6183.${b}\t${a}\t${b}\t${s}\t0.5`).join('\n')+'\n';
  const mapping='queryItem\tstringId\n'+'ABCDEFG'.split('').map(a=>`Sman__${a}\t6183.${a}`).join('\n')+'\n';
  await page.getByTestId('stFileUploader').filter({hasText:'STRING network TSV'}).locator('input[type=file]').setInputFiles([
   {name:'api.tsv',mimeType:'text/tab-separated-values',buffer:Buffer.from(api)},
   {name:'website.tsv',mimeType:'text/tab-separated-values',buffer:Buffer.from(website)}]);
  await page.getByTestId('stFileUploader').filter({hasText:'STRING mapping TSV (optional)'}).locator('input[type=file]').setInputFiles({name:'mapping.tsv',mimeType:'text/tab-separated-values',buffer:Buffer.from(mapping)});
  await page.getByRole('button',{name:'Import TSV for topology analysis',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Saved STRING imports',exact:true})).toBeVisible();
  await expect(page.getByText('Imported api.tsv · 7 unique associations',{exact:true})).toBeVisible();
  await expect(page.getByText('Imported website.tsv · 7 unique associations',{exact:true})).toBeVisible();
  await expect(page.getByTestId('stMetricValue').first()).toHaveText('7');
  await expect(page.getByTestId('stMetricValue').nth(1)).toHaveText('7');
  await choose('Imported network section','Centrality & clusters');
  await expect(page.getByRole('button',{name:'Download imported centrality and clusters',exact:true})).toBeVisible();
  await choose('Imported network section','Topological clustering');
  await expect(page.getByRole('combobox',{name:'Clustering algorithm',exact:true})).toBeVisible();
  await choose('Clustering algorithm','MCODE');
  await page.getByText('Analyze and compare all saved imports',{exact:true}).click();
  await page.getByRole('button',{name:'Analyze all imported STRING networks',exact:true}).click();
  await expect(page.getByRole('button',{name:'Download analysis for every saved STRING import',exact:true})).toBeVisible();
  await choose('Imported STRING network','api.tsv · Schistosoma mansoni · functional');
  await choose('Imported network section','Matrices');
  await choose('Imported matrix','Confidence adjacency');
  await expect(page.locator('.js-plotly-plot .gtitle')).toHaveText('Confidence adjacency');
  await expect(page.getByRole('button',{name:'Download all five matrices and topology',exact:true})).toBeVisible();
  await expect(page.getByTestId('stException')).toHaveCount(0);assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(dir,'string-import-analysis.png'),animations:'disabled'});
  fs.writeFileSync(path.join(dir,'string-import-browser-validation.json'),JSON.stringify({valid_imports:2,schemas:['API','website'],proteins:7,pairs:7,
   checks:['multi-file import','optional mapping with isolated query','default all scores retained','centralities','MCODE controls','all-import ZIP','network switching','confidence matrix'],page_errors:errors},null,2));
  console.log('PASS actual multi-file STRING uploads, both export schemas, isolate mapping, full score coverage, centrality, clustering, all-import analysis and matrices');
 }catch(e){if(page)await page.screenshot({path:path.join(dir,'string-import-failure.png')}).catch(()=>{});throw e}
 finally{if(browser)await browser.close();if(server){if(process.platform==='win32')cp.spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true});else server.kill('SIGTERM')}}
}
main().catch(e=>{console.error(e);process.exitCode=1});
