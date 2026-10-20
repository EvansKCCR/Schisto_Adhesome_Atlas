import streamlit as st

def apply_style():
    st.set_page_config(page_title='Schisto-Adhesome Atlas | Integrin–adhesome', page_icon='🧬', layout='wide')
    st.markdown("""<style>
    .block-container{padding-top:2rem;max-width:1500px;padding-bottom:3rem}
    [data-testid="stAppViewContainer"]{background:#fff}
    [data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] li{font-size:1.05rem;line-height:1.65;color:#171717}
    h1,h2,h3{letter-spacing:-.025em;color:#111;font-weight:750}
    h2{font-size:1.85rem}h3{font-size:1.5rem}
    .hero{background:#064c2c;color:white;padding:38px 42px;border-radius:18px;margin-bottom:24px;border-bottom:6px solid #f4cf24}
    .hero h1{color:#fff;font-size:clamp(2.2rem,3.6vw,3.3rem);line-height:1.15;margin:12px 0 18px;letter-spacing:-.035em;font-weight:800}
    [data-testid="stAppViewContainer"] .hero p{color:#fff;max-width:850px;font-size:1.15rem;line-height:1.65;margin-bottom:0}
    .eyebrow{font-size:.85rem;letter-spacing:2px;text-transform:uppercase;color:#ffe34d;font-weight:750}
    [data-testid="stMetric"]{background:#fff;border:1px solid #b6c5ba;border-top:4px solid #08743f;border-radius:12px;padding:20px}
    [data-testid="stMetricValue"]{color:#064c2c;font-size:2.3rem;font-weight:750}
    [data-testid="stMetricLabel"] p{color:#111!important;font-weight:650}
    [data-testid="stSidebar"]{background:#f4f6f2;border-right:2px solid #c7d1c6}
    [data-testid="stSidebar"] h2{font-size:1.4rem;line-height:1.35;color:#064c2c}
    [data-testid="stSidebar"] [role="radiogroup"]{gap:5px}
    [data-testid="stSidebar"] [role="radiogroup"] label{border-radius:8px;padding:7px 10px}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#e2ebdf}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#ffe34d;box-shadow:inset 4px 0 #064c2c}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#111;font-weight:750}
    [data-testid="stWidgetLabel"] p{color:#171717!important;font-size:1rem!important;font-weight:650}
    [data-testid="stButton"] button,[data-testid="stDownloadButton"] button{background:#fff;color:#064c2c;border:1.5px solid #08743f;border-radius:8px;font-weight:650}
    [data-testid="stButton"] button p,[data-testid="stDownloadButton"] button p{color:inherit}
    [data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{background:#ffe34d;color:#111;border-color:#111}
    button:focus-visible,a:focus-visible{outline:3px solid #b91c1c!important;outline-offset:3px}
    [data-testid="stDataFrame"],[data-testid="stPlotlyChart"]{border:1px solid #bac8bc;border-radius:12px;background:#fff;padding:6px}
    [data-testid="stExpander"]{border-radius:10px;background:#fff;border-color:#bac8bc}
    [data-testid="stTabs"] [role="tablist"]{gap:12px;border-bottom:2px solid #ccd4cb}
    [data-testid="stTabs"] [role="tab"]{padding:10px 12px;border-radius:8px 8px 0 0;color:#111}
    [data-testid="stTabs"] [aria-selected="true"]{background:#ffe34d;color:#111;font-weight:750}
    [data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:#b91c1c}
    [data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:#333!important;font-size:.95rem!important;line-height:1.6}
    [data-testid="stMarkdownContainer"] a{color:#075d32;text-decoration:underline;text-underline-offset:3px;font-weight:600}
    [data-testid="stMarkdownContainer"] a:hover{color:#b91c1c}
    @media(max-width:640px){.hero{padding:26px 22px}.eyebrow{letter-spacing:1px}.block-container{padding-top:1.2rem}[data-testid="stMetric"]{padding:14px}}
    [data-testid="stMainBlockContainer"]{min-width:0} [data-testid="stVerticalBlock"]{min-width:0} iframe{max-width:100%}
    [data-testid="stHeading"]{scroll-margin-top:80px}
    </style>""", unsafe_allow_html=True)
    
