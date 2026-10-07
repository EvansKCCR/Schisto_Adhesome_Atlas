# Schisto-Adhesome Atlas — integrin–adhesome catalogue

A local, read-only Streamlit atlas of every file in the `adhesome_atlas` directory.

## Launch in WSL (Linux)

In your WSL terminal, run:

```bash
cd /mnt/c/Users/eaasa/Desktop/Evans_PHD_Thesis/Integrin_analysis/adhesome_atlas
bash launch_atlas.sh --setup
```

The first run creates `~/.venvs/schistoatlas`, installs dependencies there, and starts the atlas. Use Python 3.12 or newer. If Python venv support is missing on Ubuntu/Debian, install it with `sudo apt install python3-venv`.

For later launches:

```bash
bash launch_atlas.sh
```

Open http://localhost:8501 in your Windows browser. Stop with Ctrl+C. Stop the existing Windows atlas before using the same port, or choose another port with `ATLAS_PORT=8502 bash launch_atlas.sh` and open http://localhost:8502.

The Linux environment is separate from the Windows `.venv`; do not activate the Windows environment in WSL. Override its location with `ATLAS_VENV=/path/to/linux/venv bash launch_atlas.sh --setup`. The app resolves source files relative to its own directory, so the whole project can also be copied to the Linux filesystem without changing Python paths. Keep the `adhesome_atlas` directory, `.streamlit` and the launcher together.

## Launch in Windows (optional)

From the project root in PowerShell:

```powershell
.\launch_atlas.ps1
```

Then open http://localhost:8501. Stop the server with Ctrl+C.

