# DriftWatch — Batas Etika & Legal

Dokumen ini menang atas kenyamanan teknis. Kalau sebuah pendekatan lebih cepat tapi
melanggar file ini, pendekatan itu dibuang — tanpa diskusi ulang tiap sesi.

Bagian dari dokumen ini disalin apa adanya ke README publik (P12), karena **klien serius
membaca bagian ini** dan itu justru yang membedakan penawaran ini dari freelancer murahan.

---

## 1. Aturan yang selalu berlaku

1. **Cek `robots.txt` sebelum request kedua.** Hasilnya dicatat di `recon.json`.
2. **Hormati `Crawl-delay`.** Kalau tidak disebut, pakai 1,0 detik per request per host.
   Tidak pernah lebih cepat dari itu untuk host publik.
3. **User-Agent jujur + kontak.** `DriftWatch/1.0 (+mailto:rayinailham9@gmail.com)`.
   Dilarang menyamar sebagai browser untuk mengelabui target.
4. **Concurrency maksimum 3** untuk host publik.
5. **Ambil metadata, bukan karya.** Untuk situs pihak ketiga: judul, H1, meta description,
   tanggal, jumlah kata, jumlah link, URL. Bukan isi artikel, bukan gambar, bukan HTML penuh.
6. **Tidak menembus apa pun.** Tidak ada captcha solver, bypass Cloudflare, stealth
   fingerprinting, atau rotasi proxy untuk menghindari rate limit.
7. **Tidak login ke akun milik orang lain.** Kalau klien minta scraping di balik login,
   minta konfirmasi tertulis bahwa mereka berwenang atas akun dan target itu.
8. **Berhenti kalau diminta berhenti.** HTTP 429 berulang, atau blokir IP, diperlakukan
   sebagai penolakan — pipeline berhenti dan melapor, bukan mencari jalan lain.

## 2. Gerbang pemilihan target `seo` (P1)

Sebuah situs hanya boleh jadi target kalau **semua** kotak ini tercentang. Satu saja gagal →
situs dibuang, cari kandidat lain, catat alasannya di `docs/TARGETS.md`.

- [ ] `robots.txt` **tidak** melarang path yang akan diambil (cek `User-agent: *` dan `Disallow`)
- [ ] `robots.txt` tidak memuat `Crawl-delay` yang lebih besar dari yang sanggup dipenuhi
- [ ] `sitemap.xml` tersedia (kalau tidak ada, crawl harus dibatasi manual dan dicatat)
- [ ] Situs bukan milik kompetitor pihak ketiga yang bisa dirugikan oleh publikasi portofolio
- [ ] Tidak ada login wall, captcha, atau Cloudflare challenge di path target
- [ ] Yang diambil murni metadata teknis SEO, bukan isi karya
- [ ] Volume total ≤ 500 URL — cukup untuk demo, tidak membebani situs orang

Kandidat awal yang layak dievaluasi (urutan bebas, cek robots-nya sendiri, jangan percaya
daftar ini): situs dokumentasi open-source, blog proyek open-source, atau situs yang
menyediakan API publik resmi. **Jangan** memakai situs berita komersial, toko online nyata,
atau situs yang ToS-nya menyebut larangan automated access.

## 3. Halaman demo publik

- Hanya metadata + tautan ke sumber asli (D13).
- Ada baris atribusi: nama situs sumber + tautan.
- Ada catatan: data dikumpulkan dengan menghormati `robots.txt`, 1 request/detik.
- Kalau pemilik situs meminta dihapus, dihapus. Catat kontak tanggapannya di README.

## 4. Kalimat yang dipakai ke klien

Kalimat ini dipakai apa adanya saat menawar job scraping. Ia menyaring klien yang akan
jadi masalah, dan meyakinkan klien yang serius:

> "Sebelum menulis kode, saya cek `robots.txt` dan ToS target. Kalau target melarang
> automated access, saya akan bilang di depan dan menawarkan jalur lain (API resmi,
> data partner, atau sumber alternatif) — bukan diam-diam menembusnya. Untuk situs yang
> boleh, saya jalan 1 request/detik dengan User-Agent yang bisa Anda tunjukkan ke mereka
> kalau ditanya. Itu yang membuat pipeline Anda tidak diblokir bulan depan."

## 5. Yang tidak dikerjakan project ini

- Menembus captcha / Cloudflare / WAF
- Scraping situs yang ToS-nya melarang
- Redistribusi konten berhak cipta
- Scraping data pribadi (nama, email, nomor telepon perorangan)
- Membangun daftar lead dari profil orang tanpa dasar hukum yang jelas
