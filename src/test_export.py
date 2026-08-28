import csv
import json
import tempfile
import unittest
from pathlib import Path

from export import export_csv


class ExportTest(unittest.TestCase):
    def test_csv_has_bom_contract_order_flat_lists_and_technical_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary)
            record = {
                "record_id": "quotes:quote_id:abc",
                "target": "quotes",
                "url": "https://example.test/café",
                "run_id": "run-1",
                "fetched_at": "2026-08-27T09:00:00+07:00",
                "content_hash": "sha256:abc",
                "fields": {
                    "quote_id": "abc",
                    "author_name": "André",
                    "author_slug": "andre",
                    "author_goodreads_link": "https://example.test/andre",
                    "quote_word_count": 3,
                    "tags": ["life", "café"],
                },
                "missing_fields": [],
                "missing_reason": {},
            }
            (snapshot / "records.jsonl").write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )

            output, count = export_csv(snapshot, "quotes")

            self.assertEqual(count, 1)
            self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
            with output.open(encoding="utf-8-sig", newline="") as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(rows[0]["author_name"], "André")
            self.assertEqual(rows[0]["tags"], "life; café")
            self.assertEqual(list(rows[0])[-2:], ["content_hash", "run_id"])

    def test_csv_row_count_is_jsonl_count_plus_header(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary)
            records = []
            for item_id in ("DW-001", "DW-002"):
                records.append(
                    {
                        "record_id": f"driftlab:item_id:{item_id}",
                        "target": "driftlab",
                        "url": f"http://127.0.0.1/item/{item_id}",
                        "run_id": "run-1",
                        "fetched_at": "2026-08-14T09:00:00+07:00",
                        "content_hash": f"sha256:{item_id}",
                        "fields": {
                            "item_id": item_id,
                            "name": "Item",
                            "price": 1.0,
                            "category": "fixture",
                            "note": None,
                        },
                        "missing_fields": ["note"],
                        "missing_reason": {"note": "tidak ada"},
                    }
                )
            (snapshot / "records.jsonl").write_text(
                "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
            )

            output, count = export_csv(snapshot, "driftlab")

            self.assertEqual(count, 2)
            self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(len(output.read_text(encoding="utf-8-sig").splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
