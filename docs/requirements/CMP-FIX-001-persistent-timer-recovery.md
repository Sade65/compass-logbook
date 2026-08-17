# CMP-FIX-001 — Persistent Timer Recovery

**Type:** Reliability
**Priority:** P0
**Target:** v0.2.0
**Status:** Verification

## User problem

Starting a timer previously stored the active timer only in Streamlit session state. A browser/session reset or stopping the Streamlit process could therefore make an in-progress timer disappear without a completed activity record.

## Requirement

An active work session must be persisted independently of the Streamlit runtime. Elapsed time must be derived from persisted timestamps, not from an in-memory counter.

## Acceptance criteria

- Start immediately persists the active session.
- The displayed timer updates while the page remains open.
- Browser reload preserves the active session and correct elapsed time.
- Stopping and restarting Streamlit preserves the active session and correct elapsed time.
- Stop captures an immutable end timestamp immediately.
- A stopped session waiting for notes/status cannot be lost by a reload or app restart.
- Saving the stopped session creates exactly one activity-log record.

## System impact

Introduces a UI-independent runtime-state module under `compass_core/` and a local runtime-state JSON file under `data/`.

## Why now

Time analytics cannot be trusted if active sessions can silently disappear.
