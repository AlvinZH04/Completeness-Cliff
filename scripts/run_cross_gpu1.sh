#!/bin/bash
# Cross-dataset irrelevant traces (user request, task #7), thinking model, GPU1:
#   1) maze questions x AIME thinking-trace donors  (fast validation)
#   2) AIME questions x maze thinking-trace donors  (flagship cross-domain test)
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=1
source scripts/env_hopper.sh

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/base_qwen3-4b-thinking_rg_maze/rollouts.jsonl \
    --cross-baseline results/base_qwen3-4b-thinking_aime24_25/rollouts.jsonl \
    --sources irrelevant_cross \
    --fractions 0.25 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 131072 \
    --run-name inject_qwen3-4b-thinking_rg_maze_cross

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/base_qwen3-4b-thinking_aime24_25/rollouts.jsonl \
    --cross-baseline results/base_qwen3-4b-thinking_rg_maze/rollouts.jsonl \
    --sources irrelevant_cross \
    --fractions 0.25 1.0 \
    --n-samples 16 --max-new-tokens 81920 --max-model-len 131072 \
    --run-name inject_qwen3-4b-thinking_aime_cross

echo "CROSS PILOT DONE"
