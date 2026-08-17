# CMP-FEAT-035 — Per-Session Activity Classification

**Type:** Feature
**Priority:** P1
**Target:** v0.2.0
**Status:** Verification

## User problem

One Todo can require different kinds of work over time. For example, a Compass roadmap Todo may involve an Admin session followed by Development / Coding and Testing sessions.

## Requirement

The Todo keeps its default category, while each timing session can select its own activity type at Start.

## Acceptance criteria

- A Todo can be started repeatedly across multiple sessions.
- Each session can use a different activity type.
- The selected activity type is persisted with the active session.
- The completed activity log stores the session activity type.
- The Todo's default category remains unchanged.
