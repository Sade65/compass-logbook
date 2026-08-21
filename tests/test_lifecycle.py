import unittest
from datetime import date, datetime

from compass_core.lifecycle import (
    add_calendar_interval,
    consumable_snapshot,
    effective_use_by,
    subscription_snapshot,
)


class LifecycleTests(unittest.TestCase):
    def test_monthly_subscription_is_calendar_aware(self):
        self.assertEqual(
            add_calendar_interval(date(2026, 1, 31), 1, "Months"),
            date(2026, 2, 28),
        )

    def test_subscription_snapshot_reports_next_charge(self):
        snap = subscription_snapshot(
            {"cycle_start": "2026-08-18", "cycle_value": 1, "cycle_unit": "Months"},
            today=date(2026, 8, 21),
        )
        self.assertEqual(snap["next_charge"], date(2026, 9, 18))
        self.assertEqual(snap["days_remaining"], 28)
        self.assertGreater(snap["progress"], 0)

    def test_consumable_uses_earliest_safety_limit(self):
        opened = datetime(2026, 8, 21, 12, 0)
        self.assertEqual(
            effective_use_by(
                opened_at=opened,
                printed_expiry_date=date(2026, 8, 28),
                use_within_days=3,
            ),
            date(2026, 8, 24),
        )

    def test_consumable_without_expiry_can_use_expected_lifespan(self):
        snap = consumable_snapshot(
            {
                "opened_at": "2026-08-21T12:00:00",
                "printed_expiry_date": "",
                "use_within_days": 0,
                "expected_lifespan_days": 14,
            },
            now=datetime(2026, 8, 23, 12, 0),
        )
        self.assertEqual(snap["expected_finish"], date(2026, 9, 4))
        self.assertEqual(snap["days_remaining"], 12)


if __name__ == "__main__":
    unittest.main()
