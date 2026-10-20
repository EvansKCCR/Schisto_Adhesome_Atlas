# Interactive schistosome adhesome map

The active visualization is in `adhesome_network/`: `Schistosome_adhesome_interactive.html` or `Schistosome_adhesome_rebuilt.html`. The app preserves its native species, grade, evidence and graph controls. Family-node selection is connected through `nodeDetails` to the linked downstream simulator.

The atlas uses the current seven-species candidate workbook for its tables and consensus projections. The self-contained map remains the evidence snapshot authored in its HTML and companion CSVs. When updating the map, keep its embedded candidate inventory and companion CSVs synchronized with the workbook. Human-reference edges describe family-level hypotheses; the S. mansoni experimental complex context retains its own evidence labels.

The hypothesis download in Introduction packages the map and linked simulator as a standalone HTML file. Orthogroup network data, centrality, memberships, projection references and input hashes download from Interactions. Network SVG buttons retain the interactive layout.


## Candidate profiles and dossier links

The standalone HTML now embeds profiles for all 2,664 current candidates. Search by accession or annotation in **Locate a candidate**; selecting a protein displays its family node and opens its profile. Clicking a family shows a searchable list of every candidate matching the native species/grade filters, rather than only 26 rows. Potential linked partner families can be explored from the same panel.

Profiles show annotation confidence, grade, family decision, orthogroup, Pfam/CDD architecture, localization/topology, the separate evidence scores, positional motifs, domain hits and reference orthologues. Each profile downloads as JSON with exact source identifiers. The atlas builds these profiles from the current workbooks at runtime using `candidate_profiles.py`; the embedded standalone file is a snapshot. The hypothesis download includes the latest profiles.

**Open complete Protein dossier** opens the selected accession in the atlas. The dossier also provides **Locate this candidate on the interactive hypothesis**. Deep links use `?view=Protein+dossier&protein=<accession>` or `?view=Introduction&protein=<accession>`. Hosted links are included in exports created from the atlas; a standalone local HTML still contains the evidence profile without requiring a running server.

The selected candidate accession, annotation, species and orthogroup are passed into its linked simulation context. The map continues to represent family-level relationships.
