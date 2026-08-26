# DriftWatch — Laporan ke Klien

Bagian ini sama pentingnya dengan kodenya. Klien tidak membaca `records.jsonl`.
Yang mereka nilai adalah: **apakah saya tahu keadaan data saya hari ini tanpa harus bertanya?**

---

## 1. Irama komunikasi

| Kapan | Bentuk | Panjang | Dikirim otomatis? |
|---|---|---|---|
| Harian, 09:30 WIB | `daily.md` — digest 1 layar | ≤ 15 baris | ya (P11) |
| Saat alarm `critical` | notifikasi terpisah, langsung | 4 baris | ya, seketika |
| Mingguan, Senin | `REPORT.xlsx` + 3 kalimat pengantar | 5 sheet | manual, dikirim manusia |
| Saat handover | README + video + akses repo | sekali | manual |

**Aturan yang tidak dilanggar:** hari sunyi tetap dilaporkan. Digest "0 baru, 0 berubah,
0 hilang, pipeline sehat" bukan laporan kosong — ia bukti pipeline masih hidup. Klien yang
tiga hari tidak menerima apa pun akan berasumsi buruk, dan mereka benar.

---

## 2. Digest harian — `reports/<target>/<date>/daily.md`

Templat yang dikunci. Digenerate oleh `src/report.py` (P11).

```markdown
# books.toscrape.com — 28 Agustus 2026

**Status: SEHAT** ✅

| | Hari ini | Kemarin |
|---|---|---|
| Total data | 1.000 | 988 |
| Baru | 12 | 3 |
| Berubah | 4 | 0 |
| Hilang | 1 | 0 |
| Kelengkapan kolom | 99,4% | 99,4% |

**Yang baru (12)** — 3 contoh teratas:
- "The Silent Patient" — Rp 51.770 — Fiction — [lihat](https://…)
- …

**Yang berubah (4)**:
- "A Light in the Attic": harga 51,77 → 48,50
- …

**Yang hilang (1)**:
- "Old Title" — terakhir terlihat 27 Agustus

**Catatan pipeline:** run selesai 09:18, 18 menit 41 detik, tanpa error.
Jeda antar request rata-rata 1,00 detik (sesuai kesepakatan 1 request/detik).
```

Aturan penyusunannya:

1. **Status dulu, angka kemudian.** Baris pertama menjawab "perlu saya khawatir tidak?"
2. **Maksimal 3 contoh per kategori.** Sisanya ada di file data. Digest bukan dump.
3. **Nol jargon.** `src/report.py` wajib punya validator yang menolak kata:
   `selector`, `selectolax`, `tenacity`, `XPath`, `stacktrace`, `traceback`, `regex`,
   `checkpoint`, `SQLite`, `exception`. Kalau salah satu muncul, report gagal dibangun.
   (Pola ini terbukti di project 1 — `qa/report.py` menolak jargon dan hasilnya `0 jargon`.)
4. **Nilai perubahan ditampilkan sebagai "dari → ke"**, bukan diff teknis.
5. **Baris rate limit selalu ada.** Itu yang membuat klien tenang saat legal mereka bertanya.

---

## 3. Laporan mingguan — `REPORT.xlsx`

Lima sheet. Urutannya sengaja: yang paling tidak teknis di depan.

| # | Sheet | Isi | Untuk siapa |
|---|---|---|---|
| 1 | **Ringkasan** | 7 hari: total, baru, berubah, hilang, uptime pipeline, jumlah alarm | pengambil keputusan |
| 2 | **Perubahan** | tiap record yang berubah: tanggal, nama, kolom, dari, ke, tautan | analis |
| 3 | **Data Baru** | record baru minggu ini, kolom penuh | analis |
| 4 | **Kesehatan Pipeline** | per hari: jam run, durasi, jumlah request, error, kelengkapan tiap kolom, alarm | teknis klien |
| 5 | **Kamus Data** | tiap kolom: nama, tipe, contoh, sumbernya di halaman, wajib/opsional, catatan | siapa pun yang mewarisi dataset ini |

Sheet 5 adalah yang paling sering dilupakan pesaing dan paling sering diminta klien tiga
bulan kemudian. Ia digenerate dari `src/contracts.py`, jadi tidak pernah basi.

Pewarnaan sel di sheet 1 & 4: hijau = sehat, kuning = `warning`, merah = `critical`.
Tidak ada warna lain. Tidak ada grafik dekoratif.

---

## 4. Notifikasi alarm — dikirim seketika, bukan menunggu digest

Templat 4 baris, dipakai apa adanya:

```
[DriftWatch] books.toscrape.com — PERLU PERHATIAN

Hanya 412 dari biasanya 988 data yang berhasil dikumpulkan pagi ini.
Kemungkinan besar situs sumber mengubah tata letak halamannya.
Saya sudah mulai memeriksa; perkiraan perbaikan: hari ini. Data kemarin tetap utuh dan aman.
```

Empat hal yang selalu ada, berurutan: **apa yang terjadi · seberapa parah · apa penyebab
dugaannya · apa yang sedang saya lakukan.** Yang terakhir itu yang membedakan alarm otomatis
dari alarm yang membuat klien panik.

Yang **tidak** boleh masuk notifikasi klien: stack trace, nama selector, nama file kode,
nomor baris, nama library. Semua itu ada di `reports/alerts.jsonl` field `likely_cause`
untuk dibaca developer.

---

## 5. Yang dikirim saat handover (P12)

1. **Repo** — kode + README yang memuat bagian etika (klien serius membaca ini)
2. **Dataset** — CSV + JSONL + kamus data (D12)
3. **`REPORT.xlsx`** contoh
4. **Video 60 detik** — scraper diputus paksa → dijalankan lagi → lanjut dari posisi terakhir
5. **Instruksi jalan sendiri** — cara pasang timer di mesin mereka, satu halaman
6. **Kesepakatan pemeliharaan** — kalimatnya di §6

---

## 6. Kalimat penawaran & pemeliharaan

Untuk penawaran (job 22 memakai kata "clean & repeatable" — mereka pernah dikecewakan
scraper rapuh, jadi jawab kekhawatiran itu langsung):

> "Saya tidak mengirim satu file `scrape.py`. Yang Anda terima adalah pipeline yang
> jalan sendiri tiap pagi, menyimpan snapshot per tanggal, mengirim ringkasan
> 'apa yang baru, apa yang berubah, apa yang hilang' setiap hari, dan mengirim peringatan
> ke Anda **di hari yang sama** kalau situs targetnya berubah struktur — bukan tiga minggu
> kemudian saat Anda sadar sendiri datanya kosong. Bisa diputus di tengah jalan dan
> dilanjutkan tanpa mengulang. Sebelum menulis kode, saya cek `robots.txt` target dan
> jalan 1 request per detik dengan User-Agent yang bisa Anda tunjukkan ke mereka."

Untuk pemeliharaan bulanan:

> "Situs berubah — itu bukan kalau, tapi kapan. Retainer bulanan menutup: perbaikan
> ketika struktur situs berubah, penambahan kolom baru, dan pemantauan bahwa pipeline
> benar-benar jalan tiap hari. Tanpa itu, pipeline apa pun akan mati dalam hitungan bulan,
> dan Anda baru tahu saat datanya sudah telanjur kosong berminggu-minggu."

---

## 7. Contoh laporan yang masuk repo

Untuk portofolio, satu contoh laporan **yang sudah disanitasi** disimpan di
`assets/sample_daily.md` dan `assets/sample_REPORT.xlsx`. Sanitasi berarti: tanpa path
lokal, tanpa nama host internal, tanpa email klien, tanpa kunci API.
