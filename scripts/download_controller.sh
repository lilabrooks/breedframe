#!/bin/sh
# Explicit online download; the application inference server stays offline.
set -eu
cd "$(dirname "$0")/.."
model_name=${1:-qwen3.5:4b}
case "$model_name" in qwen3:4b|qwen3.5:4b) ;; *) echo 'Choose qwen3:4b or qwen3.5:4b.' >&2; exit 1 ;; esac
if curl -fsS http://127.0.0.1:11435/api/version >/dev/null 2>&1; then
  echo 'Port 11435 is occupied. Stop that server before this download.' >&2
  exit 1
fi
mkdir -p models/ollama
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS="$PWD/models/ollama" OLLAMA_NO_CLOUD=1 .runtime/ollama/ollama serve > .runtime/controller-download.log 2>&1 &
download_pid=$!
cleanup() { kill "$download_pid" 2>/dev/null || true; wait "$download_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS http://127.0.0.1:11435/api/version >/dev/null 2>&1; then break; fi
  sleep 1
done
PYTHONPATH=. .venv/bin/python - "$model_name" <<'PY'
import httpx
import sys
from breedframe.config import CONTROLLER_MODELS
model = sys.argv[1]
with httpx.Client(trust_env=False, timeout=1800) as client:
    response = client.post('http://127.0.0.1:11435/api/pull', json={'model': model, 'stream': False})
    response.raise_for_status()
    result = response.json()
    if result.get('status') != 'success':
        raise SystemExit(str(result))
    tags = client.get('http://127.0.0.1:11435/api/tags').json()['models']
    if not any(m['name'] == model and m['digest'] == CONTROLLER_MODELS[model] for m in tags):
        raise SystemExit('Downloaded model differs from the reviewed digest. Do not run it as this comparison.')
print('Downloaded and verified', model)
PY
