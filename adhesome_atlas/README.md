# Schisto-Adhesome Atlas

A Streamlit atlas of the active seven-species integrin–adhesome catalogue. Assignment records, unique proteins, family inventories and orthogroup counts are calculated from the current workbook at runtime.

## Page organization and scientific typography

**Interactive hypothesis** is a dedicated page immediately after **Introduction**.
It contains the interactive integrin–adhesome map, complete linked candidate
profiles and the linked layered simulator. Introduction retains
the About summary, live counts, both read-more guides and research priorities;
its exploration button opens the dedicated page. Existing Introduction links
that specify a candidate redirect to the interactive page automatically.

Markdown `**emphasis**` renders in bold, including research cards, figures and
diagram profiles. Scientific species names appear in italics in prose, figure
labels, tables, menus and diagrams. Formatting is applied at presentation time;
source annotations, accessions, widget values and downloadable data are preserved.
`branding/scientific_text.py` and `branding/scientific_typography.js` provide shared formatting;
the main-page typography uses Streamlit's in-page components API (Streamlit 1.64+,
already required). Standalone maps embed their typography without external assets.
Run `python testing/test_scientific_text.py` and `node testing/test_typography_browser.cjs` for
formatting checks; `node testing/test_ui_redesign.cjs` checks navigation, responsive
layouts, linked profiles and the simulator.

## Audited candidate library and literature evidence

The active candidate input is `files/adhesome_candidates_list.xlsx` on
`Audited_family_assignment`. The loader accepts the current
`putative_audited_family_new` header and the historical header. The current sheet
contains 4,359 distinct proteins across seven species. The audited support
designations distinguish specific supported, broad supported, ambiguous,
provisional and unresolved records. Original grades and Pfam/CDD architectures
are available in the catalogue and dossiers.

**Citations** opens the searchable publication registry. **Protein dossier →
Literature and biological evidence** displays the selected accession's evidence
alongside labelled family and pathway context. **Components → Family literature
evidence** and **Interactions → Literature & mechanism evidence** provide
family, published interaction, projected edge and simulation views. Selected map
and consensus edges retain source identifiers and literature links.

The registry reconciles the three worksheets in
`files/Schisto_adhesome_focused_literature_crosswalk.xlsx` with the active
candidate sheet. `data/literature/` contains reference and rule sources, TSV
exports, mapping audit, priority traceability and input hashes. The simulator
uses three conceptual layers and independently configurable IPP and SmVKR1
branches. See `notes/README_adhesome_hypothesis_simulator.md` for controls and
reproducible run exports.

Run `python maintenance_directories/rebuild_evidence.py` to refresh the offline HTML snapshots and evidence
exports. **Interactive hypothesis** renders the current catalogue and simulator
from the active inputs. The implementation report records the verified sources,
reconciliation decisions and validation commands.

The literature renderer is bundled with `literature.py`. Deploy the generated
simulator HTML from `adhesome_network/` so the Atlas can use its embedded engine
and controls when the simulator JavaScript source files are unavailable.

## Supported functional repertoire

The Components section includes **Supported families by functional category**:
live category/family counts, species comparisons, localization/topology evidence
and CSV downloads. The reference mapping is read from
`files/Schisto_adhesome_functional_localization_summary.xlsx` (Family breakdown).
Updating that file or the candidate catalogue refreshes the summaries and both
network views through the existing automatic-update option.

Functional categories use `family_support_level`: specific supported and broad
supported identities contribute to the six molecular modules. Provisional,
ambiguous and unresolved identities remain unassigned; their original families,
grades and profiles are preserved. Counts use unique protein IDs. Orthogroup
totals can overlap functional categories. Grades and localization predictions
are independent evidence fields.

Both networks read `adhesome_network/interactions.csv` through the curated family
crosswalk. PARVA and PARVB map to `Parvin_like`, restoring the ILK–PINCH–parvin
hypothesis. Reference edges require supported identities in a shared species;
the full membership of each family or orthogroup stays available in profiles.
Spatial bands follow supported molecular roles, with original DeepLoc, TM and
signal-peptide predictions displayed separately. These positions do not assert
measured cellular coordinates.

## Run in WSL

From this directory:

```bash
bash launch_atlas.sh --setup
```

For a different port:

```bash
ATLAS_PORT=8502 bash launch_atlas.sh
```

The launcher changes into this directory so Streamlit loads `adhesome_atlas/.streamlit/config.toml`. On Streamlit Community Cloud, select `adhesome_atlas/app.py` as the entry point and keep the repository-root `.streamlit/config.toml` for the native widget theme. Keep the data directories beside the app.

