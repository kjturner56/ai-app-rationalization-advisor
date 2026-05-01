"""
pages/p6_search.py  —  Screen 6: Semantic CMDB Search
Conversational AI advisor powered by Claude API.

Access control (two layers):
  1. Password gate  — user must enter the access key from secrets.toml
                      before the AI interface is shown. Screens 1-5 remain
                      fully public; only the API-consuming screen is gated.
  2. Session call limit — caps API calls per browser session so a single
                      visitor cannot run up an unlimited bill.

secrets.toml additions required:
  [anthropic]
  api_key = "sk-ant-..."

  [app]
  access_key = "your-chosen-passphrase"   # share selectively with interviewers
  max_calls  = 20                          # per-session API call cap (default 20)
"""

import streamlit as st
import requests
import pandas as pd
from data_layer import REC_BG, REC_COLORS


# ── Session state keys ─────────────────────────────────────────────────────────
SESSION_KEY    = "s6_authenticated"   # bool — has this session passed the gate?
CALL_COUNT_KEY = "s6_api_calls"       # int  — calls made this session


# ── Suggested prompts ──────────────────────────────────────────────────────────
SUGGESTED_PROMPTS = [
    "Which apps should we retire first and in what order?",
    "What's the total cost of all End of Life applications?",
    "Show me all high-criticality apps that are aging or end of life",
    "Which Finance apps carry the most security risk?",
    "Explain the dependency risk if we retire LegacyDB",
    "Compare ERP Core and DataWarehouse — which is a higher priority to modernize?",
    "What would the annual savings be if we retired all recommended apps?",
    "Which apps are most likely to have an outage in the next 6 months?",
]


# ── Access control helpers ─────────────────────────────────────────────────────

def _get_access_key() -> str:
    """Return configured access key, or empty string if not set (open/dev mode)."""
    try:
        return st.secrets.get("app", {}).get("access_key", "")
    except Exception:
        return ""


def _get_max_calls() -> int:
    try:
        return int(st.secrets.get("app", {}).get("max_calls", 20))
    except Exception:
        return 20


def _get_api_key() -> str | None:
    try:
        return st.secrets.get("anthropic", {}).get("api_key")
    except Exception:
        return None


def _check_access() -> bool:
    """
    Layer 1 — password gate.
    Returns True if access is granted for this session, False if still blocked.
    If no access_key is configured (local dev), access is always granted.
    """
    if st.session_state.get(SESSION_KEY):
        return True

    configured_key = _get_access_key()

    # No key configured — open access (local / dev mode)
    if not configured_key:
        st.session_state[SESSION_KEY] = True
        return True

    # Show gate UI
    st.markdown("""
    <div style="max-width:460px;margin:48px auto;padding:32px 36px;
         border:1px solid #E5E7EB;border-radius:12px;background:#FAFAFA;
         box-shadow:0 1px 4px rgba(0,0,0,.06)">
      <div style="font-size:20px;font-weight:600;color:#1F3864;margin-bottom:4px">
        ◈ Semantic CMDB Search
      </div>
      <div style="font-size:13px;color:#6B7280;margin-bottom:24px;line-height:1.6">
        This screen calls the Anthropic API and is access-controlled.<br>
        Contact the demo owner to request an access key.
      </div>
    </div>""", unsafe_allow_html=True)

    entered = st.text_input(
        "Access key",
        type="password",
        placeholder="Enter access key…",
        label_visibility="collapsed",
    )

    if entered:
        if entered == configured_key:
            st.session_state[SESSION_KEY] = True
            st.session_state[CALL_COUNT_KEY] = 0
            st.rerun()
        else:
            st.error("Incorrect access key. Contact the demo owner for access.")

    st.caption(
        "Screens 1–5 (Portfolio Overview, Analysis, Validation Queue, "
        "Audit Log, Governance Dashboard) are fully accessible without a key."
    )
    return False


def _within_call_limit() -> bool:
    """
    Layer 2 — per-session call cap.
    Returns True if the session still has API budget remaining.
    """
    max_calls  = _get_max_calls()
    call_count = st.session_state.get(CALL_COUNT_KEY, 0)
    remaining  = max_calls - call_count

    if call_count >= max_calls:
        st.warning(
            f"You've reached the {max_calls}-query session limit. "
            "Reload the page to start a new session.",
            icon="⚠️",
        )
        st.caption(
            "This per-session limit prevents uncontrolled API consumption on a shared "
            "deployment. In production this would be replaced by user-level quota management "
            "tied to SSO identity."
        )
        return False

    # Soft warning when getting close
    if remaining <= 3:
        st.info(f"{remaining} AI quer{'y' if remaining==1 else 'ies'} remaining this session.", icon="ℹ️")

    return True


def _increment_call_count():
    st.session_state[CALL_COUNT_KEY] = st.session_state.get(CALL_COUNT_KEY, 0) + 1


