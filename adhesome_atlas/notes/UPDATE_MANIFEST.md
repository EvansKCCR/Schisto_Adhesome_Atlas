# Atlas update · 8 November 2026

## Streamlit source organization

Organized the Streamlit source into `branding/`, `main/`, `notes/`, `testing/`,
and `maintenance_directories/`. The root `app.py` remains the stable WSL and
Streamlit Community Cloud entry point. It adds the organized module directories
to the import path and loads `main/app.py`.

All scientific data directories retain their existing names and root-relative
locations: `files/`, `data/`, `orthology/`, `Phylogeny/`, `adhesome_network/`,
`family_specific_candidate_fasta/`, and `resource_library/`. Runtime path
resolution, source fingerprints, automatic refresh, dossier downloads, network
regeneration, phylogeny discovery, SMART scripts, STRING scripts, and research
brief/citation rendering now resolve through the organized directories.

The current 4,359-protein candidate library and orthogroup statistics pass the
focused structural tests. The literature registry and offline network assets
were regenerated from the current workbook, producing 21 references, 290
interaction records, and 1,246 priority-trace rows. Extended browser suites
remain optional local validation.

Files updated or reorganized: root `app.py` and `README.md`; all runtime modules
under `main/`; visual modules and assets under `branding/`; documentation under
`notes/`; test suites under `testing/`; standalone utilities under
`maintenance_directories/`; current literature exports in `data/literature/`;
and regenerated standalone HTML files under `adhesome_network/`.

# Atlas update · 7 November 2026

The active Atlas uses the November 7 audited candidate workbook and literature
crosswalk. The release integrates accession-scoped publications and the layered
mechanotransduction simulator. See `IMPLEMENTATION_REPORT_2026-11-07.md` for the
complete file list, verification results and regeneration commands.

# Atlas update · 5 November 2026

## Dedicated interactive page and scientific typography

Moved the map, catalogue/class-map controls, complete candidate profiles and
linked simulator to **Interactive hypothesis**, directly after Introduction.
The Introduction retains About, live counts, both README expanders and research
priorities, with a link to the dedicated page. Dossier/reclassification links
open that page; legacy Introduction links with candidate parameters redirect.

Shared presentation formatting renders double-asterisk emphasis in bold and
scientific species names in italics across Markdown/HTML, Plotly, native grid
canvas, species menus and owned HTML/SVG diagrams. Raw identifiers, source
annotations, scores, model topology, widget values and CSV/JSON exports are
unchanged. Main-page formatting uses the supported Streamlit components API;
standalone maps include offline formatting. Both standalone catalogue/class
HTML maps have been regenerated without replacing their scientific payloads.

Validation: formatter/navigation/legacy-route tests; all 26 research-priority
count checks; browser HTML/grid/figure/menu/embedded-SVG typography and raw-value
checks; responsive desktop/tablet/mobile navigation, candidate/profile/simulator
and Components/Interactions checks. Review artifacts are in ignored .ui_review/.

Files: app.py, navigation.py, scientific_text.py, scientific_typography.js,
atlas_styles.py, design_system.py, figure_exports.py, research_priorities.py,
reclassification_view.py, candidate_profiles.py, test_scientific_text.py,
test_typography_browser.cjs, test_ui_redesign.cjs, test_research_priorities.py,
README.md, UPDATE_MANIFEST.md, adhesome_network/Schistosome_adhesome_rebuild_README.txt,
adhesome_network/Schistosome_adhesome_rebuilt.html and
adhesome_network/Schistosome_Pfam_CDD_family_hypotheses.html.

## Reconciled local Pfam–CDD results and revised research priorities

Integrated `files/adhesome_unassigned_Pfam_CDD_classification.xlsx` by exact protein
ID: all 3,281 records match the catalogue species, orthogroup and full Pfam/CDD
architectures. There are no unmatched IDs, stale architectures or overlaps with
already supported catalogue assignments. Tiers are A = 609, B = 270, C = 2,239,
D = 163. Original family labels, grades, support flags, numerical scores and all
4,361 assignment records (4,359 unique proteins) are preserved. The separate
reclassification fields retain the exact proposed class, full tier description,
priority, rationale, module, orthogroup context and original architecture strings.

Components now includes **Pfam–CDD family reclassification**, with tier/family/
module/priority/search filters, charts, full candidate evidence, exact dossier
and class-map links, and downloadable reconciliation. Candidate prioritization
can order unique proteins by the reported local P1–P4 priority and evidence tier.
Protein dossiers, linked map profiles, orthology tables and consensus searches/
profiles expose the same classifications. The optional **Pfam–CDD family/class
map** presents 174 groups alongside the retained 76-group catalogue view.
Reference transfer retains supported-family/shared-species requirements; broad
domains and orthogroup hints do not acquire a specific reference interaction.
Per-node counts use unique protein IDs; complete source membership rows remain
in the library. Both offline HTML maps include complete annotated profiles and
remain below 25 MB.

Automatic refresh includes content hashes for both workbooks and the revised
target-prioritization brief. The reconciliation report retains unknown/stale
records explicitly, while stale classifications are excluded from applied map
groupings. Generated CSV mirrors remain excluded from refresh triggers.

The revised `Target_prioritization.md` is read without editing its scientific
content: 20 additional target families, 15 distinct roadmap entries and 19 DOI/
PubMed references. Expanded evidence paragraphs and the final selection
framework are displayed; exact links cover all seven candidate-species prefixes.
All 26 brief count comparisons match. Family-name joins normalize formatting
without combining distinct biological families; flags appear for actual count
mismatches. Pfam–CDD classes remain separate from the original catalogue grades.

Validation: exact source-field reconciliation and original-decision preservation;
stale-domain/unmatched-ID/conflicting-row cases; same-metadata content-change
detection; unchanged reference topology; source-preserving priority parsing and
all 26 counts; Streamlit explorer filters, complete evidence tables, orthogroup
contexts and empty searches. Browser checks verified independent clicks and
complete profiles/grade counts for all 174 class groups, A-tier versus D-grade
separation, the original 16 Parvin profiles and offline operation.
Browser explorer checks also passed candidate-label/profile synchronization,
exact dossier/map routes, C-tier filtering and all expanded research/roadmap
sections. The updated consensus renderer retained 579 nodes and 738 projected
pairs with complete classification fields and searchable recovered families.

### Files created or updated

- `reclassification.py` — exact reconciliation, evidence fields, class-map projection and priority ordering.
- `reclassification_view.py` — interactive evidence explorer, complete tables and dossier/map links.
- `data.py` — loads the evidence layer, schema refresh and content hashes.
- `app.py` — new Components section, map grouping, dossier evidence and priority option.
- `library_refresh.py` — provenance, tier counts, complete membership/report mirrors and class-map layout.
- `candidate_profiles.py` — reclassification evidence in linked/standalone candidate profiles.
- `linked_explorer.py` — explicit talin/filamin/alpha-actinin/GRB2 classification labels reuse existing conceptual simulator mechanisms; broad domain classes retain their separate context.
- `orthology_explorer.py` — searchable reclassification fields in candidate assignments.
- `consensus_view.py`, `consensus_view.html` — classification metadata, searches and profile display.
- `research_priorities.py` — expanded family joins, all scientific narrative, exact identifier links and DOI/PubMed references.
- `test_reclassification.py`, `test_reclassification_ui.py`, `test_reclassification_browser.cjs` — reconciliation, UI and standalone/browser validation.
- `test_research_priorities.py`, `test_library_refresh.py` — revised source fidelity and refresh regression checks.
- `adhesome_network/Schistosome_adhesome_family_inventory.csv` — regenerated catalogue counts plus tier counts.
- `adhesome_network/Schistosome_adhesome_candidate_node_members.csv` — complete membership plus reclassification evidence.
- `adhesome_network/Schistosome_Pfam_CDD_reconciliation.csv` — all 3,281 classification records and catalogue decisions.
- `adhesome_network/Schistosome_adhesome_rebuilt.html` — refreshed catalogue map/profiles.
- `adhesome_network/Schistosome_Pfam_CDD_family_hypotheses.html` — standalone 174-group class map/profiles.
- `adhesome_network/Schistosome_adhesome_rebuild_README.txt`, `README.md`, `UPDATE_MANIFEST.md` — current scopes, counts and interpretation.
- Runtime/QA: `.atlas_cache/library_refresh.json`, `.ui_review/` validation reports, preview fixtures and screenshots.