## Application directory layout

The root `app.py` remains the stable Streamlit entry point. It loads the organized
runtime without changing any scientific data paths.

- `main/` contains page logic, data loading, network analysis, orthology,
  phylogeny, dossiers, and interactive viewers.
- `branding/` contains the SYNERGY-NGS visual system, typography, figure exports,
  institutional descriptors, and logo assets.
- `notes/` contains citations, scientific briefs, implementation notes,
  phylogeny guidance, and update history.
- `testing/` contains Python and browser regression suites. Run direct tests as
  `python testing/test_<name>.py` or `node testing/test_<name>.cjs`.
- `maintenance_directories/` contains standalone evidence rebuild and SMART/STRING
  fetch utilities.

The current `files/`, `data/`, `orthology/`, `Phylogeny/`, `adhesome_network/`,
`family_specific_candidate_fasta/`, and `resource_library/` directories remain at
the deployment root and retain their existing runtime paths.

## Scientific interface theme

The SYNERGY-NGS palette pairs a navy introduction and cyan call to action with indigo controls, violet focus rings, and magenta and amber accents. Scientific workspaces use white backgrounds and dark text. Local SVG navigation icons retain Streamlit's native labels and keyboard navigation. Evidence grades and data-specific plot colors retain their scientific meaning.

`branding/design_system.py` shares the palette and control styling with embedded maps, the simulator and downloadable HTML. `branding/atlas_styles.py` handles Streamlit pages, cards, tables, tabs and responsive layouts. Run `node testing/test_ui_redesign.cjs` for browser checks of the theme, responsive layouts, linked candidates and simulation, and the Components and Interactions pages. The check starts and closes its own test server unless `ATLAS_PREVIEW_URL` is set. It saves screenshots in the ignored `.ui_review/` directory.

## Active data sources

- `files/adhesome_candidates_list.xlsx` → `Audited_family_assignment`: identifiers, seven species, putative audited families, protein names, confidence, decisions, architecture, benchmark-adjusted orthology and evidence scores. Grade A/B = Supported; grade C = Provisional. Assignment confidence (including ambiguous) remains a separate visible annotation.
- `files/Motif_annotations.xlsx` → positional motifs, context reassessment, peptides, ELM classes and domain overlaps. Both Motif explorer and the dossier Motif tab use this workbook.

The shared motif view supports multiple catalogue records for the same protein ID. `main.data.annotate_motif_sites` combines distinct family, species and protein-annotation labels into a unique lookup before the validated left join. Each original motif row is retained once, including repeated motif records; catalogue records are not deleted. A caption identifies repeated IDs in the displayed motif set. Existing motif-source columns are preserved if their names overlap the catalogue metadata. Run `python testing/test_motif_annotations.py` for repeated-ID, missing/empty-data, filter, dossier-renderer and table-download regression checks; this test does not require a local browser or Streamlit server socket.

- `files/NCBI_CDD.xlsx`, `files/Topology_predictions.xlsx`, `files/Direct_orthologues.xlsx`: dossier evidence.
- `family_specific_candidate_fasta/*.faa`: original sequences and SMART sequence queries.
- `orthology/**/candidate_report.tsv`, `candidate_HOGs.tsv`, `direct_orthologues.tsv`: current orthology results and reference taxa. No historical dictionary or orthogroup merge rules are applied.
- `resource_library/`: calibration, configuration, domain/motif libraries and validation/evaluation results, available in Source Library.

## Networks

`adhesome_network/interactions.csv` holds curated metazoan/human reference rows. `Schistosome_human_gene_family_crosswalk.csv` defines family correspondences; `Schistosome_human_reference_family_edges.csv` retains their aggregated references. Orthogroup consensus projects these family relationships onto candidate orthogroups in the selected species/grades/families. Joins ignore case, spacing, hyphens and underscores; no biological synonyms are guessed. Each edge requires A/B/C family-assigned candidates at both endpoints in a shared species. D/unassigned records retain node membership without transferring edges. Edges retain the exact supporting candidate IDs/species, reference families, symbols, types, effects, row/pair counts, PMIDs and data sources. The projection is separate from species STRING networks. Its topology uses an undirected unweighted graph, with degree, betweenness, corrected closeness, clustering, k-core and community analysis. The spatial viewer retains every filtered orthogroup and projected pair; module focus and local hiding change presentation only. Full filtered graph statistics and downloads remain available. MCODE, MCL and greedy modularity clustering are retained.

