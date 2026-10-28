"""Interactive statistics and exact-ID exploration inside the Atlas Orthology page."""
from pathlib import Path

import pandas as pd
import streamlit as st

from data import ROOT
from figure_exports import plotly_chart
from orthogroup_statistics import (FILES,SPECIES,SUMMARY,CLASSIFICATIONS,signature,load_statistics,
    summary,filter_groups,species_table,species_detail,related_candidates,chart)

PREFIX='og_stats_'
VISUALS=['Copy profiles','Family composition','Species heatmap','Classification',
         'Specific and broad support','Species representation']


@st.cache_data(show_spinner='Reading orthogroup copy-profile statistics…',max_entries=4)
def cached_statistics(folder,source_signature):
    return load_statistics(folder)


def reset_filters():
    st.session_state[PREFIX+'selection_revision']=st.session_state.get(PREFIX+'selection_revision',0)+1
    for name in ['species','families','profiles','classifications']:st.session_state[PREFIX+name]=[]
    for name,value in [('query',''),('subset','All exact profiles'),('support','All support'),
            ('species_basis','Total copies'),('match','Any selected species')]:
        st.session_state[PREFIX+name]=value


def selection_patch(kind,point):
    """The same exact source value drives chart filtering and table/group selection."""
    custom=point.get('customdata',[])
    if not isinstance(custom,(list,tuple)):custom=[custom]
    if not custom:return {}
    value=custom[0]
    if kind in ['profiles','families','classifications']:return {PREFIX+kind:[value]}
    if kind=='support':return {PREFIX+'support':value}
    if kind=='species':return {PREFIX+'species':[value],PREFIX+'species_basis':custom[1] if len(custom)>1 else 'Total copies'}
    if kind=='focus':return {PREFIX+'focus':value}
    return {}


def chart_selection(key,kind):
    current=PREFIX+'chart_'+st.session_state.get(PREFIX+'visual',VISUALS[0])+'_'+str(st.session_state.get(PREFIX+'selection_revision',0))
    if key!=current:return  # Ignore selection events from a replaced/reset chart.
    points=st.session_state.get(key,{}).get('selection',{}).get('points',[])
    if points:
        for name,value in selection_patch(kind,points[-1]).items():st.session_state[name]=value


def table_selection(key,ids):
    rows=st.session_state.get(key,{}).get('selection',{}).get('rows',[])
    if rows and 0<=rows[-1]<len(ids):st.session_state[PREFIX+'focus']=ids[rows[-1]]


def _valid_choices(name,options):
    key=PREFIX+name
    if key in st.session_state:st.session_state[key]=[v for v in st.session_state[key] if v in options]


def _metrics(frame):
    counts=summary(frame)
    metrics=[('Orthogroups',f'{counts["Orthogroups"]:,}','Complete-file rows in the active selection'),
        ('Supported 1:1',f'{counts["Supported 1:1"]:,}','Membership in the supported 1:1 subset, counted once'),
        ('Supported 2:2',f'{counts["Supported 2:2"]:,}','Membership in the supported 2:2 subset, counted once'),
        ('Supported / total copies',f'{counts["Supported copies"]:,} / {counts["Total candidates"]:,}','Reported TSV counts across all seven species'),
        ('Complete identity',f'{counts[CLASSIFICATIONS[0]]:,}',CLASSIFICATIONS[0]),
        ('Partial identity',f'{counts[CLASSIFICATIONS[1]]:,}',CLASSIFICATIONS[1]),
        ('No supported identity',f'{counts[CLASSIFICATIONS[2]]:,}',CLASSIFICATIONS[2]),
        ('Grade A / B support',f'{counts["Supported grade A"]:,} / {counts["Supported grade B"]:,}','Reported supported assignment counts')]
    st.markdown('<style>.st-key-orthogroup_summary [data-testid="stMetricValue"]{font-size:clamp(16px,1.55vw,30px)!important}'
        '.st-key-orthogroup_summary [data-testid="stMetricValue"] *{font-size:inherit!important}'
        '.st-key-orthogroup_summary [data-testid="stMetricLabel"] p{white-space:normal;line-height:1.3}'
        '[data-testid="stMain"]:has(.st-key-orthogroup_summary) [data-testid="stCaptionContainer"] p{color:#465d52!important}</style>',unsafe_allow_html=True)
    with st.container(key='orthogroup_summary'):
        for offset in [0,4]:
            for column,(label,value,help_text) in zip(st.columns(4),metrics[offset:offset+4]):
                column.metric(label,value,help=help_text)
    st.caption(f'{counts["Represented species"]} / {len(SPECIES)} species represented. Species filters select orthogroups; reported summary counts still describe each whole seven-species group.')


