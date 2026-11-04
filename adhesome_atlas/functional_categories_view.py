"""Supported functional repertoire and independent localization evidence."""
import pandas as pd
import plotly.express as px
import streamlit as st

from figure_exports import plotly_chart
from functional_categories import CATEGORIES,COLORS,SUPPORT_STATES,summary_tables


def functional_category_panel(candidates):
    st.subheader('Supported families by functional category')
    st.write('Functional categories follow supported family identities. Localization and membrane-topology predictions are evaluated separately. Counts use unique protein identifiers within the active sidebar filters.')
    modules,total,families,species=summary_tables(candidates)
    counts=total.iloc[0]
    boxes=st.columns(4)
    for box,label,value in zip(boxes,['Unique proteins','Supported proteins','Supported family labels','Unassigned / unresolved'],
        [counts['Unique proteins'],counts['Specific supported']+counts['Broad supported'],counts['Supported family labels'],
         modules.loc[modules.Category.eq(CATEGORIES[-1]),'Unique proteins'].sum()]):
        box.metric(label,f'{int(value):,}')
    st.caption('Supported = specific supported + broad supported in family_support_level. A/B grades are retained independently. Provisional, ambiguous and unresolved family identities stay in the unassigned category. Orthogroup counts can overlap categories and must not be summed.')
    labels=['Specific supported','Broad supported','Provisional','Ambiguous','Unresolved']
    display=['Category','Unique proteins']+labels+['Supported family labels','Unique orthogroups']
    tabs=st.tabs(['Functional repertoire','Family breakdown','Localization evidence'])
    with tabs[0]:
        data=modules[['Category']+labels].melt(id_vars='Category',value_vars=labels,var_name='Family support',value_name='Unique proteins')
        plotly_chart(px.bar(data,y='Category',x='Unique proteins',color='Family support',orientation='h',
            category_orders={'Category':CATEGORIES,'Family support':labels},
            color_discrete_map=dict(zip(labels,['#24734c','#73b69a','#d8b04c','#c47562','#cbd3d0'])),
            height=440,hover_data={'Unique proteins':':,'},title='Family identity support by functional category'),width='stretch')
        st.dataframe(pd.concat([modules,total],ignore_index=True)[display],hide_index=True,width='stretch')
        if len(species):
            matrix=species.pivot(index='module',columns='species',values='Unique proteins').reindex(CATEGORIES).fillna(0).astype(int)
            plotly_chart(px.imshow(matrix,aspect='auto',color_continuous_scale='Greens',text_auto=True,
                height=430,labels={'x':'Species','y':'Functional category','color':'Proteins'},
                title='Functional repertoire across species'),width='stretch')
    with tabs[1]:
        selected=st.multiselect('Functional categories',CATEGORIES,default=CATEGORIES[:-1],key='functional_category_filter')
        subset=families[families.Category.isin(selected)] if len(families) else families
        st.dataframe(subset[[c for c in ['Category','Family']+display[1:] if c in subset]],hide_index=True,width='stretch')
        if len(subset):
            counts=subset.assign(Supported=subset['Specific supported']+subset['Broad supported'])
            counts=counts[counts.Supported.gt(0)]
            if len(counts):plotly_chart(px.bar(counts,y='Family',x='Supported',color='Category',orientation='h',
                color_discrete_map=COLORS,height=max(420,len(counts)*23),hover_data=['Specific supported','Broad supported'],
                title='Supported protein families'),width='stretch')
    with tabs[2]:
        st.write('Single-location DeepLoc means one recorded location label; it does not express a numerical confidence probability. Membrane+TM requires a Cell membrane label and a predicted TM segment. Strict membrane+TM requires that sole location. Strict extracellular+SP requires the sole Extracellular label, both SignalP and DeepTMHMM signal peptides, and no TM segment.')
        st.dataframe(pd.concat([modules,total],ignore_index=True)[['Category','Unique proteins']+list(modules.columns[9:])],hide_index=True,width='stretch')
        st.caption('Membrane-actin clutch is a functional position: peripheral membrane adaptors can participate without a TM segment. Functional placement preserves every original localization prediction in candidate profiles.')
    for label,frame,filename in [('Download category summary',pd.concat([modules,total],ignore_index=True),'functional_category_summary.csv'),
        ('Download family breakdown',families,'functional_family_breakdown.csv'),('Download species summary',species,'functional_species_summary.csv')]:
        st.download_button(label,frame.to_csv(index=False).encode('utf-8'),filename,'text/csv',key=filename)
