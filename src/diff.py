"""Compare a target snapshot with its most recent successful baseline."""

from __future__ import annotations

import argparse
import json
from datetime import date as Date
from pathlib import Path
from typing import Any

MAX_DETAILS = 50
MAX_VALUE_LENGTH = 200


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_records(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        return records
    with path.open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                record = json.loads(line)
                records[record["record_id"]] = record
    return records


def successful_runs(target_dir: Path, before: str) -> list[tuple[str, dict[str, Any]]]:
    runs = []
    if not target_dir.is_dir():
        return runs
    for directory in target_dir.iterdir():
        if not directory.is_dir() or directory.name >= before:
            continue
        manifest = load_json(directory / "run.json")
        if manifest is not None and manifest.get("exit_code") == 0:
            runs.append((directory.name, manifest))
    return sorted(runs, reverse=True)


def _short(value: Any) -> Any:
    if isinstance(value, str):
        return value[:MAX_VALUE_LENGTH]
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value if len(rendered) <= MAX_VALUE_LENGTH else rendered[:MAX_VALUE_LENGTH]


def _summary(record: dict[str, Any]) -> str:
    fields = record.get("fields", {})
    for name in ("title", "name", "author_name", "url", "item_id", "quote_id", "upc"):
        if fields.get(name) not in (None, "", []):
            return str(fields[name])[:MAX_VALUE_LENGTH]
    return record["record_id"][:MAX_VALUE_LENGTH]


def compare_records(
    target: str,
    run_date: str,
    today: dict[str, dict[str, Any]],
    baseline_date: str | None,
    baseline: dict[str, dict[str, Any]],
    run_today: dict[str, Any] | None,
    run_baseline: dict[str, Any] | None,
    duration_history: list[float] | None = None,
) -> dict[str, Any]:
    today_ids = set(today)
    baseline_ids = set(baseline)
    added_ids = sorted(today_ids - baseline_ids)
    removed_ids = sorted(baseline_ids - today_ids)
    shared_ids = today_ids & baseline_ids
    changed_ids = sorted(
        record_id
        for record_id in shared_ids
        if today[record_id].get("content_hash") != baseline[record_id].get("content_hash")
    )
    unchanged = len(shared_ids) - len(changed_ids)

    added = [
        {"record_id": record_id, "url": today[record_id].get("url"), "summary": _summary(today[record_id])}
        for record_id in added_ids[:MAX_DETAILS]
    ]
    changed = []
    for record_id in changed_ids[:MAX_DETAILS]:
        current = today[record_id]
        previous = baseline[record_id]
        current_fields = current.get("fields", {})
        previous_fields = previous.get("fields", {})
        names = sorted(set(current_fields) | set(previous_fields))
        fields_changed = [
            {"field": name, "from": _short(previous_fields.get(name)), "to": _short(current_fields.get(name))}
            for name in names
            if previous_fields.get(name) != current_fields.get(name)
        ]
        changed.append({"record_id": record_id, "url": current.get("url"), "fields_changed": fields_changed})
    removed = [
        {
            "record_id": record_id,
            "url": baseline[record_id].get("url"),
            "summary": _summary(baseline[record_id]),
            "last_seen": baseline_date,
        }
        for record_id in removed_ids[:MAX_DETAILS]
    ]

    today_completeness = (run_today or {}).get("field_completeness", {})
    baseline_completeness = (run_baseline or {}).get("field_completeness", {})
    completeness_delta = {
        name: round(today_completeness.get(name, 0.0) - value, 6)
        for name, value in baseline_completeness.items()
    }
    status_counts = (run_today or {}).get("http_status_counts", {})
    requests = sum(int(count) for count in status_counts.values())
    errors = sum(int(count) for status, count in status_counts.items() if not str(status).startswith("2"))
    result = {
        "target": target,
        "date": run_date,
        "baseline_date": baseline_date,
        "counts": {
            "added": len(added_ids),
            "changed": len(changed_ids),
            "removed": len(removed_ids),
            "unchanged": unchanged,
            "baseline_total": len(baseline),
        },
        "added": added,
        "changed": changed,
        "removed": removed,
        "health": {
            "records_unique": (run_today or {}).get("records_unique", 0),
            "baseline_unique": (run_baseline or {}).get("records_unique") if run_baseline else None,
            "duration_sec": (run_today or {}).get("duration_sec"),
            "error_rate": errors / requests if requests else 0.0,
            "field_completeness_delta": completeness_delta,
            "duration_history": duration_history or [],
            "run_missing": run_today is None,
        },
        "alarms": [],
    }
    if any(len(ids) > MAX_DETAILS for ids in (added_ids, changed_ids, removed_ids)):
        result["truncated"] = True
    return result


def build_diff(target: str, run_date: str, data_root: Path, reports_root: Path) -> Path:
    target_dir = data_root / target
    run_dir = target_dir / run_date
    run_today = load_json(run_dir / "run.json")
    previous = successful_runs(target_dir, run_date)
    baseline_date, run_baseline = previous[0] if previous else (None, None)
    today_records = load_records(run_dir / "records.jsonl")
    baseline_records = (
        load_records(target_dir / baseline_date / "records.jsonl") if baseline_date is not None else {}
    )
    durations = [float(run.get("duration_sec", 0)) for _, run in previous[:7]]
    result = compare_records(
        target,
        run_date,
        today_records,
        baseline_date,
        baseline_records,
        run_today,
        run_baseline,
        durations,
    )
    output = reports_root / target / run_date / "diff.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument("--today", action="store_true")
    date_group.add_argument("--date")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--reports-root", type=Path, default=Path("reports"))
    args = parser.parse_args()
    run_date = Date.today().isoformat() if args.today else args.date
    output = build_diff(args.target, run_date, args.data_root, args.reports_root)
    result = json.loads(output.read_text(encoding="utf-8"))
    counts = result["counts"]
    print(
        f"{args.target} {run_date}: added={counts['added']} changed={counts['changed']} "
        f"removed={counts['removed']} baseline={result['baseline_date']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
