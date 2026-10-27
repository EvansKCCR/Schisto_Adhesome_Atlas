"""Authoritative copy-profile statistics, separate from Atlas candidate annotations."""
from pathlib import Path
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

SPECIES=['S. mansoni','S. japonicum','S. haematobium','S. bovis','S. curassoni',
         'S. intercalatum','S. rodhaini']
SPECIES_FULL={name:'Schistosoma '+name.split('. ')[1] for name in SPECIES}
FILES={'all':'orthogroups_all_exact_copyprofiles.tsv','1:1':'orthogroups_1to1_supported.tsv',
       '2:2':'orthogroups_2to2_supported.tsv'}
NUMERIC=['Supported copies','Total candidates','Species with supported identity','Specific supported',
         'Broad supported','Supported grade A','Supported grade B']
SUMMARY=['Orthogroup','Copy profile','Supported family identity','Supported copies','Total candidates',
         'Species with supported identity','Classification','Specific supported','Broad supported',
         'Supported grade A','Supported grade B']
CLASSIFICATIONS=['Complete supported identity','Partial supported identity','No supported identity']
COLORS=dict(zip(CLASSIFICATIONS,['#08743f','#c58b00','#70817a']))
GREEN='#08743f';GOLD='#e6b62c';GRAY='#cbd7cf'


def signature(folder):
    folder=Path(folder)
    return tuple((name,(folder/name).stat().st_mtime_ns,(folder/name).stat().st_size)
                 for name in FILES.values() if (folder/name).is_file())


def _read(path):
    frame=pd.read_csv(path,sep='\t',dtype=str,keep_default_na=False)
    columns=SUMMARY+[species+suffix for suffix in [' copies',' supported'] for species in SPECIES]
    missing=set(columns)-set(frame)
    if missing:raise ValueError(path.name+' is missing columns: '+', '.join(sorted(missing)))
    if frame.Orthogroup.eq('').any():raise ValueError(path.name+' contains an empty Orthogroup ID.')
    numbers=NUMERIC+[s+suffix for suffix in [' copies',' supported'] for s in SPECIES]
    for column in numbers:
        values=pd.to_numeric(frame[column],errors='coerce')
        if values.isna().any() or (values<0).any() or values.mod(1).ne(0).any():
            raise ValueError(path.name+' requires non-negative integer values in '+column)
        frame[column]=values.astype('int64')
    original=len(frame);frame=frame.drop_duplicates().reset_index(drop=True)
    if frame.Orthogroup.duplicated().any():
        ids=frame.loc[frame.Orthogroup.duplicated(keep=False),'Orthogroup'].unique()
        raise ValueError(path.name+' contains conflicting rows for '+', '.join(ids))
    return frame,original-len(frame)


def load_statistics(folder):
    """The complete file owns summary values; subsets contribute membership only."""
    folder=Path(folder);sources={};checks=[]
    for key,name in FILES.items():
        sources[key],duplicates=_read(folder/name)
        if duplicates:checks.append({'Source':name,'Orthogroup':'','Issue':f'{duplicates} identical duplicate rows counted once'})
    master=sources['all'].copy();index=master.set_index('Orthogroup')
    for profile in ['1:1','2:2']:
        focused=sources[profile]
        for _,row in focused.iterrows():
            group=row.Orthogroup
            if group not in index.index:
                checks.append({'Source':FILES[profile],'Orthogroup':group,'Issue':'Absent from complete dataset; not added to totals'})
            else:
                # Compare shared source fields by name, including all seven species columns.
                base=index.loc[group]
                differing=[column for column in base.index if column in row.index and row[column]!=base[column]]
                if differing:checks.append({'Source':FILES[profile],'Orthogroup':group,
                    'Issue':'Differs from complete dataset in '+', '.join(differing)+'; complete values retained'})
            if row['Copy profile']!=profile or row['Supported copies']==0:
                checks.append({'Source':FILES[profile],'Orthogroup':group,'Issue':'Focused subset profile/support differs from its file label'})
        master['In supported '+profile+' subset']=master.Orthogroup.isin(focused.Orthogroup)
    copies=master[[s+' copies' for s in SPECIES]]
    supported=master[[s+' supported' for s in SPECIES]]
    rules={
        'Species copy sum differs from Total candidates':copies.sum(axis=1).ne(master['Total candidates']),
        'Species supported sum differs from Supported copies':supported.sum(axis=1).ne(master['Supported copies']),
        'Grade A+B differs from Supported copies':master['Supported grade A'].add(master['Supported grade B']).ne(master['Supported copies']),
        'Specific+broad differs from Supported copies':master['Specific supported'].add(master['Broad supported']).ne(master['Supported copies']),
        'Supported species count differs from species columns':supported.gt(0).sum(axis=1).ne(master['Species with supported identity']),
        'Supported copies exceed total candidates':master['Supported copies'].gt(master['Total candidates']),
        'Species supported copies exceed total copies':pd.DataFrame({s:master[s+' supported'].gt(master[s+' copies']) for s in SPECIES}).any(axis=1)}
    for issue,mask in rules.items():
        checks.extend({'Source':FILES['all'],'Orthogroup':g,'Issue':issue} for g in master.loc[mask,'Orthogroup'])
    return master,sources,pd.DataFrame(checks,columns=['Source','Orthogroup','Issue'])


