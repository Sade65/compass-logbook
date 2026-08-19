"""UI-independent helpers for historical and corrected activity records."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta


def _generate_id(prefix: str, now: datetime) -> str:
    return f"{prefix}_{now.strftime('%Y%m%d%H%M%S%f')}"


def build_retroactive_records(
    *,
    activity_date: date,
    task: str,
    category: str,
    planned_minutes: int,
    start_clock: time,
    end_clock: time,
    note: str = "",
    now: datetime | None = None,
) -> tuple[dict, dict]:
    """Build a closed historical Todo and its linked completed activity session.

    The UI treats this as a past activity. The linked Todo is a v0.2 compatibility
    mechanism so planned-vs-actual remains available without changing the CSV schema.
    """
    now = now or datetime.now()
    start_dt = datetime.combine(activity_date, start_clock)
    end_dt = datetime.combine(activity_date, end_clock)

    if end_dt <= start_dt:
        raise ValueError("End time must be later than start time for same-day entries.")

    duration_minutes = round((end_dt - start_dt).total_seconds() / 60, 2)
    todo_id = _generate_id("todo", now)
    session_id = _generate_id("session", now + timedelta(microseconds=1))

    todo_row = {
        "id": todo_id,
        "date": activity_date.isoformat(),
        "task": task,
        "category": category,
        "planned_minutes": int(planned_minutes),
        "status": "done",
        "created_at": now.isoformat(timespec="seconds"),
    }
    activity_row = {
        "id": session_id,
        "todo_id": todo_id,
        "date": activity_date.isoformat(),
        "task": task,
        "category": category,
        "start_time": start_dt.isoformat(timespec="seconds"),
        "end_time": end_dt.isoformat(timespec="seconds"),
        "duration_minutes": duration_minutes,
        "note_type": "Retroactive",
        "note": note,
        "completed": True,
        "created_at": now.isoformat(timespec="seconds"),
    }
    return todo_row, activity_row


def corrected_end_time(start_time_iso: str, actual_minutes: float) -> str:
    """Keep the original start time and derive a corrected end timestamp."""
    try:
        minutes = float(actual_minutes)
    except (TypeError, ValueError) as exc:
        raise ValueError("Actual minutes must be a number.") from exc

    if minutes <= 0:
        raise ValueError("Actual minutes must be greater than zero.")

    try:
        start_dt = datetime.fromisoformat(str(start_time_iso))
    except (TypeError, ValueError) as exc:
        raise ValueError("The selected session has an invalid start time.") from exc

    return (start_dt + timedelta(minutes=minutes)).isoformat(timespec="seconds")
