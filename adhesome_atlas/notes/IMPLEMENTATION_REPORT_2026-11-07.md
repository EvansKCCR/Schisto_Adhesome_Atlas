# Schisto-Adhesome Atlas implementation report

7 November 2026 · Atlas data 6 · literature registry 1.0 · adhesion lattice 4.0

## Candidate library and reconciliation

The active source is `files/adhesome_candidates_list.xlsx`, worksheet
`Audited_family_assignment`. The loader prefers `putative_audited_family_new`
and accepts the historical column name for older workbooks. The current
workbook has 4,359 rows with 4,359 unique protein IDs, seven species and
162 audited family labels. Protein names, annotation notes, grades,
architectures, topology, localization and orthogroup identifiers come from
the source annotations.

| Audited support category | Unique proteins |
| --- | ---: |
| Specific supported | 1,123 |
| Broad supported | 1,337 |
| Ambiguous | 13 |
| Provisional | 1 |
| Unresolved | 1,885 |

The 2,460 supported proteins span 88 distinct source family labels. The source
grade totals are A = 1,123, B = 0, C = 1,351 and D = 1,885. The Atlas uses
`family_support_level` for the support categories and retains grade as a
separate filter. Historical aliases for talin, filamin and ADAM permit joining
the current labels to the existing curated family and module tables.

The three crosswalk sheets contributed 14 publications, 27 representative
protein mappings and 19 family categories. The accession audit records 27
exact current IDs. `Sman__Smp_167010` uses the current Talin-like label and
`Sman__Smp_330190` now has grade A. Current supported-family counts changed
from 45 to 52 for HSP70-like, 19 to 12 for Abl family and 11 to 14 for talin.
The mapping export includes source rows, reported labels and grades, live
values and explicit correspondence status.

The registry records the cloned SmILK and SmNck2 loci from R02. It adds the
`Smp_020540` locus correspondence for the published SmPINCH transcript
`Smp_020540.2`. This is a locus-level link. `Smp_165070` and the parvin
candidates carry pathway context. The two R11 calpain IDs have published
accession correspondence. R07 distinguishes candidate kinase loci from
immunoreactive-band assignments. The Sm-TSP-2 records use family context and
the Sm14 crosswalk retains the supplied named-locus scope. R10 uses the
verified PubMed record 41397983 and stores the workbook's original URL.

## Publication registry

R01–R14 retain the crosswalk identifiers, study findings and source row
provenance. R15–R21 add seven metazoan references. R17 and R18 are reviews.
Each registry record includes DOI and PubMed links, evidence origin, study
species, methods, scope, and links to candidate IDs, families, pathways or
rules where available.

