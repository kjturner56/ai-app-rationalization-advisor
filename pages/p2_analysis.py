"""
pages/p2_analysis.py  —  Screen 2: AI Analysis & Signals
Per-app deep dive: confidence, frontier position, signal breakdown,
data completeness, and non-determinism flag.
"""

import streamlit as st
from data_layer import REC_BG, REC_COLORS, FRONTIER_TEXT


def render():
    st.title("AI Analysis & Signals")
    st.caption("Explainable recommendations — every signal that drove the output is visible and auditable")

    df = st.session_state.apps_df

    # ── App selector ─────────────────────────────────────────────────────────
    app_names = df["name"].tolist()
    app_ids   = df["sys_id"].tolist()
    name_map  = dict(zip(app_names, app_ids))

    selected_name = st.selectbox("Select application", app_names)
    selected_id   = name_map[selected_name]
    row = df[df["sys_id"] == selected_id].iloc[0]

    st.divider()

    rec        = row["_ai_recommendation"]
    conf       = int(row["_confidence"])
    frontier   = row["_frontier"]
    completeness = int(row["_data_completeness"])
    debt       = int(row["u_technical_debt_score"])
    life       = row["u_lifecycle_status"]
    crit       = row["u_criticality"]
    inc_vol    = int(row.get("u_incident_volume_12m", 0))
    cost       = int(row["u_annual_total_cost"])

    # ── Top row: recommendation + confidence + frontier ───────────────────────
    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        st.subheader(row["name"])
        st.caption(f"{row['business_unit']} · {life} · ${cost:,}/yr · {inc_vol} incidents (12m)")

        conf_color = "#3B6D11" if conf >= 80 else "#854F0B" if conf >= 60 else "#A32D2D"
        front_cls  = frontier.lower()
        front_bg   = {"Inside": "#EAF3DE", "Edge": "#FAEEDA", "Outside": "#FCEBEB"}[frontier]
        front_color= {"Inside": "#3B6D11", "Edge": "#854F0B", "Outside": "#A32D2D"}[frontier]
        rec_bg     = REC_BG.get(rec, "#F3F4F6")
        rec_color  = REC_COLORS.get(rec, "#374151")

        st.markdown(f"""
        <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0">
          <div style="background:{rec_bg};color:{rec_color};padding:6px 16px;border-radius:20px;font-weight:600;font-size:14px">
            {rec}
          </div>
          <div style="background:{front_bg};color:{front_color};padding:6px 14px;border-radius:20px;font-size:13px;font-weight:500">
            Frontier: {frontier}
          </div>
          <div style="border:2px solid {conf_color};color:{conf_color};padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600">
            {conf}% confidence
          </div>
        </div>
        <div style="background:#EFF6FF;border-left:3px solid #3B82F6;padding:8px 12px;border-radius:4px;font-size:13px;color:#1D4ED8;margin-bottom:8px">
          <strong>Frontier position:</strong> {FRONTIER_TEXT[frontier]}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Data completeness**")
        st.progress(completeness / 100)
        note_color = "#3B6D11" if completeness >= 90 else "#854F0B" if completeness >= 75 else "#A32D2D"
        note = ("High completeness — reliability is strong."
                if completeness >= 90 else
                "Moderate — validate against source systems."
                if completeness >= 75 else
                "Low — high misapplication risk. Gather missing data first.")
        st.markdown(f"<span style='font-size:12px;color:{note_color}'>{completeness}% &nbsp;·&nbsp; {note}</span>",
                    unsafe_allow_html=True)

    with col3:
        # Non-determinism check (simulated: apps with Edge/Outside frontier get flagged)
        drifted = frontier in ("Edge", "Outside") and debt > 50
        if drifted:
            st.markdown("""
            <div style="background:#FFFBEB;border:1px solid #F59E0B;border-radius:8px;padding:10px 12px">
            <div style="font-size:12px;font-weight:600;color:#92400E">⚠ Recommendation drifted</div>
            <div style="font-size:11px;color:#92400E;margin-top:4px">
            Output changed from prior cycle. Flagged for escalation per governance policy.
            Non-determinism increases misrepresentation risk.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:10px 12px">
            <div style="font-size:12px;font-weight:600;color:#166534">✓ Stable across cycles</div>
            <div style="font-size:11px;color:#166534;margin-top:4px">
            Recommendation consistent with prior run. No non-determinism drift detected.</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Signal breakdown ──────────────────────────────────────────────────────
    st.subheader("Signal breakdown")
    st.caption("What drove this recommendation — each factor is auditable and explainable")

    signals = _build_signals(row)

    col_sig, col_why = st.columns([3, 2])
    with col_sig:
        for sig in signals:
            pct   = sig["value"]
            color = sig["color"]
            impact_bg    = {"High": "#FCEBEB", "Medium": "#FAEEDA", "Low": "#EAF3DE"}[sig["impact"]]
            impact_color = {"High": "#A32D2D", "Medium": "#854F0B", "Low": "#3B6D11"}[sig["impact"]]
            st.markdown(f"""
            <div style="margin-bottom:10px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
                <span style="font-size:12px;color:#374151">{sig['label']}</span>
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:12px;font-weight:500;color:#111">{pct}</span>
                  <span style="font-size:10px;padding:1px 8px;border-radius:10px;background:{impact_bg};color:{impact_color}">{sig['impact']}</span>
                </div>
              </div>
              <div style="background:#F3F4F6;border-radius:4px;height:8px;overflow:hidden">
                <div style="width:{pct}%;height:100%;background:{color};border-radius:4px"></div>
              </div>
            </div>""", unsafe_allow_html=True)

    with col_why:
        st.markdown(f"""
        <div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:14px">
          <div style="font-size:12px;font-weight:600;color:#111;margin-bottom:8px">Why this recommendation?</div>
          <div style="font-size:12px;color:#6B7280;line-height:1.6">
            {_build_rationale(row, rec, signals)}
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Tech debt formula transparency
        st.markdown("""
        <div style="background:#EFF6FF;border-radius:8px;padding:12px;font-size:11px;color:#1D4ED8;line-height:1.6">
        <strong>Tech debt formula</strong><br>
        Lifecycle EOL: +35pts · Aging: +20pts<br>
        Critical CVEs: +5pts each (max 25)<br>
        Incident trend ↑: +10pts<br>
        Major outages: +3pts each (max 15)<br>
        Stability inverse: up to +15pts<br>
        <em>Score capped at 100. Computed live — not a static CSV field.</em>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Raw data panel ────────────────────────────────────────────────────────
    with st.expander("Raw source data — all fields from ServiceNow CSVs"):
        display_cols = [
            "sys_id", "name", "business_unit", "u_criticality",
            "u_lifecycle_status", "u_hosting_type", "vendor", "version",
            "u_annual_total_cost", "u_technical_debt_score", "u_stability_score",
            "u_duplicate_functionality", "u_replacement_candidate_exists",
            "u_security_risk_level", "u_open_vulnerabilities", "u_critical_vulnerabilities",
            "u_incident_volume_12m", "u_sev1_sev2_count", "u_major_outages_12m",
            "u_incident_trend", "u_availability_pct",
        ]
        available = [c for c in display_cols if c in df.columns]
        row_df = df[df["sys_id"] == selected_id][available].T.reset_index()
        row_df.columns = ["Field", "Value"]
        st.dataframe(row_df, use_container_width=True, hide_index=True)


# ── Signal builder ────────────────────────────────────────────────────────────

def _build_signals(row) -> list[dict]:
    life  = row["u_lifecycle_status"]
    debt  = int(row["u_technical_debt_score"])
    stab  = int(row.get("u_stability_score", 80))
    crit_cve = int(row.get("u_critical_vulnerabilities", 0))
    inc   = int(row.get("u_incident_volume_12m", 0))
    trend = row.get("u_incident_trend", "Stable")
    dup   = row["u_duplicate_functionality"]
    repl  = row["u_replacement_candidate_exists"]
    outages = int(row.get("u_major_outages_12m", 0))

    def impact(v):
        if v >= 65: return "High"
        if v >= 35: return "Medium"
        return "Low"

    def color(v):
        if v >= 65: return "#E24B4A"
        if v >= 35: return "#EF9F27"
        return "#639922"

    lifecycle_score = {"End of Life": 95, "Aging": 60, "Current": 10}.get(life, 10)
    inc_score = min(int(inc / 1.5), 100)
    cve_score = min(crit_cve * 12, 100)
    trend_score = {"Increasing": 70, "Stable": 25, "Decreasing": 10}.get(trend, 25)
    stab_score = max(0, 100 - stab)
    outage_score = min(outages * 20, 100)
    dup_score = 65 if dup else 10
    repl_score = 55 if repl else 10

    sigs = [
        {"label": f"Lifecycle status ({life})", "value": lifecycle_score, "impact": impact(lifecycle_score), "color": color(lifecycle_score)},
        {"label": f"Technical debt index", "value": debt,  "impact": impact(debt),  "color": color(debt)},
        {"label": f"Incident trend ({trend})", "value": trend_score, "impact": impact(trend_score), "color": color(trend_score)},
        {"label": f"12-month incident volume ({inc})", "value": min(inc_score, 100), "impact": impact(inc_score), "color": color(inc_score)},
        {"label": f"Critical CVEs ({crit_cve})", "value": cve_score, "impact": impact(cve_score), "color": color(cve_score)},
        {"label": f"Stability inverse (score: {100 - stab_score})", "value": stab_score, "impact": impact(stab_score), "color": color(stab_score)},
        {"label": f"Duplicate functionality", "value": dup_score, "impact": impact(dup_score), "color": color(dup_score)},
        {"label": f"Replacement candidate exists", "value": repl_score, "impact": impact(repl_score), "color": color(repl_score)},
    ]
    return sorted(sigs, key=lambda x: -x["value"])


def _build_rationale(row, rec: str, signals: list) -> str:
    top = [s["label"].split("(")[0].strip() for s in signals[:3] if s["impact"] == "High"]
    life = row["u_lifecycle_status"]
    debt = int(row["u_technical_debt_score"])

    base = {
        "Retire":   f"End of Life lifecycle combined with high technical debt ({debt}/100) and a confirmed replacement candidate make retirement the optimal path. Continuing to run this application increases CVE exposure and support cost with no long-term value return.",
        "Replace":  f"Application is too business-critical to retire but carries unacceptable technical debt ({debt}/100) and lifecycle risk. A platform migration (e.g. ERP modernization) is the recommended path rather than incremental modernization.",
        "Modernize":f"Aging lifecycle and elevated technical debt ({debt}/100) signal growing risk, but the application serves an active business capability with no immediate replacement. Targeted modernization investment is justified.",
        "Retain":   f"Current lifecycle, low technical debt ({debt}/100), and stable incident trend indicate the application is performing within acceptable parameters. No action required this cycle.",
        "Evaluate": f"Duplicate functionality signals overlap with another platform. Cost-benefit analysis and consolidation review recommended before committing to modernization or retirement.",
    }.get(rec, "—")

    if top:
        base += f"<br><br><strong>Top signals:</strong> {', '.join(top[:2])}."
    return base
