# P1 — Target & Gerbang Etika

**Tujuan sesi:** empat target ditetapkan, target `seo` lolos gerbang etika, dan fixture
lokal `driftlab` hidup di `127.0.0.1:8100`. Belum ada scraper.

**Prasyarat:** P0 selesai.
**Read-set:** `STATE.md`, file ini, `docs/ETHICS.md`, `docs/DECISIONS.md` (D1, D2, D3, D8),
`docs/DRIFT_ORACLES.md`.
**Budget:** sedang.

---

## Langkah

### 1. Audit `robots.txt` keempat target
```bash
for u in https://books.toscrape.com https://quotes.toscrape.com; do
  echo "=== $u"; curl -sS "$u/robots.txt" || echo "(tidak ada robots.txt)"
done
```
Catat per target: `allowed`, `crawl_delay`, daftar `disallow`, lokasi `sitemap`.
Tidak ada `robots.txt` ≠ boleh semaunya — tetap pakai default D3 (1,0 dtk, concurrency 3).

### 2. Pilih target `seo` lewat gerbang `docs/ETHICS.md` §2
Evaluasi minimal **3 kandidat**. Untuk tiap kandidat jalankan tujuh kotak gerbang itu satu
per satu dan tulis hasilnya. Kandidat yang gagal **satu** kotak dibuang, dan alasannya
tetap dicatat — daftar penolakan itu sendiri adalah bukti kredibilitas untuk klien.

Kandidat yang layak dievaluasi: situs dokumentasi open-source, blog proyek open-source,
atau situs dengan API publik resmi. **Jangan** situs berita komersial, toko online nyata,
atau situs yang ToS-nya melarang automated access.

Hasilnya kunci sebagai **D16** di `docs/DECISIONS.md` (pindahkan dari daftar 🔓 ke terkunci).

### 3. Bangun fixture `driftlab` (D2, D8)
`scripts/gen_fixture.py` menghasilkan **200 item** dari seed tetap `--seed 1337` ke
`fixtures/site/`. Tiap item: `item_id`, `name`, `price`, `category`, `note`.
Struktur halaman: listing berpaginasi (20 item/halaman) + halaman detail per item —
sengaja meniru bentuk situs e-commerce supaya scraper-nya realistis.

**Server fixture: `http.server` stdlib, bukan container (D8).**
`scripts/lab_serve.py` — `ThreadingHTTPServer` + handler kustom, bind `127.0.0.1:8100`,
melayani `fixtures/site/`. `scripts/lab_up.sh` menjalankannya di latar + menulis PID-nya.

Handler wajib punya dua kait yang dipakai P8, dibaca dari berkas penanda
`fixtures/.scenario` (kalau tidak ada, server berperilaku normal):

```python
# DO-06: 15% request dibalas 503     → if hash(path) % 100 < 15: send_error(503)
# DO-08: 10% halaman dijeda 4 detik  → if hash(path) % 100 < 10: time.sleep(4)
```

Inilah alasan container dibuang: nginx statis tidak bisa melakukan dua hal itu tanpa
konfigurasi bersyarat yang dikarang, dan deliverable jadi menuntut Docker di mesin klien.

```bash
uv run python scripts/gen_fixture.py --seed 1337
bash scripts/lab_up.sh
curl -sSI http://127.0.0.1:8100/ | head -1              # harus 200
curl -sS http://127.0.0.1:8100/page-1.html | grep -c 'item-card'   # harus 20
bash scripts/lab_down.sh                                # matikan lewat PID
```

### 4. Kerangka `scripts/drift_lab.py`
Fase ini cukup membuat `--reset`, `--verify`, dan **dua** skenario paling sederhana
(DO-01 tambah, DO-03 hapus) sebagai bukti mekanismenya jalan. Sembilan skenario sisanya
diselesaikan di P8, saat detektornya sudah ada untuk diuji.

`--verify` di P1 cukup memastikan: fixture dasar utuh (200 item), seed reproducible
(bangun ulang → hash folder sama), dan mutasi bisa diterapkan lalu dibalikkan.

