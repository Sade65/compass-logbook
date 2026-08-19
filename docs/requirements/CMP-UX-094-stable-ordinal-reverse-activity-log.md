# CMP-UX-094 — Stable-Ordinal Reverse Activity Log

**Type:** UX
**Priority:** P1
**Status:** Verification
**Target:** v0.2.x

## Problem

Newest activity should be immediately visible, but renumbering the newest row as #1 destroys the chronological meaning of the record number.

## Requirement

Display activity newest-first while keeping ordinal numbers assigned in chronological order.

## Acceptance criteria

- First activity in the period remains #1.
- Later activities receive #2, #3, ... as they occur.
- Newest activity is displayed at the top with its actual ordinal.
- Today's table omits the redundant Date column.
- Today's scan order is `# | Time | Activity | Task | Actual | Planned | Note`.
- Recent-history table retains Date.