For a fresh installation, use Python 3.12 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r adhesome_atlas/requirements.txt
.\.venv\Scripts\python.exe -m streamlit run adhesome_atlas/app.py
```

## Explore

- **Introduction:** about the atlas, collection summary counts, prototype interpretation, interactive family map and evidence-stratified hypothesis downloads.
- **Components:** summary statistics, summary graphs, candidate tables, audited family decisions, species comparisons and exports.
- **Interactions:** draggable SVG STRING, unified and orthogroup networks, score thresholds, neighborhood focus, family/localization colors, interaction and node tables, functional annotations and network statistics. Node names can be hidden, placed outside, or centered; unconnected nodes can be hidden and rearranged layouts export as SVG.
- **Comments & feedback:** prepare an email draft for catalogue corrections, suggestions, and scientific queries, or use the direct curator email link. Form entries are not stored by the atlas.
- **Source Library:** every supplied data file and workbook sheet, original downloads and reconciliation checks.
- **Protein dossier / Motif explorer:** positional annotations, sequence provenance and motif evidence.

## Network interpretation

Networks read only `adhesome_network/<species>/*_string_interactions.tsv`. Reverse duplicates are collapsed by unordered STRING identifier pairs, retaining the highest combined score. Short exports remain accessible in Source Library but are not added to the graph. Coordinates retain the exported STRING layout; degrees are recalculated after filtering. Network controls are independent of component filters.

Family and DeepLoc colors use exact species-qualified catalogue ID matches. No aliases are guessed from similar-looking IDs or annotation text. Unmapped nodes remain gray. STRING localization colors highlight membership in a user-selected COMPARTMENTS term; the complete term set stays available in hover details and tables. Original STRING colors are also available, without assigning them an unsupported biological meaning. Associations do not necessarily establish direct physical binding or species-specific experimental validation.

All data now comes from this folder: `files/`, `family_specific_candidate_fasta/`, `topology_localization_cdd/`, `resource_library/` and `adhesome_network/`. The old `06_annotation_visualization` location is not consulted. Missing sequences are reported; exports include only available sequences.

## Data and interpretation

The three collections are intentionally separate. Pipeline v4's `Audited_family_assignment` worksheet contains 529 unique schistosome proteins: 198 retained family assignments, 29 parasite-specific supported-cluster assignments (`Retain provisionally`), 45 provisional candidates (`Family-level provisional only`), and 257 unassigned proteins. Thus 227 are displayed as supported and 45 as provisional. Its `Screening_hypothesis` worksheet preserves 1,091 pre-collapse family hypotheses. The separate FN3 review contains 87 proteins; the full screening workbook contains 4,997 hypothesis rows covering 3,305 unique protein IDs. Counts on the prototype map refer to all 272 retained adhesome family assignments.

IDs in the audited adhesome worksheet already carry the species prefix; the loader adds one only when absent. Species names are mapped from Shae, Sjap and Sman. Screening, assigned and audited family fields are preserved. Source workbooks are never rewritten. All FASTAs contribute sequence provenance; identical repeated sequences are deduplicated. Conflicting sequences are exposed in the audit. All raw CSV, SignalP, CDD and 3line files are parsed and available in dossiers and the source library.

The current audit retains six supported PINCH-like proteins, including three parasite-specific supported-cluster records, distinct from paxillin-like proteins. No parvin family assignment is retained. The reviewed family drives catalogue browsing, component summaries, prioritization labels and the interactive map. The workbook's `Pipeline_summary`, `Screening_hypothesis` and `Motif_annotations` sheets, together with `integrated_adhesome_pipeline.py`, document the updated audit.

Motifs are reported regex candidates, not validated interactions. Network graphs use only supplied STRING edges. FN3-containing proteins are not automatically interpreted as fibronectin orthologues. Relative representation uses distinct proteins in the filtered collection as its denominator; it is not normalized to whole proteomes and does not measure expression, enrichment, or evolutionary expansion. Missing annotation is not biological absence. CDD tracks show specific hits; raw tables preserve all hit types. Residue coordinates are 1-based and inclusive.

Files are read directly on launch and cached using relative paths, modification times and sizes. The sidebar reload button clears the cache after source updates. All processing stays local; no service credentials or remote data calls are used.

## Validation

WSL:

```bash
~/.venvs/schistoatlas/bin/python test_atlas.py
```

Windows:

```powershell
.\.venv\Scripts\python.exe adhesome_atlas/test_atlas.py
```

The validation checks sequence coverage and lengths, topology lengths, motif coordinates, deduplicated FASTA exports, every collection/view combination and empty/literal-search behavior using Streamlit AppTest. API reference: https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest


## Unified reconstruction update

Interactions opens the six-layer reconstruction and retains the species STRING explorer. The default pan view combines separate species proteins; it does not invent orthology merges. The Orthogroup consensus view reads the current `Audited_family_assignment` and `Candidates` worksheets from the two workbooks in `files/`. By default it includes supported and provisional family assignments; unassigned audit proteins can be added explicitly as context. Workbook orthogroups without mapped STRING proteins remain visible as isolates. An inter-orthogroup edge is drawn only when the supplied STRING network contains a retained association between proteins uniquely mapped to the respective groups. Associations within one orthogroup remain in a separate table.

The consensus graph supports filters for source collection, family, member species, association class and evidence, association species support, identifier or protein search, and one- or two-hop neighborhoods. Nodes can be colored by family, species coverage, collection or topological community, and sized by membership, degree or betweenness. Clicking or selecting an orthogroup reveals its source protein assignments and linked groups. The active workbook panel lists the exact worksheets and short SHA-256 fingerprints, making deployed source versions checkable. The node and edge tables, including workbook-only status and source provenance, are downloadable.

The unified graph can be filtered by STRING score, relationship/evidence class, protein family, adhesion layer, identifier, minimum degree, one- or two-hop neighborhood and greedy-modularity community. Choose layered or force-directed layout (up to 400 displayed proteins), color nodes by layer, species, community or family, and size them by degree, betweenness or closeness. The SVG network supports node dragging, inspection, centered names, position reset and vector export. Filters rebuild the displayed graph and all topology metrics; they do not change source exports.

The topology workspace reports normalized betweenness, Wasserman–Faust corrected closeness, farness, reachable proteins, local clustering coefficient, k-core, connected component and greedy-modularity community. Centrality charts rank potential hubs and bottlenecks. For up to 40 selected proteins, shortest-path distances are computed through the complete displayed graph and adjacency shows direct retained associations; disconnected pairs appear blank. Community-by-layer, k-core and local-clustering plots support module exploration. An optional Girvan–Newman edge-betweenness split is available for filtered subnetworks of at most 60 proteins. Matrices and topology tables can be downloaded as CSV.

### Prototype adhesome presentation and hypothesis builder

The Introduction keeps the interactive map and hypothesis builder. `Schistosome_adhesome_interactive.html` separates extracellular ligands, the integrin receptor, membrane-proximal machinery, actin coupling, signalling and cytoskeleton. Its family counts match the audited worksheet. Ligand classes target a virtual integrin αβ heterodimer linked to both subunit families; no specific protein pair is assigned. PINCH-like remains separate from paxillin-like. The PINCH–ILK and PINCH–Nck2 links are marked as experimentally supported *S. mansoni* complex associations from [Gelmedin et al. (2017)](https://doi.org/10.1371/journal.ppat.1006147), distinct from reference-inferred links. SmVKR1 is a membrane-receptor evidence-context node, host-vascular input is a hypothesis-only context node, and parvin remains an unresolved reference node. Select a family or protein in Streamlit or click a node or edge to inspect candidate records and provenance. Each node panel offers **Explore downstream simulation**, which opens a matched qualitative scenario in the same workspace while retaining a map tab. Nodes without a direct simulator control show the unchanged baseline with an explicit explanation. The page embeds `README_schistosome_adhesome_interactive.md` as its interpretation guide.

The hypothesis builder filters the 198 core retained, 29 parasite-specific supported-cluster and 45 provisional audited rows by family, evidence tier and relationship class. Downloads include a JSON bundle, candidate CSV and family-relationship CSV. The relationship table reads edges directly from the current HTML and carries relation, evidence class, reference, transfer basis, species support and directionality. Ligand–receptor relationships require both integrin subunit families. The selected Nck–SmVKR1 and host-vascular–integrin edges are included with `context_only=true` and no catalogue candidate count; parvin edges remain optional and `reference_only=true`. The FN3 review remains separately accessible in its dedicated atlas view.

`schistosome_integrin_adhesome_hypothesis_simulator.html` is linked from the **Introduction** map and remains available from Source Library. The seeded stochastic model stores a binary 3 × 3 I–T–V adjacency matrix at every ECM lattice site. Uniquely mapped supported-family STRING associations supply W; missing pairs use explicitly labelled Framework assumptions. Local force exposes talin, amplifies T–V recruitment, and closes an actin-force feedback loop once the complex assembles. The schistosome and canonical-reference SVG lattices share random variates, with inspectable local matrices and complete replayable JSON/CSV exports. The canonical reference uses editable shared topology assumptions; reference selection changes its context label. The map and simulator share three schematic zones: integrin signalling, force transduction and actin regulation. Zone/function selectors organize the map around mechanics, cytoskeletal organization, migration/traction, growth/survival and the ILK–PINCH–Nck2–VKR1 reproductive branch. Actin-attached I–T–V clutches increase the rupture threshold; force-dependent FAK/Src, protrusion/traction, ERK/Akt/survival and receptor-coupling readouts appear in selected-site SVG schematics and functional cards. Version 3 JSON retains the architecture and per-site functional states. `README_adhesome_hypothesis_simulator.md` documents the formulas and controls, and `test_matrix_simulator.py` validates the embedded engine.

Degree, normalized betweenness, corrected closeness, communities, interface counts and complete-case seven-feature prioritization are downloadable. Missing phylogeny, motif conservation or host-divergence evidence remains unassessed. See `adhesome_network/curation/README.md` for the input schema and interpretation rules.

After this update, run `bash launch_atlas.sh --setup` from inside `adhesome_atlas` to install NetworkX and start the app. The launcher now resolves `app.py` and `requirements.txt` in its own folder. Run `~/.venvs/schistoatlas/bin/python test_reconstruction.py` for reconstruction validation.


## Orthology-aware catalogue update

Updated candidate workbooks are read with their orthology report sheets, direct-orthologue relationships and HOG copy counts. Candidate worksheet detection tolerates the FN3 worksheet rename. Excel temporary lock files are ignored. Original source statuses and rows remain unchanged.

Components now includes **Orthology & evidence** and **FN3 / RPTP priorities**. Orthology supplies evolutionary context only. The review hierarchy is orthology, architecture, topology/localization and motif context, followed by biological review. A conserved generic kinase or cytoskeletal orthologue is never automatically called an adhesome member. Review stages mark the first unresolved step and do not exclude records. Domain-rule matches and region-supported motif predictions are provisional evidence, not validated adhesion specificity. Missing motifs are treated as missing context, not proof of absence; family-specific exceptions need biological review.

The FN3 view keeps three independent priority groups: ten sampled-HOG Schistosoma-only single-pass adhesion-receptor-like proteins; four sampled-HOG Schistosoma-only RPTP-like proteins; and ten shared-HOG secreted-FN3-assigned proteins with copies in all three schistosomes. Other 63 FN3 candidates remain separate. The groups use the revised architecture-specific FN3 family assignments. No reviewed protein meets the workbook's strict canonical fibronectin architecture. Schistosoma-only refers to sampled references, not universal taxonomic restriction.

Network integration accepts exact STRING node IDs or unique exact tokens in the supplied alias field, scoped to species. Ambiguous tokens stay unresolved. Alias-supported mappings can now attach workbook orthogroups to network proteins; sharing a family name is never a mapping rule. Human orthologues prompt selectivity assessment, without generating a host-divergence score. Source HOG species copy-count coverage is used for the conservation feature when available; complete numerical scores remain insufficient to establish adhesome membership.

The Source Library now includes PSI-MI XML and `.all` enrichment exports. The species STRING explorer displays additional protein annotations, evidence-channel references and supplied enrichment. Original annotation/domain-URL headers are preserved despite their apparent swap in the protein-annotation exports. Enrichment statistics apply to the original exported network, not the interactive filtered graph. XML edges are not counted again.

Run `~/.venvs/schistoatlas/bin/python test_orthology.py` inside this folder to validate the evidence hierarchy, priority groups, alias mapping, consensus and new resource views.


### STRING query mapping exports
The atlas discovers species-named `*_string_mapping.tsv` files recursively under `adhesome_network`, validates STRING taxon prefixes, and joins query IDs to exact species-qualified catalogue IDs. Original files stay in place, including the Sman export supplied in the Sjap folder. Identity, bit score, query alternatives and relative source paths remain in the node/topology downloads. Unique supplied mappings support catalogue annotation lookup; many-query or conflicting mappings remain unresolved. No highest-score winner is selected. Identity alone does not establish orthology, adhesome membership or functional equivalence. Orthogroups and HOG species coverage come from the linked workbook; layers retain their stated catalogue/compartment basis. Updated exports resolve 146 of 150 nodes, with 146 orthogroup-annotated nodes and four ambiguous nodes.


### Source-derived prioritization features
`prioritization_evidence.py` joins motif hits by exact sequence ID and family, using `adhesome_candidates_list.xlsx / Motif_annotations` and the FN3 workbook hit sheet. The main topology table shows biological summaries; mapping audit fields remain in the full CSV and reconstruction inputs.

- Domain architecture: workbook domain-type coverage fraction, with boolean domain-match fallback.
- Topology compatibility: 1 for agreement with the assigned class, 0 for recorded discordance, missing for unassessed cases.
- Motif conservation: aligned amino-acid identity across the motif peptide in other Schistosoma species. The complete peptide must occur uniquely in the ungapped trimmed alignment. Within-species homologues are averaged, then species are averaged. This measures residue conservation rather than retention of a degenerate ELM pattern. Family-specific hit matching prevents cross-family evidence transfer.
- Phylogenetic support: smaller of SH-aLRT and UFBoot divided by 100 for the smallest represented multispecies Schistosoma clade containing the tip. No qualifying branch means missing, not zero.
- Host divergence: one minus aligned amino-acid identity to the closest human homologue in the retained gene-tree alignments, excluding gaps and ambiguous residues. This is alignment-based homologue divergence, not whole-protein identity or an experimental selectivity measurement; paired-site counts and host IDs are retained.

For multiple qualifying motifs, runs or protein-family rows, the minimum available score is used. Every derived feature has a basis column. Cited manual feature values override derived values. The seven-feature mean remains available only for complete records; the number of available features and reasons for missing values accompany incomplete records. Original workbook assignments and network topology remain unchanged.


The Motif explorer reads `adhesome_candidates_list.xlsx / Motif_annotations`, `fibronectin_like_candidate.xlsx / motif_scan_hits`, and `fibronectin_like_candidate.xlsx / ELM_raw_summary` directly. The current adhesome sheet contains 1,097 protein–family screening summaries covering 529 proteins; its 121 priority sites are parsed into individual positional records. The FN3 sheet contributes 55 positional annotations, while the separate ELM sheet summarizes broad regex matches for 89 proteins. The explorer shows these evidence units in separate tabs with species, reviewed-family, protein, motif-ID, source, and context-tier filters. The Protein dossier presents the same positional records alongside its relevant screening summaries and full source context. Library confidence remains distinct from candidate-specific context support.

### Conservative family assignment audit

The revised adhesome workbook adds a `Family_assignment_rule` sheet, per-row scores/grades/decisions, a `Family_Audit` summary, and `Multi_family_conflicts`. Components → Family assignment audit shows those outcomes and allows filtering by Supported, Provisional, Ambiguous and Unassigned. The original `family`, `assigned_family`, and `status` fields remain in the source data. `reviewed_family` is the atlas display label only when the audit retains a family at supported or provisional level; unassigned and ambiguous rows remain visible without a resolved family label. Network family colors use this reviewed label, so a screened generic kinase with an unsupported Src or FAK label is not displayed as an assigned Src or FAK protein. Scores use domain architecture as the primary family gate, with orthology, motif context and topology/localization as supporting evidence; experimental validation was not used.

The revised FN3 workbook replaces the generic fibronectin designation with architecture-specific `recommended_family` assignments and B/C grades. The atlas exposes those as supported/provisional reviewed labels while retaining `fibronectin_like` as the original screening family. The audit script and methodology README in `conservative_adhesome_family_assignment_audit/` are downloadable from Source Library. The atlas reads the audited workbooks directly and does not rerun or overwrite the audit.


### Eight-species orthology and replacement phylogenies
The 2026-09-24 workbooks include five reference proteomes (human, mouse, Xenopus, Drosophila and C. elegans) alongside three schistosome species. Both prefixed and unprefixed reference orthology columns are exposed in the orthology view. Phylogenetic discovery and source-derived prioritization follow the nested replacement collection directories. Human host divergence remains specifically human; adding other reference species does not change it into pooled host divergence. See PHYLOGENY.md for assemblies and retention details.
