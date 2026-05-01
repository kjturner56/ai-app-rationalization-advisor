# AI Portfolio Rationalization Advisor

**Centaur Governance Model** — AI recommends, humans decide.

Built for: Senior AI PM / AI Governance role interviews  
Framework: AI Risk Assessment and Deployment Framework (K. Turner, 2026)

---

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Open http://localhost:8501

---

## Project Structure

```
portfolio_app/
├── app.py                  # Entry point, navigation, global CSS
├── data_layer.py           # Data loading, score computation, session state
├── requirements.txt
├── data/
│   ├── 01_cmdb_ci_business_app.csv     # Application inventory (ServiceNow mapped)
│   ├── 02_cmdb_rel_ci.csv              # Application dependencies
│   ├── 03_sn_vul_vulnerable_item.csv   # Security risk / CVEs
│   ├── 04_business_capability.csv      # Business capability mapping
│   └── 05_incident_summary.csv         # 12-month support activity
└── pages/
    ├── p1_overview.py      # Screen 1: Portfolio overview + KPIs
    ├── p2_analysis.py      # Screen 2: AI signals + explainability + frontier
    ├── p3_validation.py    # Screen 3: Centaur validation queue
    ├── p4_audit.py         # Screen 4: Decision audit log
    └── p5_governance.py    # Screen 5: TP/FP, SQDC, drift, cycle history
```

---

## Deploy to Streamlit Cloud (Leave-Behind URL)

1. Push this folder to a **public GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select the repo, set **Main file path** to `app.py`
5. Click Deploy — you'll get a public URL in ~2 minutes

Share that URL with interviewers as the leave-behind.

---

## Five-Screen Demo Narrative

| Screen | What It Shows | Interview Talking Point |
|--------|--------------|------------------------|
| Portfolio Overview | 15 apps, KPI cards, filterable table | "This is what the CIO sees first — business impact before technical detail" |
| AI Analysis & Signals | Per-app confidence, frontier label, signal breakdown | "Every recommendation is explainable and auditable — this is how you prevent misrepresentation" |
| Validation Queue | Centaur approval workflow, override with rationale | "Nothing is final until a human acts. Try overriding without a rationale." |
| Decision Audit Log | Timestamped, filterable, TP/FP classified | "This is your compliance artifact — every decision is documented at decision time" |
| Governance Dashboard | TP/FP by cycle, SQDC metrics, drift report | "This answers 'is the AI getting better?' and 'what's the business impact?'" |

---

## Key Design Decisions (Interview Defense)

**Why Streamlit?** Right tool for a PM portfolio piece — shows you can ship, not just design.  
**Why SQLite-free?** Session state keeps the demo self-contained and zero-infra. Migration path to ServiceNow GRC is straightforward.  
**Why the frontier label?** Directly references the jagged technological frontier framework — connects the tool to the academic governance model.  
**Why block override without rationale?** Governance as a product constraint, not a slide. Demonstrates you've thought about adoption, not just features.  
**Why SQDC?** Named directly from the AI Risk Assessment paper — shows the demo and the framework are the same artifact.

---

## ServiceNow REST API (Next Phase)

Replace CSV reads in `data_layer.py` with:

```python
import requests

BASE = "https://dev342173.service-now.com/api/now/table"
AUTH = ("admin", "your_password")

def load_apps_from_snow():
    r = requests.get(
        f"{BASE}/cmdb_ci_business_app",
        auth=AUTH,
        params={
            "sysparm_fields": "name,u_criticality,u_lifecycle_status,u_annual_total_cost,u_technical_debt_score",
            "sysparm_limit": 100,
        }
    )
    return pd.DataFrame(r.json()["result"])
```

Store credentials in `.streamlit/secrets.toml` (never in source):
```toml
[servicenow]
url = "https://dev342173.service-now.com"
username = "admin"
password = "your_password"
```