def _detail(group,candidates,app_url,tree_ids):
    st.subheader(group.Orthogroup)
    st.write('**'+group.Classification+'**')
    st.write('Supported family identity: **'+(group['Supported family identity'] or 'None reported')+'**')
    st.caption(f'Copy profile {group["Copy profile"]} · supported {group["Supported copies"]} / total {group["Total candidates"]} · '
        f'{group["Species with supported identity"]} species with supported identity')
    st.dataframe(species_detail(group),hide_index=True,width='stretch',height=294)
    st.caption(f'Specific support {group["Specific supported"]} · broad support {group["Broad supported"]} · '
               f'grade A {group["Supported grade A"]} · grade B {group["Supported grade B"]}')
    from research_priorities import target_url
    if group.Orthogroup in tree_ids:
        st.link_button('Explore this orthogroup’s phylogeny ↗',target_url(app_url,'Phylogeny',orthogroup=group.Orthogroup))
    else:st.caption('No matching gene tree is present in the current phylogeny library. To be updated when additional trees are available.')
    st.link_button('Open candidate and reference orthologues ↗',target_url(app_url,'Orthology',
        orthogroup=group.Orthogroup,workspace='references'))


def statistics_panel(candidates,folder=None):
    folder=Path(folder) if folder is not None else ROOT/'orthology'
    from orthogroup_variation import WORKBOOK,REPORT_VARIATION,REPORT_EXACT,variation_panel
    st.subheader('Orthogroup Statistics & Explorer')
    options=([REPORT_VARIATION] if (folder/WORKBOOK).exists() else [])+[REPORT_EXACT]
    if st.session_state.get('og_statistics_report') not in options:st.session_state.pop('og_statistics_report',None)
    report=st.selectbox('Orthogroup report',options,key='og_statistics_report')
    if report==REPORT_VARIATION:
        variation_panel(candidates,folder);return
    try:master,sources,checks=cached_statistics(folder,signature(folder))
    except (OSError,ValueError,pd.errors.ParserError) as error:
        st.info('Orthogroup statistics are awaiting complete, readable TSV files: '+str(error));return
    st.caption('Exact copy-profile catalogue. Summary fields follow the complete TSV; the supported 1:1 and 2:2 files define focused subsets. Copy-profile similarity alone does not establish orthology or paralogy.')
    st.button('Reset orthogroup filters',on_click=reset_filters,key=PREFIX+'reset')
    choices={'species':SPECIES,'families':sorted(set(master['Supported family identity'])-{''}),
             'profiles':sorted(master['Copy profile'].unique()),'classifications':list(master.Classification.unique())}
    for name,options in choices.items():_valid_choices(name,options)
    a,b=st.columns(2)
    species=a.multiselect('Species representation',SPECIES,key=PREFIX+'species')
    families=b.multiselect('Supported protein family',choices['families'],key=PREFIX+'families')
    a,b,c=st.columns(3)
    profiles=a.multiselect('Copy profile',choices['profiles'],key=PREFIX+'profiles')
    classifications=b.multiselect('Family identity classification',choices['classifications'],key=PREFIX+'classifications')
    subset=c.selectbox('Copy-profile dataset',['All exact profiles','Supported 1:1 subset','Supported 2:2 subset'],key=PREFIX+'subset')
    with st.expander('Species matching and support filters'):
        a,b,c=st.columns(3)
        basis=a.selectbox('Species filter counts',['Total copies','Supported copies'],key=PREFIX+'species_basis')
        match=b.selectbox('Species matching',['Any selected species','Every selected species'],key=PREFIX+'match')
        support=c.selectbox('Support basis',['All support','Specific family support','Broad family support','Grade A support','Grade B support'],key=PREFIX+'support')
    query=st.text_input('Find an orthogroup, copy profile or reported family',key=PREFIX+'query')
    filtered=filter_groups(master,species=species,families=families,profiles=profiles,classifications=classifications,
        query=query,subset=subset,species_basis=basis,match=match,support=support)
    _metrics(filtered)
    if filtered.empty:
        st.info('No orthogroups match these filters. Reset the filters to return to the complete dataset.')
    else:
        kind=st.selectbox('Orthogroup visualization',VISUALS,key=PREFIX+'visual')
        measure='Total copies';limit=40
        if kind=='Species heatmap':
            a,b=st.columns(2)
            measure=a.selectbox('Heatmap measure',['Total copies','Supported copies'],key=PREFIX+'heatmap_measure')
            options=[20,40,80,'All filtered orthogroups']
            if st.session_state.get(PREFIX+'heatmap_rows') not in options:st.session_state.pop(PREFIX+'heatmap_rows',None)
            size=b.selectbox('Maximum heatmap rows',options,index=1,key=PREFIX+'heatmap_rows')
            limit=0 if isinstance(size,str) else size
            st.caption(f'Heatmap displays {min(limit or len(filtered),len(filtered))} of {len(filtered)} filtered groups, ordered by reported supported copies. The explorer table retains every filtered group.')
        fig,event_kind=chart(filtered,kind,heatmap_measure=measure,limit=limit)
        if kind=='Family composition':st.caption('Counts use the reported supported-family identity. Groups with no reported family identity are omitted from this chart.')
        key=PREFIX+'chart_'+kind+'_'+str(st.session_state.get(PREFIX+'selection_revision',0))
        plotly_chart(fig,width='stretch',key=key,on_select=lambda chart_key=key,kind=event_kind:chart_selection(chart_key,kind),selection_mode='points')
        st.caption('Click a bar to filter the explorer. Click a heatmap cell to inspect that orthogroup. Reset orthogroup filters clears chart-driven filters; figure downloads use the Atlas PNG/SVG settings.')
        if kind=='Species representation':st.dataframe(species_table(filtered),hide_index=True,width='stretch')
        st.subheader('Orthogroup explorer')
        st.caption(f'{len(filtered):,} of {len(master):,} groups. Click a table row to inspect it; columns can be sorted from their headers.')
        ids=filtered.Orthogroup.tolist()
        if st.session_state.get(PREFIX+'focus') not in ids:st.session_state[PREFIX+'focus']=ids[0]
        table_column,detail_column=st.columns([1.5,1])
        with table_column:
            table_key=PREFIX+'table'
            st.dataframe(filtered[SUMMARY],width='stretch',hide_index=True,height=440,key=table_key,
                on_select=lambda selection_key=table_key,group_ids=ids:table_selection(selection_key,group_ids),selection_mode='single-row',
                column_config={'Supported copies':st.column_config.NumberColumn(format='%d'),
                    'Total candidates':st.column_config.NumberColumn(format='%d'),
                    'Species with supported identity':st.column_config.NumberColumn(format='%d')})
        app_url=st.context.url or ''
        from phylogeny_view import discover_trees
        tree_ids={path.name for path in discover_trees()[0]}
        with detail_column:
            group_id=st.selectbox('Inspect orthogroup',ids,key=PREFIX+'focus')
            group=filtered.set_index('Orthogroup',drop=False).loc[group_id]
            _detail(group,candidates,app_url,tree_ids)
        st.subheader('Linked candidate dossiers')
        linked=related_candidates(candidates,group_id,app_url)
        st.caption(f'{len(linked):,} Atlas records / {linked.sequence_id.nunique():,} unique proteins linked by the exact orthogroup ID. '
                   'Reported TSV totals are retained independently of the current Atlas candidate inventory.')
        if linked.empty:st.info('No candidate protein identifiers are linked to this orthogroup in the current Atlas library.')
        else:
            columns=[col for col in ['sequence_id','species','family','grade','audit_classification','candidate_annotation',
                'architecture','Protein dossier'] if col in linked]
            st.dataframe(linked[columns],hide_index=True,width='stretch',height=min(500,len(linked)*35+40),
                column_config={'Protein dossier':st.column_config.LinkColumn('Protein dossier',display_text='Open dossier ↗')})
            st.download_button('Download linked candidate records',linked.to_csv(index=False),group_id+'_atlas_candidates.csv',key=PREFIX+'candidate_download')
        st.download_button('Download selected orthogroup source record',
            master[master.Orthogroup.eq(group_id)].drop(columns=[c for c in master if c.startswith('In supported ')]).to_csv(sep='\t',index=False),
            group_id+'_copyprofile.tsv','text/tab-separated-values',key=PREFIX+'group_download')
    st.download_button('Download filtered orthogroup statistics',filtered.to_csv(sep='\t',index=False),
        'orthogroup_statistics_filtered.tsv','text/tab-separated-values',key=PREFIX+'filtered_download')
    with st.expander('Source datasets and count validation'):
        st.dataframe(pd.DataFrame([{'Dataset':FILES[key],'Unique orthogroups':len(source)} for key,source in sources.items()]),
            hide_index=True,width='stretch')
        st.caption('The complete-file scope is exact copy profiles, not the entire Atlas inventory. Subset memberships do not add rows to its totals. '
            'Family identity, supported copies, specific/broad support and A/B counts retain the TSV definitions; they are not inferred from copy numbers.')
        if checks.empty:st.success('All seven species columns and reported count sums agree. Both supported subsets match the complete dataset.')
        else:
            st.info('Some source fields differ. The complete-file values remain authoritative; details are listed below.')
            st.dataframe(checks,width='stretch',hide_index=True)
        for key,name in FILES.items():
            st.download_button('Download '+name,(folder/name).read_bytes(),name,'text/tab-separated-values',key=PREFIX+'source_'+key)
