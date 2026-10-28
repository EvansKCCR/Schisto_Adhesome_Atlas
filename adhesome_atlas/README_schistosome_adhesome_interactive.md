# Interactive schistosome adhesome map

The atlas is built from the current seven-species candidate workbook and provides an interactive view of predicted schistosome adhesome relationships. The map is a snapshot of the evidence available at the time of export, while future releases will remain synchronized with the candidate workbook and supporting CSV files. Family-level interactions are presented as hypotheses, with **S. mansoni** experimental evidence clearly distinguished.

Users can download the hypothesis map as a standalone HTML file, along with associated network data, centrality metrics, memberships, and projection references. Interactive SVG network layouts are preserved in exported files.

## Candidate Profiles and Protein Dossiers

The atlas contains profiles for all 4359 candidate adhesome-associated hypothesis. Candidates can be searched by accession or annotation, and selecting a protein highlights its family node and displays a detailed profile.

Each profile includes:

Annotation confidence and grade
Family assignment and orthogroup
Pfam/CDD domain architecture
Localization and topology predictions
Evidence scores
Motifs and domain hits
Reference orthologues

Profiles can be downloaded as JSON files with full source identifiers. Each candidate also has a dedicated protein dossier that links directly between the dossier view and its position on the interactive map.

## Network Navigation and Path Exploration

Clicking a family node highlights its connected network and opens a matching candidate profile. Users can explore:

Direct partners
Two-step neighborhoods
Entire connected components
Shortest paths between selected families

Path highlighting is based on displayed family-level associations and evidence filters. It does not imply direct candidate-level interactions or causality.

## Integrated Simulation Workspace

Selected candidates are linked directly to downstream simulation tools. Candidate information, orthogroup membership, evidence filters, and highlighted paths are automatically transferred into simulation views.

Users can:

Switch between candidates within the same family
Update simulations as paths change
Launch candidate-specific simulations
Export simulation outputs, including path information, filters, assumptions, and random seeds

Optional pathway-coupling rules apply biologically motivated module requirements (for example, FAK/Src and ILK-PINCH-Nck complexes) when generating hypothetical downstream outcomes.

## Interface and Data Integrity

The atlas supports mouse, touch, and keyboard navigation. Candidate selection, node highlighting, profiles, and network paths remain synchronized across views.

Family panels display all matching candidates together with grade distributions (A/B/C). Nodes without candidate proteins display a clear empty-state message. Non-selected network elements remain visible but are visually de-emphasized.

For example, the current dataset contains 76 collagen-like proteins across seven species (75 grade A and 1 grade C). No curated collagen interaction is currently present in the network topology, so collagen nodes appear without recorded connections.

## User Experience

The atlas uses a clean scientific design with scalable labels and adjustable display settings. Users can zoom, pan, resize labels, filter networks, and expand reference interaction tables.

Protein dossiers summarize:

Family membership
Candidate counts and grade distributions
Accessions and orthogroups
Highlighted network paths
Supporting evidence

Detailed domain, motif, orthology, and family-assignment sections remain available when needed.

The entire platform, including exported HTML files, runs without external fonts, JavaScript libraries, or online dependencies, ensuring portability and long-term accessibility.