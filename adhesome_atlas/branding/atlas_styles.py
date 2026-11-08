"""Responsive scientific workspace, typography and reusable interface surfaces."""
import streamlit as st
from urllib.parse import quote
from design_system import TOKENS_CSS

APP_CSS = '''
html{scroll-behavior:smooth}
[data-testid="stAppViewContainer"]{background:var(--atlas-paper);font-family:var(--atlas-font)}
[data-testid="stMainBlockContainer"],.block-container{max-width:none;padding:3.7rem 2rem 3rem;min-width:0}
[data-testid="stMain"] [data-testid="stVerticalBlock"]{gap:1rem;min-width:0}
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] li{color:var(--atlas-text);font-size:1rem;line-height:1.6}
h1,h2,h3{font-family:var(--atlas-font);letter-spacing:-.035em;color:var(--atlas-ink);font-weight:750;line-height:1.2}
h1{font-size:2.6rem}h2{font-size:1.8rem}h3{font-size:1.3rem}
[data-testid="stHeader"]{background:#fff;border-bottom:1px solid var(--atlas-line)}
[data-testid="stHeading"]{scroll-margin-top:65px}
[data-testid="stMetric"]{background:var(--atlas-surface);border:1px solid var(--atlas-line);border-top:2px solid var(--atlas-primary);border-radius:6px;padding:17px 20px;box-shadow:none}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;letter-spacing:-.05em;color:var(--atlas-deep);font-size:2.45rem;font-weight:750}
[data-testid="stMetricLabel"] p{color:var(--atlas-muted)!important;font-size:.9rem!important;font-weight:650}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--atlas-line)}
[data-testid="stSidebarContent"]{padding-top:.7rem}
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"]{opacity:1!important;visibility:visible!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.75rem}
.atlas-sidebar-brand{padding:4px 0 15px;border-bottom:3px solid transparent;border-image:var(--atlas-spectrum) 1;margin-bottom:3px;display:flex;align-items:center;gap:10px}
.atlas-sidebar-symbol{display:grid;place-items:center;width:42px;height:42px;flex-shrink:0;border-radius:50%;background:var(--atlas-deep);color:var(--atlas-cyan);font-size:22px;font-weight:700;box-shadow:0 0 0 3px var(--atlas-tint)}
.atlas-sidebar-brand strong{font-size:18px;line-height:1.15;color:var(--atlas-deep);letter-spacing:-.025em}
.atlas-sidebar-brand small{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--atlas-muted);margin-top:6px}
[data-testid="stSidebar"] [role="radiogroup"]{gap:2px}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:4px;padding:6px 8px;min-height:42px;border-bottom:2px solid transparent;transition:background .15s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:var(--atlas-tint)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--atlas-tint);border-bottom-color:var(--atlas-accent);box-shadow:none}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:var(--atlas-deep);font-weight:750}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:.94rem;line-height:1.35}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-size:.85rem!important;letter-spacing:.01em}
[data-testid="stWidgetLabel"] p{color:var(--atlas-ink)!important;font-size:.94rem!important;font-weight:650}
[data-baseweb="select"]>div,[data-baseweb="input"]>div{border-radius:5px!important;border-color:var(--atlas-field-line)!important;background:white;color:var(--atlas-ink)}
[data-baseweb="tag"]{background:var(--atlas-primary)!important;color:#fff!important}
[data-baseweb="tag"] span,[data-baseweb="tag"] svg{color:#fff!important}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button,[data-testid="stLinkButton"] a{border-radius:5px;min-height:40px;border:1px solid var(--atlas-primary);background:white;color:var(--atlas-deep);font-weight:650;box-shadow:none}
[data-testid="stButton"] button{background:var(--atlas-primary);color:#fff}
[data-testid="stButton"] button p,[data-testid="stDownloadButton"] button p{color:inherit}
[data-testid="stButton"] button:hover{background:var(--atlas-deep);color:#fff;border-color:var(--atlas-deep)}
[data-testid="stDownloadButton"] button:hover,[data-testid="stLinkButton"] a:hover{background:var(--atlas-tint);border-color:var(--atlas-accent);color:var(--atlas-deep)}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid var(--atlas-focus)!important;outline-offset:3px}
[data-testid="stDataFrame"],[data-testid="stPlotlyChart"]{border:1px solid var(--atlas-line);border-radius:6px;background:#fff;overflow:hidden}
[data-testid="stExpander"]{border-radius:5px;border:1px solid var(--atlas-line);background:#fff;overflow:hidden}
[data-testid="stExpander"] summary{padding:12px 15px}
[data-testid="stExpander"] summary p{font-size:.94rem;font-weight:650;color:var(--atlas-deep)}
[data-testid="stTabs"] [role="tablist"]{gap:8px;border-bottom:1px solid var(--atlas-line)}
[data-testid="stTabs"] [role="tab"]{padding:10px 14px;color:var(--atlas-text);font-weight:600}
[data-testid="stTabs"] [aria-selected="true"]{background:#fff;color:var(--atlas-deep);border-radius:0;font-weight:750}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:var(--atlas-accent)!important}
[data-testid="stAlert"]{border-radius:12px;font-size:.95rem}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--atlas-muted)!important;font-size:.88rem!important;line-height:1.55;opacity:1}
[data-testid="stMarkdownContainer"] a{color:var(--atlas-primary);text-underline-offset:3px}
[data-testid="stMarkdownContainer"] a:hover{color:var(--atlas-violet)}
iframe{max-width:100%;border-radius:6px}
.atlas-hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(245px,.34fr);gap:clamp(18px,3vw,36px);padding:clamp(16px,3vw,36px);border-radius:8px;background:var(--atlas-deep) linear-gradient(118deg,#10132f,#282052);color:#edf0ff;border-bottom:3px solid var(--atlas-accent)}
.atlas-hero h1{color:#fff;font-size:clamp(1.9rem,2.5vw,2.7rem);line-height:1.15;margin:0 0 18px;letter-spacing:-.025em;max-width:850px}
.atlas-hero h2{font-size:1rem;color:var(--atlas-cyan);margin:0 0 8px;letter-spacing:0;font-weight:700}
.atlas-hero h1,.atlas-hero h2{padding:0!important;font-family:var(--atlas-font)!important}
.atlas-section-heading h2{padding:0!important;font-family:var(--atlas-font)!important}
.atlas-sidebar-brand strong,.identity-title{font-family:var(--atlas-font)!important}
[data-testid="stAppViewContainer"] .atlas-hero p{color:inherit;font-size:1rem;line-height:1.6;margin:0;max-width:850px}
.atlas-hero-meta{display:flex;gap:14px;align-items:center;margin-top:18px;font-size:14px}
.atlas-hero-meta a{display:inline-flex;align-items:center;gap:16px;background:var(--atlas-cyan);color:var(--atlas-deep)!important;border-radius:5px;text-decoration:none;padding:10px 16px;font-weight:650}
.atlas-hero-meta a:hover{background:#b2f4ff}
.atlas-hero-meta a:focus-visible{outline-color:var(--atlas-cyan)!important}
.atlas-hero-stats{align-self:center;display:grid;grid-template-columns:1fr 1fr;gap:11px;position:relative}
.atlas-hero-stat{border:1px solid var(--atlas-line);border-top:3px solid var(--atlas-cyan);padding:16px 14px;background:#fff;border-radius:5px}
.atlas-hero-stat:nth-child(2){border-top-color:var(--atlas-violet)}
.atlas-hero-stat:nth-child(3){border-top-color:var(--atlas-accent)}
.atlas-hero-stat:nth-child(4){border-top-color:var(--atlas-amber)}
.atlas-hero-stat strong{display:block;font-size:clamp(1.8rem,2.3vw,2.65rem);font-weight:700;line-height:1.1;letter-spacing:-.03em;font-variant-numeric:tabular-nums;color:var(--atlas-deep)}
.atlas-hero-stat span{display:block;font-size:13px;color:var(--atlas-text);margin-top:8px;font-weight:600}
.atlas-section-heading{display:flex;justify-content:space-between;align-items:end;gap:12px;margin:4px 0}
.atlas-section-heading h2{font-size:1.5rem;margin:0 0 5px}
.atlas-section-heading p{font-size:.9rem!important;color:var(--atlas-muted)!important;margin:0}
.atlas-section-kicker{font-size:10px;text-transform:uppercase;letter-spacing:.16em;font-weight:750;color:var(--atlas-primary);margin-bottom:7px}
.atlas-live-label{font-size:11px;font-weight:650;color:var(--atlas-primary);border:1px solid var(--atlas-line);border-radius:30px;padding:6px 11px;background:var(--atlas-tint);white-space:nowrap}
.atlas-live-label:before{content:"";display:inline-block;height:6px;width:6px;background:var(--atlas-primary);border-radius:50%;margin-right:6px}
.research-intro{margin:16px 0 0;max-width:1150px}
.research-intro h2{font-size:1.85rem;margin:0 0 12px;padding:0!important}
.research-intro p{margin:0;font-size:.96rem!important}
.research-legend{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0}
.research-tag{display:inline-block;border:1px solid transparent;border-radius:30px;padding:5px 9px;font-size:12px;font-weight:700;line-height:1.4}
.research-tag.supported{background:var(--atlas-a-bg);color:var(--atlas-a);border-color:#c5dfd2}
.research-tag.provisional{background:var(--atlas-c-bg);color:var(--atlas-c);border-color:#e9cad6}
.research-tag.unassigned{background:#e9eef0;color:#394e58;border-color:#cbd5da}
.research-tag.published{background:#edf0fb;color:#334a87;border-color:#d2dbf1}
.research-tag.proposed{background:#fff5dc;color:#795718;border-color:#e9d69d}
.research-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:8px 0 14px;align-items:start}
.research-card{border:1px solid var(--atlas-line);border-top:3px solid var(--atlas-primary);border-radius:6px;padding:24px;background:#fff;box-shadow:none;min-width:0;transition:border-color .15s}
.research-card:hover{border-color:var(--atlas-primary)}
.research-card-kicker{font-size:10px;color:var(--atlas-muted);text-transform:uppercase;letter-spacing:.12em;font-weight:750;margin-bottom:9px}
.research-card h3{font-size:1.45rem;line-height:1.2;margin:0 0 18px;padding:0!important;min-height:3.5rem}
.research-metrics{display:flex;flex-wrap:wrap;gap:14px;border-bottom:1px solid var(--atlas-line);padding-bottom:16px;margin-bottom:14px}
.research-metric{flex:1;min-width:90px}
.research-metric strong{font-size:2.15rem;line-height:1;font-variant-numeric:tabular-nums;color:var(--atlas-deep);display:block;letter-spacing:-.04em}
.research-metric.provisional strong{color:var(--atlas-c)}
.research-metric.unassigned strong{color:#394e58}
.research-metric>span{font-size:13px;line-height:1.4;display:block;margin-top:6px;color:var(--atlas-muted);font-weight:650}
[data-testid="stAppViewContainer"] .research-objective{font-size:.92rem;font-weight:650;line-height:1.45;min-height:2.7rem;margin:0 0 12px}
.research-card-label{font-size:12px;color:#303833;text-transform:uppercase;letter-spacing:.035em;font-weight:700;margin:14px 0 7px}
.research-links{display:flex;flex-wrap:wrap;gap:6px 4px;align-items:center;font-size:12px;line-height:1.8;overflow-wrap:anywhere}
[data-testid="stMarkdownContainer"] .research-link{display:inline-block;border:1px solid var(--atlas-line);background:var(--atlas-tint);color:var(--atlas-primary);border-radius:6px;padding:3px 7px;font-size:12px;font-weight:650;text-decoration:none;overflow-wrap:anywhere;max-width:100%;line-height:1.6}
[data-testid="stMarkdownContainer"] .research-link:hover{border-color:var(--atlas-violet);color:var(--atlas-deep)}
.research-protein,.research-orthogroup{font-family:ui-monospace,Consolas,monospace}
.research-unavailable{font-size:11px;color:#8a4e16;background:#fff6e4;padding:3px 6px;border-radius:5px}
.research-next{border-left:2px solid var(--atlas-primary);padding:2px 0 2px 12px;margin:18px 0}
.research-next>span{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.035em;color:var(--atlas-deep)}
[data-testid="stAppViewContainer"] .research-next p{font-size:.88rem;margin:5px 0 0;line-height:1.55}
.research-card details{border-top:1px solid var(--atlas-line);padding-top:12px}
.research-card summary{cursor:pointer;font-size:12px;font-weight:750;color:var(--atlas-primary);padding:4px 0;list-style-position:inside}
.research-evidence{padding-top:12px}
[data-testid="stAppViewContainer"] .research-evidence p{font-size:.86rem;line-height:1.65;overflow-wrap:anywhere}
.research-difference{color:#8a4215!important;font-size:12px!important;font-weight:650}
.research-additional-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.research-additional{padding:18px;background:#fff;border:1px solid var(--atlas-line);border-radius:6px;min-width:0}
.research-additional h4{font-size:1.1rem;margin:0 0 9px;padding:0!important;color:var(--atlas-deep)}
[data-testid="stAppViewContainer"] .research-additional p{font-size:.9rem;line-height:1.6;margin:10px 0}
.research-matrix{overflow-x:auto;border:1px solid var(--atlas-line);border-radius:12px;background:white}
.research-matrix table{width:100%;border-collapse:collapse;font-size:.92rem}
.research-matrix th,.research-matrix td{text-align:left;vertical-align:top;padding:16px 20px;border:0;border-bottom:1px solid var(--atlas-line);line-height:1.6}
.research-matrix thead th{background:var(--atlas-tint);color:var(--atlas-ink);font-weight:700;border-bottom:2px solid var(--atlas-accent)}
.research-matrix tbody th{width:22%;font-weight:700;background:#fff}
.research-matrix tr:last-child td,.research-matrix tr:last-child th{border-bottom:0}
.research-roadmap{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:12px 0}
.research-step{display:flex;align-items:start;gap:15px;padding:20px;background:white;border:1px solid var(--atlas-line);border-radius:6px;min-width:0}
.research-step-number{background:var(--atlas-primary);color:#fff;border-radius:50%;min-width:36px;height:36px;display:grid;place-items:center;font-size:13px;font-weight:700}
.research-step h4{font-size:1rem;line-height:1.7;margin:0;padding:0!important;overflow-wrap:anywhere}
.research-step .research-card-label{margin-top:0}
[data-testid="stAppViewContainer"] .research-step p{font-size:.9rem;line-height:1.6;margin:9px 0 12px}
@media(max-width:1250px){.research-grid{grid-template-columns:1fr}.research-card h3,.research-objective{min-height:0!important}.research-card{padding:22px}.research-metric{flex:0 1 160px}}
@media(max-width:760px){.research-additional-grid,.research-roadmap{grid-template-columns:1fr}.research-grid{gap:12px}.research-card{padding:18px}.research-matrix th,.research-matrix td{padding:12px;font-size:.85rem}.research-intro h2{font-size:1.5rem}}
@media(min-width:1600px){[data-testid="stMainBlockContainer"]{padding-inline:2.4rem}}
@media(max-width:1100px){[data-testid="stMainBlockContainer"],.block-container{padding:3.7rem 1.25rem 2rem}.atlas-hero{grid-template-columns:minmax(0,1fr) 190px}.atlas-hero-meta{flex-wrap:wrap}.atlas-hero-stat{padding:12px 8px}.atlas-hero-stat strong{font-size:1.8rem}}
@media(max-width:760px){[data-testid="stMainBlockContainer"],.block-container{padding:3.7rem .85rem 2rem}.atlas-hero{grid-template-columns:1fr}.atlas-hero-stats{grid-template-columns:repeat(2,1fr);gap:10px}.atlas-hero-stat{padding:12px}.atlas-hero-stat strong{font-size:1.65rem}.atlas-hero-stat span{font-size:12px}.atlas-section-heading{align-items:start}.atlas-live-label{display:none}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
'''


