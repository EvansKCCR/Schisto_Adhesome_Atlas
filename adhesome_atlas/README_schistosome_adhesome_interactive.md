# Interactive schistosome adhesome map

The active visualization is in `adhesome_network/`: `Schistosome_adhesome_interactive.html` or `Schistosome_adhesome_rebuilt.html`. The app preserves its native species, grade, evidence and graph controls. Family-node selection is connected through `nodeDetails` to the linked downstream simulator.

The atlas uses the current seven-species candidate workbook for its tables and consensus projections. The self-contained map remains the evidence snapshot authored in its HTML and companion CSVs. When updating the map, keep its embedded candidate inventory and companion CSVs synchronized with the workbook. Human-reference edges describe family-level hypotheses; the S. mansoni experimental complex context retains its own evidence labels.

The hypothesis download in Introduction packages the map and linked simulator as a standalone HTML file. Orthogroup network data, centrality, memberships, projection references and input hashes download from Interactions. Network SVG buttons retain the interactive layout.


## Candidate profiles and dossier links

The standalone HTML now embeds profiles for all 2,664 current candidates. Search by accession or annotation in **Locate a candidate**; selecting a protein displays its family node and opens its profile. Clicking a family shows a searchable list of every candidate matching the native species/grade filters, rather than only 26 rows. Potential linked partner families can be explored from the same panel.

Profiles show annotation confidence, grade, family decision, orthogroup, Pfam/CDD architecture, localization/topology, the separate evidence scores, positional motifs, domain hits and reference orthologues. Each profile downloads as JSON with exact source identifiers. The atlas builds these profiles from the current workbooks at runtime using `candidate_profiles.py`; the embedded standalone file is a snapshot. The hypothesis download includes the latest profiles.

**Open complete Protein dossier** opens the selected accession in the atlas. The dossier also provides **Locate this candidate on the interactive hypothesis**. Deep links use `?view=Protein+dossier&protein=<accession>` or `?view=Introduction&protein=<accession>`. Hosted links are included in exports created from the atlas; a standalone local HTML still contains the evidence profile without requiring a running server.

The selected candidate accession, annotation, species and orthogroup are passed into its linked simulation context. The map continues to represent family-level relationships.


## Node clicks: connected paths and profiles

Clicking a family node now highlights its connected network and immediately opens a matching candidate profile at the top of the side panel. The initial selection uses grade then accession ordering; the complete filtered candidate list remains selectable. Existing exact candidate selections are retained when compatible with the clicked node and filters.

**Connected path** chooses direct partners, a two-step neighborhood (default), or the connected component. **Shortest path to** highlights one deterministic shortest route to a selected family. Paths use the currently displayed, undirected family associations and evidence filters. An unreachable target is reported explicitly. Profiles stay linked to the selected family; path highlighting does not assign interactions to individual candidate proteins.

At typical desktop widths the profile panel remains beside the map. Narrow screens open a closable right-hand panel, rather than placing the profile below the graph. JSON profile downloads, complete dossier links and candidate-aware simulator links remain available.


## Persistent candidate–path simulation workspace

Nodes are clickable and keyboard-accessible buttons. Clicking a node opens its linked candidates directly; **Locate a candidate** is optional. The map sends the exact selected accession, species, orthogroup, full profile, active evidence filters and highlighted path to the linked viewer. A dedicated candidate panel remains visible in **Adhesome map**, **Downstream simulation** and **Map + simulation** views. The mobile layout keeps it in a separate lower pane.

Choose another protein in **Candidates linked to this node**, or change the path on the map: the profile and active simulation update together. **Simulate candidate and path** starts the scenario. The selected route or neighborhood stays visible in the profile panel. Profile JSON downloads include its highlighted path and filters. Simulator exports retain the selected candidate record, source names, path edges, filters, path gate assumptions and seed.

**Use highlighted path for downstream coupling** applies explicit module gates. FAK/Src requires both families; the bridge requires ILK, PINCH and Nck. Other functional projections use their displayed module participants. VKR1 remains restricted to S. mansoni context. These gates select hypothetical downstream readouts; they do not alter binding weights from reference row counts. The same-seed baseline keeps the same path gates, separating the candidate mechanism proxy from the path scope. Disable the checkbox to retain the path as annotation only.
