# CMP-FEAT-098 — Sleep Detail and Ritual Quantities

## Goal
Capture richer sleep-context data without making the daily check-in mandatory or cumbersome.

## Requirements
- Store an optional `went_to_bed_at` separately from actual sleep onset (`slept_at`).
- Allow optional additional wake-up times for fragmented sleep.
- Allow quantities for selected pre-bed substances such as melatonin, magnesium, ashwagandha, and CBD.
- Preserve the existing lightweight CSV MVP while keeping these fields migration-friendly for a future normalized sleep/routine model.
