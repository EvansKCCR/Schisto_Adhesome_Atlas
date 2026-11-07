/* Seeded dimensionless adhesion lattice. The structural I–T–V matrix remains 3 × 3. */
const AdhesionMatrix = (() => {
    const VERSION = 'adhesion-lattice-4.0';
    const I = 0, T = 1, V = 2;
    const clip = x => Math.max(0, Math.min(1, x));
    const defaults = {
        grid:5, integrins:20, steps:50, seed:2008,
        ligand:.4, integrinAvailability:1, talinAvailability:1, vinculinAvailability:1,
        load:.2, threshold:.8, alpha:5, ruptureForce:3, off:.05, feedback:.15,
        actinProbability:.6, reinforcement:.5, allowIV:false,
        fakGate:1, bridgeGate:1, vkrGate:1, migrationGate:1, growthGate:1, cytoskeletonGate:1,
        layeredMechanics:true, talinActinProbability:.6, relaxation:.15,
        enableIPP:true, kindlinProbability:.6, ilkProbability:.55, pinchProbability:.6,
        parvinProbability:.55, ippActinProbability:.55, ippStabilization:.3,
        enableVKR:true, paxillinProbability:.35, enableActinRegulation:true, actinRegulationProbability:.4,
        enableKinaseContext:false, gonadalGate:.5, pkcMapkGate:.5
    };
    const probabilitiesFields = [
        'ligand','integrinAvailability','talinAvailability','vinculinAvailability','off','actinProbability',
        'fakGate','bridgeGate','vkrGate','migrationGate','growthGate','cytoskeletonGate',
        'talinActinProbability','kindlinProbability','ilkProbability','pinchProbability','parvinProbability',
        'ippActinProbability','paxillinProbability','actinRegulationProbability','gonadalGate','pkcMapkGate'
    ];
    const siteFields = ['talinActin','kindlin','ilk','pinch','parvin','ipp','ippActin','nck','vkr1',
        'paxillin','alphaActinin','zyxinAjuba','enaVasp'];
    const projectedFields = ['mechanics','cytoskeleton','fak','bridge','vkr','protrusion',
        'traction','erk','akt','survival','gonadalContext','pkcMapkContext'];
    const emptySite = () => Object.fromEntries(siteFields.map(key => [key,false]));

    function rng(seed) {
        let a = seed >>> 0;
        return () => {
            a = (a + 0x6D2B79F5) >>> 0;
            let t = a;
            t = Math.imul(t ^ (t >>> 15), t | 1);
            t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
            return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
        };
    }

    function matrix(it, tv, iv) { return [[0,it,iv],[it,0,tv],[iv,tv,0]]; }

    function validate(p, W) {
        for (const key of ['grid','integrins','steps','seed']) {
            if (!Number.isInteger(p[key])) throw Error(key + ' must be an integer');
        }
        if (p.grid < 2 || p.grid > 12 || p.integrins < 1 || p.integrins > p.grid ** 2 ||
            p.steps < 1 || p.steps > 300 || p.seed < 0 || p.seed > 4294967295) {
            throw Error('Check grid (2–12), receptor count, steps (1–300) and seed');
        }
        for (const key of probabilitiesFields) {
            if (!Number.isFinite(p[key]) || p[key] < 0 || p[key] > 1) throw Error(key + ' must lie in [0,1]');
        }
        for (const key of ['load','threshold','alpha','ruptureForce','feedback','reinforcement','relaxation','ippStabilization']) {
            if (!Number.isFinite(p[key]) || p[key] < 0) throw Error(key + ' must be finite and nonnegative');
        }
        if (p.alpha < 1 || p.ruptureForce <= 0) throw Error('Amplification must be ≥1 and rupture force >0');
        if (!Array.isArray(W) || W.length !== 3 || W.some(row => !Array.isArray(row) || row.length !== 3)) {
            throw Error('W must be 3 × 3');
        }
        for (let i=0; i<3; i++) for (let j=0; j<3; j++) {
            if (!Number.isFinite(W[i][j]) || W[i][j] < 0 || W[i][j] > 1 || W[i][j] !== W[j][i] ||
                (i === j && W[i][j] !== 0)) throw Error('W must be symmetric, normalized and have zero diagonal');
        }
    }

    function assembled(A) {
        return A[I][I] === 1 && A[T][T] === 1 && A[V][V] === 1 && A[I][T] === 1 && A[T][V] === 1;
    }

    function probabilities(p, W, force, talinPresent) {
        const gain = force >= p.threshold ? p.alpha : 1;
        return {
            talin:talinPresent ? 0 : clip(.5 * W[I][T] * p.talinAvailability),
            vinculin:talinPresent ? clip(.4 * W[T][V] * p.vinculinAvailability * gain) : 0
        };
    }

    function signalling(A, force, actin, p, site) {
        const root = A[I][I];
        const load = root ? force / (force + Math.max(p.threshold,1e-9)) : 0;
        const forceLink = Boolean(actin || site.ippActin);
        const fak = root * load * p.fakGate;
        const bridge = Number(site.nck);
        const vkr = Number(site.vkr1);
        const cytoskeleton = Number(forceLink || site.talinActin) * p.cytoskeletonGate;
        return {
            ...site, L1:root, L2:(A[T][T] + A[V][V] + Number(site.ipp))/3, L3:Number(cytoskeleton > 0),
            mechanics:Number(forceLink) * load, cytoskeleton, fak, bridge, vkr,
            protrusion:root * (1-load) * p.fakGate * p.migrationGate,
            traction:Number(forceLink) * load * p.migrationGate,
            erk:Math.max(fak,vkr) * p.growthGate,
            akt:vkr * p.growthGate, survival:root * (fak+vkr)/2 * p.growthGate,
            gonadalContext:p.enableKinaseContext ? root * Math.max(fak,cytoskeleton) * p.gonadalGate : 0,
            pkcMapkContext:p.enableKinaseContext ? root * Math.max(fak,vkr) * p.pkcMapkGate : 0,
        };
    }

    function recruitScaffold(site, p, draws) {
        // M08–M13. PINCH and parvin use independent ILK interfaces.
        if (p.enableIPP && draws[0] < p.kindlinProbability) site.kindlin = true;
        const bridgeEnabled = p.enableVKR && p.bridgeGate > 0;
        if ((site.kindlin || bridgeEnabled) && draws[1] < p.ilkProbability) site.ilk = true;
        if (site.ilk && draws[2] < p.pinchProbability) site.pinch = true;
        if (site.kindlin && site.ilk && draws[3] < p.parvinProbability) site.parvin = true;
        site.ipp = Boolean(p.enableIPP && site.kindlin && site.ilk && site.pinch && site.parvin);
        if (site.ipp && draws[4] < p.ippActinProbability) site.ippActin = true;
        if (bridgeEnabled && site.ilk && site.pinch && draws[5] < p.bridgeGate) site.nck = true;
        if (site.nck && draws[6] < p.vkrGate) site.vkr1 = true;
    }

    function simulate(parameters, W) {
        const p = {...defaults,...parameters};
        validate(p,W);
        const random = rng(p.seed);
        const extensionRandom = rng(p.seed ^ 0xA5C3E91B);
        const N = p.grid * p.grid;
        const positions = Array.from({length:N}, (_, i) => i);
        for (let i=N-1; i>0; i--) {
            const j = Math.floor(random()*(i+1));
            [positions[i],positions[j]] = [positions[j],positions[i]];
        }
        const eligible = new Set(positions.slice(0,p.integrins));
        const net = Array.from({length:N}, () => matrix(0,0,0));
        const states = Array.from({length:N}, emptySite);
        const force = Array(N).fill(0), actin = Array(N).fill(false), snapshots = [];
        let ruptures = 0, attachments = 0;
        function snapshot(step) {
            const bound = net.filter(A => A[I][I]).length;
            const talin = net.filter(A => A[T][T]).length;
            const mature = net.filter(assembled).length;
            const actinCount = actin.filter(Boolean).length;
            const exposed = net.filter((A,s) => A[T][T] && force[s] >= p.threshold).length;
            const local = net.map((A,s) => signalling(A,force[s],actin[s],p,states[s]));
            const metrics = {
                step,bound,talin,mature,actin:actinCount,exposed,ruptures,attachments,
                meanForce:bound ? force.reduce((a,b) => a+b,0)/bound : 0,
                boundPercent:100*bound/p.integrins, maturePercent:100*mature/p.integrins,
                actinPercent:100*actinCount/p.integrins,
            };
            for (const key of siteFields) metrics[key+'Count'] = states.filter(state => state[key]).length;
            metrics.ippPercent = 100 * metrics.ippCount / p.integrins;
            for (const key of projectedFields) metrics[key] = 100*local.reduce((sum,s) => sum+s[key],0)/p.integrins;
            const lattice = Array.from({length:p.grid},(_,x) => Array.from({length:p.grid},(_,y) =>
                net[x*p.grid+y].map(row => row.slice())));
            snapshots.push({step,adhesome_lattice:lattice,force:force.slice(),actin:actin.slice(),
                metrics,nanoscale_state:local});
        }
        snapshot(0);
        for (let step=1; step<=p.steps; step++) {
            for (let s=0; s<N; s++) {
                // Both streams have fixed draws per site and step for paired runs.
                const draws = Array.from({length:6},() => random());
                const extra = Array.from({length:12},() => extensionRandom());
                if (!eligible.has(s)) continue;
                const A = net[s], site = states[s];
                if (!A[I][I]) {
                    if (draws[0] < clip(p.ligand*p.integrinAvailability)) {
                        A[I][I] = 1;
                        force[s] = .1;
                        attachments++;
                    }
                    continue;
                }
                const linked = site.talinActin || site.ippActin || actin[s];
                if (!p.layeredMechanics || linked) force[s] += p.load + (actin[s] ? p.feedback : 0);
                else force[s] = Math.max(0,force[s]-p.relaxation);
                const reinforcement = (actin[s] && assembled(A) ? p.reinforcement : 0) +
                    (site.ippActin ? p.ippStabilization : 0);
                if (force[s] > p.ruptureForce*(1+reinforcement) || draws[1] < p.off) {
                    net[s] = matrix(0,0,0);
                    states[s] = emptySite();
                    force[s] = 0;
                    actin[s] = false;
                    ruptures++;
                    continue;
                }
                if (!A[T][T] && draws[2] < probabilities(p,W,force[s],false).talin) {
                    A[I][T] = A[T][I] = A[T][T] = 1;
                }
                if (p.layeredMechanics && A[T][T] && extra[7] < p.talinActinProbability) site.talinActin = true;
                if (A[T][T] && !A[V][V] && draws[3] < probabilities(p,W,force[s],true).vinculin) {
                    A[T][V] = A[V][T] = A[V][V] = 1;
                }
                if (assembled(A)) {
                    if (p.allowIV && draws[4] < clip(.5*W[I][V])) A[I][V] = A[V][I] = 1;
                    if (draws[5] < p.actinProbability) actin[s] = true;
                }
                recruitScaffold(site,p,extra);
                if ((site.kindlin || (p.fakGate > 0 && force[s] > 0)) && extra[8] < p.paxillinProbability) site.paxillin = true;
                if (p.enableActinRegulation && (site.talinActin || site.ippActin || actin[s])) {
                    const chance = p.actinRegulationProbability * p.cytoskeletonGate;
                    if (extra[9] < chance) site.alphaActinin = true;
                    if (extra[10] < chance) site.zyxinAjuba = true;
                    if (extra[11] < chance) site.enaVasp = true;
                }
            }
            snapshot(step);
        }
        return {engine_version:VERSION,parameters:p,W,
            site_positions:positions.slice(0,p.integrins).map(s => [Math.floor(s/p.grid),s%p.grid]),snapshots};
    }
    return {VERSION,defaults,I,T,V,matrix,validate,assembled,probabilities,simulate,siteFields};
})();
