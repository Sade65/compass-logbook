"""Persistent runtime state for timers.

This module deliberately has no Streamlit dependency. The current Streamlit UI
is one client of these operations; future clients can reuse the same behavior.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_STATE_FILE = Path("data/runtime_state.json")


def _empty_state() -> dict[str, Any]:
    return {
        "active_timer": None,
        "pending_sessions": [],
    }


def _iso_now(now: datetime | None = None) -> str:
    return (now or datetime.now()).isoformat(timespec="seconds")


def _session_id(now: datetime | None = None) -> str:
    stamp = now or datetime.now()
    return f"session_{stamp.strftime('%Y%m%d%H%M%S%f')}"


def load_runtime_state(state_file: Path = DEFAULT_STATE_FILE) -> dict[str, Any]:
    """Load timer runtime state, returning safe defaults if none exists."""
    if not state_file.exists() or state_file.stat().st_size == 0:
        return _empty_state()

    try:
        raw = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_state()

    state = _empty_state()
    state["active_timer"] = raw.get("active_timer")

    pending = raw.get("pending_sessions", [])
    if isinstance(pending, list):
        state["pending_sessions"] = pending

    return state


def save_runtime_state(
    state: dict[str, Any], state_file: Path = DEFAULT_STATE_FILE
) -> None:
    """Atomically persist runtime state to disk."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_suffix(state_file.suffix + ".tmp")
    temp_file.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp_file.replace(state_file)


def get_active_timer(state_file: Path = DEFAULT_STATE_FILE) -> dict[str, Any] | None:
    return load_runtime_state(state_file)["active_timer"]


def get_pending_sessions(state_file: Path = DEFAULT_STATE_FILE) -> list[dict[str, Any]]:
    return load_runtime_state(state_file)["pending_sessions"]


def start_timer(
    *,
    todo_id: str,
    task: str,
    todo_category: str,
    activity_type: str,
    now: datetime | None = None,
    state_file: Path = DEFAULT_STATE_FILE,
) -> dict[str, Any]:
    """Persist and return a newly started timer.

    Only one active timer is allowed at a time in the current single-user MVP.
    """
    state = load_runtime_state(state_file)
    if state["active_timer"] is not None:
        raise ValueError("Another timer is already running.")

    timer = {
        "session_id": _session_id(now),
        "todo_id": todo_id,
        "task": task,
        "todo_category": todo_category,
        "activity_type": activity_type,
        "start_time": _iso_now(now),
    }
    state["active_timer"] = timer
    save_runtime_state(state, state_file)
    return timer


def stop_timer(
    *,
    now: datetime | None = None,
    state_file: Path = DEFAULT_STATE_FILE,
) -> dict[str, Any] | None:
    """Stop the active timer immediately and persist it for later review."""
    state = load_runtime_state(state_file)
    active = state["active_timer"]
    if active is None:
        return None

    pending = dict(active)
    pending["end_time"] = _iso_now(now)

    state["active_timer"] = None
    state["pending_sessions"].append(pending)
    save_runtime_state(state, state_file)
    return pending


def remove_pending_session(
    session_id: str,
    *,
    state_file: Path = DEFAULT_STATE_FILE,
) -> None:
    """Remove one reviewed/saved pending session from runtime state."""
    state = load_runtime_state(state_file)
    state["pending_sessions"] = [
        session
        for session in state["pending_sessions"]
        if session.get("session_id") != session_id
    ]
    save_runtime_state(state, state_file)
