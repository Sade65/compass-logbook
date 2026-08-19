# CMP-UX-087 — Premium UI Baseline

**Type:** UX / Design System
**Priority:** P2
**Status:** Experimental
**Target:** v0.2.x experiment

## Problem

Compass has accumulated useful functionality faster than a coherent visual system. Page branding, navigation symbols, status treatments, spacing, controls, and cards compete for attention and can make the application feel more like a prototype dashboard than a calm instrument.

## Requirement

Establish an experimental premium visual baseline without changing Compass Core or persisted user data. The experiment must be easy to compare against and discard independently of functional work.

## Experiment scope — v1A

- neutral dark color tokens with semantic accent/success/warning/danger colors
- 1240 px main content constraint and 232 px sidebar target
- restrained typography and spacing hierarchy
- simplified text-only navigation and removal of repeated global hero/tagline
- calmer Open / Done / Running status treatment
- running timer treated as the visual hero inside the active Todo
- completed Todo action wording changed to “Start another”
- category presentation made neutral while a future vector-icon layer is evaluated
- standardized card/control radii and control height

## Explicitly deferred

- Lucide integration across Streamlit navigation and activity rows
- full compact one-line Todo composer
- full logbook-style replacement of Streamlit dataframes
- mood/energy dot visualizations
- advanced micro-interactions beyond the subtle running-state pulse
- Pause/Resume or simultaneous-timer behavior

## Acceptance criteria

- experiment applies only to UI code/documentation; no personal data migration
- existing Todo/timer functionality continues to work
- current timer persistence still survives Streamlit restart
- Open, Done, and Running are visually distinguishable without emoji badges
- Todos page no longer repeats the Compass hero/tagline above the page content
- navigation is calmer and less symbol-heavy
- the experiment can be rejected simply by switching back to the parent branch

## Decision gate

After visual comparison, choose one of:

1. **Adopt** — merge the experiment and continue Premium UI v1B.
2. **Revise** — keep selected tokens/layout decisions and discard weaker changes.
3. **Reject** — return to the parent branch with no functional rollback required.
