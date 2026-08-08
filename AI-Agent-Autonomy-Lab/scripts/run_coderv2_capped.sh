#!/usr/bin/env bash
# run_coderv2_capped.sh — only deepseek-coder-v2:16b (light MoE ~9GB), capped context.
# deepseek-r1:32b was dropped: 0 tool calls in any channel over 3 runs (narrates, doesn't act)
# and ~27 min/run — n/a established, not worth the memory-kill risk.
set -eu
cd "$(dirname "$0")/.."

echo "=== $(date +%H:%M:%S) restart ollama capped (single instance) ==="
osascript -e 'quit app "Ollama"' 2>/dev/null || true; sleep 1
pkill -x ollama 2>/dev/null || true; sleep 2
OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS='*' OLLAMA_CONTEXT_LENGTH=16384 \
  nohup ollama serve >/tmp/ollama-reB.log 2>&1 &
sleep 5
curl -s http://127.0.0.1:11434/api/tags >/dev/null || { echo "ollama DOWN — abort"; exit 1; }

# range is already up; just verify the seal + model path
bash verify_containment.sh 2>&1 | tail -1
docker exec lab-agent-kali sh -c 'curl -s -o /dev/null -w "proxy->model %{http_code}\n" -m 20 -X POST http://model-proxy:8080/v1/chat/completions -H "Host: localhost:11434" -H "Content-Type: application/json" -d "{\"model\":\"deepseek-coder-v2:16b\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":5}"'

echo "=== $(date +%H:%M:%S) deepseek-coder-v2:16b Task-B (ctx=16384, max_tokens=2048) ==="
export MODEL_MAX_TOKENS=2048
bash scripts/run_B_healthchecked.sh cmpB deepseek-coder-v2:16b
echo "CODERV2_CAPPED_DONE"
