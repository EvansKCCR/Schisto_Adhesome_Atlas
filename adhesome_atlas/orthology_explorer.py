"""Explore standalone orthology exports without modifying source assignments."""
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from data import ROOT
from phylogeny_view import NAMES


def read_collection(folder):
    return tuple(pd.read_csv(folder/name,sep='\t',dtype=str).fillna('') for name in ['candidate_report.tsv','candidate_HOGs.tsv','direct_orthologues.tsv'])


def orthology_panel():
    st.header('Orthology')
    st.write('Explore evolutionary relationships, reference orthologues and gene-family copy counts across eight species.')
    st.caption('References: H. sapiens (GRCh38.p14) · M. musculus (GRCm39) · X. laevis (Xenopus_laevis_v10.1) · D. melanogaster (GCF_000001215.4) · C. elegans (PRJNA13758). Controls here are independent of the catalogue sidebar filters.')
    folders=sorted(p.parent for p in (ROOT/'orthology').glob('*/candidate_report.tsv'))
    if not folders:
        st.info('No orthology candidate reports found.'); return
    labels={'adhesome_candidates_list':'Adhesome candidates','fibronectin_like_candidate':'Fibronectin-like candidates'}
    folder=st.selectbox('Orthology collection',folders,format_func=lambda p:labels.get(p.name,p.name),key='orthology_collection')
    report,hogs,direct=read_collection(folder)
    species=st.multiselect('Candidate species',['Shae','Sjap','Sman'],default=['Shae','Sjap','Sman'],format_func=NAMES.get,key='orthology_species')
    scope=st.multiselect('Evolutionary scope',sorted(report.HOG_status.unique()),key='orthology_scope')
    query=st.text_input('Find a candidate, reference protein or orthogroup',key='orthology_search')
    selected=report[report.candidate_id.str.split('__').str[0].isin(species)].copy()
    if scope: selected=selected[selected.HOG_status.isin(scope)]
    if query: selected=selected[selected.apply(lambda col:col.astype(str).str.contains(query,case=False,regex=False)).any(axis=1)]
    selected_hogs=hogs[hogs.Orthogroup.isin(set(selected.Orthogroup)-{''})]
    selected_direct=direct[direct.candidate_id.isin(selected.candidate_id)]
    for col,label,value in zip(st.columns(4),['Candidates','Mapped candidates','Orthogroups','Reference relationship records'],[selected.candidate_id.nunique(),selected.loc[selected.mapping_status.eq('matched'),'candidate_id'].nunique(),selected_hogs.Orthogroup.nunique(),len(selected_direct)]):
        col.metric(label,value)
    st.caption('Relationship records may contain multiple orthologue IDs; they are not individual protein-pair counts. Copy counts describe all members of each selected orthogroup, including non-candidates.')
    tabs=st.tabs(['Summary','Candidate assignments','Orthogroup membership','Direct orthologues','Provenance & downloads'])
    with tabs[0]:
        if selected.empty: st.info('No candidates match these filters.')
        else:
            summary=selected.assign(species=selected.candidate_id.str.split('__').str[0].map(NAMES)).groupby(['species','HOG_status']).candidate_id.nunique().reset_index(name='Candidates')
            st.plotly_chart(px.bar(summary,x='species',y='Candidates',color='HOG_status',title='Evolutionary scope by candidate species'),width='stretch')
        if not selected_direct.empty:
            relationships=selected_direct.groupby(['reference_species','relationship']).candidate_id.nunique().reset_index(name='Candidates')
            relationships.reference_species=relationships.reference_species.map(NAMES)
            st.plotly_chart(px.bar(relationships,x='reference_species',y='Candidates',color='relationship',title='Direct orthology relationship types'),width='stretch')
        if not selected_hogs.empty:
            display=selected_hogs.sort_values('Orthogroup').head(60)
            codes=[c for c in ['Shae','Sjap','Sman','Hsap','Mmus','Xlae','Dmel','Cele'] if c in display]
            matrix=display.set_index('Orthogroup')[codes].map(lambda x:len({v.strip() for v in x.split(',') if v.strip()}))
            st.plotly_chart(px.imshow(matrix.rename(columns=NAMES),aspect='auto',color_continuous_scale='YlGn',labels={'color':'Proteins'},title='Orthogroup copy counts',height=max(350,len(matrix)*20)),width='stretch')
            st.caption(f'Showing {len(display)} of {len(selected_hogs)} selected orthogroups in alphabetical order. Search to focus the heatmap; the membership table includes every selected group.')
    with tabs[1]:
        st.dataframe(selected,width='stretch',hide_index=True)
        st.download_button('Download filtered candidate assignments',selected.to_csv(index=False),folder.name+'_candidates.csv','text/csv')
    with tabs[2]:
        st.dataframe(selected_hogs,width='stretch',hide_index=True)
        st.download_button('Download filtered orthogroups',selected_hogs.to_csv(index=False),folder.name+'_orthogroups.csv','text/csv')
    with tabs[3]:
        refs=st.multiselect('Reference species',sorted(direct.reference_species.unique()),format_func=NAMES.get,key='orthology_refs')
        types=st.multiselect('Relationship types',sorted(direct.relationship.unique()),key='orthology_relationships')
        filtered=selected_direct
        if refs: filtered=filtered[filtered.reference_species.isin(refs)]
        if types: filtered=filtered[filtered.relationship.isin(types)]
        st.dataframe(filtered,width='stretch',hide_index=True)
        st.download_button('Download filtered direct orthologues',filtered.to_csv(index=False),folder.name+'_direct_orthologues.csv','text/csv')
    with tabs[4]:
        provenance=folder/'provenance.json'
        if provenance.exists(): st.json(json.loads(provenance.read_text(encoding='utf-8')),expanded=False)
        st.caption('Original exports preserve source paths and hashes. Downloads below contain complete source files, independent of active filters.')
        for path in sorted(folder.iterdir()):
            if path.is_file(): st.download_button('Download '+path.name,path.read_bytes(),folder.name+'_'+path.name,key='orthology_original_'+path.name)
