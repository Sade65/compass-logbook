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
    st.info("Dashboard coming next. First milestone: daily check-ins.")

elif page == "📝 Daily Check-In":
    st.header("Daily Check-In")
    st.write("Here you will log wake-up time, medication, arrival time, mood, energy and notes.")

elif page == "✅ Todos & Timers":
    st.header("Todos & Timers")
    st.write("This page will turn todos into start/stop timers.")

elif page == "⚡ Quick Log":
    st.header("Quick Log")
    st.write("This page will log cigarettes, medication, coffee, and supplements with timestamps.")

elif page == "🧼 Maintenance":
    st.header("Maintenance")
    st.write("This page will track toothbrush head, contact lenses, water filter, and haircut freshness.")

elif page == "📊 Analytics":
    st.header("Analytics")
    st.write("This page will show wake-up trends, activity charts, and habit counts.")

elif page == "📤 Export":
    st.header("Export")
    st.write("This page will generate daily text reports.")