#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
runtime_pid=''
app_pid=''
cleanup() {
  if [ -n "$app_pid" ]; then kill "$app_pid" 2>/dev/null || true; wait "$app_pid" 2>/dev/null || true; fi
  if [ -n "$runtime_pid" ]; then kill "$runtime_pid" 2>/dev/null || true; wait "$runtime_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM
if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
  /usr/bin/sandbox-exec -f scripts/offline.sb sh scripts/serve_ollama.sh > .runtime/ollama.log 2>&1 &
  runtime_pid=$!
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then break; fi
    sleep 1
  done
fi
.venv/bin/python scripts/check_models.py
/usr/bin/sandbox-exec -f scripts/offline.sb .venv/bin/uvicorn breedframe.app:app --host 127.0.0.1 --port 8765 &
app_pid=$!
echo 'BreedFrame: http://127.0.0.1:8765 (Ctrl-C stops processes started by this script)'
wait "$app_pid"
