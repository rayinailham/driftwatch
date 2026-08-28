MAKEFLAGS := -j16
.NOTPARALLEL:

.PHONY: oracles prune report weekly
oracles:
	bash scripts/lab_down.sh
	bash scripts/lab_up.sh
	uv run --no-sync python scripts/run_oracles.py

prune:
	bash scripts/prune.sh --dry-run

report:
	uv run --no-sync python src/report.py --all

weekly:
	uv run --no-sync python src/report.py --weekly --today
