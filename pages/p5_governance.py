"""
pages/p5_governance.py  —  Screen 5: Governance Dashboard
Cycle health, TP/FP accuracy tracking, SQDC metrics,
recommendation drift (non-determinism), and cycle history.
"""

import streamlit as st
import pandas as pd


CYCLE_DATA = {
    1: {"label": "Cycle 1 — Q3 2025", "tp": 6, "fp": 2, "tn": 1, "fn": 1,
        "apps_reviewed": 10, "overrides": 2, "escalations": 0, "closed": True},
    2: {"label": "Cycle 2 — Q4 2025", "tp": 8, "fp": 1, "tn": 2, "fn": 1,
        "apps_reviewed": 12, "overrides": 2, "escalations": 1, "closed": True},
}

SQDC = [
    {"dim": "Safety",   "score": 82, "delta": "+5", "note": "Regulatory risk apps identified and queued for retirement",  "color": "#639922"},
    {"dim": "Quality",  "score": 78, "delta": "+8", "note": "TP rate improving cycle-over-cycle; override rate declining",  "color": "#378ADD"},
    {"dim": "Delivery", "score": 71, "delta": "+3", "note": "Cycle review time reduced from 6 weeks to 3 weeks",           "color": "#EF9F27"},
    {"dim": "Cost",     "score": 65, "delta": "+12","note": "4 EOL apps queued for retirement — est. $733K annual savings","color": "#E24B4A"},
]

DRIFT_APPS = [
    {"name": "ERP Core",         "from_rec": "Retain",   "to_rec": "Replace",  "cycle": "1→2", "reason": "SAP EOL timeline accelerated"},
    {"name": "BIReportingSuite", "from_rec": "Modernize","to_rec": "Evaluate", "cycle": "2→3", "reason": "Duplicate BI capability discovered"},
    {"name": "ComplianceTracker","from_rec": "Retain",   "to_rec": "Modernize","cycle": "2→3", "reason": "CVE count increased significantly"},
]


def bar(score: int, color: str, max_w: int = 100) -> str:
    pct = int(score / max_w * 100)
    return f"""
    <div style="background:#F3F4F6;border-radius:4px;height:10px;overflow:hidden;flex:1">
      <div style="width:{pct}%;height:100%;background:{color};border-radius:4px"></div>
    </div>"""