# ── Portfolio context builder ──────────────────────────────────────────────────

def _build_portfolio_context(df: pd.DataFrame) -> str:
    lines = ["ENTERPRISE APPLICATION PORTFOLIO — 15 APPLICATIONS\n"]
    lines.append(
        f"Source: {st.session_state.get('data_source','csv').upper()} "
        f"({'ServiceNow PDI: ' + st.session_state.get('pdi_url','') if st.session_state.get('data_source')=='live' else 'CSV fallback'})\n"
    )

    for _, row in df.iterrows():
        lines.append(
            f"APP: {row['name']} ({row['sys_id']})\n"
            f"  Business Unit: {row['business_unit']} | Criticality: {row['u_criticality']}\n"
            f"  Lifecycle: {row['u_lifecycle_status']} | Hosting: {row.get('u_hosting_type','—')}\n"
            f"  Vendor: {row.get('vendor','—')} {row.get('version','')}\n"
            f"  Annual Cost: ${int(row.get('u_annual_total_cost',0)):,} "
            f"(License: ${int(row.get('u_annual_license_cost',0)):,} | "
            f"Infra: ${int(row.get('u_infrastructure_cost',0)):,} | "
            f"Support: ${int(row.get('u_support_labor_cost',0)):,})\n"
            f"  Users: {int(row.get('u_user_count',0)):,}\n"
            f"  Tech Debt Score: {int(row.get('u_technical_debt_score',0))}/100 | "
            f"Stability: {int(row.get('u_stability_score',0))}/100\n"
            f"  Security Risk: {row.get('u_security_risk_level','—')} | "
            f"Open CVEs: {int(row.get('u_open_vulnerabilities',0))} | "
            f"Critical CVEs: {int(row.get('u_critical_vulnerabilities',0))}\n"
            f"  Incidents (12m): {int(row.get('u_incident_volume_12m',0))} | "
            f"Trend: {row.get('u_incident_trend','—')} | "
            f"Major Outages: {int(row.get('u_major_outages_12m',0))}\n"
            f"  Duplicate Functionality: {row.get('u_duplicate_functionality',False)} | "
            f"Replacement Exists: {row.get('u_replacement_candidate_exists',False)}\n"
            f"  AI Recommendation: {row.get('_ai_recommendation','—')} | "
            f"Confidence: {int(row.get('_confidence',0))}% | "
            f"Frontier: {row.get('_frontier','—')}\n"
        )

    log = st.session_state.get("audit_log", [])
    overrides = [e for e in log if e["human_decision"] == "Overridden"]
    lines.append(f"\nGOVERNANCE CONTEXT:")
    lines.append(f"  Current cycle: Cycle 3 — Q1 2026")
    lines.append(f"  Total decisions logged: {len(log)}")
    lines.append(f"  Overrides (with rationale): {len(overrides)}")
    lines.append(f"  Pending decisions: {len(st.session_state.get('pending_ids', set()))}")
    for e in overrides:
        lines.append(
            f"  Override: {e['app_name']} — AI said {e['ai_rec']}, "
            f"human changed disposition. Reason: {e['rationale'][:80]}"
        )
    return "\n".join(lines)


def _build_system_prompt(context: str) -> str:
    return f"""You are an AI decision-support advisor embedded in an enterprise Application Portfolio Rationalization tool. You help Application Portfolio Managers, CIOs, and enterprise architects make better decisions about their IT application portfolio.

GOVERNANCE FRAMEWORK:
- This tool follows a Centaur model: AI recommends, humans validate and decide.
- You are the analytical layer. You surface patterns, explain signals, and help humans make better decisions — you do not make final decisions yourself.
- Always frame recommendations as inputs to human judgment, not final verdicts.
- Acknowledge uncertainty where it exists. Flag when confidence is low or data completeness is poor.
- Reference the jagged technological frontier concept where relevant.

PORTFOLIO DATA (use this as your source of truth):
{context}

RESPONSE STYLE:
- Be direct and analytical. Enterprise stakeholders want conclusions, not hedging.
- Use specific numbers from the data. Don't speak in generalities when you have the actual figures.
- When ranking or sequencing, explain the specific factors that drive the ordering.
- Keep responses concise but complete. Bullet points are fine for lists.
- If asked about something not in the data, say so clearly rather than guessing."""


def _call_claude(messages: list, system: str, api_key: str) -> str:
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "system": system,
                "messages": messages,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
        return f"API error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"Connection error: {str(e)}"


# ── Main render ────────────────────────────────────────────────────────────────

def render():
    st.title("Semantic CMDB Search")
    st.caption("Conversational AI advisor — ask anything about the portfolio")

    # ── Layer 1: password gate ─────────────────────────────────────────────────
    if not _check_access():
        return   # gate is showing — stop rendering the rest of the screen
