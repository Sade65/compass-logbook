# CMP-FEAT-091 — Quick Break Activity Logging

## Problem
A short break should not require creating a Todo merely to capture its duration and context.

## Requirement
Quick Log shall support a standalone timed Break that writes to the canonical Activity Log.

## Acceptance criteria
- Quick Log exposes Start break and End break.
- Break timing uses the existing persistent timer state.
- The user may optionally record what happened during the break.
- Ending the break writes one Break activity row with duration and note.
- The current single-active-timer rule remains enforced until Pause/parallel timer semantics are explicitly designed.

## Status
Verification
