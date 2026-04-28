"""
AI Application Rationalization Advisor
Enterprise decision-support tool for application portfolio rationalization.
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from src.recommender import generate_recommendation

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Application Rationalization Advisor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
  .rec-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: 0.05em;
  }
  .rec-Retain     { background:#d1fae5; color:#065f46; }
  .rec-Modernize  { background:#dbeafe; color:#1e40af; }
  .rec-Consolidate{ background:#fef3c7; color:#92400e; }
  .rec-Retire     { background:#fee2e2; color:#991b1b; }
  .review-banner  {
    background:#fff7ed; border-left:4px solid #ea580c;
    padding:12px 16px; border-radius:4px; margin-bottom:12px;
  }
  .metric-label { font-size:0.8rem; color:#6b7280; margin-bottom:2px; }
  .metric-value { font-size:1.4rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = "data"

    inventory   = pd.read_csv(f"{base}/application_inventory.csv")
    finance     = pd.read_csv(f"{base}/finance_costs.csv")
    tech        = pd.read_csv(f"{base}/technical_health.csv")
    security    = pd.read_csv(f"{base}/security_risk.csv")
    support     = pd.read_csv(f"{base}/support_activity.csv")
    capability  = pd.read_csv(f"{base}/business_capability_mapping.csv")
    deps        = pd.read_csv(f"{base}/application_dependencies.csv")

    # Clean user_count commas
    inventory["user_count"] = (
        inventory["user_count"]
        .astype(str).str.replace(",", "").str.strip()
    )

    # Merge all sources on app_id
    df = inventory.merge(finance,    on="app_id", how="left")
    df = df.merge(tech,              on="app_id", how="left")
    df = df.merge(security,          on="app_id", how="left")
    df = df.merge(support,           on="app_id", how="left")
    df = df.merge(capability,        on="app_id", how="left")

    # Dependency count per app
    dep_count = (
        deps.groupby("source_app_id")
        .size()
        .reset_index(name="dependency_count")
        .rename(columns={"source_app_id": "app_id"})
    )
    df = df.merge(dep_count, on="app_id", how="left")
    df["dependency_count"] = df["dependency_count"].fillna(0).astype(int)

    return df, deps


df, deps = load_data()


# ── Generate recommendations for all apps ─────────────────────────
@st.cache_data
def run_recommendations(df):
    results = []
    for _, row in df.iterrows():
        r = generate_recommendation(row)
        results.append({
            "app_id":         row["app_id"],
            "app_name":       row["app_name"],
            "business_unit":  row.get("business_unit", ""),
            "criticality":    row.get("criticality", ""),
            "lifecycle":      row.get("lifecycle_status", ""),
            "annual_cost":    row.get("annual_total_cost", 0),
            "recommendation": r["recommendation"],
            "confidence":     r["confidence"],
            "requires_review":r["requires_review"],
            "score":          r["score"],
        })
    return pd.DataFrame(results)


rec_df = run_recommendations(df)


# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Filters")
    bu_options = ["All"] + sorted(df["business_unit"].dropna().unique().tolist())
    selected_bu = st.selectbox("Business Unit", bu_options)

    crit_options = ["All", "High", "Medium", "Low"]
    selected_crit = st.selectbox("Criticality", crit_options)

    rec_options = ["All", "Retain", "Modernize", "Consolidate", "Retire"]
    selected_rec = st.selectbox("Recommendation", rec_options)

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "AI-assisted decision-support tool for enterprise application "
        "portfolio rationalization. AI provides recommendations. "
        "Humans validate and decide."
    )


# ── Filter rec_df ─────────────────────────────────────────────────
filtered = rec_df.copy()
if selected_bu != "All":
    filtered = filtered[filtered["business_unit"] == selected_bu]
if selected_crit != "All":
    filtered = filtered[filtered["criticality"] == selected_crit]
if selected_rec != "All":
    filtered = filtered[filtered["recommendation"] == selected_rec]


# ── Header ────────────────────────────────────────────────────────
st.title("AI Application Rationalization Advisor")
st.caption(
    "Decision-support tool for enterprise portfolio rationalization. "
    "AI recommendations require human validation before action is taken."
)
st.divider()


# ── Tab layout ────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Portfolio Overview", "Application Review", "Decision Dashboard"])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — Portfolio Overview
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Portfolio Summary")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Applications", len(rec_df))
    with col2:
        st.metric("Require Review", int(rec_df["requires_review"].sum()))
    with col3:
        retire_count = int((rec_df["recommendation"] == "Retire").sum())
        st.metric("Retire", retire_count)
    with col4:
        modernize_count = int((rec_df["recommendation"] == "Modernize").sum())
        st.metric("Modernize", modernize_count)
    with col5:
        avg_conf = int(rec_df["confidence"].mean())
        st.metric("Avg Confidence", f"{avg_conf}%")

    st.divider()
    st.subheader("Application Portfolio")

    display_cols = [
        "app_name", "business_unit", "criticality",
        "lifecycle", "recommendation", "confidence", "requires_review"
    ]

    # Color-code recommendation column
    def highlight_rec(val):
        colors = {
            "Retain":      "background-color:#d1fae5",
            "Modernize":   "background-color:#dbeafe",
            "Consolidate": "background-color:#fef3c7",
            "Retire":      "background-color:#fee2e2",
        }
        return colors.get(val, "")

    styled = (
        filtered[display_cols]
        .rename(columns={
            "app_name":      "Application",
            "business_unit": "Business Unit",
            "criticality":   "Criticality",
            "lifecycle":     "Lifecycle",
            "recommendation":"Recommendation",
            "confidence":    "Confidence %",
            "requires_review":"Needs Review"
        })
        .style.map(highlight_rec, subset=["Recommendation"])
    )

    st.dataframe(styled, use_container_width=True, height=400)

    # Recommendation breakdown
    st.divider()
    st.subheader("Recommendation Breakdown")
    breakdown = rec_df["recommendation"].value_counts().reset_index()
    breakdown.columns = ["Recommendation", "Count"]
    st.bar_chart(breakdown.set_index("Recommendation"))


# ══════════════════════════════════════════════════════════════════
# TAB 2 — Application Review
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Application Review")

    selected_app = st.selectbox(
        "Select Application",
        df["app_name"].tolist(),
        key="app_select"
    )

    row = df[df["app_name"] == selected_app].iloc[0]
    result = generate_recommendation(row)

    # Human review flag
    if result["requires_review"]:
        st.markdown(
            '<div class="review-banner">⚠️ <strong>Human validation required</strong> '
            'before this recommendation is finalized. See review conditions below.</div>',
            unsafe_allow_html=True
        )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("#### AI Recommendation")
        rec = result["recommendation"]
        st.markdown(
            f'<span class="rec-badge rec-{rec}">{rec}</span>',
            unsafe_allow_html=True
        )
        st.markdown(f"**Confidence:** {result['confidence']}%")
        st.progress(result["confidence"] / 100)

        st.markdown("#### Rationale")
        for r in result["reasons"]:
            st.markdown(f"- {r}")

        if result["risks"]:
            st.markdown("#### Risk Flags")
            for r in result["risks"]:
                st.markdown(f"- {r}")

        if result["missing_fields"]:
            st.warning(
                f"Missing data fields: {', '.join(result['missing_fields'])}. "
                "Confidence score has been reduced."
            )

    with col_right:
        st.markdown("#### Application Details")
        detail_fields = {
            "Business Unit":     row.get("business_unit", ""),
            "Criticality":       row.get("criticality", ""),
            "Lifecycle Status":  row.get("lifecycle_status", ""),
            "Hosting Type":      row.get("hosting_type", ""),
            "User Count":        row.get("user_count", ""),
            "Annual Total Cost": f"${float(str(row.get('annual_total_cost',0)).replace(',','')):,.0f}" if row.get("annual_total_cost") else "N/A",
            "Security Risk":     row.get("security_risk_level", ""),
            "Critical Vulns":    row.get("critical_vulnerabilities", ""),
            "Incident Trend":    row.get("incident_trend", ""),
            "Tech Debt Score":   row.get("technical_debt_score", ""),
            "Duplicate Func.":   row.get("duplicate_functionality", ""),
            "Regulated Workflow":row.get("regulated_workflow", ""),
            "Customer Facing":   row.get("customer_facing", ""),
            "Dependencies":      row.get("dependency_count", 0),
        }
        for label, value in detail_fields.items():
            st.markdown(f"**{label}:** {value}")

    # Dependencies
    app_id = row["app_id"]
    app_deps = deps[deps["source_app_id"] == app_id]
    if not app_deps.empty:
        st.divider()
        st.markdown("#### Application Dependencies")
        st.dataframe(
            app_deps[["target_app_id", "dependency_type", "dependency_criticality"]],
            use_container_width=True
        )

    # Human review section
    st.divider()
    st.markdown("#### Human Review")
    st.caption(
        "AI provides the recommendation. You decide. "
        "All review decisions are logged for governance and auditability."
    )

    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        review_action = st.selectbox(
            "Reviewer Decision",
            ["Pending", "Approve", "Modify", "Reject"],
            key="review_action"
        )

        if review_action == "Modify":
            modified_rec = st.selectbox(
                "Modified Recommendation",
                ["Retain", "Modernize", "Consolidate", "Retire"],
                key="modified_rec"
            )

    with col_r2:
        reviewer_comment = st.text_area(
            "Reviewer Comment",
            placeholder="Document your reasoning, context, or override rationale...",
            height=120,
            key="reviewer_comment"
        )

    if st.button("Submit Review", type="primary"):
        if review_action == "Pending":
            st.warning("Please select a review action before submitting.")
        else:
            final_rec = (
                modified_rec
                if review_action == "Modify"
                else rec
            )
            st.success(
                f"Review submitted for **{selected_app}**: "
                f"**{review_action}** — Final recommendation: **{final_rec}**"
            )
            if reviewer_comment:
                st.info(f"Comment logged: {reviewer_comment}")


# ══════════════════════════════════════════════════════════════════
# TAB 3 — Decision Dashboard
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Decision Dashboard")
    st.caption("Portfolio-level metrics aligned to Safety, Quality, Delivery, and Cost.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Safety")
        high_sec = int((rec_df["recommendation"].isin(["Retire", "Modernize"])).sum())
        st.metric(
            "Applications with High/Medium Security Risk",
            int((df["security_risk_level"].isin(["High", "Medium"])).sum())
        )
        st.metric(
            "Critical Vulnerabilities (Portfolio Total)",
            int(pd.to_numeric(df["critical_vulnerabilities"], errors="coerce").fillna(0).sum())
        )

        st.markdown("#### Quality")
        st.metric(
            "Aging or End-of-Life Applications",
            int((df["lifecycle_status"].isin(["Aging", "End of Life"])).sum())
        )
        st.metric(
            "Average Confidence Score",
            f"{int(rec_df['confidence'].mean())}%"
        )

    with col2:
        st.markdown("#### Delivery")
        st.metric(
            "Applications Requiring Review",
            int(rec_df["requires_review"].sum())
        )
        st.metric(
            "Rising Incident Trend",
            int((df["incident_trend"] == "Rising").sum())
        )

        st.markdown("#### Cost")
        total_cost = pd.to_numeric(
            df["annual_total_cost"].astype(str).str.replace(",", ""),
            errors="coerce"
        ).fillna(0).sum()
        retire_cost = pd.to_numeric(
            df[df["app_id"].isin(rec_df[rec_df["recommendation"] == "Retire"]["app_id"])]["annual_total_cost"]
            .astype(str).str.replace(",", ""),
            errors="coerce"
        ).fillna(0).sum()

        st.metric("Total Portfolio Cost", f"${total_cost:,.0f}")
        st.metric(
            "Cost at Risk (Retire candidates)",
            f"${retire_cost:,.0f}"
        )

    st.divider()
    st.subheader("Recommendations by Business Unit")
    pivot = (
        rec_df.groupby(["business_unit", "recommendation"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    st.dataframe(pivot, use_container_width=True)

    st.divider()
    st.subheader("High Priority Applications")
    high_priority = rec_df[
        (rec_df["requires_review"] == True) &
        (rec_df["recommendation"].isin(["Retire", "Modernize"]))
    ][["app_name", "business_unit", "criticality", "recommendation", "confidence"]]

    if not high_priority.empty:
        st.dataframe(high_priority, use_container_width=True)
    else:
        st.info("No high priority applications identified.")