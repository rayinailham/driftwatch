"""Build the public demo payload and page from the latest snapshot and diff."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import date as Date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from contracts import CONTRACTS
from env import load_env

JAKARTA = ZoneInfo("Asia/Jakarta")

# driftlab sengaja tidak dipublikasikan: ia fixture lokal (127.0.0.1), dan alamat
# host internal dilarang muncul di halaman publik.
PUBLIC_TARGETS = ("books", "quotes", "seo")
DEFAULT_TARGET = "books"
MAX_ROWS = 200  # D13

SOURCES = {
    "books": {
        "name": "books.toscrape.com",
        "url": "https://books.toscrape.com",
        "attribution": "Sandbox latihan scraping milik Scraping Hub. Metadata katalog saja.",
    },
    "quotes": {
        "name": "quotes.toscrape.com",
        "url": "https://quotes.toscrape.com",
        "attribution": "Sandbox latihan scraping milik Scraping Hub. Teks kutipan tidak disimpan (D17).",
    },
    "seo": {
        "name": "python-httpx.org",
        "url": "https://www.python-httpx.org",
        "attribution": "Dokumentasi HTTPX (proyek sumber terbuka). Hanya metadata SEO, bukan isi halaman.",
    },
}

# Dipilih lewat skill `claude-api` (tabel model, cache 2026-06-24): Claude Haiku 4.5
# adalah tarif termurah yang tersedia ($1/$5 per 1 juta token) dan cukup untuk
# meringkas ~20 baris agregat. Fase P10 memang meminta model termurah yang memadai.
INSIGHT_MODEL = "claude-haiku-4-5"
INSIGHT_MAX_TOKENS = 400
PRICE_USD_PER_MTOK = {"input": 1.00, "output": 5.00}

INSIGHT_SYSTEM = (
    "Kamu analis data untuk laporan pemantauan situs harian. Jawab dalam bahasa Indonesia, "
    "maksimal 4 kalimat, tanpa jargon teknis, tanpa nama pustaka atau istilah kode. "
    "Jawab dua hal: apa yang berubah hari ini, dan mana yang layak dilihat manusia. "
    "Kalau tidak ada yang berubah, katakan itu apa adanya tanpa mengarang temuan."
)


def latest_date(directory: Path) -> str | None:
    dates = sorted(p.name for p in directory.iterdir() if p.is_dir()) if directory.is_dir() else []
    return dates[-1] if dates else None


def read_records(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def status_map(diff: dict[str, Any]) -> dict[str, str]:
    labels = {"added": "baru", "changed": "berubah"}
    return {
        entry["record_id"]: label
        for key, label in labels.items()
        for entry in diff.get(key, [])
    }


def build_rows(records: list[dict[str, Any]], statuses: dict[str, str], target: str) -> list[dict[str, Any]]:
    """Rows carry contract metadata only — never source content (D13, ETHICS §3)."""
    names = [field.name for field in CONTRACTS[target]["fields"]]
    ranked = sorted(records, key=lambda record: (statuses.get(record["record_id"], "tetap") == "tetap",))
    rows = []
    for record in ranked[:MAX_ROWS]:
        fields = record.get("fields", {})
        rows.append(
            {
                "record_id": record["record_id"],
                "url": record.get("url", ""),
                "status": statuses.get(record["record_id"], "tetap"),
                "fields": {name: fields.get(name) for name in names},
            }
        )
    return rows


def aggregate_prompt(target: str, payload: dict[str, Any], diff: dict[str, Any]) -> str:
    """Aggregate only — never the whole dataset (P10 cost guard)."""
    counts = payload["counts"]
    health = diff.get("health", {})
    lines = [
        f"Situs: {payload['source']['name']} ({target})",
        f"Tanggal: {payload['generated_at'][:10]} · pembanding: {diff.get('baseline_date') or 'belum ada'}",
        f"Total record: {counts['total']} · baru: {counts['added_today']} · "
        f"berubah: {counts['changed_today']} · hilang: {counts['removed_today']}",
        f"Kelengkapan field turun: {health.get('field_completeness_delta') or 'tidak ada'}",
        f"Peringatan aktif: {diff.get('alarms', []) or 'tidak ada'}",
        "",
        "10 baris teratas:",
    ]
    for row in payload["rows"][:10]:
        fields = {key: value for key, value in row["fields"].items() if value not in (None, "")}
        lines.append(f"- [{row['status']}] {json.dumps(fields, ensure_ascii=False)[:200]}")
    return "\n".join(lines)


def empty_insight(reason: str) -> dict[str, Any]:
    return {
        "model": None,
        "text": None,
        "reason": reason,
        "generated_at": None,
        "input_tokens": 0,
        "output_tokens": 0,
    }


def generate_insight(target: str, payload: dict[str, Any], diff: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print(f"peringatan: ANTHROPIC_API_KEY kosong, {target} jatuh ke mode tanpa LLM")
        return empty_insight("kunci API tidak tersedia; jatuh otomatis ke mode tanpa LLM")

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=INSIGHT_MODEL,
            max_tokens=INSIGHT_MAX_TOKENS,
            system=INSIGHT_SYSTEM,
            messages=[{"role": "user", "content": aggregate_prompt(target, payload, diff)}],
        )
    except anthropic.APIStatusError as error:
        print(f"peringatan: panggilan insight {target} gagal ({error.status_code}), lanjut tanpa LLM")
        return empty_insight(f"panggilan API gagal dengan status {error.status_code}")
    except anthropic.APIConnectionError:
        print(f"peringatan: insight {target} tidak bisa menghubungi API, lanjut tanpa LLM")
        return empty_insight("tidak bisa menghubungi API")

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return {
        "model": response.model,
        "text": text or None,
        "reason": None,
        "generated_at": datetime.now(JAKARTA).isoformat(timespec="seconds"),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def previous_insight(path: Path, today: str) -> dict[str, Any] | None:
    """Reuse today's insight so a target never costs more than one call per day."""
    if not path.exists():
        return None
    try:
        stored = json.loads(path.read_text(encoding="utf-8")).get("insight")
    except json.JSONDecodeError:
        return None
    if isinstance(stored, dict) and (stored.get("generated_at") or "").startswith(today):
        return stored
    return None


