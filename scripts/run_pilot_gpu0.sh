#!/bin/bash
# Pilot GPU0 queue: THINKING model on AIME 24+25 (the headline experiment).
# Baseline (harvests wrong traces) -> full injection grid.
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
export CUDA_VISIBLE_DEVICES=0

python -m src.experiments.run_baseline \
    --model qwen3-4b-thinking --dataset aime24_25 \
    --n-samples 16 --max-new-tokens 81920 --max-model-len 98304 \
    --run-name base_qwen3-4b-thinking_aime24_25

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/base_qwen3-4b-thinking_aime24_25/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 81920 --max-model-len 172032 \
    --run-name inject_qwen3-4b-thinking_aime24_25

echo "GPU0 PILOT DONE"
