"""Export snapshot JSONL to Excel-friendly CSV and generate its data dictionary."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from contracts import CONTRACTS


TECHNICAL_COLUMNS = [
    "missing_fields",
    "missing_reason",
    "record_id",
    "target",
    "source_url",
    "fetched_at",
    "content_hash",
    "run_id",
]


def display(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if value is None:
        return ""
    return str(value)


def read_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def export_csv(snapshot: Path, target: str) -> tuple[Path, int]:
    records_path = snapshot / "records.jsonl"
    records = read_records(records_path)
    field_names = [field.name for field in CONTRACTS[target]["fields"]]
    columns = field_names + TECHNICAL_COLUMNS
    output = snapshot / "records.csv"

    with output.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=columns)
        writer.writeheader()
        for record in records:
            fields = record["fields"]
            row = {name: display(fields.get(name)) for name in field_names}
            row.update(
                {
                    "missing_fields": display(record["missing_fields"]),
                    "missing_reason": display(record["missing_reason"]),
                    "record_id": record["record_id"],
                    "target": record["target"],
                    "source_url": record["url"],
                    "fetched_at": record["fetched_at"],
                    "content_hash": record["content_hash"],
                    "run_id": record["run_id"],
                }
            )
            writer.writerow(row)
    return output, len(records)


def markdown(value: Any) -> str:
    return display(value).replace("|", "\\|").replace("\n", " ")


def first_examples(records: Iterable[dict[str, Any]], names: list[str]) -> dict[str, Any]:
    examples: dict[str, Any] = {}
    for record in records:
        for name in names:
            value = record["fields"].get(name)
            if name not in examples and value not in (None, "", []):
                examples[name] = value
    return examples


def generate_dictionary(data_root: Path, date: str, output: Path) -> None:
    lines = [
        "# DriftWatch — Kamus Data",
        "",
        "Digenerate oleh `src/export.py` dari `src/contracts.py`; contoh berasal dari snapshot "
        f"nyata `{date}`.",
    ]
    for target, contract in CONTRACTS.items():
        records = read_records(data_root / target / date / "records.jsonl")
        fields = contract["fields"]
        examples = first_examples(records, [field.name for field in fields])
        lines.extend(
            [
                "",
                f"## `{target}`",
                "",
                "| Kolom | Tipe | Status | Contoh nyata | Penjelasan | Sumber |",
                "|---|---|---|---|---|---|",
            ]
        )
        for field in fields:
            lines.append(
                f"| `{field.name}` | `{field.type.__name__}` | "
                f"{'wajib' if field.required else 'opsional'} | {markdown(examples.get(field.name))} | "
                f"{markdown(field.description)} | {markdown(field.source_hint)} |"
            )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Tanggal snapshot: YYYY-MM-DD")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--dictionary", type=Path, default=Path("docs/DATA_DICTIONARY.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for target in CONTRACTS:
        output, count = export_csv(args.data_root / target / args.date, target)
        print(f"{target}: {output} ({count} record)")
    generate_dictionary(args.data_root, args.date, args.dictionary)
    print(f"dictionary: {args.dictionary}")


if __name__ == "__main__":
    main()