def navigation_icons_css():
    """Small local vector symbols; native radio labels keep their keyboard behavior."""
    icons=[
        '<path d="M4 5h6c2 0 2 1 2 2v13c0-2-1-2-3-2H4zM20 5h-6c-2 0-2 1-2 2v13c0-2 1-2 3-2h5z"/>',
        '<circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="12" cy="18" r="3"/><path d="m8 8 3 7m5-7-3 7M9 6h6"/>',
        '<rect x="4" y="4" width="6" height="6"/><rect x="14" y="4" width="6" height="6"/><rect x="4" y="14" width="6" height="6"/><rect x="14" y="14" width="6" height="6"/>',
        '<path d="m7 8 9 0M7 9l4 8m5-8-4 8"/><circle cx="5" cy="7" r="3"/><circle cx="19" cy="7" r="3"/><circle cx="12" cy="19" r="3"/>',
        '<path d="M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4"/>',
        '<path d="M4 4h5v7h7V4h4M9 11v9H4m12-9v9h4"/>',
        '<path d="M5 3h10l4 4v14H5zM14 3v5h5M8 12h8m-8 4h8"/>',
        '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6M7 8h6m-6 4h6"/>',
        '<path d="M3 4h18v13H9l-6 4zM7 8h10m-10 5h7"/>',
        '<path d="M3 6h7l2 3h9v12H3zM3 6V3h7l2 3h9v3"/>',
        '<path d="M5 5h5v7H5v7m9-14h5v7h-5v7"/>',
    ]
    css='''
[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label{display:flex;align-items:center;gap:12px;width:100%;box-sizing:border-box}
[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label input[type=radio]{position:absolute;width:1px;height:1px;opacity:0}
[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label>div>div:has(+[data-testid="stMarkdownContainer"]){display:none}
[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label:before{content:"";width:32px;height:32px;flex:0 0 32px;border-radius:50%;background-color:var(--atlas-primary);background-image:var(--nav-icon);background-size:21px;background-repeat:no-repeat;background-position:center;box-shadow:0 0 0 3px var(--atlas-tint);pointer-events:none}
[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label:has(input:checked):before{background-color:var(--atlas-deep);box-shadow:0 0 0 3px #ded2f6}
[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"] label:has(input:focus-visible){outline:2px solid var(--atlas-primary);outline-offset:2px}
'''
    for index,paths in enumerate(icons,1):
        svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'+paths+'</svg>'
        css+=f'[data-testid="stSidebar"] .st-key-atlas_page [role="radiogroup"]>:nth-child({index}){{--nav-icon:url("data:image/svg+xml,{quote(svg)}")}}\n'
    return css


