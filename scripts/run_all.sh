#!/usr/bin/env bash
# Track A: run the full suite on every local model, one after another (there is only one GPU).
# Usage: bash scripts/run_all.sh
cd "$(dirname "$0")/.." || exit 1
PY=.venv/Scripts/python

# model  flags
# Model list: from the command line (e.g. bash scripts/run_all.sh "mistral-nemo --skip-vision" "qwen3.5:4b") or the default below
if [ $# -gt 0 ]; then MODELS="$(printf '%s
' "$@")"; else MODELS="
qwen3.5:9b
gemma4:12b
gemma4:latest
gemma4:e2b
llama3.1:8b --skip-vision
mistral-nemo --skip-vision
qwen3.5:4b
gpt-oss:20b --skip-vision
gemma4:26b
gemma4:e4b
"; fi

wait_for_model() {
  for i in $(seq 1 240); do
    ollama list 2>/dev/null | grep -qE "^$1[: ]" && return 0
    sleep 30
  done
  return 1
}

echo "$MODELS" | sed '/^\s*$/d' | while read -r model flags; do
  echo "=============== $model $flags  $(date +%H:%M)"
  wait_for_model "$model" || { echo "SKIP $model: not available"; continue; }
  # VRAM in use before the run (rule: < 1000 MB, close other GPU-heavy apps)
  echo "vram_before=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader)"
  $PY scripts/run.py --model "$model" --suite all $flags 2>&1 | head -1
  $PY scripts/run.py --model "$model" --suite benchmark/01-speed.yaml --users 4 2>&1 | head -1
  ollama stop "$model" >/dev/null 2>&1
done

# Thinking on: cost/benefit on documents, hallucinations, reasoning, tools
for model in qwen3.5:9b gemma4:12b; do
  echo "=============== THINK $model  $(date +%H:%M)"
  $PY scripts/run.py --model "$model" --think --max-tokens 3000 \
    --suite benchmark/03-documents.yaml,benchmark/05-hallucinations.yaml,benchmark/10-reasoning.yaml,benchmark/09-tools.yaml 2>&1 | head -1
  ollama stop "$model" >/dev/null 2>&1
done

echo "=============== EVAL  $(date +%H:%M)"
for d in results/local/*/; do $PY scripts/evaluate.py "$d" | grep -v '^  FAIL'; done
echo "BATCH DONE $(date +%H:%M)"
