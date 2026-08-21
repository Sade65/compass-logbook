"""UI-independent lifecycle calculations for subscriptions and consumables."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from dateutil.relativedelta import relativedelta


LIFECYCLE_COLUMNS = [
    "id",
    "kind",
    "name",
    "status",
    "cost",
    "currency",
    "cycle_value",
    "cycle_unit",
    "cycle_start",
    "reminder_days",
    "auto_renew",
    "opened_at",
    "printed_expiry_date",
    "use_within_days",
    "expected_lifespan_days",
    "finished_at",
    "note",
    "created_at",
    "updated_at",
]


def add_calendar_interval(start: date, value: int, unit: str) -> date:
    """Add a recurring interval, preserving calendar-month/year semantics."""
    value = int(value)
    if value <= 0:
        raise ValueError("Recurring interval must be greater than zero.")

    normalized = str(unit).strip().lower()
    if normalized in {"day", "days"}:
        return start + timedelta(days=value)
    if normalized in {"week", "weeks"}:
        return start + timedelta(weeks=value)
    if normalized in {"month", "months"}:
        return start + relativedelta(months=value)
    if normalized in {"year", "years"}:
        return start + relativedelta(years=value)
    raise ValueError(f"Unsupported recurring unit: {unit}")


def progress_fraction(start: datetime, end: datetime, now: datetime) -> float:
    """Return elapsed fraction within a time window, clamped to 0..1."""
    total = (end - start).total_seconds()
    if total <= 0:
        return 1.0
    elapsed = (now - start).total_seconds()
    return max(0.0, min(1.0, elapsed / total))


def subscription_snapshot(item: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    """Derive next charge, remaining days, and cycle progress for a subscription."""
    today = today or date.today()
    cycle_start = date.fromisoformat(str(item["cycle_start"]))
    next_charge = add_calendar_interval(
        cycle_start,
        int(float(item.get("cycle_value", 1))),
        str(item.get("cycle_unit", "Months")),
    )
    start_dt = datetime.combine(cycle_start, datetime.min.time())
    end_dt = datetime.combine(next_charge, datetime.min.time())
    now_dt = datetime.combine(today, datetime.min.time())
    return {
        "next_charge": next_charge,
        "days_remaining": (next_charge - today).days,
        "progress": progress_fraction(start_dt, end_dt, now_dt),
    }


def effective_use_by(
    *,
    opened_at: datetime,
    printed_expiry_date: date | None = None,
    use_within_days: int = 0,
) -> date | None:
    """Return the earliest applicable safety/use-by limit."""
    candidates: list[date] = []
    if printed_expiry_date is not None:
        candidates.append(printed_expiry_date)
    if int(use_within_days or 0) > 0:
        candidates.append(opened_at.date() + timedelta(days=int(use_within_days)))
    return min(candidates) if candidates else None


def consumable_snapshot(
    item: dict[str, Any], now: datetime | None = None
) -> dict[str, Any]:
    """Derive opened age, effective use-by, forecast, and progress for a consumable."""
    now = now or datetime.now()
    opened_at = datetime.fromisoformat(str(item["opened_at"]))

    expiry_raw = item.get("printed_expiry_date")
    expiry = None
    if expiry_raw not in (None, "", "nan"):
        expiry = date.fromisoformat(str(expiry_raw))

    use_within = int(float(item.get("use_within_days", 0) or 0))
    expected = int(float(item.get("expected_lifespan_days", 0) or 0))
    use_by = effective_use_by(
        opened_at=opened_at,
        printed_expiry_date=expiry,
        use_within_days=use_within,
    )

    expected_finish = (
        opened_at.date() + timedelta(days=expected) if expected > 0 else None
    )
    target = use_by or expected_finish
    progress = None
    days_remaining = None
    if target is not None:
        end_dt = datetime.combine(target, datetime.min.time())
        progress = progress_fraction(opened_at, end_dt, now)
        days_remaining = (target - now.date()).days

    return {
        "opened_days": max(0, (now.date() - opened_at.date()).days),
        "use_by": use_by,
        "expected_finish": expected_finish,
        "days_remaining": days_remaining,
        "progress": progress,
    }


def blank_lifecycle_row() -> dict[str, Any]:
    return {column: "" for column in LIFECYCLE_COLUMNS}
