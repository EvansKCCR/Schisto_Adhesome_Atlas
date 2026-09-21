from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from prioritization_evidence import enrich

with TemporaryDirectory() as temp:
    root=Path(temp); folder=root/'phylogeny'/'OGtest'/'inference';folder.mkdir(parents=True)
    (folder/'trimmed.faa').write_text('>Shae__a\nACDE\n>Sman__b\nACDF\n>Hsap__h\nACGE\n')
    pd.DataFrame([dict(branch_id='B1',support_label='90/80',tip_ids='Shae__a,Sman__b')]).to_csv(folder/'branch_evidence.tsv',sep='\t',index=False)
    frame=pd.DataFrame([dict(sequence_id='Shae__a',family='test',assigned_family='test',orthogroup='OGtest',domain_type_fraction=1,domain_evidence='Family rule matched',topology_evidence='Consistent with intracellular/peripheral assignment',priority_group='Not in FN3 review collection')])
    hits=pd.DataFrame([dict(sequence_id='Shae__a',family='test',elm_class='ELMtest',start=1,end=4,peptide='ACDE',context_state='region_supported')])
    r=enrich(frame,hits,root).iloc[0]
    assert r.domain_architecture==1 and r.topology_compatibility==1
    assert r.phylogenetic_support==.8 and r.host_divergence==.25
    assert r.motif_conservation==.75
    assert r.motif_context_evidence=='Region-supported motif'
    assert r.adhesome_interpretation=='Convergent assignment: test'
    hits.loc[0,'family']='another_family'
    r=enrich(frame,hits,root).iloc[0]
    assert pd.isna(r.motif_conservation)
    assert r.motif_context_evidence=='No contextual motif support reported'
    hits.loc[0,'family']='test'; hits.loc[0,'context_state']='outside_expected_region'
    r=enrich(frame,hits,root).iloc[0]
    assert r.motif_context_evidence=='Context conflict reported'
    assert r.evidence_review_stage.startswith('4')
print('PASS measured alignment features, family-specific motif mapping and context conflicts')
