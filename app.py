from os import path
import json
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, time, timedelta

from compass_core.activity_records import build_retroactive_records, corrected_end_time
from compass_core.lifecycle import blank_lifecycle_row, consumable_snapshot, subscription_snapshot
from compass_core.runtime_state import (
    get_active_timer,
    get_pending_sessions,
    remove_pending_session,
    start_timer,
    stop_timer,
)

st.set_page_config(
    page_title="Compass",
    page_icon="🧭",
    layout="wide",
)

# Experimental Premium UI baseline (CMP-UX-087).
# Keep this visual layer separate from Compass Core so it is easy to A/B test or discard.
st.markdown(
    """
    <style>
    :root {
        --cmp-bg: #0B0D10;
        --cmp-sidebar: #0E1116;
        --cmp-surface-1: #11151B;
        --cmp-surface-2: #171C24;
        --cmp-surface-hover: #1B212B;
        --cmp-border: #252B35;
        --cmp-border-strong: #343C49;
        --cmp-text-primary: #F4F6F8;
        --cmp-text-secondary: #A6AEBA;
        --cmp-text-muted: #707986;
        --cmp-accent: #8BA4FF;
        --cmp-accent-soft: rgba(139, 164, 255, .12);
        --cmp-success: #54C985;
        --cmp-warning: #D7A24A;
        --cmp-danger: #F25F68;
    }

    html, body, [class*="css"] {
        font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .stApp {
        background: var(--cmp-bg);
        color: var(--cmp-text-primary);
    }

    [data-testid="stSidebar"] {
        background: var(--cmp-sidebar);
        border-right: 1px solid var(--cmp-border);
        width: 232px !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 232px !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1240px;
        padding-top: 2.25rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    h1 {
        font-size: 1.875rem !important;
        line-height: 2.25rem !important;
        font-weight: 650 !important;
    }

    [data-testid="stMainBlockContainer"] h2 {
        font-size: 1.875rem !important;
        line-height: 2.25rem !important;
        font-weight: 650 !important;
    }

    [data-testid="stMainBlockContainer"] h3 {
        font-size: 1.25rem !important;
        line-height: 1.625rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--cmp-border) !important;
        border-radius: 12px !important;
        background: var(--cmp-surface-1);
    }

    div[data-baseweb="select"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    textarea {
        background: var(--cmp-surface-2) !important;
        border-color: var(--cmp-border) !important;
        border-radius: 9px !important;
    }

    .stButton > button,
    [data-testid="stFormSubmitButton"] > button {
        min-height: 40px;
        border-radius: 9px !important;
        border-color: var(--cmp-border-strong) !important;
        transition: background 140ms ease, border-color 140ms ease;
    }

    .stButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        border-color: #3A4350 !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        min-height: 40px;
        border-radius: 9px;
        padding: 0 10px;
        color: var(--cmp-text-secondary);
        transition: background 140ms ease, color 140ms ease;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: var(--cmp-accent-soft);
        color: var(--cmp-text-primary);
    }

    .cmp-status {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        font-size: 12px;
        font-weight: 550;
        color: var(--cmp-text-secondary);
        white-space: nowrap;
    }

    .cmp-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 999px;
        background: currentColor;
        display: inline-block;
    }

    .cmp-status--open { color: var(--cmp-warning); }
    .cmp-status--done { color: var(--cmp-success); }
    .cmp-status--running { color: var(--cmp-accent); }

    @keyframes cmp-breathe {
        0%, 100% { opacity: .55; }
        50% { opacity: 1; }
    }

    .cmp-status--running .cmp-status-dot {
        animation: cmp-breathe 1.8s ease-in-out infinite;
    }

    .cmp-page-date {
        color: var(--cmp-text-muted);
        font-size: 13px;
        margin-top: -8px;
        margin-bottom: 24px;
    }

    .cmp-over-plan {
        color: var(--cmp-text-muted);
        font-size: 12px;
        font-variant-numeric: tabular-nums;
    }

    [data-testid="stMetricValue"],
    [data-testid="stDataFrame"],
    .cmp-timer {
        font-variant-numeric: tabular-nums;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CHECKINS_FILE = DATA_DIR / "daily_checkins.csv"
TODOS_FILE = DATA_DIR / "todos.csv"
ACTIVITY_LOGS_FILE = DATA_DIR / "activity_logs.csv"

# add counter logs file for tracking counts of specific events (e.g., cigarettes, medication, coffee)
COUNTER_LOGS_FILE = DATA_DIR / "counter_logs.csv"

CATEGORIES_FILE = DATA_DIR / "categories.csv"
LIFECYCLE_FILE = DATA_DIR / "lifecycle_items.csv"

def append_row(path: Path, row: dict) -> None:
    df = pd.DataFrame([row])
    header = not path.exists() or path.stat().st_size == 0
    df.to_csv(path, mode="a", index=False, header=header)


def append_unique_row(path: Path, row: dict, id_column: str = "id") -> bool:
    """Append a row only when its identifier is not already persisted."""
    existing = load_csv(path)
    row_id = str(row.get(id_column, ""))

    if (
        not existing.empty
        and id_column in existing.columns
        and row_id in existing[id_column].astype(str).values
    ):
        return False

    append_row(path, row)
    return True


def load_csv(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
         return pd.read_csv(path)
    return pd.DataFrame()


def generate_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


def update_row_by_id(path: Path, row_id: str, updates: dict, id_column: str = "id") -> bool:
    """Update one persisted row without changing its immutable identifier."""
    df = load_csv(path)
    if df.empty or id_column not in df.columns:
        return False

    mask = df[id_column].astype(str) == str(row_id)
    if not mask.any():
        return False

    for column, value in updates.items():
        if column not in df.columns:
            df[column] = ""
        df.loc[mask, column] = value
    df.to_csv(path, index=False)
    return True


def get_today_str() -> str:
    return date.today().isoformat()

DEFAULT_CATEGORIES = [
    "Studying",
    "Development / Coding",
    "Job Applications",
    "Communication",
    "Phone Call",
    "Admin",
    "Uni Research",
    "Break",
    "Exercise",
    "Personal",
    "Other",
]


def load_categories() -> list[str]:
    """Load saved categories, falling back to default categories."""
    categories = DEFAULT_CATEGORIES.copy()

    if CATEGORIES_FILE.exists() and CATEGORIES_FILE.stat().st_size > 0:
        df = pd.read_csv(CATEGORIES_FILE)
        if "category" in df.columns:
            saved_categories = df["category"].dropna().astype(str).tolist()
            categories.extend(saved_categories)

    # remove duplicates while preserving order
    unique_categories = []
    for category in categories:
        cleaned = category.strip()
        if cleaned and cleaned not in unique_categories:
            unique_categories.append(cleaned)

    return unique_categories


def save_category_if_new(category: str) -> None:
    """Save a new custom category if it does not already exist."""
    cleaned = category.strip()

    if not cleaned:
        return

    existing_categories = load_categories()

    if cleaned in existing_categories:
        return

    append_row(
        CATEGORIES_FILE,
        {
            "category": cleaned,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )


def normalize_time_text(value: str) -> str:
    """Return HH:MM if valid, otherwise empty string."""
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if value in ["", "None", "nan"]:
        return ""

    try:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.strftime("%H:%M")
    except ValueError:
        return value

def calculate_sleep_duration_text(slept_at: str, end_at: str) -> str:
    """Calculate rough sleep/window duration from HH:MM to HH:MM, handling overnight sleep."""
    slept_at = normalize_time_text(slept_at)
    end_at = normalize_time_text(end_at)

    if not slept_at or not end_at:
        return ""

    try:
        start_dt = datetime.strptime(slept_at, "%H:%M")
        end_dt = datetime.strptime(end_at, "%H:%M")

        # If wake/got-up time is earlier than sleep time, assume it is next day.
        if end_dt < start_dt:
            end_dt = end_dt + pd.Timedelta(days=1)

        total_minutes = int((end_dt - start_dt).total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f"{hours}h {minutes:02d}m"
    except Exception:
        return ""



def is_valid_time_text(value: str) -> bool:
    """Allow blank values or valid HH:MM time strings."""
    value = str(value).strip()

    if value == "":
        return True

    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False


def format_short_datetime(value) -> str:
    """Format ISO timestamp as short readable time."""
    if value is None or pd.isna(value) or str(value).strip() in ["", "None", "nan"]:
        return ""

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return ""

    return parsed.strftime("%b %d, %H:%M")


def format_time_or_missing(value: str) -> str:
    value = normalize_time_text(value)
    return value if value else "Not logged"


def get_checkin_for_date(checkin_date: date) -> dict:
    """Return the latest saved check-in for a date, or empty defaults."""
    df = load_csv(CHECKINS_FILE)
    date_str = checkin_date.isoformat()

    empty_checkin = {
        "date": date_str,
        "went_to_bed_at": "",
        "wake_up_time": "",
        "additional_wake_times": "",
        "got_out_of_bed_at": "",
        "slept_at": "",
        "prebed_rituals": "",
        "prebed_amounts": "",
        "sleep_note": "",
        "medication_taken": False,
        "morning_rituals": "",
        "morning_ritual_custom": "",
        "medication_at": "",
        "arrived_at": "",
        "mood": 3,
        "energy": 3,
        "main_focus": "",
        "notes": "",
        "created_at": "",
        "updated_at": "",
    }

    if df.empty or "date" not in df.columns:
        return empty_checkin

    df["date"] = df["date"].astype(str)
    existing = df[df["date"] == date_str].copy()

    if existing.empty:
        return empty_checkin

    sort_col = "updated_at" if "updated_at" in existing.columns else "created_at"

    if sort_col in existing.columns:
        existing[sort_col] = pd.to_datetime(existing[sort_col], errors="coerce")
        existing = existing.sort_values(sort_col, ascending=False)

    latest = existing.iloc[0].to_dict()

    for key, default_value in empty_checkin.items():
        if key not in latest or pd.isna(latest[key]) or latest[key] == "None":
            latest[key] = default_value

    latest["medication_taken"] = str(latest.get("medication_taken", "")).lower() in [
        "true",
        "1",
        "yes",
    ] or bool(normalize_time_text(latest.get("medication_at", "")))

    return latest


def save_daily_checkin(row: dict) -> None:
    """Create or update one visible daily check-in record per date."""
    df = load_csv(CHECKINS_FILE)
    row_date = str(row["date"])

    if df.empty:
        pd.DataFrame([row]).to_csv(CHECKINS_FILE, index=False)
        return

    if "date" not in df.columns:
        pd.DataFrame([row]).to_csv(CHECKINS_FILE, index=False)
        return

    df["date"] = df["date"].astype(str)

    # Remove older visible versions of this date, then append updated current state.
    df = df[df["date"] != row_date].copy()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    df.to_csv(CHECKINS_FILE, index=False)


def get_current_checkins() -> pd.DataFrame:
    """Return one latest check-in per date, newest dates first."""
    df = load_csv(CHECKINS_FILE)

    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = df["date"].astype(str)

    sort_col = "updated_at" if "updated_at" in df.columns else "created_at"

    if sort_col in df.columns:
        df[sort_col] = pd.to_datetime(df[sort_col], errors="coerce")
        df = df.sort_values(sort_col, ascending=False)

    df = df.drop_duplicates(subset=["date"], keep="first")
    df = df.sort_values("date", ascending=False)

    return df


def optional_formatted_column(df, column, formatter, default="Not logged"):
    if column in df.columns:
        return df[column].apply(formatter)
    return pd.Series([default] * len(df), index=df.index)


def build_checkin_display_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a compact, human-readable recent check-in table."""
    display_df = df.copy()

    display_df["Date"] = pd.to_datetime(
        display_df.get("date", ""), errors="coerce"
    ).dt.strftime("%d.%m.%y")

    display_df["Bed"] = optional_formatted_column(
    display_df,
    "went_to_bed_at",
    format_time_or_missing,
    )

    display_df["Sleep"] = display_df.get("slept_at", "").apply(format_time_or_missing)
    display_df["Wake"] = display_df.get("wake_up_time", "").apply(format_time_or_missing)
    display_df["Got up"] = display_df.get("got_out_of_bed_at", "").apply(format_time_or_missing)
    display_df["Sleep total"] = display_df.apply(
        lambda row: calculate_sleep_duration_text(
            row.get("slept_at", ""),
            row.get("got_out_of_bed_at", "") or row.get("wake_up_time", ""),
        ),
        axis=1,
    )
    display_df["Meds"] = display_df.get("medication_at", "").apply(format_time_or_missing)
    display_df["Arrived"] = display_df.get("arrived_at", "").apply(format_time_or_missing)
    display_df["Mood / Energy"] = (
        display_df.get("mood", "").astype(str)
        + " / "
        + display_df.get("energy", "").astype(str)
    )
    display_df["Rituals"] = display_df.get("morning_rituals", "").replace({"None": "—", "nan": "—"})
    display_df["Focus"] = display_df.get("main_focus", "").replace({"None": "—", "nan": "—"})

    columns = [
        "Date",
        "Bed",
        "Sleep",
        "Wake",
        "Got up",
        "Sleep total",
        "Meds",
        "Arrived",
        "Mood / Energy",
        "Rituals",
        "Focus",
    ]
    return display_df[[c for c in columns if c in display_df.columns]]


def parse_prebed_amounts(value) -> dict[str, str]:
    """Read flexible pre-bed substance quantities stored as JSON in the CSV MVP."""
    if value is None or pd.isna(value):
        return {}
    text = str(value).strip()
    if text in ["", "None", "nan"]:
        return {}
    try:
        parsed = json.loads(text)
        return {str(k): str(v) for k, v in parsed.items() if str(v).strip()} if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def valid_time_list(value: str) -> bool:
    """Validate an optional comma-separated list of HH:MM values."""
    text = str(value or "").strip()
    if not text:
        return True
    return all(is_valid_time_text(item.strip()) and item.strip() for item in text.split(","))


def split_csv_text(value: str) -> list[str]:
    """Convert a comma-separated string into a clean list."""
    if value is None or pd.isna(value):
        return []

    value = str(value).strip()

    if value in ["", "None", "nan"]:
        return []

    return [item.strip() for item in value.split(",") if item.strip()]


def set_todo_status(todo_id: str, status: str) -> None:
    """Persist a Todo status change."""
    todos_df = load_csv(TODOS_FILE)
    if todos_df.empty or "id" not in todos_df.columns:
        return

    todos_df.loc[todos_df["id"] == todo_id, "status"] = status
    todos_df.to_csv(TODOS_FILE, index=False)


def format_added_time(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "time unknown"
    return parsed.strftime("%H:%M")


def format_live_timer(start_time: datetime) -> tuple[int, int]:
    """Return elapsed whole minutes and seconds for a running timer."""
    elapsed_seconds = max(0, int((datetime.now() - start_time).total_seconds()))
    minutes, seconds = divmod(elapsed_seconds, 60)
    return minutes, seconds


def activity_display_name(category: str) -> str:
    """Return the human-readable category name without changing stored data."""
    return str(category).strip()


def format_session_duration(minutes_value) -> str:
    """Format a persisted session duration as a compact minutes/seconds label."""
    try:
        total_seconds = max(0, int(round(float(minutes_value) * 60)))
    except (TypeError, ValueError):
        return "?"

    minutes, seconds = divmod(total_seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        if seconds == 0:
            return f"{hours}h {minutes:02d}m"
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes}m {seconds:02d}s"


def build_todo_session_recaps(logs: pd.DataFrame) -> dict[str, dict]:
    """Return the latest persisted session recap for each Todo."""
    if logs.empty or "todo_id" not in logs.columns or "end_time" not in logs.columns:
        return {}

    recaps = logs.copy()
    recaps["_end_dt"] = pd.to_datetime(recaps["end_time"], errors="coerce")
    recaps["_duration"] = pd.to_numeric(
        recaps.get("duration_minutes"), errors="coerce"
    )
    recaps = recaps[recaps["_end_dt"].notna()].sort_values("_end_dt")
    if recaps.empty:
        return {}

    latest = recaps.groupby(recaps["todo_id"].astype(str), sort=False).tail(1)
    return {
        str(row["todo_id"]): {
            "last_end": row["_end_dt"],
            "last_duration": row["_duration"],
        }
        for _, row in latest.iterrows()
        if str(row.get("todo_id", "")).strip() not in ["", "nan", "None"]
    }


def number_activity_rows(logs: pd.DataFrame) -> pd.DataFrame:
    """Give rows a chronological ordinal while allowing newest-first presentation.

    The first activity in the supplied period remains #1. The newest item can be
    displayed at the top without being relabeled as #1.
    """
    numbered = logs.copy()
    numbered["_rank_start"] = pd.to_datetime(numbered["start_time"], errors="coerce")
    sort_columns = ["_rank_start"]
    if "created_at" in numbered.columns:
        sort_columns.append("created_at")
    numbered = numbered.sort_values(sort_columns, na_position="last")
    numbered["_display_number"] = range(1, len(numbered) + 1)
    return numbered


def build_activity_log_display(
    logs: pd.DataFrame,
    todos_lookup: pd.DataFrame,
    *,
    include_date: bool = True,
) -> pd.DataFrame:
    """Build a user-facing activity table while keeping internal IDs out of the UI."""
    display_logs = logs.copy()

    if not todos_lookup.empty and {"id", "planned_minutes"}.issubset(todos_lookup.columns):
        planned_lookup = (
            todos_lookup[["id", "planned_minutes"]]
            .drop_duplicates(subset=["id"], keep="last")
            .set_index("id")["planned_minutes"]
            .to_dict()
        )
        display_logs["Planned"] = display_logs["todo_id"].map(planned_lookup)
    else:
        display_logs["Planned"] = pd.NA

    start_dt = pd.to_datetime(display_logs["start_time"], errors="coerce")
    end_dt = pd.to_datetime(display_logs["end_time"], errors="coerce")
    if "_display_number" in display_logs.columns:
        display_logs["#"] = pd.to_numeric(
            display_logs["_display_number"], errors="coerce"
        ).astype("Int64")
    else:
        display_logs["#"] = range(1, len(display_logs) + 1)
    display_logs["Date"] = pd.to_datetime(
        display_logs["date"], errors="coerce"
    ).dt.strftime("%d.%m.%y")
    display_logs["Time"] = (
        start_dt.dt.strftime("%H:%M").fillna("?")
        + " → "
        + end_dt.dt.strftime("%H:%M").fillna("?")
    )
    display_logs["Activity"] = display_logs["category"].map(activity_display_name)
    display_logs["Actual"] = pd.to_numeric(
        display_logs["duration_minutes"], errors="coerce"
    ).round(1)

    display_logs = display_logs.rename(columns={"task": "Task", "note": "Note"})
    columns = ["#"]
    if include_date:
        columns.append("Date")
    columns.extend(["Time", "Activity", "Task", "Actual", "Planned", "Note"])
    return display_logs[[c for c in columns if c in display_logs.columns]]


@st.fragment(run_every="1s")
def render_today_todos() -> None:
    """Render today's Todo queue and keep an active timer visually live."""
    todos_df = load_csv(TODOS_FILE)

    if todos_df.empty:
        st.info("No todos for today yet. Add one above.")
        return

    today_todos = todos_df[todos_df["date"] == get_today_str()].copy()
    if today_todos.empty:
        st.info("No todos for today yet. Add one above.")
        return

    if "created_at" in today_todos.columns:
        today_todos = today_todos.sort_values("created_at", ascending=False)

    active_timer = get_active_timer()
    activity_options = load_categories()
    session_recaps = build_todo_session_recaps(load_csv(ACTIVITY_LOGS_FILE))

    for _, todo in today_todos.iterrows():
        todo_id = str(todo["id"])
        task_name = str(todo["task"])
        category_name = str(todo["category"])
        planned = int(todo["planned_minutes"])
        status = str(todo["status"])
        added_time = format_added_time(todo.get("created_at", ""))
        session_recap = session_recaps.get(todo_id)

        if category_name not in activity_options:
            activity_options_for_todo = [category_name] + activity_options
        else:
            activity_options_for_todo = activity_options

        with st.container(border=True):
            status_col, task_col, action_col, button_col = st.columns([1.1, 4.7, 2.4, 1.0])

            is_active = (
                active_timer is not None
                and str(active_timer.get("todo_id")) == todo_id
            )

            if is_active:
                status_col.markdown('<span class="cmp-status cmp-status--running"><span class="cmp-status-dot"></span>Running</span>', unsafe_allow_html=True)
            elif status == "done":
                status_col.markdown('<span class="cmp-status cmp-status--done"><span class="cmp-status-dot"></span>Done</span>', unsafe_allow_html=True)
            else:
                status_col.markdown('<span class="cmp-status cmp-status--open"><span class="cmp-status-dot"></span>Open</span>', unsafe_allow_html=True)

            task_col.markdown(f"**{task_name}**")
            todo_metadata = (
                f"{activity_display_name(category_name)} · planned {planned} min · added {added_time}"
            )
            if session_recap is not None:
                todo_metadata += f" · last stopped {session_recap['last_end'].strftime('%H:%M')}"
            task_col.caption(todo_metadata)

            if is_active:
                start_time = datetime.fromisoformat(active_timer["start_time"])
                elapsed_minutes, elapsed_seconds = format_live_timer(start_time)
                if session_recap is not None:
                    action_col.caption(
                        "Previous session · "
                        f"{format_session_duration(session_recap['last_duration'])} · "
                        f"stopped {session_recap['last_end'].strftime('%H:%M')}"
                    )
                else:
                    action_col.caption("Running")
                action_col.markdown(
                    f"<span class='cmp-timer' style='font-size:2.25rem;font-weight:650;line-height:1'>{elapsed_minutes}</span>"
                    f"<span class='cmp-timer' style='font-size:1.15rem;font-weight:550;color:#707986'>:{elapsed_seconds:02d}</span>",
                    unsafe_allow_html=True,
                )
                elapsed_total_seconds = elapsed_minutes * 60 + elapsed_seconds
                planned_seconds = planned * 60
                if elapsed_total_seconds > planned_seconds:
                    over_seconds = elapsed_total_seconds - planned_seconds
                    over_minutes, over_remainder = divmod(over_seconds, 60)
                    action_col.markdown(
                        f"<span class='cmp-over-plan'>+{over_minutes}:{over_remainder:02d} over plan</span>",
                        unsafe_allow_html=True,
                    )
                task_col.caption(
                    f"Current activity: {activity_display_name(active_timer.get('activity_type', category_name))}"
                )

                if button_col.button("Stop", key=f"stop_{todo_id}", type="primary"):
                    stop_timer()
                    st.rerun()
            else:
                default_index = activity_options_for_todo.index(category_name)
                activity_type = action_col.selectbox(
                    "Start as",
                    activity_options_for_todo,
                    index=default_index,
                    key=f"activity_type_{todo_id}",
                )

                start_label = "Start another" if status == "done" else "Start"

                if button_col.button(start_label, key=f"start_{todo_id}"):
                    if get_active_timer() is not None:
                        st.warning("Another timer is already running. Stop it first.")
                    else:
                        if status == "done":
                            set_todo_status(todo_id, "open")

                        start_timer(
                            todo_id=todo_id,
                            task=task_name,
                            todo_category=category_name,
                            activity_type=activity_type,
                        )
                        st.rerun()


@st.fragment(run_every="1s")
def render_quick_break() -> None:
    """Start/end a standalone Break session using the canonical activity log.

    The current MVP intentionally keeps the single-active-timer rule. If a Todo
    timer is running, Compass does not start an overlapping Break until the
    Pause/parallel-timer interaction model has been designed.
    """
    active_timer = get_active_timer()
    is_break = (
        active_timer is not None
        and str(active_timer.get("todo_id", "")) == "__quick_break__"
    )

    if is_break:
        start_dt = datetime.fromisoformat(active_timer["start_time"])
        elapsed_minutes, elapsed_seconds = format_live_timer(start_dt)
        col1, col2, col3 = st.columns([2.3, 1.4, 1.0])
        col1.markdown("**Break running**")
        col1.caption(f"Started {start_dt.strftime('%H:%M')}")
        col2.markdown(
            f"<span class='cmp-timer' style='font-size:1.8rem;font-weight:650'>{elapsed_minutes}</span>"
            f"<span class='cmp-timer' style='font-size:1rem;color:#707986'>:{elapsed_seconds:02d}</span>",
            unsafe_allow_html=True,
        )
        break_note = st.text_input(
            "What did you do during the break? (optional)",
            key="quick_break_note",
            placeholder="e.g. bathroom, lunch, spoke to a friend, messages",
        )
        if col3.button("End break", type="primary", use_container_width=True):
            pending = stop_timer()
            if pending is not None:
                stop_start = datetime.fromisoformat(pending["start_time"])
                stop_end = datetime.fromisoformat(pending["end_time"])
                duration_minutes = round(
                    (stop_end - stop_start).total_seconds() / 60, 2
                )
                append_unique_row(
                    ACTIVITY_LOGS_FILE,
                    {
                        "id": pending["session_id"],
                        "todo_id": "",
                        "date": stop_start.date().isoformat(),
                        "task": "Break",
                        "category": "Break",
                        "start_time": stop_start.isoformat(timespec="seconds"),
                        "end_time": stop_end.isoformat(timespec="seconds"),
                        "duration_minutes": duration_minutes,
                        "note_type": "Quick Log",
                        "note": break_note,
                        "completed": True,
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                    },
                )
                remove_pending_session(pending["session_id"])
                st.success(f"Break logged · {duration_minutes:.1f} min")
                st.rerun()
        return

    if active_timer is not None:
        st.caption(
            f"Current session: {active_timer.get('task', 'Activity')}. "
            "Starting a break will stop that work session now; the Todo itself stays open."
        )
        if st.button("Stop current & start break", use_container_width=False):
            stop_timer()
            start_timer(
                todo_id="__quick_break__",
                task="Break",
                todo_category="Break",
                activity_type="Break",
            )
            st.rerun()
        return

    if st.button("Start break", use_container_width=False):
        start_timer(
            todo_id="__quick_break__",
            task="Break",
            todo_category="Break",
            activity_type="Break",
        )
        st.rerun()



def _clean_lifecycle_value(value):
    if pd.isna(value):
        return ""
    return value


def _lifecycle_row(kind: str, name: str, **values) -> dict:
    row = blank_lifecycle_row()
    now_iso = datetime.now().isoformat(timespec="seconds")
    row.update(
        {
            "id": generate_id("life"),
            "kind": kind,
            "name": name.strip(),
            "status": "active" if kind == "subscription" else "opened",
            "created_at": now_iso,
            "updated_at": now_iso,
        }
    )
    row.update(values)
    return row


def render_subscription_cards(items: pd.DataFrame, *, compact: bool = False) -> None:
    if items.empty:
        if not compact:
            st.info("No subscriptions tracked yet.")
        return

    rows = []
    for _, raw in items.iterrows():
        item = {key: _clean_lifecycle_value(value) for key, value in raw.to_dict().items()}
        if not item.get("cycle_start"):
            continue
        try:
            snap = subscription_snapshot(item)
        except (ValueError, TypeError):
            continue
        rows.append((snap["next_charge"], item, snap))

    rows.sort(key=lambda value: value[0])
    if compact:
        rows = rows[:3]

    for _, item, snap in rows:
        with st.container(border=True):
            top1, top2 = st.columns([3.2, 1.2])
            top1.markdown(f"**{item.get('name', 'Subscription')}**")
            cost = item.get("cost", "")
            currency = item.get("currency", "")
            if cost not in ("", None):
                try:
                    cost_text = f"{float(cost):g} {currency}".strip()
                except (TypeError, ValueError):
                    cost_text = f"{cost} {currency}".strip()
                top1.caption(
                    f"{cost_text} · every {int(float(item.get('cycle_value', 1)))} "
                    f"{str(item.get('cycle_unit', 'Months')).lower()}"
                )
            days = snap["days_remaining"]
            top2.metric("Days left", days)
            start_text = date.fromisoformat(str(item["cycle_start"])).strftime("%d.%m.%y")
            next_text = snap["next_charge"].strftime("%d.%m.%y")
            st.caption(f"Cycle {start_text} → {next_text} · next charge {next_text}")
            st.progress(
                snap["progress"],
                text=f"{round(snap['progress'] * 100)}% of current billing cycle used",
            )
            note = str(item.get("note", "") or "").strip()
            if note and note.lower() != "nan":
                st.caption(note)
            if not compact:
                if st.button("Renewed now", key=f"renew_lifecycle_{item['id']}"):
                    update_row_by_id(
                        LIFECYCLE_FILE,
                        str(item["id"]),
                        {
                            "cycle_start": date.today().isoformat(),
                            "updated_at": datetime.now().isoformat(timespec="seconds"),
                        },
                    )
                    st.rerun()


def render_consumable_cards(items: pd.DataFrame, *, compact: bool = False) -> None:
    if items.empty:
        if not compact:
            st.info("No open consumables tracked yet.")
        return

    rows = []
    for _, raw in items.iterrows():
        item = {key: _clean_lifecycle_value(value) for key, value in raw.to_dict().items()}
        if not item.get("opened_at"):
            continue
        try:
            snap = consumable_snapshot(item)
        except (ValueError, TypeError):
            continue
        sort_date = snap["use_by"] or snap["expected_finish"] or date.max
        rows.append((sort_date, item, snap))

    rows.sort(key=lambda value: value[0])
    if compact:
        rows = rows[:3]

    for _, item, snap in rows:
        with st.container(border=True):
            top1, top2 = st.columns([3.2, 1.2])
            top1.markdown(f"**{item.get('name', 'Consumable')}**")
            opened_dt = datetime.fromisoformat(str(item["opened_at"]))
            top1.caption(
                f"Opened {opened_dt.strftime('%d.%m.%y %H:%M')} · open {snap['opened_days']} day(s)"
            )

            target = snap["use_by"] or snap["expected_finish"]
            if target is not None:
                label = "Use by" if snap["use_by"] is not None else "Expected finish"
                top2.metric("Days left", snap["days_remaining"])
                st.caption(f"{label}: {target.strftime('%d.%m.%y')}")
                if snap["progress"] is not None:
                    st.progress(
                        snap["progress"],
                        text=f"{round(snap['progress'] * 100)}% of current open-life window used",
                    )
            else:
                top2.metric("Open", f"{snap['opened_days']}d")
                st.caption("No expiry/open-life target set yet.")

            expiry = str(item.get("printed_expiry_date", "") or "").strip()
            use_days = item.get("use_within_days", "")
            details = []
            if expiry and expiry.lower() != "nan":
                try:
                    details.append(f"printed expiry {date.fromisoformat(expiry).strftime('%d.%m.%y')}")
                except ValueError:
                    pass
            try:
                if int(float(use_days or 0)) > 0:
                    details.append(f"use within {int(float(use_days))} days after opening")
            except (TypeError, ValueError):
                pass
            if details:
                st.caption(" · ".join(details))

            note = str(item.get("note", "") or "").strip()
            if note and note.lower() != "nan":
                st.caption(note)

            if not compact:
                c1, c2 = st.columns([1, 1])
                if c1.button("Finished now", key=f"finish_lifecycle_{item['id']}"):
                    now_iso = datetime.now().isoformat(timespec="seconds")
                    update_row_by_id(
                        LIFECYCLE_FILE,
                        str(item["id"]),
                        {"status": "finished", "finished_at": now_iso, "updated_at": now_iso},
                    )
                    st.rerun()
                if c2.button("Discarded", key=f"discard_lifecycle_{item['id']}"):
                    now_iso = datetime.now().isoformat(timespec="seconds")
                    update_row_by_id(
                        LIFECYCLE_FILE,
                        str(item["id"]),
                        {"status": "discarded", "finished_at": now_iso, "updated_at": now_iso},
                    )
                    st.rerun()


def render_lifecycle_overview(*, compact: bool = False) -> None:
    items = load_csv(LIFECYCLE_FILE)
    if items.empty:
        if not compact:
            st.info("No lifecycle items yet. Add Claude, milk, coffee, or another recurring item below.")
        return

    status = items.get("status", pd.Series(index=items.index, dtype=str)).astype(str)
    active = items[~status.isin(["finished", "discarded", "archived"])].copy()
    subscriptions = active[active.get("kind", "").astype(str) == "subscription"] if "kind" in active.columns else pd.DataFrame()
    consumables = active[active.get("kind", "").astype(str) == "consumable"] if "kind" in active.columns else pd.DataFrame()

    if compact:
        render_subscription_cards(subscriptions, compact=True)
        render_consumable_cards(consumables, compact=True)
    else:
        if not subscriptions.empty:
            st.markdown("#### Active subscriptions")
            render_subscription_cards(subscriptions)
        if not consumables.empty:
            st.markdown("#### Open consumables")
            render_consumable_cards(consumables)


def render_lifecycle_page() -> None:
    st.header("Lifecycle")
    st.caption("Keep recurring payments and opened consumables visible while their clocks are running.")

    render_lifecycle_overview()
    st.divider()

    subscription_tab, consumable_tab = st.tabs(["Add subscription", "Add consumable"])

    with subscription_tab:
        with st.form("add_subscription_form", clear_on_submit=True):
            name = st.text_input("Name", placeholder="e.g. Claude Pro")
            c1, c2 = st.columns(2)
            cost = c1.number_input("Cost", min_value=0.0, value=0.0, step=1.0)
            currency = c2.selectbox("Currency", ["EUR", "USD", "GBP", "IRR", "Toman"])
            cycle_start = st.date_input("Renewed / cycle started", value=date.today(), format="DD.MM.YYYY")
            c3, c4 = st.columns(2)
            cycle_value = c3.number_input("Recurring every", min_value=1, value=1, step=1)
            cycle_unit = c4.selectbox("Unit", ["Months", "Weeks", "Days", "Years"])
            c5, c6 = st.columns(2)
            reminder_days = c5.number_input("Remind me this many days before", min_value=0, value=3, step=1)
            auto_renew = c6.checkbox("Auto-renews", value=True)
            note = st.text_area("Notes", placeholder="Optional contract/account context")
            submitted = st.form_submit_button("Add subscription")

        if submitted:
            if not name.strip():
                st.warning("Please enter a subscription name.")
            else:
                row = _lifecycle_row(
                    "subscription",
                    name,
                    cost=float(cost),
                    currency=currency,
                    cycle_value=int(cycle_value),
                    cycle_unit=cycle_unit,
                    cycle_start=cycle_start.isoformat(),
                    reminder_days=int(reminder_days),
                    auto_renew=bool(auto_renew),
                    note=note.strip(),
                )
                append_row(LIFECYCLE_FILE, row)
                st.success(f"{name.strip()} added ✓")
                st.rerun()

    with consumable_tab:
        with st.form("add_consumable_form", clear_on_submit=True):
            name = st.text_input("Name", placeholder="e.g. Milk carton or Lavazza coffee beans", key="consumable_name")
            c1, c2 = st.columns(2)
            opened_date = c1.date_input("Opened date", value=date.today(), format="DD.MM.YYYY")
            opened_time = c2.time_input("Opened time", value=datetime.now().time().replace(second=0, microsecond=0), step=60)
            has_expiry = st.checkbox("Printed expiry date applies")
            printed_expiry = st.date_input(
                "Printed expiry date",
                value=date.today() + timedelta(days=7),
                format="DD.MM.YYYY",
                help="Ignored unless the checkbox above is selected.",
            )
            c3, c4 = st.columns(2)
            use_within_days = c3.number_input(
                "Use within N days after opening",
                min_value=0,
                value=0,
                step=1,
                help="Use 0 if no after-opening limit applies.",
            )
            expected_lifespan = c4.number_input(
                "Expected lifespan (days)",
                min_value=0,
                value=0,
                step=1,
                help="Useful for coffee or household stock; 0 means learn it from Finished later.",
            )
            note = st.text_area("Notes", placeholder="Brand, size, storage, etc.", key="consumable_note")
            submitted = st.form_submit_button("Add opened consumable")

        if submitted:
            if not name.strip():
                st.warning("Please enter an item name.")
            else:
                opened_at = datetime.combine(opened_date, opened_time)
                row = _lifecycle_row(
                    "consumable",
                    name,
                    opened_at=opened_at.isoformat(timespec="seconds"),
                    printed_expiry_date=printed_expiry.isoformat() if has_expiry else "",
                    use_within_days=int(use_within_days),
                    expected_lifespan_days=int(expected_lifespan),
                    note=note.strip(),
                )
                append_row(LIFECYCLE_FILE, row)
                st.success(f"{name.strip()} opened lifecycle started ✓")
                st.rerun()

st.sidebar.title("Compass")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Daily Check-In",
        "Todos",
        "Quick Log",
        "Lifecycle",
        "Analytics",
        "Export",
    ],
    label_visibility="collapsed",
)


