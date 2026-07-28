#!/bin/bash
# Smoke + throughput benchmark for the ssrm_hopper env (FA3 on H100).
# Old-env reference: smoke baseline gen 80s, injection gen 177s.
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=${1:-1}
source scripts/env_hopper.sh

python -m src.experiments.run_baseline \
    --model qwen3-4b-thinking --dataset rg_maze --limit 4 \
    --n-samples 4 --max-new-tokens 8192 --max-model-len 16384 \
    --run-name smoke_hopper_base

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking --baseline results/smoke_hopper_base/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.5 1.0 \
    --n-samples 4 --max-new-tokens 8192 --max-model-len 24576 \
    --run-name smoke_hopper_inject

echo "HOPPER SMOKE PASSED"
