# CMP-FEAT-016 — Subscription Lifecycle MVP

**Type:** Feature
**Priority:** P0
**Status:** Verification
**Target:** v0.2.x

## Requirement

Compass must make active subscription cycles visible enough that renewal windows and costs do not have to be remembered mentally.

## Acceptance criteria

- Capture name, cost, currency, cycle-start/renewal date, recurring value/unit, reminder lead time, auto-renew flag, and notes.
- Calendar-aware recurring months/years are used rather than treating a month as a fixed 30 days.
- Derive and display next charge date, days remaining, and cycle progress.
- `Renewed now` resets the cycle start without creating a new subscription identity.
- Active lifecycle items can be surfaced on the Dashboard and Lifecycle page.
