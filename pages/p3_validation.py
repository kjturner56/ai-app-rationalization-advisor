"""
pages/p3_validation.py  —  Screen 3: Validation Queue
The Centaur model made visible. AI recommendations are pending —
nothing is final until a human acts. Override requires written rationale.
"""

import streamlit as st
from data_layer import record_decision, REC_BG, REC_COLORS


def render():
    st.title("Validation Queue")
    st.markdown("""
    <div class="callout-info">
    <strong>Centaur model — AI recommends, humans decide.</strong>
    No recommendation below is final until reviewed by the Application Portfolio Manager.
    Overrides require a written rationale. All actions are captured in the audit log.
    </div>""", unsafe_allow_html=True)

    df      = st.session_state.apps_df
    pending = st.session_state.pending_ids
    log     = st.session_state.audit_log

    # ── Role indicator ────────────────────────────────────────────────────────
    col_role, col_cycle = st.columns([3, 1])
    with col_role:
        actor_name = st.text_input(
            "Reviewer name (APM)",
            value="K. Turner — APM",
            help="Your name is captured on every action in the audit log",
        )
    with col_cycle:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<span class="badge badge-evaluate">Cycle 3 — Q1 2026</span>',
                    unsafe_allow_html=True)

    st.divider()

    # ── Pending items ─────────────────────────────────────────────────────────
    pending_apps = df[df["sys_id"].isin(pending)]

    if pending_apps.empty:
        st.success("All applications reviewed this cycle. Governance checkpoint complete.")
    else:
        st.subheader(f"Pending APM review  ({len(pending_apps)} remaining)")
        st.caption("Review each recommendation before the cycle closes on April 30.")

        for _, row in pending_apps.iterrows():
            app_id = row["sys_id"]
            rec    = row["_ai_recommendation"]
            conf   = int(row["_confidence"])
            life   = row["u_lifecycle_status"]
            debt   = int(row["u_technical_debt_score"])
            inc    = int(row.get("u_incident_volume_12m", 0))
            risk   = row.get("u_security_risk_level", "—")
            cost   = int(row["u_annual_total_cost"])
            frontier = row["_frontier"]

            conf_color  = "#3B6D11" if conf >= 80 else "#854F0B" if conf >= 60 else "#A32D2D"
            front_bg    = {"Inside": "#EAF3DE", "Edge": "#FAEEDA", "Outside": "#FCEBEB"}[frontier]
            front_color = {"Inside": "#3B6D11", "Edge": "#854F0B", "Outside": "#A32D2D"}[frontier]

            with st.container():
                st.markdown(f"""
                <div style="border:1px solid #E5E7EB;border-radius:10px;padding:16px;margin-bottom:16px;background:#FAFAFA">
                  <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px">
                    <div>
                      <span style="font-size:15px;font-weight:600;color:#111">{row['name']}</span>
                      <span style="font-size:12px;color:#9CA3AF;margin-left:8px">{app_id}</span><br>
                      <span style="font-size:12px;color:#6B7280">{row['business_unit']} · {row['vendor']} · {life}</span>
                    </div>
                    <div style="text-align:right">
                      <div style="background:{REC_BG.get(rec,'#F3F4F6')};color:{REC_COLORS.get(rec,'#374151')};
                           padding:5px 14px;border-radius:16px;font-weight:600;font-size:13px;margin-bottom:4px">
                        AI recommends: {rec}
                      </div>
                      <div style="font-size:11px;color:{conf_color}">Confidence: {conf}%</div>
                    </div>
                  </div>
                  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:10px">
                    <span style="font-size:12px;color:#6B7280">Tech debt: <strong style="color:#111">{debt}/100</strong></span>
                    <span style="font-size:12px;color:#6B7280">Incidents: <strong style="color:#111">{inc}</strong></span>
                    <span style="font-size:12px;color:#6B7280">Annual cost: <strong style="color:#111">${cost:,}</strong></span>
                    <span style="font-size:12px;color:#6B7280">Security: <strong style="color:#111">{risk}</strong></span>
                    <span style="font-size:11px;padding:2px 10px;border-radius:12px;background:{front_bg};color:{front_color}">
                      Frontier: {frontier}
                    </span>
                  </div>
                </div>""", unsafe_allow_html=True)

                # Action buttons + override form
                b1, b2, b3 = st.columns([1, 1, 1])
                with b1:
                    if st.button(f"✓ Approve", key=f"approve_{app_id}", type="primary",
                                 use_container_width=True):
                        record_decision(
                            app_id=app_id, app_name=row["name"],
                            ai_rec=rec, decision="Approved",
                            actor=actor_name, role="APM", rationale="",
                        )
                        st.success(f"{row['name']} approved.")
                        st.rerun()

                with b2:
                    show_override = st.toggle(f"Override", key=f"toggle_{app_id}")

                with b3:
                    if st.button(f"↑ Escalate to CIO", key=f"escalate_{app_id}",
                                 use_container_width=True):
                        record_decision(
                            app_id=app_id, app_name=row["name"],
                            ai_rec=rec, decision="Escalated",
                            actor=actor_name, role="APM",
                            rationale="Escalated to CIO — decision authority or timeline requires executive approval.",
                        )
                        st.warning(f"{row['name']} escalated to CIO.")
                        st.rerun()

                if show_override:
                    with st.container():
                        st.markdown("""
                        <div class="callout-warn">
                        Override requires a documented rationale. This is captured in the audit log
                        and supports post-outcome TP/FP classification.
                        </div>""", unsafe_allow_html=True)

                        new_rec = st.selectbox(
                            "Correct disposition",
                            ["Retain", "Modernize", "Retire", "Replace", "Evaluate"],
                            key=f"newrec_{app_id}",
                        )
                        rationale = st.text_area(
                            "Rationale for override (required)",
                            key=f"rationale_{app_id}",
                            placeholder="Explain why the AI recommendation is incorrect and what the right decision is...",
                            height=90,
                        )
                        if st.button("Submit override", key=f"submit_{app_id}", type="primary"):
                            if not rationale.strip():
                                st.error("Rationale is required. Overrides without documentation cannot be submitted.")
                            else:
                                record_decision(
                                    app_id=app_id, app_name=row["name"],
                                    ai_rec=rec, decision="Overridden",
                                    actor=actor_name, role="APM",
                                    rationale=f"Changed to {new_rec}. {rationale}",
                                )
                                st.success(f"Override recorded. {row['name']} → {new_rec}.")
                                st.rerun()

                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    st.divider()

    # ── Already actioned this cycle ───────────────────────────────────────────
    cycle3_done = [e for e in log if e["cycle"] == 3]
    if cycle3_done:
        st.subheader(f"Actioned this cycle  ({len(cycle3_done)})")
        for e in reversed(cycle3_done):
            dec_color = {"Approved": "#3B6D11", "Overridden": "#854F0B", "Escalated": "#4338CA"}.get(e["human_decision"], "#6B7280")
            dec_bg    = {"Approved": "#EAF3DE", "Overridden": "#FAEEDA", "Escalated": "#EEF2FF"}.get(e["human_decision"], "#F3F4F6")
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;padding:8px 0;
                 border-bottom:1px solid #F3F4F6;font-size:13px">
              <span style="font-weight:500;width:160px">{e['app_name']}</span>
              <span style="background:{REC_BG.get(e['ai_rec'],'#F3F4F6')};color:{REC_COLORS.get(e['ai_rec'],'#374151')};
                   padding:2px 10px;border-radius:12px;font-size:11px">{e['ai_rec']}</span>
              <span style="color:#9CA3AF">→</span>
              <span style="background:{dec_bg};color:{dec_color};padding:2px 10px;border-radius:12px;font-size:11px;font-weight:500">
                {e['human_decision']}
              </span>
              <span style="color:#9CA3AF;font-size:12px;margin-left:auto">{e['actor']} · {e['timestamp']}</span>
            </div>""", unsafe_allow_html=True)
            if e["rationale"]:
                st.markdown(f"<div style='font-size:11px;color:#6B7280;padding:2px 0 6px 172px;font-style:italic'>{e['rationale']}</div>",
                            unsafe_allow_html=True)
