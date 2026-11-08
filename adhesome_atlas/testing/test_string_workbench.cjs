/* Verify original-sequence mapping through the live Streamlit controls. */
const path=require('node:path');let pw,expect;
const ATLAS_ROOT=path.resolve(module.path,'..');
try{pw=require('playwright');({expect}=require('playwright/test'))}catch(_){const pkg=path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');pw=require(pkg);({expect}=require(path.join(pkg,'test')))}
async function choose(page,label,option){await page.getByRole('combobox',{name:label,exact:true}).click();await page.getByRole('option',{name:option,exact:true}).click()}
async function main(){const browser=await pw.chromium.launch({headless:true,...(process.platform==='win32'?{channel:'chrome'}:{})});try{
 const page=await browser.newPage({viewport:{width:1800,height:1100}});await page.goto(process.env.ATLAS_PREVIEW_URL||'http://127.0.0.1:8511/');
 await expect(page.getByText('Interactions',{exact:true})).toBeVisible({timeout:180000});await page.getByText('Interactions',{exact:true}).click();
 await expect(page.getByRole('combobox',{name:'Network workspace'})).toBeVisible({timeout:120000});await choose(page,'Network workspace','STRING query & import');
 await expect(page.getByRole('combobox',{name:'STRING query species'})).toBeVisible({timeout:60000});await choose(page,'STRING query species','Schistosoma mansoni');
 await expect(page.getByRole('button',{name:'Remove Provisional',exact:true})).toBeVisible({timeout:60000});await page.getByRole('button',{name:'Remove Provisional',exact:true}).click();
 await choose(page,'Protein families for STRING','ILK');await page.keyboard.press('Escape');
 await expect(page.getByRole('combobox',{name:'STRING protein mapping',exact:true})).toHaveValue('Protein sequences (recommended)',{timeout:30000});
 await page.getByRole('button',{name:'1 · Resolve selected proteins in STRING',exact:true}).click();
 await expect(page.getByText('1 proteins mapped; 0 unresolved.',{exact:true})).toBeVisible({timeout:180000});
 await expect(page.getByRole('button',{name:'Download resolved STRING mapping · TSV',exact:true})).toBeVisible();
 await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download resolved STRING mapping · TSV',exact:true}).click();
 const file=await download,pathOnDisk=await file.path();const fs=require('node:fs'),text=fs.readFileSync(pathOnDisk,'utf8');
 if(!text.includes('Sman__Smp_079760\t6183.A0A3Q0KIA3')||!text.includes('Protein sequence similarity'))throw new Error('Downloaded mapping does not join the selected candidate to its sequence representative');
 await page.getByRole('button',{name:'2 · Fetch STRING network and analyze',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Imported STRING network · topology and communities',exact:true})).toBeVisible({timeout:180000});
 await expect(page.locator('[data-testid="stException"]')).toHaveCount(0);
 await page.screenshot({path:path.join(ATLAS_ROOT,'.ui_review/string-sequence-workbench.png')});
 console.log('PASS live Atlas UI: S. mansoni ILK selection, original-sequence default, STRING mapping TSV, network retrieval and topology workspace');
}finally{await browser.close()}}
main().catch(e=>{console.error(e);process.exitCode=1});
