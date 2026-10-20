"""Display institutional identity without modifying original logo assets."""
import base64
from html import escape
import streamlit as st
from data import ROOT


def descriptors():
    path = ROOT / 'Global Health and Infectious Diseas.txt'
    return [line.strip() for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()] if path.exists() else []


def identity_banner():
    lines = descriptors()
    logos = []
    for name, mime, label in [('Logo.jpeg', 'image/jpeg', 'Global Health and Infectious Diseases Research Group, KCCR'),
                              ('Synergy_NGS2025.png', 'image/png', 'Synergy-NGS 2025')]:
        path = ROOT / name
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode('ascii')
            logos.append(f'<img src="data:{mime};base64,{encoded}" alt="{escape(label)}" title="{escape(label)}">')
    if not lines and not logos:
        return
    title = f'<div class="identity-title">{escape(lines[0])}</div>' if lines else ''
    detail = ''.join(f'<div class="identity-detail">{escape(line)}</div>' for line in lines[1:] if not line.lower().startswith('created by'))
    st.markdown('''<style>
    .atlas-identity{display:flex;align-items:center;gap:20px;padding:0 2px 5px;color:#13251f}
    .identity-logos{display:flex;align-items:center;gap:12px;flex-shrink:0;padding-right:20px;border-right:1px solid #dce5df}
    .identity-logos img{width:56px;height:56px;object-fit:contain;background:white;border-radius:4px}
    .identity-title{font-weight:700;font-size:.92rem;line-height:1.35;letter-spacing:-.015em}
    .identity-detail{font-size:.76rem;color:#526760;margin-top:4px;line-height:1.45}
    @media(max-width:760px){.atlas-identity{gap:13px}.identity-logos{padding-right:12px;gap:8px}.identity-logos img{width:43px;height:43px}.identity-detail{display:none}.identity-title{font-size:.8rem}}
    </style>''' + f'<div class="atlas-identity"><div class="identity-logos">{"".join(logos)}</div><div>{title}{detail}</div></div>', unsafe_allow_html=True)


def creator_credit():
    for line in descriptors():
        if line.lower().startswith('created by'):
            st.caption(line)
