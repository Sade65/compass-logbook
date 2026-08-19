import unittest
from datetime import date, datetime, time

from compass_core.activity_records import build_retroactive_records, corrected_end_time


class ActivityRecordTests(unittest.TestCase):
    def test_retroactive_records_keep_historical_occurrence_and_link(self):
        todo, activity = build_retroactive_records(
            activity_date=date(2026, 8, 18),
            task="Called repair service",
            category="Communication",
            planned_minutes=15,
            start_clock=time(14, 20),
            end_clock=time(14, 55),
            note="follow-up",
            now=datetime(2026, 8, 19, 9, 0),
        )
        self.assertEqual(todo["date"], "2026-08-18")
        self.assertEqual(todo["status"], "done")
        self.assertEqual(activity["todo_id"], todo["id"])
        self.assertEqual(activity["duration_minutes"], 35.0)
        self.assertEqual(activity["start_time"], "2026-08-18T14:20:00")
        self.assertEqual(activity["end_time"], "2026-08-18T14:55:00")

    def test_retroactive_same_day_end_must_follow_start(self):
        with self.assertRaises(ValueError):
            build_retroactive_records(
                activity_date=date(2026, 8, 18),
                task="Bad range",
                category="Admin",
                planned_minutes=0,
                start_clock=time(15, 0),
                end_clock=time(14, 0),
            )

    def test_corrected_duration_recalculates_end_time(self):
        self.assertEqual(
            corrected_end_time("2026-08-19T13:32:00", 60.5),
            "2026-08-19T14:32:30",
        )


if __name__ == "__main__":
    unittest.main()
