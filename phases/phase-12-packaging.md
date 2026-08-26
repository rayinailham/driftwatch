# P12 — Visual, Packaging & Gladi Bersih

**Tujuan sesi:** orang lain bisa menjalankan seluruh pipeline dari nol dengan satu perintah,
dan calon klien bisa yakin dalam 60 detik tanpa membaca satu baris kode pun.

**Prasyarat:** P9, P10, P11 selesai.
**Read-set:** `STATE.md`, file ini, `docs/ACCEPTANCE.md`, `docs/ETHICS.md`,
`docs/DECISIONS.md` (D10, D19, D20).
**Budget:** ringan tapi panjang.

---

## Langkah

### 1. `Makefile` (D10)
```
make setup      uv sync + siapkan fixture
make lab-up     nyalakan driftlab di :8100
make oracles    11 skenario drift → wajib 11/11
make harvest    panen 4 target
make diff       diff + alarm
make report     digest harian + REPORT.xlsx mingguan
make publish    perbarui halaman demo
make test       unit test
make audit      pemindaian kebocoran rahasia
make prune      rotasi log > 30 hari
make all        setup → lab-up → harvest → diff → report → publish
make lab-down   matikan fixture
```
Wajib memuat `.NOTPARALLEL:` — `MAKEFLAGS` di shell user memuat `-j16` dan urutan
pipeline harus tetap benar (fakta terverifikasi dari project 1).

### 2. `scripts/secret_audit.py` → `make audit`
Memindai seluruh repo untuk nilai dari `.env`, pola kunci API, dan file sensitif yang
ter-track git. Keluaran: daftar nilai kelas RAHASIA dan berapa berkas memuatnya —
wajib **0**. Membedakan kelas *rahasia* (kunci, password) dari kelas *identitas*
(nama akun demo lokal) dan melaporkan keduanya secara terpisah.

Setelah ada, `make audit` menjadi gerbang wajib sebelum setiap commit (D19).

### 3. Video 60 detik — deliverable paling meyakinkan
Satu take, tanpa suara, dengan teks di layar:

```
0:00–0:10  scraper jalan, log mengalir, counter naik
0:10–0:15  DIBUNUH PAKSA (kill -9)          ← teks besar di layar
0:15–0:25  dijalankan ulang dengan --resume
0:25–0:35  lanjut dari posisi terakhir — TIDAK mengulang dari nol
           tampilkan angka: sebelum N1 → sesudah N2, duplikat 0
0:35–0:45  selector sengaja dirusak (DO-04)
0:45–0:55  ALARM berbunyi + isi notifikasi ke klien
0:55–1:00  halaman demo dengan data hari ini
```

```bash
wf-recorder -o eDP-1 -f /tmp/raw.mp4     # satu monitor, tanpa audio
ffmpeg -i /tmp/raw.mp4 -vf "scale=1920:1080" -c:v libx264 -crf 23 assets/v1_resume_demo.mp4
```
Sebelum merekam: pastikan layar tidak menampilkan kredensial, email, atau jendela kerja user.

### 4. Visual pendukung
| Berkas | Isi |
|---|---|
| `assets/v2_architecture.png` | diagram alur `docs/PIPELINE.md` §1, via PlantUML `localhost:20080` |
| `assets/v3_diff_timeline.png` | grafik 3+ hari: baru/berubah/hilang per hari |
| `assets/v4_alarm_matrix.png` | 11 oracle × alarm yang terpicu, hijau/merah |
| `assets/v5_tier_drop.png` | "sebelum: N request browser · sesudah: M request httpx" (A10) |
| `assets/v6_case_study.pdf` | satu halaman A4: masalah, pendekatan, hasil, angka |

### 5. README publik
Struktur yang dikunci:
1. Satu kalimat pitch
2. Apa yang dilakukan (5 poin)
3. **Etika scraping** — disalin dari `docs/ETHICS.md` §1 dan §4. **Klien serius membaca
   bagian ini**; letakkan tinggi, bukan di footer.
4. Cara menjalankan (`make all`)
5. Bentuk data + tautan kamus data
6. Bukti: video, angka soak, 11/11 oracle
7. Batasan yang jujur — apa yang project ini **tidak** lakukan (`docs/ACCEPTANCE.md` §D)

Poin 7 terasa berlawanan dengan naluri menjual, dan justru itu yang membuat poin 1–6 dipercaya.

### 6. Gladi bersih salinan bersih (A11)
```bash
rsync -a --exclude data --exclude reports --exclude .venv --exclude .git \
  ./ /tmp/driftwatch-clean/
cd /tmp/driftwatch-clean && cp .env.example .env
# isi kunci seadanya; pakai LAB_PORT berbeda supaya tidak menabrak port kerja user
LAB_PORT=8101 make all
```
Harus exit 0 dan menghasilkan dataset + laporan yang sebanding. Kalau gagal, itu bug
paling berharga di seluruh project — ia persis yang akan dialami klien.

### 7. Audit akhir & latihan pitch
- `make audit` → 0 kebocoran
- centang A1–A12 di `docs/ACCEPTANCE.md` dengan bukti perintah
- naskah pitch 60 detik di `docs/PITCH.md`, **diucapkan keras sekali** dan diukur waktunya
- 🔓 D20: tanyakan ke user apakah repo dijadikan publik. **Jangan lakukan sendiri.**

---

## Output fase
- `Makefile`, `scripts/secret_audit.py`
- `assets/v1..v6`
- `README.md` publik, `docs/PITCH.md`
- `docs/ACCEPTANCE.md` A1–A12 tercentang

## Definition of Done
- [ ] `make all` di salinan bersih → **exit 0**, durasi dicatat (A11)
- [ ] `make audit` → **0 kebocoran** (A12); `.env`/`data`/`reports` tidak ter-track
- [ ] `make oracles` di salinan bersih → 11/11
- [ ] Video 60 dtk ada, 1920×1080, memuat kill→resume **dan** alarm berbunyi
- [ ] 5 visual pendukung lahir
- [ ] README publik memuat bagian etika + batasan jujur
- [ ] A1–A12 di `docs/ACCEPTANCE.md` tercentang **dengan output perintah**, bukan klaim
- [ ] `docs/PITCH.md` ada dan sudah diucapkan sekali (durasi dicatat)
- [ ] Pertanyaan D20 (repo publik) diajukan ke user; keputusannya dicatat
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`make all exit 0 dalam X menit · 11/11 oracle · 0 kebocoran · A1–A12 ✅ · video Y dtk`

## Jebakan
- Jangan pakai `just` — tidak terpasang di mesin ini (D10).
- Jangan lupa `.NOTPARALLEL:`. Tanpa itu `-j16` di shell user akan mengacak urutan pipeline.
- Jangan menguji salinan bersih di port yang sama (`8100`). Pakai `8101`.
- Jangan merekam desktop penuh. Satu monitor, dan periksa layar dulu.
- Jangan menjadikan repo publik sendiri. 🔓 D20 butuh izin eksplisit user.
- Jangan mencentang acceptance tanpa menempelkan output perintahnya (D15).

## Sebelum menutup sesi
1. Centang DoD + A1–A12 dengan output nyata.
2. Update `STATE.md`: **PROJECT COMPLETE**, tabel metrik final, sisa catatan untuk user.
3. `git add -A && git commit -m "P12: packaging, visual, gladi bersih — project complete" && git push`
