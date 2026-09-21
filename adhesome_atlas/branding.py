"""Display the supplied institutional identity without modifying original assets."""
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
    detail = ''.join(f'<div class="identity-detail">{escape(line)}</div>' for line in lines[1:])
    st.markdown('''<style>
    .atlas-identity{display:flex;align-items:center;gap:24px;background:#fff;border:1px solid #dce6ed;border-radius:16px;padding:16px 24px;margin-bottom:16px;color:#18354a}
    .identity-logos{display:flex;align-items:center;gap:16px;flex-shrink:0}
    .identity-logos img{width:92px;height:92px;object-fit:contain;background:white}
    .identity-title{font-weight:700;font-size:1.05rem;line-height:1.4}
    .identity-detail{font-size:.86rem;color:#526977;margin-top:6px;line-height:1.5}
    @media(max-width:640px){.atlas-identity{flex-direction:column;align-items:flex-start;gap:12px;padding:16px}.identity-logos img{width:76px;height:76px}}
    </style>''' + f'<div class="atlas-identity"><div class="identity-logos">{"".join(logos)}</div><div>{title}{detail}</div></div>', unsafe_allow_html=True)


def creator_credit():
    for line in descriptors():
        if line.lower().startswith('created by'):
            st.caption(line)
