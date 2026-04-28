# Human Review Design

## Principle
The system provides decision support, not autonomous decision-making.

## Review Actions
A reviewer can:
- Approve the AI recommendation
- Modify the recommendation
- Reject the recommendation

## Required Review Conditions
Human validation is required when:
- the application is business critical
- the recommendation is Retire
- confidence is low
- dependency data is incomplete
- security risk is high
- cost or ownership data is stale

## Review Log
Each review should capture:
- application ID
- AI recommendation
- confidence score
- reviewer decision
- final action
- reviewer comment
- timestamp

## Why This Matters
Human review reduces false confidence and ensures accountability for high-impact enterprise decisions.