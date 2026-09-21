# Phylogeny explorer

Select **Phylogeny** in the atlas. Search by orthogroup or protein ID; these controls are independent of catalogue filters. Species colors come from `tips.tsv`; stars and diamonds identify its `candidate=1` tips. Tip hover text includes identifiers and sequence lengths. Branch hover text exposes the corresponding branch ID and interpretation.

The display reads `gene_tree.treefile`, preserves branch lengths and topology, and joins branch evidence by exact descendant-tip sets. Internal support labels are reproduced verbatim. The supplied IQ-TREE reports identify paired labels as SH-aLRT (%) / ultrafast bootstrap (%). The rectangular origin is a drawing convention for these unrooted trees, not an inferred ancestor. The optional cladogram changes only displayed lengths. Phylogeny never independently establishes adhesome membership.

The library currently contains 136 tree runs and 1,167 tips across runs: 120 all-candidate runs and 16 fibronectin-like runs. The collection filter reads `settings.project` from each `run.json`. Runs for the same orthogroup remain separate, including `OG0000761` and `OG0000761_fib`; counts describe tree runs rather than unique orthogroups or unique proteins. Each group retains:

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
