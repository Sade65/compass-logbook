from os import path
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, time

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

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CHECKINS_FILE = DATA_DIR / "daily_checkins.csv"
TODOS_FILE = DATA_DIR / "todos.csv"
ACTIVITY_LOGS_FILE = DATA_DIR / "activity_logs.csv"

# add counter logs file for tracking counts of specific events (e.g., cigarettes, medication, coffee)
COUNTER_LOGS_FILE = DATA_DIR / "counter_logs.csv"

CATEGORIES_FILE = DATA_DIR / "categories.csv"

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
        "wake_up_time": "",
        "got_out_of_bed_at": "",
        "slept_at": "",
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


def build_checkin_display_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a cleaner UI table for check-ins."""
    if df.empty:
        return df

    display_df = df.copy()

    if "updated_at" in display_df.columns:
        display_df["updated"] = display_df["updated_at"].apply(format_short_datetime)
    elif "created_at" in display_df.columns:
        display_df["updated"] = display_df["created_at"].apply(format_short_datetime)
    else:
        display_df["updated"] = ""

    display_df["mood_energy"] = (
        display_df.get("mood", "").astype(str)
        + " / "
        + display_df.get("energy", "").astype(str)
    )

    # Prefer got-out-of-bed time for sleep window. Fall back to wake-up time.
    display_df["sleep_total"] = display_df.apply(
        lambda row: calculate_sleep_duration_text(
            row.get("slept_at", ""),
            row.get("got_out_of_bed_at", "") or row.get("wake_up_time", ""),
        ),
        axis=1,
    )

    preferred_cols = [
        "updated",
        "date",
        "slept_at",
        "wake_up_time",
        "got_out_of_bed_at",
        "sleep_total",
        "medication_at",
        "morning_rituals",
        "arrived_at",
        "mood_energy",
        "main_focus",
        "notes",
    ]

    existing_cols = [col for col in preferred_cols if col in display_df.columns]
    display_df = display_df[existing_cols]

    display_df = display_df.rename(
        columns={
            "slept_at": "t_sleep",
            "wake_up_time": "t_wake",
            "got_out_of_bed_at": "t_got_up",
            "medication_at": "t_meds",
            "arrived_at": "t_arrive",
            "morning_rituals": "rituals",
            "main_focus": "focus",
            "mood_energy": "mood/energy",
        }
    )

    return display_df


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
    """Return a compact, scan-friendly label without changing stored data."""
    normalized = str(category).strip().lower()
    icon_map = {
        "communication": "📞",
        "break": "☕",
        "development / coding": "💻",
        "development/coding": "💻",
        "coding/dev": "💻",
        "studying": "📚",
        "study / learning": "📚",
        "study": "📚",
        "research": "🔎",
        "admin": "🗂️",
        "shopping": "🛒",
        "personal": "👤",
        "health / fitness": "🏃",
        "social": "👥",
        "travel / commute": "🚉",
        "other": "•",
    }
    return f"{icon_map.get(normalized, '🏷️')} {category}"


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

    for _, todo in today_todos.iterrows():
        todo_id = str(todo["id"])
        task_name = str(todo["task"])
        category_name = str(todo["category"])
        planned = int(todo["planned_minutes"])
        status = str(todo["status"])
        added_time = format_added_time(todo.get("created_at", ""))

        if category_name not in activity_options:
            activity_options_for_todo = [category_name] + activity_options
        else:
            activity_options_for_todo = activity_options

        with st.container(border=True):
            status_col, task_col, action_col, button_col = st.columns([1.25, 4.3, 2.2, 1.1])

            is_active = (
                active_timer is not None
                and str(active_timer.get("todo_id")) == todo_id
            )

            if is_active:
                status_col.markdown("▶️ **RUNNING**")
            elif status == "done":
                status_col.markdown("✅ **DONE**")
            else:
                status_col.markdown("🟠 **OPEN**")

            task_col.markdown(f"**{task_name}**")
            task_col.caption(
                f"{activity_display_name(category_name)} · planned {planned} min · added {added_time}"
            )

            if is_active:
                start_time = datetime.fromisoformat(active_timer["start_time"])
                elapsed_minutes, elapsed_seconds = format_live_timer(start_time)
                action_col.caption("Running · min:sec")
                action_col.markdown(
                    f"<span style='font-size:2.35rem;font-weight:700;line-height:1'>{elapsed_minutes}</span>"
                    f"<span style='font-size:1.25rem;font-weight:600;color:#9ca3af'>:{elapsed_seconds:02d}</span>",
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

                if button_col.button("Start", key=f"start_{todo_id}"):
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


st.sidebar.title("🧭 Compass")
st.sidebar.caption("Make invisible time visible.")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📝 Daily Check-In",
        "✅ Todos & Timers",
        "⚡ Quick Log",
        "🧼 Maintenance",
        "📊 Analytics",
        "📤 Export",
    ],
)

st.title("🧭 Compass")
st.caption("Make invisible time visible.")


if page == "🏠 Dashboard":
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
        st.dataframe(recent_display, use_container_width=True)
    else:
        st.info("No check-ins yet. Add one in Daily Check-In.")

elif page == "📝 Daily Check-In":
    st.header("Daily Check-In")

    selected_date = st.date_input("Date", value=date.today())
    existing_checkin = get_checkin_for_date(selected_date)

    st.caption(
        "One editable daily summary per date. Save partial notes now and update the same day later."
    )

    with st.form("daily_checkin_form"):
        st.subheader("Sleep")

        slept_at = st.text_input(
            "Slept last night at (HH:MM, optional)",
            value=normalize_time_text(existing_checkin.get("slept_at", "")),
            placeholder="e.g. 02:30",
        )

        wake_up = st.text_input(
            "First woke up at (HH:MM, optional)",
            value=normalize_time_text(existing_checkin.get("wake_up_time", "")),
            placeholder="e.g. 09:30",
        )

        got_out_of_bed_at = st.text_input(
            "Got out of bed / day started at (HH:MM, optional)",
            value=normalize_time_text(existing_checkin.get("got_out_of_bed_at", "")),
            placeholder="e.g. 11:10",
        )   

        with st.expander("Optional pre-bed / sleep ritual notes"):
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
                    "Other",
                ],
                default=[],
            )
            sleep_note = st.text_area(
                "Sleep notes",
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

        submitted = st.form_submit_button("Save / Update Daily Check-In")

    if submitted:
        time_fields = {
            "Slept last night at": slept_at,
            "First woke up at": wake_up,
            "Got out of bed at": got_out_of_bed_at,
            "Medication taken at": medication_at,
            "Arrived at": arrived_at,
        }

        invalid_fields = [
            label for label, value in time_fields.items() if not is_valid_time_text(value)
        ]

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
                    "wake_up_time": normalize_time_text(wake_up),
                    "got_out_of_bed_at": normalize_time_text(got_out_of_bed_at),
                    "slept_at": normalize_time_text(slept_at),
                    "prebed_rituals": ", ".join(prebed_rituals),
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
        today_str = selected_date.isoformat()
        today_rows = current_checkins[current_checkins["date"] == today_str]

        if not today_rows.empty:
            st.subheader("Selected Day Summary")
            selected = today_rows.iloc[0]

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

            st.caption(f"Last updated: {format_short_datetime(selected.get('updated_at', selected.get('created_at', '')))}")

            ritual_summary = selected.get("morning_rituals", "")

            if selected.get("morning_ritual_custom", ""):
                ritual_summary = f"{ritual_summary}, {selected.get('morning_ritual_custom', '')}".strip(", ")

            if ritual_summary:
                st.caption(f"Morning ritual: {ritual_summary}")

            st.write("Current saved record for this day:")  
            st.dataframe(
                build_checkin_display_table(today_rows),
                use_container_width=True,
            )

        st.subheader("Last 5 days of Check-Ins")

        previous = current_checkins[current_checkins["date"] != selected_date.isoformat()]
        recent_previous = previous.head(5)
        older_previous = previous.iloc[5:]

        if not recent_previous.empty:
            st.dataframe(
                build_checkin_display_table(recent_previous),
                use_container_width=True,
            )
        else:
            st.info("No previous check-ins yet.")

        if not older_previous.empty:
            with st.expander("Show older check-ins"):
                st.dataframe(
                    build_checkin_display_table(older_previous),
                    use_container_width=True,
                )

elif page == "✅ Todos & Timers":
    st.header("Todos & Timers")
    st.caption("Turn today's tasks into trackable time sessions.")

    st.subheader("Add Todo")

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
                        "date": get_today_str(),
                        "task": task.strip(),
                        "category": category,
                        "planned_minutes": int(planned_minutes),
                        "status": "open",
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                    },
                )
                st.success("Todo added ✓")

    st.divider()
    st.subheader("Today's Todos")
    render_today_todos()

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
        today_logs = logs_df[logs_df["date"] == get_today_str()].copy()
        if not today_logs.empty:
            display_logs = today_logs.tail(10).copy()

            # Add planned duration from the linked Todo while keeping IDs internal.
            todos_lookup = load_csv(TODOS_FILE)
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

            display_columns = ["Date", "task", "Activity", "Time", "Planned", "Actual", "note"]
            display_logs = display_logs[[c for c in display_columns if c in display_logs.columns]]
            display_logs = display_logs.rename(
                columns={"task": "Task", "note": "Note"}
            )

            st.dataframe(
                display_logs,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Planned": st.column_config.NumberColumn("Planned", format="%d min"),
                    "Actual": st.column_config.NumberColumn("Actual", format="%.1f min"),
                },
            )
        else:
            st.info("No activity sessions logged today yet.")
    else:
        st.info("No activity sessions logged yet.")

elif page == "⚡ Quick Log":
    st.header("Quick Log")
    st.caption("One-click timestamp logs for small recurring events.")

    st.subheader("Add Quick Log")

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

elif page == "🧼 Maintenance":
    st.header("Maintenance")
    st.write("Next: toothbrush, contact lenses, water filter, and haircut freshness trackers.")

elif page == "📊 Analytics":
    st.header("Analytics")
    st.write("Next: wake-up trend, activity time, and counter charts.")

elif page == "📤 Export":
    st.header("Export")
    st.write("Next: generate daily text reports.")