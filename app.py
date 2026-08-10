from os import path
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, time

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


# timer session state initialization
if "active_timer" not in st.session_state:
    st.session_state.active_timer = None



if page == "🏠 Dashboard":
    st.header("Dashboard")

    if CHECKINS_FILE.exists() and CHECKINS_FILE.stat().st_size > 0:
        df = pd.read_csv(CHECKINS_FILE)
        latest = df.iloc[-1]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Wake-up", latest["wake_up_time"])
        col2.metric("Medication", latest["medication_at"])
        col3.metric("Arrival", latest["arrived_at"])
        col4.metric("Energy", f'{latest["energy"]}/5')

        st.subheader("Recent Check-Ins")
        st.dataframe(df.tail(7), use_container_width=True)
    else:
        st.info("No check-ins yet. Add one in Daily Check-In.")

elif page == "📝 Daily Check-In":
    st.header("Daily Check-In")

    with st.form("daily_checkin_form"):
        checkin_date = st.date_input("Date", value=date.today())
        wake_up = st.time_input("Woke up at", value=time(8, 30))
        slept_at = st.time_input("Slept last night at", value=time(0, 30))
        medication_at = st.time_input("Medication taken at", value=time(9, 15))
        arrived_at = st.time_input("Arrived at library/workplace", value=time(10, 0))
        mood = st.slider("Mood", 1, 5, 3)
        energy = st.slider("Energy", 1, 5, 3)
        main_focus = st.text_input("Main focus today")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save Daily Check-In")

    if submitted:
        append_row(
            
            CHECKINS_FILE,
            {
                "date": checkin_date.isoformat(),
                "wake_up_time": wake_up.strftime("%H:%M"),
                "slept_at": slept_at.strftime("%H:%M"),
                "medication_at": medication_at.strftime("%H:%M"),
                "arrived_at": arrived_at.strftime("%H:%M"),
                "mood": mood,
                "energy": energy,
                "main_focus": main_focus,
                "notes": notes,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
        st.success("Daily check-in saved.")

    if CHECKINS_FILE.exists() and CHECKINS_FILE.stat().st_size > 0:
        st.subheader("Recent Check-Ins")
        df = pd.read_csv(CHECKINS_FILE)
        st.dataframe(df.tail(10), use_container_width=True)

elif page == "✅ Todos & Timers":
    st.header("Todos & Timers")
    st.caption("Turn today's tasks into trackable time sessions.")

    st.subheader("Add Todo")

    with st.form("add_todo_form"):
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
                st.success("Todo added.")

    st.divider()

    st.subheader("Today's Todos")

    todos_df = load_csv(TODOS_FILE)
    today_todos = pd.DataFrame()

    if not todos_df.empty:
        today_todos = todos_df[todos_df["date"] == get_today_str()].copy()

    if today_todos.empty:
        st.info("No todos for today yet. Add one above.")
    else:
        for _, todo in today_todos.iterrows():
            todo_id = todo["id"]
            task_name = todo["task"]
            category_name = todo["category"]
            planned = int(todo["planned_minutes"])
            status = todo["status"]

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([4, 2, 2, 2])

                col1.markdown(f"**{task_name}**")
                col1.caption(f"{category_name} · planned {planned} min")
                col2.write(f"Status: `{status}`")

                active_timer = st.session_state.active_timer
                is_active = active_timer is not None and active_timer["todo_id"] == todo_id

                if is_active:
                    start_time = datetime.fromisoformat(active_timer["start_time"])
                    elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
                    col3.metric("Running", f"{elapsed_minutes:.1f} min")

                    if col4.button("Stop", key=f"stop_{todo_id}", type="primary"):
                        st.session_state.stop_todo_id = todo_id
                        st.session_state.stop_task_name = task_name
                        st.session_state.stop_category = category_name
                        st.session_state.stop_start_time = active_timer["start_time"]
                        st.session_state.active_timer = None
                        st.rerun()
                else:
                    if col4.button("Start", key=f"start_{todo_id}"):
                        if st.session_state.active_timer is not None:
                            st.warning("Another timer is already running. Stop it first.")
                        else:
                            st.session_state.active_timer = {
                                "todo_id": todo_id,
                                "task": task_name,
                                "category": category_name,
                                "start_time": datetime.now().isoformat(timespec="seconds"),
                            }
                            st.rerun()

    if "stop_todo_id" in st.session_state:
        st.divider()
        st.subheader("Save Completed Session")

        stop_start = datetime.fromisoformat(st.session_state.stop_start_time)
        stop_end = datetime.now()
        duration_minutes = round((stop_end - stop_start).total_seconds() / 60, 2)

        st.info(
            f"Session: {st.session_state.stop_task_name} — {duration_minutes} minutes"
        )

        with st.form("save_session_form"):
            note_type = st.selectbox(
                "Note type",
                ["General", "Observation", "Idea", "Todo", "Person", "Event"],
            )
            note = st.text_area("Notes", placeholder="What happened during this session?")
            completed = st.radio(
                "Did you finish the task?",
                ["Yes, mark done", "No, keep open"],
                horizontal=True,
            )

            save_session = st.form_submit_button("Save Session")

        if save_session:
            append_row(
                ACTIVITY_LOGS_FILE,
                {
                    "id": generate_id("session"),
                    "todo_id": st.session_state.stop_todo_id,
                    "date": get_today_str(),
                    "task": st.session_state.stop_task_name,
                    "category": st.session_state.stop_category,
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
                todos_df = load_csv(TODOS_FILE)
                if not todos_df.empty:
                    todos_df.loc[todos_df["id"] == st.session_state.stop_todo_id, "status"] = "done"
                    todos_df.to_csv(TODOS_FILE, index=False)

            del st.session_state.stop_todo_id
            del st.session_state.stop_task_name
            del st.session_state.stop_category
            del st.session_state.stop_start_time

            st.success("Session saved.")
            st.rerun()

    st.divider()
    st.subheader("Today's Activity Log")

    logs_df = load_csv(ACTIVITY_LOGS_FILE)
    if not logs_df.empty:
        today_logs = logs_df[logs_df["date"] == get_today_str()].copy()
        if not today_logs.empty:
            st.dataframe(today_logs.tail(10), use_container_width=True)
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