MAKEFLAGS := -j16
.NOTPARALLEL:

.PHONY: prune
prune:
	bash scripts/prune.sh --dry-run
