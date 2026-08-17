# Changelog

All notable Compass changes are documented here.

## [Unreleased]

### Added
- CMP-FEAT-035 per-session activity classification.
- Formal requirement register, roadmap, architecture notes, and ADR process.

### Changed
- CMP-UX-002 Todo creation form resets after successful creation.
- CMP-UX-003 today's Todos are shown newest first.
- CMP-FEAT-004 Todo cards show when they were added.

### Fixed
- CMP-FIX-001 active and stopped-but-unsaved timer state is persisted outside Streamlit session state.
- CMP-FIX-036 restarting work on a completed Todo reopens it and Stop captures the true end time immediately.
- CMP-UX-037 Streamlit developer toolbar is hidden in viewer mode to mitigate accidental Clear Cache actions while copying text.
