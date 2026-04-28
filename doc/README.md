# AI Application Rationalization Advisor

AI-powered decision-support tool for enterprise application portfolio rationalization.

This product helps organizations make consistent, transparent decisions on whether to retain, retire, modernize, or consolidate applications.

## Product Requirements Document (PRD)
1. Problem Statement

Enterprise application portfolios lack consistent, data-driven decision support for rationalization decisions.
Organizations rely on fragmented data, manual analysis, and subjective judgment to determine whether to retain, retire, modernize, or consolidate applications.

This leads to:

inconsistent decisions across teams
limited transparency into why decisions are made
increased risk due to aging technology and security exposure
inefficient portfolio spend
This product focuses on improving decision quality, not automating decisions.

2. Target Users
Application Portfolio Managers
Enterprise Architects
IT and Digital Leadership

These users are responsible for evaluating application portfolios and making planning and investment decisions.

3. Core Decision

For each application, determine:

Retain
Retire
Modernize
Consolidate

This is the primary decision the product supports.

4. Solution Overview

The AI Application Rationalization Advisor is a decision-support tool that evaluates enterprise applications using multiple data sources and generates structured recommendations.

The system:

analyzes application attributes across cost, usage, lifecycle, technical health, and risk
produces a recommendation with supporting rationale
provides confidence and risk indicators
enables human validation before decisions are finalized

This is not an autonomous system. It is designed to augment decision-making, not replace it.

5. Key Features (Demo Scope)
Portfolio Overview
application inventory view
filtering and segmentation (business unit, criticality, lifecycle)
high-level portfolio metrics
AI Recommendation Engine
recommendation (retain / retire / modernize / consolidate)
confidence score
supporting rationale
risk flags
Decision Review
detailed application view
AI recommendation summary
human-in-the-loop decision:
approve
modify
reject
Dashboard
recommendation breakdown
decision outcomes (approved / modified / rejected)
risk distribution
recent decision activity
6. Data Inputs

The system integrates multiple enterprise data sources:

application inventory (metadata, ownership, lifecycle)
cost data (annual cost, licensing)
technical health (stability, maintainability)
security risk (exposure, vulnerabilities)
usage and support data (user count, ticket volume)

The demo uses structured CSV data to simulate these sources.

7. Decision Logic (Simplified)

Recommendations are based on weighted evaluation of:

lifecycle status (current, aging, end-of-life)
cost
user adoption
technical health
security risk
business criticality

The system prioritizes:

risk reduction
cost efficiency
business continuity
8. Guardrails and Design Principles
AI provides recommendations, not final decisions
high-impact decisions require human validation
all outputs must include rationale and confidence
transparency is prioritized over automation
the system is designed to avoid false confidence
9. Success Metrics (SQDC-Aligned)
Safety
reduction in security and compliance risks
Quality
improved consistency and defensibility of decisions
Delivery
reduced time required to evaluate applications
Cost
improved portfolio cost efficiency
reduction in redundant or low-value applications
10. Demo Goal

The purpose of this prototype is to demonstrate:

how AI can be applied to real enterprise decision workflows
how to structure AI-assisted recommendations with transparency and control
how to integrate AI into existing planning and governance processes

This is a product-thinking exercise, not a production system.