Source workbooks, `Target_prioritization.md`, curated interactions and the family
crosswalk are consumed as primary inputs. Their scientific content was not edited.

# Atlas update · 4 November 2026

## Functional repertoire and ILK–PINCH–parvin hypothesis

Integrated the updated `adhesome_network/interactions.csv`. Added PARVA and PARVB
to the curated parvin-family crosswalk, restoring the ILK–parvin and PINCH–parvin
reference relationships in both network views. Original interaction rows, types,
effects, PMIDs and sources remain intact. Reference transfer now follows explicit
specific/broad supported family identities in a shared species; every candidate
and original grade remains in its family/orthogroup profiles. Historical imports
without that support field use their grade-based compatibility path.

The functional-summary workbook was located in the workspace root and copied
unchanged into the Atlas `files` directory for portable deployment. Its supported
family breakdown defines the functional mapping, overriding historical display
categories. The candidate and interaction source files were not edited. Original
workbook bytes match the packaged copy.

Added Components → **Supported families by functional category**, including
category/support charts, family breakdown, seven-species comparison, independent
localization/topology evidence and CSV exports. All counts are recomputed from
unique candidate IDs and active filters. Reconciliation matches every reported
numeric field in all seven category rows, the overall row and all 80 family rows:
4,359 unique proteins, 953 specific + 125 broad supported, 70 supported family
labels and 3,281 unassigned/unresolved proteins. Orthogroup counts are not
additive across categories. Grade and family support remain separate.

Corrected both spatial views to function-first molecular roles. Parvin, vinculin,
spectrin and zyxin/ajuba join the membrane-actin clutch; MMP is extracellular;
dynamin and RACK1 join adaptors/GTPases; ADAM, INSR and SPTLC are in the membrane/
receptor functional category. These conceptual bands do not overwrite DeepLoc,
TM or signal-peptide predictions. Mixed supported functional contexts remain
explicit. Parvin OG0000818 retains 16 profiles: 14 supported + two unresolved;
its supported context places it in the clutch, with source-supported ILK/PINCH
reference relationships across seven species. The complete graph has 579 nodes
and 738 unique projected pairs after applying these support criteria.

### Files created or updated

Validation passed: complete workbook/count reconciliation; refresh mutation tests;
independent per-species consensus reconstruction; four deterministic layouts;
actual clicks on all 579 orthogroups with exact profile/neighbor checks; offline
vector export and interaction controls. Live Atlas checks confirmed Parvin's
16 profiles, seven-species IPP projections, supported/unresolved profile switching,
desktop/tablet/mobile bounds and linked simulator controls. The new dashboard
passed its isolated complete-inventory AppTest and browser checks for calculated
metrics, rendered charts, all three tabs and downloads. A chart-reshape column
collision identified during browser testing was fixed and regression-tested.
The standalone HTML is approximately 21.35 MB.

- `functional_categories.py` — workbook-based mapping, support definitions and unique-protein summaries.
- `functional_categories_view.py` — Components charts, tables, evidence definitions and downloads.
- `app.py` — adds the functional-category component section.
- `data.py` — assigns per-candidate functional categories and refreshes cached schema.
- `library_refresh.py` — source-based family map, support-gated edges, unique node counts and mapping provenance.
- `candidate_profiles.py` — adds functional category/basis and explicit family support to profiles.
- `curated_network.py` — support-gated, shared-species reference projection.
- `consensus_view.py` and `consensus_view.html` — functional placement and complete profile/evidence display.
- `adhesome_network/Schistosome_human_gene_family_crosswalk.csv` — PARVA/PARVB → Parvin_like.
- `adhesome_network/family_module_annotations.csv` — corrected functional categories and missing supported families.
- `adhesome_network/Schistosome_human_reference_family_edges.csv` — regenerated reference-family mirror.
- `adhesome_network/Schistosome_adhesome_family_inventory.csv` — regenerated counts/modules and supported/unsupported totals.
- `adhesome_network/Schistosome_adhesome_rebuilt.html` — regenerated standalone map and complete linked profiles.
- `files/Schisto_adhesome_functional_localization_summary.xlsx` — unchanged source workbook packaged with the Atlas.
- `test_functional_categories.py` — workbook reconciliation, duplicate-ID handling and IPP projection/profile checks.
- `test_functional_dashboard.py` — complete-inventory dashboard rendering, metrics and chart regression test (including proteins without orthogroups).
- `test_consensus_projection.py` and `test_consensus_layout.py` — support-aware graph and placement validation.
- `test_library_refresh.py` and `test_ui_redesign.cjs` — refresh regression checks, Parvin interactions and Components UI validation.
- `README.md` and `UPDATE_MANIFEST.md` — source definitions, behavior and change list.
- Runtime/QA outputs: `.atlas_cache/library_refresh.json` and `.ui_review/` (standalone fixtures, graph validation reports and browser screenshots; these are not scientific source files).

# Atlas update · 3 November 2026

## Updated candidate inventory and automatic-update option

Reconciled the generated inventory and candidate membership with the latest `files/adhesome_candidates_list.xlsx`: 4,361 assignment records, 4,359 distinct protein identifiers, 76 family labels and seven species. Record grades are A = 1,065, B = 21, C = 2, D = 3,273; distinct-protein grade counts are A = 1,064, B = 21, C = 2, D = 3,272. Family inventory rows now expose assignment-record counts alongside their existing unique-protein totals; all source records remain in the membership library. Provenance records both scopes and the exact workbook hash.

Added an enabled-by-default sidebar **Automatically update inventory** toggle, with visible active/paused status and the retained **Reload source files** action. Active checks run every 30 seconds. The candidate workbook fingerprint includes SHA-256 content, detecting changes even when a copy preserves size and modification time. Generated mirrors remain excluded from the watcher, and temporarily replaced/locked files follow the existing pending-save/retry behavior. Species filters retain their choices across refreshes without combining an explicit widget default with a session-state value.

The simulator's supported-family inventory now accepts the same formatting-equivalent labels as the catalogue/network inventory, including `integrin alpha` / `integrin_alpha`, while retaining source assignments, grade requirements and unique-ID counts.

Files updated: `app.py`, `data.py`, `source_watch.py`, `library_refresh.py`, `simulator.py`, `test_library_refresh.py`, `test_auto_refresh.cjs`, `README.md`, `UPDATE_MANIFEST.md`. Regenerated: `adhesome_network/Schistosome_adhesome_family_inventory.csv` and runtime `.atlas_cache/library_refresh.json`. Candidate workbook, membership rows and curated reference inputs are preserved; existing matching mirrors are not rewritten.

