"""태블릿 발표용 광선 추적 시뮬레이터."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="광선 추적 실험실", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.block-container {max-width:1450px; padding:.8rem 1rem 1rem}
header[data-testid="stHeader"] {height:0}
[data-testid="stDecoration"] {display:none}
@media(max-width:700px){.block-container {padding:.4rem .35rem}}
</style>""", unsafe_allow_html=True)
components.html(Path(__file__).with_name("simulator.html").read_text(encoding="utf-8"), height=1100, scrolling=False)
