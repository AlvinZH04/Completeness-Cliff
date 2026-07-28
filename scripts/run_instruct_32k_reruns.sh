#!/bin/bash
# Longer-budget reruns of the two instruct runs whose cells exceeded the 2%
# truncation gate (findings.md T1). Same conditions, budget raised 16k -> 32k.
# Originals are kept under their old run names so the two can be compared.
#
#   WR_GPU=0 bash scripts/run_instruct_32k_reruns.sh ablation
#   WR_GPU=1 bash scripts/run_instruct_32k_reruns.sh waitappend
set -uo pipefail
cd "$(dirname "$0")/.."
GPU="${WR_GPU:-0}"; WHICH="${1:?ablation|waitappend}"
export CUDA_VISIBLE_DEVICES="$GPU"
source scripts/env_hopper.sh
case "$WHICH" in
  ablation)   SRC=paired_fixed; NAME=ablation_paired_qwen3-4b-instruct_aime_32k; CLOSED="" ;;
  waitappend) SRC=wait_append;  NAME=waitappend_qwen3-4b-instruct_aime_32k;     CLOSED="--no-full-closed" ;;
  *) echo "unknown: $WHICH"; exit 1 ;;
esac
LOG="logs/rerun32k_${WHICH}.log"
echo "=== $(date -Is) START 32k rerun: $WHICH on GPU$GPU -> $NAME" | tee -a "$LOG"
python -m src.experiments.run_injection \
    --model qwen3-4b-instruct \
    --baseline results/base_qwen3-4b-instruct_aime24_25/rollouts.jsonl \
    --sources "$SRC" --fractions 1.0 --n-samples 16 \
    --max-new-tokens 32768 --max-model-len 81920 --forced-max-tokens 16384 \
    $CLOSED --run-name "$NAME" 2>&1 | tee -a "$LOG"
echo "=== $(date -Is) 32K RERUN DONE: $WHICH (rc=${PIPESTATUS[0]})" | tee -a "$LOG"
