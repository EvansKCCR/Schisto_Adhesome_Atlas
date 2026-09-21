# Reconstruction evidence inputs

These header-only TSV files are intentionally empty. Populate them with reviewed evidence; do not infer mappings from similar identifiers. The app reloads them on rerun. Original exports are unchanged.

## node_mapping.tsv

- `string_id`: exact STRING identifier from the node table (including taxonomy prefix).
- `sequence_id`: existing, species-qualified candidate identifier.
- `orthogroup`: documented orthogroup ID, or blank if only the identifier mapping is established.
- `reference`: source of the mapping/orthology assignment, such as analysis file and row or publication accession.

Each STRING ID occurs once. The species must match. Sharing a family annotation is not enough to establish orthology. Orthogroup conservation counts the number of represented species divided by three; coverage is limited to mapped network proteins.

## reference_interactions.tsv

`source` and `target` are exact STRING IDs in the same species. `relation` must be one of:

- Predicted physical interaction
- Domain-mediated association
- Motif-dependent interaction
- Regulatory relationship
- Functional coupling

To pass the conservative transfer gate, `orthology_transfer`, `domain_compatibility`, `motif_compatibility`, `topology_compatibility`, and `family_relationship` must all equal `supported`. A nonempty `reference` must identify the characterized reference interaction and its compatibility assessment. `phylogenetic_support` is retained when `supported`; otherwise it is not counted as supporting evidence. Blank or unassessed prerequisites exclude the row and expose it in the edge-evidence view. This strict implementation follows the requested all-prerequisites rule; it does not automatically validate the supplied assessments.

Reference transfers are not assigned a synthetic STRING score. The STRING score slider filters STRING edges only. Relationship and evidence-support filters apply to both sources. Network topology currently uses undirected associations: source/target ordering is preserved in the table, but regulatory direction is not analyzed.

## candidate_evidence.tsv

One row per STRING ID, with a reference documenting how each reviewed feature was normalized to 0–1:

- `domain_architecture`: compatibility with the adhesome-specific architecture.
- `motif_conservation`: comparative motif conservation, not merely motif presence.
- `topology_compatibility`: topology compatible with the proposed role, not merely a prediction being available.
- `phylogenetic_support`: support for the relevant family/orthology hypothesis.
- `host_divergence`: divergence/selectivity feature; higher means more divergent under the cited method. It is not a drug-safety prediction.
- `host_similarity_flag`: retain a clear assessment such as “High similarity — selectivity review required”; blank displays “Not assessed”.

Leave missing feature cells blank. The app calculates conservation from documented orthogroups and connectivity from degree centrality. An exploratory integrated score is the equal-weight mean of all seven values and is only produced for complete records. Equal weights are an explicit initial modeling choice, not a validated biological model. No missing value is converted to zero and incomplete scores are not rescaled. Proteins flagged for host similarity remain included.

Interface counts identify edges across extracellular/membrane, membrane/membrane-proximal, membrane-proximal/actin-coupling, or distinct known layers involving signalling. These counts depend on display-layer annotations and are exploratory. They order incomplete records for review but are not an eighth score feature.

## Topology methods

Centralities use the thresholded undirected unweighted simple graph with isolates retained. Parallel evidence rows collapse to a single pair for graph calculations. Degree is an edge count; connectivity is degree/(N−1). Betweenness is normalized. Closeness uses the Wasserman–Faust correction for disconnected components. Communities use greedy modularity maximization. Numerical community IDs have no biological meaning and can change with filters.

See [NetworkX centrality documentation](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) and [closeness correction](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.centrality.closeness_centrality.html).

An edge observed in one species is not automatically species-specific. Orthogroup consensus labels report occurrence in retained exports, not validated evolutionary conservation. STRING score bands at 0.7 distinguish export scores only, not conserved versus species-specific interactions or validated support tiers. Centrality does not establish essentiality.


## Workbook orthology and membership interpretation

The app now imports orthogroups from the updated candidate workbooks after exact species-qualified STRING ID/alias mapping. Manual mappings remain available and explicitly record their provenance. Source HOG copy counts provide species conservation when available; otherwise mapped network coverage is used. Orthogroup merging expresses family history only. It neither filters candidates into the adhesome nor transfers interactions by itself.

The required biological review hierarchy is orthology + diagnostic architecture + topology/localization + motif context. Each is displayed separately with unresolved/conflicting evidence. Family-rule matches are not automatically adhesome-specific, and a complete seven-feature numerical score is not a membership classification. Host orthology is not host sequence similarity. Orthology-only kinases/cytoskeletal proteins remain unconfirmed candidates.
