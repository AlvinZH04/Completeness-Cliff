#!/bin/bash
# Paired fixed-answer scaffold ablation, run locally on ONE GPU (default: GPU 1).
#
# Used when the batch queue ETA is worse than just running it here: the two models
# run sequentially, thinking first because it is the primary result.
#
#   bash scripts/run_paired_ablation_local.sh            # GPU 1
#   WR_GPU=0 bash scripts/run_paired_ablation_local.sh   # pick another GPU
#
# Estimated ~9.2h (thinking) then ~2.8h (instruct), calibrated from each model's
# own pilot throughput. Writes results/ablation_paired_<model>_aime/.
set -uo pipefail
cd "$(dirname "$0")/.."

GPU="${WR_GPU:-1}"
export CUDA_VISIBLE_DEVICES="$GPU"
source scripts/env_hopper.sh

LOG="logs/paired_ablation_local.log"
echo "=== $(date -Is) host=$(hostname) CUDA_VISIBLE_DEVICES=$GPU" | tee -a "$LOG"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader | tee -a "$LOG"

run_one () {
  local model="$1" maxnew="$2" maxlen="$3"
  local run_name="ablation_paired_${model}_aime"
  echo "=== $(date -Is) START $model (max_new=$maxnew max_len=$maxlen)" | tee -a "$LOG"
  python -m src.experiments.run_injection \
      --model "$model" \
      --baseline "results/base_${model}_aime24_25/rollouts.jsonl" \
      --sources paired_fixed \
      --fractions 1.0 \
      --n-samples 16 \
      --max-new-tokens "$maxnew" \
      --max-model-len "$maxlen" \
      --forced-max-tokens 16384 \
      --run-name "$run_name" 2>&1 | tee -a "$LOG"
  local rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then
    echo "=== $(date -Is) PAIRED ABLATION DONE: $run_name" | tee -a "$LOG"
  else
    echo "=== $(date -Is) PAIRED ABLATION FAILED (rc=$rc): $run_name" | tee -a "$LOG"
  fi
  return "$rc"
}

# thinking first: it is the primary result and the slower of the two
run_one qwen3-4b-thinking 81920 172032
th_rc=$?
run_one qwen3-4b-instruct 16384 49152
in_rc=$?

echo "=== $(date -Is) ALL LOCAL ABLATION RUNS FINISHED (thinking rc=$th_rc, instruct rc=$in_rc)" | tee -a "$LOG"
exit $(( th_rc != 0 || in_rc != 0 ))