def build_payload(
    target: str,
    data_root: Path,
    reports_root: Path,
    web_root: Path,
    use_llm: bool,
) -> dict[str, Any] | None:
    run_date = latest_date(data_root / target)
    if run_date is None:
        print(f"lewati {target}: belum ada snapshot")
        return None
    records_path = data_root / target / run_date / "records.jsonl"
    diff_path = reports_root / target / run_date / "diff.json"
    if not records_path.exists():
        print(f"lewati {target}: {records_path.name} tidak ada untuk {run_date}")
        return None

    records = read_records(records_path)
    diff = json.loads(diff_path.read_text(encoding="utf-8")) if diff_path.exists() else {}
    counts = diff.get("counts", {})
    statuses = status_map(diff)

    payload: dict[str, Any] = {
        "generated_at": datetime.now(JAKARTA).isoformat(timespec="seconds"),
        "target": target,
        "snapshot_date": run_date,
        "source": SOURCES[target],
        "counts": {
            "total": len(records),
            "added_today": counts.get("added", 0),
            "changed_today": counts.get("changed", 0),
            "removed_today": counts.get("removed", 0),
        },
        "insight": empty_insight("panen ini dijalankan tanpa ringkasan AI"),
        "rows": build_rows(records, statuses, target),
    }

    if use_llm:
        cached = previous_insight(web_root / f"data-{target}.json", run_date)
        payload["insight"] = cached or generate_insight(target, payload, diff)
    return payload


def render_page(payloads: list[dict[str, Any]], template: Path, out_path: Path) -> None:
    bundle = json.dumps(payloads, ensure_ascii=False, indent=1)
    html = template.read_text(encoding="utf-8")
    marker = '<script id="dw-data" type="application/json">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    out_path.write_text(html[:start] + "\n" + bundle + "\n" + html[end:], encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", choices=list(PUBLIC_TARGETS))
    parser.add_argument("--no-llm", action="store_true", help="jalankan tanpa satu pun panggilan API")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--reports-root", type=Path, default=Path("reports"))
    parser.add_argument("--web-root", type=Path, default=Path("web"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    load_env(root)
    targets = args.target or list(PUBLIC_TARGETS)
    args.web_root.mkdir(parents=True, exist_ok=True)

    payloads = []
    for target in targets:
        payload = build_payload(target, args.data_root, args.reports_root, args.web_root, not args.no_llm)
        if payload is None:
            continue
        out = args.web_root / f"data-{target}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payloads.append(payload)
        insight = payload["insight"]
        print(
            f"{target}: {len(payload['rows'])} baris · insight "
            f"{insight['input_tokens']}+{insight['output_tokens']} token"
        )

    if not payloads:
        print("tidak ada payload yang bisa dipublikasikan")
        return 1

    default = next((p for p in payloads if p["target"] == DEFAULT_TARGET), payloads[0])
    shutil.copyfile(args.web_root / f"data-{default['target']}.json", args.web_root / "data.json")
    render_page(payloads, args.web_root / "template.html", args.web_root / "index.html")

    tokens = sum(p["insight"]["input_tokens"] for p in payloads), sum(p["insight"]["output_tokens"] for p in payloads)
    cost = tokens[0] / 1e6 * PRICE_USD_PER_MTOK["input"] + tokens[1] / 1e6 * PRICE_USD_PER_MTOK["output"]
    print(f"web/index.html + web/data.json ditulis · {tokens[0]}+{tokens[1]} token · ~${cost:.5f}/hari")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