if page == "Dashboard":
    st.header("Dashboard")

    current_checkins = get_current_checkins()

    if not current_checkins.empty:
        today_str = get_today_str()
        today_rows = current_checkins[current_checkins["date"] == today_str]

        if not today_rows.empty:
            latest = today_rows.iloc[0]
            st.subheader("Today")

            col1, col2, col3, col4, col5, col6 = st.columns(6)

            col1.metric("Slept", format_time_or_missing(latest.get("slept_at", "")))
            col2.metric("First wake", format_time_or_missing(latest.get("wake_up_time", "")))
            col3.metric("Got up", format_time_or_missing(latest.get("got_out_of_bed_at", "")))

            medication_label = (
                format_time_or_missing(latest.get("medication_at", ""))
                if str(latest.get("medication_taken", "")).lower() in ["true", "1", "yes"]
                or normalize_time_text(latest.get("medication_at", ""))
                else "Not taken/logged"
            )

            col4.metric("Medication", medication_label)
            col5.metric("Arrival", format_time_or_missing(latest.get("arrived_at", "")))
            col6.metric("Mood / Energy", f'{latest.get("mood", 3)} / {latest.get("energy", 3)}')

            sleep_total = calculate_sleep_duration_text(
                latest.get("slept_at", ""),
                latest.get("got_out_of_bed_at", "") or latest.get("wake_up_time", ""),
            )

            if sleep_total:
                st.caption(f"Sleep window: {sleep_total}")

        else:
            st.info("No check-in saved for today yet.")

        st.subheader("Recent Check-Ins")
        recent_display = build_checkin_display_table(current_checkins.head(5))
        st.dataframe(recent_display, use_container_width=True, hide_index=True)
    else:
        st.info("No check-ins yet. Add one in Daily Check-In.")

    lifecycle_items = load_csv(LIFECYCLE_FILE)
    if not lifecycle_items.empty:
        st.subheader("Lifecycle watch")
        render_lifecycle_overview(compact=True)

