# Phylogenetic evidence

The app recursively discovers `gene_tree.treefile` and `tree.treefile` in `Phylogeny` (including `Phylogeny/family_phylogeny`) and a top-level `family_phylogeny` directory. Both `group/inference/` and flat group directories are accepted. It rescans every 30 seconds while the Phylogeny page is open. Add new runs without editing code or a group registry. If both tree names occur in the same run, `gene_tree.treefile` takes precedence and the run is listed only once.

Available trees are displayed even when companions are incomplete. Missing files are listed. Tips are annotated from `tips.tsv` with species colors and candidate stars/diamonds. Branch evidence joins by exact descendant-tip sets; Newick labels and lengths remain those of the inferred tree. The display origin is a convention for unrooted trees. Orthogroup identities follow the active run exactly; no old dictionary or fixed group merges are used.

The explorer separates **Family-level phylogenies** from **Orthogroup trees** with a collection selector. Each collection retains its own search and selected tree. Family runs are identified by their `family_phylogeny` directory or recorded project provenance, and retain their source orthogroup IDs. Links arriving from the Orthology explorer automatically select the matching orthogroup collection.

Each tree has a linked-candidate table with clickable protein dossiers, catalogue family annotations, species, grades, classifications and an `in_tree` indicator. Family candidate tables open expanded. Links use exact IDs present in the tree or its tip table, rather than requiring a folder-name/family-name match. All matching catalogue records, including repeated IDs and input records absent from the final tree, remain available for viewing and CSV download. The candidate selector highlights its tip and exposes a direct dossier button; dossiers provide the existing domain, motif, topology, orthology and sequence views. An empty state identifies trees without matching catalogue profiles.

Retain:

- `tips.tsv`
- `inference/gene_tree.treefile`
- `inference/branch_evidence.tsv`
- `inference/gene_tree.iqtree`
- `inference/run.json`
- `inference/trimmed.faa`

Family runs may instead use `tree.treefile`, `tree.iqtree`, and `trimmed.fasta` or `trimed.fasta`. Original filenames are preserved in download bundles. Missing `branch_evidence.tsv` or `run.json` does not hide an available tree; support labels embedded in Newick remain visible.

The family tip-table format (`sequence_id`, `panel_label`, `source_orthogroup`, `length_aa`) is accepted alongside the existing `species`/`candidate` format. Species use `panel_label` or the sequence prefix when not explicitly recorded; candidate markers use exact catalogue ID matches when no candidate flag is recorded. All source columns remain available in the tip table. Source file changes and additions invalidate the atlas data fingerprint; the sidebar also offers Reload source files.

The tip table retains input records absent from the inferred tree and marks them with `in_tree = False`. Tree-tip, candidate-tip and species metrics count the displayed tree. No missing sequences or connecting branches are inferred.

Validation: `python test_family_phylogeny_formats.py`; add `--app` for Streamlit family/original tree navigation checks.
