# DriftWatch — Tools: kenapa dipakai & perintah persisnya

Dua aturan pemilihan tool, berurutan:

1. **Pakai yang paling murah yang masih menyelesaikan pekerjaan.**
   Browser mahal (token, RAM, waktu). httpx murah. Naik tingkat hanya kalau dipaksa bukti.
2. **Pakai yang sudah ada di device ini; jangan pasang ulang per project (D21)** —
   tapi hanya untuk pekerjaan **waktu-bangun**. Yang dipakai saat pipeline **berjalan**
   wajib berdiri sendiri, karena ikut jadi syarat pasang di mesin klien.

## Yang sudah ada di device — dipakai ulang, nol pemasangan

| Sudah terpasang | Ukuran | Dipakai untuk | Catatan |
|---|---|---|---|
| cache `uv` `~/.cache/uv` | 1,6 GB | semua dependency Python | venv per project, **cache paket global** — `httpx`/`openpyxl` dst tidak pernah diunduh dua kali |
| cache Playwright `~/.cache/ms-playwright` | 2,0 GB | chromium/firefox/webkit | jangan hapus revisi lama (MCP `chrome-devtools` mem-pin `chromium-1228`) |
| service infra `plantuml` `:20080` | image 1,13 GB | diagram arsitektur (P12) | **sedang mati** → minta izin user untuk menyalakan (D22) |
| image `pandoc/core` | 305 MB | studi kasus PDF (P12) | `docker run --rm`; **jangan** `texlive/texlive` (8,73 GB) — pandoc cukup untuk 1 halaman A4 |
| MCP `playwright` + `chrome-devtools` | — | recon (P2 saja) | sudah terdaftar device-wide |
| MCP `serena` | — | telusur simbol saat kode sudah besar | opsional |
| `jq`, `sqlite3`, `ffmpeg`, `wf-recorder` | — | agregasi, checkpoint, video | sudah ada di PATH |

## Yang sengaja TIDAK dipakai walaupun tersedia di device

| Tersedia | Kenapa tidak dipakai |
|---|---|
| MySQL `:3306`, Redis `:6379`, TiDB `:4000` | checkpoint/dedupe **wajib SQLite**. Jaminan "bisa diputus lalu lanjut" tidak boleh bergantung pada layanan jaringan yang tidak dimiliki klien (D21) |
| MCP `excel` | `REPORT.xlsx` dibangun tanpa pengawasan pukul 09:00 oleh systemd; MCP butuh sesi agent yang hidup → tetap `openpyxl` |
| nginx `infra-dashboard` `:8000` | fixture butuh server yang **bisa diprogram** (DO-06 503, DO-08 jeda) dan menulis ke `infra/dashboard/` dilarang (D22) → `http.server` stdlib |
| `texlive/texlive` | 8,73 GB untuk satu halaman A4; `pandoc/core` 305 MB sudah cukup |
| n8n MCP | penjadwalan sudah dijawab systemd timer (D9), yang lebih dekat ke mesin klien |

---

## Peta cepat

| Tool | Lapis | Dipakai di fase | Menggantikan |
|---|---|---|---|
| `curl` | 0 | P1, P2 | membuka browser untuk hal yang bisa dijawab satu request |
| skill `web-recon` | 1 | P2 | menebak selector dari ingatan |
| MCP `playwright` | 1 | P2 saja | — |
| MCP `chrome-devtools` | 1 | P2 saja | membaca JS bundle manual |
| skill `scraper-forge` | — | P4 | menulis scraper dari nol tiap kali |
| `httpx` | 3–4 | P4–P12 | Playwright, kalau tidak butuh JS |
| `selectolax` | 3 | P4 | BeautifulSoup (10× lebih lambat) |
| `Playwright` (script) | 2 | P4, hanya kalau `js_required` | MCP browser untuk kerja berulang |
| SQLite | — | P4 | file `.txt` berisi daftar "sudah diproses" |
| `tenacity` | — | P4 | `try/except` + `sleep` manual |
| `typer` | — | P4 | `sys.argv` |
| `http.server` stdlib | — | P1, P8 | container nginx untuk fixture (D8) |
| systemd user timer | — | P7 | cron (D9) |
| `jq` | — | semua | membaca JSONL mentah ke context (boros token) |
| `openpyxl` | — | P11 | mengirim CSV telanjang ke klien |
| Claude API | — | P10 | menulis insight manual tiap hari |
| `ffmpeg` / `wf-recorder` | — | P12 | — |
| PlantUML infra (`:20080`) | — | P12 | menggambar diagram manual |
| `pandoc/core` (docker run --rm) | — | P12 | memasang texlive 8,73 GB |