Validation passed: inventory record totals and membership IDs reconcile to the unchanged workbook SHA-256; duplicate records and unique grade counts remain distinct; content changes with identical file size/mtime invalidate the cache; generated outputs do not cause refresh loops; read-only fallback and source/orthology mutations pass. Streamlit verifies enabled-by-default auto-update, pause/resume and manual reload. The browser verifies actual timer-driven refresh (about 48 seconds including reload), current record/grade counts, exact candidate profiles in both network viewers and all four consensus layouts without page errors. Its temporary non-scientific probe was removed after validation. Review artifacts are in ignored `.ui_review/`.

## White scientific interface

Replaced the green-tinted page and gradient hero/card backgrounds with white surfaces, sharp dark text, green actions/circular navigation symbols, light-gray structure and red selection rules. The native Streamlit theme matches the shared CSS. Removed decorative hero/section/card captions, the repeated sidebar tagline and watermark-like hero ornament while retaining functional headings, scientific labels and institutional credits.

The navigation symbols are embedded local SVGs and retain the existing native radio controls and keyboard behavior. Shared standalone/iframe styling updates map, simulator and consensus controls/backgrounds without recoloring biological node/edge encodings. Counts, routes, catalogue annotations and analytical functions are unchanged.

Files updated: `design_system.py`, `atlas_styles.py`, `.streamlit/config.toml`, `app.py`, `research_priorities.py`, `test_ui_redesign.cjs`, `README.md`, `UPDATE_MANIFEST.md`.

Validation passed in the real browser: white page/hero surfaces with no gradient, ten distinct local navigation icons and visible labels, body-text contrast above 7:1 and green-button contrast above 4.5:1, no decorative watermark captions, and desktop/tablet/mobile layouts without page or linked-workspace overflow. Candidate selection, profile retention during simulation, Components/Interactions navigation and native keyboard navigation pass. Research-priority source/count/link regression checks also pass. Preview screenshots and the contrast/layout report are in ignored `.ui_review/`.

## Revised target-prioritization brief

Updated the research-priority reader and presentation to support the revised `Target_prioritization.md`: space-separated tables, standard Markdown DOI links, the roadmap before the featured targets, revised narrative and opening rationale, and renumbered additional-target sections. Tab-separated tables, Markdown-pipe tables and legacy citation syntax remain supported. Table values and source prose are retained; ambiguous plain-text cells request explicit tab/pipe boundaries rather than being silently misclassified.

The Atlas displays three featured priorities, seven additional families, six framework criteria, seven unique roadmap entries and five linked references. The repeated Sm-p80 roadmap row is displayed once, with a caption and the unchanged original available for download. Exact protein, orthogroup and family links remain active, including the divergent integrin alpha candidate `Smp_170280` / `OG0006637`. The assignment table and later sections are excluded from the integrin narrative and displayed in their appropriate places. Family-representative links now follow the source row rather than assuming it is the last row. All 13 source count comparisons match the catalogue, so no mismatch flags are displayed.

Files updated: `research_priorities.py`, `test_research_priorities.py`, `test_research_priorities.cjs`, `README.md`, `UPDATE_MANIFEST.md`. The user-edited `Target_prioritization.md` and candidate workbook are read without modification. Existing source watching picks up subsequent brief edits automatically.

Starting the Atlas for browser validation also refreshed its generated mirrors from the current catalogue: `adhesome_network/Schistosome_adhesome_family_inventory.csv`, `adhesome_network/Schistosome_adhesome_candidate_node_members.csv`, and runtime `.atlas_cache/library_refresh.json`. The primary workbook and the aggregated reference-edge CSV were not rewritten.

Validation passed: identical scientific fields across space-separated, tab-separated and Markdown tables; both DOI syntaxes; malformed-row rejection; exact section boundaries; source rationale; duplicate-row handling; all 13 catalogue counts; exact protein/family/orthogroup links and source-file hashes. Streamlit rendering/framework checks pass. Browser checks pass for desktop/tablet/mobile layouts, three featured cards, seven additional families, six criteria, seven unique roadmap entries, five references and actual dossier/family/orthogroup navigation. Screenshots and the browser layout report are stored in ignored `.ui_review/`.

## Earlier updates · 1 November 2026

## Correct consensus-network connectivity

Corrected failed joins between catalogue family labels (`integrin alpha`, `PINCH-like`, etc.) and reference/module labels (`integrin_alpha`, `PINCH_like`). Formatting-only join keys preserve the source labels and keep biologically different families distinct. Restored family-module assignments and reference-symbol annotations in the generated inventory, plus matching endpoints and authored special-context links in the runtime family map. Primary candidate, crosswalk, interaction, module and authored HTML inputs are unchanged.

The consensus retains one node per actual selected orthogroup and all its selected members. Edges require A/B/C assigned family candidates at both endpoints in at least one common species; D/unassigned records and earlier family hypotheses do not transfer edges. Self-loops are excluded. Explicit source/target candidate IDs, reference families and shared species are carried into the standalone viewer and evidence downloads. The edge inspector uses those exact IDs instead of treating every family-labelled member of a mixed orthogroup as supporting the edge. Family-role localization rules recognize the same formatting variants.

The complete source snapshot retains 579 nodes. Reference-supported unique pairs increased from 30 to 747, connecting 90 orthogroups; 489 orthogroups remain unconnected under the current reference map. All graph metrics, communities, matrices, module neighborhoods and layouts are recomputed from the corrected pairs. The existing hide-unconnected option and every catalogue grade remain available. Data/projection version keys invalidate stale cached graphs.

Application files updated:

- `library_refresh.py`
- `data.py`
- `curated_network.py`
- `consensus_view.py`
- `consensus_view.html`
- `test_consensus_projection.py` (new)
- `test_consensus_layout.py`
- `test_consensus_view.cjs`
- `README.md`
- `UPDATE_MANIFEST.md`

Regenerated outputs: `adhesome_network/Schistosome_adhesome_family_inventory.csv` and runtime `.atlas_cache/library_refresh.json`. The reference-edge and candidate-member CSV mirrors are unchanged when their contents already agree. Validation artifacts use the existing ignored `.ui_review/` directory.

Validation passed: independent per-species graph reconstruction and orthogroup union reproduce all 747 pairs; every edge's family, grade, shared species and candidate IDs reconcile to primary annotations. Formatting-only changes preserve graph connectivity. Library refresh/cache/read-only-host regressions pass. Streamlit verifies counts, isolate filtering, centrality/matrices and evidence downloads. All 579 nodes pass real browser clicks with exact candidate/neighbor mappings; four deterministic collision-free layouts, one-/two-step highlighting, module focus, hide/restore, search, node dragging, labels, zoom, vector export, offline rendering and desktop/tablet behavior pass. Primary scientific input hashes remain unchanged.

## Earlier updates · 28 October 2026

## Separate phylogeny collections and linked candidate dossiers

Added independent Family-level phylogenies and Orthogroup trees browsing views. Searches and tree selections persist separately, new files are still discovered automatically, and incoming orthogroup links select the appropriate collection. Family labels and source orthogroups appear separately from the original orthogroup-tree inventory. Missing-companion notices describe the active collection.

Tree/input sequence IDs now link directly to the existing candidate dossiers. All exact matching catalogue records are retained, including alternate annotations, repeated IDs and candidates absent from the final inferred tree. Family/folder spelling differences no longer suppress candidate matches. The table preserves catalogue species/family/grade/classification, marks in-tree status, links each dossier and exports every linked record. Selecting a candidate enlarges its tree marker and provides a direct dossier button. Source tree topology and annotations are unchanged.

