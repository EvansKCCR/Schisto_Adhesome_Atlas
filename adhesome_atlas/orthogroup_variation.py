"""Read-only interspecific copy-number report, separate from exact-profile evidence."""
from pathlib import Path
import re
import warnings
from zipfile import BadZipFile

import pandas as pd
import plotly.express as px

from orthogroup_statistics import SPECIES,related_candidates

WORKBOOK='schistosoma_interspecific_copy_number_variation.xlsx'
MARKED_TSV='schistosoma_marked_copy_variation_46.tsv'
REPORT_VARIATION='Interspecific copy-number summary'
REPORT_EXACT='Exact copy profiles'
DELTA='Max−min Δ'
NUMERIC=['Supported n','Total candidates','Unresolved n','Species present','Reference taxa count',DELTA]+SPECIES
REQUIRED=['Orthogroup','Supported family identity','Supported n']+SPECIES+[DELTA,'Species present',
    'Total candidates','Unresolved n','Reference taxa count','Reference species support',
    'All candidate family labels','Family-support breakdown']


def variation_signature(folder):
    folder=Path(folder)
    return tuple((name,(folder/name).stat().st_mtime_ns,(folder/name).stat().st_size)
        for name in [WORKBOOK,MARKED_TSV] if (folder/name).exists())


def _validate(frame,label):
    missing=set(REQUIRED)-set(frame)
    if missing:raise ValueError(label+' is missing: '+', '.join(sorted(missing)))
    result=frame.copy();result['Orthogroup']=result.Orthogroup.astype(str).str.strip()
    result=result[result.Orthogroup.ne('')].copy()
    for field in NUMERIC:
        value=pd.to_numeric(result[field],errors='coerce')
        if value.isna().any() or value.lt(0).any() or value.mod(1).ne(0).any():
            raise ValueError(label+' requires non-negative integer counts: '+field)
        result[field]=value.astype('int64')
    result=result.drop_duplicates().reset_index(drop=True)
    if result.Orthogroup.duplicated().any():raise ValueError(label+' has conflicting duplicate orthogroup records.')
    return result.fillna('')


def support_breakdown(text):
    result={}
    for part in str(text).split(';'):
        if not part.strip():continue
        match=re.fullmatch(r'\s*([^:]+):\s*(\d+)\s*',part)
        if not match:raise ValueError('Cannot read family-support breakdown: '+str(text))
        label=match[1].strip();result[label]=result.get(label,0)+int(match[2])
    return result


def family_labels(row):
    if row['Supported n']==0:return []
    return [match[1].strip() for match in re.finditer(r'(?:^|;)\s*([^;]+?)\s*\((\d+)\)\s*(?=;|$)',str(row['Supported family identity']))]


