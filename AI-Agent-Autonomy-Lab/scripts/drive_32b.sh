#!/usr/bin/env bash
# drive_32b.sh — pull the two 32b models, wait for the 7-8b batch to free the GPU, then run
# the 32b Task-B comparison. One background driver so no babysitting and no VRAM contention.
set -eu
cd "$(dirname "$0")/.."

echo "=== $(date +%H:%M:%S) pulling qwen2.5-coder:32b ==="
ollama pull qwen2.5-coder:32b
echo "=== $(date +%H:%M:%S) pulling huihui_ai/qwen2.5-abliterate:32b ==="
ollama pull huihui_ai/qwen2.5-abliterate:32b

echo "=== $(date +%H:%M:%S) waiting for the 7-8b comparison to finish (frees VRAM) ==="
until grep -q ALL_COMPARE_B_DONE runs/compareB.log 2>/dev/null; do sleep 15; done
echo "=== $(date +%H:%M:%S) 7-8b batch done — starting 32b comparison ==="

bash scripts/compare_B_32b.sh
echo "DRIVE_32B_COMPLETE"