Files updated: `phylogeny_view.py`, `app.py`, `test_family_phylogeny_formats.py`, `PHYLOGENY.md`, `README.md`, `UPDATE_MANIFEST.md`.

Validation passed: seven completed family trees (609 visible tips) and 22 orthogroup trees are classified into separate collections; exact candidate matching, repeated-record/grade preservation, absent-input status, empty results, dossier URLs, tip highlighting, retained per-collection searches/selections and incoming orthogroup routing. The targeted Streamlit tests and existing filename/layout/download checks passed. Candidate workbooks and inferred tree files were not modified.

## Mismatch-only priority flags and family phylogeny formats

Research priority comparisons now flag and list only mismatches; matching rows and their boolean agreement column are removed from presentation. References and brief downloads remain available. Explicit legacy/current family-name aliases prevent punctuation-only false mismatches and link to the actual catalogue family without altering its annotation or classification. Parser tests now reflect the updated two-class integrin brief while retaining coverage of unassigned/provisional clauses.

Phylogeny discovers both `gene_tree.treefile` and `tree.treefile` recursively in `Phylogeny` (including its `family_phylogeny` subdirectory) and a top-level `family_phylogeny`. Reports accept `gene_tree.iqtree`/`tree.iqtree`; alignments accept `trimmed.faa`, `trimmed.fasta`, and the requested `trimed.fasta`. Nested and flat layouts work; duplicate names resolve to one run with legacy-name precedence. Downloads preserve the filenames actually present. Both directory roots participate in source signatures. Available trees remain visible while optional companions await addition.

Family tip tables now use `panel_label`, `length_aa`, and `source_orthogroup` alongside the earlier metadata format. Candidate markers use exact catalogue IDs when flags are absent. All original records remain visible; `in_tree` marks input records absent from the inferred tree, and summary counts describe the displayed tree. Existing Newick support labels and exact descendant-set branch evidence remain intact.

Validation: matching/mismatching priority presentations, all filename/layout variants, companion ZIPs, automatic discovery/signature changes, incomplete runs, duplicate-name precedence, all seven completed new family trees (609 visible tips) alongside 22 existing trees, and Streamlit family/original-tree switching, candidate metrics and empty search. No analysis was run, and source workbooks/tree files were not edited or deleted.

Files updated or added:

- `research_priorities.py`
- `phylogeny_view.py`
- `data.py`
- `test_family_phylogeny_formats.py` (new)
- `test_research_priorities.py`
- `test_research_priorities.cjs`
- `PHYLOGENY.md`
- `README.md`
- `UPDATE_MANIFEST.md`

## Earlier updates · 27 October 2026

## New interspecific orthogroup summary report

Added the new formatted XLSX report and marked-variation TSV to Orthology's existing explorer. The full workbook covers 579 groups; marked/pronounced sheets contain 46/8 groups and are membership subsets, not extra observations. The 298-group exact-profile TSV report remains a separate selectable view. Its shared supported-copy counts agree with the workbook, and direct drill-through preserves the original support statistics.

The parser detects actual headers beneath titles/notes. Source counts reconcile to 4,355 total copies: 1,050 supported (925 specific, 125 broad), 3,278 unresolved, 25 ambiguous and two provisional. Ambiguous/provisional copies are not folded into unresolved. A/B totals and species-level supported-copy counts are absent from this summary and are not inferred. Report Δ thresholds remain descriptive. Source family labels, reference evidence and complete candidate records remain available.

Updated/added files for this addition:

- `orthogroup_variation.py` (new)
- `orthogroup_dashboard.py`
- `orthology_explorer.py`
- `test_orthogroup_variation.py` (new)
- `test_orthogroup_statistics.py`
- `test_orthogroup_statistics.cjs`
- `README.md`
- `UPDATE_MANIFEST.md`

Source hash, count, seven-species, support-state, subset and overlap checks passed. Streamlit checks passed for all three summary figures, marked/pronounced filters, group selection, empty results, report switching and exact-profile drill-through. Workbook and TSV bytes are unchanged. Browser review artifacts use the `orthogroup-summary-` prefix in ignored `.ui_review/`.

## Topological analysis for every imported STRING network

Unified API fetches and single/multiple TSV uploads behind a common topology engine and analysis workspace. Imports are retained independently by species/type/source content, with exact reimport replacement, version-distinguishing labels and legacy-session migration. Switching query species or leaving its taxon unconfigured no longer hides saved networks. Initial display retains all imported scores; the API retrieval threshold and subsequent display filters remain explicit.

Added comprehensive node/edge/global/component metrics, confidence strength and confidence-weighted PageRank, component-normalized eigenvectors, degree distributions/rankings/correlations, articulation proteins/bridges, five matrices, default comparison of all three applicable clustering methods and parameterized clustering viewers. Edge evidence channels and exact candidate mappings remain available. Graph paths are unweighted hops; confidence is not treated as a distance or affinity. Undefined, size-limited and unconverged outputs remain explicitly unavailable. Large visualization layouts avoid the optional SciPy dependency and do not truncate nodes.

All saved imports can be analyzed independently in one batch, producing comparison tables and combined analysis archives. ZIP outputs contain original source TSVs, metrics, component summaries, algorithm availability, default cluster memberships and convergence/method provenance. Current displayed-graph downloads include their filter scope; batch analyses use whole imported graphs. Existing metazoan projection algorithms and primary annotation data were not modified.

Files updated or added:

- `string_analysis.py` (new)
- `string_analysis_view.py` (new)
- `string_workbench.py`
- `topological_clustering.py`
- `test_string_analysis.py` (new)
- `test_string_import_analysis.cjs` (new)
- `README.md`
- `UPDATE_MANIFEST.md`

Numerical/source checks passed for functional/physical networks, API/website exports, both score scales, reversed/duplicate edges, independent PageRank solutions, exact NetworkX centralities, component distances, five matrices, clustering outputs, strict JSON/ZIP provenance, multi-species import retention, isolates, zero confidence and 501-node analysis/layout without SciPy. Existing clustering and sequence-mapping regression checks passed. Streamlit checks passed for all sections, matrices, clustering methods, batch comparison/download, import switching, removal and empty filtered graphs. Browser validation uses real multi-file uploads, optional mapping, retained isolates, full initial score coverage, network switching and analysis controls; artifacts are stored in ignored `.ui_review/`.

## Orthogroup Statistics & Explorer

Integrated the three new orthogroup TSVs into the existing Orthology page. The original candidate/reference-orthologue workspace remains available through the workspace selector. The complete exact-copy-profile table defines the dashboard universe; focused 1:1/2:2 files provide membership flags and never add duplicate rows to totals.

Current source reconciliation: 298 groups, 51 supported 1:1 and 12 supported 2:2 groups; 49 complete, 14 partial and 235 with no supported family identity; 488 supported copies / 2,289 total candidates; grade A = 488 and B = 0; specific support = 433 and broad support = 55. All seven species are represented, and every reported count sum agrees with the species fields. Source TSV hashes are unchanged.

Added compact metrics, species/family/profile/classification/support filters, six interactive chart views, a sortable/selectable orthogroup table, species-level details, exact-ID candidate dossier links, matching phylogeny links, source/count diagnostics and downloads. The dashboard retains distinctions between reported copies, supported identities and current Atlas candidate records. New profiles are discovered from updated sources. Copy-profile similarity is not interpreted as definitive orthology or paralogy evidence.

Updated or added application files:

- `orthogroup_statistics.py` (new; source validation, filtering, statistics and chart models)
- `orthogroup_dashboard.py` (new; dashboard, interaction callbacks, explorer and details)
- `orthology_explorer.py` (workspace integration and exact orthogroup routing)
- `research_priorities.py` (workspace-aware Orthology and Phylogeny links)
- `phylogeny_view.py` (preselected orthogroup query)

Validation and documentation:

- `test_orthogroup_statistics.py` (new)
- `test_orthogroup_statistics.cjs` (new)
- `README.md`
- `UPDATE_MANIFEST.md`

Automatically regenerated during application testing from the latest candidate workbook:

- `adhesome_network/Schistosome_adhesome_family_inventory.csv`
- `adhesome_network/Schistosome_adhesome_candidate_node_members.csv`

No source TSV, scientific workbook, raw reference interaction, crosswalk or network algorithm was edited for this feature. Runtime dependencies are unchanged.

Validation passed: source totals/subset agreement and seven-species checks; mutation fixtures for new profiles, duplicates, conflicting subset records and invalid schemas; exact filtering and dossier links; Streamlit startup, six visualizations, both subsets, search/empty/reset and preserved reference views. Real browser clicks passed for profile, family, classification, support and species bars, heatmap cells and table rows. Reset clears selections and stale events from replaced charts are ignored. Desktop/tablet review has no page errors or horizontal page overflow. Reports/screenshots are in `.ui_review/`, including `orthogroup-browser-validation.json`. Numbered heatmaps also use integer count legends and black labels, retaining the standard Atlas PNG/SVG exports.

## Motif annotation join for repeated protein IDs

Fixed the `many_to_one` MergeError in both Protein dossier → Motif and Motif explorer. The candidate workbook contains 4,361 records for 4,359 unique protein IDs. `Srhoda__SRDH2_99780` and `Srhoda__SRDH2_99800` each occur twice, with matching core annotations and different orthology text.

`data.annotate_motif_sites` creates a unique lookup per ID by combining every distinct family/species/protein-annotation label, then performs the validated left join. This preserves one output row per input motif row without deleting candidate records, dropping motif hits, selecting an arbitrary family, or multiplying counts. Missing candidates retain empty annotation fields. Existing motif-source columns are preserved if names overlap, and the motif view displays a caption for repeated catalogue IDs.

Updated files:

- `app.py`
- `data.py`
- `test_motif_annotations.py` (new)
- `README.md`
- `UPDATE_MANIFEST.md`

Validation: `python test_motif_annotations.py` passed. The two affected dossiers retain exactly 1 and 3 motif sites. The actual shared `motif_view` function was exercised with a display-capture harness for all 13,814 catalogue-matched motif rows, both duplicate IDs, function/tier filters, empty results and full table downloads. Fixtures also cover different family assignments under one ID, identical motif rows, missing candidates and metadata-column collisions. Workbook hashes were unchanged; syntax checks passed. This validation does not claim a live Streamlit/browser run. No scientific workbook, family assignment, network input or generated network CSV was edited by this correction.

---

# Atlas update · 25 October 2026

## Family-assignment audit schema correction

The workbook header `identity rule` now maps to the canonical `identity_rule` used by the audit table and candidate profiles. The loader retains the original header and values, adds a canonical field, and preserves existing canonical values when both forms occur. Optional audit fields are displayed when present; unavailable fields are identified in a caption rather than causing a KeyError or fabricating annotations. The full candidate CSV download remains available, and stage-one family hypotheses remain explicitly separate from audited family assignments.

A data-schema version invalidates cached catalogue/profile data after this fix. Updated files for this correction: `app.py`, `data.py`, `test_audit_schema.py` (new), `README.md`, and `UPDATE_MANIFEST.md`. No scientific workbook was edited.

Validation: `python test_audit_schema.py --app` checks spaced/underscored headers, canonical precedence, absent optional fields, empty selections, the complete current audit inventory, profile values and the Streamlit audit view with Unassigned filtering.

## Priority brief and automatic source refresh

The priority brief now recognizes **unassigned** and **unresolved** alongside the earlier provisional wording. All 14 brief counts match the current catalogue. The nine unassigned integrin-alpha hypotheses are counted using their recorded stage-one hypothesis; their audited classification remains D/unassigned. Candidate profiles expose that distinction explicitly.

The Atlas checks primary-source file changes every 30 seconds while open and reloads the catalogue, counts, candidate profiles, current orthology reports, family map and orthogroup consensus network. A change also takes effect on the next app load. Reference-family edges are regenerated from `adhesome_network/interactions.csv` and `Schistosome_human_gene_family_crosswalk.csv`; stale generated edges are no longer authoritative.

The three derived CSVs below are atomically rewritten only when their contents change. Generated outputs are excluded from the source-change fingerprint to prevent refresh loops. If storage is read-only, the same regenerated data remains available in memory. Refresh diagnostics and source hashes are recorded in the ignored `.atlas_cache/library_refresh.json`.

`family_module_annotations.csv` preserves curated family-to-module assignments independently of generated counts. New families without a module annotation remain explicitly unresolved. The authored interactive HTML is preserved and refreshed in memory with the current candidate inventory, A/B/C/D counts and qualifying reference-family edges. New family interactions require an explicit curated crosswalk entry; unassigned records do not acquire family interactions from stage-one hypotheses. Existing special interaction context is retained only where its named candidates still have the corresponding audited family assignments.

Current inventory: **4,361 records**, seven species, **A = 1,042; B = 21; C = 2; D = 3,296**. The orthogroup consensus contains **578 nodes and 743 unique pairs**, with 4,357 candidate records; four records without an orthogroup remain accessible in the catalogue and dossier. Large consensus layouts now use deterministic NumPy calculations without requiring SciPy.

Automatic refresh observes files available to the running app. Desktop changes must still be published to the deployed GitHub/Streamlit application. This refresh reads updated analysis outputs; it does not rerun sequence annotation, orthology or phylogenetic inference.

### Files updated or added in this update

Application and interface:

- `app.py`
- `data.py`
- `library_refresh.py` (new)
- `source_watch.py` (new)
- `curated_network.py`
- `candidate_profiles.py`
- `linked_explorer.py`
- `research_priorities.py`
- `atlas_styles.py`
- `design_system.py`
- `consensus_view.py`
- `consensus_view.html`

Content, metadata and regenerated outputs:

- `Target_prioritization.md`
- `adhesome_network/family_module_annotations.csv` (new)
- `adhesome_network/Schistosome_human_reference_family_edges.csv`
- `adhesome_network/Schistosome_adhesome_family_inventory.csv`
- `adhesome_network/Schistosome_adhesome_candidate_node_members.csv`

Validation:

- `test_library_refresh.py` (new)
- `test_auto_refresh.cjs` (new)
- `test_research_priorities.py`
- `test_consensus_layout.py`
- `test_consensus_view.cjs`
- `test_current_library.py`
- `test_candidate_profiles.py`

Documentation and configuration:

- `README.md`
- `UPDATE_MANIFEST.md`
- `.gitignore`

### Functional validation

- Primary-source mutation fixtures verify regenerated edges, provenance, exact candidate membership, grade D handling, removed families, read-only fallback, stable output timestamps and orthology-report updates.
- Live browser validation measured automatic refresh at **33.491 seconds**, without manual reload; family-map and consensus counts matched their current inputs. The unassigned example `Sman__Smp_170280` retained its profile across all four consensus layouts.
- Independent browser clicks passed for **all 578 orthogroups**. Tests also cover exact candidate lists and classifications, pathway traversal, module focus, hide/restore, search, dragging, zoom, labels, vector export, offline rendering and desktop/tablet layouts.
- Current-library and layout tests verify source preservation, non-overlapping repeatable layouts, current phylogeny discovery and linked viewer/simulator APIs. No primary scientific workbook, raw interaction file, crosswalk or authored family HTML was rewritten.

