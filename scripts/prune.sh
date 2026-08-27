#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

[[ -d data ]] || exit 0

case "${1:---dry-run}" in
  --dry-run)
    find data -type f -name run.log -mtime +30 -print
    ;;
  --delete)
    find data -type f -name run.log -mtime +30 -print -delete
    ;;
  *)
    echo "usage: scripts/prune.sh [--dry-run|--delete]" >&2
    exit 2
    ;;
esac
