# CMP-ANL-107 — Daily Flow Bar

## Intent
Give the user an immediate visual read of how the current day unfolded without scanning the activity table.

## MVP requirements
- Render one horizontal chronological band for the selected/current day.
- Each persisted session is a segment positioned by its actual start and end timestamps.
- A currently running session may appear as a live/current segment ending at the current time.
- Color segments by activity type, with Break visually distinct.
- Hovering a segment exposes task, activity, start/end, duration, state, and note when available.
- Show the same reusable Flow Bar prominently on the Dashboard immediately below the Today metrics row, and retain it on the Todos page above the Todo cards.
- Preserve the detailed Activity Log below; this visualization is a summary, not a replacement.
- Hide Plotly's mode bar in the normal Compass UI.

## Future extensions
- Click a segment to open/edit the underlying Session.
- Selected-day navigation and Day Card integration.
- Work/break ratios, idle gaps, and Today Signals layered above the same canonical session data.
