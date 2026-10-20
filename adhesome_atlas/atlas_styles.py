"""Responsive scientific workspace, typography and reusable interface surfaces."""
import streamlit as st
from design_system import TOKENS_CSS

APP_CSS = '''
html{scroll-behavior:smooth}
[data-testid="stAppViewContainer"]{background:var(--atlas-paper);font-family:var(--atlas-font)}
[data-testid="stMainBlockContainer"],.block-container{max-width:none;padding:3.7rem 2rem 3rem;min-width:0}
[data-testid="stMain"] [data-testid="stVerticalBlock"]{gap:1rem;min-width:0}
[data-testid="stAppViewContainer"] p,[data-testid="stAppViewContainer"] li{color:var(--atlas-text);font-size:1rem;line-height:1.6}
h1,h2,h3{font-family:var(--atlas-font);letter-spacing:-.035em;color:var(--atlas-ink);font-weight:750;line-height:1.2}
h1{font-size:2.6rem}h2{font-size:1.8rem}h3{font-size:1.3rem}
[data-testid="stHeader"]{background:#f3f6f4ed}
[data-testid="stHeading"]{scroll-margin-top:65px}
[data-testid="stMetric"]{background:var(--atlas-surface);border:1px solid var(--atlas-line);border-radius:14px;padding:17px 20px;box-shadow:0 3px 12px #173d2705}
[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;letter-spacing:-.05em;color:var(--atlas-deep);font-size:2.45rem;font-weight:750}
[data-testid="stMetricLabel"] p{color:var(--atlas-muted)!important;font-size:.9rem!important;font-weight:650}
[data-testid="stSidebar"]{background:#fbfcfa;border-right:1px solid var(--atlas-line)}
[data-testid="stSidebarContent"]{padding-top:.7rem}
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"]{opacity:1!important;visibility:visible!important}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.75rem}
.atlas-sidebar-brand{padding:4px 0 15px;border-bottom:1px solid var(--atlas-line);margin-bottom:3px;display:flex;align-items:center;gap:10px}
.atlas-sidebar-symbol{display:grid;place-items:center;width:39px;height:43px;border-radius:12px 4px 12px 4px;background:var(--atlas-deep);color:var(--atlas-gold);font-size:23px;font-weight:700}
.atlas-sidebar-brand strong{font-size:18px;line-height:1.15;color:var(--atlas-deep);letter-spacing:-.025em}
.atlas-sidebar-brand small{display:block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--atlas-muted);margin-top:6px}
[data-testid="stSidebar"] [role="radiogroup"]{gap:2px}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:6px 10px;min-height:36px;transition:background .15s}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#edf3ee}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#e5f0e9;box-shadow:inset 3px 0 var(--atlas-green)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:var(--atlas-deep);font-weight:750}
[data-testid="stSidebar"] [role="radiogroup"] label p{font-size:.94rem;line-height:1.35}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-size:.85rem!important;letter-spacing:.01em}
[data-testid="stWidgetLabel"] p{color:var(--atlas-ink)!important;font-size:.94rem!important;font-weight:650}
[data-baseweb="select"]>div,[data-baseweb="input"]>div{border-radius:9px!important;border-color:#cbd8d0!important;background:white}
[data-baseweb="tag"]{background:#e6f1eb!important;color:#123e2d!important}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button,[data-testid="stLinkButton"] a{border-radius:9px;min-height:40px;border:1px solid #b8cdc1;background:white;color:var(--atlas-deep);font-weight:650;box-shadow:0 2px 4px #183c2605}
[data-testid="stButton"] button p,[data-testid="stDownloadButton"] button p{color:inherit}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover,[data-testid="stLinkButton"] a:hover{background:#e7f1eb;border-color:var(--atlas-green);color:var(--atlas-deep)}
button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid var(--atlas-focus)!important;outline-offset:3px}
[data-testid="stDataFrame"],[data-testid="stPlotlyChart"]{border:1px solid var(--atlas-line);border-radius:14px;background:#fff;overflow:hidden}
[data-testid="stExpander"]{border-radius:12px;border:1px solid var(--atlas-line);background:#fff;overflow:hidden}
[data-testid="stExpander"] summary{padding:12px 15px}
[data-testid="stExpander"] summary p{font-size:.94rem;font-weight:650;color:var(--atlas-deep)}
[data-testid="stTabs"] [role="tablist"]{gap:8px;border-bottom:1px solid var(--atlas-line)}
[data-testid="stTabs"] [role="tab"]{padding:10px 14px;color:var(--atlas-muted)}
[data-testid="stTabs"] [aria-selected="true"]{background:#e5f1e9;color:var(--atlas-deep);border-radius:9px 9px 0 0;font-weight:750}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:var(--atlas-green)}
[data-testid="stAlert"]{border-radius:12px;font-size:.95rem}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--atlas-muted)!important;font-size:.86rem!important;line-height:1.5}
[data-testid="stMarkdownContainer"] a{color:var(--atlas-green);text-underline-offset:3px}
[data-testid="stMarkdownContainer"] a:hover{color:#8b4a22}
iframe{max-width:100%;border-radius:16px}
.atlas-hero{position:relative;isolation:isolate;overflow:hidden;display:grid;grid-template-columns:minmax(0,1fr) minmax(245px,.34fr);gap:36px;padding:30px 36px;border-radius:20px;background:radial-gradient(ellipse at 88% 6%,#37847270,transparent 50%),linear-gradient(115deg,#073c32,#105647 65%,#174b47);color:white;box-shadow:0 15px 40px #153d2520}
.atlas-hero:after{content:"";position:absolute;z-index:-1;inset:-120px -200px -100px 62%;border:1px solid #d4e7d33b;border-radius:44% 0 0 30%;transform:rotate(27deg);box-shadow:-38px 0 0 #e4cf8f09,-76px 0 0 #d9f0e509}
.atlas-hero .eyebrow{color:#e8cf8d;font-size:10px;text-transform:uppercase;letter-spacing:.18em;font-weight:750;margin:0 0 9px}
.atlas-hero h1{color:white;font-size:clamp(2rem,3vw,3.25rem);line-height:1.05;margin:0 0 14px;letter-spacing:-.05em;max-width:850px}
.atlas-hero h2{font-size:.95rem;color:#f2ddb0;margin:0 0 6px;letter-spacing:0;font-weight:650}
.atlas-hero h1,.atlas-hero h2{padding:0!important;font-family:var(--atlas-font)!important}
.atlas-section-heading h2{padding:0!important;font-family:var(--atlas-font)!important}
.atlas-sidebar-brand strong,.identity-title{font-family:var(--atlas-font)!important}
[data-testid="stAppViewContainer"] .atlas-hero p{color:#f1f7f2;font-size:.98rem;line-height:1.55;margin:0;max-width:850px}
.atlas-hero-meta{display:flex;gap:14px;align-items:center;margin-top:15px;font-size:12px;color:#c5dfcf}
.atlas-hero-meta a{display:inline-flex;align-items:center;gap:16px;background:#f0d07b;color:#153b2e!important;border-radius:8px;text-decoration:none;padding:9px 14px;font-weight:750;white-space:nowrap}
.atlas-hero-stats{align-self:center;display:grid;grid-template-columns:1fr 1fr;gap:11px;position:relative}
.atlas-hero-stat{border-top:1px solid #9bc4b961;padding:13px 5px 11px}
.atlas-hero-stat strong{display:block;font-size:clamp(1.8rem,2.3vw,2.65rem);font-weight:700;line-height:1.1;letter-spacing:-.05em;font-variant-numeric:tabular-nums;color:#fff}
.atlas-hero-stat span{display:block;font-size:12px;color:#d4e8dc;margin-top:6px}
.atlas-section-heading{display:flex;justify-content:space-between;align-items:end;gap:12px;margin:4px 0}
.atlas-section-heading h2{font-size:1.5rem;margin:0 0 5px}
.atlas-section-heading p{font-size:.9rem!important;color:var(--atlas-muted)!important;margin:0}
.atlas-section-kicker{font-size:10px;text-transform:uppercase;letter-spacing:.16em;font-weight:750;color:var(--atlas-green);margin-bottom:7px}
.atlas-live-label{font-size:11px;font-weight:650;color:var(--atlas-green);border:1px solid #c8ded0;border-radius:30px;padding:6px 11px;background:#eef6f0;white-space:nowrap}
.atlas-live-label:before{content:"";display:inline-block;height:6px;width:6px;background:#1b7c59;border-radius:50%;margin-right:6px}
@media(min-width:1600px){[data-testid="stMainBlockContainer"]{padding-inline:2.4rem}.atlas-hero{padding:32px 40px}}
@media(max-width:1100px){[data-testid="stMainBlockContainer"],.block-container{padding:3.7rem 1.25rem 2rem}.atlas-hero{grid-template-columns:minmax(0,1fr) 190px;gap:22px;padding:25px}.atlas-hero-meta{flex-wrap:wrap}.atlas-hero-stat strong{font-size:1.95rem}}
@media(max-width:760px){[data-testid="stMainBlockContainer"],.block-container{padding:3.7rem .85rem 2rem}.atlas-hero{grid-template-columns:1fr;gap:18px;padding:24px;border-radius:16px}.atlas-hero-stats{grid-template-columns:repeat(4,1fr);gap:10px}.atlas-hero-stat{padding:12px 0 0}.atlas-hero-stat strong{font-size:1.65rem}.atlas-hero-stat span{font-size:11px}.atlas-section-heading{align-items:start}.atlas-live-label{display:none}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
'''


