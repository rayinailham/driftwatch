"""Focused unit tests for diff and all ten alarm detectors."""

import unittest

import alarm
from diff import compare_records


def manifest(records=200, exit_code=0, duration=10.0):
    return {
        "target": "driftlab",
        "records_unique": records,
        "exit_code": exit_code,
        "duration_sec": duration,
        "field_completeness": {"name": 1.0},
        "http_status_counts": {"200": records},
        "schema_unknown_fields": [],
        "rate_limit": {"delay_sec": 1.0, "observed_min_gap_ms": 1000},
    }


def diff_data(**counts):
    return {
        "baseline_date": "2026-08-01",
        "counts": {"added": 0, "changed": 0, "removed": 0, "baseline_total": 200, **counts},
        "health": {"error_rate": 0.0, "duration_history": [10.0] * 7},
    }


class DiffTests(unittest.TestCase):
    def test_identical_snapshots_have_zero_changes(self):
        record = {"record_id": "driftlab:item_id:1", "url": "http://local/1", "content_hash": "x",
                  "fields": {"item_id": "1", "name": "A"}}
        result = compare_records("driftlab", "2026-08-02", {record["record_id"]: record},
                                 "2026-08-01", {record["record_id"]: record}, manifest(1), manifest(1))
        self.assertEqual(result["counts"]["added"], 0)
        self.assertEqual(result["counts"]["changed"], 0)
        self.assertEqual(result["counts"]["removed"], 0)


class AlarmTests(unittest.TestCase):
    def test_all_ten_detectors_trigger_at_locked_thresholds(self):
        baseline = manifest()
        cases = [
            (alarm.zero_records, manifest(0), baseline, diff_data(), "ZERO_RECORDS"),
            (alarm.record_count_drop, manifest(159), baseline, diff_data(), "RECORD_COUNT_DROP"),
            (alarm.field_completeness_drop, {**manifest(), "field_completeness": {"name": 0.979}}, baseline,
             diff_data(), "FIELD_COMPLETENESS_DROP"),
            (alarm.schema_unknown_field, {**manifest(), "schema_unknown_fields": ["promo"]}, baseline,
             diff_data(), "SCHEMA_UNKNOWN_FIELD"),
            (alarm.http_error_spike, manifest(), baseline,
             {**diff_data(), "health": {"error_rate": 0.10}}, "HTTP_ERROR_SPIKE"),
            (alarm.run_missing, None, baseline, diff_data(), "RUN_MISSING"),
            (alarm.run_failed, manifest(exit_code=1), baseline, diff_data(), "RUN_FAILED"),
            (alarm.duration_anomaly, manifest(duration=61), baseline,
             {**diff_data(), "health": {"error_rate": 0, "duration_history": [20] * 7}}, "DURATION_ANOMALY"),
            (alarm.rate_limit_violation,
             {**manifest(), "rate_limit": {"delay_sec": 1.0, "observed_min_gap_ms": 899}}, baseline,
             diff_data(), "RATE_LIMIT_VIOLATION"),
            (alarm.churn_spike, manifest(), baseline, diff_data(changed=61), "CHURN_SPIKE"),
        ]
        for detector, today, previous, difference, code in cases:
            with self.subTest(code=code):
                self.assertEqual(detector(today, previous, difference).code, code)

    def test_comparison_alarms_are_silent_without_baseline(self):
        observed = {item.code for item in alarm.evaluate(manifest(1), None, diff_data(changed=200))}
        self.assertFalse(observed & {"RECORD_COUNT_DROP", "FIELD_COMPLETENESS_DROP", "DURATION_ANOMALY", "CHURN_SPIKE"})

    def test_optional_field_below_threshold_does_not_alarm(self):
        today = {**manifest(), "field_completeness": {"note": 0.0}}
        previous = {**manifest(), "field_completeness": {"note": 1.0}}
        self.assertIsNone(alarm.field_completeness_drop(today, previous, diff_data()))

    def test_message_validator_rejects_jargon(self):
        with self.assertRaisesRegex(ValueError, "jargon"):
            alarm._alarm("RUN_FAILED", "critical", 1, 0, None, "SQLite gagal", "x", "Buka log.")


if __name__ == "__main__":
    unittest.main()
