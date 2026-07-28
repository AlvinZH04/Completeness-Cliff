#!/bin/bash
# End-to-end GPU smoke test: tiny baseline + tiny injection on rg_maze.
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

export CUDA_VISIBLE_DEVICES=${1:-0}

python -m src.experiments.run_baseline \
    --model qwen3-4b-thinking --dataset rg_maze --limit 4 \
    --n-samples 4 --max-new-tokens 8192 --max-model-len 16384 \
    --run-name smoke_base

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking --baseline results/smoke_base/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.5 1.0 \
    --n-samples 4 --max-new-tokens 8192 --max-model-len 24576 \
    --run-name smoke_inject

echo "SMOKE TEST PASSED"
