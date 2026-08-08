#!/usr/bin/env bash
# run_deepseek_capped.sh — deepseek Task-B, with the LLM-Benchmark lesson applied:
# cap the context so a 32b does not default to a 32K KV-cache and swap the host to a crawl.
# Launch ONLY after the coder/mistral re-test has finished (this restarts ollama + rebuilds
# the image — both would kill a run in flight).
set -eu
cd "$(dirname "$0")/.."

echo "=== $(date +%H:%M:%S) restarting ollama with OLLAMA_CONTEXT_LENGTH=16384 (single instance) ==="
osascript -e 'quit app "Ollama"' 2>/dev/null || true; sleep 1
pkill -x ollama 2>/dev/null || true; sleep 2
OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS='*' OLLAMA_CONTEXT_LENGTH=16384 \
  nohup ollama serve >/tmp/ollama-reB.log 2>&1 &
sleep 5
curl -s http://127.0.0.1:11434/api/tags >/dev/null || { echo "ollama DOWN — abort"; exit 1; }

echo "=== $(date +%H:%M:%S) rebuilding kali + gate ==="
MODEL_HOST_PORT=11434 docker compose -f docker/compose.yml --profile kali up -d --build >/dev/null 2>&1
bash verify_containment.sh 2>&1 | tail -1

echo "=== $(date +%H:%M:%S) deepseek Task-B (ctx=16384, r1 reasoning budget trimmed to 3072) ==="
export MODEL_MAX_TOKENS=3072
bash scripts/run_B_healthchecked.sh cmpB deepseek-r1:32b deepseek-coder-v2:16b
echo "DEEPSEEK_CAPPED_DONE"
