#!/bin/bash
# Gemma cross-domain irrelevant (F4b x F8 interaction): maze questions x AIME
# Gemma traces, and AIME questions x maze Gemma traces.
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=1
source scripts/env_hopper.sh

python -m src.experiments.run_injection \
    --model gemma-4-e2b \
    --baseline results/base_gemma-4-e2b_rg_maze/rollouts.jsonl \
    --cross-baseline results/base_gemma-4-e2b_aime24_25/rollouts.jsonl \
    --sources irrelevant_cross \
    --fractions 0.25 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 65536 \
    --run-name inject_gemma-4-e2b_rg_maze_cross

python -m src.experiments.run_injection \
    --model gemma-4-e2b \
    --baseline results/base_gemma-4-e2b_aime24_25/rollouts.jsonl \
    --cross-baseline results/base_gemma-4-e2b_rg_maze/rollouts.jsonl \
    --sources irrelevant_cross \
    --fractions 0.25 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 65536 \
    --run-name inject_gemma-4-e2b_aime_cross

echo "GEMMA CROSS DONE"
