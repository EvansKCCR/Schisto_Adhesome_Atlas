"""Offline design tokens shared by the atlas and standalone visualizations."""
TOKENS_CSS = '''
:root{
 --atlas-ink:#13251f;--atlas-text:#172d29;--atlas-muted:#526760;
 --atlas-green:#0a624d;--atlas-deep:#073f35;--atlas-mint:#e8f3ee;
 --atlas-gold:#f1d27b;--atlas-paper:#f3f6f4;--atlas-surface:#ffffff;
 --atlas-line:#dce5df;--atlas-red:#b91c1c;--atlas-focus:#b47b12;
 --atlas-a:#0b6648;--atlas-a-bg:#e4f3eb;--atlas-b:#7b5010;--atlas-b-bg:#fff2d4;
 --atlas-c:#813850;--atlas-c-bg:#f8eaf0;
 --atlas-font:"Inter","Segoe UI",Arial,sans-serif;
 --atlas-radius:16px;--atlas-small-radius:9px;
 --atlas-shadow:0 8px 32px #153b2810;--atlas-space:8px;
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
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
'''

def network_style():
    return '<style>'+TOKENS_CSS+NETWORK_CSS+'</style>'