def load_variation(folder):
    folder=Path(folder)
    # Formatting-extension warnings concern re-saving XLSX; these files are only read.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',message='.*extension is not supported.*',category=UserWarning)
        sheets=pd.read_excel(folder/WORKBOOK,sheet_name=None,header=None,keep_default_na=False)
    frames={};notes={}
    for name in ['All orthogroups','Marked differences','Pronounced differences']:
        if name not in sheets:raise ValueError(WORKBOOK+' is missing worksheet '+name)
        raw=sheets[name];headers=raw.index[raw.iloc[:,0].astype(str).str.strip().eq('Orthogroup')]
        if not len(headers):raise ValueError(name+' has no Orthogroup header row.')
        start=headers[0];frame=raw.iloc[start+1:].copy();frame.columns=raw.iloc[start].astype(str).tolist()
        frames[name]=_validate(frame,name)
        notes[name]=[str(value) for value in raw.iloc[:start,0] if str(value).strip()]
    master=frames['All orthogroups'].copy();checks=[];index=master.set_index('Orthogroup')
    for name,threshold in [('Marked differences',2),('Pronounced differences',3)]:
        subset=frames[name]
        for _,row in subset.iterrows():
            if row.Orthogroup not in index.index:
                checks.append({'Orthogroup':row.Orthogroup,'Issue':name+': not in all-orthogroup worksheet; not added to totals'})
            elif any(row[field]!=index.loc[row.Orthogroup,field] for field in REQUIRED if field!='Orthogroup'):
                checks.append({'Orthogroup':row.Orthogroup,'Issue':name+': values differ; all-orthogroup worksheet retained'})
        expected=set(master.loc[master[DELTA].ge(threshold),'Orthogroup'])
        if set(subset.Orthogroup)!=expected:checks.append({'Orthogroup':'','Issue':name+' membership differs from reported Δ threshold'})
        master['In '+name.lower()]=master.Orthogroup.isin(subset.Orthogroup)
    if (folder/MARKED_TSV).exists():
        companion=_validate(pd.read_csv(folder/MARKED_TSV,sep='\t',keep_default_na=False),MARKED_TSV)
        frames['Marked TSV']=companion
        if set(companion.Orthogroup)!=set(frames['Marked differences'].Orthogroup):
            checks.append({'Orthogroup':'','Issue':'Marked TSV membership differs from the workbook worksheet'})
        shared=set(companion.Orthogroup)&set(index.index)
        for _,row in companion[companion.Orthogroup.isin(shared)].iterrows():
            if any(row[field]!=index.loc[row.Orthogroup,field] for field in REQUIRED if field!='Orthogroup'):
                checks.append({'Orthogroup':row.Orthogroup,'Issue':'Marked TSV values differ; workbook values retained'})
    breakdowns=master['Family-support breakdown'].map(support_breakdown)
    for label in sorted({label for values in breakdowns for label in values}):
        master['Support state: '+label]=breakdowns.map(lambda values:values.get(label,0))
    coverage=[]
    for _,row in master.iterrows():
        counts=[row[sp] for sp in SPECIES];states=support_breakdown(row['Family-support breakdown'])
        for condition,issue in [
            (sum(counts)!=row['Total candidates'],'Species copy counts do not sum to Total candidates'),
            (max(counts)-min(counts)!=row[DELTA],'Species copy spread differs from reported Δ'),
            (sum(value>0 for value in counts)!=row['Species present'],'Species-presence count differs'),
            (sum(states.values())!=row['Total candidates'],'Support-state breakdown does not sum to Total candidates'),
            (states.get('specific supported',0)+states.get('broad supported',0)!=row['Supported n'],'Supported breakdown differs from Supported n'),
            (states.get('unresolved',0)!=row['Unresolved n'],'Unresolved breakdown differs from Unresolved n')]:
            if condition:checks.append({'Orthogroup':row.Orthogroup,'Issue':issue})
        coverage.append('All copies supported' if row['Supported n']==row['Total candidates'] and row['Total candidates'] else
            'Some copies supported' if row['Supported n'] else 'No supported copies')
    master['Supported copy coverage']=coverage
    return master,frames,pd.DataFrame(checks,columns=['Orthogroup','Issue']),notes


def filter_variation(master,scope='All orthogroups',species=(),families=(),coverage=(),query=''):
    frame=master.copy()
    if scope!='All orthogroups':frame=frame[frame['In '+scope.lower()]]
    if species:frame=frame[frame[list(species)].gt(0).any(axis=1)]
    if families:frame=frame[frame.apply(lambda row:bool(set(family_labels(row))&set(families)),axis=1)]
    if coverage:frame=frame[frame['Supported copy coverage'].isin(coverage)]
    if query:frame=frame[frame[REQUIRED].astype(str).apply(lambda values:values.str.contains(query,case=False,regex=False)).any(axis=1)]
    return frame.reset_index(drop=True)


