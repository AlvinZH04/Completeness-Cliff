#!/bin/bash
# GPU1 queue v2 (ssrm_hopper env, FA3): remaining pilot jobs after the
# instruct-AIME injection finished under the old env, plus the instruct-AIME
# baseline rerun at 32768 tokens (old one truncated 12.4% at 16384).
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=1
source scripts/env_hopper.sh

# --- rerun: instruct AIME baseline with adequate budget ---
python -m src.experiments.run_baseline \
    --model qwen3-4b-instruct --dataset aime24_25 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 49152 \
    --run-name base_qwen3-4b-instruct_aime24_25_32k

# --- thinking on reasoning_gym maze ---
python -m src.experiments.run_baseline \
    --model qwen3-4b-thinking --dataset rg_maze \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 49152 \
    --run-name base_qwen3-4b-thinking_rg_maze

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/base_qwen3-4b-thinking_rg_maze/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 81920 \
    --run-name inject_qwen3-4b-thinking_rg_maze

# --- instruct on reasoning_gym maze ---
python -m src.experiments.run_baseline \
    --model qwen3-4b-instruct --dataset rg_maze \
    --n-samples 16 --max-new-tokens 16384 --max-model-len 32768 \
    --run-name base_qwen3-4b-instruct_rg_maze

python -m src.experiments.run_injection \
    --model qwen3-4b-instruct \
    --baseline results/base_qwen3-4b-instruct_rg_maze/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 16384 --max-model-len 49152 \
    --run-name inject_qwen3-4b-instruct_rg_maze

# --- mini_sudoku (bonus if time) ---
python -m src.experiments.run_baseline \
    --model qwen3-4b-thinking --dataset rg_mini_sudoku \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 49152 \
    --run-name base_qwen3-4b-thinking_rg_mini_sudoku

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/base_qwen3-4b-thinking_rg_mini_sudoku/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 32768 --max-model-len 81920 \
    --run-name inject_qwen3-4b-thinking_rg_mini_sudoku

echo "GPU1 V2 PILOT DONE"