elif page == "Daily Check-In":
    st.header("Daily Check-In")

    selected_date = st.date_input("Date", value=date.today())
    existing_checkin = get_checkin_for_date(selected_date)

    st.caption(
        "One editable daily summary per date. Save partial notes now and update the same day later."
    )

    st.subheader("Sleep")

    went_to_bed_at = st.text_input(
        "Went to bed / tried to sleep at (HH:MM, optional)",
        value=normalize_time_text(existing_checkin.get("went_to_bed_at", "")),
        placeholder="e.g. 01:10",
        help="When you decided to try to sleep; separate from when you actually fell asleep.",
    )

    slept_at = st.text_input(
        "Actually fell asleep at (HH:MM, optional)",
        value=normalize_time_text(existing_checkin.get("slept_at", "")),
        placeholder="e.g. 01:30",
    )

    wake_up = st.text_input(
        "First woke up at (HH:MM, optional)",
        value=normalize_time_text(existing_checkin.get("wake_up_time", "")),
        placeholder="e.g. 08:30",
    )

    log_extra_wakes = st.checkbox(
        "Register additional wake-up(s)",
        value=bool(str(existing_checkin.get("additional_wake_times", "") or "").strip()),
    )
    additional_wake_times = ""
    if log_extra_wakes:
        additional_wake_times = st.text_input(
            "Additional wake times (HH:MM, comma separated)",
            value=str(existing_checkin.get("additional_wake_times", "") or ""),
            placeholder="e.g. 04:20, 06:10",
        )

    got_out_of_bed_at = st.text_input(
        "Got out of bed / day started at (HH:MM, optional)",
        value=normalize_time_text(existing_checkin.get("got_out_of_bed_at", "")),
        placeholder="e.g. 08:50",
    )

    with st.expander("Optional pre-bed / sleep ritual details"):
        prebed_rituals = st.multiselect(
            "Pre-bed rituals",
            [
                "Meditation",
                "Magnesium",
                "Ashwagandha",
                "CBD",
                "Melatonin",
                "Reading",
                "No phone before bed",
                "Stretching",
                "Other",
            ],
            default=split_csv_text(existing_checkin.get("prebed_rituals", "")),
        )
        saved_amounts = parse_prebed_amounts(existing_checkin.get("prebed_amounts", ""))
        prebed_amounts = {}
        for substance in ["Melatonin", "Magnesium", "Ashwagandha", "CBD"]:
            if substance in prebed_rituals:
                amount = st.text_input(
                    f"{substance} amount (optional)",
                    value=saved_amounts.get(substance, ""),
                    placeholder="e.g. 1.8 mg, 3 g, 10 drops",
                    key=f"prebed_amount_{selected_date.isoformat()}_{substance}",
                )
                if amount.strip():
                    prebed_amounts[substance] = amount.strip()

        sleep_note = st.text_area(
            "Sleep notes",
            value=str(existing_checkin.get("sleep_note", "") or ""),
            placeholder="e.g. woke up for WC, slept again, restless night",
        )

    st.subheader("Morning state")

    mood = st.slider(
        "Mood upon waking",
        1,
        5,
        int(existing_checkin.get("mood", 3)),
    )

    energy = st.slider(
        "Energy upon waking",
        1,
        5,
        int(existing_checkin.get("energy", 3)),
    )

    st.subheader("Medication")
    medication_taken = st.checkbox(
        "Took medication today",
        value=bool(existing_checkin.get("medication_taken", False)),
    )
    medication_at = ""
    if medication_taken:
        medication_at = st.text_input(
            "Medication taken at (HH:MM)",
            value=normalize_time_text(existing_checkin.get("medication_at", "")),
            placeholder="e.g. 09:15",
        )

    st.subheader("Morning ritual")
    morning_rituals = st.multiselect(
        "Did you do any morning rituals?",
        [
            "Meditation",
            "Stretching",
            "Breathwork",
            "Bodyweight / home workout",
            "Sunlight / walk",
            "Journaling",
            "Reading",
            "Other",
        ],
        default=split_csv_text(existing_checkin.get("morning_rituals", "")),
    )

    morning_ritual_custom = ""
    if "Other" in morning_rituals:
        morning_ritual_custom = st.text_input(
            "Custom morning ritual",
            value=str(existing_checkin.get("morning_ritual_custom", "") or ""),
            placeholder="e.g. cold shower, mobility, prayer, language practice",
        )

    st.subheader("Arrival / Workday start")
    arrived_logged = st.checkbox(
        "Arrived at library/workplace",
        value=bool(normalize_time_text(existing_checkin.get("arrived_at", ""))),
    )
    arrived_at = ""
    if arrived_logged:
        arrived_at = st.text_input(
            "Arrived at (HH:MM)",
            value=normalize_time_text(existing_checkin.get("arrived_at", "")),
            placeholder="e.g. 15:15",
        )

    st.subheader("Day orientation")
    main_focus = st.text_input(
        "Main focus today",
        value=str(existing_checkin.get("main_focus", "") or ""),
    )
    notes = st.text_area(
        "Notes",
        value=str(existing_checkin.get("notes", "") or ""),
    )

    submitted = st.button("Save / Update Daily Check-In", type="primary")

    if submitted:
        time_fields = {
            "Went to bed at": went_to_bed_at,
            "Actually fell asleep at": slept_at,
            "First woke up at": wake_up,
            "Got out of bed at": got_out_of_bed_at,
            "Medication taken at": medication_at,
            "Arrived at": arrived_at,
        }

        invalid_fields = [
            label for label, value in time_fields.items() if not is_valid_time_text(value)
        ]
        if not valid_time_list(additional_wake_times):
            invalid_fields.append("Additional wake times")

        if invalid_fields:
            st.error(
                "Please use HH:MM format for: "
                + ", ".join(invalid_fields)
                + ". Example: 15:15"
            )
        else:
            now = datetime.now().isoformat(timespec="seconds")
            created_at = existing_checkin.get("created_at", "")
            if not created_at or created_at == "None":
                created_at = now

            save_daily_checkin(
                {
                    "date": selected_date.isoformat(),
                    "went_to_bed_at": normalize_time_text(went_to_bed_at),
                    "wake_up_time": normalize_time_text(wake_up),
                    "additional_wake_times": additional_wake_times.strip() if log_extra_wakes else "",
                    "got_out_of_bed_at": normalize_time_text(got_out_of_bed_at),
                    "slept_at": normalize_time_text(slept_at),
                    "prebed_rituals": ", ".join(prebed_rituals),
                    "prebed_amounts": json.dumps(prebed_amounts, ensure_ascii=False),
                    "sleep_note": sleep_note,
                    "medication_taken": medication_taken,
                    "medication_at": normalize_time_text(medication_at) if medication_taken else "",
                    "morning_rituals": ", ".join(morning_rituals),
                    "morning_ritual_custom": morning_ritual_custom,
                    "arrived_at": normalize_time_text(arrived_at) if arrived_logged else "",
                    "mood": mood,
                    "energy": energy,
                    "main_focus": main_focus,
                    "notes": notes,
                    "created_at": created_at,
                    "updated_at": now,
                }
            )

            st.success("Daily check-in saved/updated.")
            st.rerun()

    current_checkins = get_current_checkins()

    if not current_checkins.empty:
        selected_date_str = selected_date.isoformat()
        selected_rows = current_checkins[current_checkins["date"] == selected_date_str]

        if not selected_rows.empty:
            st.subheader("Selected Day Summary")
            selected = selected_rows.iloc[0]

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("First wake", format_time_or_missing(selected.get("wake_up_time", "")))
            col2.metric("Got up", format_time_or_missing(selected.get("got_out_of_bed_at", "")))
            col3.metric("Medication", format_time_or_missing(selected.get("medication_at", "")))
            col4.metric("Arrival", format_time_or_missing(selected.get("arrived_at", "")))
            col5.metric("Mood / Energy", f'{selected.get("mood", 3)} / {selected.get("energy", 3)}')

            sleep_total = calculate_sleep_duration_text(
                selected.get("slept_at", ""),
                selected.get("got_out_of_bed_at", "") or selected.get("wake_up_time", ""),
            )
            if sleep_total:
                st.caption(f"Sleep window: {sleep_total}")

            bed_time = normalize_time_text(selected.get("went_to_bed_at", ""))
            if bed_time:
                st.caption(f"Went to bed: {bed_time} · Fell asleep: {format_time_or_missing(selected.get('slept_at', ''))}")
            if str(selected.get("additional_wake_times", "") or "").strip():
                st.caption(f"Additional wake-ups: {selected.get('additional_wake_times')}")

            st.caption(
                f"Last updated: {format_short_datetime(selected.get('updated_at', selected.get('created_at', '')))}"
            )

            ritual_summary = selected.get("morning_rituals", "")
            if selected.get("morning_ritual_custom", ""):
                ritual_summary = f"{ritual_summary}, {selected.get('morning_ritual_custom', '')}".strip(", ")
            if ritual_summary:
                st.caption(f"Morning ritual: {ritual_summary}")

            prebed_amount_summary = parse_prebed_amounts(selected.get("prebed_amounts", ""))
            if prebed_amount_summary:
                st.caption(
                    "Pre-bed amounts: "
                    + " · ".join(f"{name} {amount}" for name, amount in prebed_amount_summary.items())
                )

            st.write("Current saved record for this day:")
            st.dataframe(
                build_checkin_display_table(selected_rows),
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("Check-In History")
        previous = current_checkins[current_checkins["date"] != selected_date_str].copy()
        history_limit = int(st.session_state.get("checkin_history_limit", 5))
        visible_previous = previous.head(history_limit)

        if not visible_previous.empty:
            st.caption(f"Showing {len(visible_previous)} most recent previous check-in(s).")
            st.dataframe(
                build_checkin_display_table(visible_previous),
                use_container_width=True,
                hide_index=True,
            )
            if len(previous) > history_limit:
                if st.button("Show 5 older check-ins", key="show_older_checkins"):
                    st.session_state.checkin_history_limit = history_limit + 5
                    st.rerun()
        else:
            st.info("No previous check-ins yet.")

elif page == "Todos":
    st.header("Todos")
    st.markdown(
        f"<div class='cmp-page-date'>{date.today().strftime('%A, %d %B')}</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("**Quick break**")
        st.caption("Log a standalone break without creating a Break Todo.")
        render_quick_break()

    st.subheader("New todo")

    with st.form("add_todo_form", clear_on_submit=True):
        task = st.text_input("Task", placeholder="e.g. Study SQL joins")
        available_categories = load_categories()

        category_choice = st.selectbox(
            "Category",
            available_categories + ["Custom"],
        )

        if category_choice == "Custom":
            custom_category = st.text_input(
                "Custom category",
                placeholder="e.g. BWB Interview Prep, German Speaking, Life Admin",
            )
            category = custom_category.strip()
        else:
            category = category_choice

        planned_minutes = st.number_input(
            "Planned minutes",
            min_value=1,
            max_value=240,
            value=25,
            step=5,
        )

        date_mode = st.radio(
            "When",
            ["Today", "Tomorrow", "Pick date"],
            horizontal=True,
            help="Past work is logged separately below as an activity; Todos represent current or future intention.",
        )
        if date_mode == "Today":
            todo_date = date.today()
        elif date_mode == "Tomorrow":
            todo_date = date.today() + timedelta(days=1)
        else:
            date_col, _ = st.columns([1.2, 4.8])
            with date_col:
                todo_date = st.date_input(
                    "Date",
                    value=date.today() + timedelta(days=1),
                    min_value=date.today(),
                    format="DD.MM.YYYY",
                    help="Choose any future date.",
                )

        add_todo = st.form_submit_button("Add Todo")

        if add_todo:
            if not task.strip():
                st.warning("Please enter a task name.")
            elif not category:
                st.warning("Please choose or enter a category.")
            else:
                save_category_if_new(category)

                append_row(
                    TODOS_FILE,
                    {
                        "id": generate_id("todo"),
                        "date": todo_date.isoformat(),
                        "task": task.strip(),
                        "category": category,
                        "planned_minutes": int(planned_minutes),
                        "status": "open",
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                    },
                )
                st.success("Todo added ✓")

    with st.expander("Log past activity"):
        st.caption(
            "For work you already did. Compass records it as historical activity; "
            "a linked closed Todo is created internally for planned-vs-actual compatibility in v0.2."
        )
        with st.form("retroactive_activity_form", clear_on_submit=True):
            retro_date = st.date_input(
                "Activity date",
                value=date.today() - timedelta(days=1),
                max_value=date.today(),
                format="DD.MM.YYYY",
                key="retro_activity_date",
            )
            retro_task = st.text_input(
                "What did you do?",
                placeholder="e.g. Called repair service",
                key="retro_activity_task",
            )
            retro_categories = load_categories()
            retro_category_choice = st.selectbox(
                "Activity",
                retro_categories + ["Custom"],
                key="retro_activity_category",
            )
            if retro_category_choice == "Custom":
                retro_custom_category = st.text_input(
                    "Custom activity",
                    placeholder="e.g. Comedy Writing",
                    key="retro_activity_custom_category",
                )
                retro_category = retro_custom_category.strip()
            else:
                retro_category = retro_category_choice

            retro_planned = st.number_input(
                "Planned minutes",
                min_value=0,
                max_value=1440,
                value=0,
                step=5,
                help="Use 0 if this activity was not planned in advance.",
                key="retro_activity_planned",
            )
            time_col1, time_col2 = st.columns(2)
            with time_col1:
                retro_start = st.time_input(
                    "Start", value=time(12, 0), step=60, key="retro_activity_start"
                )
            with time_col2:
                retro_end = st.time_input(
                    "End", value=time(12, 30), step=60, key="retro_activity_end"
                )
            retro_note = st.text_area(
                "Note",
                placeholder="Optional context",
                key="retro_activity_note",
            )
            add_retroactive = st.form_submit_button("Log past activity")

        if add_retroactive:
            if not retro_task.strip():
                st.warning("Please describe the activity.")
            elif not retro_category:
                st.warning("Please choose or enter an activity type.")
            else:
                try:
                    todo_row, activity_row = build_retroactive_records(
                        activity_date=retro_date,
                        task=retro_task.strip(),
                        category=retro_category,
                        planned_minutes=int(retro_planned),
                        start_clock=retro_start,
                        end_clock=retro_end,
                        note=retro_note.strip(),
                    )
                except ValueError as exc:
                    st.warning(str(exc))
                else:
                    save_category_if_new(retro_category)
                    append_row(TODOS_FILE, todo_row)
                    append_unique_row(ACTIVITY_LOGS_FILE, activity_row)
                    st.success(
                        f"Past activity logged · {retro_date.strftime('%d.%m.%y')} · "
                        f"{retro_start.strftime('%H:%M')} → {retro_end.strftime('%H:%M')} ✓"
                    )
                    st.rerun()

    st.divider()
    st.subheader("Today's Todos")
    render_today_todos()

    todos_for_upcoming = load_csv(TODOS_FILE)
    if not todos_for_upcoming.empty and "date" in todos_for_upcoming.columns:
        todo_dates = pd.to_datetime(todos_for_upcoming["date"], errors="coerce")
        upcoming = todos_for_upcoming[
            (todo_dates > pd.Timestamp(get_today_str()))
            & (todos_for_upcoming["status"].astype(str) != "done")
        ].copy()
        if not upcoming.empty:
            upcoming["Date"] = pd.to_datetime(
                upcoming["date"], errors="coerce"
            ).dt.strftime("%d.%m.%y")
            upcoming = upcoming.rename(
                columns={
                    "task": "Task",
                    "category": "Activity",
                    "planned_minutes": "Planned",
                }
            )
            upcoming = upcoming.sort_values("date").head(12)
            with st.expander(f"Upcoming · {len(upcoming)} scheduled todo(s)"):
                st.dataframe(
                    upcoming[["Date", "Task", "Activity", "Planned"]],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Planned": st.column_config.NumberColumn(
                            "Planned", format="%d min"
                        )
                    },
                )

    pending_sessions = get_pending_sessions()
    if pending_sessions:
        pending = pending_sessions[0]
        st.divider()
        st.subheader("Save Completed Session")

        stop_start = datetime.fromisoformat(pending["start_time"])
        stop_end = datetime.fromisoformat(pending["end_time"])
        duration_minutes = round((stop_end - stop_start).total_seconds() / 60, 2)
        activity_type = pending.get(
            "activity_type", pending.get("todo_category", "Other")
        )

        st.info(
            f"Session: {pending['task']} · {activity_type} · {duration_minutes} minutes"
        )
        if len(pending_sessions) > 1:
            st.caption(
                f"{len(pending_sessions) - 1} additional stopped session(s) are waiting to be reviewed."
            )

        with st.form(f"save_session_form_{pending['session_id']}"):
            note_type = st.selectbox(
                "Note type",
                ["General", "Observation", "Idea", "Todo", "Person", "Event"],
            )
            note = st.text_area("Notes", placeholder="What happened during this session?")
            completed = st.radio(
                "Did you finish the task?",
                ["No, keep open", "Yes, mark done"],
                horizontal=True,
            )

            save_session = st.form_submit_button("Save Session")

        if save_session:
            append_unique_row(
                ACTIVITY_LOGS_FILE,
                {
                    "id": pending["session_id"],
                    "todo_id": pending["todo_id"],
                    "date": stop_start.date().isoformat(),
                    "task": pending["task"],
                    "category": activity_type,
                    "start_time": stop_start.isoformat(timespec="seconds"),
                    "end_time": stop_end.isoformat(timespec="seconds"),
                    "duration_minutes": duration_minutes,
                    "note_type": note_type,
                    "note": note,
                    "completed": completed == "Yes, mark done",
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                },
            )

            if completed == "Yes, mark done":
                set_todo_status(str(pending["todo_id"]), "done")
            else:
                set_todo_status(str(pending["todo_id"]), "open")

            remove_pending_session(pending["session_id"])
            st.success("Session saved.")
            st.rerun()

    st.divider()
    st.subheader("Today's Activity Log")

    logs_df = load_csv(ACTIVITY_LOGS_FILE)
    if not logs_df.empty:
        todos_lookup = load_csv(TODOS_FILE)
        today = pd.Timestamp(get_today_str())
        log_dates = pd.to_datetime(logs_df["date"], errors="coerce")

        today_logs = logs_df[log_dates == today].copy()
        if not today_logs.empty:
            today_logs = number_activity_rows(today_logs)
            today_logs = today_logs.sort_values("_rank_start", ascending=False).head(20)
            today_display = build_activity_log_display(
                today_logs, todos_lookup, include_date=False
            )
            st.dataframe(
                today_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn("#", format="%d"),
                    "Planned": st.column_config.NumberColumn("Planned", format="%d min"),
                    "Actual": st.column_config.NumberColumn("Actual", format="%.1f min"),
                },
            )
        else:
            st.info("No activity sessions logged today yet.")

        st.subheader("Activity History by Day")
        previous_logs = logs_df[log_dates < today].copy()
        if not previous_logs.empty:
            previous_logs["_date_dt"] = pd.to_datetime(previous_logs["date"], errors="coerce")
            available_days = [
                day for day in previous_logs["_date_dt"].dropna().dt.normalize().drop_duplicates().sort_values(ascending=False).tolist()
            ]
            day_limit = int(st.session_state.get("activity_history_days_limit", 5))
            visible_days = available_days[:day_limit]

            for day_value in visible_days:
                day_logs = previous_logs[previous_logs["_date_dt"].dt.normalize() == day_value].copy()
                day_logs = number_activity_rows(day_logs)
                day_logs = day_logs.sort_values("_rank_start", ascending=False)
                day_display = build_activity_log_display(day_logs, todos_lookup, include_date=False)
                st.markdown(f"**{day_value.strftime('%A · %d.%m.%y')}**")
                st.dataframe(
                    day_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "#": st.column_config.NumberColumn("#", format="%d"),
                        "Planned": st.column_config.NumberColumn("Planned", format="%d min"),
                        "Actual": st.column_config.NumberColumn("Actual", format="%.1f min"),
                    },
                )

            if len(available_days) > day_limit:
                if st.button("Show 5 older activity days", key="show_older_activity_days"):
                    st.session_state.activity_history_days_limit = day_limit + 5
                    st.rerun()
        else:
            st.caption("No activity sessions from previous days yet.")

        with st.expander("Correct logged time"):
            st.caption(
                "Use this when you stopped a timer late or need to correct the recorded duration. "
                "Changing Actual keeps the original start time and recalculates the end time."
            )
            editable_logs = logs_df.copy()
            editable_logs["_start_dt"] = pd.to_datetime(
                editable_logs["start_time"], errors="coerce"
            )
            editable_logs = editable_logs.sort_values("_start_dt", ascending=False).head(50)
            editable_logs = editable_logs[editable_logs["id"].notna()]

            if editable_logs.empty:
                st.caption("No logged sessions available to edit.")
            else:
                session_ids = editable_logs["id"].astype(str).tolist()
                session_lookup = editable_logs.set_index(editable_logs["id"].astype(str))

                def _session_label(session_id: str) -> str:
                    row = session_lookup.loc[session_id]
                    start_dt = pd.to_datetime(row.get("start_time"), errors="coerce")
                    date_label = start_dt.strftime("%d.%m") if not pd.isna(start_dt) else "?"
                    time_label = start_dt.strftime("%H:%M") if not pd.isna(start_dt) else "?"
                    return (
                        f"{date_label} {time_label} · {row.get('category', 'Other')} · "
                        f"{row.get('task', 'Activity')}"
                    )

                selected_session_id = st.selectbox(
                    "Session", session_ids, format_func=_session_label
                )
                selected_row = session_lookup.loc[selected_session_id]
                current_actual_value = pd.to_numeric(
                    selected_row.get("duration_minutes"), errors="coerce"
                )
                current_actual = (
                    float(current_actual_value) if not pd.isna(current_actual_value) else 0.0
                )
                corrected_minutes = st.number_input(
                    "Actual minutes",
                    min_value=0.1,
                    max_value=1440.0,
                    value=round(current_actual, 1),
                    step=1.0,
                    format="%.1f",
                    help="Use the − / + controls or type the corrected duration.",
                    key=f"correct_duration_{selected_session_id}",
                )
                if st.button("Save corrected time", key=f"save_duration_{selected_session_id}"):
                    row_mask = logs_df["id"].astype(str) == selected_session_id
                    start_value = logs_df.loc[row_mask, "start_time"].iloc[0]
                    try:
                        new_end = corrected_end_time(start_value, corrected_minutes)
                    except ValueError as exc:
                        st.warning(str(exc))
                    else:
                        logs_df.loc[row_mask, "duration_minutes"] = round(
                            float(corrected_minutes), 2
                        )
                        logs_df.loc[row_mask, "end_time"] = new_end
                        logs_df.to_csv(ACTIVITY_LOGS_FILE, index=False)
                        st.success(
                            f"Corrected to {float(corrected_minutes):.1f} min ✓"
                        )
                        st.rerun()
    else:
        st.info("No activity sessions logged yet.")

