"""Render the functional dashboard against the validated full candidate fixture."""
from bootstrap import ATLAS_ROOT
from streamlit.testing.v1 import AppTest

SOURCE='''
import json,re
from pathlib import Path
import pandas as pd
import streamlit as st
from functional_categories_view import functional_category_panel
st.set_page_config(layout='wide')
st.header('Components')
st.selectbox('Component section',['Supported families by functional category'])
html=Path('adhesome_network/Schistosome_adhesome_rebuilt.html').read_text(encoding='utf-8')
model=json.JSONDecoder().raw_decode(html.split('const atlasProfiles=',1)[1])[0]
functional_category_panel(pd.DataFrame(model['candidates'],columns=model['fields']))
'''


if __name__=='__main__':
    from pathlib import Path
    Path('.ui_review/functional_dashboard_preview.py').write_text(SOURCE,encoding='utf-8')
    app=AppTest.from_string(SOURCE,default_timeout=120).run()
    for error in app.exception:print(error.message,error.stack_trace,flush=True)
    assert not app.exception
    assert {metric.label:metric.value for metric in app.metric}=={
        'Unique proteins':'4,359','Supported proteins':'2,460','Supported family labels':'88','Unassigned / unresolved':'3,258'}
    assert len(app.dataframe)==3 and len(app.get('plotly_chart'))==3
    print('PASS all dashboard metrics, category/family/localization tables and three interactive charts render without exceptions.',flush=True)