---

## 1. `curl` — pengecekan termurah, selalu duluan

Sebelum membuka browser apa pun, empat perintah ini menjawab 70% pertanyaan recon:

```bash
BASE="https://books.toscrape.com"

curl -sS "$BASE/robots.txt"                       # boleh tidak? ada Crawl-delay?
curl -sS "$BASE/sitemap.xml" | head -50           # sitemap lengkap = crawl tidak perlu
curl -sSI "$BASE"                                 # server, CDN, Cloudflare?
curl -sS "$BASE/catalogue/page-1.html" -o /tmp/p.html && wc -c /tmp/p.html
grep -o '__NEXT_DATA__\|__NUXT__\|application/ld+json\|window.__INITIAL' /tmp/p.html | sort -u
```

Cara baca hasilnya:

| Yang terlihat | Artinya | Lompat ke |
|---|---|---|
| `__NEXT_DATA__` / `__NUXT__` / `window.__INITIAL` | data JSON tertanam di HTML | Lapis 4, tanpa selector |
| `application/ld+json` | metadata terstruktur siap pakai | Lapis 4 |
| judul/harga sudah ada di HTML | server-rendered | Lapis 3 (`httpx`+`selectolax`) |
| hanya `<div id="root"></div>` | butuh JS render | Lapis 2 (Playwright) |
| header `cf-ray` / `server: cloudflare` | ada proteksi | evaluasi ulang, mungkin batalkan |

## 2. Skill `web-recon` — fase pemetaan

Ada di `../skills/web-recon/SKILL.md`. Menghasilkan `recon/<target>.json`.
Panggil dengan menyebut skill-nya di awal sesi P2. **Jangan** lanjut ke codegen sebelum
`recon.json` lengkap dan `sample` terisi.

Tambahan wajib project ini di atas skill aslinya: `engine_rationale`, `ethics_gate`,
`expected_volume` (`docs/SCHEMA.md` §1).

## 3. MCP `playwright` + `chrome-devtools` — hanya untuk recon

Dipakai **hanya di P2**, hanya untuk hal yang tidak bisa dijawab `curl`:

1. `browser_navigate` ke halaman listing
2. scroll / klik "next page"
3. `browser_network_requests` → cari XHR/fetch yang membalas JSON

Kalau ketemu endpoint seperti `GET /api/quotes?page=2`, **langsung uji di luar browser**:

```bash
curl -sS "https://quotes.toscrape.com/api/quotes?page=2" -H 'Accept: application/json' | jq '.quotes[0]'
```

Berhasil tanpa browser → tutup browser, catat `recommended_engine: "httpx+json"`, selesai.
Ini momen "100× lebih cepat" yang dijual ke klien — dan `quotes.toscrape.com` sengaja
dipilih di D1 supaya momen ini bisa direkam untuk video P12.

⚠️ **MCP browser dilarang untuk pekerjaan berulang.** 1.000 halaman lewat MCP =
context habis dan tagihan token tidak masuk akal. Berulang = script.

## 4. Skill `scraper-forge` — recon → scraper produksi

Ada di `../skills/scraper-forge/SKILL.md`. Input wajibnya `recon.json`.
Ia sudah memuat kerangka `httpx` dan `Playwright` beserta sembilan komponen wajib
(rate limit, retry, checkpoint, dedupe, JSONL streaming, logging, UA jujur, CLI, guard sesi).

