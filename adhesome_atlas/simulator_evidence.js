/* Literature and controls for the layered simulator. Included in offline builds. */
const simulatorEvidence = JSON.parse(document.getElementById('atlas-mechanisms').textContent);
const moduleSwitches = [
    ['layeredMechanics','Force-transmitting talin/actin linkage'],
    ['enableIPP','Kindlin–ILK–PINCH–parvin scaffold'],
    ['enableVKR','Smβ-Int1–ILK–PINCH–Nck2–SmVKR1 branch'],
    ['enableActinRegulation','Actin-regulatory recruitment'],
    ['enableKinaseContext','Schistosome kinase and Rho context'],
];
const moduleParameters = [
    ['talinActinProbability','Talin–actin coupling probability',0,1,.05],
    ['relaxation','Unloaded force relaxation per step',0,3,.05],
    ['kindlinProbability','Kindlin occupancy probability',0,1,.05],
    ['ilkProbability','Shared ILK recruitment probability',0,1,.05],
    ['pinchProbability','PINCH recruitment probability',0,1,.05],
    ['parvinProbability','Parvin recruitment probability',0,1,.05],
    ['ippActinProbability','IPP–actin coupling probability',0,1,.05],
    ['ippStabilization','IPP-linked overload tolerance gain',0,3,.05],
    ['paxillinProbability','Paxillin recruitment probability',0,1,.05],
    ['actinRegulationProbability','Actin regulator recruitment probability',0,1,.05],
    ['gonadalGate','Src/Syk/Abl/Rho context gate',0,1,.05],
    ['pkcMapkGate','PKC/ERK context gate',0,1,.05],
];
const ruleList = simulatorEvidence.mechanisms.rules;
const architectureLayers = simulatorEvidence.mechanisms.layers;

function activeRules(p) {
    const enabled = {
        M03:p.layeredMechanics, M08:p.enableIPP, M09:p.enableIPP || (p.enableVKR && p.bridgeGate > 0),
        M10:p.enableIPP, M11:p.enableIPP, M12:p.enableVKR && p.bridgeGate > 0,
        M13:p.enableVKR && p.bridgeGate > 0 && p.vkrGate > 0, M14:p.fakGate > 0,
        M15:p.paxillinProbability > 0, M16:p.enableActinRegulation,
        M17:p.enableKinaseContext, M18:p.enableKinaseContext, M19:p.allowIV
    };
    return ruleList.filter(rule => enabled[rule.rule_id] !== false).map(rule => rule.rule_id);
}

function modelProvenance(p) {
    return {
        ...simulatorEvidence.provenance,
        simulator_config_version:simulatorEvidence.mechanisms.version,
        active_rule_ids:activeRules(p),
        random_seed:p.seed,
        parameter_values:p,
    };
}

function inspectMechanism() {
    const component = $('mechanismProtein').value;
    const choices = ruleList.filter(rule => !component || rule.components.includes(component));
    const select = $('mechanismRule'), previous = select.value;
    select.replaceChildren();
    for (const rule of choices) {
        const option = new Option(rule.rule_id+' · '+rule.rule_name,rule.rule_id);
        select.add(option);
    }
    if (choices.some(rule => rule.rule_id === previous)) select.value = previous;
    const rule = choices.find(rule => rule.rule_id === select.value);
    const box = $('mechanismEvidence');
    box.replaceChildren();
    if (!rule) return;
    const role = document.createElement('p');
    role.textContent = rule.biological_description;
    const scope = document.createElement('p');
    scope.className = 'muted';
    scope.textContent = [rule.functional_layer,rule.model_basis,rule.evidence_origin.replaceAll('_',' ')].join(' · ');
    const transition = document.createElement('p');
    transition.textContent = [rule.input_state,rule.transition_condition,rule.output_state].join(' → ');
    const parameters = document.createElement('p');
    parameters.textContent = 'Simulation variables · ' + rule.configurable_parameters.join(', ');
    box.append(role,scope,transition,parameters);
    if (results.length) {
        const active = document.createElement('p');
        const projected = activeRules(results[0].parameters).includes(rule.rule_id);
        active.textContent = projected ? 'Enabled in the last schistosome run.' : 'Disabled in the last schistosome run.';
        box.append(active);
    }
    renderLiteratureEvidence(box,rule.reference_ids.map(reference_id => ({reference_id})),simulatorEvidence.references);
    const names = component ? [component] : rule.components;
    const candidates = names.flatMap(name => (simulatorEvidence.candidates[name]||[]).map(record => ({name,...record})))
        .filter(record => $('species').value === 'pan' || speciesLabels[$('species').value] === record.species);
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Library candidates in the selected context ('+candidates.length+')';
    details.append(summary);
    for (const record of candidates) {
        const row = document.createElement('div');
        row.textContent = [record.name,record.sequence_id,record.species,record.family,record.family_support_level].join(' · ');
        details.append(row);
    }
    box.append(details);
}

