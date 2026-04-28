# Data Model

## Data Sources
- Application inventory
- Business capability mapping
- Finance / cost data
- Technical health assessment
- Security risk assessment
- Support activity
- Application dependencies

## Required Fields

### Application Inventory
- app_id: unique application identifier
- app_name: application name
- business_unit: owning business unit
- business_capability: business capability supported
- business_owner: accountable owner
- criticality: Low, Medium, High
- user_count: number of active users
- hosting_type: On Prem, Cloud, SaaS, Hybrid
- lifecycle_status: Current, Aging, End of Life

### Finance
- annual_total_cost: total annual cost
- cost_baseline_date: date cost was last validated

### Technical Health
- technical_debt_score: 1 to 5
- stability_score: 1 to 5
- integration_complexity_score: 1 to 5
- duplicate_functionality: Yes or No
- replacement_candidate_exists: Yes or No

### Security Risk
- security_risk_level: Low, Medium, High
- open_vulnerabilities: count
- critical_vulnerabilities: count
- internet_facing: Yes or No
- sensitive_data_present: Yes or No

### Support Activity
- incident_volume_12m: incident count over last 12 months
- major_outages_12m: outage count over last 12 months
- user_satisfaction_score: 0 to 100
- incident_trend: Stable, Rising, Declining

## Data Quality Rules
- app_id must exist in all core datasets
- user_count must be numeric
- annual_total_cost must be numeric
- criticality must be Low, Medium, or High
- lifecycle_status must be Current, Aging, or End of Life
- stale data lowers confidence