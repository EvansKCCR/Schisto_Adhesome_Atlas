# Phylogeny explorer

Select **Phylogeny** in the atlas. The default collection is **Family-level phylogeny**. Search by family, source orthogroup or protein accession; these controls are independent of catalogue sidebar filters. Species colors come from `tips.tsv`; stars and diamonds identify its `candidate=1` tips. Tip hover text includes identifiers and sequence lengths. Branch hover text exposes the corresponding branch ID and interpretation.

The display reads `gene_tree.treefile`, preserves branch lengths and topology, and joins branch evidence by exact descendant-tip sets. Internal support labels are reproduced verbatim. The library IQ-TREE reports identify paired labels as SH-aLRT (%) / ultrafast bootstrap (%). The rectangular origin is a drawing convention for these unrooted trees, not an inferred ancestor. The optional cladogram changes only displayed lengths. Phylogeny never independently establishes adhesome membership.

The library contains 171 tree runs and 3,061 tips across runs: **19 jointly inferred family runs (800 tips, 190 candidate tips)**, 135 all-candidate runs and 17 fibronectin-like runs. Trees are discovered recursively under `Phylogeny/family_phylogeny`, `Phylogeny/adhesome_candidates_list` and `Phylogeny/fibronectin_like_candidate`. The collection filter reads `settings.project` from each `run.json`. Runs for the same orthogroup remain distinct, and exports include collection paths in their names. Each group retains:

- `tips.tsv`
- `inference/gene_tree.treefile`
- `inference/trimmed.faa`
- `inference/gene_tree.iqtree`
- `inference/branch_evidence.tsv`
- `inference/run.json`

The Reproducibility tab provides individual files and a ZIP bundle. Interactive HTML export embeds Plotly for offline viewing and retains the atlas image-export settings. The plot camera button uses the sidebar's **Figure downloads** format: high-resolution PNG or scalable SVG. Tall tree heights are preserved, with raster dimensions bounded to browser canvas limits. On narrow screens, use fullscreen or the HTML export for more room.

## Joint family trees (2026-10-07)

`family_phylogeny/family_…/inference/gene_tree.treefile` represents the newly inferred family topology. It is displayed as one family tree, rather than a group of disconnected orthogroup trees. `tips.tsv` supplies the family and each protein's `source_groups`; the inventory and tree caption show these source orthogroups. Src and FAK remain independent families. PINCH uses the current audited PINCH assignments.

The integrin α tree contains **49 tips, including eight schistosome candidates**. It includes all six specified candidates from OG0000401 and OG0001220, plus the additional candidates recorded in the new family input. No branch is constructed by the atlas: topology and support come directly from the new IQ-TREE output.

Classification uses matching candidate identifiers and audited family assignments. Supported and Provisional select eligible family runs without pruning their reference or candidate tips. Functional-module browsing remains available alongside family browsing; previous orthogroup collections retain their original grouping behavior.

Full species prefixes such as `Homo_sapiens__GeneID_3674` are normalized to `Hsap__GeneID_3674` only for identifier-map joins and species colors. Original `sequence_id`, `source_species`, tree topology, branch tip sets and companion files are preserved. Display labels use mapped protein annotation accessions; unmapped identifiers remain explicit. Human host-divergence calculations also recognize the full reference-species prefix.

Cleanup removed **442 intermediate files (61,425,893 bytes)** solely from `Phylogeny/family_phylogeny`, leaving **114 files: six per family run**, in the structure listed above. `Resources/family_phylogeny_cleanup_manifest_2026-10-07.csv`, outside the reduced collection, records retained/removed paths, sizes and SHA-256 hashes. All retained files were verified byte-for-byte unchanged. Earlier orthogroup collections were preserved. `run.json` retains its original provenance, including historical paths to removed intermediates.

