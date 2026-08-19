# CMP-FEAT-047 — Retroactive Past Activity Entry

**Type:** Feature
**Priority:** P0
**Status:** Verification
**Target:** v0.2.x

## Problem

Real activity is not always logged live. The user may remember yesterday that a call, study block, or other activity happened and still wants it represented accurately in the day history and planned-vs-actual analytics.

## Requirement

Provide a dedicated **Log past activity** flow rather than treating past dates as ordinary future-facing Todos.

## Acceptance criteria

- Past date can be selected up to today.
- Activity, task, planned minutes, start, end, and optional note can be recorded.
- Same-day end time must be later than start time.
- Historical occurrence time is preserved independently of the time the record is entered into Compass.
- The activity appears in the appropriate day history without starting a live timer.
- v0.2 may create a linked closed Todo internally so existing planned-vs-actual lookup continues to work; this is an implementation compatibility detail, not the user-facing concept.