Di project ini kerangka itu **diperluas** dengan: penulisan `run.json`, perhitungan
`content_hash` (D7), `missing_reason` (D6), dan pencatatan `observed_min_gap_ms`.

## 5. `httpx` + `selectolax` — jalur produksi

```bash
uv add httpx selectolax tenacity typer pydantic
uv run python src/scrape.py --target books --limit 2      # cicip dulu
uv run python src/scrape.py --target books --resume       # full run
```

`selectolax` dipilih karena ~10× lebih cepat dari BeautifulSoup dan API-nya cukup:

```python
from selectolax.parser import HTMLParser
tree = HTMLParser(html)
for node in tree.css("article.product_pod"):
    title = n.attributes.get("title") if (n := node.css_first("h3 a")) else None
```

Prioritas selector (dari paling tahan banting): `data-*` > id semantik > class semantik >
struktur DOM. **Hindari** class hash (`.css-1x2y3z`) dan `nth-child` dalam — pasti patah.
Verifikasi tiap selector di 3 halaman berbeda sebelum dicatat ke `recon.json`.

## 6. SQLite — checkpoint & dedupe

Tanpa dependency tambahan, sudah ada di Python. Skema di `docs/SCHEMA.md` §4.

```bash
sqlite3 data/books/2026-08-27/progress.db "SELECT status, COUNT(*) FROM progress GROUP BY status;"
sqlite3 data/books/2026-08-27/progress.db "SELECT COUNT(*) FROM seen;"
```

Cara membuktikan resume bekerja (ini bukti nomor satu di portofolio):

```bash
uv run python src/scrape.py --target books &
sleep 25 && kill -9 %1                                   # putus paksa di tengah
sqlite3 …/progress.db "SELECT COUNT(*) FROM progress WHERE status='ok';"   # catat N
uv run python src/scrape.py --target books --resume      # lanjut
wc -l …/records.jsonl                                    # total benar, duplikat 0
```

## 7. `tenacity` — retry yang tidak bodoh

```python
@retry(stop=stop_after_attempt(4),
       wait=wait_exponential(min=2, max=30),
       retry=retry_if_exception_type((httpx.TransportError, RetryableHttpStatus)))
```

`RetryableHttpStatus` hanya dilempar untuk **429, 500, 502, 503, 504**.
404 dan 403 tidak pernah masuk ke sana — itu temuan, bukan gangguan.
Bukti aturan ini di P5: `grep -c RETRY run.log` harus 0 walaupun ada respons 403/404.

## 8. systemd user timer — penjadwalan (D9)

```bash
# pasang
mkdir -p ~/.config/systemd/user
cp deploy/driftwatch.service deploy/driftwatch.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now driftwatch.timer

# periksa
systemctl --user list-timers driftwatch.timer
systemctl --user status driftwatch.service
journalctl --user -u driftwatch.service --since "3 days ago" --no-pager | tail -40

# bukti untuk P9
journalctl --user -u driftwatch.service --since "3 days ago" -o short-iso | grep -c "Started"
```

Isi `driftwatch.timer` yang dikunci D3/D9:

```ini
[Timer]
OnCalendar=*-*-* 09:00:00 Asia/Jakarta
RandomizedDelaySec=300
Persistent=true
```

`Persistent=true` adalah alasan klaim "tahan mati listrik" boleh diucapkan: run yang
terlewat karena mesin mati akan dikejar saat mesin menyala lagi.
Kalau `systemctl --user` tidak tersedia, jatuh ke cron dan **catat penurunan itu** di `STATE.md`.

## 9. `jq` — membaca hasil tanpa membakar context

**Jangan pernah** membaca `records.jsonl` mentah ke context. Selalu agregasi:

```bash
wc -l data/books/2026-08-27/records.jsonl
jq -r '.fields.category' data/books/2026-08-27/records.jsonl | sort | uniq -c | sort -rn | head
jq -s 'length' data/books/2026-08-27/records.jsonl
jq -r '.record_id' data/books/2026-08-27/records.jsonl | sort | uniq -d | wc -l   # duplikat, harus 0
jq '.field_completeness' data/books/2026-08-27/run.json
jq -r 'select(.severity=="critical") | "\(.date) \(.target) \(.code)"' reports/alerts.jsonl
```

