#!/bin/bash
# "Wait,"-append intervention: a one-token test of the commitment reading.
#
# If a complete own-wrong chain collapses recovery because it looks FINISHED, then
# re-opening it should restore some. Four arms on the same questions:
#   W0_unchanged  the chain as-is                (control, replicates arm D)
#   W1_wait       + "Wait,"                      (the intervention)
#   W2_neutral    + "So,"                        (control: any appended text?)
#   W3_recheck    + "Wait, let me double-check that."
#
#   WR_GPU=1 bash scripts/run_wait_append.sh [model]
set -uo pipefail
cd "$(dirname "$0")/.."
GPU="${WR_GPU:-1}"
MODEL="${1:-qwen3-4b-thinking}"
export CUDA_VISIBLE_DEVICES="$GPU"
source scripts/env_hopper.sh
case "$MODEL" in
  qwen3-4b-thinking) MAXNEW=81920; MAXLEN=172032 ;;
  qwen3-4b-instruct) MAXNEW=16384; MAXLEN=49152  ;;
esac
LOG="logs/wait_append_${MODEL}.log"
echo "=== $(date -Is) START wait_append $MODEL on GPU$GPU" | tee -a "$LOG"
python -m src.experiments.run_injection \
    --model "$MODEL" \
    --baseline "results/base_${MODEL}_aime24_25/rollouts.jsonl" \
    --sources wait_append --fractions 1.0 --n-samples 16 \
    --max-new-tokens "$MAXNEW" --max-model-len "$MAXLEN" --no-full-closed \
    --run-name "waitappend_${MODEL}_aime" 2>&1 | tee -a "$LOG"
echo "=== $(date -Is) WAIT APPEND DONE: $MODEL (rc=${PIPESTATUS[0]})" | tee -a "$LOG"