All STRING networks are created by the user through **Interactions → STRING query & import**. Families or orthogroups select candidate query IDs. Three previously supported species have prefilled taxon IDs; for additional species enter the correct STRING taxon ID. The app does not silently substitute another species. Querying requires a STRING-covered species and internet access. Imported TSVs and mappings stay in the session.

**Protein sequences (recommended)** maps the original amino-acid FASTAs with STRING 12.5 `POST /api/json/similarity_search`, avoiding gene IDs that STRING does not recognize. **Identifiers + sequence fallback** keeps successful identifier mappings and sequences unresolved queries, including identifier HTTP 404 responses. **Identifiers only** preserves the original workflow. A unique highest-bitscore hit is selected after configurable identity, E-value and relative-bitscore-gap criteria; all alternative hits and unresolved/missing-sequence statuses remain visible. Alignment identity is not a full-length coverage statistic. Multiple candidates mapping to one STRING representative retain all candidate IDs.

Download the original selected FASTA, mapping TSV, all sequence alignments, query JSON and request provenance from the workspace. The standalone `string_fetch.py` accepts the exported JSON, including its original sequences, mode and criteria, and saves the final mapping, alignment hits and network. No additional Python dependency is needed. Run `python -X utf8 test_string_sequences.py` for regression tests, or add `--live` to test ILK/PINCH/Nck sequences and network retrieval against STRING. `node test_string_workbench.cjs` validates the live Atlas UI against `ATLAS_PREVIEW_URL` (default localhost:8511).

## Interactive hypothesis and simulator

The atlas reads `adhesome_network/Schistosome_adhesome_interactive.html` when present, otherwise `Schistosome_adhesome_rebuilt.html`. The network directory also holds `schistosome_integrin_adhesome_hypothesis_simulator.html`. The new family-map selection API is connected to the simulator from the Interactive hypothesis page; there is no standalone simulator page. Inventory uses the active catalogue. Simulation weights remain explicit conceptual assumptions, since metazoan evidence counts are not recruitment probabilities or binding affinities. Families without an explicit simulation mechanism open a clearly labeled baseline scenario.

## Phylogeny additions

The Phylogeny page rescans every 30 seconds while open. New `gene_tree.treefile` files appear automatically, including partial runs; missing companions are listed. Both flat and `inference/` layouts are accepted. Keep `tips.tsv`, `inference/gene_tree.treefile`, `inference/branch_evidence.tsv`, `inference/trimmed.faa`, `inference/gene_tree.iqtree` and `inference/run.json`. Source tree labels, candidate flags, species and branch support are preserved. Optional missing metadata never hides an available tree. A full source reload is also available in the sidebar.

## Downloads and feedback

Charts export high-resolution PNG or SVG. Network SVGs retain dragged positions, centered labels and adjusted font sizes. Original files and workbook sheets remain available in Source Library, immediately before Citations in navigation. Comments and queries prepare an email draft to evansasamoahadu@gmail.com.

## Validation and cleanup

Run `python test_current_library.py --app`, `python test_smart_links.py`, and `python test_topological_clustering.py --app` in the installed environment. `cleanup_manifest.json` records removed historical modules, obsolete fixtures/maps and redundant phylogeny intermediates with sizes and SHA-256 hashes. The six phylogeny visualization/reproducibility companions are retained per run. Primary source workbooks and replacement network/library files are preserved.


## Candidate exploration and page navigation

Interactive hypothesis provides **Locate a candidate on the map**, while the HTML map has its own accession/annotation search and searchable family candidate lists. Candidate evidence is embedded in the standalone file and refreshed from the workbooks inside the atlas. Complete dossiers, profile JSON exports, partner-family exploration and candidate-aware simulator links are available from each profile.

Components uses **Component section**; Interactions uses **Network workspace** followed by **Network analysis section**. These selectors expose all sections without crowded horizontal navigation. Imported STRING networks have their own section selector. Responsive SVG sizing removes the fixed minimum graph width, and **Full screen**, **Fit view**, zoom and SVG export controls support detailed exploration.

Run `python test_candidate_profiles.py --app` to verify exact candidate/evidence joins, JavaScript selection, deep links and every Components/consensus section.

## Scientific workspace design

