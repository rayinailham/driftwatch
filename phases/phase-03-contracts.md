# P3 — Kontrak Data

**Tujuan sesi:** bentuk data dikunci dan **ditegakkan oleh kode**, bukan oleh niat baik.
Setelah fase ini, tidak ada lagi diskusi "field-nya apa saja".

**Prasyarat:** P2 selesai (4 `recon.json` dengan `sample` terisi).
**Read-set:** `STATE.md`, file ini, `docs/SCHEMA.md`, `docs/DECISIONS.md` (D4–D7, D12),
`recon/*.json` (bagian `schema` + `sample` saja).
**Budget:** sedang.

---

## Langkah

### 1. Cocokkan `docs/SCHEMA.md` §2b dengan kenyataan recon
Tabel field per target di SCHEMA masih **draf**. Bandingkan dengan `schema` + `sample`
di tiap `recon.json`. Perbaiki yang meleset. Kunci hasilnya sebagai **D17**
(pindahkan dari daftar 🔓 ke terkunci di `docs/DECISIONS.md`).

Untuk tiap field, putuskan **eksplisit**: `required` atau opsional.
Aturannya: `required` berarti "kalau kosong, datanya cacat dan alarm boleh berbunyi".
Menandai terlalu banyak field `required` menghasilkan alarm palsu tiap hari — dan alarm
palsu adalah cara tercepat membuat klien berhenti membaca peringatan.

### 2. `src/contracts.py` — satu sumber kebenaran
```python
# bentuk, bukan salinan final
FIELD = namedtuple("FIELD", "name type required description source_hint")

CONTRACTS = {
  "books": {
    "key": "upc",
    "fields": [
      FIELD("upc", str, True, "Kode unik buku dari halaman detail", "table.product_page td"),
      FIELD("price_incl_tax", float, True, "Harga termasuk pajak, dalam GBP", "p.price_color"),
      ...
    ],
  },
  ...
}
VOLATILE = {"fetched_at", "run_id", "scrape_duration_ms"}   # D7: tidak ikut di-hash
```

`description` dan `source_hint` bukan hiasan — keduanya menjadi isi **Sheet 5 "Kamus Data"**
di laporan mingguan (P11) dan `docs/DATA_DICTIONARY.md` (P6). Ditulis sekali di sini,
tidak pernah basi.

### 3. `src/validate.py`
Fungsi yang wajib ada:

| Fungsi | Tugas |
|---|---|
| `validate_record(rec, target)` | key asing → `SCHEMA_UNKNOWN_FIELD`; tipe salah → tolak; `missing_fields` tanpa `missing_reason` → tolak (D6) |
| `content_hash(fields)` | sha256 atas JSON kanonik, `VOLATILE` dibuang (D7) |
| `make_record_id(target, key_value)` | `"{target}:{key}:{nilai}"` (D7) |
| `field_completeness(records, target)` | pecahan 0–1 per field, dipakai `run.json` dan alarm |
| `validate_run(path)` | CLI: validasi seluruh `records.jsonl`, exit ≠ 0 kalau ada pelanggaran |

### 4. Uji kontrak dengan `sample` dari recon
Ambil 3 record `sample` tiap target, jalankan lewat `validate_record`. Semuanya harus lulus.
Kalau ada yang gagal, **kontraknya yang salah, bukan sampelnya** — sampel diambil dari
halaman nyata. Perbaiki kontrak, jangan longgarkan validator.

### 5. Uji `content_hash` stabil
```python
# record sama, fetched_at berbeda → hash WAJIB sama (D7)
# satu nilai field berubah   → hash WAJIB berbeda
```
Ini uji terpenting di fase ini. Kalau `content_hash` ikut berubah karena `fetched_at`,
seluruh mesin diff di P8 akan melaporkan 100% record berubah setiap hari.

### 6. Unit test
`src/test_contracts.py` — minimal 6 test: hash stabil, hash berubah, key asing ditolak,
tipe salah ditolak, `missing_reason` wajib, `record_id` konsisten.
```bash
uv run python -m unittest discover -s src -p 'test_*.py' -v
```
(Mesin ini tidak punya `pytest` — fakta terverifikasi dari project 1. Pakai `unittest`.)

---

## Output fase
- `docs/SCHEMA.md` versi terkunci (hapus label "draf")
- `src/contracts.py`, `src/validate.py`, `src/test_contracts.py`
- D17 terkunci di `docs/DECISIONS.md`

## Definition of Done
- [x] Tabel field 4 target di `docs/SCHEMA.md` §2b cocok dengan `recon/*.json`; label "draf" hilang
- [x] D17 dipindahkan dari 🔓 ke terkunci
- [x] 12 record `sample` (3 × 4 target) lulus `validate_record` tanpa pengecualian
- [x] Uji hash: `fetched_at` berubah → hash sama; nilai field berubah → hash beda
- [x] `python -m unittest discover -s src` → ≥ 6 test, semua lulus, output ditempel
- [x] Tiap field punya `description` + `source_hint` yang terisi (bahan kamus data)
- [x] **Commit + push berhasil** (D19)

### Bukti 2026-08-27

```text
$ uv run --no-sync python -m unittest discover -s src -p 'test_*.py' -v
Ran 11 tests in 0.001s
OK

$ uv run --no-sync python -c '<validasi 12 sampel recon>'
samples=12/12 valid

$ uv run --no-sync python -c '<hitung metadata kontrak>'
contracts=4 fields=31 required=27 descriptions=31 source_hints=31

$ uv run --no-sync python -m py_compile src/contracts.py src/validate.py src/test_contracts.py
exit 0
```

## Metrik selesai
`4 kontrak terkunci · N field (M required) · 12/12 sampel lulus · X/X test lulus`

## Jebakan
- Jangan menandai semua field `required`. Setiap `required` adalah janji 98% kelengkapan
  yang harus ditepati tiap hari (A2).
- Jangan lupa `VOLATILE` (D7). Ini kesalahan yang paling mahal di project ini karena
  akibatnya baru terlihat di P8, jauh setelah kodenya ditulis.
- Jangan menulis `description` asal-asalan. Ia langsung mendarat di laporan klien.
- Jangan pakai `pytest` — tidak terpasang di mesin ini.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P3 ✅, jumlah field per target, jumlah test.
3. `git add -A && git commit -m "P03: kontrak data terkunci + validator" && git push`
