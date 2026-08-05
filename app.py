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


def append_row(path: Path, row: dict) -> None:
    df = pd.DataFrame([row])
    header = not path.exists() or path.stat().st_size == 0
    df.to_csv(path, mode="a", index=False, header=header)


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
    st.write("Next: add todos that become timer buttons.")

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