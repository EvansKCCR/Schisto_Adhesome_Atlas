"""Offline design tokens shared by the atlas and standalone visualizations."""
TOKENS_CSS = '''
:root{
 --atlas-ink:#111111;--atlas-text:#202421;--atlas-muted:#454c48;
 --atlas-green:#146b4e;--atlas-deep:#10523e;--atlas-mint:#edf5f0;
 --atlas-gold:#f1d27b;--atlas-paper:#ffffff;--atlas-surface:#ffffff;
 --atlas-line:#d4d9d6;--atlas-red:#c43c2c;--atlas-focus:#146b4e;
 --atlas-a:#0b6648;--atlas-a-bg:#e4f3eb;--atlas-b:#7b5010;--atlas-b-bg:#fff2d4;
 --atlas-c:#a62d25;--atlas-c-bg:#fff0ee;
 --atlas-font:"Segoe UI",Arial,Helvetica,sans-serif;
 --atlas-radius:7px;--atlas-small-radius:5px;
 --atlas-shadow:none;--atlas-space:8px;
}
'''
NETWORK_CSS = '''
body{font-family:var(--atlas-font);color:var(--atlas-ink);background:var(--atlas-paper)}
button,select,input{font-family:inherit}
button,select,input[type=search]{min-height:36px;border-radius:var(--atlas-small-radius);border-color:#bdcec5;font-size:14px}
button{transition:background .15s,border-color .15s;cursor:pointer}
button:hover{background:#f6f9f7;border-color:var(--atlas-green)}
button:focus-visible,a:focus-visible,select:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--atlas-focus);outline-offset:3px}
.atlas-grade{display:inline-flex;align-items:center;gap:5px;border-radius:30px;padding:5px 10px;font-size:12px;font-weight:750;letter-spacing:.02em}
.atlas-grade[data-grade=A]{background:var(--atlas-a-bg);color:var(--atlas-a)}
.atlas-grade[data-grade=B]{background:var(--atlas-b-bg);color:var(--atlas-b)}
.atlas-grade[data-grade=C]{background:var(--atlas-c-bg);color:var(--atlas-c)}
.atlas-grade[data-grade=D]{background:#e9eef0;color:#394e58}
.atlas-profile-id{font-family:ui-monospace,Consolas,monospace;font-size:13px;overflow-wrap:anywhere}
.atlas-profile-heading{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px}
.atlas-profile-heading small{font-size:11px;text-transform:uppercase;letter-spacing:.12em;font-weight:750;color:var(--atlas-muted)}
details>summary{cursor:pointer}
/* Scientific interface surfaces; SVG node/edge colors retain their data meaning. */
html,body{background:#fff!important;color:var(--atlas-ink)!important}
header,.toolbar,.bar,.controlbar,.mapbar,.topstats,.paper,.panel,.stage,.workspace,
.profile-rail,.sidebar,.legend,.detail,.atlas-profiles-bar,.atlas-filter-drawer,.atlas-evidence-drawer{background:#fff!important;box-shadow:none!important}
header,.toolbar,.bar{border-bottom:1px solid var(--atlas-red)!important}
header h1,header h2,header strong{color:var(--atlas-deep)!important}
header p,header label,.muted,.view-status,.hint{color:var(--atlas-muted)!important}
button,select,input[type=search],input[type=text]{border:1px solid #aebcb3!important;border-radius:5px!important;min-height:36px;font:600 14px var(--atlas-font)!important}
button{background:#fff!important;color:var(--atlas-deep)!important;box-shadow:none!important}
button:hover{background:#edf5f0!important;border-color:var(--atlas-green)!important}
button.active,button.primary,button.major,.btn.major,button[aria-pressed=true],#simulateSelection{background:var(--atlas-green)!important;color:#fff!important;border-color:var(--atlas-green)!important}
button.active:hover,button.primary:hover,button.major:hover,#simulateSelection:hover{background:var(--atlas-deep)!important;color:#fff!important}
select,input[type=search],input[type=text]{background:#fff!important;color:#111!important}
label,.ctrl{font-size:13px!important;font-weight:600;color:#303833!important}
input[type=checkbox],input[type=radio],input[type=range]{accent-color:var(--atlas-green)}
.profile-rail,.sidebar{border-left:1px solid var(--atlas-line)!important}
.profile-rail th,.atlas-profile th{background:#f4f5f4!important;color:#202421!important}
#status,#pathSummary,.hint,.atlas-connected-info{background:#fff!important;border-color:var(--atlas-line)!important;border-left:3px solid var(--atlas-green)!important;color:#303833!important}
.metric,#candidateCounts{background:#f4f5f4!important;color:#202421!important;box-shadow:none!important}
.eyebrow,.atlas-profile-heading small{font-size:12px!important;letter-spacing:.025em!important;color:#303833!important}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
'''

def network_style():
    return '<style>'+TOKENS_CSS+NETWORK_CSS+'</style>'
