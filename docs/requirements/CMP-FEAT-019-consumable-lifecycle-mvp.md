# CMP-FEAT-019 — Consumable / Perishable Lifecycle MVP

**Type:** Feature
**Priority:** P0
**Status:** Verification
**Target:** v0.2.x

## Requirement

Compass must capture when a consumable is opened and make its relevant use-by/restock window visible.

## Acceptance criteria

- Capture name, opened date/time, optional printed expiry date, optional `use within N days after opening`, optional expected lifespan, and notes.
- When both printed expiry and an after-opening limit exist, derive the earliest applicable use-by date.
- Show days remaining and a progress bar when a target exists; otherwise show how long the item has been open.
- `Finished now` and `Discarded` close the lifecycle while preserving history.
- Supports immediate real use cases such as milk and coffee beans without hard-coding those products.
