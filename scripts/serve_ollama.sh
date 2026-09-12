#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_MODELS="$PWD/models/ollama"
export OLLAMA_NO_CLOUD=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_CONTEXT_LENGTH=8192
exec .runtime/ollama/ollama serve