### 5. Tulis `docs/TARGETS.md`
Satu tabel per target: URL, peran, `render_mode` dugaan (belum dikonfirmasi — itu P2),
hasil audit `robots.txt`, volume perkiraan, dan **untuk `seo`: tujuh kotak gerbang beserta
bukti tiap kotak**. Plus daftar kandidat yang ditolak dan alasannya.

---

## Output fase
- `docs/TARGETS.md`
- `scripts/gen_fixture.py`, `fixtures/site/` (gitignored)
- `scripts/lab_serve.py`, `scripts/lab_up.sh`, `scripts/lab_down.sh`
- `scripts/drift_lab.py` (reset + verify + DO-01 + DO-03)
- D16 terkunci di `docs/DECISIONS.md`

## Definition of Done
- [x] `robots.txt` keempat target diambil dan hasilnya ditulis di `docs/TARGETS.md`
- [x] ≥ 3 kandidat `seo` dievaluasi; yang dipilih lolos **tujuh** kotak `docs/ETHICS.md` §2 dengan bukti per kotak
- [x] Kandidat yang ditolak tercatat beserta alasannya
- [x] D16 dipindahkan dari 🔓 ke terkunci di `docs/DECISIONS.md`
- [x] `curl -sSI http://127.0.0.1:8100/` → `200`; halaman listing berisi 20 `item-card`
- [x] `gen_fixture.py --seed 1337` dijalankan dua kali → hash folder identik (reproducible)
- [x] `drift_lab.py --verify` exit 0; DO-01 dan DO-03 bisa diterapkan lalu di-`--reset`
- [x] Kait `.scenario` terbukti: tulis penanda 503 → `curl` beberapa kali → sebagian balas 503;
      hapus penanda → semua balas 200
- [x] **Tidak ada `docker-compose.yml`** di project ini (D8); `lab_up.sh` tidak memanggil Docker
- [x] **Commit + push berhasil** (D19)

### Bukti nyata (2026-08-27)

```text
robots: books=404 · quotes=404 · HTTPX=404 · driftlab=200 Allow:/
kandidat: HTTPX=23 URL PASS 7/7 · FastAPI=151 URL PASS 7/7 · Pydantic=1796 URL FAIL volume
first=b09a1d162a6608374fb26ad7c95cfa33f5e055217cb4c7b8be733bb8e22ce5d3
second=b09a1d162a6608374fb26ad7c95cfa33f5e055217cb4c7b8be733bb8e22ce5d3
identical=yes
baseline items=200 reproducible_sha256=b09a1d162a6608374fb26ad7c95cfa33f5e055217cb4c7b8be733bb8e22ce5d3
DO-01 added=12 PASS
DO-03 removed=1 PASS
2/11 PASS; fixture reset to 200 items
HTTP root: HTTP/1.0 200 OK
item-card: 20
DO-06: 32 200 · 8 503
reset: 40 200
compileall=PASS bash-n=PASS docker-compose=absent forbidden_refs=0
```

## Metrik selesai
`4 target ditetapkan · N kandidat seo dievaluasi, 1 lolos · fixture 200 item · 2/11 oracle siap`

## Jebakan
- **Jangan pilih target `seo` karena datanya menarik.** Pilih karena gerbangnya lolos.
  Reputasi lebih mahal dari satu dataset.
- Jangan bind fixture ke `0.0.0.0`. `127.0.0.1` saja (D8).
- **Jangan bikin `docker-compose.yml`** untuk fixture ini, dan jangan menumpang nginx
  `infra-dashboard` `:8000` — menulis ke `/home/rayin/infra/dashboard/` dilarang (D22).
- Jangan pakai port selain 8100 tanpa mengubah D8 — port lain berisiko menabrak
  service user (8000, 3000, 3100, 3170, 20080, 4000, 2379, 5540).
- Jangan sentuh apa pun di `/home/rayin/infra/` (D22).
- Fixture tanpa seed tetap = `make all` di salinan bersih tidak reproducible (P12 gagal).

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P1 ✅, 4 target, D16 terkunci, status fixture.
3. `git add -A && git commit -m "P01: target ditetapkan + gerbang etika + fixture driftlab" && git push`
