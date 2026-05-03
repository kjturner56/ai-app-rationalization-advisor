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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* ── Sidebar — dark corporate nav ── */
[data-testid="stSidebar"] {
    background-color: #0F1923 !important;
    border-right: 1px solid #1E2D3D !important;
    min-width: 240px !important;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar nav buttons — invisible but clickable ── */
[data-testid="stSidebar"] .stButton > button {
    position: absolute !important;
    opacity: 0 !important;
    width: 100% !important;
    height: 36px !important;
    margin-top: -36px !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
    z-index: 10 !important;
}

/* ── Tighten nav item spacing ── */
[data-testid="stSidebar"] .stButton {
    margin: -12px 0 0 0 !important;
    padding: 0 !important;
    height: 0 !important;
    line-height: 0 !important;
    overflow: visible !important;
}

/* ── Hide Streamlit button tooltips ── */
[data-testid="stSidebar"] [data-testid="stTooltipHoverTarget"] {
    display: none !important;
}

/* ── Sidebar divider ── */
[data-testid="stSidebar"] hr {
    border-color: #1E2D3D !important;
    margin: 12px 0 !important;
}

/* ── Sidebar caption/small text ── */
[data-testid="stSidebar"] .stCaption p {
    color: #475569 !important;
    font-size: 11px !important;
    letter-spacing: 0.03em !important;
}

/* ── Sidebar warning ── */
[data-testid="stSidebar"] .stAlert {
    background: #1C1A0F !important;
    border: 1px solid #854F0B !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stAlert p {
    color: #FCD34D !important;
    font-size: 12px !important;
}

/* ── Main content area ── */
.block-container {
    padding-top: 1.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Page titles ── */
h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 24px !important;
    color: #0F1923 !important;
    letter-spacing: -0.02em !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: #64748B !important;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 600 !important;
    color: #0F1923 !important;
}

/* ── Main content buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    background: #FFFFFF !important;
    color: #0F1923 !important;
    padding: 6px 16px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #F1F5F9 !important;
    border-color: #94A3B8 !important;
}
.stButton > button[kind="primary"] {
    background: #1E3A5F !important;
    color: #FFFFFF !important;
    border-color: #1E3A5F !important;
}

/* ── Dataframe / tables ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #E2E8F0 !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 8px 20px !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: #1E3A5F !important;
    border-bottom-color: #1E3A5F !important;
}

/* ── Badges ── */
.badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 500;
    padding: 2px 10px;
    border-radius: 12px;
    white-space: nowrap;
    font-family: 'Inter', sans-serif;
    letter-spacing: 0.02em;
}
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

/* ── Callouts ── */
.callout-info {
    background: #EFF6FF;
    border-left: 3px solid #1E3A5F;
    border-radius: 0 4px 4px 0;
    padding: 10px 14px;
    font-size: 13px;
    color: #1E3A5F;
    margin: 8px 0;
    font-family: 'Inter', sans-serif;
}
.callout-warn {
    background: #FFFBEB;
    border-left: 3px solid #F59E0B;
    border-radius: 0 4px 4px 0;
    padding: 10px 14px;
    font-size: 13px;
    color: #92400E;
    margin: 8px 0;
    font-family: 'Inter', sans-serif;
}

/* ── Audit entries ── */
.audit-entry {
    padding: 10px 0;
    border-bottom: 1px solid #F3F4F6;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
}
.audit-entry:last-child { border-bottom: none; }

/* ── Select/multiselect ── */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background: #1E3A5F !important;
    border-radius: 4px !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
    color: #FFFFFF !important;
    font-size: 12px !important;
}
/* ── Hide sidebar collapse button and tooltip ── */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
init_session()

if "page_key" not in st.session_state:
    st.session_state.page_key = "overview"

# ── Sidebar ────────────────────────────────────────────────────────────────────
pending_count = len(st.session_state.pending_ids)
source        = st.session_state.get("data_source", "csv")
pdi_url       = st.session_state.get("pdi_url", "")

