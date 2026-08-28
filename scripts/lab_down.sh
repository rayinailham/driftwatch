#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
pid_file="$root/fixtures/.lab.pid"

if [[ ! -f "$pid_file" ]]; then
  echo "DriftLab is not running"
  exit 0
fi

pid=$(<"$pid_file")
if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$pid_file"
  echo "DriftLab is not running (removed stale PID $pid)"
  exit 0
fi
cmdline=$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null || true)
if [[ "$cmdline" != *"scripts/lab_serve.py"* ]]; then
  echo "Refusing to stop PID $pid: not DriftLab" >&2
  rm -f "$pid_file"
  exit 1
fi

kill "$pid"
for _ in {1..50}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$pid_file"
    echo "DriftLab stopped (PID $pid)"
    exit 0
  fi
  sleep 0.1
done

echo "DriftLab did not stop after SIGTERM" >&2
exit 1
