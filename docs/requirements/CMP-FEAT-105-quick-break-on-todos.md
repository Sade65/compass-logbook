# CMP-FEAT-105 — Quick Break Capture on Todos

**Type:** Feature / UX
**Priority:** P0
**Status:** Verification
**Target:** v0.2.x

## Requirement

The Todos page must provide a low-friction Break action without requiring a reusable Break Todo.

## Acceptance criteria

- `Start break` is directly available on the Todos page.
- When no timer is active, it starts a standalone Break session immediately.
- When a work timer is active, `Stop current & start break` stops that session at the real current time and begins the Break; the underlying Todo remains open.
- `End break` persists the Break directly into the canonical Activity Log with start, end, duration, and optional context note.
- Breaks do not ask `keep open` / `done` because those are Todo-level semantics.
- Each Break is a separate activity/session and can be logged again later.
