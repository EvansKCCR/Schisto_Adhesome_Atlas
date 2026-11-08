/* Reproducibility and independent IPP/VKR1 assembly checks. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ATLAS_ROOT = path.resolve(module.path,'..');
const {createHash} = require('node:crypto');
const {pathToFileURL} = require('node:url');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(ATLAS_ROOT,'main','simulator_engine.js'),'utf8');
const engine = vm.runInNewContext(source + '\nAdhesionMatrix');
const weights = engine.matrix(.85,.30,.05);
const canonical = engine.simulate({grid:3,integrins:8,steps:30,seed:975,
    layeredMechanics:false,enableIPP:false,enableVKR:false},weights);
const structuralHistory = canonical.snapshots.map(({adhesome_lattice,force,actin})=>({adhesome_lattice,force,actin}));
assert.equal(createHash('sha256').update(JSON.stringify(structuralHistory)).digest('hex'),
    'd7188e5b5afda57af240e61590f9dcb6014922527f4beec2779dcf89f633e62f',
    'Legacy structural trajectory matches the preceding engine');

const p = {grid:3,integrins:9,steps:12,seed:2008,ligand:1,off:0,ruptureForce:100,
    kindlinProbability:1,ilkProbability:1,pinchProbability:1,parvinProbability:1,ippActinProbability:1,
    bridgeGate:1,vkrGate:1,talinActinProbability:1,enableKinaseContext:true,actinRegulationProbability:1};
const run = overrides => engine.simulate({...p,...overrides},weights);
const last = overrides => run(overrides).snapshots.at(-1);
const both = last({});
for (const key of ['kindlinCount','ilkCount','pinchCount','parvinCount','ippCount','ippActinCount','nckCount','vkr1Count']) {
    assert.equal(both.metrics[key],9,key);
}
assert.equal(last({enableIPP:false}).metrics.ippCount,0);
assert.equal(last({enableIPP:false}).metrics.vkr1Count,9);
assert.equal(last({enableVKR:false}).metrics.ippCount,9);
assert.equal(last({enableVKR:false}).metrics.nckCount,0);
assert.equal(last({vkrGate:0}).metrics.nckCount,9);
assert.equal(last({vkrGate:0}).metrics.vkr1Count,0);
assert.equal(last({parvinProbability:0}).metrics.ippCount,0);
assert.equal(last({parvinProbability:0}).metrics.vkr1Count,9);
assert.equal(last({pinchProbability:0}).metrics.parvinCount,9);
assert.equal(last({pinchProbability:0}).metrics.ippCount,0);
assert.equal(last({pinchProbability:0}).metrics.vkr1Count,0);
assert.equal(last({kindlinProbability:0}).metrics.ippCount,0);
assert.equal(last({kindlinProbability:0}).metrics.vkr1Count,9);
assert.equal(last({fakGate:0}).metrics.fak,0);
assert(last({}).metrics.fak>0);
assert(last({}).metrics.enaVaspCount>0);
assert.equal(last({enableActinRegulation:false}).metrics.enaVaspCount,0);
assert(last({}).metrics.gonadalContext>0);
assert.equal(last({enableKinaseContext:false}).metrics.gonadalContext,0);
assert.deepEqual(run({}),run({}));
assert.notDeepEqual(run({seed:2026}).snapshots,run({}).snapshots);
const lowThreshold = run({threshold:.2,enableIPP:false});
const highThreshold = run({threshold:100,enableIPP:false});
assert(lowThreshold.snapshots.reduce((n,s)=>n+s.metrics.mature,0)>highThreshold.snapshots.reduce((n,s)=>n+s.metrics.mature,0));
assert(highThreshold.snapshots.every(s=>s.metrics.exposed===0));
for (const snap of run({ruptureForce:.6}).snapshots) {
    snap.adhesome_lattice.flat().forEach((A,i)=>{
        const site=snap.nanoscale_state[i];
        if (!A[0][0]) assert(engine.siteFields.every(key=>!site[key]) && snap.force[i]===0);
        if (site.ipp) assert(site.kindlin && site.ilk && site.pinch && site.parvin);
        if (site.vkr1) assert(site.ilk && site.pinch && site.nck);
    });
}
console.log('PASS legacy I–T–V parity, fixed seeds, exposure-dependent recruitment, explicit ternary assembly, shared occupancy, independent VKR1, FAK/Src, actin recruitment and rupture resets.');

async function browserChecks() {
    let pw;
    try { pw = require('playwright'); }
    catch (_) { pw = require(path.join(process.env.USERPROFILE,'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright')); }
    const browser = await pw.chromium.launch({headless:true,channel:'chrome'});
    try {
        const page = await browser.newPage({acceptDownloads:true});
        const errors = [], requests = [];
        page.on('pageerror',error=>errors.push(error.message));
        page.on('request',request=>{if (/^https?:/.test(request.url())) requests.push(request.url());});
        const html = path.join(ATLAS_ROOT,'adhesome_network','schistosome_integrin_adhesome_hypothesis_simulator.html');
        await page.goto(pathToFileURL(html).href);
        await page.locator('#depth0 text').first().waitFor();
        assert.equal(await page.locator('#zoneCards .zoneCard').count(),3);
        assert.equal(await page.locator('#species option').count(),8);
        await page.locator('#mechanismInspector > summary').click();
        await page.locator('#mechanismProtein').selectOption('Parvin_like');
        await page.locator('#mechanismRule').selectOption('M10');
        const evidence = await page.locator('#mechanismEvidence').innerText();
        assert(evidence.includes('R19') && evidence.includes('Parvin occupancy'));
        assert.equal(await page.locator('#mechanismEvidence a[href="https://doi.org/10.1242/jcs.155879"]').count(),1);
        await page.getByText('Layered assembly modules and parameters',{exact:true}).click();
        await page.locator('#enableIPP').uncheck();
        await page.locator('#run').click();
        assert.equal(await page.evaluate(()=>results[0].snapshots.at(-1).metrics.ippCount),0);
        await page.locator('#enableIPP').check();
        await page.locator('#run').click();
        assert(await page.evaluate(()=>results[0].snapshots.at(-1).metrics.ippCount)>0);
        assert.equal(await page.evaluate(()=>results[1].snapshots.at(-1).metrics.vkr1Count),0);
        const downloadEvent = page.waitForEvent('download');
        await page.locator('#export').click();
        const download = await downloadEvent;
        const exported = JSON.parse(fs.readFileSync(await download.path(),'utf8'));
        assert.equal(exported.schema_version,4);
        assert.equal(exported.schistosome_provenance.random_seed,2008);
        assert(exported.schistosome_provenance.active_rule_ids.includes('M10'));
        assert(!exported.reference_provenance.active_rule_ids.includes('M13'));
        assert(exported.reference_registry.R02.doi_url.includes('1006147'));
        assert(exported.systems.schistosome.snapshots.at(-1).nanoscale_state.some(site=>site.ipp));
        assert.deepEqual(errors,[]);
        assert.deepEqual(requests,[]);
        console.log('PASS offline browser layers, mechanism evidence, toggle controls and reproducible JSON export.');
    } finally { await browser.close(); }
}
if (process.argv.includes('--browser')) browserChecks().catch(error=>{console.error(error);process.exitCode=1;});
