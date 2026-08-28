"""Evaluate DriftWatch's closed set of ten alarm codes."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
from dataclasses import asdict, dataclass
from datetime import date as Date, datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from contracts import CONTRACTS

JAKARTA = ZoneInfo("Asia/Jakarta")
ALARM_CODES = {
    "ZERO_RECORDS",
    "RECORD_COUNT_DROP",
    "FIELD_COMPLETENESS_DROP",
    "SCHEMA_UNKNOWN_FIELD",
    "HTTP_ERROR_SPIKE",
    "RUN_MISSING",
    "RUN_FAILED",
    "DURATION_ANOMALY",
    "RATE_LIMIT_VIOLATION",
    "CHURN_SPIKE",
}
FORBIDDEN_MESSAGE_WORDS = {
    "selectolax",
    "tenacity",
    "storage_state",
    "stacktrace",
    "traceback",
    "sqlite",
    "checkpoint",
    "exception",
    "xpath",
    "regex",
}


@dataclass(frozen=True)
class Alarm:
    code: str
    severity: str
    observed: Any
    expected: Any
    baseline: Any
    message: str
    likely_cause: str
    next_action: str


def _alarm(code: str, severity: str, observed: Any, expected: Any, baseline: Any, message: str,
           likely_cause: str, next_action: str) -> Alarm:
    alarm = Alarm(code, severity, observed, expected, baseline, message, likely_cause, next_action)
    validate_alarm(alarm)
    return alarm


def validate_alarm(alarm: Alarm) -> None:
    if alarm.code not in ALARM_CODES:
        raise ValueError(f"kode alarm tidak dikenal: {alarm.code}")
    lowered = alarm.message.casefold()
    found = sorted(word for word in FORBIDDEN_MESSAGE_WORDS if word in lowered)
    if found:
        raise ValueError(f"message memuat jargon terlarang: {', '.join(found)}")
    if not alarm.next_action.strip() or alarm.next_action.casefold() == "periksa lebih lanjut":
        raise ValueError("next_action harus konkret")


def zero_records(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    observed = (run_today or {}).get("records_unique", 0)
    if run_today is not None and observed == 0:
        return _alarm("ZERO_RECORDS", "critical", observed, 1, None,
                      "Tidak ada data yang berhasil dikumpulkan hari ini.",
                      "Tata letak sumber mungkin berubah sehingga daftar item tidak ditemukan.",
                      "Jalankan ulang recon target lalu bandingkan penanda daftar dengan versi terakhir.")
    return None


def record_count_drop(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_today is None or run_baseline is None:
        return None
    observed = run_today.get("records_unique", 0)
    baseline = run_baseline.get("records_unique", 0)
    expected = baseline * 0.8
    if observed < expected:
        return _alarm("RECORD_COUNT_DROP", "critical", observed, expected, baseline,
                      f"Hanya {observed} data terkumpul, kurang dari 80% jumlah normal {baseline}.",
                      "Sebagian halaman atau tautan daftar kemungkinan tidak lagi terbaca.",
                      "Jalankan `make recon` untuk target ini lalu cocokkan jumlah halaman dan tautannya.")
    return None


def field_completeness_drop(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_today is None or run_baseline is None:
        return None
    today = run_today.get("field_completeness", {})
    baseline = run_baseline.get("field_completeness", {})
    target = str(run_today.get("target", ""))
    required = {
        field.name for field in CONTRACTS.get(target, {}).get("fields", ()) if field.required
    }
    bad = {
        name: value for name, value in today.items()
        if (not required or name in required)
        and (value < 0.98 or baseline.get(name, value) - value > 0.10)
    }
    if bad:
        observed = min(bad.values())
        name = min(bad, key=lambda field: bad[field])
        return _alarm("FIELD_COMPLETENESS_DROP", "critical", observed, 0.98,
                      baseline.get(name),
                      f"Kolom {name} hanya terisi {observed:.1%} pada data hari ini.",
                      f"Elemen sumber untuk kolom {name} mungkin hilang atau berganti nama.",
                      f"Buka tiga halaman sampel dan cocokkan sumber kolom {name} dengan kontrak data.")
    return None


def schema_unknown_field(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    unknown = (run_today or {}).get("schema_unknown_fields", [])
    if unknown:
        return _alarm("SCHEMA_UNKNOWN_FIELD", "warning", unknown, [], None,
                      f"Ditemukan kolom baru yang belum disepakati: {', '.join(unknown)}.",
                      "Situs sumber menambahkan atribut baru pada data.",
                      "Bandingkan kolom baru dengan kontrak, lalu setujui atau abaikan secara eksplisit.")
    return None


def http_error_spike(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    rate = diff.get("health", {}).get("error_rate", 0.0)
    if run_today is not None and rate >= 0.10:
        return _alarm("HTTP_ERROR_SPIKE", "critical", rate, 0.10, None,
                      f"Sebanyak {rate:.1%} permintaan gagal setelah percobaan ulang.",
                      "Situs sumber mungkin sedang bermasalah atau membatasi akses.",
                      "Tunggu 15 menit, jalankan target sekali lagi, lalu hubungi pemilik situs bila tetap gagal.")
    return None


def run_missing(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_today is None:
        return _alarm("RUN_MISSING", "critical", False, True, diff.get("baseline_date"),
                      "Jadwal pengambilan data berlalu tanpa hasil hari ini.",
                      "Komputer, timer, atau proses harian mungkin tidak berjalan.",
                      "Jalankan `systemctl --user status driftwatch.service` lalu mulai run harian secara manual.")
    return None


def run_failed(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_today is not None and run_today.get("exit_code") != 0:
        return _alarm("RUN_FAILED", "critical", run_today.get("exit_code"), 0, None,
                      "Pengambilan data hari ini berhenti dengan kegagalan.",
                      "Log run memuat kegagalan yang mencegah proses selesai normal.",
                      "Buka `run.log`, perbaiki kegagalan pertama, lalu jalankan target dengan `--resume`.")
    return None


def duration_anomaly(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_today is None or run_baseline is None:
        return None
    duration = float(run_today.get("duration_sec", 0))
    history = [float(value) for value in diff.get("health", {}).get("duration_history", [])]
    median = statistics.median(history) if history else float(run_baseline.get("duration_sec", 0))
    if duration > 3 * median and duration > 60:
        return _alarm("DURATION_ANOMALY", "warning", duration, 3 * median, median,
                      f"Run hari ini memakan {duration:.1f} detik, lebih dari tiga kali durasi normal.",
                      "Respons situs sumber melambat atau beberapa permintaan menunggu terlalu lama.",
                      "Bandingkan waktu respons di `run.log` dan uji tiga URL sampel dari mesin yang sama.")
    return None


def rate_limit_violation(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_today is None:
        return None
    rate = run_today.get("rate_limit", {})
    observed = rate.get("observed_min_gap_ms")
    expected = float(rate.get("delay_sec", 0)) * 1000 * 0.9
    if observed is not None and observed < expected:
        return _alarm("RATE_LIMIT_VIOLATION", "warning", observed, expected, rate.get("delay_sec"),
                      f"Jeda terpendek antarpermintaan hanya {observed} ms, di bawah batas aman.",
                      "Pengaturan jeda run lebih kecil daripada kebijakan target.",
                      "Hentikan run dan jalankan ulang tanpa opsi `--delay` agar jeda standar dipakai.")
    return None


def churn_spike(run_today: dict | None, run_baseline: dict | None, diff: dict) -> Alarm | None:
    if run_baseline is None:
        return None
    counts = diff.get("counts", {})
    baseline = counts.get("baseline_total", 0)
    observed = counts.get("changed", 0) + counts.get("removed", 0)
    if observed > baseline * 0.30:
        return _alarm("CHURN_SPIKE", "warning", observed, baseline * 0.30, baseline,
                      f"Sebanyak {observed} data berubah atau hilang sekaligus hari ini.",
                      "Sumber mungkin melakukan pembaruan besar atau mengubah cara nilai ditampilkan.",
                      "Ambil sampel lima perubahan, konfirmasi di sumber, lalu tandai pembaruan massal bila sah.")
    return None


DETECTORS: tuple[Callable[[dict | None, dict | None, dict], Alarm | None], ...] = (
    zero_records,
    record_count_drop,
    field_completeness_drop,
    schema_unknown_field,
    http_error_spike,
    run_missing,
    run_failed,
    duration_anomaly,
    rate_limit_violation,
    churn_spike,
)


def evaluate(run_today: dict | None, run_baseline: dict | None, diff: dict) -> list[Alarm]:
    if run_today is None:
        missing = run_missing(run_today, run_baseline, diff)
        return [missing] if missing is not None else []
    if run_baseline is None:
        comparison_detectors = {record_count_drop, field_completeness_drop, duration_anomaly, churn_spike}
    else:
        comparison_detectors = set()
    return [alarm for detector in DETECTORS
            if detector not in comparison_detectors
            for alarm in [detector(run_today, run_baseline, diff)] if alarm is not None]


def load_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def append_alerts(
    alarms: list[Alarm],
    target: str,
    run_date: str,
    reports_root: Path,
    notify: bool,
) -> list[Alarm]:
    """Append only alarms not already recorded for the same target, date, and code."""
    alerts_path = reports_root / "alerts.jsonl"
    alerts_path.parent.mkdir(parents=True, exist_ok=True)
    alerts_path.touch(exist_ok=True)
    existing: set[tuple[str, str, str]] = set()
    with alerts_path.open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                payload = json.loads(line)
                existing.add((payload.get("target"), payload.get("date"), payload.get("code")))

    raised_at = datetime.now(JAKARTA).isoformat(timespec="seconds")
    new_alarms = [alarm for alarm in alarms if (target, run_date, alarm.code) not in existing]
    if new_alarms:
        with alerts_path.open("a", encoding="utf-8") as output:
            for alarm in new_alarms:
                payload = {"raised_at": raised_at, "target": target, "date": run_date, **asdict(alarm)}
                output.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        if notify and shutil.which("notify-send"):
            subprocess.run(
                ["notify-send", f"DriftWatch: {target}", "\n".join(alarm.message for alarm in new_alarms)],
                check=False,
            )
    return new_alarms


def check_missing_runs(
    targets: list[str],
    run_date: str,
    data_root: Path,
    reports_root: Path,
    notify: bool = True,
) -> dict[str, list[Alarm]]:
    """Check an explicit scheduled date and emit deduplicated RUN_MISSING alerts."""
    results: dict[str, list[Alarm]] = {}
    for target in targets:
        if (data_root / target / run_date / "run.json").is_file():
            results[target] = []
            continue
        missing = run_missing(None, None, {})
        alarms = [missing] if missing is not None else []
        append_alerts(alarms, target, run_date, reports_root, notify)
        results[target] = alarms
    return results


def run_alarms(target: str, run_date: str, data_root: Path, reports_root: Path, notify: bool = True) -> list[Alarm]:
    diff_path = reports_root / target / run_date / "diff.json"
    diff = json.loads(diff_path.read_text(encoding="utf-8"))
    run_today = load_json(data_root / target / run_date / "run.json")
    baseline_date = diff.get("baseline_date")
    run_baseline = load_json(data_root / target / baseline_date / "run.json") if baseline_date else None
    alarms = evaluate(run_today, run_baseline, diff)
    diff["alarms"] = [alarm.code for alarm in alarms]
    diff_path.write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    append_alerts(alarms, target, run_date, reports_root, notify)
    return alarms


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=list(CONTRACTS))
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument("--today", action="store_true")
    date_group.add_argument("--date")
    date_group.add_argument("--check-missing", metavar="DATE")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--reports-root", type=Path, default=Path("reports"))
    parser.add_argument("--no-notify", action="store_true")
    args = parser.parse_args()
    if args.check_missing:
        targets = [args.target] if args.target else list(CONTRACTS)
        results = check_missing_runs(
            targets, args.check_missing, args.data_root, args.reports_root, not args.no_notify
        )
        missing = [target for target, alarms in results.items() if alarms]
        print(f"check {args.check_missing}: RUN_MISSING={missing}")
        return int(bool(missing))
    if not args.target or not (args.today or args.date):
        parser.error("--target dan salah satu --today/--date wajib untuk evaluasi alarm")
    run_date = Date.today().isoformat() if args.today else args.date
    alarms = run_alarms(args.target, run_date, args.data_root, args.reports_root, not args.no_notify)
    print(f"{args.target} {run_date}: alarms={[alarm.code for alarm in alarms]}")
    return int(any(alarm.severity == "critical" for alarm in alarms))


if __name__ == "__main__":
    raise SystemExit(main())