Browser reports and screenshots are in the ignored `.ui_review/` directory, including `automatic-refresh-browser.json` and `consensus-browser-validation.json`.

---

# Atlas update · 20 October 2026

The atlas now uses the replacement seven-species library, metazoan reference projection and current orthology/phylogeny runs.

## Updated or added files

- [.gitignore](.gitignore)
- [app.py](app.py)
- [atlas_styles.py](atlas_styles.py)
- [curated_network.py](curated_network.py)
- [data.py](data.py)
- [family_merges.py](family_merges.py)
- [feedback.py](feedback.py)
- [identifier_labels.py](identifier_labels.py)
- [linked_explorer.py](linked_explorer.py)
- [networks.py](networks.py)
- [orthology_explorer.py](orthology_explorer.py)
- [phylogeny_view.py](phylogeny_view.py)
- [reconstruction.py](reconstruction.py)
- [simulator.py](simulator.py)
- [string_workbench.py](string_workbench.py)
- [test_current_library.py](test_current_library.py)
- [test_smart_links.py](test_smart_links.py)
- [test_topological_clustering.py](test_topological_clustering.py)
- [README.md](README.md)
- [PHYLOGENY.md](PHYLOGENY.md)
- [README_schistosome_adhesome_interactive.md](README_schistosome_adhesome_interactive.md)
- [README_adhesome_hypothesis_simulator.md](README_adhesome_hypothesis_simulator.md)
- [CITATIONS.md](CITATIONS.md)
- [cleanup_manifest.json](cleanup_manifest.json)
- [UPDATE_MANIFEST.md](UPDATE_MANIFEST.md)

## Removed files

334 files removed, totaling 172.4 MiB. This includes 300 redundant phylogeny intermediates; six visualization/reproducibility companions per run remain. Primary replacement workbooks, network assets and family FASTAs were preserved. All paths, sizes and SHA-256 hashes are recorded in cleanup_manifest.json.

Apply the same deletions when updating a separate GitHub checkout so historical modules and the old orthogroup dictionary do not remain in the deployed library.

- `candidate_annotations.py`
- `candidate_prioritization.py`
- `evidence.py`
- `family_audit.py`
- `motif_explorer.py`
- `nanoscale_architecture.py`
- `orthogroup_annotations.py`
- `orthology_views.py`
- `prioritization_evidence.py`
- `prioritize_candidates.py`
- `prototype.py`
- `refresh_interactive_map.py`
- `phylogeny_family_groups.tsv`
- `identifier_map.tsv`
- `identifier_map_expanded8.tsv`
- `identifier_map_expanded8.tsv.gz`
- `orthology/Orthogroup_dictionary.xlsx`
- `test_atlas.py`
- `test_candidate_annotations.py`
- `test_candidate_prioritization.py`
- `test_cloud_schema.py`
- `test_feedback.py`
- `test_figure_exports.py`
- `test_linked_explorer.py`
- `test_matrix_simulator.py`
- `test_motif_explorer.py`
- `test_orthogroup_annotations.py`
- `test_orthology.py`
- `test_phylogeny.py`
- `test_prioritization_evidence.py`
- `test_prototype.py`
- `test_reconstruction.py`
- `test_simulator.py`
- `test_string_workbench.py`
- `Phylogeny/adhesome_candidates_list/OG0000076/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000076/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000076/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000076/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000094/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000094/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000094/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000094/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000122/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000122/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000122/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000122/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000129/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000129/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000129/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000129/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000130/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000130/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000130/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000130/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000148/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000148/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000148/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000148/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000180/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000180/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000180/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000180/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000197/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000197/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000197/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000197/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000199/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000199/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000199/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000199/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000211/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000211/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000211/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000211/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000242/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000242/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000242/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000242/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000246/duplication_evidence.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000246/duplication_status.json`
- `Phylogeny/adhesome_candidates_list/OG0000246/members.faa`
- `Phylogeny/adhesome_candidates_list/OG0000246/orthology_edges.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000076/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000094/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000122/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000129/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000130/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000148/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000180/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000197/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000199/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000211/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000242/inference/trimmed_aliases.faa`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/aligned.faa`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/aligned.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/alignment_qc.json`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/command_1.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/command_2.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/command_2.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/command_3.stderr.log`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/command_3.stdout.log`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.bionj`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.ckp.gz`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.contree`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.log`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.mldist`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.model.gz`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.splits.nex`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/gene_tree.ufboot`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/trimal_identifiers.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/trimal_input.faa`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/trimmed.sequence_qc.tsv`
- `Phylogeny/adhesome_candidates_list/OG0000246/inference/trimmed_aliases.faa`

## Verification

- 2,664 candidates across seven species, 64 families and 337 current orthogroups.
- 14,032 motif records; original FASTAs provide 4,692 unique sequence IDs.
- All atlas page smoke checks and S. mansoni STRING family-query planning passed.
- Current phylogeny has 17 trees; a newly added partial tree is discovered without requiring its pending companions.
- Map/simulator JavaScript syntax, new family selection API and seven-species simulation controls passed.
- SMART query contracts and topological clustering algorithm tests passed.


## Candidate-profile links and page visibility · 20 October 2026

All 2,664 candidates are linked to the map through exact accessions and current family assignments. Profiles include domain/motif/orthology evidence, dossier deep links, JSON export, partner-family browsing and candidate-aware simulation context. Components and Interactions now use full-width section selectors; SVG networks support responsive sizing and full-screen exploration.

Updated files:

- [app.py](app.py)
- [candidate_profiles.py](candidate_profiles.py)
- [linked_explorer.py](linked_explorer.py)
- [adhesome_network/Schistosome_adhesome_rebuilt.html](adhesome_network/Schistosome_adhesome_rebuilt.html)
- [curated_network.py](curated_network.py)
- [string_workbench.py](string_workbench.py)
- [vector_network.py](vector_network.py)
- [atlas_styles.py](atlas_styles.py)
- [test_current_library.py](test_current_library.py)
- [test_candidate_profiles.py](test_candidate_profiles.py)
- [README.md](README.md)
- [README_schistosome_adhesome_interactive.md](README_schistosome_adhesome_interactive.md)
- [UPDATE_MANIFEST.md](UPDATE_MANIFEST.md)


## Node-click paths and side profiles · 20 October 2026

Updated `candidate_profiles.py`, `adhesome_network/Schistosome_adhesome_rebuilt.html`, `test_candidate_profiles.py`, `README_schistosome_adhesome_interactive.md` and this manifest. Node selection now opens a candidate profile automatically at the top of a visible side panel and highlights direct/two-step/component or shortest paths. Desktop and mobile side-panel layouts were corrected. Exact candidate IDs, evidence joins, shortest routes, unreachable targets, candidate switching and simulation context passed regression checks.


## Persistent candidate–path simulation · 20 October 2026

Node clicks and side-panel candidate choices now synchronize exact profile and highlighted-path context with the simulator. The candidate profile remains visible in map, simulation and combined views. Path gates, the same-path baseline and the S. mansoni-only VKR1 rule are explicit, and context is retained in downloads.

Updated files:

