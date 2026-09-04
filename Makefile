# DriftWatch — orkestrasi operator (D10: GNU Make, `just` tidak terpasang di mesin ini).
#
# `make all` WAJIB jalan tanpa Docker sama sekali (D8/D21). Fixture DriftLab dilayani
# `http.server` stdlib, checkpoint SQLite, laporan openpyxl — tidak ada satu pun langkah
# di bawah yang memanggil `docker`.

MAKEFLAGS := -j16
.NOTPARALLEL:

# `MAKEFLAGS := -j16` di atas (dan `-j` apa pun di shell user) tidak boleh mengacak urutan
# pipeline: `harvest` sebelum `diff`, `diff` sebelum `report`. `.NOTPARALLEL:` adalah
# gerbang konservatif itu — jangan dihapus sampai ada target paralel yang eksplisit.

PY      := uv run --no-sync python
TARGETS := driftlab books quotes seo
DATE    ?= $(shell date +%F)

.PHONY: all setup lab-up lab-down oracles harvest diff report weekly publish test audit prune help

help:
	@echo "setup     uv sync + siapkan fixture DriftLab"
	@echo "lab-up    nyalakan driftlab di :$${LAB_PORT:-8100} (http.server stdlib, tanpa Docker)"
	@echo "oracles   11 skenario drift → wajib 11/11"
	@echo "harvest   panen 4 target ($(TARGETS))"
	@echo "diff      diff + alarm"
	@echo "report    digest harian + REPORT.xlsx mingguan"
	@echo "publish   perbarui halaman demo"
	@echo "test      unit test"
	@echo "audit     pemindaian kebocoran rahasia (wajib 0)"
	@echo "prune     rotasi log > 30 hari (dry-run)"
	@echo "all       setup → lab-up → harvest → diff → report → publish"
	@echo "lab-down  matikan fixture"

setup:
	uv sync
	$(PY) scripts/gen_fixture.py --seed 1337

lab-up:
	bash scripts/lab_up.sh

lab-down:
	bash scripts/lab_down.sh

# Server segar wajib: DO-06 menggagalkan tiap path hanya sekali per umur proses
# (`failed_once` di lab_serve.py), jadi server bekas `--verify` membalas 200 dan DO-06
# gagal dengan alarms=[] — kelihatan seperti regresi detector padahal server yang basi.
oracles:
	bash scripts/lab_down.sh
	bash scripts/lab_up.sh
	$(PY) scripts/run_oracles.py

harvest:
	@set -e; for t in $(TARGETS); do \
	  echo "== harvest $$t $(DATE)"; \
	  $(PY) src/scrape.py --target $$t --date $(DATE) --out data/$$t/$(DATE) --resume; \
	  $(PY) src/validate.py data/$$t/$(DATE)/records.jsonl; \
	  $(PY) src/export.py --target $$t --date $(DATE); \
	done

diff:
	@set -e; for t in $(TARGETS); do \
	  echo "== diff $$t $(DATE)"; \
	  $(PY) src/diff.py --target $$t --date $(DATE); \
	  $(PY) src/alarm.py --target $$t --date $(DATE) --no-notify; \
	done

report:
	$(PY) src/report.py --all
	$(MAKE) weekly

weekly:
	$(PY) src/report.py --weekly --today

publish:
	$(PY) src/publish.py

test:
	$(PY) -m unittest discover -s src -p 'test_*.py' -t src

audit:
	$(PY) scripts/secret_audit.py

prune:
	bash scripts/prune.sh --dry-run

all: setup lab-up harvest diff report publish
	@echo "make all selesai — fixture masih menyala, matikan dengan: make lab-down"