## 10. `openpyxl` — laporan mingguan

Dipakai di P11 untuk `REPORT.xlsx`. Alasan XLSX bukan CSV: klien non-teknis membuka
XLSX tanpa dialog impor, dan XLSX bisa memuat beberapa sheet + pewarnaan status.
Bentuk sheet-nya di `docs/CLIENT_REPORT.md` §3.

## 11. Claude API — insight di halaman demo (D14)

**Sebelum menulis kode LLM di P10, baca skill `claude-api` untuk model id dan harga yang
berlaku. Jangan mengarang dari ingatan.** Pagar yang sudah dikunci:

- maksimum 1 panggilan per target per hari
- input = ringkasan agregat (`counts`, 10 baris teratas), bukan seluruh dataset
- ada `--no-llm` yang membuat pipeline jalan penuh tanpa biaya sama sekali
- `ANTHROPIC_API_KEY` di `.env`, tidak pernah masuk repo atau halaman demo

## 12. `ffmpeg` / `wf-recorder` — video bukti (P12)

`wf-recorder` 0.6.0 ada di `~/.local/bin` (fakta terverifikasi dari project 1).
Rekam **satu monitor saja**, tanpa audio, dan pastikan layar tidak menampilkan
kredensial atau jendela kerja user:

```bash
wf-recorder -o eDP-1 -f /tmp/raw.mp4
ffmpeg -i /tmp/raw.mp4 -vf "scale=1920:1080" -c:v libx264 -crf 23 assets/v_resume_demo.mp4
```

## 13. PlantUML infra (`localhost:20080`) — diagram arsitektur

Service ini **sudah terdefinisi** di `/home/rayin/infra/docker-compose.yml` dan image-nya
sudah ada (1,13 GB). Saat plan ini ditulis ia **sedang mati**.

```bash
docker ps --format '{{.Names}}' | grep -q plantuml-server && echo hidup || echo mati
# kalau mati → MINTA IZIN USER dulu (D22), baru:
#   docker compose --project-directory /home/rayin/infra up -d plantuml
curl -sS -X POST --data-binary @assets/architecture.puml \
  http://localhost:20080/svg -o assets/architecture.svg
```

Jangan pasang PlantUML sendiri, jangan `docker run` image kedua. Jangan pernah `stop`
atau `restart` service infra yang sedang hidup.

## 13b. `pandoc/core` — studi kasus PDF satu halaman

```bash
docker run --rm -v "$PWD/assets:/data" pandoc/core \
  case_study.md -o v6_case_study.pdf --pdf-engine=weasyprint -V geometry:a4paper
```

Image sudah ada (305 MB). **Jangan** pakai `texlive/texlive` (8,73 GB) walaupun terpasang —
tidak sepadan untuk satu halaman. Jangan menulis ke `/home/rayin/infra/latex/`; direktori
itu sudah dipakai pekerjaan lain (D22).

## 14. Yang **tidak** dipakai, dan alasannya

| Tidak dipakai | Alasan |
|---|---|
| Scrapy | terlalu berat untuk 4 target; opini framework-nya menyulitkan checkpoint kustom |
| BeautifulSoup | ~10× lebih lambat dari `selectolax` tanpa keuntungan setara |
| Selenium | Playwright lebih cepat, API-nya lebih waras, sudah terpasang |
| proxy rotator | melanggar `docs/ETHICS.md` §1.6 |
| captcha solver | melanggar `docs/ETHICS.md` §1.6 |
| cron | kalah dari systemd user timer soal log & `Persistent=true` (D9) |
| Pandas | dataset ini streaming; `csv` + `json` stdlib sudah cukup dan tidak menahan RAM |
| Docker untuk fixture | fixture butuh server yang bisa diprogram, dan deliverable harus jalan tanpa Docker di mesin klien (D8) |
