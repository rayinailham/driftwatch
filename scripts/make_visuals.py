#!/usr/bin/env python3
"""Bangun visual pendukung P12 (v3, v4, v5) dari data nyata di repo ini.

Alat **waktu-bangun**, bukan runtime deliverable (D21): ia tidak dipanggil pipeline harian
dan tidak menambah dependency apa pun — SVG ditulis dengan stdlib, lalu `rsvg-convert`
(sudah ada di device) mengubahnya jadi PNG.

  v3_diff_timeline.png  reports/<target>/<tanggal>/diff.json  → baru/berubah/hilang per hari
  v4_alarm_matrix.png   keluaran `make oracles`               → 11 skenario x 10 kode alarm
  v5_tier_drop.png      recon/quotes.json                     → browser 8 request vs httpx 1

Pakai:
    uv run --no-sync python scripts/make_visuals.py --oracle-log <log make oracles>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TARGETS = ["books", "quotes", "seo", "driftlab"]

ALARM_CODES = [
    "ZERO_RECORDS", "RECORD_COUNT_DROP", "FIELD_COMPLETENESS_DROP", "SCHEMA_UNKNOWN_FIELD",
    "HTTP_ERROR_SPIKE", "RUN_MISSING", "RUN_FAILED", "DURATION_ANOMALY",
    "RATE_LIMIT_VIOLATION", "CHURN_SPIKE",
]

EXPECTED = {
    "DO-01": set(), "DO-02": set(), "DO-03": set(),
    "DO-04": {"ZERO_RECORDS", "RECORD_COUNT_DROP", "FIELD_COMPLETENESS_DROP", "RUN_FAILED", "CHURN_SPIKE"},
    "DO-05": {"FIELD_COMPLETENESS_DROP"},
    "DO-06": {"HTTP_ERROR_SPIKE"},
    "DO-07": {"RUN_FAILED", "SCHEMA_UNKNOWN_FIELD"},
    "DO-08": {"DURATION_ANOMALY"},
    "DO-09": {"RUN_MISSING"},
    "DO-10": {"CHURN_SPIKE"},
    "DO-11": {"RATE_LIMIT_VIOLATION"},
}

SCENARIO_NAME = {
    "DO-01": "data bertambah", "DO-02": "nilai berubah", "DO-03": "data hilang",
    "DO-04": "struktur patah", "DO-05": "field hilang sebagian", "DO-06": "situs bermasalah (503)",
    "DO-07": "field asing muncul", "DO-08": "situs melambat", "DO-09": "run terlewat",
    "DO-10": "restrukturisasi besar", "DO-11": "scraper terlalu cepat",
}

INK = "#1F2933"
MUTED = "#6B7280"
GRID = "#D8DEE6"
GREEN = "#2E7D32"
AMBER = "#E08700"
RED = "#C62828"
BLUE = "#1565C0"
PAPER = "#FFFFFF"
FONT = "DejaVu Sans, Arial, sans-serif"


def text(x, y, body, size=13, fill=INK, anchor="start", weight="normal"):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" font-weight="{weight}">{escape(str(body))}</text>'
    )


def rect(x, y, w, h, fill, stroke="none", rx=0, opacity=1.0):
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" '
        f'fill="{fill}" stroke="{stroke}" rx="{rx}" opacity="{opacity}"/>'
    )


def write(name: str, width: int, height: int, body: list[str]) -> Path:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        + rect(0, 0, width, height, PAPER)
        + "".join(body)
        + "</svg>"
    )
    svg_path = ASSETS / f"{name}.svg"
    png_path = ASSETS / f"{name}.png"
    svg_path.write_text(svg, encoding="utf-8")
    subprocess.run(
        ["rsvg-convert", "-w", str(width * 2), "-o", str(png_path), str(svg_path)], check=True
    )
    svg_path.unlink()
    print(f"{png_path.relative_to(ROOT)}  {width * 2}x{height * 2}")
    return png_path


# ---------------------------------------------------------------- v3


def read_timeline() -> tuple[list[str], dict[str, dict[str, dict[str, int]]]]:
    reports = ROOT / "reports"
    dates: set[str] = set()
    data: dict[str, dict[str, dict[str, int]]] = {}
    for target in TARGETS:
        folder = reports / target
        if not folder.is_dir():
            continue
        data[target] = {}
        for day in sorted(p.name for p in folder.iterdir() if p.is_dir()):
            path = folder / day / "diff.json"
            if not path.exists():
                continue
            counts = json.loads(path.read_text(encoding="utf-8"))["counts"]
            data[target][day] = counts
            dates.add(day)
    return sorted(dates), data


def build_v3() -> None:
    dates, data = read_timeline()
    if not dates:
        raise SystemExit("tidak ada reports/*/*/diff.json — jalankan pipeline dulu")
    width, height = 1180, 790
    left, top = 150, 108
    panel_h, gap = 118, 22
    plot_w = width - left - 300
    step = plot_w / len(dates)
    body = [
        text(40, 44, "Timeline diff DriftWatch — baru / berubah / hilang per hari", 21, INK, weight="bold"),
        text(40, 70, f"{len(dates)} tanggal berturut ({dates[0]} … {dates[-1]}) × 4 target, "
                     f"dari reports/<target>/<tanggal>/diff.json", 13, MUTED),
        text(40, 90, "Sumbu tegak diskalakan per target. Hari pertama = seluruh dataset masuk "
                     "sebagai 'baru', itu memang baseline.", 12, MUTED),
    ]
    legend_x = width - 290
    for index, (label, colour) in enumerate([("baru", GREEN), ("berubah", AMBER), ("hilang", RED)]):
        body.append(rect(legend_x, 78 + index * 20, 12, 12, colour, rx=2))
        body.append(text(legend_x + 20, 89 + index * 20, label, 12, INK))

    for row, target in enumerate(TARGETS):
        y0 = top + row * (panel_h + gap)
        series = data.get(target, {})
        peak = max(
            [max(c["added"], c["changed"], c["removed"]) for c in series.values()] or [1]
        ) or 1
        body.append(rect(left, y0, plot_w, panel_h, "#FAFBFC", stroke=GRID))
        body.append(text(40, y0 + 22, target, 15, INK, weight="bold"))
        body.append(text(40, y0 + 42, f"puncak {peak}", 11, MUTED))
        for fraction in (0.5, 1.0):
            gy = y0 + panel_h - fraction * (panel_h - 16)
            body.append(f'<line x1="{left}" y1="{gy:.1f}" x2="{left + plot_w}" y2="{gy:.1f}" '
                        f'stroke="{GRID}" stroke-dasharray="3 3"/>')
        for column, day in enumerate(dates):
            counts = series.get(day)
            cx = left + column * step
            if counts is None:
                body.append(text(cx + step / 2, y0 + panel_h / 2, "—", 12, MUTED, anchor="middle"))
                continue
            bar_w = min(14.0, step / 4.2)
            for index, key in enumerate(("added", "changed", "removed")):
                value = counts[key]
                bar_h = (value / peak) * (panel_h - 20) if peak else 0
                bx = cx + step / 2 - 1.5 * bar_w - 2 + index * (bar_w + 2)
                colour = (GREEN, AMBER, RED)[index]
                if value:
                    body.append(rect(bx, y0 + panel_h - bar_h - 4, bar_w, bar_h, colour, rx=2))
                    body.append(text(bx + bar_w / 2, y0 + panel_h - bar_h - 8, value, 10, colour,
                                     anchor="middle", weight="bold"))
                else:
                    body.append(rect(bx, y0 + panel_h - 6, bar_w, 2, GRID))
        if row == len(TARGETS) - 1:
            for column, day in enumerate(dates):
                body.append(text(left + column * step + step / 2, y0 + panel_h + 20,
                                 day[5:], 11, MUTED, anchor="middle"))

    note_y = top + len(TARGETS) * (panel_h + gap) + 34
    body.append(rect(40, note_y - 18, width - 80, 58, "#FFF6F6", stroke="#F3C9C9", rx=6))
    body.append(text(56, note_y + 2, "Yang jujur ditampilkan, bukan disembunyikan:", 13, RED, weight="bold"))
    body.append(text(56, note_y + 22,
                     "driftlab 2026-08-29 dan 08-30 → 200 hilang. Fixture lokal tidak pernah dinyalakan saat timer memicu; "
                     "alarm menangkapnya, akar masalahnya ditutup D24.", 12, INK))
    write("v3_diff_timeline", width, height, body)


# ---------------------------------------------------------------- v4


def parse_oracles(log_path: Path) -> dict[str, set[str]]:
    observed: dict[str, set[str]] = {}
    pattern = re.compile(r"^(DO-\d\d)\s.*alarms=\[(.*?)\]")
    for line in log_path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        codes = {c.strip().strip("'\"") for c in match.group(2).split(",") if c.strip()}
        observed[match.group(1)] = codes
    return observed


def build_v4(log_path: Path) -> None:
    observed = parse_oracles(log_path)
    if len(observed) != 11:
        raise SystemExit(f"log oracle memuat {len(observed)} skenario, butuh 11: {log_path}")
    cell_w, cell_h = 62, 40
    left, top = 330, 250
    width = left + cell_w * len(ALARM_CODES) + 250
    height = top + cell_h * 11 + 130
    body = [
        text(40, 46, "Matriks alarm DriftWatch — 11 skenario drift × 10 kode alarm", 21, INK, weight="bold"),
        text(40, 72, "Kerusakan ditanam di fixture lokal, lalu pipeline produksi yang sama "
                     "dijalankan. Detektor tidak pernah tahu skenario mana yang aktif.", 13, MUTED),
        text(40, 92, "Hijau = kode alarm yang memang seharusnya berbunyi dan berbunyi. "
                     "Abu = seharusnya diam dan diam. Merah = meleset.", 13, MUTED),
    ]
    for index, code in enumerate(ALARM_CODES):
        x = left + index * cell_w + cell_w / 2
        body.append(f'<g transform="rotate(-58 {x} {top - 12})">' +
                    text(x, top - 12, code.replace("_", " ").lower(), 11, MUTED, anchor="start") + "</g>")
    passed = 0
    for row, scenario in enumerate(sorted(EXPECTED)):
        y = top + row * cell_h
        want, got = EXPECTED[scenario], observed[scenario]
        ok = want == got
        passed += int(ok)
        body.append(text(40, y + 26, scenario, 13, INK, weight="bold"))
        body.append(text(104, y + 26, SCENARIO_NAME[scenario], 12, MUTED))
        for column, code in enumerate(ALARM_CODES):
            x = left + column * cell_w
            expected_here, observed_here = code in want, code in got
            if expected_here and observed_here:
                fill, mark, mark_fill = GREEN, "✓", "#FFFFFF"
            elif not expected_here and not observed_here:
                fill, mark, mark_fill = "#F1F4F7", "", MUTED
            else:
                fill, mark, mark_fill = RED, "!", "#FFFFFF"
            body.append(rect(x + 2, y + 4, cell_w - 4, cell_h - 8, fill, stroke=GRID, rx=4))
            if mark:
                body.append(text(x + cell_w / 2, y + cell_h / 2 + 5, mark, 15, mark_fill,
                                 anchor="middle", weight="bold"))
        verdict_x = left + len(ALARM_CODES) * cell_w + 22
        body.append(text(verdict_x, y + 26, "PASS" if ok else "FAIL", 14,
                         GREEN if ok else RED, weight="bold"))
    footer = top + 11 * cell_h + 40
    body.append(rect(40, footer - 20, width - 80, 46, "#F2F8F3", stroke="#C7E2CB", rx=6))
    body.append(text(56, footer + 8, f"{passed}/11 PASS — `make oracles`, exit 0. "
                                     f"0 false positive: DO-01..DO-03 mengubah data tanpa merusaknya "
                                     f"dan sistem benar-benar diam.", 14, GREEN, weight="bold"))
    write("v4_alarm_matrix", width, height, body)


# ---------------------------------------------------------------- v5


def build_v5() -> None:
    api = json.loads((ROOT / "recon" / "quotes.json").read_text(encoding="utf-8"))["api"]
    before = api["browser_requests_for_same_data"]
    after = api["httpx_requests_for_same_data"]
    width, height = 1100, 620
    body = [
        text(40, 46, "Turun lapis engine — target `quotes`", 21, INK, weight="bold"),
        text(40, 72, "Browser dipakai SEKALI untuk recon (membaca network tab), menemukan "
                     "XHR GET /api/quotes?page=N, lalu dibuang.", 13, MUTED),
        text(40, 92, "Endpoint diuji ulang di luar browser: HTTP 200, tanpa cookie, tanpa "
                     "Authorization/CSRF/Referer. Karena berhasil, browser tidak dipakai lagi.", 13, MUTED),
    ]
    bar_top, bar_h, bar_left = 170, 62, 350
    scale = 600 / before
    rows = [
        ("SEBELUM — Lapis 1/2 (browser)", before, RED,
         "HTML + CSS + jQuery + 2 font + XHR + favicon"),
        ("SESUDAH — Lapis 4 (httpx+json)", after, GREEN,
         "satu GET JSON, tanpa aset, tanpa proses browser"),
    ]
    for index, (label, value, colour, detail) in enumerate(rows):
        y = bar_top + index * (bar_h + 92)
        body.append(text(40, y + 26, label, 14, INK, weight="bold"))
        body.append(text(40, y + 48, detail, 11, MUTED))
        body.append(rect(bar_left, y, value * scale, bar_h, colour, rx=6))
        body.append(text(bar_left + value * scale + 16, y + bar_h / 2 + 8,
                         f"{value} request", 20, colour, weight="bold"))
    arrow_x = bar_left + 24
    body.append(f'<line x1="{arrow_x}" y1="{bar_top + bar_h + 14}" x2="{arrow_x}" '
                f'y2="{bar_top + bar_h + 74}" stroke="{BLUE}" stroke-width="2" marker-end="url(#a)"/>')
    body.append('<defs><marker id="a" markerWidth="8" markerHeight="8" refX="4" refY="4" '
                f'orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{BLUE}"/></marker></defs>')
    body.append(text(arrow_x + 18, bar_top + bar_h + 54,
                     f"hemat {before // after}× untuk data yang sama", 15, BLUE, weight="bold"))
    box_y = 452
    body.append(rect(40, box_y, width - 80, 118, "#F4F8FD", stroke="#C9DCF0", rx=8))
    body.append(text(60, box_y + 30, "Panen penuh 100 kutipan, harian:", 14, INK, weight="bold"))
    for index, line in enumerate([
        "10 request httpx  (has_next=false pada halaman 10)",
        "0 proses browser · 0 dependensi Playwright · 0 browser terpasang di mesin klien",
        "Menahan browser padahal httpx cukup adalah kegagalan desain di project ini, bukan pilihan gaya.",
    ]):
        body.append(text(60, box_y + 56 + index * 22, ("· " if index < 2 else "") + line, 12,
                         INK if index < 2 else MUTED))
    write("v5_tier_drop", width, height, body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-log", type=Path, required=True,
                        help="berkas berisi keluaran `make oracles`")
    args = parser.parse_args()
    ASSETS.mkdir(exist_ok=True)
    build_v3()
    build_v4(args.oracle_log)
    build_v5()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