The interface uses shared, offline design tokens in `design_system.py`: evergreen and warm gold accents, pale neutral surfaces, clear typography, confidence-grade colors and visible keyboard focus. `atlas_styles.py` styles all Streamlit sections; `branding.py` renders the original institutional logos at their natural proportions. The Introduction integrates the approved About text and live catalogue counts into a compact hero, with both README expanders immediately below it.

The map and persistent candidate dossier form one workspace with Map, Simulation and combined views. Network filters and reference evidence remain expandable. **Path & display** holds label-size and path controls. **Read labels** uses a readable scale with panning; **Fit all** shows the full network. Full screen and standalone HTML download support presentations and detailed exploration. A/B/C/D badges repeat the recorded classification; color never replaces the grade text. Layout changes do not modify scientific data, calculations, edge provenance or candidate assignments.

Run `node test_ui_redesign.cjs` against a running Atlas (default `http://127.0.0.1:8510`, override with `ATLAS_PREVIEW_URL`) for desktop/tablet screenshots and live node/profile/simulator/navigation checks. Screenshots and dimension reports go into ignored `.ui_review/`, or `ATLAS_REVIEW_DIR`. Browser-test dependencies are described in `README_schistosome_adhesome_interactive.md`.

## Research priorities and target discovery

The Introduction now includes **Research Priorities & Target Discovery** after the About summary and read-more documentation. Three featured cards cover tetraspanins, calpains and integrin α/β receptors, with separate supported/provisional/unassigned counts, exact candidate and orthogroup links, next investigations and expandable evidence. Additional functional targets, a qualitative vaccine/antibody versus small-molecule comparison and an experimental roadmap are available without leaving the page. No new numerical score or therapeutic validation is inferred.

`research_priorities.py` reads the opening rationale, counts, identifiers, scientific prose, tables and DOI references from `Target_prioritization.md` at runtime. Preserve its three `## **Target ...` headings and table column headings when editing the brief. Tab-separated and Markdown-pipe tables support arbitrary prose; the revised space-separated tables are also recognized using explicit ID/classification and clause boundaries. Ambiguous plain-text cells produce a format message rather than shifting scientific content into the wrong column. Standard `[Author](https://doi.org/...)` citations and the earlier `(Author)[https://doi.org/...]` notation both become clickable links. Missing or structurally incomplete content produces an informative message while the rest of the Introduction remains available. Counts cover the full catalogue and are checked against unique supported/provisional/unassigned candidate IDs; only mismatches are flagged and listed, with both values. Matching comparisons produce no reconciliation flags or table rows. Published Sm-TSP-2 findings do not assign that antigen identity to the listed orthogroups.

The roadmap uses the source-authored targets, objectives and experiments, wherever its table appears in the document. Identical rows with spacing differences are displayed once with a short caption; the original brief download retains every source row. Integrin assignment tables remain separate from narrative evidence, and following additional-target/framework sections do not spill into the integrin card. Family-representative links are detected from the actual row rather than its position in the roadmap.

Priority comparisons and family links recognize explicit legacy/current spellings for tetraspanin, calpain, integrin α/β, collagen and laminin families (underscores versus catalogue spaces/hyphens). This display join preserves source family assignments. Phylogeny accepts family-level `tree.treefile`, `tree.iqtree`, `trimmed.fasta` and `trimed.fasta` alongside the original names; see `PHYLOGENY.md` for layouts, annotations and automatic refresh.

The Phylogeny explorer has separate family-level and orthogroup collections, with independent searches and selections. Family trees show their source groups and an expanded candidate-profile table. Exact-ID dossier links retain catalogue annotations and every matching record; selecting a linked candidate highlights its tree tip. Candidate CSV downloads include all linked records and their presence/absence in the displayed tree. Existing orthogroup deep links choose the orthogroup collection automatically.

Protein links reuse the existing dossier route. `?view=Components&family=kindlin` opens the exact family in the candidate catalogue, resetting incompatible sidebar filters. `?view=Orthology&orthogroup=OG0006637` selects the relevant orthology collection and query. Links are generated only for exact candidate/family/orthogroup records; unavailable entries are labeled. Deep links initialize once, so subsequent navigation and filter changes remain usable.

Deploy `research_priorities.py`, `Target_prioritization.md`, `app.py`, `atlas_styles.py` and `orthology_explorer.py` together. Run `python test_research_priorities.py` for table/citation/source/record/count/routing checks; add `--app` for Streamlit rendering and framework controls. Run `node test_research_priorities.cjs` for browser navigation and responsive layout checks. It starts and closes its own local test server, or uses `ATLAS_PREVIEW_URL` when set. Review images are written to ignored `.ui_review/`.

