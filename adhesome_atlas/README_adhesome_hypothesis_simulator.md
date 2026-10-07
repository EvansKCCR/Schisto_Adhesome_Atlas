# Schistosome Integrin-Adhesome Matrix Simulator

The simulator reconstructs stochastic nascent adhesion complexes at individual ECM lattice sites. It adapts the supplied `Framework.py` into a spatial, inspectable and reproducible model linked to the atlas family map. The standalone file is `schistosome_integrin_adhesome_hypothesis_simulator.html`; all simulation and SVG rendering code is contained in that HTML.

## Nanoscale organization and functional hubs

The map and simulator share `nanoscale_architecture.py`, with three schematic zones:

| Zone | Principal families | Function |
| --- | --- | --- |
| L1 · Integrin signalling | Integrin αβ, FAK/Src, paxillin, adaptors; membrane SmVKR1 context | Receptor engagement and force-dependent signalling |
| L2 · Force transduction | Talin, kindlin, vinculin | Receptor activation, talin exposure and clutch reinforcement |
| L3 · Actin regulation | ILK–PINCH, α-actinin, filamin, zyxin, cofilin, profilin, F-actin | Scaffold coupling, cross-linking and remodelling |

This functional organization follows [Kanchanawong et al. (2010)](https://doi.org/10.1038/nature09621) and the talin force-exposure mechanism of [del Rio et al. (2009)](https://doi.org/10.1126/science.1162912). It is a reference schematic, not measured schistosome nanometre coordinates. ILK–PINCH placement is functional context; unresolved parvin and VASP remain reference components. The parasite reproductive branch uses the Smβ-Int1–ILK–PINCH–Nck2–SmVKR1 relationship described by [Gelmedin et al. (2017)](https://doi.org/10.1371/journal.ppat.1006147).

Five selectable functional hubs connect these zones: **mechanotransduction/tensile strength**, **cytoskeletal organization**, **migration/traction**, **growth/survival**, and **reproduction/development**. Each system displays a selected-site zone schematic and five module cards alongside its lattice. The local structural matrix retains I/T/V; other families contribute contextual or gated projections rather than invented molecular occupancy.

## Local matrices and components

Every site stores a binary 3 × 3 matrix A, with components ordered as:

1. **I:** the putative integrin αβ receptor, using the β-tail interface for intracellular family-pair mapping;
2. **T:** talin;
3. **V:** vinculin.

The diagonal of A records component occupancy, while reciprocal off-diagonal entries record assembled associations. Diagonal entries are not self-binding interactions. The full `adhesome_lattice` has shape `(grid, grid, 3, 3)` and is retained for every timestep.

Receptor positions are sampled without replacement so each lattice site has one owner. Ligand anchoring sets AII = 1. Talin recruitment sets AIT = ATI = ATT = 1. Vinculin recruitment requires talin and sets ATV = AVT = AVV = 1. Full I–T–V assembly requires all three occupied components and both I–T and T–V bonds. The optional I–V association can be added after assembly; it does not bypass the talin-dependent recruitment pathway.

## Static topology W and evidence

W is symmetric, normalized to [0,1], and has a zero diagonal. Its three pair weights are exposed in the controls and local inspector.

| Pair | Family mapping | Framework assumption |
| --- | --- | ---: |
| I–T | Supported integrin β ↔ supported talin | 0.85 |
| T–V | Supported talin ↔ supported vinculin | 0.30 |
| I–V | Supported integrin β ↔ supported vinculin | 0.05 |

The embedded atlas supplies uniquely mapped STRING protein associations from the current network exports. For each species and family pair, W uses the maximum mapped `combined_score`; the pan-schistosome setting uses the maximum across species. The provenance table and JSON export retain the actual protein pairs, STRING identifiers, species, scores and file paths. Supported family assignments include the atlas's parasite-specific supported-cluster category.

When a mapped pair is unavailable, its Framework assumption is shown explicitly as a fallback. Users can select all Framework assumptions or enter custom weights. In standalone mode, no atlas mapping is available and all weights use Framework assumptions.

STRING confidence is an association-confidence input, not a measured binding affinity or an experimentally calibrated recruitment probability. The reference panel uses editable canonical assumptions; selecting a reference proteome changes its evolutionary-context label and does not invent reference-specific kinetic parameters.

## Recruitment and mechanics

The engine uses probabilities bounded to [0,1]:

```text
P(anchor) = clip(ligand_probability × integrin_availability)
P(T)      = clip(0.5 × WIT × talin_availability)
gain      = α if talin is present and local force ≥ threshold; otherwise 1
P(V)      = clip(0.4 × WTV × vinculin_availability × gain)
```

The effective T–V weight can exceed 1 after amplification; the resulting probability is clipped to 1. Static W remains normalized. Newly anchored integrins enter recruitment at the next timestep; talin and vinculin can subsequently be recruited sequentially within one timestep.

At an anchored site:

```text
F(t+1) = F(t) + external_load + feedback × actin_attached(t)
```

An assembled I–T–V site can attach actin with the specified probability. Actin then contributes additional force on the next timestep, completing the feedback loop. The engine checks overload and basal dissociation before recruitment. Either event clears the entire local matrix, force and actin state; later ligand attachment can initialize a new complex at that site. Higher load can therefore accelerate talin exposure and also promote rupture.

Vinculin–actin reinforcement raises the overload threshold of an assembled, actin-attached clutch:

```text
effective_rupture_force = rupture_force × (1 + reinforcement)
```

Other sites retain the base rupture threshold. The default reinforcement is 0.5; this is an editable mechanical assumption.

Force values are normalized assumed units. No conversion to pN, fitted binding energy or tissue mechanics is claimed.

## Default parameters

| Parameter | Default |
| --- | ---: |
| Lattice | 5 × 5 |
| Receptor sites | 20 |
| Timesteps | 50 |
| Random seed | 2008 |
| Ligand-anchoring probability | 0.4 |
| I/T/V availability multipliers | 1 |
| External force load per timestep | 0.2 |
| Talin-exposure threshold | 0.8 |
| Mechanical multiplier α | 5 |
| Overload rupture force | 3 |
| Basal dissociation probability | 0.05 |
| Actin attachment probability | 0.6 |
| Additional actin force feedback | 0.15 |
| Clutch reinforcement | 0.5 |
| Downstream projection gates | 1 (reference VKR1 gate = 0) |

The structural defaults and W assumptions follow the supplied Framework; the actin-attachment and feedback controls make its proposed feedback-amplification phase explicit.

## Inspecting the simulation

Both SVG lattice panels display a miniature I–T–V graph at every site. Solid edges show realized associations. Red site borders indicate talin exposure and a star indicates actin attachment. Click a site to inspect the matching coordinate in both systems, including local A, static W, effective WTV, force and recruitment probabilities. The timeline scrubs all snapshots; playback reveals assembly, maturation and rupture. Curves show receptor occupancy, assembled I–T–V sites and actin-attached sites, expressed as fractions of configured receptor sites.

Both systems share seeded receptor placement and random variates at each site/timestep. Matching structural parameters and W therefore give identical structural trajectories. This makes differences attributable to the selected topology or model parameters. Family inventory counts describe the catalogue; they do not determine simulated receptor copy number or recruitment rates.

## Linking the current adhesome network

Select a node in the Introduction map and choose **Explore downstream simulation**. The link sets an explicit scenario:

- Collagen-like and laminin-like nodes reduce ligand availability.
- Integrin nodes reduce αβ receptor availability.
- Talin and vinculin reduce their respective recruitment multipliers.
- Kindlin uses an upstream receptor-availability proxy.
- Actin reduces actin attachment and feedback; α-actinin and filamin use force-transfer proxies.
- Host-vascular context reduces external force loading.
- FAK/Src, ILK/PINCH/Nck and VKR1 alter their named downstream projection gates.

FAK/Src follows force-dependent signalling at ligand-anchored receptors. ILK–PINCH–Nck2 and VKR1 follow assembled-site coupling; the canonical reference has no VKR1 branch. Paxillin/PTP-PEST, Shc/Grb2 and cofilin/profilin/zyxin selections control migration, growth/survival and cytoskeletal projection gates respectively. These gates do not alter core I–T–V matrices. Unresolved parvin displays the baseline with reference context.

## Functional projection formulas

For each site, let `I` be receptor occupancy, `M` complete I–T–V assembly, `C` assembled plus actin-attached clutch, `B` actin attachment, and `q = F / (F + max(threshold, 10⁻⁹))` for an occupied receptor (otherwise zero). Gates are in [0,1].

```text
mechanics     = C × q
cytoskeleton  = B × cytoskeleton_gate
FAK/Src       = I × q × fak_gate
bridge        = M × bridge_gate
VKR1          = bridge × vkr_gate
protrusion    = I × (1 − q) × fak_gate × migration_gate
traction      = C × q × migration_gate
ERK           = FAK/Src × growth_gate
Akt           = bridge × B × growth_gate
survival      = I × (FAK/Src + bridge) / 2 × growth_gate
```

Cards show averages as percentages of configured receptor sites. These are dimensionless functional projections: protrusion/traction distinguish low-load and high-load states; ERK/Akt/survival express coupling without calculating migration distance, proliferation, survival probability or reproductive output. Rac/Cdc42–Arp2/3, Rho–ROCK–myosin and Akt–mTOR remain reference pathways. The model does not assign phosphorylation sites or kinase substrates.

The linked banner compares the selected scenario with a same-seed default-parameter baseline using the same schistosome W. Manual changes are retained when returning between map and simulator tabs. Selecting another map node resets the scenario to its defined controls.

Selecting a candidate supplies its species and identifier context. W remains the selected species' family-level aggregate rather than a fitted weight for that individual protein. Downloads retain the last completed run, including its frozen source metadata; changed controls take effect after pressing **Run matrix simulation**.

## Reproducibility and exports

The engine version is `adhesion-lattice-3.0` and export schema is version 3; the random generator is Mulberry32. **Download reproducible run · JSON** includes all parameters, W, topology provenance, reference label, selected map context, shared zone/function definitions, receptor positions and complete timestep histories of the 4D tensor, force, actin and per-site `nanoscale_state` for both systems. **Download trajectories · CSV** includes the functional projections with timestep summaries. The engine is deterministic for a given parameter set, W and seed.

Validation checks cover seeded replay, unique receptor ownership, binary symmetric matrices, recruitment dependencies, probability clipping, complete rupture resets, force-feedback timing, clutch reinforcement, bounded zone projections, load-dependent protrusion/traction and separation of structural matrices from downstream gates. Run `python test_matrix_simulator.py` to exercise the embedded engine directly with Node.js.
