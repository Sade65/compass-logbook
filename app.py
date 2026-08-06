from os import path
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, time

st.set_page_config(
    page_title="Compass Logbook",
    page_icon="🧭",
    layout="wide",
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

CHECKINS_FILE = DATA_DIR / "daily_checkins.csv"
TODOS_FILE = DATA_DIR / "todos.csv"
ACTIVITY_LOGS_FILE = DATA_DIR / "activity_logs.csv"


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



st.sidebar.title("🧭 Compass Logbook")
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

st.title("🧭 Compass Logbook")
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
        category = st.selectbox(
            "Category",
            [
                "Studying",
                "Job Applications",
                "Communication",
                "Admin",
                "Uni Research",
                "Break",
                "Exercise",
                "Personal",
                "Other",
            ],
        )
        planned_minutes = st.number_input(
            "Planned minutes",
            min_value=1,
            max_value=240,
            value=25,
            step=5,
        )

        add_todo = st.form_submit_button("Add Todo")

    if add_todo:
        if task.strip():
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
        else:
            st.warning("Please enter a task name.")

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
    st.write("Next: one-click logs for cigarettes, medication, coffee, and supplements.")

elif page == "🧼 Maintenance":
    st.header("Maintenance")
    st.write("Next: toothbrush, contact lenses, water filter, and haircut freshness trackers.")

elif page == "📊 Analytics":
    st.header("Analytics")
    st.write("Next: wake-up trend, activity time, and counter charts.")

elif page == "📤 Export":
    st.header("Export")
    st.write("Next: generate daily text reports.")