## Spatial orthogroup consensus explorer

**Interactions → Curated orthogroup consensus → Interactive network** uses `consensus_view.py` and the self-contained SVG template `consensus_view.html`. All orthogroups, projected pairs, reference evidence records and associated candidate memberships are regenerated from the current primary sources and retained with the complete default selection. Nodes are no longer truncated to the highest-degree 200. Projection version 2 reconciles formatting-equivalent family names and requires supported/provisional family candidates in a shared species. The same centrality, matrix and clustering algorithms run on this corrected graph. Source labels, grades, orthogroup IDs and catalogue records are preserved.

Four layouts use deterministic initialization and collision-free node slots:

- **Cellular localization view:** ordered extracellular, membrane, membrane-proximal, signaling, cytoskeletal and unresolved bands. Singleton DeepLoc Extracellular/Cell membrane predictions directly select the corresponding conceptual region. For singleton Cytoplasm predictions, annotated talin/kindlin/ILK/PINCH families define proximal context; annotated cytoskeletal families define cytoskeletal context; kinase/phosphatase or adaptor/GTPase inventory modules define signaling context. Missing, multiple, other-organelle, contradictory or unclassified cytoplasmic contexts remain unresolved. Every member must agree before an orthogroup is assigned a resolved region. Unresolved counts update with the library; individual localization predictions are retained in the dossier.
- **Functional module view:** retains every functional annotation from the family inventory. Each module is subdivided by connected components of its existing induced graph. Isolates form separate neighborhoods. Multiple module annotations remain explicit on the original single orthogroup node.
- **Connectivity/community view:** spaces the existing unweighted greedy-modularity communities in separate regions; these algorithmic communities are not biological module assignments.
- **Free network view:** Seed-20 force initialization, followed by deterministic nearest-grid placement to remove collisions. At 500 or more nodes a blockwise NumPy implementation avoids requiring SciPy. Coordinates are presentation metadata and are cached with a hash of the layout/annotation source.

Colors identify conceptual regions, annotated modules or algorithmic communities. Circle radius is `12 + 4 × log2(1 + unique candidate count)` in layout units. Confidence uses an independent outline: solid for A/B-only membership, dashed for C-only, dotted for mixed supported/provisional membership, dash-dot when D/unassigned members are present. Labels adapt to zoom, prioritize selection and suppress collisions; full IDs remain available through hover, search and selection. Centered labels fit inside the quantitative circles without changing circle size.

Click any orthogroup for its complete filtered candidate list, exact A/B/C/D totals, architecture, localization/topology and supporting evidence, with links to full Protein Dossiers. One-/two-step highlighting follows the original undirected edges; it does not infer downstream direction. **Focus on module** isolates the selected connected annotated neighborhood. **Restore all nodes** clears local hiding/focus; layout switches retain the selected orthogroup and candidate. Dragging, pan, zoom, Read labels, Fit network and search modify presentation only.

Click a highlighted edge to inspect all of its reference evidence rows, symbols, types, effects, PMIDs, shared species and exact supporting candidate IDs. Supporting IDs are stored with each edge rather than reconstructed from all members of a mixed-family orthogroup. Edge row counts are not binding affinities. Download the offline interactive HTML, all four coordinate/annotation tables, annotation rules, current layout JSON or scalable SVG; the standalone file embeds every candidate profile and requires no external JavaScript/font resources. Evidence CSVs retain their earlier columns and add original reference-family names and shared-species fields.

Run `python test_consensus_layout.py` for complete source/graph/membership/evidence integrity, strict localization rules, filtered/singleton graphs and deterministic circle separation. Then run `node test_consensus_view.cjs` against the local Atlas (default 8511; `ATLAS_PREVIEW_URL` overrides it). The browser test clicks every current node, checks complete profile/neighbor mappings, all four modes, module focus, second-degree traversal, search, drag/zoom, labels, SVG export and desktop/tablet layouts, including an offline exported-file check. `--before` captures the legacy viewer before changes. Before/after screenshots and JSON validation reports are stored under ignored `.ui_review/`.

Run `python test_consensus_projection.py` for family-format invariance, endpoint orientation, grade/species eligibility, exact edge IDs and an independent reconstruction that unions separately built species networks. Add `--app` for Streamlit count/filter/analysis/download checks. After the layout test generates its fixture, `node test_consensus_view.cjs --offline` validates the standalone SVG viewer without a running Atlas server. The source snapshot checked on 1 November 2026 contains 579 orthogroups and 747 projected pairs connecting 90 orthogroups; application counts are computed from current sources.

