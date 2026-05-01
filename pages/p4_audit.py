"""
pages/p4_audit.py  —  Screen 4: Decision Audit Log
Full timestamped, filterable record of every human decision.
Supports compliance review and TP/FP classification.
"""

import streamlit as st
import pandas as pd
from data_layer import REC_BG, REC_COLORS


def render():
    st.title("Decision Audit Log")
    st.caption("Every action captured — AI recommendation, human decision, rationale, actor, timestamp")

    st.markdown("""
    <div class="callout-info">
    This log supports regulatory compliance review. Every override includes documented rationale
    captured at decision time. TP/FP classification is applied post-outcome during the governance review.
    </div>""", unsafe_allow_html=True)

    log = st.session_state.audit_log

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        dec_filter = st.selectbox(
            "Filter by decision",
            ["All decisions", "Approved", "Overridden", "Escalated"],
        )
    with col2:
        cycle_filter = st.selectbox(
            "Filter by cycle",
            ["All cycles", "Cycle 1", "Cycle 2", "Cycle 3"],
        )
    with col3:
        tpfp_filter = st.selectbox(
            "Filter by classification",
            ["All", "TP", "FP", "TN", "FN", "Unclassified (—)"],
        )

    filtered = log
    if dec_filter != "All decisions":
        filtered = [e for e in filtered if e["human_decision"] == dec_filter]
    if cycle_filter != "All cycles":
        c = int(cycle_filter.split()[1])
        filtered = [e for e in filtered if e["cycle"] == c]
    if tpfp_filter != "All":
        tpfp_val = "—" if tpfp_filter == "Unclassified (—)" else tpfp_filter
        filtered = [e for e in filtered if e["tpfp"] == tpfp_val]

    st.caption(f"Showing {len(filtered)} of {len(log)} entries")
    st.divider()

    # ── Summary stats ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    total      = len(log)
    approved   = sum(1 for e in log if e["human_decision"] == "Approved")
    overridden = sum(1 for e in log if e["human_decision"] == "Overridden")
    escalated  = sum(1 for e in log if e["human_decision"] == "Escalated")
    tp_count   = sum(1 for e in log if e["tpfp"] == "TP")

    with c1: st.metric("Total decisions", total)
    with c2: st.metric("Approved", approved)
    with c3: st.metric("Overridden", overridden, help="Each override has a documented rationale")
    with c4: st.metric("Escalated", escalated)
    with c5: st.metric("True positives", tp_count)

    st.divider()

    # ── Log entries ───────────────────────────────────────────────────────────
    DEC_STYLE = {
        "Approved":  ("background:#EAF3DE;color:#3B6D11",),
        "Overridden":("background:#FAEEDA;color:#854F0B",),
        "Escalated": ("background:#EEF2FF;color:#4338CA",),
    }
    TPFP_STYLE = {
        "TP": "background:#EAF3DE;color:#3B6D11",
        "FP": "background:#FCEBEB;color:#A32D2D",
        "TN": "background:#E6F1FB;color:#185FA5",
        "FN": "background:#FAEEDA;color:#854F0B",
        "—":  "background:#F3F4F6;color:#9CA3AF",
    }

    for e in reversed(filtered):
        dec_style  = DEC_STYLE.get(e["human_decision"], ("background:#F3F4F6;color:#374151",))[0]
        tpfp_style = TPFP_STYLE.get(e["tpfp"], TPFP_STYLE["—"])
        rec_bg     = REC_BG.get(e["ai_rec"], "#F3F4F6")
        rec_color  = REC_COLORS.get(e["ai_rec"], "#374151")
        cycle_badge = f"Cycle {e['cycle']}"

        st.markdown(f"""
        <div class="audit-entry">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:5px">
            <span style="font-size:11px;color:#9CA3AF;min-width:110px">{e['timestamp']}</span>
            <span style="font-weight:600;font-size:13px;color:#111">{e['app_name']}</span>
            <span style="font-size:10px;color:#9CA3AF">{e['app_id']}</span>
            <span style="font-size:10px;padding:1px 8px;border-radius:10px;background:#F3F4F6;color:#6B7280">{cycle_badge}</span>
            <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
              <span style="font-size:11px;padding:2px 10px;border-radius:12px;background:{rec_bg};color:{rec_color}">AI: {e['ai_rec']}</span>
              <span style="font-size:11px">→</span>
              <span style="font-size:11px;padding:2px 10px;border-radius:12px;{dec_style};font-weight:500">{e['human_decision']}</span>
              <span style="font-size:10px;padding:1px 8px;border-radius:10px;{tpfp_style};font-weight:500">{e['tpfp']}</span>
            </div>
          </div>
          <div style="display:flex;gap:12px;padding-left:110px">
            <span style="font-size:12px;color:#6B7280">Actor: <strong style="color:#374151">{e['actor']}</strong></span>
            {f'<span style="font-size:12px;color:#6B7280;font-style:italic">"{e["rationale"][:120]}{"…" if len(e["rationale"])>120 else ""}"</span>' if e["rationale"] else ''}
          </div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Export ────────────────────────────────────────────────────────────────
    if st.button("Export audit log as CSV"):
        df_export = pd.DataFrame(log)
        csv = df_export.to_csv(index=False)
        st.download_button(
            label="Download audit_log.csv",
            data=csv,
            file_name="audit_log.csv",
            mime="text/csv",
        )