- [app.py](app.py)
- [candidate_profiles.py](candidate_profiles.py)
- [linked_explorer.py](linked_explorer.py)
- [simulator.py](simulator.py)
- [adhesome_network/Schistosome_adhesome_rebuilt.html](adhesome_network/Schistosome_adhesome_rebuilt.html)
- [test_candidate_profiles.py](test_candidate_profiles.py)
- [test_linked_context.py](test_linked_context.py)
- [README_schistosome_adhesome_interactive.md](README_schistosome_adhesome_interactive.md)
- [README_adhesome_hypothesis_simulator.md](README_adhesome_hypothesis_simulator.md)
- [UPDATE_MANIFEST.md](UPDATE_MANIFEST.md)

## Independent node selection repair · 20 October 2026

Actual Chromium pointer clicks reproduced the selection failure: SVG pointer capture retargeted pointer-up to the canvas, so the previous handler could not identify the clicked family. The repaired handler remembers the pointer-down family/edge and distinguishes clicks, pans and cancelled gestures. `atlasSelectNode` centralizes pointer, keyboard, partner and candidate selection. The generator reapplies the repair idempotently without changing the authored DATA inventory or topology.

The side panels show complete filtered candidate lists and A/B/C totals, auto-open a matching profile, and explicitly clear profiles for nodes without candidates. Connected-component highlighting is the default, with direct/two-step and shortest-path controls retained. Context nodes are available as shortest-path targets. Only recorded, undirected associations are traversed.

Validation: real Chromium clicks passed for all 64 candidate families across six levels and the SmVKR1 context node. All 11 S. mansoni collagen profiles were inspected through the actual candidate selector (A=11/B=0/C=0). All seven collagen species sets, the intercalatum A=9/C=1 case, confidence filters, full candidate IDs/counts, actual-edge paths/dimming, empty states, keyboard/partner navigation, pan/zoom/search/filter controls, SVG download, mobile drawer and generated linked simulator/profile view passed. No external requests occurred. All 2,664 profile IDs, domain/motif/orthologue joins and native graph inventory/grades match the current workbooks.

The current curated topology has no collagen-family edges. Its selected node and candidates are displayed with an explicit no-recorded-connections message; no biological edge was invented.

Files updated for this repair:

- [candidate_profiles.py](candidate_profiles.py)
- [linked_explorer.py](linked_explorer.py)
- [adhesome_network/Schistosome_adhesome_rebuilt.html](adhesome_network/Schistosome_adhesome_rebuilt.html)
- [test_node_interactivity.cjs](test_node_interactivity.cjs) — new real-browser regression suite
- [test_candidate_profiles.py](test_candidate_profiles.py)
- [test_linked_context.py](test_linked_context.py)
- [README_schistosome_adhesome_interactive.md](README_schistosome_adhesome_interactive.md)
- [UPDATE_MANIFEST.md](UPDATE_MANIFEST.md)

## Introduction read-more documentation · 20 October 2026

Added two collapsed, clickable read-more sections directly below the About text and above the summary metrics. They render the complete interactor and simulator README files inside the page, using the local Markdown files so content stays synchronized and remains available without external hosting.

Updated files: `app.py`, `UPDATE_MANIFEST.md`.

## Scientific E-value import compatibility · 20 October 2026

Removed the scientific_evalue import from app.py and string_workbench.py. Domain CSV and STRING alignment exports now use the standard-library Decimal formatter directly, so the display/export formatting does not depend on the STRING module providing a new helper. Scientific notation in tables and domain tooltips remains unchanged. This resolves the reported import location when deployment contains an older string_fetch.py without scientific_evalue. Publish both updated Python files together; the standalone STRING script retains its existing formatter.

Validation: Python syntax, formatter precision/missing-value checks and offline STRING sequence-mapping regression checks passed.

Updated files: `app.py`, `string_workbench.py`, `UPDATE_MANIFEST.md`.
## Scientific discovery workspace redesign · 20 October 2026

Implemented the visual brief using a shared offline design system: evergreen/neutral surfaces, restrained gold accents, high-contrast scientific text, consistent spacing, borders, focus states and confidence badges. The main workspace now uses the available width. Institutional logos remain unmodified and preserve their aspect ratios in a compact identity strip. The approved About text and runtime catalogue counts share a geometric gradient hero; the two README expanders follow immediately beneath it. Every original navigation section and catalogue filter remains available, including the native sidebar collapse control.

The interactive network and persistent candidate dossier are the primary workspace. Duplicate embedded headers were removed; filters, supplementary display/path options and reference evidence remain expandable. A readable-width view and adjustable, wrapping labels complement Fit all, zoom, pan, full screen and SVG download. Family/candidate headings, A/B/C totals and badges, identifiers, architecture, orthology and expandable evidence are clearly structured. The simulator and consensus SVG workspaces share the same control and surface styling.

Scientific integrity: no source workbooks, FASTAs, interaction CSVs, orthology or phylogeny files were modified. The native HTML DATA inventory/topology remains unchanged. Candidate selection, underlying graph traversal, confidence classifications and scientific calculations retain their existing meaning. The standalone map was regenerated with embedded evidence and offline design tokens; no new runtime dependency was added.

Validation covers actual Chromium node clicks for all 64 candidate families across six levels plus the context node, complete candidate lists/A/B/C totals, all 11 S. mansoni collagen profiles, species/confidence filters, recorded-edge highlighting, empty states, pan/zoom/search/keyboard controls, SVG download and linked simulator profile persistence. All 2,664 profile/evidence joins and idempotent generation passed. The live-application review script checks desktop 1920×1080 and tablet 1024×1366 layouts, horizontal overflow, native sidebar collapse and Components/Interactions navigation. Review screenshots and dimension reports are generated under ignored `.ui_review/`.

Updated or added files:

- `design_system.py` (new)
- `atlas_styles.py`
- `branding.py`
- `app.py`
- `.streamlit/config.toml`
- `candidate_profiles.py`
- `linked_explorer.py`
- `simulator.py`
- `vector_network.py`
- `adhesome_network/Schistosome_adhesome_rebuilt.html`
- `test_candidate_profiles.py`
- `test_node_interactivity.cjs`
- `test_ui_redesign.cjs` (new)
- `.gitignore`
- `README.md`
- `README_schistosome_adhesome_interactive.md`
- `README_adhesome_hypothesis_simulator.md`
- `UPDATE_MANIFEST.md`
## STRING original-sequence mapping · 20 October 2026

STRING identifier resolution did not recognize the tested Atlas gene ID Smp_079760, while the version-pinned service and a control identifier worked. STRING's official sequence-search implementation confirmed the direct endpoint POST /api/json/similarity_search. The Atlas now defaults to original amino-acid sequence queries from its existing family FASTAs. Identifier-only mode remains available, and automatic mode retains successful ID mappings while sequencing unresolved inputs, including identifier HTTP 404 responses.

Sequence requests are POSTed in sequential batches, at least one second apart. Every alignment hit, identity, E-value, bitscore, representative ID and query ID is retained. Configurable identity/E-value/relative-bitscore-gap criteria select a unique representative; ambiguous or unavailable sequences remain explicitly unresolved. No host substitution or family-name matching is used. Several candidates sharing one STRING representative retain all candidate IDs. Mapping signatures include the numeric taxon, original sequence hashes, mode and criteria; network score/neighborhood changes do not require remapping.

The UI and standalone WSL script export original FASTA, configuration, selected mapping, all alignment evidence and complete request provenance. Network analysis retains the mapped candidate/profile/family/orthogroup joins and the original query taxon. Scientific candidate classifications and the default curated consensus graph are unchanged.

