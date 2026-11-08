# Interactive schistosome adhesome map

The atlas is built from the current seven-species candidate workbook and provides an interactive view of predicted schistosome adhesome relationships. The map is a snapshot of the evidence available at the time of export, while future releases will remain synchronized with the candidate workbook and supporting CSV files. Family-level interactions are presented as hypotheses, with **S. mansoni** experimental evidence clearly distinguished.

Users can download the hypothesis map as a standalone HTML file, along with associated network data, centrality metrics, memberships, and projection references. Interactive SVG network layouts are preserved in exported files.

## Candidate Profiles and Protein Dossiers

The current Atlas contains 4,359 unique candidate profiles. Candidates can be searched by accession or annotation, and selecting a protein highlights its family node and displays a detailed profile.

Each profile includes:

Annotation confidence and grade
Family assignment and orthogroup
Pfam/CDD domain architecture
Localization and topology predictions
Evidence scores
Motifs and domain hits
Reference orthologues
Scoped literature and biological evidence

Profiles can be downloaded as JSON files with full source identifiers. Each candidate also has a dedicated protein dossier that links directly between the dossier view and its position on the interactive map.

## Network Navigation and Path Exploration

Clicking a family node highlights its connected network and opens a matching candidate profile. Users can explore:

Direct partners
Two-step neighborhoods
Entire connected components
Shortest paths between selected families

In **Network filters**, enable **Show connected nodes only** to display families with at least one edge under the active species, grade and evidence filters. Clear the option to see isolated families again.

Path highlighting is based on displayed family-level associations and evidence filters. It does not imply direct candidate-level interactions or causality.

## Integrated Simulation Workspace

Selected candidates are linked directly to downstream simulation tools. Candidate information, orthogroup membership, evidence filters, and highlighted paths are automatically transferred into simulation views.

Users can:

Switch between candidates within the same family
Update simulations as paths change
Launch candidate-specific simulations
Export simulation outputs, including path information, filters, assumptions, and random seeds

Optional path controls apply the selected FAK/Src and SmVKR1 pathway context. Kindlin, ILK, PINCH and parvin selections adjust the corresponding scaffold recruitment parameters. The simulator inspector links the selected mechanism to the publication registry.

## Interface and Data Integrity

The atlas supports mouse, touch, and keyboard navigation. Candidate selection, node highlighting, profiles, and network paths remain synchronized across views.

Family panels display matching candidates with A/B/C/D grade distributions. The dossier records the audited support designation separately. Nodes without candidate proteins display a clear empty-state message. Non-selected network elements remain visible but are visually de-emphasized.

The current collagen-like label covers 75 broad-supported candidates. The Parvin_like label contains 14 specific-supported candidates. OG0000818 includes two additional broad CH-domain proteins, which retain their own audited label.

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
