# Changelog

All notable Compass changes are documented here.

## [Unreleased]

### Added
- CMP-FEAT-105 puts first-class Quick Break capture directly on the Todos page; a Break is saved as its own activity/session with no Todo open/done semantics.
- CMP-FEAT-016 / CMP-UX-017 add a Lifecycle subscription MVP with cost, calendar-aware recurrence, next-charge date, days remaining, cycle progress, and Renewed-now reset.
- CMP-FEAT-019 adds opened consumable/perishable tracking with printed expiry, after-opening limits, expected lifespan, derived use-by date, and Finished/Discarded state changes.
- CMP-FEAT-047 adds a dedicated **Log past activity** flow for work remembered after the fact, while keeping planned-vs-actual compatibility through a linked closed Todo internally.
- CMP-FEAT-095 Todo cards surface the latest stop time and show the previous session duration when the same Todo is started again.
- CMP-FEAT-096 logged session duration can be corrected manually with a numeric − / + control; Compass preserves the original start and recalculates the end time.
- CMP-FEAT-012 Todo creation now defaults to today and exposes a calendar picker for future dates, with future Todos surfaced in Upcoming.
- CMP-FEAT-091 Quick Log can time a standalone Break and record an optional break-context note.
- CMP-FEAT-035 per-session activity classification.
- Formal requirement register, roadmap, architecture notes, and ADR process.

### Experimental
- CMP-UX-092 corrects the Premium UI page/section heading hierarchy for evaluation.
- CMP-UX-087 introduces a branch-isolated Premium UI v1A baseline for visual A/B evaluation; it does not change Compass Core or persisted data.

### Changed
- CMP-UX-093 Todo scheduling uses quick Today / Tomorrow choices and only reveals the full calendar for a custom future date; past work uses the retroactive activity flow instead.
- CMP-UX-094 activity logs display newest entries first while preserving chronological ordinals, so the first activity remains #1 and later activities retain their true sequence number. Today omits the redundant Date column and shows Actual before Planned.
- CMP-UX-084 Recent Check-Ins now use compact dates, readable labels, row numbers, and hide the raw dataframe index.
- CMP-UX-008 Activity Log columns now follow scan order: #, Date, Time, Activity, Task, Planned, Actual, Note.
- CMP-UX-083 adds a compact activity history for the previous five calendar days.
- CMP-UX-008 Activity Log now hides internal IDs and uses compact date/time, activity labels, and planned/actual duration.
- CMP-UX-043 live timers use a familiar minutes:seconds display.
- CMP-UX-082 Todo states are visually distinct and shown before task details.
- CMP-UX-002 Todo creation form resets after successful creation.
- CMP-UX-003 today's Todos are shown newest first.
- CMP-FEAT-004 Todo cards show when they were added.

### Fixed
- CMP-FIX-001 active and stopped-but-unsaved timer state is persisted outside Streamlit session state.
- CMP-FIX-036 restarting work on a completed Todo reopens it and Stop captures the true end time immediately.
- CMP-UX-037 Streamlit developer toolbar is hidden in viewer mode to mitigate accidental Clear Cache actions while copying text.

### Warm-up improvements (CMP-FEAT-098 / CMP-UX-099 / CMP-UX-100 / CMP-UX-101)
- Daily Check-In separates **went to bed / tried to sleep** from **actually fell asleep**, supports additional wake-up times, and records optional quantities for selected pre-bed substances.
- Medication and workplace-arrival checkboxes now reveal their time fields immediately instead of requiring an intermediate Save / Update.
- Morning rituals include **Bodyweight / home workout**.
- Check-in history removes redundant row-number columns and loads previous check-ins progressively in batches of five.
- Previous activity history is grouped into separate day clusters and can reveal five additional historical days at a time.