## Automatic primary-source refresh

The family-assignment audit accepts spaced or underscored versions of its audit headers, including `identity rule` / `identity_rule`. Original workbook columns and values are retained; a canonical field supplies the audit display and candidate profiles. Optional absent audit columns are listed in a caption instead of crashing the page. The full-record CSV export is preserved. Deploy `app.py` and `data.py` together for this schema correction. Run `python test_audit_schema.py --app` to verify aliases, optional fields, complete candidate counts, profile values and the Streamlit audit view.

The sidebar **Automatically update inventory** toggle is enabled by default. While enabled, the open Atlas checks deployed source files every 30 seconds and refreshes the catalogue, inventory, counts, profiles and derived networks when they change. The candidate workbook is checked by SHA-256 content as well as modification time and size, so copies retaining their original timestamps are detected. Other library files retain modification-time/size detection. Turn the toggle off to pause background checks; opening/reloading or interacting with the app still reads the latest inputs. The sidebar **Reload source files** button remains available for an immediate manual refresh. Incomplete or temporarily unreadable input files display a pending-refresh message and retry automatically. Valid sidebar choices and page navigation are retained; deleted IDs/families are removed from selections. This observes files available to the running app: local/WSL changes must still be published to the deployed GitHub branch for Streamlit Cloud. It does not push runtime outputs back to GitHub.

Primary network inputs:

- `files/adhesome_candidates_list.xlsx / Audited_family_assignment`: current identifiers, audited families, grades, annotations and orthogroups.
- `adhesome_network/interactions.csv`: raw curated reference interactions, including relation/effect/source/PMID evidence.
- `adhesome_network/Schistosome_human_gene_family_crosswalk.csv`: explicit symbol-to-family correspondences. Unmapped symbols are reported in refresh provenance; no correspondence is inferred.
- `adhesome_network/family_module_annotations.csv`: editable curated family-to-module labels, separated from generated counts. New unmapped modules are shown as unresolved.

`library_refresh.py` automatically regenerates `Schistosome_human_reference_family_edges.csv`, `Schistosome_adhesome_family_inventory.csv` and `Schistosome_adhesome_candidate_node_members.csv`. Write changes are atomic and skipped when bytes agree; generated outputs are excluded from the primary-input watcher to prevent refresh loops. The consensus computes from primary inputs even if the generated edge CSV is stale or absent. On a read-only host regeneration still works in memory and the sidebar explains why disk mirrors could not be saved. `.atlas_cache/library_refresh.json` records hashes, counts and unmapped-reference diagnostics. Edit the primary interaction/crosswalk/module files rather than the regenerated mirrors.

The family inventory distinguishes `assignment_records` (every source annotation row) from `total` (distinct protein identifiers within that family). Grade and species columns count distinct identifiers within their family/grade/species scope. The membership CSV retains every original assignment row. Refresh provenance includes global assignment records, distinct proteins, record-based grade counts and distinct-protein grade counts; duplicate source records remain traceable. The simulator's supported inventory uses the same formatting-only family joins, including space-separated integrin labels, and counts unique supported proteins.

The Interactive hypothesis family map rebuilds its DATA inventory, candidates and projected edges at render time using the authored HTML as its visual/control template. Authored special literature context is retained only when its named candidates still have the corresponding audited family assignments. The original HTML is not overwritten. Downloads contain the refreshed data and profiles. The map defaults to the complete inventory; the authored core subset remains an optional filter. New families and unassigned pools remain browsable without inventing interactions or module assignments.

A/B are Supported, C is Provisional and D is Unassigned throughout filters, network badges and candidate dossiers. Unassigned records do not regain family membership through the crosswalk, orthology or an earlier hypothesis. Research-brief `unresolved` and `unassigned` terms both map to the Unassigned display category. The nine unassigned integrin-α records are counted from their recorded `stage1_family_hypothesis`; their audited family remains unassigned. Brief counts remain source-authored and discrepancies are flagged. Protein profiles prefer current `orthology/**/direct_orthologues.tsv` reports over an older Excel export.

The refresh does not rerun upstream motif prediction, orthology, tree inference, audited scoring or experimental models. Those outputs are read when updated; simulator recruitment weights remain the documented conceptual parameters.

