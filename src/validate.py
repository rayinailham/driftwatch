"""Validation and identity helpers for DriftWatch records."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from contracts import CONTRACTS, VOLATILE


class RecordValidationError(ValueError):
    """A record violates its locked target contract."""


class SchemaUnknownField(RecordValidationError):
    code = "SCHEMA_UNKNOWN_FIELD"


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def _fields(rec: dict[str, Any]) -> dict[str, Any]:
    return rec["fields"] if "fields" in rec else {
        key: value for key, value in rec.items() if key not in {"missing_fields", "missing_reason"}
    }


def _matches_type(value: Any, expected: type | tuple[type, ...]) -> bool:
    types = expected if isinstance(expected, tuple) else (expected,)
    if isinstance(value, bool) and bool not in types:
        return False
    return isinstance(value, types)


def validate_record(rec: dict[str, Any], target: str) -> dict[str, Any]:
    """Validate one canonical record or a bare field mapping; return it unchanged."""
    if target not in CONTRACTS:
        raise RecordValidationError(f"target tidak dikenal: {target}")
    fields = _fields(rec)
    definitions = {field.name: field for field in CONTRACTS[target]["fields"]}
    unknown = sorted(set(fields) - set(definitions))
    if unknown:
        raise SchemaUnknownField(f"SCHEMA_UNKNOWN_FIELD: {', '.join(unknown)}")

    missing_fields = rec.get("missing_fields", [])
    missing_reason = rec.get("missing_reason", {})
    if not isinstance(missing_fields, list):
        raise RecordValidationError("missing_fields harus list")
    if not isinstance(missing_reason, dict):
        raise RecordValidationError("missing_reason harus object")
    if set(missing_reason) - set(missing_fields):
        raise RecordValidationError("missing_reason memuat field yang tidak dinyatakan hilang")

    for name, definition in definitions.items():
        empty = name not in fields or _is_empty(fields.get(name))
        if empty:
            if definition.required:
                raise RecordValidationError(f"field required kosong: {name}")
            if name not in missing_fields or not missing_reason.get(name):
                raise RecordValidationError(f"missing_reason wajib untuk field kosong: {name}")
        elif not _matches_type(fields[name], definition.type):
            raise RecordValidationError(
                f"tipe salah untuk {name}: {type(fields[name]).__name__}"
            )

    undeclared_missing = sorted(set(missing_fields) - set(definitions))
    if undeclared_missing:
        raise SchemaUnknownField(f"SCHEMA_UNKNOWN_FIELD: {', '.join(undeclared_missing)}")
    return rec


def content_hash(fields: dict[str, Any]) -> str:
    stable = {key: value for key, value in fields.items() if key not in VOLATILE}
    canonical = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"


def make_record_id(target: str, key_value: Any) -> str:
    if target not in CONTRACTS:
        raise RecordValidationError(f"target tidak dikenal: {target}")
    return f"{target}:{CONTRACTS[target]['key']}:{key_value}"


def field_completeness(records: list[dict[str, Any]], target: str) -> dict[str, float]:
    if target not in CONTRACTS:
        raise RecordValidationError(f"target tidak dikenal: {target}")
    names = [field.name for field in CONTRACTS[target]["fields"]]
    if not records:
        return {name: 0.0 for name in names}
    return {
        name: sum(not _is_empty(_fields(record).get(name)) for record in records) / len(records)
        for name in names
    }


def validate_run(path: str | Path) -> int:
    count = 0
    with Path(path).open(encoding="utf-8") as records_file:
        for line_number, line in enumerate(records_file, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                validate_record(record, record.get("target", ""))
            except (json.JSONDecodeError, RecordValidationError) as error:
                raise RecordValidationError(f"baris {line_number}: {error}") from error
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Validasi records.jsonl DriftWatch")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        count = validate_run(args.path)
    except (OSError, RecordValidationError) as error:
        print(f"INVALID: {error}")
        return 1
    print(f"VALID: {count} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
