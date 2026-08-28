"""Regression tests for publish alarm contract and no-LLM mode."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import publish


class PublishTests(unittest.TestCase):
    def payload(self) -> dict:
        return {
            "generated_at": "2026-08-14T09:00:00+07:00",
            "source": {"name": "example.test"},
            "counts": {"total": 1, "added_today": 0, "changed_today": 0, "removed_today": 0},
            "rows": [],
        }

    def test_aggregate_prompt_accepts_empty_alarm_codes(self) -> None:
        prompt = publish.aggregate_prompt("books", self.payload(), {"alarms": []})
        self.assertIn("Peringatan aktif: tidak ada", prompt)

    def test_aggregate_prompt_accepts_active_alarm_code(self) -> None:
        prompt = publish.aggregate_prompt("books", self.payload(), {"alarms": ["RUN_FAILED"]})
        self.assertIn("RUN_FAILED", prompt)

    def test_no_llm_build_makes_zero_api_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "data" / "books" / "2026-08-14"
            snapshot.mkdir(parents=True)
            record = {
                "record_id": "books:upc:one",
                "url": "https://example.test/one",
                "fields": {},
            }
            (snapshot / "records.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
            with patch("publish.generate_insight") as api_call:
                payload = publish.build_payload(
                    "books", root / "data", root / "reports", root / "web", use_llm=False
                )

            api_call.assert_not_called()
            assert payload is not None
            self.assertEqual(payload["insight"]["input_tokens"], 0)
            self.assertEqual(payload["insight"]["output_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