with st.sidebar:
    # App branding
    st.markdown("""
    <div style="padding: 8px 4px 16px 4px;">
        <div style="font-size:11px; font-weight:600; letter-spacing:0.1em;
                    text-transform:uppercase; color:#475569; margin-bottom:4px;">
            Portfolio Intelligence
        </div>
        <div style="font-size:16px; font-weight:600; color:#E2E8F0; letter-spacing:-0.01em;">
            AI Portfolio Advisor
        </div>
        <div style="font-size:11px; color:#475569; margin-top:2px;">
            Centaur Governance Model
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Data source indicator
    if source == "live":
        st.markdown(f"""
        <div style="background:#0D2137; border:1px solid #0F6E56; border-radius:6px;
                    padding:6px 10px; font-size:11px; color:#5DCAA5; margin-bottom:12px;
                    display:flex; align-items:center; gap:6px;">
            <span style="width:6px;height:6px;background:#5DCAA5;border-radius:50%;
                         display:inline-block;flex-shrink:0;"></span>
            Live · {pdi_url}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#1C1506; border:1px solid #854F0B; border-radius:6px;
                    padding:6px 10px; font-size:11px; color:#FCD34D; margin-bottom:12px;
                    display:flex; align-items:center; gap:6px;">
            <span style="width:6px;height:6px;background:#FCD34D;border-radius:50%;
                         display:inline-block;flex-shrink:0;"></span>
            Demo mode · CSV data
        </div>""", unsafe_allow_html=True)

    # Section label
    st.markdown("""
    <div style="font-size:10px; font-weight:600; letter-spacing:0.1em;
                text-transform:uppercase; color:#334155; padding: 4px 4px 6px 4px;">
        Navigation
    </div>""", unsafe_allow_html=True)

    # Nav items
    nav_items = [
        ("Portfolio Overview",    "overview",   ""),
        ("AI Analysis & Signals", "analysis",   ""),
        ("Validation Queue",      "validation", " ●" if pending_count else ""),
        ("Decision Audit Log",    "audit",      ""),
        ("Governance Dashboard",  "governance", ""),
        ("Semantic CMDB Search",  "search",     ""),
    ]

    for label, key, badge in nav_items:
        active     = st.session_state.page_key == key
        bg         = "#1E3A5F" if active else "#1E2D3D"
        color      = "#FFFFFF" if active else "#CBD5E1"
        badge_html = f'<span style="font-size:9px;color:#EF4444;margin-left:4px;">{badge}</span>' if badge else ""
        st.markdown(f"""
        <div style="padding:6px 12px;border-radius:6px;font-size:13px;font-weight:400;
                    background:{bg};color:{color};margin:0;position:relative;
                    cursor:pointer;font-family:Inter,sans-serif;">
            {label}{badge_html}
        </div>""", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}", use_container_width=True, help=""):
            st.session_state.page_key = key
            st.rerun()

    # Footer info
    st.markdown("""<div style="height:1px;background:#1E2D3D;margin:16px 0 12px 0;"></div>""",
                unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding: 0 4px;">
        <div style="font-size:11px; color:#334155; margin-bottom:4px;">
            Cycle 3 — Q1 2026
        </div>
        <div style="font-size:11px; color:#475569;">
            {pending_count} decision(s) pending
        </div>
    </div>""", unsafe_allow_html=True)

    if pending_count:
        st.markdown(f"""
        <div style="background:#1C1506; border:1px solid #854F0B; border-radius:6px;
                    padding:8px 10px; font-size:11px; color:#FCD34D; margin-top:10px;">
            ⚠ {pending_count} app(s) awaiting review before Apr 30
        </div>""", unsafe_allow_html=True)

# ── Route ──────────────────────────────────────────────────────────────────────
page_key = st.session_state.page_key

if page_key == "overview":
    from screens.p1_overview import render; render()
elif page_key == "analysis":
    from screens.p2_analysis import render; render()
elif page_key == "validation":
    from screens.p3_validation import render; render()
elif page_key == "audit":
    from screens.p4_audit import render; render()
elif page_key == "governance":
    from screens.p5_governance import render; render()
elif page_key == "search":
    from screens.p6_search import render; render()