def summary(frame):
    result={'Orthogroups':len(frame),'Supported 1:1':int(frame['In supported 1:1 subset'].sum()),
        'Supported 2:2':int(frame['In supported 2:2 subset'].sum())}
    result.update({column:int(frame[column].sum()) for column in NUMERIC if column!='Species with supported identity'})
    result.update({label:int(frame.Classification.eq(label).sum()) for label in CLASSIFICATIONS})
    result['Represented species']=int(sum(frame[s+' copies'].sum()>0 for s in SPECIES))
    return result


def filter_groups(frame,*,species=(),families=(),profiles=(),classifications=(),query='',
                  subset='All exact profiles',species_basis='Total copies',match='Any selected species',
                  support='All support'):
    chosen=frame.copy()
    if subset in ['Supported 1:1 subset','Supported 2:2 subset']:
        chosen=chosen[chosen['In '+subset.lower()]]
    for column,values in [('Supported family identity',families),('Copy profile',profiles),('Classification',classifications)]:
        if values:chosen=chosen[chosen[column].isin(values)]
    if species:
        suffix=' supported' if species_basis=='Supported copies' else ' copies'
        present=chosen[[s+suffix for s in species]].gt(0)
        chosen=chosen[present.all(axis=1) if match=='Every selected species' else present.any(axis=1)]
    support_column={'Specific family support':'Specific supported','Broad family support':'Broad supported',
                    'Grade A support':'Supported grade A','Grade B support':'Supported grade B'}.get(support)
    if support_column:chosen=chosen[chosen[support_column].gt(0)]
    if query:
        chosen=chosen[chosen[SUMMARY].astype(str).apply(lambda col:col.str.contains(query,case=False,regex=False)).any(axis=1)]
    return chosen.reset_index(drop=True)


def species_table(frame):
    return pd.DataFrame([{'Species':s,'Total copies':int(frame[s+' copies'].sum()),
        'Supported copies':int(frame[s+' supported'].sum()),
        'Orthogroups with copies':int(frame[s+' copies'].gt(0).sum()),
        'Orthogroups with supported identity':int(frame[s+' supported'].gt(0).sum())} for s in SPECIES])


def species_detail(row):
    return pd.DataFrame([{'Species':s,'Total copies':int(row[s+' copies']),
        'Supported copies':int(row[s+' supported']),
        'Supported identity':'Present' if row[s+' supported']>0 else 'None reported'} for s in SPECIES])


def related_candidates(candidates,group,app_url=''):
    from candidate_profiles import atlas_url
    records=candidates[candidates.orthogroup.eq(group)].copy()
    records['Protein dossier']=[atlas_url(app_url,'Protein dossier',protein) for protein in records.sequence_id]
    return records


