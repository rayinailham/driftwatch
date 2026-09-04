#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
pid_file="$root/fixtures/.lab.pid"
log_file="$root/logs/driftlab.log"

# Port fixture: LAB_PORT dari lingkungan menang, lalu .env, lalu 8100 (D8).
# Salinan bersih A11 memakai 8101 supaya tidak menabrak fixture run harian.
if [[ -z "${LAB_PORT:-}" && -f "$root/.env" ]]; then
  LAB_PORT=$(sed -n 's/^LAB_PORT=//p' "$root/.env" | tail -1)
fi
LAB_PORT=${LAB_PORT:-8100}
[[ "$LAB_PORT" =~ ^[0-9]+$ ]] || { echo "LAB_PORT harus angka, dapat: $LAB_PORT" >&2; exit 1; }
export LAB_PORT

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
  if curl -fs -o /dev/null "http://127.0.0.1:$LAB_PORT/"; then
    echo "DriftLab ready on http://127.0.0.1:$LAB_PORT (PID $pid)"
    exit 0
  fi
  sleep 0.1
done

echo "DriftLab failed to become ready" >&2
kill "$pid" 2>/dev/null || true
rm -f "$pid_file"
exit 1