elif page == "Quick Log":
    st.header("Quick Log")
    st.caption("One-click timestamp logs for small recurring events.")

    st.subheader("Break")
    render_quick_break()

    st.divider()
    st.subheader("Timestamp Quick Log")

    note = st.text_input(
        "Optional note",
        placeholder="e.g. after lunch, morning dose, before study session",
    )

    col1, col2, col3, col4 = st.columns(4)

    quick_log_options = [
        ("🚬 Cigarette", "Cigarette", col1),
        ("💊 Medication", "Medication", col2),
        ("☕ Coffee", "Coffee", col3),
        ("💊 Supplement", "Supplement", col4),
    ]

    for button_label, category, col in quick_log_options:
        if col.button(button_label, use_container_width=True):
            now = datetime.now()
            append_row(
                COUNTER_LOGS_FILE,
                {
                    "id": generate_id("counter"),
                    "date": get_today_str(),
                    "category": category,
                    "timestamp": now.isoformat(timespec="seconds"),
                    "note": note,
                    "created_at": now.isoformat(timespec="seconds"),
                },
            )
            st.success(f"{category} logged at {now.strftime('%H:%M')}.")

    st.divider()
    st.subheader("Today's Quick Logs")

    counter_df = load_csv(COUNTER_LOGS_FILE)

    if counter_df.empty:
        st.info("No quick logs yet.")
    else:
        today_logs = counter_df[counter_df["date"] == get_today_str()].copy()

        if today_logs.empty:
            st.info("No quick logs for today yet.")
        else:
            counts = today_logs["category"].value_counts()

            metric_cols = st.columns(4)
            metric_cols[0].metric("Cigarettes", int(counts.get("Cigarette", 0)))
            metric_cols[1].metric("Medication", int(counts.get("Medication", 0)))
            metric_cols[2].metric("Coffee", int(counts.get("Coffee", 0)))
            metric_cols[3].metric("Supplements", int(counts.get("Supplement", 0)))

            display_df = today_logs[["timestamp", "category", "note"]].copy()
            display_df["timestamp"] = pd.to_datetime(display_df["timestamp"]).dt.strftime("%H:%M")

            st.dataframe(
                display_df.sort_values("timestamp", ascending=False),
                use_container_width=True,
            )

elif page == "Lifecycle":
    render_lifecycle_page()

elif page == "Analytics":
    st.header("Analytics")
    st.write("Next: wake-up trend, activity time, and counter charts.")

elif page == "Export":
    st.header("Export")
    st.write("Next: generate daily text reports.")