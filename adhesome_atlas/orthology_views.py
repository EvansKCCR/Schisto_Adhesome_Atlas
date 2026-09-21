import pandas as pd
import plotly.express as px
import streamlit as st
from evidence import PRIORITIES

def evidence_view(df):
    st.subheader('Orthology and hierarchical evidence review')
    st.info('Orthology is evidence of shared evolutionary history, not a standalone adhesome-membership filter. Review orthology → diagnostic domain architecture → topology/localization → motif context, then apply adhesome-specific biological interpretation. Original candidate statuses are preserved.')
    counts=df.groupby(['species','evidence_review_stage']).sequence_id.nunique().reset_index(name='proteins')
    st.plotly_chart(px.bar(counts,x='species',y='proteins',color='evidence_review_stage',title='Review stages · distinct proteins within each stage'),width='stretch')
    st.caption('Stages identify the first unresolved review step; no candidate is excluded. A protein with several hypotheses can occur in several stages. Region support is not validated binding; a matched family rule is not proof of adhesome-specific architecture.')
    cols=[c for c in ['sequence_id','species','family','assigned_family','status','orthogroup','orthology_scope','schistosome_species_in_HOG','domain_evidence','topology_evidence','motif_context_evidence','evidence_review_stage','host_orthology_flag','adhesome_interpretation'] if c in df]
    st.dataframe(df[cols],width='stretch',hide_index=True)
    st.download_button('Download hierarchical evidence review',df.to_csv(index=False),'hierarchical_evidence.csv')
    orthcols=[c for c in df if c.startswith('Orthology_') or c in ['Orthogroup','HOG_status','Hsap_orthologues','Hsap_relationship','Cele_orthologues','Cele_relationship']]
    with st.expander('Original orthology assignments and relationship types'):
        st.dataframe(df[['sequence_id']+orthcols],width='stretch',hide_index=True)
    st.caption('Human orthologues trigger selectivity review, not exclusion. They do not quantify host sequence similarity. Schistosoma-only means only within the sampled HOG/reference species, not proven absence throughout metazoans. One-to-many and many-to-many relationships preclude automatic gene-name transfer.')

def priority_view(frame):
    st.subheader('Three distinct FN3 / RPTP priority groups')
    st.caption('This view uses the complete FN3 review collection, independently of the sidebar collection filters. Group membership combines the supplied assigned-family label and evolutionary scope; it does not establish adhesome membership or erase localization conflicts.')
    for col,name in zip(st.columns(3),PRIORITIES):
        col.metric(name,frame.loc[frame.priority_group.eq(name),'sequence_id'].nunique())
    interpretations={PRIORITIES[0]:'Lineage-restricted receptor candidates for cell-surface recognition or adhesion hypotheses; assess extracellular FN3 architecture, one-pass topology and intracellular motif context.',PRIORITIES[1]:'Lineage-restricted receptor phosphatase-like candidates; prioritize regulatory hypotheses and verify phosphatase architecture and membrane organization separately from FN3 adhesion receptors.',PRIORITIES[2]:'Conserved proteins assigned to a secreted FN3 class; assess extracellular roles, signal peptide and localization concordance. Shared orthology does not establish fibronectin identity or an integrin-binding role.'}
    selected=st.selectbox('Priority group',PRIORITIES+['Other / unresolved FN3 candidates'])
    subset=frame[frame.priority_group.eq(selected)]
    st.write(interpretations.get(selected,'Other FN3 evolutionary histories and classes remain available for review; they are not silently forced into one of the three priority groups.'))
    if not subset.empty:
        summary=subset.groupby(['species','topology_evidence']).sequence_id.nunique().reset_index(name='proteins')
        st.plotly_chart(px.bar(summary,x='species',y='proteins',color='topology_evidence',title='Priority group · localization agreement and review needs'),width='stretch')
    cols=['sequence_id','species','assigned_family','orthogroup','orthology_scope','schistosome_species_in_HOG','architecture','DeepTMHMM','DeepLoc_2.1','domain_evidence','topology_evidence','motif_context_evidence','evidence_review_stage','host_orthology_flag']
    st.dataframe(subset[[c for c in cols if c in subset]],width='stretch',hide_index=True)
    st.download_button('Download this priority group',subset.to_csv(index=False),'fn3_priority_group.csv')
    st.caption('Conserved secreted group: shared HOG with copies reported in all three schistosome species and source assignment secreted_FN3_protein_like. The two Schistosoma-only groups require that exact sampled-HOG status and the corresponding receptor class. General single-pass membrane FN3 proteins are not automatically classified as adhesion receptors.')
