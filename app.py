"""
app.py  —  AI Portfolio Rationalization Advisor
Entry point. Sets page config, injects CSS, renders navigation.

Run with:  streamlit run app.py
"""

import streamlit as st
from data_layer import init_session

st.set_page_config(
    page_title="AI Portfolio Advisor",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color:#F8F9FA; border-right:1px solid #E5E7EB; }
[data-testid="stSidebar"] .stMarkdown p { margin-bottom:0; }
.block-container { padding-top:1.5rem !important; }
.badge { display:inline-block; font-size:11px; font-weight:500;
         padding:2px 10px; border-radius:12px; white-space:nowrap; }
.badge-retain    { background:#EAF3DE; color:#3B6D11; }
.badge-modernize { background:#FAEEDA; color:#854F0B; }
.badge-retire    { background:#FCEBEB; color:#A32D2D; }
.badge-replace   { background:#FAEEDA; color:#854F0B; }
.badge-evaluate  { background:#E6F1FB; color:#185FA5; }
.badge-pending   { background:#F3F4F6; color:#6B7280; }
.badge-approved  { background:#EAF3DE; color:#3B6D11; }
.badge-overridden{ background:#FAEEDA; color:#854F0B; }
.badge-escalated { background:#EEF2FF; color:#4338CA; }
.badge-inside    { background:#EAF3DE; color:#3B6D11; }
.badge-edge      { background:#FAEEDA; color:#854F0B; }
.badge-outside   { background:#FCEBEB; color:#A32D2D; }
.badge-tp        { background:#EAF3DE; color:#3B6D11; }
.badge-fp        { background:#FCEBEB; color:#A32D2D; }
.badge-tn        { background:#E6F1FB; color:#185FA5; }
.badge-fn        { background:#FAEEDA; color:#854F0B; }
.badge-high      { background:#FCEBEB; color:#A32D2D; }
.badge-medium    { background:#FAEEDA; color:#854F0B; }
.badge-low       { background:#EAF3DE; color:#3B6D11; }
.callout-info { background:#EFF6FF; border-left:3px solid #3B82F6; border-radius:4px;
                padding:8px 12px; font-size:13px; color:#1D4ED8; margin:8px 0; }
.callout-warn { background:#FFFBEB; border-left:3px solid #F59E0B; border-radius:4px;
                padding:8px 12px; font-size:13px; color:#92400E; margin:8px 0; }
.audit-entry { padding:10px 0; border-bottom:1px solid #F3F4F6; font-size:13px; }
.audit-entry:last-child { border-bottom:none; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
init_session()

# ── Sidebar ────────────────────────────────────────────────────────────────────
pending_count = len(st.session_state.pending_ids)
source        = st.session_state.get("data_source", "csv")
pdi_url       = st.session_state.get("pdi_url", "")

with st.sidebar:
    st.markdown("### ◈ AI Portfolio Advisor")
    st.caption("Centaur Governance Model · Q1 2026")

    # Data source indicator
    if source == "live":
        st.markdown(f"""<div style="background:#EAF3DE;border-radius:6px;padding:6px 10px;
            font-size:11px;color:#3B6D11;margin:6px 0">
            ● Live · {pdi_url}</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#FEF3C7;border-radius:6px;padding:6px 10px;
            font-size:11px;color:#92400E;margin:6px 0">
            ● Demo mode · CSV data</div>""", unsafe_allow_html=True)

    st.divider()

    nav_labels = {
        "◫  Portfolio Overview":    "overview",
        "◈  AI Analysis & Signals": "analysis",
        f"◎  Validation Queue {'🔴' if pending_count else ''}": "validation",
        "◷  Decision Audit Log":    "audit",
        "◉  Governance Dashboard":  "governance",
        "⌖  Semantic CMDB Search":  "search",
    }

    selection = st.radio(
        "Navigate", list(nav_labels.keys()),
        label_visibility="collapsed",
    )
    page_key = nav_labels[selection]

    st.divider()
    st.caption("Cycle 3 — Q1 2026")
    st.caption(f"{pending_count} decision(s) pending")
    if pending_count:
        st.warning(f"{pending_count} app(s) awaiting review before Apr 30")

# ── Route ──────────────────────────────────────────────────────────────────────
if page_key == "overview":
    from pages.p1_overview import render; render()
elif page_key == "analysis":
    from pages.p2_analysis import render; render()
elif page_key == "validation":
    from pages.p3_validation import render; render()
elif page_key == "audit":
    from pages.p4_audit import render; render()
elif page_key == "governance":
    from pages.p5_governance import render; render()
elif page_key == "search":
    from pages.p6_search import render; render()
