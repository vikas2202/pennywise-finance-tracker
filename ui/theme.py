from html import escape
from pathlib import Path
import streamlit as st

PALETTE = ["#7662ef", "#ff9974", "#20bfa9", "#eab84e", "#5e9ded", "#dd78b0"]


def apply_theme():
    st.markdown('<style>' + (Path(__file__).parent / 'theme.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)


def hero(title, subtitle, tag="PENNYWISE STUDIO"):
    st.markdown(f'<section class="pw-hero"><div class="pw-orbit"></div><div class="pw-hero-content"><span class="pw-tag">{escape(tag)}</span><h1>{escape(title)}</h1><p>{escape(subtitle)}</p><div class="pw-chips"><span>◈ Track</span><span>↗ Discover</span><span>◎ Plan ahead</span></div></div></section>', unsafe_allow_html=True)


def section_intro(number, title, text):
    st.markdown(f'<div class="pw-intro"><span>{escape(number)}</span><div><h3>{escape(title)}</h3><p>{escape(text)}</p></div></div>', unsafe_allow_html=True)