Validation: regression tests passed for identifier HTTP404 recovery, retained successful IDs, POST transport, alignment schema and species checks, ambiguity, missing sequences, service errors, evidence retention and batching. Live STRING 12.5 tests mapped Sman__Smp_079760 → 6183.A0A3Q0KIA3 (100% alignment identity), Sman__Smp_020540 → 6183.A0A3Q0KD53 and Sman__Smp_014850 → 6183.G4VBX5, retrieved three network edges and verified exact Atlas candidate joins. The browser test exercises the page's original-sequence default, mapping TSV download and topology workspace.

Updated or added files:

- `app.py`
- `string_fetch.py`
- `string_workbench.py`
- `test_string_sequences.py` (new)
- `test_string_workbench.cjs` (new)
- `README.md`
- `CITATIONS.md`
- `UPDATE_MANIFEST.md`
## Scientific E-value notation · 20 October 2026

STRING resolved-mapping and sequence-alignment tables now explicitly format E-values in scientific notation, retaining numeric sorting and the original numeric data for filtering. Mapping and all-hit TSV exports also use scientific notation, preserving decimal precision. Request/response evidence and numeric JSON provenance remain unchanged.

Updated files: `string_workbench.py`, `string_fetch.py`, `UPDATE_MANIFEST.md`.
## Protein dossier domain E-values · 20 October 2026

Applied scientific E-value notation to the Protein dossier Domains table, CDD architecture hover tooltips and domain CSV download. The shared atlas table renderer also recognizes E-value/evalue/e_value column names, so domain evidence previews in Source Library receive the same display formatting. Numeric data and sorting remain intact; CSV formatting preserves decimal precision and missing values. Source workbooks and domain assignments are unchanged.

Updated files: `app.py`, `UPDATE_MANIFEST.md`.

## Research priorities and target discovery · 22 October 2026

Added a responsive scientific research entry point to the Introduction, after the About summary and README links and before the existing interactive map. Reusable source-driven components read Target_prioritization.md at runtime: three featured cards (tetraspanins, calpains, integrin α/β), seven additional family groups, a six-criterion vaccine/antibody versus small-molecule comparison, seven proposed first investigations and all five original DOI references. Supported computational annotations, provisional assignments, published evidence and proposed research have separate text badges. The Sm-TSP-2 orthogroup caveat and the integrin α provisional distinction remain explicit. No new priority score is calculated.

The brief's original counts are preserved and compared with unique proteins in the complete live catalogue, independent of sidebar filters. All 14 comparisons currently agree. Differences display both values; absent identifiers are labeled unavailable, and ambiguous accession suffixes retain all exact matches. Protein links reuse the dossier route. Family links open Components → Candidate catalogue with the exact family and compatible filters; orthogroup links open the matching Orthology collection and query. Routing initializes once so later manual navigation remains functional. Research controls run in a Streamlit fragment without regenerating the linked map on every control change.

Validation: source counts, IDs, evidence references, missing/ambiguous records, synthetic count discrepancies, deep-link state and unchanged source hashes passed. Actual Chromium testing passed for all three destination routes, evidence expanders, additional families, framework controls, roadmap and references. Desktop 1920px, tablet 1024px and mobile 600px layouts have no page/card horizontal overflow. The existing desktop/tablet UI regression also passed map selection, candidate profiles, simulator profile retention, Components and Interactions. The broader existing library test passed candidate/grade/motif and consensus-graph assertions, then stopped at its pre-existing minimum of 17 phylogeny runs: the current library has nine discoverable runs. Phylogeny files and that unrelated assertion were not modified.

No scientific source workbook, FASTA, orthology result, phylogeny result, network HTML or analytical scoring pipeline was changed. Keep Target_prioritization.md beside app.py when deploying the updated modules. Review images and layout measurements are generated under ignored .ui_review/.

Updated or added files:

- `research_priorities.py` (new)
- `app.py`
- `atlas_styles.py`
- `orthology_explorer.py`
- `test_research_priorities.py` (new)
- `test_research_priorities.cjs` (new)
- `README.md`
- `UPDATE_MANIFEST.md`

## Biologically organized orthogroup consensus network · 22 October 2026

Replaced the consensus viewer's compact spring layout and top-200 node drawing limit with a dedicated offline SVG spatial explorer. The full default graph retains 337 orthogroups, 9,738 unique projected pairs, all 11,480 reference evidence records and 2,664 exact candidate memberships. The projection builder, analytical node/edge tables, A/B/C classifications, orthology and all centrality/matrix/clustering calculations are unchanged. STRING and the separate family-level hypothesis/simulator viewers retain their existing rendering.

Four deterministic modes are available: cellular localization bands; packed functional-module cards with separate connected neighborhoods; the existing algorithmic communities; and seeded free-force initialization with collision-free grid placement. The same node is represented once even when it has multiple functional annotations. Layout coordinates and derived contextual regions are downloadable presentation metadata, cached with a hash of the annotation/layout rules.

Cellular placement requires agreement across all filtered member predictions. Singleton DeepLoc extracellular and membrane predictions are used directly; singleton cytoplasmic predictions combine with explicit audited family/inventory roles for proximal, signaling or cytoskeletal context. Multiple/missing/other-organelle predictions, conflicting members and unsupported cytoplasmic contexts remain unresolved. The full selection has 7 extracellular, 27 membrane, 24 proximal, 44 signaling, 36 cytoskeletal-context and 199 unresolved orthogroups. All individual localization/topology and architecture annotations remain inspectable. These are conceptual regions rather than measured spatial localizations.

Independent selection highlights the recorded one- or two-step undirected neighborhood, dims unrelated elements and populates a persistent side dossier with every associated candidate, A/B/C totals, exact protein/species/family identifiers, domain architecture and supporting evidence. Functional-module focus uses connected components within an annotated module, not broad family similarity alone. Switching layouts retains the selected orthogroup/candidate and local focus/hiding. Restore all, reset view, reset positions, search, keyboard selection, pan, zoom, readable-scale mode and dragging are included. Highlighted edges expose every corresponding reference evidence record with exact candidate-family mappings and PMID links.

Node radius is explicitly log-scaled by unique candidate count; compartment/module/community colors and independent confidence outlines have a visible legend. Black labels adapt to zoom, shorten at overview scale and suppress collisions. Centered labels fit within quantitative circles without resizing them. Edge routing uses curved paths and selection-focused opacity; every original pair remains in the embedded model. The requested hypothesis disclaimer is always visible. Offline interactive HTML, all layout/annotation CSVs, annotation rules, current-layout JSON and scalable SVG exports are available without new dependencies or external frontend resources.

Validation: full source hashes, exact node/pair identities, all evidence fields and reconstructed candidate-side evidence mappings, candidate memberships/grades and unchanged analytical input frames passed. Four layouts reproduce exactly and have no overlapping node circles; filtered and singleton/edge-free graphs also passed. Chromium pointer-click tests cover all 337 orthogroups and their complete profile/neighbor/grade mappings. Additional browser checks cover all six conceptual regions, all four layouts, candidate retention, two-step expansion, connected-module focus, hide/restore, exact accession search, labels/collision suppression, dragging/zoom, vector export and desktop/tablet layout. The exported standalone file is tested with external requests blocked. Before/after screenshots, the standalone review file and integrity/browser reports are stored under ignored `.ui_review/`.

Deploy the three production files together: `curated_network.py`, `consensus_view.py` and `consensus_view.html`.

Updated or added files:

- `curated_network.py`
- `consensus_view.py` (new)
- `consensus_view.html` (new)
- `test_consensus_layout.py` (new)
- `test_consensus_view.cjs` (new)
- `README.md`
- `UPDATE_MANIFEST.md`