# ── Process pending user message (from suggested prompt buttons) ───────────
    if (st.session_state.chat_history and
            st.session_state.chat_history[-1]["role"] == "user" and
            not st.session_state.get("s6_processing", False)):
        st.session_state.s6_processing = True
        pending = st.session_state.chat_history[-1]["content"]
        api_key = _get_api_key()
        if api_key and _within_call_limit():
            with st.chat_message("assistant"):
                with st.spinner("Analyzing portfolio data…"):
                    context  = _build_portfolio_context(st.session_state.apps_df)
                    system   = _build_system_prompt(context)
                    recent   = st.session_state.chat_history[-10:]
                    api_msgs = [{"role": m["role"], "content": m["content"]} for m in recent]
                    _increment_call_count()
                    response = _call_claude(api_msgs, system, api_key)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.session_state.s6_processing = False
        st.rerun()
    # ── Layer 2: call limit ────────────────────────────────────────────────────
    # (checked again just before each API call — shown here for status display)
    max_calls  = _get_max_calls()
    call_count = st.session_state.get(CALL_COUNT_KEY, 0)
    api_key    = _get_api_key()
    df         = st.session_state.apps_df

    # ── Status bar ────────────────────────────────────────────────────────────
    source = st.session_state.get("data_source", "csv")
    pdi    = st.session_state.get("pdi_url", "")
    col_src, col_quota = st.columns([3, 1])

    with col_src:
        if source == "live":
            st.markdown(
                f'<div style="font-size:11px;color:#3B6D11">● Live · {pdi} · {len(df)} apps</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:11px;color:#854F0B">● Demo mode · CSV · ServiceNow PDI not reachable</div>',
                unsafe_allow_html=True,
            )

    with col_quota:
        remaining = max_calls - call_count
        quota_color = "#3B6D11" if remaining > 5 else "#854F0B" if remaining > 2 else "#A32D2D"
        st.markdown(
            f'<div style="font-size:11px;color:{quota_color};text-align:right">'
            f'{remaining}/{max_calls} queries remaining</div>',
            unsafe_allow_html=True,
        )

    # ── API key warning ───────────────────────────────────────────────────────
    if not api_key:
        st.markdown("""
        <div class="callout-warn">
        <strong>Anthropic API key not configured.</strong>
        Add <code>[anthropic] api_key = "sk-ant-..."</code> to
        <code>.streamlit/secrets.toml</code> to enable AI responses.
        </div>""", unsafe_allow_html=True)

    # ── Suggested prompts (shown only when conversation is empty) ─────────────
    if not st.session_state.chat_history:
        st.markdown("**Try asking:**")
        cols = st.columns(2)
        for i, prompt in enumerate(SUGGESTED_PROMPTS):
            with cols[i % 2]:
                if st.button(prompt, key=f"sug_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    st.rerun()

    # ── Chat history display ──────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    at_limit  = call_count >= max_calls
    user_input = st.chat_input(
        "Ask about the portfolio — risk, cost, retirement sequencing, dependencies…",
        disabled=(not api_key or at_limit),
    )

    if user_input:
        # Check call limit before firing
        if not _within_call_limit():
            return

        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing portfolio data…"):
                context  = _build_portfolio_context(df)
                system   = _build_system_prompt(context)
                recent   = st.session_state.chat_history[-10:]
                api_msgs = [{"role": m["role"], "content": m["content"]} for m in recent]

                if api_key:
                    _increment_call_count()
                    response = _call_claude(api_msgs, system, api_key)
                else:
                    response = (
                        "⚠ API key not configured. "
                        "Add your Anthropic API key to `.streamlit/secrets.toml`."
                    )

            st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()   # refresh quota display after each call

    # ── Controls ──────────────────────────────────────────────────────────────
    if st.session_state.chat_history:
        col_clear, col_meta = st.columns([1, 4])
        with col_clear:
            if st.button("Clear conversation"):
                st.session_state.chat_history = []
                st.rerun()
        with col_meta:
            st.caption(
                f"{len(st.session_state.chat_history)//2} exchange(s) · "
                f"{call_count} API call(s) this session · "
                f"Model: claude-sonnet-4-5"
            )

    # ── Portfolio quick reference ──────────────────────────────────────────────
    with st.expander("Portfolio quick reference — all 15 apps"):
        rows = []
        for _, row in df.iterrows():
            rows.append({
                "App":           row["name"],
                "Unit":          row["business_unit"],
                "Lifecycle":     row["u_lifecycle_status"],
                "Criticality":   row["u_criticality"],
                "Cost":          f"${int(row.get('u_annual_total_cost',0)):,}",
                "Tech Debt":     f"{int(row.get('u_technical_debt_score',0))}/100",
                "Incidents 12m": int(row.get("u_incident_volume_12m", 0)),
                "AI Rec":        row["_ai_recommendation"],
                "Confidence":    f"{int(row.get('_confidence',0))}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
