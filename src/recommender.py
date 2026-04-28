"""
AI Application Rationalization Advisor - Recommendation Engine
Generates retain / retire / modernize / consolidate recommendations
based on multi-source enterprise data.
"""


def to_int(value, default=0):
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def to_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


def to_str(value, default=""):
    try:
        return str(value).strip()
    except (ValueError, TypeError):
        return default


def generate_recommendation(row):
    score = 0
    reasons = []
    risks = []
    missing_fields = []

    # ── Pull fields ───────────────────────────────────────────────
    lifecycle_status    = to_str(row.get("lifecycle_status", ""))
    criticality         = to_str(row.get("criticality", ""))
    user_count          = to_int(row.get("user_count", 0))
    annual_total_cost   = to_float(row.get("annual_total_cost", 0))
    tech_debt_score     = to_float(row.get("technical_debt_score", 0))
    stability_score     = to_float(row.get("stability_score", 5))
    security_risk_level = to_str(row.get("security_risk_level", ""))
    critical_vulns      = to_int(row.get("critical_vulnerabilities", 0))
    incident_trend      = to_str(row.get("incident_trend", ""))
    sev_incidents       = to_int(row.get("sev1_sev2_incidents_12m", 0))
    duplicate           = to_str(row.get("duplicate_functionality", "No"))
    replacement_exists  = to_str(row.get("replacement_candidate_exists", "No"))
    suggested_posture   = to_str(row.get("suggested_technical_posture", ""))
    regulated_workflow  = to_str(row.get("regulated_workflow", "No"))
    customer_facing     = to_str(row.get("customer_facing", "No"))
    satisfaction_score  = to_float(row.get("user_satisfaction_score", 100))

    # ── Data quality checks ───────────────────────────────────────
    if not user_count:
        missing_fields.append("user count")
    if not annual_total_cost:
        missing_fields.append("annual cost")
    if not tech_debt_score:
        missing_fields.append("technical debt score")
    if not security_risk_level:
        missing_fields.append("security risk level")

    # ── Lifecycle ─────────────────────────────────────────────────
    if lifecycle_status == "End of Life":
        score += 3
        reasons.append("Application is end-of-life.")
        risks.append("Vendor support has ended, creating operational and security risk.")
    elif lifecycle_status == "Aging":
        score += 1
        reasons.append("Application is aging and approaching end of supported life.")

    # ── Cost ──────────────────────────────────────────────────────
    if annual_total_cost > 400000:
        score += 3
        reasons.append(f"Annual cost is very high (${annual_total_cost:,.0f}).")
    elif annual_total_cost > 200000:
        score += 1
        reasons.append(f"Annual cost is elevated (${annual_total_cost:,.0f}).")

    # ── Usage ─────────────────────────────────────────────────────
    if user_count and user_count < 50:
        score += 2
        reasons.append(f"Very low user adoption ({user_count} users).")
    elif user_count and user_count < 150:
        score += 1
        reasons.append(f"Below average user adoption ({user_count} users).")

    # ── Technical health ──────────────────────────────────────────
    if tech_debt_score >= 4:
        score += 2
        reasons.append(f"High technical debt score ({tech_debt_score}/5).")
    elif tech_debt_score >= 3:
        score += 1
        reasons.append(f"Moderate technical debt ({tech_debt_score}/5).")

    if stability_score <= 2:
        score += 2
        reasons.append(f"Low stability score ({stability_score}/5).")
        risks.append("Instability increases outage risk.")

    # ── Security ──────────────────────────────────────────────────
    if security_risk_level == "High":
        score += 3
        reasons.append("Security risk is assessed as High.")
        risks.append("High security exposure requires immediate attention.")
    elif security_risk_level == "Medium":
        score += 1
        reasons.append("Security risk is assessed as Medium.")

    if critical_vulns >= 3:
        score += 2
        reasons.append(f"{critical_vulns} critical vulnerabilities are open.")
        risks.append("Open critical vulnerabilities increase breach risk.")

    # ── Support activity ──────────────────────────────────────────
    if incident_trend == "Rising":
        score += 1
        reasons.append("Incident volume is trending upward.")
    if sev_incidents >= 8:
        score += 1
        reasons.append(f"High volume of Sev1/Sev2 incidents ({sev_incidents} in last 12 months).")

    if satisfaction_score and satisfaction_score < 65:
        score += 1
        reasons.append(f"Low user satisfaction score ({satisfaction_score}/100).")

    # ── Duplicate / consolidation signal ─────────────────────────
    if duplicate == "Yes":
        score += 2
        reasons.append("Duplicate functionality exists in the portfolio.")
        if replacement_exists == "Yes":
            reasons.append("A viable replacement candidate has been identified.")

    # ── Criticality guardrail ─────────────────────────────────────
    if criticality == "High":
        reasons.append("Application supports a high-criticality business process.")
        risks.append("Decision requires business owner validation due to high criticality.")

    if regulated_workflow == "Yes":
        risks.append("Application supports a regulated workflow. Compliance review required before any action.")

    if customer_facing == "Yes":
        risks.append("Application is customer-facing. Retirement or changes may impact customer experience.")

    # ── Decision mapping ──────────────────────────────────────────
    if score >= 7 and criticality != "High":
        recommendation = "Retire"
    elif lifecycle_status in ["Aging", "End of Life"] and criticality == "High":
        recommendation = "Modernize"
    elif duplicate == "Yes" and replacement_exists == "Yes" and criticality != "High":
        recommendation = "Consolidate"
    elif score >= 5:
        recommendation = "Modernize"
    elif score >= 3:
        recommendation = "Consolidate"
    else:
        recommendation = "Retain"

    # Align with suggested technical posture if available
    if suggested_posture and suggested_posture != recommendation:
        reasons.append(
            f"Note: Technical assessment suggests '{suggested_posture}'. "
            f"AI recommendation is '{recommendation}' based on weighted scoring."
        )

    # ── Confidence ────────────────────────────────────────────────
    confidence = min(95, 50 + (score * 5))

    if missing_fields:
        penalty = len(missing_fields) * 10
        confidence = max(30, confidence - penalty)
        risks.append(
            f"Confidence reduced due to missing data: {', '.join(missing_fields)}."
        )

    # ── Human review flag ─────────────────────────────────────────
    requires_review = (
        criticality == "High"
        or recommendation == "Retire"
        or confidence < 60
        or len(missing_fields) > 0
        or regulated_workflow == "Yes"
        or critical_vulns >= 3
    )

    if not reasons:
        reasons.append("Current signals suggest the application remains fit for purpose.")

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "reasons": reasons,
        "risks": risks,
        "requires_review": requires_review,
        "missing_fields": missing_fields,
        "score": score,
    }