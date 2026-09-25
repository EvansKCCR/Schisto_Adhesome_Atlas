# Phylogeny explorer

Select **Phylogeny** in the atlas. Search by orthogroup or protein ID; these controls are independent of catalogue filters. Species colors come from `tips.tsv`; stars and diamonds identify its `candidate=1` tips. Tip hover text includes identifiers and sequence lengths. Branch hover text exposes the corresponding branch ID and interpretation.

The display reads `gene_tree.treefile`, preserves branch lengths and topology, and joins branch evidence by exact descendant-tip sets. Internal support labels are reproduced verbatim. The supplied IQ-TREE reports identify paired labels as SH-aLRT (%) / ultrafast bootstrap (%). The rectangular origin is a drawing convention for these unrooted trees, not an inferred ancestor. The optional cladogram changes only displayed lengths. Phylogeny never independently establishes adhesome membership.

The replacement library contains 152 tree runs and 2,261 tips across runs: 135 all-candidate runs and 17 fibronectin-like runs. Trees are discovered recursively under `Phylogeny/adhesome_candidates_list` and `Phylogeny/fibronectin_like_candidate`. The collection filter reads `settings.project` from each `run.json`. Runs for the same orthogroup remain distinct, and exports include collection paths in their names. Each group retains:

- `tips.tsv`
- `inference/gene_tree.treefile`
- `inference/trimmed.faa`
- `inference/gene_tree.iqtree`
- `inference/branch_evidence.tsv`
- `inference/run.json`

The Reproducibility tab provides individual files and a ZIP bundle. Interactive HTML export embeds Plotly for offline viewing; the plot toolbar provides PNG export. On narrow screens, use fullscreen or the HTML export for more room.

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
The Phylogeny page defaults to Protein family browsing, with Functional module and Orthogroup modes. `phylogeny_family_groups.tsv` records the user-specified Integrin α, Kindlin, Src, PTP-PEST and Paxillin groupings. Other family and module labels come from the candidate catalogue, matched by orthogroup and collection. These labels organize existing trees; they do not merge alignments, modify source family assignments or infer new inter-orthogroup branches. The group inventory lists all matching runs, and the tree selector retains orthogroup IDs. Deploy the grouping TSV alongside app.py.
`OG0013508` (Kindlin) and `OG0013668` (Paxillin) are listed in the requested groups but currently have no discoverable tree. Their family views show an explicit unavailable notice; new runs will be discovered automatically when added.


Src, FAK and ILK remain independent browsing families: Src OG0000213/OG0001055/OG0003193; FAK OG0002086; ILK OG0003976. The family heading identifies the analysis run; per-protein family support is reported separately by the audited workbook. Classification offers Supported, Provisional and All (default), using the audited family decision within the selected collection. A run is included if it has a matching candidate; complete trees remain intact. A run with mixed decisions can appear in both subsets. The group inventory reports the selected audited classifications.


Integrin alpha OG0000401 and OG0001220 are combined into one atlas display group in Orthology and the phylogenetic group selector. Orthology membership unions unique identifiers and preserves source group IDs. Phylogeny renders both original trees under the one selected group, without introducing an artificial connecting branch. Original files and orthology relationships are unchanged.

The combined Integrin alpha view opens with a combined member list and separate, immediately visible OG0000401 and OG0001220 tree tabs. Summary counts cover both runs. Searching for either orthogroup selects the complete family group, preserving both source trees.
