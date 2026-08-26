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

`docker-compose.yml` project ini: satu service nginx, bind `127.0.0.1:8100`,
nama proyek compose `driftwatch-lab`, mount `fixtures/site/` read-only.

```bash
uv run python scripts/gen_fixture.py --seed 1337
bash scripts/lab_up.sh
curl -sSI http://127.0.0.1:8100/ | head -1              # harus 200
curl -sS http://127.0.0.1:8100/page-1.html | grep -c 'item-card'   # harus 20
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
- `scripts/gen_fixture.py`, `fixtures/site/` (gitignored), `scripts/lab_up.sh`
- `docker-compose.yml`
- `scripts/drift_lab.py` (reset + verify + DO-01 + DO-03)
- D16 terkunci di `docs/DECISIONS.md`

## Definition of Done
- [ ] `robots.txt` keempat target diambil dan hasilnya ditulis di `docs/TARGETS.md`
- [ ] ≥ 3 kandidat `seo` dievaluasi; yang dipilih lolos **tujuh** kotak `docs/ETHICS.md` §2 dengan bukti per kotak
- [ ] Kandidat yang ditolak tercatat beserta alasannya
- [ ] D16 dipindahkan dari 🔓 ke terkunci di `docs/DECISIONS.md`
- [ ] `curl -sSI http://127.0.0.1:8100/` → `200`; halaman listing berisi 20 `item-card`
- [ ] `gen_fixture.py --seed 1337` dijalankan dua kali → hash folder identik (reproducible)
- [ ] `drift_lab.py --verify` exit 0; DO-01 dan DO-03 bisa diterapkan lalu di-`--reset`
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`4 target ditetapkan · N kandidat seo dievaluasi, 1 lolos · fixture 200 item · 2/11 oracle siap`

## Jebakan
- **Jangan pilih target `seo` karena datanya menarik.** Pilih karena gerbangnya lolos.
  Reputasi lebih mahal dari satu dataset.
- Jangan bind fixture ke `0.0.0.0`. `127.0.0.1` saja (D8).
- Jangan pakai port selain 8100 tanpa mengubah D8 — port lain berisiko menabrak
  service user (8000, 3000, 3100, 3170, 20080, 4000, 2379, 5540).
- Jangan sentuh `/home/rayin/infra/docker-compose.yml`.
- Fixture tanpa seed tetap = `make all` di salinan bersih tidak reproducible (P12 gagal).

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P1 ✅, 4 target, D16 terkunci, status fixture.
3. `git add -A && git commit -m "P01: target ditetapkan + gerbang etika + fixture driftlab" && git push`