def chart(frame,kind,*,heatmap_measure='Total copies',limit=40):
    """Use source columns for plots; selectable points carry exact filters or group IDs."""
    event=''
    if kind=='Copy profiles':
        counts=frame.groupby('Copy profile',sort=False).agg(Orthogroups=('Orthogroup','size'),
            supported=('Supported copies','sum'),total=('Total candidates','sum')).reset_index()
        fig=px.bar(counts,x='Copy profile',y='Orthogroups',text='Orthogroups',custom_data=['Copy profile'],
            hover_data={'supported':True,'total':True},color_discrete_sequence=[GREEN],
            labels={'supported':'Supported copies','total':'Total candidates'},title='Observed copy profiles')
        event='profiles'
    elif kind=='Family composition':
        supported=frame[frame['Supported family identity'].ne('')]
        counts=supported.groupby('Supported family identity').agg(Orthogroups=('Orthogroup','size'),
            supported=('Supported copies','sum')).reset_index().sort_values('Orthogroups')
        fig=px.bar(counts,x='Orthogroups',y='Supported family identity',orientation='h',text='Orthogroups',
            custom_data=['Supported family identity'],hover_data={'supported':True},color_discrete_sequence=[GREEN],
            labels={'supported':'Supported copies'},title='Orthogroups by reported supported family identity',
            height=max(420,len(counts)*28+100))
        event='families'
    elif kind=='Classification':
        counts=frame.groupby('Classification',sort=False).size().reset_index(name='Orthogroups')
        fig=px.bar(counts,x='Classification',y='Orthogroups',color='Classification',text='Orthogroups',
            color_discrete_map=COLORS,custom_data=['Classification'],title='Supported family identity classification')
        event='classifications'
    elif kind=='Specific and broad support':
        counts=pd.DataFrame({'Support':['Specific family support','Broad family support'],
            'Supported copies':[frame['Specific supported'].sum(),frame['Broad supported'].sum()]})
        fig=px.bar(counts,x='Support',y='Supported copies',color='Support',text='Supported copies',
            custom_data=['Support'],color_discrete_sequence=[GREEN,GOLD],title='Specific and broad family support')
        event='support'
    elif kind=='Species representation':
        counts=species_table(frame).melt(id_vars='Species',value_vars=['Total copies','Supported copies'],
            var_name='Measure',value_name='Copies')
        fig=px.bar(counts,x='Species',y='Copies',color='Measure',barmode='group',
            custom_data=['Species','Measure'],color_discrete_map={'Total copies':GRAY,'Supported copies':GREEN},
            title='Candidate copies across seven species')
        event='species'
    else:
        groups=frame.sort_values(['Supported copies','Orthogroup'],ascending=[False,True])
        if limit:groups=groups.head(limit)
        x=[];y=[];custom=[];z=[]
        for _,row in groups.iterrows():
            line=[]
            for s in SPECIES:
                total=int(row[s+' copies']);supported=int(row[s+' supported'])
                line.append(supported if heatmap_measure=='Supported copies' else total)
                x.append(s);y.append(row.Orthogroup)
                custom.append([row.Orthogroup,s,total,supported,row['Supported family identity'],row.Classification])
            z.append(line)
        maximum=max((value for row in z for value in row),default=0) or 1
        fig=go.Figure(go.Heatmap(x=SPECIES,y=groups.Orthogroup.tolist(),z=z,zmin=0,zmax=maximum,
            xgap=2,ygap=2,texttemplate='%{z}',textfont=dict(color='#000000',size=14),
            colorscale=[[0,'#f4f7f5'],[.45,'#f0d36d'],[1,GREEN]],
            colorbar=dict(title=heatmap_measure,dtick=max(1,math.ceil(maximum/8)),tickformat='d'),
            hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=20,color='#000000',opacity=.01),
            customdata=custom,showlegend=False,
            hovertemplate='%{customdata[0]} · %{customdata[1]}<br>Total copies: %{customdata[2]}'
            '<br>Supported copies: %{customdata[3]}<br>Family: %{customdata[4]}'
            '<br>%{customdata[5]}<extra></extra>'))
        fig.update_layout(title=heatmap_measure+' by orthogroup and species',height=max(460,len(groups)*24+160))
        fig.update_yaxes(autorange='reversed',title='Orthogroup')
        event='focus'
    fig.update_layout(clickmode='event+select',margin=dict(l=20,r=25,t=80,b=75),legend_title_text='',
        uirevision='orthogroup-statistics-'+kind)
    return fig,event
