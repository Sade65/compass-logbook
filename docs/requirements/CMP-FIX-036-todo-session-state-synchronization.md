# CMP-FIX-036 — Todo / Session State Synchronization

**Type:** Reliability
**Priority:** P0
**Target:** v0.2.0
**Status:** Verification

## Observed behavior

A Todo could display `done` while a timer was actively running. Code inspection showed that a Todo previously marked done could be started again without reopening its Todo status.

## Root cause

Code inspection confirmed two state-transition gaps:

1. Saving a session with `No, keep open` did not explicitly set the Todo back to `open`; it only avoided setting it to `done`. A Todo that was already done therefore stayed done.
2. The Start action did not check/reopen a completed Todo, so a new running session could coexist with `status = done`.

## Requirement

Todo completion state and session timing state must remain logically consistent.

## Acceptance criteria

- Starting a Todo that is `done` automatically reopens it.
- Stop ends only the timing session.
- Choosing `No, keep open` explicitly leaves/reopens the Todo as `open`.
- Choosing `Yes, mark done` marks the Todo as `done`.
- A running Todo must not continue to display `done`.
- Session end time is captured at Stop, not when the post-session form is eventually saved.