Validation: `python test_library_refresh.py` (add `--app` for the sidebar toggle), `python test_research_priorities.py`, `python test_consensus_layout.py`, and `node test_auto_refresh.cjs`. Refresh tests include workbook-content changes with preserved file size/timestamps, duplicate-record counting, pause/resume, current profiles/counts and actual timer-driven refresh using a temporary non-scientific library entry. The browser check starts/closes its own server unless `ATLAS_PREVIEW_URL` is set and verifies both network viewers and all four consensus layouts. Run the existing catalogue/profile and consensus browser checks for broader regression coverage.

## Orthogroup Statistics & Explorer

Open **Orthology → Orthogroup Statistics & Explorer** for the exact-copy-profile dashboard. **Candidate & reference orthologues** retains the existing report collections, assignments, HOG members and direct-orthologue exploration.

Both statistics views recalculate from `files/adhesome_candidates_list.xlsx`, sheet `Audited_family_assignment`. Each unique protein ID counts once per species and orthogroup. If an ID has multiple assignment rows in the same group, the strongest audited support state and then the best recorded grade determine its contribution to the counts. Dossiers still display the linked catalogue records. The Atlas source watcher reloads the workbook when it changes.

**Exact copy profiles** includes groups with equal nonzero candidate-copy counts in all seven species. The 1:1 and 2:2 supported subsets include groups with at least one supported copy. Complete, partial and no supported identity describe support for all, some or none of the copies. A group can have more than one supported family label. Copy-profile similarity alone does not establish orthology or paralogy.

Specific and broad family support are counted from the audited support designation. The dashboard breaks supported copies down by recorded grades A–D, including broad-supported grade C. Filters select whole orthogroups and retain their seven-species totals. Family filters include mixed groups that contain the selected supported label.

The workspace can download current exact-profile TSVs and their 1:1 and 2:2 subsets. The saved `orthogroups_all_exact_copyprofiles.tsv`, `orthogroups_1to1_supported.tsv` and `orthogroups_2to2_supported.tsv` files are also available for comparison.

Six chart views cover copy profiles, family composition, species heatmaps, identity classification, specific/broad support and species representation. Bar clicks apply exact source-value filters. Heatmap cells and explorer rows select an orthogroup in the detail panel; the searchable selector provides a keyboard alternative. Reset clears logical and visual chart selections, and events from replaced charts are ignored. Heatmaps include black count labels, integer legends, seven species columns and a selectable maximum row count; every filtered group remains in the explorer table. Figures reuse high-resolution PNG and vector SVG exports.

Details show the current species copy counts, supported family identities, specific/broad support and recorded grades. Candidate dossiers link through exact Atlas orthogroup and protein IDs. Matching gene trees link to **Phylogeny** with the orthogroup query already selected. Direct-reference links open the candidate and reference orthologues workspace.

Run `python test_orthogroup_statistics.py` for catalogue reconciliation, filters, links and chart checks. Run `node test_orthogroup_statistics.cjs` for browser checks of table selection, reset and chart interactions. It starts and closes its own test server unless `ATLAS_PREVIEW_URL` is set. `--visual-only` captures both numbered heatmaps in the ignored `.ui_review/` directory.

## Interspecific orthogroup summary report

**Orthology → Orthogroup Statistics & Explorer → Interspecific copy-number summary** includes every orthogroup assigned in the current candidate workbook. It reports species copy counts, max−min Δ, and the marked (Δ ≥ 2) and pronounced (Δ ≥ 3) subsets. The original `orthology/schistosoma_interspecific_copy_number_variation.xlsx` supplies reference taxa where an exact orthogroup ID matches. That workbook and its marked-variation TSV remain downloadable as saved reports.

The summary reports supported, unresolved, ambiguous and provisional copies separately. Species detail includes both total and supported copies and the grade breakdown for the selected orthogroup. All/some/no supported-copy coverage follows the audited supported and total counts.

Choose subsets, species, supported families and coverage. Search by orthogroup, family label or reference taxon. The copy-spread, support-state and species-heatmap figures support PNG/SVG downloads. Groups with equal nonzero counts in all seven species can open their current exact-profile record directly.

Run `python test_orthogroup_variation.py` to check the catalogue and saved report separately. Run `node test_orthogroup_statistics.cjs --summary-only` for browser checks of the summary and its link to the exact-profile explorer.

## Analysis of all imported STRING networks

