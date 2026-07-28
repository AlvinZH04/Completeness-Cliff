#!/bin/bash
# Paired fixed-answer scaffold ablation (review item 1, docs/blog section 6).
#
# Holds the wrong ANSWER fixed per question and varies only the scaffold around it,
# so the "the scaffold persuades, not the conclusion" claim can be tested rather than
# asserted. Four arms, all asserting the same wrong answer W (= the answer the model's
# own wrong rollout reached, so arm D needs no rewriting):
#
#   A_answer_only     "The answer is W."                      (no steps)
#   B_generic         task-agnostic pseudo-rationale -> W     (no real work shown)
#   C_task_specific   short prefix of the model's own reasoning + conclusion -> W
#   D_own_complete    the model's own complete wrong derivation (already ends on W)
#
# Each arm runs open (model may keep thinking) and forced (answer immediately).
# Forced cells use a raised budget plus stop strings, because the pilot's forced
# cells hit the 4096-token cap and emitted no answer on 43-57% of samples
# (findings.md C6), which inflated the open-block premium.
#
# Takes the model as an argument so each model can be sized and queued separately.
# Time limits are set close to the measured estimate rather than padded to the
# partition maximum: a shorter request is far more likely to be backfilled into a
# gap ahead of long high-priority jobs.
#
# Submit (thinking, ~9.2h est, needs the 94GB NVL cards for its 172k context):
#   sbatch --partition=nvl --time=14:00:00 scripts/sbatch_paired_ablation.sh qwen3-4b-thinking
# Submit (instruct, ~2.8h est, 49k context fits either card):
#   sbatch --partition=nvl,h100 --time=06:00:00 scripts/sbatch_paired_ablation.sh qwen3-4b-instruct
#
# Watch: squeue -u $USER ; tail -f logs/paired_ablation_*.log
#
#SBATCH --job-name=wr-paired
#SBATCH --gres=gpu:h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --output=logs/paired_ablation_%j.log
#SBATCH --error=logs/paired_ablation_%j.log

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"

source scripts/env_hopper.sh

MODEL="${1:?usage: sbatch [slurm opts] $0 <qwen3-4b-thinking|qwen3-4b-instruct>}"
case "$MODEL" in
  qwen3-4b-thinking) MAXNEW=81920; MAXLEN=172032 ;;
  qwen3-4b-instruct) MAXNEW=16384; MAXLEN=49152  ;;
  *) echo "unsupported model: $MODEL"; exit 1 ;;
esac

BASELINE="results/base_${MODEL}_aime24_25/rollouts.jsonl"
RUN_NAME="ablation_paired_${MODEL}_aime"

echo "=== $(date -Is) host=$(hostname) job=${SLURM_JOB_ID:-none} partition=${SLURM_JOB_PARTITION:-none}"
echo "=== model=$MODEL  baseline=$BASELINE  run=$RUN_NAME"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || true

python -m src.experiments.run_injection \
    --model "$MODEL" \
    --baseline "$BASELINE" \
    --sources paired_fixed \
    --fractions 1.0 \
    --n-samples 16 \
    --max-new-tokens "$MAXNEW" \
    --max-model-len "$MAXLEN" \
    --forced-max-tokens 16384 \
    --run-name "$RUN_NAME"

echo "=== $(date -Is) PAIRED ABLATION DONE: $RUN_NAME"
