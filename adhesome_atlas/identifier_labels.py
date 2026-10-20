"""Optional exact identifier maps from the active library only."""
import pandas as pd

def identifier_annotations():
    # Current IDs are the accession identifiers in the active candidate workbook.
    # Historical eight-species maps are deliberately not applied to this dataset.
    return pd.DataFrame(columns=['sequence_id','protein_annotation_id','original_gene_id','identifier_mapping_status','alternative_protein_ids'])


def canonical_sequence_id(identifier):
    return str(identifier)