def variation_panel(candidates,folder):
    import streamlit as st
    from figure_exports import plotly_chart
    from research_priorities import target_url
    from phylogeny_view import discover_trees
    prefix='og_variation_'
    @st.cache_data(show_spinner='Reading copy-number summary workbook…',max_entries=4)
    def read(path,signature):return load_variation(path)
    try:master,frames,checks,notes=read(folder,variation_signature(folder))
    except (OSError,ValueError,BadZipFile) as error:st.info('Copy-number summary awaits a readable report: '+str(error));return
    st.caption('Workbook scope: all reported orthogroups, including unequal copy profiles. Δ is max−min across the seven species, including recorded zeros. Marked (Δ ≥ 2) and pronounced (Δ ≥ 3) are descriptive thresholds, not significance tests.')
    a,b,c=st.columns(3)
    scope=a.selectbox('Summary report subset',['All orthogroups','Marked differences','Pronounced differences'],key=prefix+'scope')
    species=b.multiselect('Summary species',SPECIES,key=prefix+'species')
    options=sorted({family for _,row in master.iterrows() for family in family_labels(row)})
    family_key=prefix+'families'
    if family_key in st.session_state:st.session_state[family_key]=[name for name in st.session_state[family_key] if name in options]
    families=c.multiselect('Summary supported families',options,key=family_key)
    a,b=st.columns([1,2])
    coverage_options=list(master['Supported copy coverage'].unique())
    if prefix+'coverage' in st.session_state:st.session_state[prefix+'coverage']=[v for v in st.session_state[prefix+'coverage'] if v in coverage_options]
    coverage=a.multiselect('Supported copy coverage',coverage_options,key=prefix+'coverage')
    query=b.text_input('Find a summary orthogroup, family or reference taxon',key=prefix+'query')
    chosen=filter_variation(master,scope,species,families,coverage,query)
    st.markdown('<style>.st-key-orthogroup_variation_summary [data-testid="stMetricValue"]{font-size:clamp(16px,1.55vw,30px)!important}'
        '.st-key-orthogroup_variation_summary [data-testid="stMetricValue"] *{font-size:inherit!important}</style>',unsafe_allow_html=True)
    with st.container(key='orthogroup_variation_summary'):
        for column,label,value in zip(st.columns(4),['Orthogroups','Marked Δ ≥ 2','Pronounced Δ ≥ 3','Supported / total copies'],
            [len(chosen),int(chosen['In marked differences'].sum()),int(chosen['In pronounced differences'].sum()),
             f'{chosen["Supported n"].sum():,} / {chosen["Total candidates"].sum():,}']):column.metric(label,value)
    state_columns=[name for name in chosen if name.startswith('Support state: ')]
    st.caption('Support states in this selection: '+', '.join(name.removeprefix('Support state: ')+f' = {chosen[name].sum():,}' for name in state_columns)+'.')
    st.caption('This report does not provide A/B totals or supported-copy counts per species. Exact-profile tables retain those reported fields; linked Atlas dossiers show their current candidate grades.')
    if chosen.empty:st.info('No summary orthogroups match these filters.')
    else:
        view=st.selectbox('Summary visualization',['Copy-number spread','Species copy heatmap','Support states'],key=prefix+'visual')
        if view=='Copy-number spread':
            counts=chosen.groupby(DELTA).size().reset_index(name='Orthogroups')
            figure=px.bar(counts,x=DELTA,y='Orthogroups',text='Orthogroups',color_discrete_sequence=['#08743f'],title='Interspecific copy-number spread')
            figure.update_xaxes(dtick=1)
        elif view=='Support states':
            counts=pd.DataFrame({'Support state':[name.removeprefix('Support state: ') for name in state_columns],
                'Candidate copies':[chosen[name].sum() for name in state_columns]})
            figure=px.bar(counts,x='Support state',y='Candidate copies',text='Candidate copies',color_discrete_sequence=['#08743f'],title='Reported support-state composition')
        else:
            limit=st.selectbox('Maximum summary heatmap rows',[20,40,80,'All filtered groups'],index=1,key=prefix+'rows')
            visible=chosen.sort_values([DELTA,'Orthogroup'],ascending=[False,True])
            if isinstance(limit,int):visible=visible.head(limit)
            figure=px.imshow(visible.set_index('Orthogroup')[SPECIES],text_auto=True,aspect='auto',zmin=0,
                color_continuous_scale=['#ffffff','#f0d36d','#08743f'],title='Species copy counts · summary report',height=max(420,len(visible)*26+150))
            st.caption(f'Heatmap: {len(visible)} of {len(chosen)} filtered groups. The table retains all groups.')
        plotly_chart(figure,width='stretch',key=prefix+'plot')
        st.subheader('Summary orthogroup explorer')
        st.caption(f'{len(chosen)} of {len(master)} report groups. Select a row or use the orthogroup selector. Support-state counts are retained separately; unresolved, ambiguous and provisional are not combined.')
        ids=chosen.Orthogroup.tolist();focus_key=prefix+'focus'
        if st.session_state.get(focus_key) not in ids:st.session_state[focus_key]=ids[0]
        table_key=prefix+'table'
        def select_row():
            rows=st.session_state.get(table_key,{}).get('selection',{}).get('rows',[])
            if rows and 0<=rows[-1]<len(ids):st.session_state[focus_key]=ids[rows[-1]]
        left,right=st.columns([1.5,1])
        with left:st.dataframe(chosen[REQUIRED],hide_index=True,width='stretch',height=430,key=table_key,on_select=select_row,selection_mode='single-row')
        with right:
            group=st.selectbox('Inspect summary orthogroup',ids,key=focus_key)
            row=chosen.set_index('Orthogroup',drop=False).loc[group]
            st.subheader(group);st.write('**'+row['Supported family identity']+'**')
            st.caption(f'Supported {row["Supported n"]} / total {row["Total candidates"]}; Δ = {row[DELTA]}; {row["Species present"]} species present.')
            st.dataframe(pd.DataFrame({'Species':SPECIES,'Reported copies':[row[sp] for sp in SPECIES]}),hide_index=True,width='stretch',height=294)
            st.write('Support breakdown: '+row['Family-support breakdown'])
            with st.expander('Family labels and reference evidence'):
                st.write(row['All candidate family labels']);st.write(f'{row["Reference taxa count"]} reference taxa: '+row['Reference species support'])
            tree_ids={path.name for path in discover_trees()[0]};base=st.context.url or ''
            if group in tree_ids:st.link_button('Explore summary orthogroup phylogeny ↗',target_url(base,'Phylogeny',orthogroup=group))
            else:st.caption('No matching gene tree is present in the current library.')
            st.link_button('Open summary reference orthologues ↗',target_url(base,'Orthology',orthogroup=group,workspace='references'))
            from orthogroup_statistics import FILES
            exact=Path(folder)/FILES['all']
            if exact.exists() and group in set(pd.read_csv(exact,sep='\t',usecols=['Orthogroup']).Orthogroup):
                def open_exact():
                    from orthogroup_dashboard import reset_filters,PREFIX
                    reset_filters();st.session_state['og_statistics_report']=REPORT_EXACT
                    st.session_state[PREFIX+'focus']=group;st.session_state[PREFIX+'query']=group
                st.button('Open exact-profile support record',on_click=open_exact,key=prefix+'exact')
        st.subheader('Linked summary candidate dossiers')
        linked=related_candidates(candidates,group,st.context.url or '')
        st.caption(f'{len(linked)} Atlas records / {linked.sequence_id.nunique()} unique proteins linked by exact orthogroup ID; workbook totals remain authoritative.')
        if linked.empty:st.info('No linked candidate identifiers are present in the current Atlas.')
        else:
            fields=[name for name in ['sequence_id','species','family','grade','candidate_annotation','architecture','Protein dossier'] if name in linked]
            st.dataframe(linked[fields],hide_index=True,width='stretch',column_config={'Protein dossier':st.column_config.LinkColumn(display_text='Open dossier ↗')})
        st.download_button('Download selected summary record',chosen[chosen.Orthogroup.eq(group)].to_csv(sep='\t',index=False),group+'_copy_number_summary.tsv',key=prefix+'record')
    st.download_button('Download filtered copy-number summary',chosen.to_csv(sep='\t',index=False),'orthogroup_copy_number_summary.tsv',key=prefix+'download')
    with st.expander('Summary report sources and validation'):
        st.dataframe(pd.DataFrame([{'Report':name,'Orthogroups':len(frame)} for name,frame in frames.items()]),hide_index=True,width='stretch')
        for name,paragraphs in notes.items():
            for paragraph in paragraphs:st.caption(name+': '+paragraph)
        if checks.empty:st.success('Species sums, copy-number spreads, support-state breakdowns and subset/TSV memberships agree.')
        else:st.dataframe(checks,width='stretch',hide_index=True)
        st.download_button('Download original copy-number summary workbook',(Path(folder)/WORKBOOK).read_bytes(),WORKBOOK,key=prefix+'workbook')
        if (Path(folder)/MARKED_TSV).exists():st.download_button('Download marked-variation source TSV',(Path(folder)/MARKED_TSV).read_bytes(),MARKED_TSV,key=prefix+'tsv')
