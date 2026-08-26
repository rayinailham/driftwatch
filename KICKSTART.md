# DriftWatch — Prompt Kickstart (universal)

Satu prompt, dipakai kapan saja, sesi keberapa pun, dari fase 0 sampai selesai.
Agent menentukan sendiri posisi progres dari `STATE.md`. **Tidak perlu diedit.**

Kirim isi blok di bawah ini apa adanya, berulang kali, sampai `STATE.md` berbunyi
`PROJECT COMPLETE`.

---

## Prompt

```
Project: DriftWatch — pipeline data: recon → scraper → dataset → monitoring harian.
Root: /home/rayin/Projects/Testing/driftwatch

LANGKAH 1 — ORIENTASI (lakukan ini dulu, sebelum apa pun):

1. Baca berurutan: driftwatch/AGENTS.md, lalu ../AGENTS.md (aturan Arch — wajib),
   lalu driftwatch/STATE.md, lalu driftwatch/docs/DECISIONS.md (keputusan terkunci —
   jangan dinegosiasi ulang).

2. Cocokkan klaim dengan kenyataan disk:
     ls -R driftwatch/src driftwatch/scripts driftwatch/recon 2>/dev/null
     ls driftwatch/data driftwatch/reports 2>/dev/null | head -20
     git -C driftwatch log --oneline | head -15
   Kalau STATE.md berbeda dengan disk, DISK yang benar. Perbaiki STATE.md sebelum lanjut.
   Kalau STATE.md bilang sebuah fase ✅ tapi tidak ada commit untuk fase itu, fase itu
   BELUM selesai (D19) — turunkan statusnya jadi 🟨.

3. Tentukan sendiri fase mana yang dikerjakan sesi ini, memakai aturan berikut:

     P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 ──► P9 (soak, jam dinding)
                                        │
                                        ├─► P8 ──► P11 ──► P12
                                        └─► P10 ─────────────┘

   - Ambil fase belum-selesai dengan nomor terkecil yang semua prasyaratnya sudah ✅.
   - Kalau ada fase bertanda 🟨 (jalan) atau 🟥 (blocked), selesaikan itu dulu.
   - P7 didahulukan begitu tersedia — ia membuka jam soak untuk P9.
   - P9 BUKAN sesi kerja. Kalau `soak_dibuka` di STATE.md belum berjarak 3 hari, atau
     belum ada 3 tanggal data berturut, LEWATI P9 dan ambil fase tersedia berikutnya
     (P8, P10, atau P11). Ini bukan kemunduran — memang begitu rancangannya.
   - P11 tidak boleh mulai sebelum P8 punya output. P12 butuh P9, P10, P11 selesai.

4. Buka HANYA file fase yang terpilih: driftwatch/phases/phase-NN-*.md
   Lalu buka file yang disebut di bagian "Read-set" fase itu. Tidak lebih.
   Kalau file fase bertentangan dengan docs/DECISIONS.md, docs/SCHEMA.md, atau
   docs/ETHICS.md: ketiganya menang, dan perbaiki file fase itu di sesi yang sama.

5. Sebelum mulai kerja, sebutkan ke saya dalam 3 baris: fase yang kamu pilih,
   alasannya, dan apa yang akan lahir di akhir sesi.

LANGKAH 2 — SIAPKAN (hanya kalau fase terpilih menyentuhnya):

   Fixture lokal (P1, P8, P12):
     bash driftwatch/scripts/lab_up.sh
     uv run --no-sync python driftwatch/scripts/drift_lab.py --verify   # wajib 11/11 (2/11 di P1)
     Container tidak auto-start. Kalau verify gagal, BERHENTI dan laporkan —
     fixture bergeser berarti angka recall alarm tidak sah.

   Browser (hanya P2, dan hanya kalau curl tidak cukup):
     bash /home/rayin/Projects/Testing/crosscheck/scripts/arch_provision.sh
     JANGAN `playwright install-deps`, `--with-deps`, `sudo`, atau `pacman`. Selalu gagal di Arch.

LANGKAH 3 — KERJAKAN:

Selesaikan fase itu sampai SEMUA "Definition of Done"-nya tercentang dengan
bukti nyata (output perintah yang ditempel), bukan klaim.

ATURAN HEMAT TOKEN (wajib):
- Jangan baca file fase selain yang terpilih.
- Jangan baca ../HARNESS.md, ../portfolio/, atau ../crosscheck/ — kutipan yang perlu
  sudah ada di file fase dan docs/.
- Jangan baca records.jsonl / diff.json mentah. Agregasi dengan jq / wc -l / sort | uniq -c.
- Jangan buka halaman fixture satu per satu. Cukup ls | wc -l + 1–2 sampel.
- MCP browser hanya untuk recon di P2. Pekerjaan berulang selalu pakai script.

ATURAN ETIKA (tidak bisa dinegosiasi — docs/ETHICS.md menang atas kenyamanan teknis):
- robots.txt dilanggar → BERHENTI dan laporkan. Jangan cari celah, jangan ganti UA.
- 1 request/detik per host publik, concurrency maks 3. Jangan dinaikkan.
- User-Agent jujur berisi kontak. Jangan menyamar sebagai browser.
- Tidak menembus captcha/Cloudflare/WAF. Tidak login ke akun orang lain.
- Dari situs pihak ketiga: metadata saja, bukan isi karya.
- Skenario mutasi drift HANYA dijalankan di fixture lokal, tidak pernah ke situs orang.

ATURAN KERJA:
- Kerjakan lewat Bash sebisa mungkin. Verifikasi tiap langkah, jangan asumsi.
- Patch kecil dan reversible. Jangan refactor yang tidak diminta.
- Jangan sentuh /home/rayin/infra/. Jangan restart container di luar `driftwatch-lab`.
- Jangan hapus revision browser lama di ~/.cache/ms-playwright.
- Kalau gagal, laporkan output error persis. Jangan diperhalus, jangan diklaim sukses.
- Kalau sebuah keputusan 🔓 di DECISIONS.md jatuh di fase ini, kunci sekarang dan tulis
  alasannya. Kecuali D20 (repo publik) — itu butuh izin eksplisit saya.

LANGKAH 4 — PENUTUP SESI (wajib, jangan dilewat):

1. Centang DoD di file fase (edit di tempat), tempel output perintahnya.
2. GERBANG COMMIT (D19) — fase BELUM ✅ sebelum tiga langkah ini berhasil:
     make audit          # atau cek manual sebelum P12: git status --short tidak boleh
                         # memuat .env, data/, reports/, auth/, *.db
     git add -A && git status --short
     git commit -m "PNN: <ringkas>"     # body memuat artefak + metrik selesai
     git push
   Remote: git@rayin-personal:rayinailham/driftwatch.git (akun PERSONAL, repo privat).
   Jangan pakai akun work. Kalau push gagal, fase tetap 🟨 dan alasannya dicatat.
   Satu fase = satu commit.
3. Update driftwatch/STATE.md:
   - tabel status fase (⬜ belum · 🟨 jalan · ✅ selesai · 🟥 blocked)
   - tanggal, fase aktif, fase berikutnya, soak_dibuka kalau sudah ada
   - artefak baru yang lahir
   - tabel metrik diisi ANGKA NYATA dari file hasil, bukan perkiraan
   - blocker / keputusan yang masih 🔓
   - jaga STATE.md tetap < 100 baris; buang catatan yang sudah tidak relevan
4. Laporkan ke saya: fase apa yang selesai, metrik selesainya, hash commit-nya,
   dan apa yang jadi fase berikutnya.

Selesaikan SATU fase saja per sesi. Jangan lanjut ke fase berikutnya, kecuali fase itu
bertanda "ringan" di PLAN.md dan fase sekarang sudah 100% selesai termasuk push-nya.
```

