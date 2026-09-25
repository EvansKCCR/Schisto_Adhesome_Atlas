import pandas as pd
import plotly.express as px
import streamlit as st
from evidence import PRIORITIES

def evidence_view(df):
    st.subheader('Integrated evidence and assignment confidence')
    st.caption('Orthology references: H. sapiens (GRCh38.p14), M. musculus (GRCm39), X. laevis (Xenopus_laevis_v10.1), D. melanogaster (GCF_000001215.4), and C. elegans (PRJNA13758).')
    st.info('The audited family decision uses domain architecture as its primary gate. Orthology, motif context and topology/localization support the interpretation. Original screening labels and source statuses remain visible.')
    counts=df.groupby(['species','evidence_review_stage']).sequence_id.nunique().reset_index(name='proteins')
    st.plotly_chart(px.bar(counts,x='species',y='proteins',color='evidence_review_stage',title='Evidence convergence · distinct proteins by stage'),width='stretch')
    st.caption('Stages show convergence across all four evidence types or the first incomplete/conflicting component. A protein with multiple family assignments can occur in multiple stages.')
    cols=[c for c in ['sequence_id','species','family','reviewed_family','audit_classification','grade','family_decision','status','orthogroup','orthology_scope','schistosome_species_in_HOG','domain_evidence','topology_evidence','motif_context_evidence','evidence_review_stage','host_orthology_flag','adhesome_interpretation'] if c in df]
    st.dataframe(df[cols],width='stretch',hide_index=True)
    st.download_button('Download hierarchical evidence review',df.to_csv(index=False),'hierarchical_evidence.csv')
    orthcols=[c for c in df if c.startswith('Orthology_') or c in ['Orthogroup','HOG_status'] or c.endswith(('_orthologues','_relationship','_HOG_copy_counts'))]
    with st.expander('Original orthology assignments and relationship types'):
        st.dataframe(df[['sequence_id']+orthcols],width='stretch',hide_index=True)
    st.caption('Human orthologues trigger selectivity review, not exclusion. They do not quantify host sequence similarity. Schistosoma-only means only within the sampled HOG/reference species, not proven absence throughout metazoans. One-to-many and many-to-many relationships preclude automatic gene-name transfer.')

def priority_view(frame):
    st.subheader('Three distinct FN3 / RPTP priority groups')
    st.caption('This view uses the complete FN3 review collection, independently of the sidebar collection filters. Group membership combines assigned family and evolutionary scope; topology/localization agreement is shown for each protein.')
    for col,name in zip(st.columns(3),PRIORITIES):
        col.metric(name,frame.loc[frame.priority_group.eq(name),'sequence_id'].nunique())
    interpretations={PRIORITIES[0]:'Schistosoma-restricted single-pass FN3 receptors: cell-surface recognition and adhesion assignments integrating FN3 architecture, membrane topology and intracellular motif context.',PRIORITIES[1]:'Schistosoma-restricted RPTP-like proteins: receptor-associated signalling assignments integrating FN3/phosphatase architecture and membrane organization.',PRIORITIES[2]:'Conserved secreted FN3 proteins: extracellular assignments integrating shared orthology, FN3 architecture, signal peptide and localization.'}
    selected=st.selectbox('Priority group',PRIORITIES+['Other / unresolved FN3 candidates'])
    subset=frame[frame.priority_group.eq(selected)]
    st.write(interpretations.get(selected,'Other FN3 evolutionary histories and classes remain available for review; they are not silently forced into one of the three priority groups.'))
    if not subset.empty:
        summary=subset.groupby(['species','topology_evidence']).sequence_id.nunique().reset_index(name='proteins')
        st.plotly_chart(px.bar(summary,x='species',y='proteins',color='topology_evidence',title='Priority group · localization agreement and review needs'),width='stretch')
    cols=['sequence_id','species','reviewed_family','audit_classification','grade','orthogroup','orthology_scope','schistosome_species_in_HOG','architecture','DeepTMHMM','DeepLoc_2.1','domain_evidence','topology_evidence','motif_context_evidence','evidence_review_stage','host_orthology_flag']
    st.dataframe(subset[[c for c in cols if c in subset]],width='stretch',hide_index=True)
    st.download_button('Download this priority group',subset.to_csv(index=False),'fn3_priority_group.csv')
    st.caption('Conserved secreted group: shared HOG with copies reported in all three schistosome species and source assignment secreted_FN3_protein_like. The two Schistosoma-only groups require that exact sampled-HOG status and the corresponding receptor class. General single-pass membrane FN3 proteins are not automatically classified as adhesion receptors.')
