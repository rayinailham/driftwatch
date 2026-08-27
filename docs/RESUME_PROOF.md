# Bukti Kill → Resume

**Tanggal uji:** 2026-08-27  
**Target:** `books`  
**Tujuan:** membuktikan proses yang mati paksa melanjutkan checkpoint tanpa menulis ulang record.

## Prosedur

```bash
D=$(date +%F)
rm -rf "data/books/$D"
timeout --signal=KILL 30s uv run python src/scrape.py --target books

N1=$(sqlite3 "data/books/$D/progress.db" "SELECT COUNT(*) FROM progress WHERE status='ok';")
L1=$(wc -l < "data/books/$D/records.jsonl")
printf 'sebelum resume: progress ok=%s  baris=%s\n' "$N1" "$L1"

uv run python src/scrape.py --target books --resume

N2=$(sqlite3 "data/books/$D/progress.db" "SELECT COUNT(*) FROM progress WHERE status='ok';")
L2=$(wc -l < "data/books/$D/records.jsonl")
DUP=$(jq -r .record_id "data/books/$D/records.jsonl" | sort | uniq -d | wc -l)
printf 'sesudah resume: progress ok=%s  baris=%s  duplikat=%s\n' "$N2" "$L2" "$DUP"
jq '{exit_code,resume_used,records_unique,rate_limit}' "data/books/$D/run.json"
```

Run pertama dihentikan paksa dengan SIGKILL setelah 30 detik. Log berhenti sesudah 12 record; tidak ada kesempatan shutdown teratur. Output checkpoint dan resume:

```text
sebelum resume: progress ok=12  baris=12
sesudah resume: progress ok=1050  baris=1000  duplikat=0
{
  "exit_code": 0,
  "resume_used": true,
  "records_unique": 1000,
  "rate_limit": {
    "delay_sec": 1.0,
    "concurrency": 1,
    "observed_min_gap_ms": 1000
  }
}
```

`progress ok=1050` terdiri dari 1.000 unit detail dan 50 unit halaman katalog. `records.jsonl` berisi tepat 1.000 `record_id` unik. Resume menambah 988 record, bukan mengulang 12 record awal.

## Bukti rate limit

Ambang D5 adalah `1.0 × 1000 × 0.9 = 900 ms`.

```text
observed_min_gap_ms=1000
ambang_ms=900
hasil=PASS
```

## Bukti HTTP 404 tidak di-retry

Satu request terkontrol diarahkan ke URL detail yang pasti tidak ada melalui `Fetcher` produksi. Respons 404 dicatat ke `run.log`; `Fetcher.retries` tetap nol.

```text
404 proof: status=404 requests=1 retries=0
grep RETRY=0
grep 404=4
```

Empat kecocokan teks `404` berasal dari URL dan status/error di dua baris log, bukan empat request. Bukti jumlah request adalah `requests=1`; unit test terisolasi juga menegakkan satu pemanggilan untuk masing-masing 403 dan 404.

## Kesimpulan

Semua syarat bukti terpenuhi: `N2 > N1`, `L2 > L1`, duplikat nol, `resume_used == true`, rate limit di atas ambang, serta 404 tidak di-retry.