function layeredDepth(index) {
    const result = results[index], snap = result.snapshots[frame];
    const A = snap.adhesome_lattice.flat()[site], n = snap.nanoscale_state[site];
    const svg = $('depth'+index);
    svg.replaceChildren();
    const rows = [
        ['#edf7ef', ['I αβ '+A[0][0], 'Kindlin '+Number(n.kindlin), 'Paxillin '+Number(n.paxillin),
            'FAK/Src '+(100*n.fak).toFixed(0)+'%', 'Nck2 '+Number(n.nck), 'VKR1 '+Number(n.vkr1)]],
        ['#fff8d8', ['Talin '+A[1][1], 'Vinculin '+A[2][2], 'ILK '+Number(n.ilk),
            'PINCH '+Number(n.pinch), 'Parvin '+Number(n.parvin), 'IPP '+Number(n.ipp)]],
        ['#fbeeed', ['F-actin '+Number(snap.actin[site]||n.talinActin||n.ippActin),
            'α-Actinin '+Number(n.alphaActinin), 'Zyxin/Ajuba '+Number(n.zyxinAjuba),
            'Ena/VASP '+Number(n.enaVasp), 'IPP–actin '+Number(n.ippActin)]],
    ];
    rows.forEach(([color,labels],i) => {
        const layer = architectureLayers[i], top = i*90+5;
        const background = svgElement('rect',{x:4,y:top,width:590,height:84,fill:color,rx:7,stroke:'#b7cbbd'});
        background.append(svgElement('title',{},layer.components.join(' · ')+' · '+layer.reference_ids.join(', ')));
        svg.append(background,svgElement('text',{x:16,y:top+22,'font-size':14,'font-weight':700},layer.id+' · '+layer.name));
        labels.forEach((label,j) => svg.append(svgElement('text',{x:20+(j%3)*190,y:top+49+Math.floor(j/3)*22},label)));
    });
    svg.append(svgElement('text',{x:16,y:292},'Conceptual positions · '+architectureLayers[0].reference_ids[0]));
}

function initializeLayeredControls() {
    for (const [key,label] of moduleSwitches) {
        const row = document.createElement('label');
        const input = document.createElement('input');
        input.id = key;
        input.type = 'checkbox';
        input.checked = AdhesionMatrix.defaults[key];
        row.append(input,document.createTextNode(' '+label));
        $('layerSwitches').append(row);
    }
    const components = [...new Set(ruleList.flatMap(rule => rule.components))].sort();
    for (const component of components) $('mechanismProtein').add(new Option(component,component));
    $('mechanismProtein').onchange = inspectMechanism;
    $('mechanismRule').onchange = inspectMechanism;
    for (const layer of architectureLayers) {
        const card = document.createElement('div');
        card.className = 'zoneCard';
        const title = document.createElement('strong');
        title.textContent = layer.id+' · '+layer.name;
        const role = document.createElement('p');
        role.textContent = layer.components.join(' · ');
        card.append(title,role);
        for (const rid of layer.reference_ids) {
            const anchor = document.createElement('a');
            anchor.textContent = rid;
            anchor.href = simulatorEvidence.references[rid].doi_url;
            anchor.target = '_blank';
            anchor.rel = 'noopener';
            card.append(anchor,document.createTextNode(' '));
        }
        $('zoneCards').append(card);
    }
    inspectMechanism();
}
