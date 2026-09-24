"""Explore standalone orthology exports without modifying source assignments."""
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from data import ROOT
from identifier_labels import identifier_annotations
import re
from phylogeny_view import NAMES


def read_collection(folder):
    return tuple(pd.read_csv(folder/name,sep='\t',dtype=str).fillna('') for name in ['candidate_report.tsv','candidate_HOGs.tsv','direct_orthologues.tsv'])


def orthology_panel(candidates=None):
    st.header('Orthology')
    st.write('Explore evolutionary relationships, reference orthologues and gene-family copy counts across eight species.')
    st.caption('References: H. sapiens (GRCh38.p14) · M. musculus (GRCm39) · X. laevis (Xenopus_laevis_v10.1) · D. melanogaster (GCF_000001215.4) · C. elegans (PRJNA13758). Controls here are independent of the catalogue sidebar filters.')
    folders=sorted(p.parent for p in (ROOT/'orthology').glob('*/candidate_report.tsv'))
    if not folders:
        st.info('No orthology candidate reports found.'); return
    labels={'adhesome_candidates_list':'Adhesome candidates','fibronectin_like_candidate':'Fibronectin-like candidates'}
    folder=st.selectbox('Orthology collection',folders,format_func=lambda p:labels.get(p.name,p.name),key='orthology_collection')
    report,hogs,direct=read_collection(folder)
    if candidates is not None and {'sequence_id','family','source'} <= set(candidates):
        subset=candidates[candidates.source.str.contains(folder.name,regex=False,na=False)]
        families=subset.groupby('sequence_id').family.agg(lambda values:' | '.join(sorted(set(values.dropna()))))
        report['family']=report.candidate_id.map(families).fillna('Unassigned family')
    else:
        report['family']='Unassigned family'
    grouping=ROOT/'phylogeny_family_groups.tsv'
    if grouping.exists():
        curated=pd.read_csv(grouping,sep='\t')
        labels_by_og=curated.groupby('orthogroup').family.agg(lambda values:' | '.join(sorted(set(values))))
        report['family']=report.Orthogroup.map(labels_by_og).fillna(report.family)
    annotations=identifier_annotations()
    lookup={key:key.split('__')[0]+'__'+row.protein_annotation_id for key,row in annotations.iterrows() if row.protein_annotation_id}
    def display_ids(frame):
        displayed=frame.copy()
        for col in displayed:
            displayed[col]=displayed[col].map(lambda value:re.sub(r'[A-Za-z]+__[A-Za-z0-9_.-]+',lambda match:lookup.get(match.group(),match.group()),str(value)))
        return displayed
    st.caption('Protein accessions are displayed using identifier maps. Original gene IDs remain available in the source downloads; search accepts either identifier.')

    species=st.multiselect('Candidate species',['Shae','Sjap','Sman'],default=['Shae','Sjap','Sman'],format_func=NAMES.get,key='orthology_species')
    families=sorted({family for value in report.family for family in value.split(' | ')})
    family=st.selectbox('Protein family',['All families']+families,key='orthology_family')
    scope=st.multiselect('Evolutionary scope',sorted(report.HOG_status.unique()),key='orthology_scope')
    query=st.text_input('Find a candidate, reference protein or orthogroup',key='orthology_search')
    selected=report[report.candidate_id.str.split('__').str[0].isin(species)].copy()
    if family!='All families': selected=selected[selected.family.map(lambda value:family in value.split(' | '))]
    if scope: selected=selected[selected.HOG_status.isin(scope)]
    if query: selected=selected[selected.apply(lambda col:col.astype(str).str.contains(query,case=False,regex=False)).any(axis=1) | display_ids(selected).apply(lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)]
    selected_hogs=hogs[hogs.Orthogroup.isin(set(selected.Orthogroup)-{''})]
    selected_direct=direct[direct.candidate_id.isin(selected.candidate_id)]
    for col,label,value in zip(st.columns(4),['Candidates','Mapped candidates','Orthogroups','Reference relationship records'],[selected.candidate_id.nunique(),selected.loc[selected.mapping_status.eq('matched'),'candidate_id'].nunique(),selected_hogs.Orthogroup.nunique(),len(selected_direct)]):
        col.metric(label,value)
    st.caption('Relationship records may contain multiple orthologue IDs; they are not individual protein-pair counts. Copy counts describe all members of each selected orthogroup, including non-candidates.')
    tabs=st.tabs(['Summary','Candidate assignments','Orthogroup membership','Direct orthologues','Provenance & downloads'])
    with tabs[0]:
        if family!='All families' and not selected.empty:
            st.subheader('Family orthogroups')
            family_members=selected.groupby('Orthogroup').candidate_id.agg(lambda values:', '.join(sorted(set(values)))).reset_index(name='Candidate proteins')
            st.dataframe(display_ids(family_members),width='stretch',hide_index=True)
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
        st.dataframe(display_ids(selected),width='stretch',hide_index=True)
        st.download_button('Download filtered candidate assignments',display_ids(selected).to_csv(index=False),folder.name+'_candidates.csv','text/csv')
    with tabs[2]:
        st.dataframe(display_ids(selected_hogs),width='stretch',hide_index=True)
        st.download_button('Download filtered orthogroups',display_ids(selected_hogs).to_csv(index=False),folder.name+'_orthogroups.csv','text/csv')
    with tabs[3]:
        refs=st.multiselect('Reference species',sorted(direct.reference_species.unique()),format_func=NAMES.get,key='orthology_refs')
        types=st.multiselect('Relationship types',sorted(direct.relationship.unique()),key='orthology_relationships')
        filtered=selected_direct
        if refs: filtered=filtered[filtered.reference_species.isin(refs)]
        if types: filtered=filtered[filtered.relationship.isin(types)]
        st.dataframe(display_ids(filtered),width='stretch',hide_index=True)
        st.download_button('Download filtered direct orthologues',display_ids(filtered).to_csv(index=False),folder.name+'_direct_orthologues.csv','text/csv')
    with tabs[4]:
        provenance=folder/'provenance.json'
        if provenance.exists(): st.json(json.loads(provenance.read_text(encoding='utf-8')),expanded=False)
        st.caption('Original exports preserve source paths and hashes. Downloads below contain complete source files, independent of active filters.')
        for path in sorted(folder.iterdir()):
            if path.is_file(): st.download_button('Download '+path.name,path.read_bytes(),folder.name+'_'+path.name,key='orthology_original_'+path.name)
