#!/bin/sh
# Online bootstrap; application runtime performs no downloads.
set -eu
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
  echo 'The bundled Ollama setup targets Apple Silicon macOS.' >&2
  exit 1
fi
command -v uv >/dev/null || { echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2; exit 1; }
mkdir -p .runtime/ollama models data
export UV_CACHE_DIR="$PWD/.runtime/uv-cache"
uv sync --frozen --python 3.11
if [ ! -x .runtime/ollama/ollama ]; then
  curl -fL https://github.com/ollama/ollama/releases/download/v0.34.0/ollama-darwin.tgz -o .runtime/ollama-darwin.tgz
  echo 'dd12b00bcce2d6551178e67ada90d5af9f75bdb54a118b96655250fa3e8ef734  .runtime/ollama-darwin.tgz' | shasum -a 256 -c -
  tar xzf .runtime/ollama-darwin.tgz -C .runtime/ollama
fi
HF_HOME="$PWD/.runtime/huggingface" .venv/bin/python scripts/download_classifier.py
.venv/bin/python scripts/prepare_images.py
runtime_pid=''
cleanup() { if [ -n "$runtime_pid" ]; then kill "$runtime_pid" 2>/dev/null || true; wait "$runtime_pid" 2>/dev/null || true; fi; }
trap cleanup EXIT INT TERM
if ! curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
  sh scripts/serve_ollama.sh > .runtime/setup-ollama.log 2>&1 &
  runtime_pid=$!
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then break; fi
    sleep 1
  done
  curl -fsS http://127.0.0.1:11434/api/pull -d '{"model":"qwen3:4b","stream":false}' > .runtime/pull-result.json
fi
.venv/bin/python scripts/check_models.py
echo 'Setup complete. Run: sh scripts/start.sh'
