import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from contracts import CONTRACTS
from validate import (
    RecordValidationError,
    SchemaUnknownField,
    content_hash,
    field_completeness,
    make_record_id,
    validate_record,
    validate_run,
)


ROOT = Path(__file__).resolve().parents[1]


def canonical_sample(target, sample):
    sample = sample.copy()
    if target == "quotes":
        text = sample.pop("text")
        sample["quote_id"] = hashlib.sha256(text.encode()).hexdigest()[:16]
        sample["quote_word_count"] = len(text.split())
    missing = sample.get("missing_fields", [])
    if isinstance(sample.get("missing_reason"), str):
        sample["missing_reason"] = {name: sample["missing_reason"] for name in missing}
    return sample


class ContractTests(unittest.TestCase):
    def test_all_twelve_recon_samples_pass(self):
        count = 0
        for target in CONTRACTS:
            recon = json.loads((ROOT / "recon" / f"{target}.json").read_text())
            for sample in recon["sample"]:
                validate_record(canonical_sample(target, sample), target)
                count += 1
        self.assertEqual(count, 12)

    def test_hash_ignores_volatile_fields(self):
        first = {"item_id": "DW-1", "price": 10.0, "fetched_at": "yesterday"}
        second = {**first, "fetched_at": "today"}
        self.assertEqual(content_hash(first), content_hash(second))

    def test_hash_changes_with_field_value(self):
        self.assertNotEqual(content_hash({"price": 10.0}), content_hash({"price": 11.0}))

    def test_hash_includes_business_url(self):
        self.assertNotEqual(content_hash({"url": "https://a"}), content_hash({"url": "https://b"}))

    def test_unknown_field_rejected(self):
        with self.assertRaisesRegex(SchemaUnknownField, "SCHEMA_UNKNOWN_FIELD"):
            validate_record({"fields": {"item_id": "DW-1", "name": "Lamp", "price": 1.0, "category": "home", "rogue": 1}, "missing_fields": ["note"], "missing_reason": {"note": "tidak ada"}}, "driftlab")

    def test_wrong_type_rejected(self):
        with self.assertRaisesRegex(RecordValidationError, "tipe salah"):
            validate_record({"fields": {"item_id": "DW-1", "name": "Lamp", "price": "1.0", "category": "home"}, "missing_fields": ["note"], "missing_reason": {"note": "tidak ada"}}, "driftlab")

    def test_missing_reason_required(self):
        with self.assertRaisesRegex(RecordValidationError, "missing_reason wajib"):
            validate_record({"item_id": "DW-1", "name": "Lamp", "price": 1.0, "category": "home"}, "driftlab")

    def test_record_id_consistent(self):
        self.assertEqual(make_record_id("books", "abc"), "books:upc:abc")

    def test_field_completeness(self):
        records = [
            {"fields": {"item_id": "1", "name": "A", "price": 1.0, "category": "x", "note": "yes"}},
            {"fields": {"item_id": "2", "name": "B", "price": 2.0, "category": "x", "note": None}},
        ]
        self.assertEqual(field_completeness(records, "driftlab")["note"], 0.5)

    def test_validate_run(self):
        record = {"target": "driftlab", "fields": {"item_id": "1", "name": "A", "price": 1.0, "category": "x"}, "missing_fields": ["note"], "missing_reason": {"note": "tidak ada"}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text(json.dumps(record) + "\n")
            self.assertEqual(validate_run(path), 1)

    def test_descriptions_and_source_hints_present(self):
        fields = [field for contract in CONTRACTS.values() for field in contract["fields"]]
        self.assertTrue(all(field.description and field.source_hint for field in fields))


if __name__ == "__main__":
    unittest.main()
