/* Real Chromium pointer-event regression tests; no network resources required. */
const assert = require('node:assert/strict');
const path = require('node:path');
const ATLAS_ROOT = path.resolve(module.path,'..');
const {pathToFileURL} = require('node:url');
let playwright, expect;
try { playwright = require('playwright'); ({expect} = require('playwright/test')); }
catch (_) { const packagePath = path.join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright'); playwright = require(packagePath); ({expect} = require(path.join(packagePath,'test'))); }

async function main() {
  const options = {headless: true};
  if (process.env.ATLAS_TEST_CHROME) options.executablePath = process.env.ATLAS_TEST_CHROME;
  else if (process.platform === 'win32') options.channel = 'chrome';
  const browser = await playwright.chromium.launch(options);
  try {
    const page = await browser.newPage({viewport: {width: 1920, height: 1400}});
    const errors = [], externalRequests = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route(/^https?:/, route => { externalRequests.push(route.request().url()); return route.abort(); });
    const source = path.join(ATLAS_ROOT, 'adhesome_network/Schistosome_adhesome_rebuilt.html');
    await page.goto(pathToFileURL(source).href);
    await page.locator('#reset').click();
    const filterDrawer=page.locator('.atlas-filter-drawer > summary');
    if (await filterDrawer.count()) await filterDrawer.click();
    await page.locator('#species').selectOption('Schistosoma mansoni');
    await page.locator('#scope').selectOption('all');
    await page.locator('[data-family="collagen-like"]').click();
    const actual = await state(page);
    if (process.argv.includes('--reproduce')) {
      console.log(JSON.stringify({clicked: 'collagen-like', selected: actual.selected, candidateCount: actual.context?.candidates.length ?? null, errors}, null, 2));
      return;
    }
    assert.equal(actual.selected, 'collagen-like', 'actual pointer click must select the node');
    const mansoniCollagens=await page.evaluate(()=>DATA.candidates.filter(p=>p.f==='collagen-like'&&p.s==='Schistosoma mansoni'));
    await assertSelection(page,'collagen-like',mansoniCollagens);
    assert(actual.context.candidates.every(c => c.grade === 'C'));
    assert.deepEqual(actual.context.highlighted_path.nodes, ['collagen-like']);
    assert.deepEqual(actual.context.highlighted_path.edges, []);
    assert.match(await page.locator('#atlas-connected-info').innerText(), /No recorded connections/);
    const collagenIds = actual.context.candidates.map(p => p.id);
    for (const id of collagenIds) {
      await page.locator('select[aria-label="Candidate profiles for collagen-like"]').selectOption(id);
      const next = await state(page);
      assert.equal(next.selected, 'collagen-like');
      assert.equal(next.context.candidate, id);
      assert.equal(next.context.profile.candidate.sequence_id, id);
      assert.equal(next.context.profile.candidate.grade, 'C');
      assert.match(await page.locator('#atlas-profile-detail').innerText(), new RegExp(id));
    }
    // Species and confidence controls must retain exact source counts, including C.
    const bySpecies = await page.evaluate(() => DATA.meta.species.map(species => ({species,
      records: DATA.candidates.filter(p => p.f === 'collagen-like' && p.s === species)})));
    for (const {species, records} of bySpecies) {
      await page.locator('#species').selectOption(species);
      await page.locator('[data-family="collagen-like"]').click();
      await assertSelection(page, 'collagen-like', records);
    }
    await page.locator('#species').selectOption('Schistosoma intercalatum');
    await page.locator('[data-family="collagen-like"]').click();
    const intercalatum=bySpecies.find(item=>item.species==='Schistosoma intercalatum').records;
    await assertSelection(page,'collagen-like',intercalatum);
    for (const grade of ['A', 'AB']) {
      await page.locator('#grade').selectOption(grade);
      assert.equal(await page.locator('[data-family="collagen-like"]').count(),0);
    }
    await page.locator('#grade').selectOption('all');
    await page.locator('#species').selectOption('all');
    await page.locator('#pairs').selectOption('1');
    const snapshot = await page.evaluate(() => ({families: DATA.families, candidates: DATA.candidates, edges: activeEdges}));
    const profileInventory = await page.evaluate(() => [...atlasProfileIndex.values()].map(p => ({id:p.sequence_id,f:p.family,s:p.species,g:p.grade})));
    assert.deepEqual(profileInventory.sort((a,b)=>a.id.localeCompare(b.id)), snapshot.candidates.map(p=>({id:p.id,f:p.f,s:p.s,g:p.g})).sort((a,b)=>a.id.localeCompare(b.id)), 'native graph and audited profile inventories must agree exactly');
    const zones = new Set();
    for (const family of snapshot.families) {
      // Locator.click emits real Chromium pointerdown/capture/pointerup events.
      await page.locator(`[data-family="${family.id}"]`).click();
      await assertSelection(page, family.id, snapshot.candidates.filter(p => p.f === family.id));
      const selected = await state(page), expected = neighborhood(family.id, snapshot.edges, Infinity);
      assert.deepEqual(selected.context.highlighted_path.nodes.sort(), [...expected.nodes].sort(), family.id + ' connected nodes');
      assert.deepEqual(selected.context.highlighted_path.edges.map(e=>e.id).sort(), expected.edges.sort(), family.id + ' recorded edges');
      const styles = await page.evaluate(() => ({
        nodes:[...document.querySelectorAll('[data-family]')].map(g=>({id:g.dataset.family,opacity:g.getAttribute('opacity'),stroke:g.querySelector('rect').getAttribute('stroke')})),
        edges:[...document.querySelectorAll('[data-edge-id]')].map(e=>({id:e.dataset.edgeId,opacity:e.getAttribute('opacity')}))}));
      for (const node of styles.nodes) assert.equal(Number(node.opacity), expected.nodes.has(node.id) ? 1 : .25, family.id + ' node dimming ' + node.id);
      for (const edge of styles.edges) assert.equal(Number(edge.opacity), expected.edges.includes(edge.id) ? 1 : .045, family.id + ' edge dimming ' + edge.id);
      assert.equal(styles.nodes.find(n=>n.id===family.id).stroke, '#b91c1c');
      zones.add(family.zone);
    }
    console.log(`PASS actual Chromium node clicks, candidate sets/counts, recorded-edge traversal and dimming for all ${snapshot.families.length} families in ${zones.size} levels`);
    // Context-only receptor: zero candidates, no stale profile from the previous node.
    await page.locator('[data-family="SmVKR1"]').click();
    assert.equal((await state(page)).selected, 'SmVKR1');
    assert.deepEqual((await state(page)).context.candidates, []);
    assert.equal((await state(page)).context.candidate, '');
    assert.equal((await state(page)).context.profile_html, '');
    assert.match(await page.locator('#sidebar').innerText(), /No candidate profiles are associated with SmVKR1/);
    await page.locator('[data-family="ILK"]').click();
    const displayOptions=page.locator('.atlas-display-options > summary');
    if (await displayOptions.count()) await displayOptions.click();
    for (const [mode, limit] of [['1',1],['2',2],['component',Infinity]]) {
      await page.locator('#atlas-path-scope').selectOption(mode);
      const expected = neighborhood('ILK', snapshot.edges, limit), actual = (await state(page)).context.highlighted_path;
      assert.deepEqual(actual.nodes.sort(), [...expected.nodes].sort());
      assert.deepEqual(actual.edges.map(e=>e.id).sort(), expected.edges.sort());
    }
    await page.locator('#atlas-path-target').selectOption('SmVKR1');
    let route = (await state(page)).context.highlighted_path;
    assert.equal(route.route[0], 'ILK'); assert.equal(route.route.at(-1), 'SmVKR1');
    for(let i=1;i<route.route.length;i++) assert(snapshot.edges.some(e=>[e.a,e.b].includes(route.route[i-1])&&[e.a,e.b].includes(route.route[i])), 'shortest route uses actual edges');
    await page.locator('#atlas-path-target').selectOption('collagen-like');
    route = (await state(page)).context.highlighted_path;
    assert.equal(route.unreachable, true); assert.deepEqual(route.nodes, ['ILK']);
    await page.locator('#atlas-path-target').selectOption('');
    // Keyboard selection and partner browsing use the same transaction.
    await page.locator('[data-family="Src"]').focus(); await page.keyboard.press('Enter');
    assert.equal((await state(page)).selected, 'Src');
    await page.locator('[data-family="FAK"]').focus(); await page.keyboard.press('Space');
    assert.equal((await state(page)).selected, 'FAK');
    const partner = await page.locator('select[aria-label="Linked partner families"] option').nth(1).getAttribute('value');
    await page.locator('select[aria-label="Linked partner families"]').selectOption(partner);
    assert.equal((await state(page)).selected, partner);
    // Pan preserves selection; zoom controls and wheel still update the viewport.
    const beforePan = await page.locator('#network').getAttribute('viewBox'), graph = await page.locator('#network').boundingBox();
    await page.mouse.move(graph.x+5, graph.y+5); await page.mouse.down();
    await page.mouse.move(graph.x+85,graph.y+65,{steps:8}); await page.mouse.up();
    assert.notEqual(await page.locator('#network').getAttribute('viewBox'), beforePan);
    assert.equal((await state(page)).selected, partner);
    await page.locator('#reset').click();
    const fitted = await page.locator('#network').getAttribute('viewBox');
    await page.locator('#zoomIn').click(); assert.notEqual(await page.locator('#network').getAttribute('viewBox'), fitted);
    await page.locator('#zoomOut').click(); await page.locator('#reset').click();
    await page.locator('#network').hover(); await page.mouse.wheel(0,-100);
    await page.waitForFunction(value=>document.getElementById('network').getAttribute('viewBox')!==value,fitted);
    assert.notEqual(await page.locator('#network').getAttribute('viewBox'), fitted);
    await page.locator('#reset').click();
    // Select an unobstructed point on a real edge, rather than its bounding box.
    const point = await page.evaluate(() => {
      for(const edge of document.querySelectorAll('[data-edge-id]')) for(const t of [.25,.4,.6,.75]) {
        const local=edge.getPointAtLength(edge.getTotalLength()*t), screen=new DOMPoint(local.x,local.y).matrixTransform(edge.getScreenCTM());
        if(document.elementFromPoint(screen.x,screen.y)?.closest('[data-edge-id]')===edge)return {x:screen.x,y:screen.y,id:edge.dataset.edgeId};
      }
    });
    assert(point, 'an accessible edge is required'); await page.mouse.click(point.x,point.y);
    assert.equal(await page.evaluate(()=>current.edge), point.id);
    assert.equal((await state(page)).context, null);
    await page.locator('#human').uncheck(); await page.locator('[data-family="Src"]').click();
    assert.equal((await state(page)).context.highlighted_path.edges.length,0);
    await page.locator('#human').check();
    await page.locator('#search').fill('ILK');
    assert.equal(await page.locator('[data-family="ILK"]').getAttribute('opacity'), '1');
    assert.equal(await page.locator('[data-family="collagen-like"]').getAttribute('opacity'), '0.35');
    await page.locator('#search').fill('');
    await page.locator('#scope').selectOption('linked'); assert.equal(await page.locator('[data-family="collagen-like"]').count(),0);
    await page.locator('#scope').selectOption('all');
    // Search in the complete family list does not change node/path selection.
    await page.locator('[data-family="collagen-like"]').click();
    assert.equal((await state(page)).context.candidates.length,75);
    await page.locator('input[aria-label="Find a candidate in this family"]').fill(collagenIds[0]);
    assert.equal(await page.locator('select[aria-label="Candidate profiles for collagen-like"] option').count(),1);
    assert.equal((await state(page)).selected, 'collagen-like');
    await page.locator('input[aria-label="Find a candidate in this family"]').fill('');
    assert.equal(await page.locator('select[aria-label="Candidate profiles for collagen-like"] option').count(),75);
    // Connected-only follows the visible edges and clears a hidden selection.
    const connectedOnly=page.getByRole('checkbox',{name:'Show connected nodes only'});
    const graphBefore=await graphState(page);
    assert(graphBefore.edges.length>0);
    assert(graphBefore.families.includes('collagen-like'));
    await connectedOnly.check();
    assert.deepEqual(await graphState(page),{...graphBefore,families:graphBefore.endpoints});
    assert.deepEqual(await state(page),{selected:null,context:null});
    await page.locator('#species').selectOption('Schistosoma mansoni');
    const mansoniGraph=await graphState(page);
    assert.notDeepEqual(mansoniGraph.edges,graphBefore.edges);
    assert.deepEqual(mansoniGraph.families,mansoniGraph.endpoints);
    await page.locator('#human').uncheck(); await page.locator('#sm').uncheck();
    assert.deepEqual(await graphState(page),{families:[],edges:[],endpoints:[]});
    await expect(page.locator('.atlas-connectivity-message')).toHaveText('No connections match the active filters.');
    await connectedOnly.uncheck();
    await page.locator('#species').selectOption('all');
    await page.locator('#human').check(); await page.locator('#sm').check();
    assert.deepEqual(await graphState(page),graphBefore);
    await page.locator('[data-family="collagen-like"]').click();
    // Local SVG export remains downloadable.
    const downloadPromise=page.waitForEvent('download'); await page.locator('#svgExport').click();
    assert.match((await downloadPromise).suggestedFilename(), /\.svg$/);
    // Mobile drawer can be closed and re-opened by independent node selection.
    await page.setViewportSize({width:600,height:1000});
    await page.locator('button.atlas-panel-close').click();
    await page.locator('[data-family="collagen-like"]').click();
    assert.match(await page.locator('body').getAttribute('class'), /atlas-side-open/);
    await page.locator('button.atlas-panel-close').click();
    await page.locator('[data-family="ILK"]').click();
    assert.equal((await state(page)).selected, 'ILK');
    assert.deepEqual(errors, []);
    assert.deepEqual(externalRequests, []);
    console.log(`PASS actual Chromium clicks: ${snapshot.families.length} families across ${zones.size} network levels; complete profiles, exact A/B/C and path/dimming checks; SmVKR1 empty state`);
    console.log('PASS all S. mansoni collagen profiles; seven species; A/AB and connected-only filters; direct/component/shortest paths; keyboard/partners; pan/zoom/search/SVG export/mobile; offline');
    const linkedIndex=process.argv.indexOf('--linked');
    if(linkedIndex>=0) await checkLinked(browser, process.argv[linkedIndex+1]);
  } finally { await browser.close(); }
}

async function state(page) { return page.evaluate(() => ({selected: current.family, context: window.atlasCandidateContext()})); }
async function graphState(page) {
  return page.evaluate(() => {
    const families=[...document.querySelectorAll('[data-family]')].map(node=>node.dataset.family).sort();
    const edges=[...document.querySelectorAll('[data-edge-id]')].map(edge=>edge.dataset.edgeId).sort();
    const visible=new Set(edges);
    const endpoints=[...new Set(activeEdges.filter(edge=>visible.has(edge.id)).flatMap(edge=>[edge.a,edge.b]))].sort();
    return {families,edges,endpoints};
  });
}
async function assertSelection(page, family, records) {
  const selected=await state(page), context=selected.context;
  assert.equal(selected.selected,family);
  assert.deepEqual(context.candidates.map(p=>p.id).sort(),records.map(p=>p.id).sort(),family+' complete candidate set');
  assert.deepEqual(context.candidate_counts,Object.fromEntries(['A','B','C','D'].map(g=>[g,records.filter(p=>p.g===g).length])),family+' exact grades');
  assert.equal(context.profile.candidate.family,family);
  assert.equal(context.profile.candidate.sequence_id,context.candidate);
  assert(records.some(p=>p.id===context.candidate));
  assert.deepEqual(await page.locator(`select[aria-label="Candidate profiles for ${family}"] option`).evaluateAll(options=>options.map(o=>o.value).sort()),records.map(p=>p.id).sort(),family+' full rendered list');
  const evidence=await page.locator('#atlas-profile-detail').innerText();
  for(const label of ['Architecture & localization','Integrated evidence & family decision','CDD domain hits','Motif context evidence','Reference orthologues'])assert(evidence.includes(label));
}
function neighborhood(start,edges,limit) {
  const nodes=new Set([start]);let frontier=[start];
  for(let depth=0;frontier.length&&depth<limit;depth++){
    const next=[];
    for(const node of frontier)for(const edge of edges){const target=edge.a===node?edge.b:edge.b===node?edge.a:null;if(target&&!nodes.has(target)){nodes.add(target);next.push(target)}}
    frontier=next;
  }
  return {nodes,edges:edges.filter(e=>nodes.has(e.a)&&nodes.has(e.b)).map(e=>e.id)};
}
async function checkLinked(browser,file) {
  const page=await browser.newPage({viewport:{width:1920,height:1400}}), errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(/^https?:/,route=>{external.push(route.request().url());return route.abort()});
  await page.goto(pathToFileURL(file).href);
  const map=page.frameLocator('#mapFrame');
  await map.locator('.atlas-filter-drawer > summary').click();
  await map.locator('#species').selectOption('Schistosoma mansoni');
  await map.locator('#scope').selectOption('all');
  await map.locator('[data-family="collagen-like"]').click();
  const n=await map.locator('#network').evaluate(()=>DATA.candidates.filter(p=>p.f==='collagen-like'&&p.s==='Schistosoma mansoni').length);
  await expect(page.locator('#linkedCandidate option')).toHaveCount(n);
  await expect(page.locator('#candidateCounts')).toHaveText(n+' candidates · A = 0 · B = 0 · C = '+n+' · D = 0 (unassigned)');
  await expect(page.locator('#pathSummary')).toContainText('No recorded connections for collagen-like');
  const ids=await page.locator('#linkedCandidate option').evaluateAll(options=>options.map(o=>o.value));
  for(const id of ids){await page.locator('#linkedCandidate').selectOption(id);await expect(page.locator('#candidateProfile')).toContainText(id);}
  const selected=ids.at(-1);
  await page.locator('#simulateSelection').click();
  await expect(page.locator('#mapFrame')).toBeHidden();
  await expect(page.locator('#candidateProfile')).toBeVisible();
  await expect(page.locator('#candidateProfile')).toContainText(selected);
  await expect(page.frameLocator('#simulatorFrame').locator('#linkedContext')).toContainText(selected);
  await page.locator('#showMap').click();
  await map.locator('[data-family="ILK"]').click();
  await expect(page.locator('#selectionHint')).toContainText('ILK');
  const frame=page.frames().find(f=>f.name()==='mapFrame')||await page.locator('#mapFrame').elementHandle().then(e=>e.contentFrame());
  const ctx=await state(frame);
  await expect(page.locator('#linkedCandidate option')).toHaveCount(ctx.context.candidates.length);
  await expect(page.locator('#candidateProfile')).toContainText(ctx.context.candidate);
  await page.locator('#showBoth').click();await expect(page.locator('#candidateProfile')).toBeVisible();
  await page.locator('#showMap').click();await map.locator('[data-family="SmVKR1"]').click();
  await expect(page.locator('#linkedCandidate')).toBeDisabled();
  await expect(page.locator('#candidateCounts')).toHaveText('0 candidates · A = 0 · B = 0 · C = 0 · D = 0 (unassigned)');
  await expect(page.locator('#candidateProfile')).toContainText('No candidate profiles are associated');
  const connectedOnly=map.getByRole('checkbox',{name:'Show connected nodes only'});
  await connectedOnly.check();
  await expect(map.locator('[data-family="SmVKR1"]')).toHaveCount(1);
  await expect(page.locator('#selectionHint')).toContainText('SmVKR1');
  await connectedOnly.uncheck();
  await map.locator('[data-family="collagen-like"]').click();
  await connectedOnly.check();
  await expect(map.locator('[data-family="collagen-like"]')).toHaveCount(0);
  await expect(page.locator('#pathSummary')).toHaveText('No path selected.');
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('PASS generated linked HTML: actual node clicks, complete collagen candidate rail, candidate switching, connected-only filter and dossier synchronization, simulator context/profile retention, both view and empty state; no external requests');
  await page.close();
}
main().catch(e => { console.error(e); process.exitCode = 1; });
