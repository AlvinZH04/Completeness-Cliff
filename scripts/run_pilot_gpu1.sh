#!/bin/bash
# Pilot GPU1 queue: INSTRUCT model on AIME 24+25, then both models on
# reasoning_gym maze (and mini_sudoku if time remains).
set -euo pipefail
cd "$(dirname "$0")/.."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate reasoning_gym
# conda libstdc++ needed by zmq; system /usr/local/cuda must NOT be on the path
# (its cuBLAS 12.9 shadows torch's bundled 12.8 -> CUBLAS_STATUS_INVALID_VALUE)
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib
# stale compile cache from crashed runs causes cudaErrorNoKernelImageForDevice
export VLLM_DISABLE_COMPILE_CACHE=1
# flash-attn kernels in this env lack sm_90 images -> triton attention (still compiled, not eager)
export WR_ATTN_BACKEND=TRITON_ATTN
export CUDA_VISIBLE_DEVICES=1

# --- instruct on AIME ---
python -m src.experiments.run_baseline \
    --model qwen3-4b-instruct --dataset aime24_25 \
    --n-samples 16 --max-new-tokens 16384 --max-model-len 32768 \
    --run-name base_qwen3-4b-instruct_aime24_25

python -m src.experiments.run_injection \
    --model qwen3-4b-instruct \
    --baseline results/base_qwen3-4b-instruct_aime24_25/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 16384 --max-model-len 49152 \
    --run-name inject_qwen3-4b-instruct_aime24_25

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

echo "GPU1 PILOT DONE"
