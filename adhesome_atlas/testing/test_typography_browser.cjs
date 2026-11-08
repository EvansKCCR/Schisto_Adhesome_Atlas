/* Verify actual canvas/HTML/SVG typography while retaining raw widget values. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),cp=require('node:child_process'),net=require('node:net');
let pw,expect;try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
const root=path.resolve(module.path,'..'),out=path.join(root,'.ui_review');
async function freePort(){return new Promise((resolve,reject)=>{const s=net.createServer();s.on('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p))})})}
async function main(){
 fs.mkdirSync(out,{recursive:true});
 const script=`import streamlit as st
import pandas as pd
import plotly.express as px
from atlas_styles import apply_style
from figure_exports import plotly_chart
from design_system import network_style
apply_style()
st.header('Scientific typography')
st.markdown('<p id="proof">**Strong evidence** from Schistosoma mansoni and *S. japonicum*.</p>',unsafe_allow_html=True)
st.caption('Fasciola hepatica and S. haematobium')
species=st.selectbox('Species proof',['Schistosoma mansoni','Schistosoma japonicum'])
st.caption('Raw selection: '+species)
data=pd.DataFrame({'Species':['Schistosoma mansoni','Schistosoma japonicum'],'Evidence':['**Concordant**','Architecture'],'Count':[2,3]})
st.dataframe(data,hide_index=True,width='stretch')
plotly_chart(px.bar(data,x='Species',y='Count',color='Species',title='**Species** comparison'),width='stretch')
st.iframe(network_style()+'<body><p id="owned">**Supported** in S. mansoni</p><svg xmlns="http://www.w3.org/2000/svg" width="400" height="80"><text x="10" y="25">S. haematobium</text></svg><code id="literal">**raw** S. mansoni</code></body>',height=200)
`;
 fs.writeFileSync(path.join(out,'typography_preview.py'),script);
 let browser,server,logs='';
 try{
  const port=await freePort(),base='http://127.0.0.1:'+port+'/';
  server=cp.spawn(path.join(root,'.venv/Scripts/python.exe'),['-X','utf8','-m','streamlit','run','.ui_review/typography_preview.py','--server.address=127.0.0.1','--server.port='+port,'--server.headless=true','--server.fileWatcherType=none','--browser.gatherUsageStats=false'],{cwd:root,windowsHide:true,stdio:['ignore','pipe','pipe']});
  server.stdout.on('data',d=>logs=(logs+d).slice(-5000));server.stderr.on('data',d=>logs=(logs+d).slice(-5000));
  let ready=false;for(let i=0;i<90;i++){try{ready=(await fetch(base+'_stcore/health')).ok}catch(_){}if(ready)break;await new Promise(r=>setTimeout(r,400))}assert(ready,logs);
  browser=await pw.chromium.launch({headless:true,channel:'chrome'});
  const page=await browser.newPage({viewport:{width:1650,height:1200}}),errors=[],consoleErrors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text().slice(0,500))});
  await page.addInitScript(()=>{window.__fontProof=[];const native=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(text,...args){if(typeof text==='string'&&/Schistosoma|Concordant/.test(text))window.__fontProof.push({text,font:this.font});return native.call(this,text,...args)}});
  await page.goto(base);
  await expect(page.locator('#proof strong')).toHaveText('Strong evidence',{timeout:120000});
  await expect(page.locator('#proof em').first()).toHaveText('Schistosoma mansoni');
  await expect(page.locator('#proof')).not.toContainText('**');
  await expect(page.locator('[data-testid="stPlotlyChart"] .js-plotly-plot')).toBeVisible({timeout:120000});
  await page.setViewportSize({width:1640,height:1200});
  await expect.poll(()=>page.evaluate(()=>window.__fontProof.some(r=>r.text==='Schistosoma mansoni'&&/italic/.test(r.font)))).toBe(true);
  await expect.poll(()=>page.evaluate(()=>window.__fontProof.some(r=>r.text==='Concordant'&&/700|bold/.test(r.font)))).toBe(true);
  const legend=page.locator('[data-testid="stPlotlyChart"] .legendtext').filter({hasText:'Schistosoma mansoni'}).first();
  assert(await legend.evaluate(e=>[...e.querySelectorAll('tspan')].some(s=>s.textContent==='Schistosoma mansoni'&&getComputedStyle(s).fontStyle==='italic')),await legend.evaluate(e=>e.outerHTML));
  await page.getByRole('combobox',{name:'Species proof',exact:true}).click();
  const option=page.getByRole('option',{name:'Schistosoma japonicum',exact:true});
  await expect(option).toHaveCSS('font-style','italic');await option.click();
  await expect(page.getByText('Raw selection:',{exact:false}).last()).toContainText('Schistosoma japonicum');
  const frame=page.frameLocator('iframe').first();
  await expect(frame.locator('#owned strong')).toHaveText('Supported');
  await expect(frame.locator('#owned em')).toHaveText('S. mansoni');
  await expect(frame.locator('svg tspan')).toHaveCSS('font-style','italic');
  await expect(frame.locator('#literal')).toHaveText('**raw** S. mansoni');
  await frame.locator('body').evaluate(body=>{const select=document.createElement('select');select.id='species-menu';select.innerHTML='<option value="all">All species</option><option value="protein1">protein1 · S. mansoni</option>';body.appendChild(select)});
  await frame.locator('#species-menu').selectOption('protein1');
  await expect(frame.locator('#species-menu')).toHaveCSS('font-style','italic');
  await expect(frame.locator('#species-menu')).toHaveValue('protein1');
  await frame.locator('#species-menu').selectOption('all');
  await expect(frame.locator('#species-menu')).toHaveCSS('font-style','normal');
  await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(out,'scientific-typography.png'),fullPage:true,animations:'disabled'});
  fs.writeFileSync(path.join(out,'scientific-typography-validation.json'),JSON.stringify({html_bold:true,html_species:true,canvas_species:true,canvas_bold:true,figure_species:true,dropdown_species:true,raw_values_preserved:true,owned_svg:true,code_preserved:true},null,2));
  console.log('PASS scientific HTML, bold markers, actual native-grid canvas italics/bold, figure legends, species menus, unchanged widget values, embedded HTML/SVG and literal code.');
 }finally{if(browser)await browser.close();if(server)cp.spawnSync('taskkill',['/PID',String(server.pid),'/T','/F'],{windowsHide:true})}
}
main().catch(e=>{console.error(e);process.exitCode=1});
