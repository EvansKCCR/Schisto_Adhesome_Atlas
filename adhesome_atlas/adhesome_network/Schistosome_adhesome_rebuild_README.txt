REBUILT COMPARATIVE SCHISTOSOME INTEGRIN–ADHESOME INTERACTION HYPOTHESIS
2026-10-20

INPUTS
  adhesome_candidates_list.xlsx  / Audited_family_assignment
  interactions.csv              / human reference interaction table
  Schistosome_adhesome_interactive.html / prior conceptual schema and S. mansoni literature context

INVENTORY
  2,664 unique protein records, 64 putative_audited_family categories, seven Schistosoma species:
  bovis, curassoni, haematobium, intercalatum, japonicum, mansoni, rodhaini.
  Audited grades A=953, B=21, C=1,690.

REFERENCE PROJECTION
  interactions.csv: 6,542 source rows, Source/Target are human symbols.
  An explicit, conservative source-symbol -> candidate family mapping is given in
  Schistosome_human_gene_family_crosswalk.csv. It is NOT exact orthology evidence.
  2,344 source rows have both endpoints mapped; aggregated into 252 distinct
  between-family human-reference interaction groups; 9 additional intra-family
  groups are omitted from the graph to avoid misleading self-loops.
  Counts in CSV distinguish raw reference rows from unique HUMAN gene pairs.
  The mapping does not place interactions on individual parasite proteins.
  Unmapped human symbols and reference-only interaction partners are NOT silently
  invented as parasite candidate proteins.

PARASITE-SPECIFIC EVIDENCE CONTEXT
  The SmILK–SmPINCH–SmNck2 / Smβ-Int1–SmVKR1 branch is shown separately,
  based on the user's earlier HTML literature annotations (Gelmedin et al., 2017,
  https://doi.org/10.1371/journal.ppat.1006147).
  These represent complex/receptor-coupling context, NOT verified binary
  endogenous PPIs for all candidate family members.
  In the current S. mansoni candidate set, Sman__Smp_079760 (ILK),
  Sman__Smp_020540 (PINCH_like), and Sman__Smp_014850 (Nck) are grade A.
  SmVKR1 is a contextual receptor node, not a candidate inventory count.
  Experiment-context edges display only with S. mansoni or all species selected.

FILES
  Schistosome_adhesome_rebuilt.html : offline self-contained interactive network
  Schistosome_adhesome_family_inventory.csv : seven-species family and grade counts
  Schistosome_human_reference_family_edges.csv : mapped human evidence with sources/PMIDs
  Schistosome_human_gene_family_crosswalk.csv : inspectable symbol-to-family mapping
  Schistosome_adhesome_candidate_node_members.csv : exact source proteins per family
  Schistosome_adhesome_rebuilt_data.json : JSON model used in HTML

INTERPRETATION
  User-defined network groups are functional layout heuristics, NOT localization results.
  Audit grade reflects family annotation evidence, not interaction confidence.
  Human-reference transfer identifies possible relationships, NOT established
  Schistosoma protein-protein interactions or unique gene orthology.
  Transferred interactions should be validated against specific orthogroups,
  Pfam architecture, accessible motifs, subcellular colocalization, and assays.