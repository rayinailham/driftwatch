"""Shell smoke tests for daily pipeline ordering and publish observability."""

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DailyRunTests(unittest.TestCase):
    def run_pipeline(self, validate_exit: int = 0, publish_exit: int = 0, report_exit: int = 0):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake_uv = bin_dir / "uv"
        fake_uv.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                set -euo pipefail
                printf '%s\n' "$*" >> "$FAKE_UV_LOG"
                command="$*"
                if [[ "$command" == *"src/scrape.py"* ]]; then
                  mkdir -p "$DRIFTWATCH_DATA_ROOT/driftlab/$DRIFTWATCH_DATE"
                  printf '{}\n' > "$DRIFTWATCH_DATA_ROOT/driftlab/$DRIFTWATCH_DATE/records.jsonl"
                  printf '{"exit_code":0}\n' > "$DRIFTWATCH_DATA_ROOT/driftlab/$DRIFTWATCH_DATE/run.json"
                elif [[ "$command" == *"src/validate.py"* ]]; then
                  exit "$FAKE_VALIDATE_EXIT"
                elif [[ "$command" == *"scripts/mark_run_failed.py"* ]]; then
                  printf '{"exit_code":1}\n' > "$DRIFTWATCH_DATA_ROOT/driftlab/$DRIFTWATCH_DATE/run.json"
                elif [[ "$command" == *"src/export.py"* ]]; then
                  printf '\\xEF\\xBB\\xBFheader\nrow\n' > "$DRIFTWATCH_DATA_ROOT/driftlab/$DRIFTWATCH_DATE/records.csv"
                elif [[ "$command" == *"src/report.py"* ]]; then
                  exit "$FAKE_REPORT_EXIT"
                elif [[ "$command" == *"src/publish.py"* ]]; then
                  exit "$FAKE_PUBLISH_EXIT"
                fi
                """
            ),
            encoding="utf-8",
        )
        fake_uv.chmod(0o755)
        env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "FAKE_UV_LOG": str(root / "uv.log"),
            "FAKE_VALIDATE_EXIT": str(validate_exit),
            "FAKE_PUBLISH_EXIT": str(publish_exit),
            "FAKE_REPORT_EXIT": str(report_exit),
            "DRIFTWATCH_DATE": "2026-08-14",
            "DRIFTWATCH_MISSING_DATE": "2026-08-13",
            "DRIFTWATCH_DATA_ROOT": str(root / "data"),
            "DRIFTWATCH_REPORTS_ROOT": str(root / "reports"),
            "DRIFTWATCH_WEB_ROOT": str(root / "web"),
            "DRIFTWATCH_TARGETS": "driftlab",
            "DRIFTWATCH_LOCK_FILE": str(root / "driftwatch.lock"),
        }
        result = subprocess.run(
            ["bash", "scripts/daily_run.sh"], cwd=ROOT, env=env, text=True, capture_output=True
        )
        log = (root / "uv.log").read_text(encoding="utf-8").splitlines()
        return temporary, root, result, log

    def test_pipeline_orders_export_after_validation_and_logs_publish_failure(self) -> None:
        temporary, root, result, log = self.run_pipeline(publish_exit=7)
        try:
            positions = {
                name: next(index for index, line in enumerate(log) if name in line)
                for name in (
                    "--check-missing",
                    "src/scrape.py",
                    "src/validate.py",
                    "src/export.py",
                    "src/diff.py",
                    "src/alarm.py --target driftlab --date 2026-08-14",
                    "src/report.py",
                    "src/publish.py",
                )
            }
            self.assertLess(positions["--check-missing"], positions["src/scrape.py"])
            self.assertLess(positions["src/scrape.py"], positions["src/validate.py"])
            self.assertLess(positions["src/validate.py"], positions["src/export.py"])
            self.assertLess(positions["src/export.py"], positions["src/diff.py"])
            alarm_command = "src/alarm.py --target driftlab --date 2026-08-14"
            self.assertLess(positions["src/diff.py"], positions[alarm_command])
            self.assertLess(positions[alarm_command], positions["src/report.py"])
            self.assertLess(positions["src/report.py"], positions["src/publish.py"])
            self.assertEqual(result.returncode, 0)
            self.assertIn("ERROR publish gagal exit=7", result.stderr)
            csv_path = root / "data" / "driftlab" / "2026-08-14" / "records.csv"
            self.assertTrue(csv_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(len(csv_path.read_text(encoding="utf-8-sig").splitlines()), 2)
        finally:
            temporary.cleanup()

    def test_report_failure_is_logged_and_fails_the_unit_without_losing_data(self) -> None:
        temporary, root, result, log = self.run_pipeline(report_exit=3)
        try:
            self.assertEqual(result.returncode, 1)
            self.assertIn("laporan harian gagal exit=3", result.stderr)
            self.assertTrue(any("src/publish.py" in line for line in log))
            self.assertTrue((root / "data" / "driftlab" / "2026-08-14" / "records.jsonl").exists())
        finally:
            temporary.cleanup()

    def test_validation_failure_skips_export_and_fails_pipeline(self) -> None:
        temporary, root, result, log = self.run_pipeline(validate_exit=1)
        try:
            self.assertEqual(result.returncode, 1)
            self.assertFalse(any("src/export.py" in line for line in log))
            self.assertFalse((root / "data" / "driftlab" / "2026-08-14" / "records.csv").exists())
            manifest = (root / "data" / "driftlab" / "2026-08-14" / "run.json").read_text(
                encoding="utf-8"
            )
            self.assertIn('"exit_code":1', manifest)
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