**Interactions → STRING query & import** now retains independent API-fetched and uploaded networks in the current session. Upload multiple TSVs in one batch; the selected species, functional/physical type and score scale apply to that batch. Other species can be imported in subsequent batches. Each file is validated independently, so an invalid file does not discard valid siblings. Exact reimports refresh metadata; changed source content creates a separate retained network. Same-name versions have distinct selector labels. Original library files are not rewritten, and networks/species are not merged automatically. Download reports before ending a session.

Every import uses the same analysis engine in `string_analysis.py` and workspace in `string_analysis_view.py`. Initial score threshold is zero, retaining all associations already present in the source response; API request thresholds still apply at retrieval. Confidence/family/neighborhood/isolate filters recompute every analysis on the same displayed graph. Saved imports remain accessible even when the current query species has no configured STRING taxon.

Available sections:

- **Interactive network:** editable vector network, mapping/family/community/component/articulation colors, bridge highlighting and standalone HTML download. Large graphs retain all nodes using component islands or circular layouts without SciPy.
- **Network overview:** density, degree distribution, local clustering, transitivity, triangles, components, isolates, assortativity, global efficiency and mean distance over reachable pairs.
- **Centrality & clusters:** degree/degree centrality, confidence strength, normalized betweenness, disconnected-corrected closeness, harmonic centrality, unweighted and confidence-weighted PageRank, component eigenvector, clustering coefficient, triangles, k-core, average neighbor degree, reachable-node/farness/eccentricity values, articulation/bridge counts and existing annotated-layer interface counts. Rankings and Spearman correlations use applicable metrics. Component-normalized eigenvectors are reported within components and excluded from pooled rankings/correlations when disconnected.
- **Topological clustering:** default Greedy modularity, MCODE and MCL comparison; parameterized cluster exploration, memberships, diagnostics, editable cluster visualization, overlap/composition analysis and downloads. STRING users no longer need to enable a nested clustering checkbox.
- **Components & robustness:** component sizes/densities, component diameter/radius/mean shortest path, articulation proteins and bridge interactions. These describe graph structure rather than experimental essentiality.
- **Interactions & mapping:** original evidence channels plus edge betweenness, common-neighbor counts, neighborhood overlap and bridge flags. Exact many-candidate STRING mappings are preserved.
- **Matrices:** binary adjacency, confidence adjacency, full-graph hop distances, full-graph neighbor Jaccard and the selected induced-subgraph Laplacian. Up to 60 selected nodes; all five matrices can be downloaded together. Unreachable paths and undefined empty-neighborhood overlaps remain blank.
- **Query provenance:** original source/query metadata, graph hash, calculation methods, current filters and original TSV download.

Shortest-path metrics use unweighted hops. STRING confidence is a connection weight for strength and weighted PageRank, not a path length, binding affinity or recruitment probability. PageRank uses alpha 0.85 and explicitly reports nonconvergence. Eigenvectors are normalized separately within nontrivial connected components; isolates have no eigenvector value. Degree centrality is zero for a singleton. No new family identity or biological essentiality is assigned by topology.

Calculation limits are explicit: all-node exact path metrics default to at most 2,000 nodes; larger graphs use normalized betweenness sampled from up to 256 source nodes (seed 23), with exact closeness/harmonic/farness/eccentricity unavailable until requested or filtered. Exact path analysis can be requested up to 5,000 nodes. Exact edge betweenness is bounded to 500 nodes / 5,000 edges. Greedy modularity, MCODE and dense NumPy MCL are available up to 5,000, 1,200 and 400 nodes respectively. Missing/unconverged results are not replaced with zero or an invented assignment.

**Analyze and compare all saved imports → Analyze all imported STRING networks** evaluates each full imported graph independently, including resolved isolates. It produces a comparison table and a combined ZIP containing per-network node/edge/component tables, clustering memberships and summaries, algorithm availability/convergence, source TSV and methods/provenance. Selected-network filters do not alter the batch inputs. Per-network topology and matrix downloads retain the displayed graph/filter scope. Removing the selected import preserves other imports; clearing all imports is a separate action.

Deploy `string_workbench.py`, `string_analysis.py`, `string_analysis_view.py` and `topological_clustering.py` together. Dependencies are unchanged. Run `python test_string_analysis.py` for numerical/parser/registry/ZIP and SciPy-free large-graph checks, adding `--app` for every analysis section and batch controls. Existing `test_topological_clustering.py` and `test_string_sequences.py` cover algorithm/mapping regressions. `node test_string_import_analysis.cjs` tests real multi-file API/website uploads and analysis controls using local fixtures with no remote STRING calls. It closes its own server/browser and writes ignored review artifacts in `.ui_review/`.
