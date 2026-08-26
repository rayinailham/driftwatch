#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
pid_file="$root/fixtures/.lab.pid"
log_file="$root/logs/driftlab.log"

if [[ -f "$pid_file" ]]; then
  pid=$(<"$pid_file")
  if kill -0 "$pid" 2>/dev/null; then
    echo "DriftLab already running (PID $pid)"
    exit 0
  fi
  rm -f "$pid_file"
fi

mkdir -p "$root/logs"
uv run --no-sync python "$root/scripts/gen_fixture.py" --seed 1337 >/dev/null
nohup uv run --no-sync python "$root/scripts/lab_serve.py" >"$log_file" 2>&1 &
pid=$!
printf '%s\n' "$pid" >"$pid_file"

for _ in {1..50}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    cat "$log_file" >&2
    rm -f "$pid_file"
    exit 1
  fi
  if curl -fs -o /dev/null http://127.0.0.1:8100/; then
    echo "DriftLab ready on http://127.0.0.1:8100 (PID $pid)"
    exit 0
  fi
  sleep 0.1
done

echo "DriftLab failed to become ready" >&2
kill "$pid" 2>/dev/null || true
rm -f "$pid_file"
exit 1
