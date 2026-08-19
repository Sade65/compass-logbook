# Compass Roadmap

## Current release focus — v0.2.0 Reliable Todos & Timers

Goal: make Todos & Timers trustworthy enough to become the foundation for later analytics, urgency, automation, and multi-client operation.

### Acceptance focus

- persistent timer recovery
- Todo/session state consistency
- multiple sessions per Todo
- per-session activity classification
- clear Todo creation feedback
- newest-first Todo ordering
- visible Todo creation time
- Streamlit copy/shortcut mitigation

The authoritative requirement inventory is maintained in `docs/requirements/README.md`.

## Next v0.2.x candidates

- Todo Open / Edit / Delete or Archive actions
- Todo date assignment
- planned vs actual duration
- activity-log cleanup and information hierarchy
- daily time breakdown by activity type

## Future product systems

- effort-aware urgency and criticality
- lifecycle maintenance automation
- subscription / contract hub
- consumable and household inventory forecasting
- automatic shopping-list generation
- health / WHOOP data ingestion
- mobile quick logger and multi-client synchronization
- automation rule engine
- AI/MCP access layer
## Experimental design track

- CMP-UX-087 Premium UI Baseline is intentionally isolated from functional work so visual decisions can be accepted, revised, or discarded without changing Compass Core.
