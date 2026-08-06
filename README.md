# Compass Logbook

**Compass Logbook** is a local-first personal tracking dashboard built with Python and Streamlit.

It helps users track daily rhythm, todos, focused work sessions, quick life logs, and recurring maintenance tasks in one simple dashboard.

The project is the first working prototype of a broader idea: **Compass LifeOS** — a personal operating system for time awareness, executive function, routines, goals, and life maintenance.

---

## Why this project exists

Many productivity tools track only one slice of life:

- todo apps track tasks
- habit trackers track streaks
- time trackers track work sessions
- calendars track appointments
- notes apps store reflections

Compass Logbook explores a more integrated approach:

> Make invisible time visible.

The goal is to help users understand where their day goes, reduce cognitive overload, and keep small but important life responsibilities from disappearing.

---

## Current MVP Features

### Daily Check-In

Users can log:

- wake-up time
- sleep time
- medication time
- library/work arrival time
- mood
- energy
- main focus
- daily notes

The latest check-in appears on the dashboard.

### Todos & Timers

Users can:

- add todos for the day
- assign a category
- set planned minutes
- start and stop task timers
- save session notes
- mark tasks as done or keep them open

This turns a static todo list into trackable time sessions.

### Local CSV Persistence

The app saves data locally using CSV files.

Private personal logs are ignored by Git and stay on the user's machine.

### Sample Demo Data

The repository includes safe sample CSV files so the project can be demonstrated without exposing private personal data.

---

## Tech Stack

- Python
- Streamlit
- pandas
- CSV-based local storage
- Git / GitHub

Planned future upgrades may include:

- Plotly charts
- SQLite
- DuckDB / dbt analytics layer
- NLP smart tags
- AI weekly reflection
- OCR screenshot-to-action capture
- Electron desktop app
- mobile companion app

---

## Project Structure

```text
compass-logbook/
├── app.py
├── README.md
├── requirements.txt
├── data/
│   ├── sample_daily_checkins.csv
│   ├── sample_todos.csv
│   ├── sample_activity_logs.csv
│   ├── sample_counter_logs.csv
│   └── sample_maintenance_logs.csv
├── docs/
├── exports/
└── screenshots/
```

---

## How to Run Locally

Clone the repository:

```bash
git clone https://github.com/Sade65/compass-logbook.git
cd compass-logbook
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
python -m streamlit run app.py
```

The app will open locally at:

```text
http://localhost:8501
```

---

## Data Privacy

Real personal logs are stored locally in CSV files such as:

```text
data/daily_checkins.csv
data/todos.csv
data/activity_logs.csv
```

These files are ignored by Git and should not be committed.

Only fake sample files named `sample_*.csv` are included in the repository.

---

## Roadmap

### v0.1 — Current MVP

- Daily Check-In
- Todos & Timers
- CSV persistence
- Activity session logging
- GitHub repository setup

### v0.2 — Quick Logs and Maintenance

- Cigarette, coffee, medication, supplement logs
- Toothbrush head, contact lenses, water filter, haircut trackers
- Freshness progress bars
- Basic dashboard metrics

### v0.3 — Analytics

- Wake-up trend
- Arrival time trend
- Focus time by category
- Cigarettes per day
- Weekly summary
- Daily report export

### v0.4 — Behavior and Productivity Layer

- Communication sprint
- Pomodoro/timebox presets
- Habit targets
- Friction Coach prompts
- “What should I do?” productive dice

### v0.5 — Intelligence Layer

- NLP smart tags from notes
- AI weekly reflection
- Screenshot-to-action capture
- Calendar/event extraction

---

## Product Vision

Compass Logbook is not intended to be just another timer app.

The long-term vision is a local-first personal dashboard that combines:

- daily rhythm
- tasks
- timers
- habits
- reminders
- maintenance cycles
- notes
- analytics
- AI-assisted reflection

into one simple system for making life more visible and manageable.
