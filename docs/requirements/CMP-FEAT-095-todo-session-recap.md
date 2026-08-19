# CMP-FEAT-095 — Todo Session Recap Metadata

**Type:** Feature / UX
**Priority:** P1
**Status:** Verification
**Target:** v0.2.x

## Requirement

Surface prior work context when one Todo has multiple sessions.

## Acceptance criteria

- Todo metadata shows `last stopped HH:MM` after at least one saved session.
- Starting another session begins at zero as a new measured work session.
- While the new session is running, the previous saved session duration and stop time are visible above the live timer.
- Previous duration is contextual history and is not added into the new live timer.
