#!/usr/bin/env python3
"""Run all eleven DriftLab scenarios through the real scraper, diff, and alarm pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from drift_lab import SCENARIOS, apply_scenario, reset  # noqa: E402

EXPECTED = {
    "DO-01": set(),
    "DO-02": set(),
    "DO-03": set(),
    "DO-04": {
        "ZERO_RECORDS",
        "RECORD_COUNT_DROP",
        "FIELD_COMPLETENESS_DROP",
        "RUN_FAILED",
        "CHURN_SPIKE",
    },
    "DO-05": {"FIELD_COMPLETENESS_DROP"},
    "DO-06": {"HTTP_ERROR_SPIKE"},
    "DO-07": {"SCHEMA_UNKNOWN_FIELD"},
    "DO-08": {"DURATION_ANOMALY"},
    "DO-09": {"RUN_MISSING"},
    "DO-10": {"CHURN_SPIKE"},
    "DO-11": {"RATE_LIMIT_VIOLATION"},
}


def command(*args: str, allowed: set[int] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if result.returncode not in (allowed or {0}):
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n{result.stdout}{result.stderr}"
        )
    return result


def scrape(output: Path, extra: tuple[str, ...] = ()) -> None:
    command(
        "uv", "run", "--no-sync", "python", "src/scrape.py",
        "--target", "driftlab", "--out", str(output), *extra,
        allowed={0, 1},
    )


def main() -> int:
    passed = 0
    try:
        with tempfile.TemporaryDirectory(prefix="driftwatch-oracles-") as temporary:
            root = Path(temporary)
            data_root = root / "data"
            reports_root = root / "reports"
            for number, code in enumerate(SCENARIOS, 2):
                scenario_data = data_root / code
                scenario_reports = reports_root / code
                baseline_date = "2026-08-01"
                reset()
                scrape(scenario_data / "driftlab" / baseline_date)
                run_date = f"2026-08-{number:02d}"
                apply_scenario(code)
                if code != "DO-09":
                    extra = ("--delay", "0.1", "--policy-delay", "1.0") if code == "DO-11" else ()
                    scrape(scenario_data / "driftlab" / run_date, extra)
                command(
                    "uv", "run", "--no-sync", "python", "src/diff.py",
                    "--target", "driftlab", "--date", run_date,
                    "--data-root", str(scenario_data), "--reports-root", str(scenario_reports),
                )
                command(
                    "uv", "run", "--no-sync", "python", "src/alarm.py",
                    "--target", "driftlab", "--date", run_date,
                    "--data-root", str(scenario_data), "--reports-root", str(scenario_reports), "--no-notify",
                    allowed={0, 1},
                )
                result = json.loads(
                    (scenario_reports / "driftlab" / run_date / "diff.json").read_text(encoding="utf-8")
                )
                observed = set(result["alarms"])
                ok = observed == EXPECTED[code]
                counts = result["counts"]
                detail = (
                    f"added={counts['added']} changed={counts['changed']} removed={counts['removed']}"
                    if code in {"DO-01", "DO-02", "DO-03", "DO-10"}
                    else f"records={result['health']['records_unique']}"
                )
                print(f"{code}  {detail}  alarms={sorted(observed)}  {'PASS' if ok else 'FAIL'}")
                if not ok:
                    print(f"       expected={sorted(EXPECTED[code])}")
                passed += int(ok)
                reset()
            print(f"{passed}/11 PASS")
            return 0 if passed == 11 else 1
    finally:
        reset()


if __name__ == "__main__":
    raise SystemExit(main())
