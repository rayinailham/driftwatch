# P7 — Penjadwalan

**Tujuan sesi:** pipeline jalan sendiri tiap pagi tanpa disentuh.
**Fase ini mendesak** — begitu timer nyala, jam 3 hari untuk P9 mulai berdetak sendiri
sementara fase lain dikerjakan.

**Prasyarat:** P6 selesai.
**Read-set:** `STATE.md`, file ini, `docs/DECISIONS.md` (D3, D9, D11), `docs/TOOLS.md` §8.
**Budget:** ringan.

---

## Langkah

### 1. `scripts/daily_run.sh`
Satu skrip yang menjalankan urutan harian penuh dan mengembalikan exit code yang benar:

```bash
#!/usr/bin/env bash
set -uo pipefail            # BUKAN -e: satu target gagal tidak boleh membatalkan sisanya
cd /home/rayin/Projects/Testing/driftwatch
FAIL=0
for T in driftlab books quotes seo; do
  uv run --no-sync python src/scrape.py --target "$T" --resume || FAIL=1
  uv run --no-sync python src/validate.py --target "$T" --today || FAIL=1
  uv run --no-sync python src/diff.py   --target "$T" --today || FAIL=1   # ada setelah P8
  uv run --no-sync python src/alarm.py  --target "$T" --today || FAIL=1   # ada setelah P8
  uv run --no-sync python src/report.py --target "$T" --today || true     # ada setelah P11
done
exit $FAIL
```

Dua keputusan penting di sini:
- **`set -uo pipefail`, bukan `-e`.** Kalau `books` gagal, `quotes` tetap harus dipanen.
  Kegagalan dikumpulkan lalu dilaporkan sekali di akhir.
- **Langkah yang belum ada (P8, P11) ditulis sekarang** dan dijaga agar tidak menggagalkan
  skrip sebelum file-nya lahir. Jangan mengedit skrip ini tiga kali di tiga fase berbeda.

Sertakan `flock` supaya dua run tidak pernah tumpang tindih:
```bash
exec 9>/tmp/driftwatch.lock && flock -n 9 || { echo "run lain masih jalan"; exit 0; }
```

### 2. Unit systemd (D9)
`deploy/driftwatch.service`:
```ini
[Unit]
Description=DriftWatch daily harvest
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/rayin/Projects/Testing/driftwatch
ExecStart=/usr/bin/env bash scripts/daily_run.sh
```

`deploy/driftwatch.timer`:
```ini
[Unit]
Description=DriftWatch daily 09:00 WIB

[Timer]
OnCalendar=*-*-* 09:00:00 Asia/Jakarta
RandomizedDelaySec=300
Persistent=true

[Install]
WantedBy=timers.target
```

`RandomizedDelaySec=300` adalah kesopanan: menghantam server tepat pukul 09:00:00 setiap
hari adalah pola yang mudah dikenali sebagai bot dan mudah diblokir.
`Persistent=true` adalah alasan klaim "tahan mati listrik" boleh diucapkan.

### 3. Pasang & uji

> 🚨 **`~/.config/systemd/user/` juga rumah `9router.service`** (9Router local AI proxy,
> port 20128). Sepanjang fase ini: sebut nama unit secara **eksplisit**, jangan pernah
> wildcard. `systemctl --user stop '*'`, `reset-failed` massal, atau membersihkan isi
> direktori itu akan ikut membunuhnya — dan karena ia proxy AI, sesi agent bisa mati
> bersamanya dengan gejala yang tampak acak. `daemon-reload` aman.

```bash
mkdir -p ~/.config/systemd/user
cp deploy/driftwatch.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now driftwatch.timer
systemctl --user list-timers driftwatch.timer        # ada NEXT
systemctl --user is-active 9router.service           # WAJIB tetap `active` (D22-A)
systemctl --user start driftwatch.service            # picu manual sekali
systemctl --user status driftwatch.service
journalctl --user -u driftwatch.service --no-pager | tail -30
```

Kalau `systemctl --user` tidak ada di mesin ini: jatuh ke cron, **catat penurunan itu di
`STATE.md`** beserta konsekuensinya (kehilangan `Persistent=true`, log tidak terstruktur).

### 4. Rotasi log (D11)
`scripts/prune.sh`: hapus `run.log` > 30 hari, pertahankan `run.json` dan `diff.json`
selamanya (kecil, dan merupakan bukti historis). Dipanggil dari `make prune`, manual —
jangan otomatis menghapus di dalam `daily_run.sh`.

### 5. Mulai hitungan soak
Catat di `STATE.md`: **`soak_dibuka: <tanggal>`**. P9 baru boleh ditutup kalau sudah ada
**3 tanggal berturut** yang datanya lahir tanpa intervensi manual.

---

## Output fase
- `scripts/daily_run.sh`, `scripts/prune.sh`
- `deploy/driftwatch.service`, `deploy/driftwatch.timer`
- timer aktif, satu run manual sukses
- `soak_dibuka` tercatat di `STATE.md`

## Definition of Done
- [ ] `systemctl --user list-timers driftwatch.timer` menunjukkan `NEXT` yang masuk akal (output ditempel)
- [ ] `systemctl --user start driftwatch.service` sukses; `journalctl` menunjukkan 4 target diproses
- [ ] Folder `data/<target>/<hari ini>/` lahir untuk keempat target dari run terjadwal itu
- [ ] `flock` terbukti: jalankan dua kali bersamaan → yang kedua keluar rapi, tidak menabrak
- [ ] Satu target sengaja digagalkan → target lain tetap jalan, `daily_run.sh` exit ≠ 0
- [ ] `scripts/prune.sh` ada dan dry-run-nya benar
- [ ] `soak_dibuka: <tanggal>` tertulis di `STATE.md`
- [ ] `systemctl --user is-active 9router.service` → **`active`** (dicek sesudah semua
      pemasangan; buktinya ditempel) — D22-A
- [ ] **Commit + push berhasil** (D19)

## Metrik selesai
`timer aktif · NEXT = <waktu> · 1 run terjadwal sukses · soak dibuka <tanggal>`

## Jebakan
- **Jangan pakai `set -e`** di `daily_run.sh`. Satu target gagal akan membunuh sisanya
  dan menghasilkan `RUN_MISSING` palsu untuk tiga target yang sebenarnya sehat.
- Jangan lupa `uv run --no-sync` di unit systemd. `uv run` biasa bisa mencoba sync jaringan
  saat jaringan belum siap dan menggagalkan run.
- Jangan pasang timer sebelum P6 punya baseline. Timer tanpa baseline menghasilkan
  alarm tanpa arti.
- Jangan menyetel `OnCalendar` ke tengah malam. Kalau ada masalah, kamu ingin bangun dan
  melihat alarmnya, bukan menemukannya tiga hari kemudian.
- **Jangan pernah pakai wildcard `systemctl --user`.** `9router.service` ada di direktori
  yang sama dan mematikannya bisa memutus sesi agent sendiri (D22-A).
- **Jangan sentuh timer lagi setelah fase ini.** Menyentuhnya membatalkan klaim
  "3 hari tanpa disentuh" dan hitungan P9 mulai dari nol.

## Sebelum menutup sesi
1. Centang DoD dengan output nyata.
2. Update `STATE.md`: P7 ✅, `soak_dibuka`, jadwal berikutnya.
3. `git add -A && git commit -m "P07: systemd timer harian + daily_run.sh" && git push`
