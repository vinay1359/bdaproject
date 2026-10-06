"""Small hand-calculated checks for the MapReduce calculation rules."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


JOBS = Path(__file__).resolve().parents[1] / "src/jobs"


def run_script(name, lines):
    result = subprocess.run(
        [sys.executable, str(JOBS / name)], input="\n".join(lines) + "\n",
        text=True, capture_output=True, check=True,
    )
    return [json.loads(line.split("\t", 1)[1]) for line in result.stdout.splitlines()]


class CompareReducerTests(unittest.TestCase):
    def records(self, missing_baseline=None, closed_holiday=False):
        rows = []
        for i in range(30):
            if i != missing_baseline:
                rows.append(f'2024-12-25-c|000001\t{json.dumps(["baseline", f"B{i:02d}", 8000, 1, 0])}')
        for i in range(7):
            closed = closed_holiday and i == 0
            rows.append(f'2024-12-25-c|000001\t{json.dumps(["holiday", f"H{i:02d}", 0 if closed else 10000, 0 if closed else 1, 0])}')
        return rows

    def test_daily_means_and_percentage(self):
        row = run_script("compare_reducer.py", self.records())[0]
        self.assertTrue(row["complete"])
        self.assertEqual(row["baseline_daily_mean"], 8000)
        self.assertEqual(row["holiday_daily_mean"], 10000)
        self.assertEqual(row["percent_change"], 25)

    def test_missing_day_excludes_store(self):
        row = run_script("compare_reducer.py", self.records(missing_baseline=4))[0]
        self.assertFalse(row["complete"])
        self.assertEqual(row["baseline_days"], 29)
        self.assertIsNone(row["percent_change"])

    def test_recorded_closed_day_counts_as_zero(self):
        row = run_script("compare_reducer.py", self.records(closed_holiday=True))[0]
        self.assertTrue(row["complete"])
        self.assertEqual(row["holiday_days"], 7)
        self.assertEqual(row["holiday_closed_days"], 1)
        self.assertEqual(row["holiday_sales"], 60000)

    def test_replayed_duplicate_not_counted_twice(self):
        rows = self.records()
        rows.insert(0, rows[0])
        row = run_script("compare_reducer.py", rows)[0]
        self.assertEqual(row["baseline_days"], 30)
        self.assertEqual(row["baseline_sales"], 240000)

    def test_zero_baseline_has_no_percentage(self):
        rows = [line.replace(", 8000,", ", 0,") for line in self.records()]
        row = run_script("compare_reducer.py", rows)[0]
        self.assertTrue(row["complete"])
        self.assertEqual(row["delta_daily"], 10000)
        self.assertIsNone(row["percent_change"])


if __name__ == "__main__":
    unittest.main()