Cleanup on 2026-09-21 removed 2,159 other files solely inside `phylogeny/`. `phylogeny_cleanup_manifest.csv` records their relative paths, sizes and SHA-256 hashes. The original `run.json` files remain unmodified and contain historical paths/hashes for removed intermediates. The retained trimmed alignment permits rerunning tree inference, but the reduced library does not retain every input needed to repeat upstream sequence preparation and alignment.

No additional packages are required. Launch from WSL as usual, selecting an available port when needed:

```bash
ATLAS_PORT=8503 bash launch_atlas.sh
```

Validation: `python test_phylogeny.py` checks every tree against tip metadata, branch support and alignment identifiers, and exercises the Streamlit explorer controls.


Reference proteomes (updated 2026-09-24): H. sapiens GRCh38.p14; Mus musculus GRCm39; Xenopus laevis Xenopus_laevis_v10.1; Drosophila melanogaster GCF_000001215.4; C. elegans PRJNA13758. Each reference species has a distinct tree color. New cleanup records are in `phylogeny_cleanup_manifest_2026-09-24.csv`; all six files listed above are retained per run. The older cleanup manifest describes the superseded library.


Tree tip labels now use species-qualified representative protein annotation accessions from the atlas-root `identifier_map.tsv`. Mapping joins exact prepared IDs and retains unresolved/conflicting IDs unchanged. Original gene IDs remain in hover details and source files; the tip tab offers a mapped CSV. Search includes representative and alternative protein IDs. Deploy `identifier_map.tsv` alongside `app.py` and `identifier_labels.py`.

The expanded eight-species identifier map is copied from `04_orthology_phylogenetic_classification/03_qc/expanded8/identifier_map.tsv` to `identifier_map_expanded8.tsv`. It fills only prepared IDs absent from the primary map. The mapped-tip table records the mapping source. Deploy both map files alongside the scripts.

For GitHub upload, use `identifier_map_expanded8.tsv.gz` in place of the uncompressed expanded map. The loader prefers gzip and pandas decompresses it automatically. Keep `identifier_map.tsv` as the primary map. The uncompressed expanded map is retained locally but is not needed in deployment.


### Family and functional-module browsing
The Phylogeny page defaults to Protein family browsing, with Functional module and Orthogroup modes. In the joint-family collection, family labels and source orthogroups come from the new tip annotations; audited matching candidates provide classifications and functional modules. For earlier orthogroup collections, `phylogeny_family_groups.tsv` records the user-specified Integrin α, Kindlin, Src, PTP-PEST and Paxillin groupings. Other family and module labels come from the candidate catalogue, matched by orthogroup and collection. These browsing labels do not merge alignments, modify source family assignments or infer new branches. Deploy the grouping TSV alongside app.py.
Unavailable notices in older orthogroup collections refer only to that collection. Joint-family inputs can include source orthogroups without a corresponding standalone tree. Following the PINCH re-audit, OG0013668 belongs to the PINCH family context.


In the earlier orthogroup collections, Src, FAK and ILK retain their independent curated browsing groups: Src OG0000213/OG0001055/OG0003193; FAK OG0002086; ILK OG0003976. The new family collection uses the source groups recorded in each family input. The family heading identifies the analysis run; per-protein family support is reported separately by the audited workbook. Classification offers Supported, Provisional and All (default), using the audited family decision within the selected collection. A run is included if it has a matching candidate; complete trees remain intact. A run with mixed decisions can appear in both subsets. The group inventory reports the selected audited classifications.


Integrin alpha OG0000401 and OG0001220 retain their combined display group in Orthology and the earlier phylogeny collections. Orthology membership unions unique identifiers and preserves source group IDs. Earlier phylogeny collections render both original trees under one browsing group, without introducing an artificial connecting branch. The new family collection instead displays its newly inferred joint tree. Original files and orthology relationships are unchanged.

In the earlier collections, the combined Integrin alpha view opens with a combined member list and separate, immediately visible OG0000401 and OG0001220 tree tabs. Summary counts cover both runs. Searching for either orthogroup selects the complete family group, preserving both source trees.
