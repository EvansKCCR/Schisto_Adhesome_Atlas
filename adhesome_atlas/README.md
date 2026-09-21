# Schisto-Adhesome Atlas — integrin–adhesome catalogue

A Streamlit atlas for exploring schistosome adhesome.

## Launch in WSL (Linux)

In your terminal window, run:

```bash
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

- **Introduction:** about the atlas, collection summary counts and interactive networks.
- **Components:** summary statistics, summary graphs, candidate tables, species comparisons and exports.
- **Interactions:** STRING networks, score thresholds, neighborhood focus, family/localization colors, interaction and node tables, functional annotations and network statistics.
- **Source Library:** every supplied data file and workbook sheet, original downloads and reconciliation checks.
- **Protein dossier / Motif explorer:** positional annotations, sequence provenance and motif evidence.

## Network interpretation

Networks read only `adhesome_network/<species>/*_string_interactions.tsv`. Reverse duplicates are collapsed by unordered STRING identifier pairs, retaining the highest combined score. Short exports remain accessible in Source Library but are not added to the graph. Coordinates retain the exported STRING layout; degrees are recalculated after filtering. Network controls are independent of component filters.

Family and DeepLoc colors use exact species-qualified catalogue ID matches. No aliases are guessed from similar-looking IDs or annotation text. Unmapped nodes remain gray. STRING localization colors highlight membership in a user-selected COMPARTMENTS term; the complete term set stays available in hover details and tables. Original STRING colors are also available, without assigning them an unsupported biological meaning. Associations do not necessarily establish direct physical binding or species-specific experimental validation.

All data now comes from this folder: `files/`, `family_specific_candidate_fasta/`, `topology_localization_cdd/`, `resource_library/` and `adhesome_network/`. The old `06_annotation_visualization` location is not consulted. Missing sequences are reported; exports include only available sequences.

## Data and interpretation

The three collections are intentionally separate. The adhesome workbook has 597 hypothesis records; the FN3 review workbook has 89; the full screening workbook has 4,550 records describing 3,305 unique protein IDs. A row is a family hypothesis, not necessarily a unique protein. Distinct-protein counts are computed within each group, so summed group counts may overlap. Status comparisons can also overlap where a protein has several hypotheses.

IDs in the adhesome workbook are joined using `standardized_id + '__' + protein_id`; the other collections already use these canonical IDs. Species names are mapped from Shae, Sjap and Sman. Original family and assigned-family fields are both preserved. Source workbooks are never rewritten. All FASTAs contribute sequence provenance; identical repeated sequences are deduplicated. Conflicting sequences are exposed in the audit. All raw CSV, SignalP, CDD and 3line files are parsed and available in dossiers and the source library.

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

Introduction and Interactions now open the six-layer reconstruction. Interactions also retains the species STRING explorer. The default pan view combines separate species proteins; it does not invent orthology merges. The orthogroup consensus view activates when cited mappings are supplied. Layer assignments expose their basis, and unresolved nodes remain visible.

Degree, normalized betweenness, corrected closeness, communities, interface counts and complete-case seven-feature prioritization are downloadable. Missing phylogeny, motif conservation or host-divergence evidence remains unassessed. See `adhesome_network/curation/README.md` for the input schema and interpretation rules.

After this update, run `bash launch_atlas.sh --setup` from inside `adhesome_atlas` to install NetworkX and start the app. The launcher now resolves `app.py` and `requirements.txt` in its own folder. Run `~/.venvs/schistoatlas/bin/python test_reconstruction.py` for reconstruction validation.


## Orthology-aware catalogue

Updated candidate workbooks are read with their orthology report sheets, direct-orthologue relationships and HOG copy counts. Candidate worksheet detection tolerates the FN3 worksheet rename. Excel temporary lock files are ignored. Original source statuses and rows remain unchanged.

Components now includes **Orthology & evidence** and **FN3 / RPTP priorities**. Orthology supplies evolutionary context only. The review hierarchy is orthology, architecture, topology/localization and motif context, followed by biological review. A conserved generic kinase or cytoskeletal orthologue is never automatically called an adhesome member. Review stages mark the first unresolved step and do not exclude records. Domain-rule matches and region-supported motif predictions are provisional evidence, not validated adhesion specificity. Missing motifs are treated as missing context, not proof of absence; family-specific exceptions need biological review.

The FN3 view keeps three independent priority groups: eight sampled-HOG Schistosoma-only single-pass adhesion-receptor-like proteins; four sampled-HOG Schistosoma-only RPTP-like proteins; and ten shared-HOG secreted-FN3-assigned proteins with copies in all three schistosomes. Other 67 FN3 candidates remain separate. These are grouping criteria, not a ranking across groups or positive membership claims. Most proteins assigned to the conserved secreted group have discordant localization predictions; the view exposes those conflicts rather than hiding them. Schistosoma-only refers to sampled references, not universal taxonomic restriction.

Network integration accepts exact STRING node IDs or unique exact tokens in the supplied alias field, scoped to species. Ambiguous tokens stay unresolved. Alias-supported mappings can now attach workbook orthogroups to network proteins; sharing a family name is never a mapping rule. Human orthologues prompt selectivity assessment, without generating a host-divergence score. Source HOG species copy-count coverage is used for the conservation feature when available; complete numerical scores remain insufficient to establish adhesome membership.

The Source Library now includes PSI-MI XML and `.all` enrichment exports. The species STRING explorer displays additional protein annotations, evidence-channel references and supplied enrichment. Original annotation/domain-URL headers are preserved despite their apparent swap in the protein-annotation exports. Enrichment statistics apply to the original exported network, not the interactive filtered graph. XML edges are not counted again.

Run `~/.venvs/schistoatlas/bin/python test_orthology.py` inside this folder to validate the evidence hierarchy, priority groups, alias mapping, consensus and new resource views.
