# DriftWatch — naskah pitch 60 detik

Dipakai saat menawar job scraping. Satu tarikan, tanpa slide. Angka di dalamnya semuanya
punya perintah pembuktinya di `docs/ACCEPTANCE.md`.

---

## Naskah

> Kebanyakan scraper tidak rusak dengan berisik. Ia rusak diam-diam — satu class CSS berganti
> nama, satu kolom jadi kosong — dan datanya tetap mengalir sampai Anda yang menemukan
> laporan tiga minggu terakhir salah.
>
> DriftWatch memanen empat situs tiap pagi, seribu tiga ratus dua puluh tiga baris,
> lalu membandingkannya dengan panen kemarin. Ia tahu mana yang baru, berubah, dan hilang —
> dan berteriak duluan lewat sepuluh kode alarm dengan ambang tertulis.
>
> Alarmnya bukan klaim. Saya tanam sebelas kerusakan di situs uji, jalankan pipeline
> yang sama di atasnya: sebelas dari sebelas terdeteksi, nol false positive.
>
> Dibunuh di tengah jalan, ia lanjut dari checkpoint terakhir tanpa mengulang.
> Tiga hari berturut ia jalan sendiri tanpa saya sentuh.
>
> Dan sebelum menulis kode, saya cek `robots.txt` dan ToS target. Kalau melarang, saya bilang
> di depan. Itu yang membuat pipeline Anda tidak diblokir bulan depan.

---

## Pengukuran durasi

**138 kata.** Pada tempo presentasi bahasa Indonesia yang wajar (140–155 kata/menit),
naskah ini jatuh di **53–59 detik** — pas untuk slot 60 detik, dengan sedikit ruang jeda.

```console
$ sed -n '/^## Naskah/,/^---$/p' docs/PITCH.md | sed 's/^> \?//' \
    | grep -v '^##\|^---\|^$' | wc -w
138
```

**Catatan jujur:** DoD P12 meminta naskah ini "diucapkan keras sekali dan diukur waktunya".
Yang bisa diukur di sesi ini hanya panjangnya, bukan pengucapannya — agent tidak bisa
membunyikan suara. Angka 53–59 detik di atas adalah **estimasi dari jumlah kata**, bukan
stopwatch. Baca sekali dengan keras sebelum dipakai ke klien sungguhan, lalu ganti angka
di bagian ini dengan hasil stopwatch yang sebenarnya.

---

## Kalau ditanya lanjutan

| Pertanyaan | Jawaban satu kalimat | Bukti |
|---|---|---|
| "Berapa lama dipasang di mesin saya?" | Satu perintah, `make all`, 18 menit dari nol — tanpa Docker, tanpa database. | `docs/ACCEPTANCE.md` A11 |
| "Kalau situsnya berubah total?" | Alarm `ZERO_RECORDS` + `RECORD_COUNT_DROP` berbunyi hari itu juga, laporan hariannya ikut berubah jadi PERLU PERHATIAN. | `assets/v4_alarm_matrix.png` |
| "Kalau listrik mati semalam?" | Timer `Persistent=true` mengejar run yang terlewat saat mesin menyala; watchdog H+1 berteriak kalau tidak. | `docs/DECISIONS.md` D9, D23 |
| "Datanya bentuknya apa?" | JSONL sebagai sumber utama, CSV siap Excel, plus `REPORT.xlsx` 5 sheet tiap minggu. | `docs/DATA_DICTIONARY.md` |
| "Aman secara hukum?" | Metadata saja, `robots.txt` dihormati, User-Agent jujur berisi kontak yang bisa Anda tunjukkan ke pemilik situs. | `docs/ETHICS.md` |
| "Berapa biaya AI-nya?" | Nol. Ringkasan AI opsional dan mati secara default; halaman tetap terbit lengkap tanpanya. | `web/data.json` |
