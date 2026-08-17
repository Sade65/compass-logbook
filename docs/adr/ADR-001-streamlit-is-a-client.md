# ADR-001 — Streamlit is a Client, Not Compass Core

**Status:** Accepted
**Date:** 2026-08-17

## Context

Compass currently runs as a local Streamlit application, but the intended product must later support additional clients such as a minimal iPhone interface, possible Android support, remote synchronization, integrations, and an AI/MCP interface.

If business logic is embedded directly in Streamlit widget handlers, changing UI technology or adding another client would require duplicating or rewriting core behavior.

## Decision

Treat Streamlit as one presentation client of Compass.

New domain and persistence logic should progressively move into UI-independent Python modules. UI code should call operations such as `start_timer`, `stop_timer`, `create_todo`, or `complete_todo` rather than owning their business rules.

## Consequences

### Positive

- easier future mobile/API integration
- reusable business logic
- independently testable core behavior
- cleaner separation of concerns
- reduced dependence on Streamlit runtime/session state

### Trade-offs

- slightly more project structure than a single-file prototype
- some existing `app.py` logic will need gradual refactoring

## First application of this decision

CMP-FIX-001 moves persistent timer runtime state into `compass_core/runtime_state.py` rather than storing the active timer solely in `st.session_state`.
