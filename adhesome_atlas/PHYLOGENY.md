# Phylogeny explorer

Select **Phylogeny** in the atlas. Search by orthogroup or protein ID; these controls are independent of catalogue filters. Species colors come from `tips.tsv`; stars and diamonds identify its `candidate=1` tips. Tip hover text includes identifiers and sequence lengths. Branch hover text exposes the corresponding branch ID and interpretation.

The display reads `gene_tree.treefile`, preserves branch lengths and topology, and joins branch evidence by exact descendant-tip sets. Internal support labels are reproduced verbatim. The supplied IQ-TREE reports identify paired labels as SH-aLRT (%) / ultrafast bootstrap (%). The rectangular origin is a drawing convention for these unrooted trees, not an inferred ancestor. The optional cladogram changes only displayed lengths. Phylogeny never independently establishes adhesome membership.

The replacement library contains 152 tree runs and 2,261 tips across runs: 135 all-candidate runs and 17 fibronectin-like runs. Trees are discovered recursively under `phylogeny/adhesome_candidates_list` and `phylogeny/fibronectin_like_candidate`. The collection filter reads `settings.project` from each `run.json`. Runs for the same orthogroup remain distinct, and exports include collection paths in their names. Each group retains:

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
