"""Orthology explorer driven by the active candidate reports."""
import pandas as pd
import plotly.express as px
import streamlit as st
from data import ROOT
from figure_exports import plotly_chart

def orthology_panel(candidates):
    st.header('Orthology')
    folders=sorted(p.parent for p in (ROOT/'orthology').rglob('candidate_report.tsv'))
    if not folders: st.info('No orthology report is present in the current library.');return
    folder=st.selectbox('Orthology collection',folders,format_func=lambda p:p.name)
    signature=tuple((p.name,p.stat().st_mtime_ns,p.stat().st_size) for p in folder.glob('*') if p.is_file())
    @st.cache_data(show_spinner=False)
    def read(folder,signature):
        return tuple(pd.read_csv(folder/name,sep='\t',dtype=str).fillna('') for name in ['candidate_report.tsv','candidate_HOGs.tsv','direct_orthologues.tsv'])
    report,hogs,direct=read(folder,signature)
    annotations=candidates.drop_duplicates('sequence_id').set_index('sequence_id')
    report=report[report.candidate_id.isin(annotations.index)].copy()
    for field in ['family','species','candidate_annotation','grade','assignment_confidence']:
        report[field]=report.candidate_id.map(annotations[field])
    refs=sorted(direct.reference_species.unique())
    st.caption(f'{candidates.species.nunique()} candidate species; {len(refs)} reference taxa in the active direct-orthologue report. Reference names and copy counts follow the report headers. Orthogroup IDs belong to this run; no historical groups are merged.')
    a,b=st.columns(2)
    species=a.multiselect('Orthology species',sorted(report.species.unique()),default=sorted(report.species.unique()))
    families=b.multiselect('Orthology families',sorted(report.family.unique()))
    query=st.text_input('Find a candidate, orthogroup or reference protein')
    selected=report[report.species.isin(species)]
    if families:selected=selected[selected.family.isin(families)]
    if query:selected=selected[selected.astype(str).apply(lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)]
    groups=hogs[hogs.Orthogroup.isin(set(selected.Orthogroup)-{''})]
    direct=direct[direct.candidate_id.isin(selected.candidate_id)]
    for col,label,value in zip(st.columns(4),['Candidates','Orthogroups','Reference taxa','Relationship records'],[selected.candidate_id.nunique(),groups.Orthogroup.nunique(),direct.reference_species.nunique(),len(direct)]): col.metric(label,value)
    tabs=st.tabs(['Overview','Candidate assignments','Orthogroup members','Direct orthologues'])
    with tabs[0]:
        if len(selected):plotly_chart(px.bar(selected.groupby(['species','HOG_status']).size().reset_index(name='Candidates'),x='species',y='Candidates',color='HOG_status'),width='stretch')
        st.dataframe(pd.DataFrame({'Reference taxon':refs}),hide_index=True,width='stretch')
        numeric=[col for col in groups if col not in ['Orthogroup','Matched_candidates']]
        display=groups.head(40).copy()
        if not display.empty:
            counts=display.set_index('Orthogroup')[numeric].map(lambda value:len([v for v in str(value).split(',') if v.strip()]))
            plotly_chart(px.imshow(counts,aspect='auto',title='Orthogroup member counts · first 40 selected groups'),width='stretch')
    for tab,frame,name in [(tabs[1],selected,'candidate_assignments'),(tabs[2],groups,'orthogroup_members'),(tabs[3],direct,'direct_orthologues')]:
        with tab:
            st.dataframe(frame,width='stretch',hide_index=True)
            st.download_button('Download '+name.replace('_',' '),frame.to_csv(index=False),name+'.csv')
