# Compass Requirement Register

This register gives every meaningful product, UX, reliability, data, integration, analytics, security, or architecture change a stable identifier.

## Status vocabulary

- **Backlog** — captured, not yet scheduled
- **Planned** — selected for an upcoming release
- **Investigating** — behavior is being verified before implementation
- **In Progress** — implementation underway
- **Verification** — implemented, awaiting acceptance test
- **Done** — acceptance criteria satisfied

## Requirement register

| ID | Title | Type | Priority | Status | Target |
|---|---|---|---|---|---|
| CMP-FIX-001 | Persistent Timer Recovery | Reliability | P0 | Verification | v0.2.0 |
| CMP-UX-002 | Todo Form Reset After Creation | UX | P1 | Verification | v0.2.0 |
| CMP-UX-003 | Reverse-Chronological Todo Ordering | UX | P1 | Verification | v0.2.0 |
| CMP-FEAT-004 | Todo Creation Timestamp | Feature | P1 | Verification | v0.2.0 |
| CMP-FEAT-005 | Todo Action Controls | Feature | P1 | Planned | v0.2.x |
| CMP-ARCH-006 | Multi-Session Todo Model | Architecture | P0 | In Progress | v0.2.0 |
| CMP-ANL-007 | Daily Activity Time Breakdown | Analytics | P1 | Planned | v0.2.x |
| CMP-UX-008 | Activity Log Information Hierarchy | UX | P1 | Verification | v0.2.x |
| CMP-FEAT-009 | Planned vs Actual Duration | Feature | P1 | Planned | v0.2.x |
| CMP-FEAT-010 | Timestamped Quick Notes | Feature | P2 | Backlog | v0.3+ |
| CMP-SEC-011 | Protected Journal | Security | P2 | Backlog | v0.3+ |
| CMP-FEAT-012 | Todo Date Assignment | Feature | P1 | Planned | v0.2.x |
| CMP-FEAT-013 | Lifecycle Replacement Tracker | Feature | P1 | Backlog | v0.3+ |
| CMP-FEAT-014 | Lifecycle Alerts & Due-State UI | Feature | P1 | Backlog | v0.3+ |
| CMP-ARCH-015 | Lifecycle-to-Todo Automation | Architecture | P1 | Backlog | v0.3+ |
| CMP-FEAT-016 | Subscription & Contract Hub | Feature | P1 | Backlog | v0.3+ |
| CMP-UX-017 | Subscription Visual Cards | UX | P2 | Backlog | v0.3+ |
| CMP-FEAT-018 | Account / Contract Context | Feature | P2 | Backlog | v0.3+ |
| CMP-FEAT-019 | Consumable Usage Tracker | Feature | P2 | Backlog | v0.3+ |
| CMP-INTEG-020 | Health Data Ingestion | Integration | P1 | Backlog | v0.4+ |
| CMP-INTEG-021 | WHOOP Data Integration | Integration | P2 | Backlog | v0.4+ |
| CMP-DATA-022 | WHOOP CSV Importer | Data | P2 | Backlog | v0.4+ |
| CMP-ARCH-023 | Multi-Client Compass Architecture | Architecture | P0 | Adopted principle | Ongoing |
| CMP-FEAT-024 | Mobile Quick Logger | Feature | P1 | Backlog | v0.4+ |
| CMP-ARCH-025 | Remote / Offline Sync Strategy | Architecture | P1 | Backlog | v0.4+ |
| CMP-FEAT-026 | Measured Routine Entries | Feature | P2 | Backlog | v0.3+ |
| CMP-ARCH-027 | Automation Rule Engine | Architecture | P1 | Backlog | v0.3+ |
| CMP-INTEG-028 | Compass MCP Interface | Integration | P3 | Backlog | Later |
| CMP-ANL-029 | Effort-Aware Urgency Engine | Analytics | P1 | Backlog | v0.3+ |
| CMP-ANL-030 | Dynamic Priority & Criticality Score | Analytics | P1 | Backlog | v0.3+ |
| CMP-FEAT-031 | Proactivity Scoring | Feature | P2 | Backlog | v0.3+ |
| CMP-FEAT-032 | Smart Household Inventory | Feature | P2 | Backlog | v0.3+ |
| CMP-ANL-033 | Consumption Forecasting | Analytics | P2 | Backlog | v0.4+ |
| CMP-AUTO-034 | Predictive Shopping List | Automation | P2 | Backlog | v0.4+ |
| CMP-FEAT-035 | Per-Session Activity Classification | Feature | P1 | Verification | v0.2.0 |
| CMP-FIX-036 | Todo / Session State Synchronization | Reliability | P0 | Verification | v0.2.0 |
| CMP-UX-037 | Safe Text Copy / Streamlit Shortcut Mitigation | UX | P2 | Verification | v0.2.0 |
| CMP-UX-043 | Human-Readable Live Timer | UX | P1 | Verification | v0.2.x |
| CMP-FEAT-047 | Retroactive Todo / Activity Entry | Feature | P0 | Planned | v0.2.x |
| CMP-UX-083 | Recent Activity History Table | UX | P1 | Verification | v0.2.x |
| CMP-UX-084 | Recent Check-In Table Readability | UX | P1 | Verification | v0.2.x |
| CMP-UX-082 | Todo Status Visual Hierarchy | UX | P1 | Verification | v0.2.x |

## Traceability convention

Use the requirement ID everywhere the change matters:

- branch / PR title
- commit message
- requirement file when the change is substantial
- tests or manual acceptance notes
- changelog / release notes

Example commit:

```text
fix(timer): persist and recover active sessions [CMP-FIX-001]
```