def render():
    st.title("Governance Dashboard")
    st.caption("Cycle health · accuracy tracking · SQDC metrics · recommendation drift · continuous improvement")

    df   = st.session_state.apps_df
    log  = st.session_state.audit_log
    pend = st.session_state.pending_ids

    # ── Top KPI row ───────────────────────────────────────────────────────────
    cycle3_done  = [e for e in log if e["cycle"] == 3]
    cycle3_acted = len(cycle3_done)
    all_tp = sum(1 for e in log if e["tpfp"] == "TP")
    all_classified = sum(1 for e in log if e["tpfp"] in ("TP","FP","TN","FN"))
    overall_acc = f"{int(all_tp/all_classified*100)}%" if all_classified else "—"

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Current cycle",      "Cycle 3 — Q1 2026")
    with c2: st.metric("Open decisions",     len(pend),           delta=f"-{4-len(pend)} this cycle")
    with c3: st.metric("Overall TP accuracy",overall_acc,         help="True positive rate across all classified decisions")
    with c4: st.metric("Recommendation drift","3 apps",           help="Apps where AI recommendation changed between cycles")

    st.divider()

    # ── Row 1: TP/FP + SQDC ──────────────────────────────────────────────────
    col_acc, col_sqdc = st.columns(2)

    with col_acc:
        st.subheader("Accuracy tracking — TP / FP / TN / FN")

        cycle_tab = st.radio("Cycle", ["Cycle 1", "Cycle 2", "Cycle 3 (live)"],
                             horizontal=True, label_visibility="collapsed")

        if "Cycle 1" in cycle_tab:
            d = CYCLE_DATA[1]
        elif "Cycle 2" in cycle_tab:
            d = CYCLE_DATA[2]
        else:
            # Cycle 3 — build from live log
            tp = sum(1 for e in log if e["cycle"]==3 and e["tpfp"]=="TP")
            fp = sum(1 for e in log if e["cycle"]==3 and e["tpfp"]=="FP")
            tn = sum(1 for e in log if e["cycle"]==3 and e["tpfp"]=="TN")
            fn = sum(1 for e in log if e["cycle"]==3 and e["tpfp"]=="FN")
            d  = {"label":"Cycle 3 — Q1 2026 (in progress)",
                  "tp":tp,"fp":fp,"tn":tn,"fn":fn,
                  "apps_reviewed":cycle3_acted,"overrides":0,"escalations":0,"closed":False}

        total_cl = d["tp"]+d["fp"]+d["tn"]+d["fn"]
        accuracy  = int((d["tp"]+d["tn"])/total_cl*100) if total_cl else 0
        precision = int(d["tp"]/(d["tp"]+d["fp"])*100) if (d["tp"]+d["fp"]) else 0

        st.caption(d["label"])

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div style="background:#EAF3DE;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:24px;font-weight:600;color:#3B6D11">{d['tp']}</div>
              <div style="font-size:11px;color:#3B6D11">True positives</div></div>""",
                        unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div style="background:#FCEBEB;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:24px;font-weight:600;color:#A32D2D">{d['fp']}</div>
              <div style="font-size:11px;color:#A32D2D">False positives</div></div>""",
                        unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div style="background:#E6F1FB;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:24px;font-weight:600;color:#185FA5">{d['tn']}</div>
              <div style="font-size:11px;color:#185FA5">True negatives</div></div>""",
                        unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div style="background:#FAEEDA;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:24px;font-weight:600;color:#854F0B">{d['fn']}</div>
              <div style="font-size:11px;color:#854F0B">False negatives</div></div>""",
                        unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top:12px;padding:10px;background:#F9FAFB;border-radius:8px;
             display:flex;gap:20px;font-size:13px">
          <span>Accuracy: <strong>{accuracy}%</strong></span>
          <span>Precision: <strong>{precision}%</strong></span>
          <span>Apps reviewed: <strong>{d['apps_reviewed']}</strong></span>
          <span>Overrides: <strong>{d.get('overrides',0)}</strong></span>
        </div>""", unsafe_allow_html=True)

        # Trend note
        if "Cycle 2" in cycle_tab or "Cycle 3" in cycle_tab:
            st.markdown("""
            <div class="callout-info" style="margin-top:10px">
            Accuracy improved from 70% (Cycle 1) to 80% (Cycle 2).
            Override rate declined from 20% to 12.5%, indicating the signal model is strengthening.
            </div>""", unsafe_allow_html=True)

    with col_sqdc:
        st.subheader("SQDC metrics — portfolio impact")
        st.caption("Safety · Quality · Delivery · Cost — tracked run-over-run")

        for m in SQDC:
            st.markdown(f"""
            <div style="margin-bottom:10px">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
                <span style="font-size:13px;font-weight:500;width:70px;color:#111">{m['dim']}</span>
                {bar(m['score'], m['color'])}
                <span style="font-size:14px;font-weight:600;color:{m['color']};width:32px;text-align:right">{m['score']}</span>
                <span style="font-size:11px;color:#3B6D11;background:#EAF3DE;padding:1px 6px;border-radius:10px">{m['delta']}</span>
              </div>
              <div style="font-size:11px;color:#9CA3AF;padding-left:80px">{m['note']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:11px;color:#9CA3AF;margin-top:8px;font-style:italic">
        SQDC scores are composite indices (0–100) measuring portfolio impact across four dimensions.
        Delta shown vs. prior cycle. Tracked each bi-annual review.
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Row 2: Drift + Cycle history ──────────────────────────────────────────
    col_drift, col_hist = st.columns(2)

    with col_drift:
        st.subheader("Recommendation drift")
        st.caption("Apps where AI output changed between cycles — non-determinism flags")

        for d in DRIFT_APPS:
            from_bg  = {"Retain":"#EAF3DE","Modernize":"#FAEEDA","Retire":"#FCEBEB","Replace":"#FAEEDA","Evaluate":"#E6F1FB"}.get(d["from_rec"],"#F3F4F6")
            from_col = {"Retain":"#3B6D11","Modernize":"#854F0B","Retire":"#A32D2D","Replace":"#854F0B","Evaluate":"#185FA5"}.get(d["from_rec"],"#374151")
            to_bg    = {"Retain":"#EAF3DE","Modernize":"#FAEEDA","Retire":"#FCEBEB","Replace":"#FAEEDA","Evaluate":"#E6F1FB"}.get(d["to_rec"],"#F3F4F6")
            to_col   = {"Retain":"#3B6D11","Modernize":"#854F0B","Retire":"#A32D2D","Replace":"#854F0B","Evaluate":"#185FA5"}.get(d["to_rec"],"#374151")

            st.markdown(f"""
            <div style="padding:10px 0;border-bottom:1px solid #F3F4F6">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                <span style="font-size:13px;font-weight:500;color:#111;width:160px">{d['name']}</span>
                <span style="font-size:11px;padding:2px 8px;border-radius:10px;background:{from_bg};color:{from_col};text-decoration:line-through">{d['from_rec']}</span>
                <span style="color:#9CA3AF">→</span>
                <span style="font-size:11px;padding:2px 8px;border-radius:10px;background:{to_bg};color:{to_col};font-weight:600">{d['to_rec']}</span>
                <span style="font-size:10px;color:#9CA3AF;margin-left:auto">Cycles {d['cycle']}</span>
              </div>
              <div style="font-size:11px;color:#9CA3AF;padding-left:160px;font-style:italic">{d['reason']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="callout-warn" style="margin-top:12px">
        Per governance policy, drifted recommendations are automatically escalated for human review.
        Non-determinism is a documented risk in the AI Risk Assessment (Part B — Failure Mode Analysis).
        </div>""", unsafe_allow_html=True)

    with col_hist:
        st.subheader("Cycle history")

        cycle_rows = [
            {"cycle":"Cycle 1","period":"Q3 2025","reviewed":10,"overrides":2,"esc":0,"acc":"70%","status":"Complete"},
            {"cycle":"Cycle 2","period":"Q4 2025","reviewed":12,"overrides":2,"esc":1,"acc":"80%","status":"Complete"},
            {"cycle":"Cycle 3","period":"Q1 2026","reviewed":len(cycle3_done),"overrides":sum(1 for e in log if e["cycle"]==3 and e["human_decision"]=="Overridden"),
             "esc":sum(1 for e in log if e["cycle"]==3 and e["human_decision"]=="Escalated"),
             "acc":"—","status":"In progress"},
        ]

        for r in cycle_rows:
            status_bg  = "#EAF3DE" if r["status"]=="Complete" else "#FEF3C7"
            status_col = "#3B6D11" if r["status"]=="Complete" else "#92400E"
            st.markdown(f"""
            <div style="padding:10px;border:1px solid #E5E7EB;border-radius:8px;margin-bottom:8px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
                <span style="font-size:13px;font-weight:600;color:#111">{r['cycle']}</span>
                <span style="font-size:11px;padding:2px 10px;border-radius:10px;background:{status_bg};color:{status_col}">{r['status']}</span>
              </div>
              <div style="font-size:11px;color:#6B7280">{r['period']}</div>
              <div style="display:flex;gap:16px;margin-top:6px;font-size:12px">
                <span>Reviewed: <strong>{r['reviewed']}/15</strong></span>
                <span>Overrides: <strong>{r['overrides']}</strong></span>
                <span>Escalations: <strong>{r['esc']}</strong></span>
                <span>Accuracy: <strong>{r['acc']}</strong></span>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div class="callout-info" style="margin-top:8px">
        Governance checkpoint: bi-annual review cycle aligned to the framework in the AI Risk Assessment.
        Each cycle creates an auditable record of decisions and outcomes.
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Portfolio disposition summary ─────────────────────────────────────────
    st.subheader("Portfolio disposition — current cycle recommendations")

    rec_counts = df["_ai_recommendation"].value_counts()
    cols = st.columns(len(rec_counts))
    colors = {"Retain":"#EAF3DE","Modernize":"#FAEEDA","Retire":"#FCEBEB",
              "Replace":"#FAEEDA","Evaluate":"#E6F1FB"}
    text_colors = {"Retain":"#3B6D11","Modernize":"#854F0B","Retire":"#A32D2D",
                   "Replace":"#854F0B","Evaluate":"#185FA5"}

    for i, (rec, count) in enumerate(rec_counts.items()):
        cost = int(df[df["_ai_recommendation"]==rec]["u_annual_total_cost"].sum()/1000)
        with cols[i]:
            st.markdown(f"""
            <div style="background:{colors.get(rec,'#F3F4F6')};border-radius:10px;padding:14px;text-align:center">
              <div style="font-size:24px;font-weight:600;color:{text_colors.get(rec,'#374151')}">{count}</div>
              <div style="font-size:12px;font-weight:500;color:{text_colors.get(rec,'#374151')}">{rec}</div>
              <div style="font-size:11px;color:{text_colors.get(rec,'#374151')};opacity:0.8;margin-top:2px">${cost:,}K/yr</div>
            </div>""", unsafe_allow_html=True)
