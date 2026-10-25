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
.research-intro{margin:16px 0 0;max-width:1150px}
.research-intro h2{font-size:1.85rem;margin:0 0 12px;padding:0!important}
.research-intro p{margin:0;font-size:.96rem!important}
.research-legend{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0}
.research-tag{display:inline-block;border:1px solid transparent;border-radius:30px;padding:5px 9px;font-size:11px;font-weight:750;line-height:1.4}
.research-tag.supported{background:var(--atlas-a-bg);color:var(--atlas-a);border-color:#c5dfd2}
.research-tag.provisional{background:var(--atlas-c-bg);color:var(--atlas-c);border-color:#e9cad6}
.research-tag.unassigned{background:#e9eef0;color:#394e58;border-color:#cbd5da}
.research-tag.published{background:#edf0fb;color:#334a87;border-color:#d2dbf1}
.research-tag.proposed{background:#fff5dc;color:#795718;border-color:#e9d69d}
.research-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:8px 0 14px;align-items:start}
.research-card{border:1px solid #d1dfd7;border-top:4px solid var(--atlas-green);border-radius:15px;padding:24px;background:linear-gradient(155deg,#f2f8f4 0,#fff 40%);box-shadow:var(--atlas-shadow);min-width:0;transition:box-shadow .2s,border-color .2s}
.research-card:nth-child(2){border-top-color:#ae791d;background:linear-gradient(155deg,#fff9e8 0,#fff 40%)}
.research-card:nth-child(3){border-top-color:#486882;background:linear-gradient(155deg,#eff5fa 0,#fff 40%)}
.research-card:hover{border-color:#a9c6b6;box-shadow:0 10px 32px #153b2818}
.research-card-kicker{font-size:10px;color:var(--atlas-muted);text-transform:uppercase;letter-spacing:.12em;font-weight:750;margin-bottom:9px}
.research-card h3{font-size:1.45rem;line-height:1.2;margin:0 0 18px;padding:0!important;min-height:3.5rem}
.research-metrics{display:flex;flex-wrap:wrap;gap:14px;border-bottom:1px solid var(--atlas-line);padding-bottom:16px;margin-bottom:14px}
.research-metric{flex:1;min-width:90px}
.research-metric strong{font-size:2.15rem;line-height:1;font-variant-numeric:tabular-nums;color:var(--atlas-deep);display:block;letter-spacing:-.04em}
.research-metric.provisional strong{color:var(--atlas-c)}
.research-metric.unassigned strong{color:#394e58}
.research-metric>span{font-size:11px;line-height:1.4;display:block;margin-top:6px;color:var(--atlas-muted);font-weight:650}
[data-testid="stAppViewContainer"] .research-objective{font-size:.92rem;font-weight:650;line-height:1.45;min-height:2.7rem;margin:0 0 12px}
.research-card-label{font-size:10px;color:var(--atlas-muted);text-transform:uppercase;letter-spacing:.07em;font-weight:750;margin:14px 0 7px}
.research-links{display:flex;flex-wrap:wrap;gap:6px 4px;align-items:center;font-size:12px;line-height:1.8;overflow-wrap:anywhere}
[data-testid="stMarkdownContainer"] .research-link{display:inline-block;border:1px solid #d8e4dc;background:#f6faf7;color:#064d39;border-radius:6px;padding:3px 7px;font-size:12px;font-weight:650;text-decoration:none;overflow-wrap:anywhere;max-width:100%;line-height:1.6}
[data-testid="stMarkdownContainer"] .research-link:hover{background:#dfefe5;border-color:#92b8a3;color:#063a2c}
.research-protein,.research-orthogroup{font-family:ui-monospace,Consolas,monospace}
.research-unavailable{font-size:11px;color:#8a4e16;background:#fff6e4;padding:3px 6px;border-radius:5px}
.research-next{border-left:3px solid #d5ba6e;padding:2px 0 2px 12px;margin:18px 0}
.research-next>span{font-size:10px;font-weight:750;text-transform:uppercase;letter-spacing:.08em;color:#725214}
[data-testid="stAppViewContainer"] .research-next p{font-size:.88rem;margin:5px 0 0;line-height:1.55}
.research-card details{border-top:1px solid var(--atlas-line);padding-top:12px}
.research-card summary{cursor:pointer;font-size:12px;font-weight:750;color:var(--atlas-green);padding:4px 0;list-style-position:inside}
.research-evidence{padding-top:12px}
[data-testid="stAppViewContainer"] .research-evidence p{font-size:.86rem;line-height:1.65;overflow-wrap:anywhere}
.research-difference{color:#8a4215!important;font-size:12px!important;font-weight:650}
.research-additional-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.research-additional{padding:18px;background:#f9fbfa;border:1px solid var(--atlas-line);border-radius:12px;min-width:0}
.research-additional h4{font-size:1.1rem;margin:0 0 9px;padding:0!important;color:var(--atlas-deep)}
[data-testid="stAppViewContainer"] .research-additional p{font-size:.9rem;line-height:1.6;margin:10px 0}
.research-matrix{overflow-x:auto;border:1px solid var(--atlas-line);border-radius:12px;background:white}
.research-matrix table{width:100%;border-collapse:collapse;font-size:.92rem}
.research-matrix th,.research-matrix td{text-align:left;vertical-align:top;padding:16px 20px;border:0;border-bottom:1px solid var(--atlas-line);line-height:1.6}
.research-matrix thead th{background:#e7f1eb;color:var(--atlas-deep);font-weight:750}
.research-matrix tbody th{width:22%;font-weight:700;background:#f8faf8}
.research-matrix tr:last-child td,.research-matrix tr:last-child th{border-bottom:0}
.research-roadmap{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:12px 0}
.research-step{display:flex;align-items:start;gap:15px;padding:20px;background:white;border:1px solid var(--atlas-line);border-radius:12px;min-width:0}
.research-step-number{background:#e5f0e9;color:var(--atlas-deep);border-radius:9px;min-width:36px;height:36px;display:grid;place-items:center;font-size:13px;font-weight:750}
.research-step h4{font-size:1rem;line-height:1.7;margin:0;padding:0!important;overflow-wrap:anywhere}
.research-step .research-card-label{margin-top:0}
[data-testid="stAppViewContainer"] .research-step p{font-size:.9rem;line-height:1.6;margin:9px 0 12px}
@media(max-width:1250px){.research-grid{grid-template-columns:1fr}.research-card h3,.research-objective{min-height:0!important}.research-card{padding:22px}.research-metric{flex:0 1 160px}}
@media(max-width:760px){.research-additional-grid,.research-roadmap{grid-template-columns:1fr}.research-grid{gap:12px}.research-card{padding:18px}.research-matrix th,.research-matrix td{padding:12px;font-size:.85rem}.research-intro h2{font-size:1.5rem}}
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
    stats=[('Candidates',len(candidates)),('Species',candidates.species.nunique()),('Family labels',candidates.family.nunique()),('Orthogroups',candidates.loc[candidates.orthogroup.ne(''),'orthogroup'].nunique())]
    cards=''.join(f'<div class="atlas-hero-stat"><strong>{value:,}</strong><span>{escape(label)}</span></div>' for label,value in stats)
    st.markdown('''<section class="atlas-hero" aria-label="About the Schisto-Adhesome Atlas">
<div><div class="eyebrow">Comparative adhesion biology · GHID–KCCR</div><h1>Schisto-Adhesome Atlas</h1>
<h2>About the Schisto-Adhesome Atlas</h2><p>The <strong>Schisto-Adhesome Atlas</strong> is an interactive platform for exploring adhesion-associated proteins across medically important <em>Schistosoma</em> species. It integrates protein annotations, orthology, phylogeny, conserved domains and motif exploration to reveal evolutionary relationships, parasite-specific features and potential functional interaction modules. By connecting comparative bioinformatics with experimental prioritization, the Atlas supports the discovery of candidate drug targets, vaccine antigens and biomarkers for schistosomiasis research.</p>
<div class="atlas-hero-meta"><a href="#hypothesis-workspace" target="_self">Explore the adhesome <span aria-hidden="true">↗</span></a><span>Comparative evidence. Connected hypotheses.</span></div></div>
<div class="atlas-hero-stats" aria-label="Catalogue summary">'''+cards+'</div></section>',unsafe_allow_html=True)
