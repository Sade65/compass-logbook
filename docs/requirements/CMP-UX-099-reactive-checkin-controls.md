# CMP-UX-099 — Reactive Daily Check-In Controls

## Goal
Avoid requiring a save cycle merely to reveal dependent fields.

## Requirements
- Checking `Took medication today` immediately reveals the medication time input.
- Checking `Arrived at library/workplace` immediately reveals the arrival time input.
- Conditional inputs must remain visible and retain values across Streamlit reruns.
- Morning rituals are independent of medication state.
