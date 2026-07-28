#!/bin/bash
# Gemma-4-E2B-it suite (task #6, non-Qwen generalization check), GPU1:
# smoke -> AIME thinking baseline+injection -> maze thinking baseline+injection.
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=1
source scripts/env_hopper.sh

# --- smoke (tiny, validates channel-marker handling end-to-end) ---
python -m src.experiments.run_baseline \
    --model gemma-4-e2b --dataset rg_maze --limit 4 \
    --n-samples 4 --max-new-tokens 8192 --max-model-len 16384 \
    --run-name smoke_gemma_base

python -m src.experiments.run_injection \
    --model gemma-4-e2b --baseline results/smoke_gemma_base/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.5 1.0 \
    --n-samples 4 --max-new-tokens 8192 --max-model-len 24576 \
    --run-name smoke_gemma_inject

echo "GEMMA SMOKE PASSED"

# --- AIME (thinking mode) ---
python -m src.experiments.run_baseline \
    --model gemma-4-e2b --dataset aime24_25 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 49152 \
    --run-name base_gemma-4-e2b_aime24_25

python -m src.experiments.run_injection \
    --model gemma-4-e2b \
    --baseline results/base_gemma-4-e2b_aime24_25/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 81920 \
    --run-name inject_gemma-4-e2b_aime24_25

# --- maze (thinking mode) ---
python -m src.experiments.run_baseline \
    --model gemma-4-e2b --dataset rg_maze \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 49152 \
    --run-name base_gemma-4-e2b_rg_maze

python -m src.experiments.run_injection \
    --model gemma-4-e2b \
    --baseline results/base_gemma-4-e2b_rg_maze/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 81920 \
    --run-name inject_gemma-4-e2b_rg_maze

echo "GEMMA PILOT DONE"
