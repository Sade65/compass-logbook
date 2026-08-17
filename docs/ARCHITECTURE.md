# Compass Architecture

## Architectural direction

Compass is a local-first personal operating system. Streamlit is the current UI client, not the long-term system boundary.

```text
                   ┌─────────────────┐
                   │   Compass Core  │
                   │ domain + rules  │
                   └────────┬────────┘
                            │
                 persistence / services
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   Streamlit UI        Mobile client       AI / MCP
        │                                      │
        └──────── future shared API / sync ────┘
```

## Engineering principles

1. UI-independent core logic.
2. Important state survives process/session shutdown.
3. Explicit domain objects and state transitions.
4. Timestamp/event history over destructive overwrites where practical.
5. API-ready operations for future clients.
6. Personal data remains local by default.
7. Schema and architecture changes are documented and traceable.
8. Core behavior should be testable without launching Streamlit.

## Current storage

The MVP uses local CSV files for durable logs. CMP-FIX-001 adds a small ignored JSON runtime-state file for active/pending timing state. A later architecture iteration can migrate durable domain storage to SQLite without changing the requirement-level behavior.
