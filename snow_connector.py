"""
snow_connector.py
Auto-detects ServiceNow PDI availability and pulls live data.
Falls back to CSV silently if the PDI is unreachable, credentials
are missing, or any request fails.

Data source status is stored in st.session_state.data_source:
  "live"  — successfully connected to ServiceNow PDI
  "csv"   — fallback mode (PDI unavailable or not configured)
"""

import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import json


# ── PDI config — read from secrets, never hardcoded ───────────────────────────

def _get_config() -> dict | None:
    """Return PDI config from st.secrets, or None if not configured."""
    try:
        cfg = st.secrets.get("servicenow", {})
        url  = cfg.get("url", "").rstrip("/")
        user = cfg.get("username", "")
        pwd  = cfg.get("password", "")
        if url and user and pwd:
            return {"url": url, "username": user, "password": pwd}
    except Exception:
        pass
    return None


def _table_url(cfg: dict, table: str) -> str:
    return f"{cfg['url']}/api/now/table/{table}"


def _get(cfg: dict, table: str, params: dict) -> list | None:
    """
    Single GET to a ServiceNow table. Returns list of records or None on failure.
    Timeout is intentionally short (4s) so a dead PDI fails fast.
    """
    try:
        r = requests.get(
            _table_url(cfg, table),
            auth=HTTPBasicAuth(cfg["username"], cfg["password"]),
            headers={"Accept": "application/json"},
            params=params,
            timeout=4,
        )
        if r.status_code == 200:
            return r.json().get("result", [])
    except Exception:
        pass
    return None


# ── Table fetchers — one per ServiceNow table ─────────────────────────────────

def _fetch_apps(cfg: dict) -> pd.DataFrame | None:
    fields = ",".join([
        "sys_id", "name", "short_description", "business_unit",
        "u_criticality", "u_user_count", "u_hosting_type", "u_lifecycle_status",
        "u_annual_license_cost", "u_infrastructure_cost", "u_support_labor_cost",
        "u_annual_total_cost", "u_technical_debt_score", "u_stability_score",
        "u_duplicate_functionality", "u_replacement_candidate_exists",
        "vendor", "version", "install_status", "operational_status",
        "used_for", "portfolio_status",
    ])
    records = _get(cfg, "cmdb_ci_business_app", {
        "sysparm_fields": fields,
        "sysparm_limit": 50,
        # Only pull our demo apps — filter by portfolio_status presence
        "sysparm_query": "portfolio_statusISNOTEMPTY",
    })
    if not records:
        return None

    df = pd.DataFrame(records)

    # ServiceNow returns reference fields as {value, display_value} dicts
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.get("display_value", x.get("value", x))
            if isinstance(x, dict) else x
        )

    # Coerce types
    for col in ["u_annual_license_cost", "u_infrastructure_cost",
                "u_support_labor_cost", "u_annual_total_cost",
                "u_user_count", "u_technical_debt_score", "u_stability_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["u_duplicate_functionality"] = (
        df.get("u_duplicate_functionality", pd.Series(["false"] * len(df)))
        .astype(str).str.lower()
        .isin(["true", "1", "yes"])
    )
    df["u_replacement_candidate_exists"] = (
        df.get("u_replacement_candidate_exists", pd.Series(["false"] * len(df)))
        .astype(str).str.lower()
        .isin(["true", "1", "yes"])
    )

    return df if len(df) > 0 else None


def _fetch_vulnerabilities(cfg: dict) -> pd.DataFrame | None:
    fields = ",".join([
        "cmdb_ci", "u_security_risk_level", "u_open_vulnerabilities",
        "u_critical_vulnerabilities", "u_internet_facing",
    ])
    records = _get(cfg, "sn_vul_vulnerable_item", {
        "sysparm_fields": fields,
        "sysparm_limit": 50,
        "sysparm_query": "cmdb_ciISNOTEMPTY",
    })
    if not records:
        return None

    df = pd.DataFrame(records)
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.get("display_value", x.get("value", x))
            if isinstance(x, dict) else x
        )
    for col in ["u_open_vulnerabilities", "u_critical_vulnerabilities"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def _fetch_incidents(cfg: dict) -> pd.DataFrame | None:
    fields = ",".join([
        "u_app_id", "u_incident_volume_12m", "u_sev1_sev2_count",
        "u_major_outages_12m", "u_incident_trend", "u_availability_pct",
    ])
    records = _get(cfg, "incident", {
        "sysparm_fields": fields,
        "sysparm_limit": 50,
        "sysparm_query": "u_app_idISNOTEMPTY",
    })
    if not records:
        return None

    df = pd.DataFrame(records)
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.get("display_value", x.get("value", x))
            if isinstance(x, dict) else x
        )
    for col in ["u_incident_volume_12m", "u_sev1_sev2_count",
                "u_major_outages_12m"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    if "u_availability_pct" in df.columns:
        df["u_availability_pct"] = pd.to_numeric(
            df["u_availability_pct"], errors="coerce").fillna(99.0)
    return df


# ── Public interface ──────────────────────────────────────────────────────────

def try_load_from_servicenow() -> tuple[pd.DataFrame | None,
                                        pd.DataFrame | None,
                                        pd.DataFrame | None,
                                        str]:
    """
    Attempt to load apps, vulnerabilities, and incidents from ServiceNow.

    Returns (apps_df, vuln_df, inc_df, source) where source is:
      "live"  — all three tables loaded successfully
      "csv"   — fallback (any failure; caller should use CSV loaders)

    Failures are silent — no exceptions propagate to the UI.
    """
    cfg = _get_config()
    if not cfg:
        return None, None, None, "csv"

    try:
        apps = _fetch_apps(cfg)
        if apps is None or len(apps) == 0:
            return None, None, None, "csv"

        vuln = _fetch_vulnerabilities(cfg)
        inc  = _fetch_incidents(cfg)

        # Partial success is still useful — missing tables fall back gracefully
        return apps, vuln, inc, "live"

    except Exception:
        return None, None, None, "csv"


def get_pdi_instance_url() -> str | None:
    """Return the configured PDI URL for display in the sidebar."""
    cfg = _get_config()
    if cfg:
        return cfg["url"].replace("https://", "").replace("http://", "")
    return None
