"""Interactive exploration of the local Pfam/CDD reclassification library."""
from urllib.parse import urlsplit,urlunsplit,urlencode
import pandas as pd
import plotly.express as px
import streamlit as st

from candidate_profiles import atlas_url
from figure_exports import plotly_chart
from reclassification import FILE,TIER_LABELS,reconciliation_table


def map_url(base,protein):
    from navigation import hypothesis_url
    return hypothesis_url(base,protein,'pfam_cdd')


def reclassification_panel(candidates,classified,base,library_candidates=None):
    st.subheader('Local Pfam–CDD family reclassification')
    st.write('Explore diagnostic family assignments, divergent architecture-associated hypotheses and broader domain classes. Reclassification tiers A–D describe Pfam/CDD evidence; catalogue grades and family-support decisions remain separate.')
    if classified is None:
        st.info('To be updated when adhesome_unassigned_Pfam_CDD_classification.xlsx is available.');return
    reviewed=candidates[candidates.reclassification_tier.ne('')].drop_duplicates('sequence_id')
    if reviewed.empty:
        st.info('No reclassification records match the sidebar filters. Select All or Unassigned catalogue classifications to explore recovered families.');return
    for box,(label,value) in zip(st.columns(5),[('Reclassified proteins',len(reviewed))]+[
        (tier+' · '+label,int(reviewed.reclassification_tier.eq(tier).sum())) for tier,label in TIER_LABELS.items()]):box.metric(label,f'{value:,}')
    a,b,c=st.columns(3)
    tiers=a.multiselect('Pfam–CDD evidence tiers',list(TIER_LABELS),default=['A','B'],key='pfam_cdd_tiers',format_func=lambda t:t+' · '+TIER_LABELS[t])
    families=b.multiselect('Reclassified family / domain class',sorted(reviewed.reclassification_family.unique()),key='pfam_cdd_families')
    modules=c.multiselect('Reclassification functional module',sorted(reviewed.reclassification_module.unique()),key='pfam_cdd_modules')
    a,b=st.columns([1,2])
    priorities=a.multiselect('Reclassification priority',sorted(reviewed.reclassification_priority.unique()),key='pfam_cdd_priority')
    query=b.text_input('Search reclassification evidence',placeholder='Protein, orthogroup, family, Pfam, CDD or rationale',key='pfam_cdd_query')
    visible=reviewed[reviewed.reclassification_tier.isin(tiers)]
    for names,field in [(families,'reclassification_family'),(modules,'reclassification_module'),(priorities,'reclassification_priority')]:
        if names:visible=visible[visible[field].isin(names)]
    if query:
        fields=['sequence_id','species','orthogroup','family','reclassification_family','reclassification_rationale','reclassification_pfam','reclassification_cdd','reclassification_orthogroup_context']
        visible=visible[visible[fields].fillna('').astype(str).apply(lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)]
    visible=visible.sort_values(['reclassification_tier','reclassification_priority','reclassification_family','sequence_id']).reset_index(drop=True)
    st.caption(f'{len(visible):,} of {len(reviewed):,} proteins shown. Sidebar species, family and catalogue-grade filters also apply. Orthogroup hints are retained as context and do not upgrade a domain class.')
    tabs=st.tabs(['Family exploration','Candidate evidence','Reconciliation'])
    with tabs[0]:
        if len(visible):
            counts=visible.groupby(['reclassification_family','reclassification_tier']).size().reset_index(name='Proteins')
            plotly_chart(px.bar(counts,x='Proteins',y='reclassification_family',color='reclassification_tier',orientation='h',
                height=max(430,counts.reclassification_family.nunique()*26),labels={'reclassification_family':'Family / domain class','reclassification_tier':'Evidence tier'},
                color_discrete_map={'A':'#22734f','B':'#5b9e8a','C':'#d3ad42','D':'#aab6b1'},title='Pfam–CDD family and domain evidence'),width='stretch')
            matrix=visible.groupby(['reclassification_module','species']).size().unstack(fill_value=0)
            plotly_chart(px.imshow(matrix,aspect='auto',text_auto=True,color_continuous_scale='Greens',height=430,
                labels={'x':'Species','y':'Functional context','color':'Proteins'},title='Reclassified functional contexts across species'),width='stretch')
        else:st.info('No records match these reclassification filters.')
    with tabs[1]:
        columns=['sequence_id','species','orthogroup','reclassification_family','reclassification_evidence_tier','reclassification_priority',
            'reclassification_module','family','grade','family_support_level','reclassification_alignment','reclassification_rationale']
        table=visible[columns].copy()
        table['Protein dossier']=table.sequence_id.map(lambda p:atlas_url(base,'Protein dossier',p))
        table['Hypothesis map']=table.sequence_id.map(lambda p:map_url(base,p))
        event=st.dataframe(table,hide_index=True,width='stretch',on_select='rerun',selection_mode='single-row',key='pfam_cdd_table',
            column_config={name:st.column_config.LinkColumn(name,display_text='Explore ↗') for name in ['Protein dossier','Hypothesis map']})
        if len(visible):
            chosen=event.selection.rows
            labels=visible.set_index('sequence_id').reclassification_family.to_dict()
            if st.session_state.get('pfam_cdd_protein') not in labels:st.session_state['pfam_cdd_protein']=visible.iloc[0].sequence_id
            if chosen and chosen[0]<len(visible):
                row_id=visible.iloc[chosen[0]].sequence_id
                if st.session_state.get('pfam_cdd_selected_row')!=row_id:
                    st.session_state['pfam_cdd_selected_row']=row_id;st.session_state['pfam_cdd_protein']=row_id
            protein=st.selectbox('Inspect reclassified candidate',visible.sequence_id.tolist(),format_func=lambda p:p+' · '+labels[p],key='pfam_cdd_protein')
            row=visible[visible.sequence_id.eq(protein)].iloc[0]
            st.write('**'+row.reclassification_family+'** · '+row.reclassification_evidence_tier)
            st.write(row.reclassification_rationale)
            st.dataframe(row[['reclassification_pfam','reclassification_cdd','reclassification_orthogroup_context',
                'family','grade','family_support_level','reclassification_alignment']].rename_axis('Evidence field').reset_index(name='Value'),hide_index=True,width='stretch')
            a,b=st.columns(2)
            a.link_button('Open Protein dossier ↗',atlas_url(base,'Protein dossier',protein))
            b.link_button('Locate reclassified family on the hypothesis map ↗',map_url(base,protein))
    with tabs[2]:
        report=reconciliation_table(library_candidates if library_candidates is not None else candidates,classified)
        diagnostics=candidates.attrs.get('reclassification',{})
        st.write('Exact protein IDs connect the two libraries. Original Pfam/CDD strings, orthogroups, species and catalogue decisions are retained alongside the reclassification.')
        st.caption(f"Unmatched source IDs: {len(diagnostics.get('unmatched_ids',[])):,} · changed evidence: {diagnostics.get('stale_proteins',0):,} · supported catalogue overlaps: {diagnostics.get('supported_catalogue_overlaps',0):,}.")
        st.dataframe(report,hide_index=True,width='stretch')
        st.download_button('Download complete reconciliation',report.to_csv(index=False).encode('utf-8'),'Pfam_CDD_reconciliation.csv','text/csv')
    st.download_button('Download filtered Pfam–CDD evidence',visible.to_csv(index=False).encode('utf-8'),'Pfam_CDD_filtered_candidates.csv','text/csv')
