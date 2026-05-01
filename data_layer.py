"""
data_layer.py
Loads all data sources, computes derived scores, and manages
session-state for the validation queue and audit log.

Data source priority:
  1. ServiceNow PDI (via snow_connector.py) — if configured and reachable
  2. CSV files in data/ — silent fallback, always available

Active source stored in st.session_state.data_source ("live" | "csv").
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from snow_connector import try_load_from_servicenow, get_pdi_instance_url


# ── CSV paths (fallback) ───────────────────────────────────────────────────────
DATA_DIR = "data"
CSV_APPS  = f"{DATA_DIR}/01_cmdb_ci_business_app.csv"
CSV_DEPS  = f"{DATA_DIR}/02_cmdb_rel_ci.csv"
CSV_VULN  = f"{DATA_DIR}/03_sn_vul_vulnerable_item.csv"
CSV_CAP   = f"{DATA_DIR}/04_business_capability.csv"
CSV_INC   = f"{DATA_DIR}/05_incident_summary.csv"


# ── CSV loaders ────────────────────────────────────────────────────────────────

@st.cache_data
def _csv_apps() -> pd.DataFrame:
    df = pd.read_csv(CSV_APPS)
    df["u_duplicate_functionality"]      = df["u_duplicate_functionality"].astype(str).str.lower() == "true"
    df["u_replacement_candidate_exists"] = df["u_replacement_candidate_exists"].astype(str).str.lower() == "true"
    return df

@st.cache_data
def _csv_vulnerabilities() -> pd.DataFrame:
    return pd.read_csv(CSV_VULN)

@st.cache_data
def _csv_incidents() -> pd.DataFrame:
    return pd.read_csv(CSV_INC)

@st.cache_data
def load_dependencies() -> pd.DataFrame:
    return pd.read_csv(CSV_DEPS)

@st.cache_data
def load_capabilities() -> pd.DataFrame:
    return pd.read_csv(CSV_CAP)


# ── Derived score functions ────────────────────────────────────────────────────

def compute_tech_debt(row: pd.Series) -> int:
    score = 0
    if row["u_lifecycle_status"] == "End of Life":  score += 35
    elif row["u_lifecycle_status"] == "Aging":       score += 20
    crit = row.get("u_critical_vulnerabilities", 0)
    score += min(int(crit) * 5, 25)
    if row.get("u_incident_trend") == "Increasing":  score += 10
    outages = row.get("u_major_outages_12m", 0)
    score += min(int(outages) * 3, 15)
    stab = row.get("u_stability_score", 100)
    score += max(0, int((60 - stab) // 4))
    return min(score, 100)


def compute_ai_recommendation(row: pd.Series) -> str:
    life    = row["u_lifecycle_status"]
    crit    = row["u_criticality"]
    debt    = row["u_technical_debt_score"]
    replace = row["u_replacement_candidate_exists"]
    dup     = row["u_duplicate_functionality"]
    if life == "End of Life" and replace:                    return "Retire"
    if life == "End of Life" and not replace and crit=="High": return "Replace"
    if life == "Aging" and debt >= 70:                       return "Replace" if crit=="High" else "Modernize"
    if life == "Aging" and debt >= 40:                       return "Modernize"
    if dup and life != "Current":                            return "Evaluate"
    if dup and life == "Current":                            return "Modernize"
    return "Retain"


def compute_confidence(row: pd.Series) -> int:
    base = 50
    if row["u_lifecycle_status"] == "End of Life":   base += 30
    elif row["u_lifecycle_status"] == "Current":     base += 20
    elif row["u_lifecycle_status"] == "Aging":       base += 10
    debt = row["u_technical_debt_score"]
    if debt >= 80 or debt <= 20:   base += 15
    elif debt >= 60 or debt <= 35: base += 8
    completeness = row.get("_data_completeness", 80)
    base = int(base * (completeness / 100))
    return min(base, 98)


def compute_frontier(row: pd.Series) -> str:
    conf = row["_confidence"]
    if conf >= 80:  return "Inside"
    elif conf >= 60: return "Edge"
    return "Outside"


def compute_data_completeness(row: pd.Series) -> int:
    key_fields = [
        "u_lifecycle_status", "u_criticality", "u_technical_debt_score",
        "u_stability_score", "u_annual_total_cost", "u_user_count",
        "u_hosting_type", "u_duplicate_functionality",
    ]
    filled = sum(1 for f in key_fields
                 if pd.notna(row.get(f)) and str(row.get(f, "")) not in ["", "nan"])
    return int((filled / len(key_fields)) * 100)


def _enrich(apps: pd.DataFrame, vuln: pd.DataFrame | None,
            inc: pd.DataFrame | None) -> pd.DataFrame:
    """Join vulnerability + incident data onto apps, then compute all scores."""

    # Vulnerability join
    if vuln is not None and not vuln.empty:
        vcols = [c for c in ["cmdb_ci", "u_security_risk_level",
                              "u_open_vulnerabilities", "u_critical_vulnerabilities",
                              "u_internet_facing"] if c in vuln.columns]
        vsub = vuln[vcols].rename(columns={"cmdb_ci": "sys_id"})
        apps = apps.merge(vsub, on="sys_id", how="left")
    else:
        for c in ["u_security_risk_level","u_open_vulnerabilities",
                  "u_critical_vulnerabilities","u_internet_facing"]:
            apps[c] = None

    # Incident join — handle both column naming conventions
    if inc is not None and not inc.empty:
        id_col = "u_app_id" if "u_app_id" in inc.columns else "cmdb_ci"
        icols  = [id_col, "u_incident_volume_12m", "u_sev1_sev2_count",
                  "u_major_outages_12m", "u_incident_trend", "u_availability_pct"]
        icols  = [c for c in icols if c in inc.columns]
        isub   = inc[icols].rename(columns={id_col: "sys_id"})
        apps   = apps.merge(isub, on="sys_id", how="left")
    else:
        for c in ["u_incident_volume_12m","u_sev1_sev2_count",
                  "u_major_outages_12m","u_incident_trend","u_availability_pct"]:
            apps[c] = None

    # Fill numeric nulls so score functions don't crash
    for col in ["u_critical_vulnerabilities","u_open_vulnerabilities",
                "u_incident_volume_12m","u_sev1_sev2_count",
                "u_major_outages_12m","u_stability_score"]:
        if col in apps.columns:
            apps[col] = pd.to_numeric(apps[col], errors="coerce").fillna(0)

    apps["u_incident_trend"] = apps.get("u_incident_trend", "Stable").fillna("Stable")

    # Derived scores
    apps["_data_completeness"]   = apps.apply(compute_data_completeness, axis=1)
    apps["u_technical_debt_score"] = apps.apply(compute_tech_debt, axis=1)
    apps["_ai_recommendation"]   = apps.apply(compute_ai_recommendation, axis=1)
    apps["_confidence"]          = apps.apply(compute_confidence, axis=1)
    apps["_frontier"]            = apps.apply(compute_frontier, axis=1)

    return apps


def build_enriched_apps() -> pd.DataFrame:
    """
    Auto-detect data source: try ServiceNow first, fall back to CSV silently.
    Sets st.session_state.data_source to "live" or "csv".
    """
    snow_apps, snow_vuln, snow_inc, source = try_load_from_servicenow()

    if source == "live" and snow_apps is not None:
        st.session_state.data_source = "live"
        st.session_state.pdi_url = get_pdi_instance_url()
        return _enrich(snow_apps, snow_vuln, snow_inc)
    else:
        st.session_state.data_source = "csv"
        st.session_state.pdi_url = None
        apps = _csv_apps()
        vuln = _csv_vulnerabilities()
        inc  = _csv_incidents()
        return _enrich(apps, vuln, inc)


# ── Session state ──────────────────────────────────────────────────────────────

SEED_AUDIT = [
    {"timestamp":"2025-08-14 09:14","app_id":"APP002","app_name":"HR Hub",
     "ai_rec":"Retain","human_decision":"Approved","actor":"K. Turner — APM",
     "role":"APM","cycle":1,"tpfp":"TP","rationale":""},
    {"timestamp":"2025-08-14 09:31","app_id":"APP005","app_name":"CustomerPortal",
     "ai_rec":"Retain","human_decision":"Approved","actor":"K. Turner — APM",
     "role":"APM","cycle":1,"tpfp":"TP","rationale":""},
    {"timestamp":"2025-08-14 10:05","app_id":"APP004","app_name":"LegacyDB",
     "ai_rec":"Retire","human_decision":"Approved","actor":"K. Turner — APM",
     "role":"APM","cycle":1,"tpfp":"TP","rationale":""},
    {"timestamp":"2025-08-14 10:22","app_id":"APP001","app_name":"ERP Core",
     "ai_rec":"Retain","human_decision":"Overridden","actor":"K. Turner — APM",
     "role":"APM","cycle":1,"tpfp":"FN",
     "rationale":"SAP ECC approaching EOL — S/4HANA migration needed. Changed to Replace."},
    {"timestamp":"2025-11-10 11:01","app_id":"APP008","app_name":"MarketingHub",
     "ai_rec":"Retain","human_decision":"Approved","actor":"J. Patel — App Owner",
     "role":"App Owner","cycle":2,"tpfp":"TP","rationale":""},
    {"timestamp":"2025-11-10 11:15","app_id":"APP007","app_name":"ProcureTrack",
     "ai_rec":"Retire","human_decision":"Approved","actor":"K. Turner — APM",
     "role":"APM","cycle":2,"tpfp":"TP","rationale":""},
    {"timestamp":"2025-11-10 13:30","app_id":"APP012","app_name":"BIReportingSuite",
     "ai_rec":"Modernize","human_decision":"Overridden","actor":"K. Turner — APM",
     "role":"APM","cycle":2,"tpfp":"FP",
     "rationale":"Duplicate BI capability with DataWarehouse. Changed to Evaluate pending consolidation review."},
    {"timestamp":"2025-11-11 09:00","app_id":"APP011","app_name":"FieldServiceMgr",
     "ai_rec":"Retire","human_decision":"Approved","actor":"L. Chen — App Owner",
     "role":"App Owner","cycle":2,"tpfp":"TP","rationale":""},
    {"timestamp":"2025-11-11 10:00","app_id":"APP013","app_name":"IdentityVault",
     "ai_rec":"Retain","human_decision":"Approved","actor":"K. Turner — APM",
     "role":"APM","cycle":2,"tpfp":"TP","rationale":""},
    {"timestamp":"2026-02-03 10:00","app_id":"APP009","app_name":"ITSMPlatform",
     "ai_rec":"Retain","human_decision":"Approved","actor":"K. Turner — APM",
     "role":"APM","cycle":3,"tpfp":"—","rationale":""},
    {"timestamp":"2026-02-03 10:30","app_id":"APP015","app_name":"LegacyPayroll",
     "ai_rec":"Retire","human_decision":"Escalated","actor":"K. Turner — APM",
     "role":"APM","cycle":3,"tpfp":"—",
     "rationale":"HR owns payroll transition timeline — escalated to CIO."},
]

PENDING_IDS = {"APP003", "APP006", "APP010", "APP012"}


def init_session():
    if "audit_log"   not in st.session_state: st.session_state.audit_log   = list(SEED_AUDIT)
    if "pending_ids" not in st.session_state: st.session_state.pending_ids = set(PENDING_IDS)
    if "data_source" not in st.session_state: st.session_state.data_source = "csv"
    if "pdi_url"     not in st.session_state: st.session_state.pdi_url     = None
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "apps_df"     not in st.session_state:
        st.session_state.apps_df = build_enriched_apps()


def record_decision(app_id, app_name, ai_rec, decision, actor, role, rationale=""):
    st.session_state.audit_log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "app_id": app_id, "app_name": app_name,
        "ai_rec": ai_rec, "human_decision": decision,
        "actor": actor, "role": role,
        "cycle": 3, "tpfp": "—", "rationale": rationale,
    })
    st.session_state.pending_ids.discard(app_id)


# ── Colour helpers ─────────────────────────────────────────────────────────────

REC_COLORS = {
    "Retain":"#3B6D11","Modernize":"#854F0B",
    "Retire":"#A32D2D","Replace":"#854F0B","Evaluate":"#185FA5",
}
REC_BG = {
    "Retain":"#EAF3DE","Modernize":"#FAEEDA",
    "Retire":"#FCEBEB","Replace":"#FAEEDA","Evaluate":"#E6F1FB",
}
LIFECYCLE_COLORS = {"Current":"#3B6D11","Aging":"#854F0B","End of Life":"#A32D2D"}
CRIT_COLORS      = {"High":"#A32D2D","Medium":"#854F0B","Low":"#185FA5"}
FRONTIER_TEXT    = {
    "Inside":  "Structured data + clear lifecycle signal. AI pattern-matching is reliable here. Human review still required, but confidence is high.",
    "Edge":    "Data gaps or competing signals reduce reliability. This sits at the boundary of the jagged frontier — validate carefully before acting. Misapplication risk is highest here.",
    "Outside": "Recommendation requires business judgment AI cannot reliably perform. Treat as a starting point only. Human expertise must drive the final decision.",
}