def apply_style():
    st.set_page_config(page_title='Schisto-Adhesome Atlas | Integrin–adhesome',page_icon='🧬',layout='wide',initial_sidebar_state='auto')
    st.markdown('<style>'+TOKENS_CSS+APP_CSS+'</style>',unsafe_allow_html=True)


def introduction_hero(candidates):
    from html import escape
    stats=[('Candidates',len(candidates)),('Species',candidates.species.nunique()),('Families',candidates.family.nunique()),('Orthogroups',candidates.loc[candidates.orthogroup.ne(''),'orthogroup'].nunique())]
    cards=''.join(f'<div class="atlas-hero-stat"><strong>{value:,}</strong><span>{escape(label)}</span></div>' for label,value in stats)
    st.markdown('''<section class="atlas-hero" aria-label="About the Schisto-Adhesome Atlas">
<div><div class="eyebrow">Comparative adhesion biology · GHID–KCCR</div><h1>Schisto-Adhesome Atlas</h1>
<h2>About the Schisto-Adhesome Atlas</h2><p>The <strong>Schisto-Adhesome Atlas</strong> is an interactive platform for exploring adhesion-associated proteins across medically important <em>Schistosoma</em> species. It integrates protein annotations, orthology, phylogeny, conserved domains and motif exploration to reveal evolutionary relationships, parasite-specific features and potential functional interaction modules. By connecting comparative bioinformatics with experimental prioritization, the Atlas supports the discovery of candidate drug targets, vaccine antigens and biomarkers for schistosomiasis research.</p>
<div class="atlas-hero-meta"><a href="#hypothesis-workspace" target="_self">Explore the adhesome <span aria-hidden="true">↗</span></a><span>Comparative evidence. Connected hypotheses.</span></div></div>
<div class="atlas-hero-stats" aria-label="Catalogue summary">'''+cards+'</div></section>',unsafe_allow_html=True)
