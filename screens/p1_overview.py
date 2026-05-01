"""
pages/p1_overview.py  —  Screen 1: Portfolio Overview
Executive entry point. KPI cards + full app table.
"""

import streamlit as st
import pandas as pd
from data_layer import (
    load_dependencies, load_capabilities,
    REC_COLORS, REC_BG, LIFECYCLE_COLORS, CRIT_COLORS,
)


def badge(text: str, cls: str) -> str:
    return f'<span class="badge badge-{cls}">{text}</span>'


def render():
    st.title("Portfolio Overview")
    st.caption("15 applications · Enterprise rationalization cycle · Q1 2026")

    df   = st.session_state.apps_df
    pend = st.session_state.pending_ids
    log  = st.session_state.audit_log

    # ── KPI cards ────────────────────────────────────────────────────────────
    eol_count  = int((df["u_lifecycle_status"] == "End of Life").sum())
    total_cost = df["u_annual_total_cost"].sum()
    retire_count = int((df["_ai_recommendation"].isin(["Retire", "Replace"])).sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("At-Risk Apps", eol_count, help="Apps with End of Life lifecycle status")
    with c2:
        st.metric("Portfolio TCO", f"${total_cost/1_000_000:.1f}M", help="Total annual cost across all 15 apps")
    with c3:
        st.metric("Pending Decisions", len(pend), help="Awaiting APM review this cycle")
    with c4:
        tp = sum(1 for e in log if e["tpfp"] == "TP")
        total_classified = sum(1 for e in log if e["tpfp"] in ("TP","FP","TN","FN"))
        accuracy = f"{int(tp/total_classified*100)}%" if total_classified else "—"
        st.metric("Cycle Accuracy", accuracy, help="True positive rate across completed cycles")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        life_filter = st.multiselect(
            "Lifecycle", ["Current", "Aging", "End of Life"],
            default=["Current", "Aging", "End of Life"],
        )
    with col_f2:
        rec_filter = st.multiselect(
            "AI Recommendation", ["Retain", "Modernize", "Retire", "Replace", "Evaluate"],
            default=["Retain", "Modernize", "Retire", "Replace", "Evaluate"],
        )
    with col_f3:
        unit_filter = st.multiselect(
            "Business Unit", sorted(df["business_unit"].unique()),
            default=list(df["business_unit"].unique()),
        )

    filtered = df[
        df["u_lifecycle_status"].isin(life_filter) &
        df["_ai_recommendation"].isin(rec_filter) &
        df["business_unit"].isin(unit_filter)
    ]

    st.caption(f"Showing {len(filtered)} of {len(df)} applications")

    # ── App table ─────────────────────────────────────────────────────────────
    rows_html = ""
    for _, row in filtered.iterrows():
        app_id   = row["sys_id"]
        rec      = row["_ai_recommendation"]
        life     = row["u_lifecycle_status"]
        crit     = row["u_criticality"]
        cost     = row["u_annual_total_cost"]
        inc      = int(row.get("u_incident_volume_12m", 0))
        debt     = int(row["u_technical_debt_score"])
        status   = "Pending" if app_id in pend else "Reviewed"
        status_cls = "pending" if status == "Pending" else "approved"

        life_color = LIFECYCLE_COLORS.get(life, "#6B7280")
        inc_color  = "#A32D2D" if inc > 80 else "#854F0B" if inc > 40 else "#374151"
        debt_color = "#A32D2D" if debt > 70 else "#854F0B" if debt > 40 else "#3B6D11"

        rows_html += f"""
        <tr style="border-bottom:1px solid #F3F4F6;">
          <td style="padding:9px 8px;font-weight:500;font-size:13px">{row['name']}
            <br><span style="font-size:10px;color:#9CA3AF">{app_id}</span></td>
          <td style="padding:9px 8px;font-size:12px;color:#6B7280">{row['business_unit']}</td>
          <td style="padding:9px 8px">
            <span style="font-size:11px;font-weight:500;color:{CRIT_COLORS.get(crit,'#374151')}">{crit}</span>
          </td>
          <td style="padding:9px 8px">
            <span style="font-size:11px;color:{life_color}">{life}</span>
          </td>
          <td style="padding:9px 8px;font-size:12px;font-weight:500">${int(cost):,}</td>
          <td style="padding:9px 8px;font-size:12px;color:{inc_color}">{inc}</td>
          <td style="padding:9px 8px;font-size:12px;color:{debt_color};font-weight:500">{debt}</td>
          <td style="padding:9px 8px">{badge(rec, rec.lower())}</td>
          <td style="padding:9px 8px">{badge(status, status_cls)}</td>
        </tr>"""

    table_html = f"""
    <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
      <thead>
        <tr style="border-bottom:2px solid #E5E7EB;background:#F9FAFB">
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Application</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Business Unit</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Criticality</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Lifecycle</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Annual Cost</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Incidents 12m</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Tech Debt</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">AI Recommendation</th>
          <th style="text-align:left;padding:8px;font-size:11px;color:#6B7280;font-weight:500;text-transform:uppercase;letter-spacing:.05em">Status</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>"""

    st.markdown(table_html, unsafe_allow_html=True)

    # ── Portfolio story callout ───────────────────────────────────────────────
    st.divider()
    retire_apps = df[df["_ai_recommendation"].isin(["Retire","Replace"])]["name"].tolist()
    modernize_apps = df[df["_ai_recommendation"] == "Modernize"]["name"].tolist()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="callout-warn">
        <strong>Retire / Replace ({len(retire_apps)} apps):</strong><br>
        {', '.join(retire_apps)}<br>
        <small>These carry the highest incident volume, CVE counts, and support cost. Combined annual spend: 
        ${int(df[df['_ai_recommendation'].isin(['Retire','Replace'])]['u_annual_total_cost'].sum()/1000):,}K</small>
        </div>""", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="callout-info">
        <strong>Modernize ({len(modernize_apps)} apps):</strong><br>
        {', '.join(modernize_apps)}<br>
        <small>Aging lifecycle but business-critical. Upgrade path exists. 
        Combined annual spend: ${int(df[df['_ai_recommendation']=='Modernize']['u_annual_total_cost'].sum()/1000):,}K</small>
        </div>""", unsafe_allow_html=True)