| ID | Publication and Atlas scope | DOI |
| --- | --- | --- |
| R01 | Beckmann et al. 2012, schistosome integrin cloning and reproduction | [Publisher](https://doi.org/10.1371/journal.pone.0052519) |
| R02 | Gelmedin et al. 2017, Smβ-Int1 and SmVKR1 multicomponent signalling | [Publisher](https://doi.org/10.1371/journal.ppat.1006147) |
| R03 | Beckmann et al. 2010, SmTK4 and gametogenesis | [Publisher](https://doi.org/10.1371/journal.ppat.1000769) |
| R04 | Kapp et al. 2004, gonadal SmTK3 and cytoskeletal signalling | [Publisher](https://doi.org/10.1016/j.molbiopara.2004.07.010) |
| R05 | Quack et al. 2009, SmDia, SmTK3 and SmRho1 | [Publisher](https://doi.org/10.1371/journal.pone.0006998) |
| R06 | Beckmann et al. 2011, SmTK6 Src/Abl hybrid kinase | [Publisher](https://doi.org/10.1074/jbc.M110.210336) |
| R07 | Ressurreição et al. 2014, PKC/ERK physiology | [Publisher](https://doi.org/10.1371/journal.pntd.0002924) |
| R08 | Tran et al. 2006, surface tetraspanins and vaccine challenge | [Publisher](https://doi.org/10.1038/nm1430) |
| R09 | Jia et al. 2014, Sm-TSP-2 EC2 structure and tegumental partners | [Publisher](https://doi.org/10.1074/jbc.M113.531558) |
| R10 | de Oliveira et al. 2025, Sm-TSP-2 mRNA vaccine challenge | [Publisher](https://doi.org/10.1038/s41541-025-01301-y) |
| R11 | Wang et al. 2017, tegumental calpains and fibronectin cleavage | [Publisher](https://doi.org/10.1038/s41598-017-13141-5) |
| R12 | Tendler et al. 1996, Sm14 antigen characterization | [Publisher](https://doi.org/10.1073/pnas.93.1.269) |
| R13 | Ly et al. 2025, Sm14 Phase II vaccine study | [Publisher](https://doi.org/10.3390/vaccines13030316) |
| R14 | Sotillo et al. 2015, schistosomulum tegument proteomics | [Publisher](https://doi.org/10.1016/j.ijpara.2015.03.004) |
| R15 | Kanchanawong et al. 2010, conceptual focal-adhesion strata | [Publisher](https://doi.org/10.1038/nature09621) |
| R16 | del Rio et al. 2009, force-dependent talin–vinculin recruitment | [Publisher](https://doi.org/10.1126/science.1162912) |
| R17 | Legate et al. 2006, IPP scaffold review | [Publisher](https://doi.org/10.1038/nrm1789) |
| R18 | Zhu et al. 2021, talin and kindlin assembly review | [Publisher](https://doi.org/10.1002/pro.4014) |
| R19 | Huet-Calderwood et al. 2014, primary kindlin–IPP binding evidence | [Publisher](https://doi.org/10.1242/jcs.155879) |
| R20 | Böttcher et al. 2017, primary kindlin–paxillin and Arp2/3 evidence | [Publisher](https://doi.org/10.1083/jcb.201701176) |
| R21 | Schaller et al. 1994, primary FAK–Src association evidence | [Publisher](https://doi.org/10.1128/MCB.14.3.1680-1688.1994) |

The interaction registry contains 13 published context records, 258 curated
reference-family projections and 19 simulated transitions. Published and
simulated entries are separate records. The projected entries retain the
source symbols, relationship types and PMIDs. Registry links on these entries
require an exact source PMID match. A projection requires supported endpoint
families in a shared species under the active filters. The live consensus
contains 579 orthogroups, 4,355 proteins with an orthogroup ID and 808
projected pairs. The other four proteins are available in the catalogue
and protein dossiers.
In mixed orthogroups, supported assignments with a known functional module
determine the conceptual placement. The broader domain-class members remain
visible with their source support and domains.

## Atlas views and simulator

**Citations** has searchable publications, the accession audit, family and
pathway context, and TSV/JSON exports. **Components** and **Protein dossier**
provide scoped literature views and the interaction workspace exposes
published, projected and simulated relationships. The catalogue map and
consensus edge inspectors display their evidence sources and references.
The target-prioritization brief retains its featured sections, tables and
experimental roadmap. It uses the current candidate counts and includes MAPK
and FABP priorities. The traceability TSV ties the recommendations to current
candidate IDs and separately labels accession, orthogroup and family context.

The original 3 × 3 I–T–V matrix and receptor lattice remain the structural
state. New occupancy variables track kindlin, ILK, PINCH, parvin, IPP,
IPP–actin, Nck2, VKR1, paxillin and actin regulators at each site. PINCH and
parvin recruit to ILK independently. IPP assembly requires kindlin, ILK,
PINCH and parvin. The separately configurable SmVKR1 branch requires
ILK/PINCH and Nck2. Both branches use one ILK/PINCH pool. The canonical
comparison panel uses the metazoan scaffold and signalling rules.

The model uses a force-transmitting talin–actin or IPP–actin link, a
dimensionless talin exposure threshold, force-sensitive vinculin recruitment,
reinforcement, relaxation and rupture. FAK/Src, paxillin and actin regulation
have separate controls and output variables. The optional PKC/MAPK and
Src/Syk/Abl/Rho outputs are pathway indices. Spatial strata and transition
probabilities are conceptual model inputs. Exports include the exact active
rule IDs, references, parameter values, seed, full local trajectories,
and the paired baseline for a selected candidate or path. The map refresh
groups the columns it needs and serializes each profile evidence table in
one pass to reduce the live page load.

## Reproduction

From the `adhesome_atlas` directory in PowerShell with the project
environment and Node available:

```powershell
.venv\Scripts\python.exe -X utf8 rebuild_evidence.py
.venv\Scripts\python.exe -X utf8 -m streamlit run app.py
```

The rebuild refreshes the standalone catalogue map and simulator, derived
inventory and candidate membership CSVs, literature and interaction exports,
priority trace, and provenance. The provenance JSON records the SHA-256 of
both workbooks, reference inputs and rule sources. Source book hashes for
this release are:

| Input | SHA-256 |
| --- | --- |
| `files/adhesome_candidates_list.xlsx` | `ab1add5c2e15ae6c73f6e6f5bb833daef16b6da36caa458218356f0c6497ed44` |
| `files/Schisto_adhesome_focused_literature_crosswalk.xlsx` | `dd20788edf1fe3435b23a2362cf01b053c1b5d287f7c5e0444570a39a58b35d5` |

## Validation

```powershell
.venv\Scripts\python.exe -X utf8 test_literature.py --app
node test_layered_simulator.cjs --browser
.venv\Scripts\python.exe -X utf8 test_linked_context.py
.venv\Scripts\python.exe -X utf8 test_research_priorities.py
.venv\Scripts\python.exe -X utf8 test_candidate_profiles.py
.venv\Scripts\python.exe -X utf8 test_library_refresh.py
node test_ui_redesign.cjs
node test_node_interactivity.cjs
```

These checks passed candidate and support fidelity, source worksheet coverage,
reference and accession reconciliation, exact DOI identifiers, scoping of
family and pathway evidence, updated priority counts, live Atlas evidence
views and standalone registry payloads. The simulator checks passed legacy
structural trajectory parity, force-sensitive recruitment, independent IPP and
SmVKR1 assembly, shared state, FAK/Src, regulator gates, rupture resets and
same-seed repeatability. The browser checked the three layers, mechanism DOI
links, IPP toggling and JSON download. Candidate/path synchronization passed
the linked workspace regression. All 28 priority-count comparisons matched.
The live browser checked the Parvin and ILK profiles, literature and simulator
linkage, desktop/tablet/mobile layouts, Components and Interactions. A separate
Chromium check verified all 162 family node selections, candidate sets,
grade counts and recorded paths in the standalone map.
The profile regression verified exact evidence joins and idempotent embedding.
The refresh regression checked source changes, regenerated mirrors, filters and
the fallback for read-only hosts.

## Files changed

- Data and navigation — `app.py`, `data.py`, `library_refresh.py`,
  `orthology_explorer.py`, `research_priorities.py`.
- Literature — `literature.py`, `literature_view.py`, `literature_browser.js`,
  `data/literature/reference_sources.json`, `data/literature/simulator_mechanisms.json`.
- Maps and simulation — `candidate_profiles.py`, `consensus_view.py`,
  `consensus_view.html`, `curated_network.py`, `linked_explorer.py`,
  `simulator.py`, `simulator_engine.js`, `simulator_evidence.js`, `rebuild_evidence.py`.
- Generated literature exports in `data/literature/` — `literature_registry.json`,
  `literature_references.tsv`, `protein_to_reference.tsv`, `protein_mapping_audit.tsv`,
  `family_evidence.tsv`, `family_to_reference.tsv`, `pathway_to_reference.tsv`,
  `interaction_evidence.tsv`, `simulator_rule_to_reference.tsv`,
  `priority_reference_trace.tsv`, `provenance.json`.
- Network snapshots in `adhesome_network/` — `Schistosome_adhesome_rebuilt.html`,
  `schistosome_integrin_adhesome_hypothesis_simulator.html`,
  `Schistosome_adhesome_family_inventory.csv`, `Schistosome_adhesome_candidate_node_members.csv`.
- Documentation — `Target_prioritization.md`, `README.md`,
  `README_adhesome_hypothesis_simulator.md`, `README_schistosome_adhesome_interactive.md`,
  `adhesome_network/Schistosome_adhesome_rebuild_README.txt`, `UPDATE_MANIFEST.md`,
  `IMPLEMENTATION_REPORT_2026-11-07.md`.
- Tests — `test_literature.py`, `test_layered_simulator.cjs`, `test_candidate_profiles.py`,
  `test_current_library.py`, `test_library_refresh.py`, `test_linked_context.py`,
  `test_reclassification.py`, `test_scientific_text.py`, `test_research_priorities.py`,
  `test_research_priorities.cjs`, `test_orthogroup_statistics.py`,
  `test_consensus_projection.py`, `test_consensus_layout.py`, `test_family_phylogeny_formats.py`,
  `test_motif_annotations.py`, `test_string_sequences.py`, `test_functional_categories.py`,
  `test_functional_dashboard.py`, `test_ui_redesign.cjs`, `test_node_interactivity.cjs`.
- Retired interface files — `reclassification_view.py`, `test_reclassification_ui.py`,
  `test_reclassification_browser.cjs`, `adhesome_network/Schistosome_Pfam_CDD_family_hypotheses.html`,
  `adhesome_network/Schistosome_Pfam_CDD_reconciliation.csv`.
