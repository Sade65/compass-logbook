# CMP-FEAT-096 — Correct Logged Session Duration

**Type:** Feature
**Priority:** P1
**Status:** Verification
**Target:** v0.2.x

## Problem

A live timer can be stopped late or the remembered actual duration may be slightly different from the recorded interval.

## Requirement

Allow a persisted session's Actual minutes to be corrected after logging.

## Acceptance criteria

- User can select a recent persisted session.
- Actual minutes can be typed or adjusted with the number control's − / + buttons.
- Saving changes `duration_minutes`.
- Original start time stays fixed.
- End time is recalculated from start + corrected duration so the displayed interval remains internally consistent.
- Correction does not create a duplicate session.
