#!/bin/bash
# GPU0 v2 (ssrm_hopper env, FA3): thinking-model AIME injection grid.
# Launch after the old-env baseline finishes (kill the old queue at the
# stage boundary so the slow env never starts this big stage).
set -euo pipefail
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=0
source scripts/env_hopper.sh

python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/base_qwen3-4b-thinking_aime24_25/rollouts.jsonl \
    --sources self_wrong irrelevant corrupted wrong_conclusion \
    --fractions 0.25 0.5 0.75 1.0 \
    --n-samples 16 --max-new-tokens 81920 --max-model-len 172032 \
    --run-name inject_qwen3-4b-thinking_aime24_25

echo "GPU0 V2 INJECT DONE"