def apply_style():
    from scientific_text import install_streamlit,install_browser_typography
    install_streamlit()
    st.set_page_config(page_title='Schisto-Adhesome Atlas | Integrin–adhesome',page_icon='🧬',layout='wide',initial_sidebar_state='auto')
    st.markdown('<style>'+TOKENS_CSS+APP_CSS+navigation_icons_css()+'</style>',unsafe_allow_html=True)
    install_browser_typography()


def introduction_hero(candidates,app_url=''):
    from html import escape
    from navigation import hypothesis_url
    stats=[('Candidates',len(candidates)),('Species',candidates.species.nunique()),('Family labels',candidates.family.nunique()),('Orthogroups',candidates.loc[candidates.orthogroup.ne(''),'orthogroup'].nunique())]
    cards=''.join(f'<div class="atlas-hero-stat"><strong>{value:,}</strong><span>{escape(label)}</span></div>' for label,value in stats)
    st.markdown('''<section class="atlas-hero" aria-label="About the Schisto-Adhesome Atlas">
<div><h1>Schisto-Adhesome Atlas</h1>
<h2>About the Schisto-Adhesome Atlas</h2><p>The <strong>Schisto-Adhesome Atlas</strong> is an interactive platform for exploring adhesion-associated proteins across medically important <em>Schistosoma</em> species. It integrates protein annotations, orthology, phylogeny, conserved domains and motif exploration to reveal evolutionary relationships, parasite-specific features and potential functional interaction modules. By connecting comparative bioinformatics with experimental prioritization, the Atlas supports the discovery of candidate drug targets, vaccine antigens and biomarkers for schistosomiasis research.</p>
<div class="atlas-hero-meta"><a href="'''+escape(hypothesis_url(app_url),quote=True)+'''" target="_self">Explore the adhesome <span aria-hidden="true">↗</span></a></div></div>
<div class="atlas-hero-stats" aria-label="Catalogue summary">'''+cards+'</div></section>',unsafe_allow_html=True)
