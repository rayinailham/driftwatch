# DriftWatch — Master Plan

Total **13 fase (P0–P12)**. Tiap fase dirancang selesai dalam **satu sesi agent**,
tanpa perlu membaca fase lain.

Sumber: `../portfolio/portfolio_02_scraper_pipeline.md`.
Pola kerja diwarisi dari project 1 (`../crosscheck/`) yang sudah selesai 11/11.

---

## Prinsip pemecahan fase

1. **Satu fase = satu artefak konkret.** Kalau tidak lahir file baru, fase itu belum selesai.
2. **Satu fase = satu jenis pekerjaan.** Jangan campur "bangun scraper" dengan "bikin laporan".
3. **Read-set eksplisit.** Tiap file fase menyebut file apa saja yang boleh dibaca. Di luar itu, jangan.
4. **Turun lapis secepatnya.** Recon pakai MCP browser (mahal token), produksi pakai `httpx`.
5. **Handoff lewat file, bukan ingatan.** `STATE.md` satu-satunya memori antar sesi.
6. **Yang pernah ambigu dikunci sekali** di `docs/DECISIONS.md`; bentuk file hasil di `docs/SCHEMA.md`.
7. **Bukti > klaim.** DoD dicentang hanya dengan output perintah yang benar-benar dijalankan.

---

## Peta fase

| # | Fase | Output utama | Estimasi | Berat token |
|---|---|---|---|---|
| P0 | Bootstrap & Environment | `pyproject.toml`, `uv.lock`, struktur folder, `env-check.md` | 45–60 mnt | ringan |
| P1 | Target & Gerbang Etika | `docs/TARGETS.md`, audit `robots.txt` 4 target, fixture `driftlab` hidup | 60–90 mnt | sedang |
| P2 | Recon | `recon/<target>.json` ×4, keputusan engine per target | 90 mnt | **berat** |
| P3 | Kontrak Data | `docs/SCHEMA.md` terkunci + `src/contracts.py` + `src/validate.py` | 60–90 mnt | sedang |
| P4 | Mesin Scraper | `src/scrape.py` — rate limit, retry, checkpoint, dedupe, log, CLI | 120 mnt | sedang |
| P5 | Validasi & Bukti Resume | 20-record run, 3 record dicek manual, kill→resume terbukti, unit test | 90 mnt | ringan |
| P6 | Panen Penuh & Dataset | ≥ 1.000 record, CSV + JSONL, `docs/DATA_DICTIONARY.md` | 60–90 mnt | sedang |
| P7 | Penjadwalan | systemd user timer + `scripts/daily_run.sh` + rotasi log | 60 mnt | ringan |
| P8 | Mesin Diff & Alarm | `src/diff.py`, `src/alarm.py`, 10 kode alarm, 11 oracle lulus | 120 mnt | sedang |
| P9 | Soak 3 Hari | bukti timer jalan 3 hari berturut tanpa disentuh | jam dinding | sangat ringan |
| P10 | Halaman Demo + Insight LLM | `web/index.html` + `web/data.json` + ringkasan Claude API | 90 mnt | sedang |
| P11 | Laporan Klien | `src/report.py` → digest harian `.md` + `REPORT.xlsx` mingguan | 90 mnt | sedang |
| P12 | Visual, Packaging & Gladi Bersih | video 60 dtk, diagram, `Makefile`, README publik, audit rahasia | 120 mnt | ringan |

**Total ≈ 16–20 jam kerja aktif**, plus 3 hari jam dinding untuk P9 yang berjalan di latar.

---

## Ketergantungan

```
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 ──► P9 (soak, jam dinding)
                                  │
                                  └─► P8 ──► P11 ──► P12
                                  │            ▲
                                  └─► P10 ─────┘
```

Aturan turunan:

- **P7 harus dicapai secepat mungkin.** Begitu timer nyala, jam P9 mulai berdetak sendiri.
  Sesi-sesi berikutnya (P8, P10, P11) dikerjakan **sambil menunggu** soak terkumpul.
- **P9 bukan sesi kerja.** Ia hanya gerbang: cek log, catat bukti, tutup. Kalau umur soak
  belum 3 hari, agent **melewati** P9 dan mengerjakan fase tersedia berikutnya.
- **P8 butuh P6** (harus ada baseline dataset untuk dibandingkan) dan **fixture `driftlab`** dari P1.
- **P10 butuh P6** (butuh data asli untuk ditampilkan). Tidak butuh P8.
- **P11 butuh P8** (laporan memuat hasil diff + alarm).
- **P12 butuh semua**, termasuk P9 tertutup — video menampilkan timer yang sudah 3 hari jalan.

---

## Jalur kritis (kenapa urutannya begitu)

Portofolio ini menjual **tiga bukti**, bukan satu:

| Bukti | Lahir di | Kenapa klien peduli |
|---|---|---|
| "Bisa diputus lalu lanjut" | P5 | pesaing kirim script yang mengulang dari nol |
| "Jalan sendiri 3 hari" | P7 → P9 | pesaing kirim script sekali pakai |
| "Berteriak kalau situs berubah" | P8 | pesaing kirim script yang diam-diam mengembalikan 0 baris |

Tiga bukti itu adalah alasan tiga fase paling awal yang bisa didahulukan: P5, P7, P8.
Fase kosmetik (P10, P11, P12) tidak pernah boleh mendahului mereka.

---

## Aturan sesi agent

**Awal sesi — baca ini saja:**
```
driftwatch/STATE.md
driftwatch/docs/DECISIONS.md
driftwatch/phases/phase-NN-<nama>.md
```
Plus file yang disebut di bagian "Read-set" fase tersebut. Tidak lebih.

**Akhir sesi — wajib:**
1. Centang DoD di file fase (edit di tempat).
2. Update `STATE.md`: status fase, artefak baru, angka metrik nyata, blocker.
3. Jangan lanjut fase berikutnya di sesi yang sama kecuali fase itu bertanda **ringan**
   dan fase sekarang sudah 100% selesai.

**Yang membuat sesi boros token (hindari):**
- Membaca `data/**/records.jsonl` mentah-mentah. Pakai `jq`, `wc -l`, `sort | uniq -c`.
- Membaca `../HARNESS.md` atau `../portfolio/` — kutipan yang perlu sudah disalin ke file fase.
- Membuka HTML fixture satu per satu. Cukup `ls | wc -l` + 1–2 sampel.
- Memakai MCP browser untuk pekerjaan berulang. MCP hanya untuk recon di P2.

---

## Definisi "project selesai"

Semua checklist di `docs/ACCEPTANCE.md` (A1–A12) tercentang, **dan** orang lain bisa
menjalankan seluruh pipeline dari nol dengan satu perintah (`make all`) dan mendapat
hasil yang sama.

## Dokumen kunci

| File | Peran |
|---|---|
| `docs/DECISIONS.md` | keputusan terkunci (D1–D15). Menang atas dokumen lain. |
| `docs/SCHEMA.md` | bentuk semua file hasil. Dikunci di P3. |
| `docs/ETHICS.md` | batas legal & etika. Menang atas kenyamanan teknis. |
| `docs/DRIFT_ORACLES.md` | 11 skenario mutasi fixture = oracle untuk 10 kode alarm. |
| `docs/PIPELINE.md` | alur data ujung ke ujung, satu halaman. |
| `docs/TOOLS.md` | tiap tool: kenapa dipakai + perintah persisnya. |
| `docs/CLIENT_REPORT.md` | bentuk, nada, dan irama laporan ke klien. |
