#!/usr/bin/env bash
# drive_deepseek.sh — pull deepseek-r1:32b + deepseek-coder-v2:16b, wait for the current
# coder/mistral re-test to free the image, rebuild kali (bakes MODEL_MAX_TOKENS support), then
# run Task B on both. r1 is a reasoning model → MODEL_MAX_TOKENS=4096 so its CoT doesn't eat the
# budget before a tool call. One 32b in VRAM at a time; per-run target restart via the runner.
set -eu
cd "$(dirname "$0")/.."

echo "=== $(date +%H:%M:%S) pulling deepseek-r1:32b ==="
ollama pull deepseek-r1:32b
echo "=== $(date +%H:%M:%S) pulling deepseek-coder-v2:16b ==="
ollama pull deepseek-coder-v2:16b

echo "=== $(date +%H:%M:%S) waiting for the coder/mistral re-test to finish (frees the image) ==="
until grep -q ALL_HEALTHCHECKED_B_DONE runs/rerun_protocol_fix.log 2>/dev/null; do sleep 15; done
echo "=== $(date +%H:%M:%S) re-test done — rebuilding kali with MODEL_MAX_TOKENS support ==="

MODEL_HOST_PORT=11434 docker compose -f docker/compose.yml --profile kali up -d --build >/dev/null 2>&1
bash verify_containment.sh 2>&1 | tail -1

echo "=== $(date +%H:%M:%S) running deepseek Task-B (r1 reasoning: max_tokens=4096) ==="
export MODEL_MAX_TOKENS=4096
bash scripts/run_B_healthchecked.sh cmpB deepseek-r1:32b deepseek-coder-v2:16b
echo "DRIVE_DEEPSEEK_COMPLETE"