---

## Cara memakai

1. Buka sesi baru di `/home/rayin/Projects/Testing`.
2. Tempel blok prompt di atas apa adanya.
3. Agent akan menyebut fase yang dipilihnya dalam 3 baris — baca sebentar, lalu biarkan jalan.
4. Di akhir sesi ia melapor + sudah commit & push.
5. Sesi berikutnya: **tempel prompt yang sama persis**. Tidak ada yang perlu diubah.

## Catatan

- Fase pertama yang akan dipilih agent kalau `STATE.md` masih perawan: **P0 — Bootstrap**.
- **Memaksa fase tertentu:** tambahkan satu baris di akhir prompt:
  `Abaikan pemilihan otomatis, kerjakan fase P07.`
- **Sesi terputus di tengah fase:** prompt yang sama tetap dipakai — agent melihat 🟨 di
  `STATE.md` dan melanjutkan fase itu.
- **Setelah P7:** prompt yang sama akan otomatis melewati P9 selama soak belum matang, dan
  mengambil P8/P10/P11. Begitu 3 hari terkumpul, ia akan menutup P9 sendiri tanpa diminta.
- **Kalau agent mengklaim fase selesai tanpa commit:** prompt ini sudah menyuruhnya
  menurunkan status sendiri di langkah orientasi 2. Kalau tetap terjadi, itu bug perilaku —
  tunjukkan langkah 4 poin 2 kepadanya.
