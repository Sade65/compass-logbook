import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from compass_core.runtime_state import (
    get_active_timer,
    get_pending_sessions,
    remove_pending_session,
    start_timer,
    stop_timer,
)


class RuntimeStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_file = Path(self.temp_dir.name) / "runtime_state.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_active_timer_survives_reload_from_disk(self) -> None:
        started = datetime(2026, 8, 17, 18, 30, 0)

        start_timer(
            todo_id="todo_1",
            task="Update Compass roadmap",
            todo_category="Admin",
            activity_type="Development / Coding",
            now=started,
            state_file=self.state_file,
        )

        recovered = get_active_timer(self.state_file)

        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["todo_id"], "todo_1")
        self.assertEqual(recovered["activity_type"], "Development / Coding")
        self.assertEqual(recovered["start_time"], "2026-08-17T18:30:00")

    def test_stop_captures_end_time_and_persists_pending_session(self) -> None:
        start_timer(
            todo_id="todo_1",
            task="Update Compass roadmap",
            todo_category="Admin",
            activity_type="Admin",
            now=datetime(2026, 8, 17, 18, 30, 0),
            state_file=self.state_file,
        )

        stopped = stop_timer(
            now=datetime(2026, 8, 17, 18, 45, 0),
            state_file=self.state_file,
        )

        self.assertIsNotNone(stopped)
        self.assertEqual(stopped["end_time"], "2026-08-17T18:45:00")
        self.assertIsNone(get_active_timer(self.state_file))

        pending = get_pending_sessions(self.state_file)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["session_id"], stopped["session_id"])

        remove_pending_session(stopped["session_id"], state_file=self.state_file)
        self.assertEqual(get_pending_sessions(self.state_file), [])

    def test_only_one_active_timer_is_allowed(self) -> None:
        start_timer(
            todo_id="todo_1",
            task="First",
            todo_category="Admin",
            activity_type="Admin",
            state_file=self.state_file,
        )

        with self.assertRaisesRegex(ValueError, "already running"):
            start_timer(
                todo_id="todo_2",
                task="Second",
                todo_category="Admin",
                activity_type="Admin",
                state_file=self.state_file,
            )


if __name__ == "__main__":
    unittest.main()
