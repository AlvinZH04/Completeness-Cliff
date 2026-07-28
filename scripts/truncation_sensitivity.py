"""Truncation sensitivity analysis for cells that exceed TRUNCATION_GATE.

The third review flagged that several instruct cells sit above the project's 2%
gate. Raw truncation overstates the damage, because a sample can hit the token cap
*after* emitting its boxed answer, in which case it is still graded normally. What
actually threatens a result is the subset that is truncated AND has no extractable
answer, since those are scored as failures.

This script reports, per cell:
  * raw truncation rate
  * the share of truncated samples that still produced an answer
  * the effective loss (truncated AND no answer)
  * a worst-case bound: pass@k recomputed as if every lost sample had been correct

The worst-case bound is deliberately absurd (a sample that ran to the cap without
emitting an answer was not about to be right), so a conclusion that survives it is
safe against this artifact.

    python scripts/truncation_sensitivity.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import TRUNCATION_GATE  # noqa: E402
from src.metrics import pass_at_k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

RUNS = [
    ("instruct paired ablation 32k", "ablation_paired_qwen3-4b-instruct_aime_32k",
     ["A_answer_only", "B_generic", "C_task_specific", "D_own_complete"]),
    ("instruct wait-append 32k", "waitappend_qwen3-4b-instruct_aime_32k",
     ["W0_unchanged", "W1_wait", "W2_neutral", "W3_recheck"]),
    ("instruct paired ablation", "ablation_paired_qwen3-4b-instruct_aime",
     ["A_answer_only", "B_generic", "C_task_specific", "D_own_complete"]),
    ("instruct wait-append", "waitappend_qwen3-4b-instruct_aime",
     ["W0_unchanged", "W1_wait", "W2_neutral", "W3_recheck"]),
    ("thinking paired ablation", "ablation_paired_qwen3-4b-thinking_aime",
     ["A_answer_only", "B_generic", "C_task_specific", "D_own_complete"]),
]


def cell_stats(run, cond):
    per = {}
    path = os.path.join(RESULTS, run, "rollouts.jsonl")
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r["condition"] != cond:
                continue
            s = r["samples"]
            clean = [x for x in s if not x.get("truncated")]
            per[r["qid"]] = {
                "n": len(s),
                "correct": sum(bool(x.get("correct")) for x in s),
                "trunc": sum(bool(x.get("truncated")) for x in s),
                "trunc_with_answer": sum(1 for x in s if x.get("truncated")
                                         and x.get("answer") is not None),
                "no_answer": sum(1 for x in s if x.get("answer") is None),
                "trunc_no_answer": sum(1 for x in s if x.get("truncated")
                                       and x.get("answer") is None),
                # termination-clean subset: samples that ended on their own
                "n_clean": len(clean),
                "correct_clean": sum(bool(x.get("correct")) for x in clean),
                "tokens": sum(x.get("n_tokens", 0) for x in s),
            }
    return per


def main() -> int:
    print(f"TRUNCATION_GATE = {TRUNCATION_GATE:.0%}\n")
    out = {}
    for label, run, arms in RUNS:
        if not os.path.exists(os.path.join(RESULTS, run, "rollouts.jsonl")):
            print(f"skip {label}: no rollouts")
            continue
        print(f"=== {label} ({run}) ===")
        print(f"  {'cell':16s} {'trunc':>7s} {'answered':>9s} {'tr+no-ans':>9s} "
              f"{'pass@1':>7s} {'worst':>7s} {'pass@16':>8s} {'worst':>7s}")
        out[run] = {}
        for arm in arms:
            per = cell_stats(run, f"{arm}:prefix1")
            if not per:
                continue
            tot = sum(v["n"] for v in per.values())
            tr = sum(v["trunc"] for v in per.values())
            twa = sum(v["trunc_with_answer"] for v in per.values())
            na = sum(v["no_answer"] for v in per.values())
            tna = sum(v["trunc_no_answer"] for v in per.values())
            p1 = sum(pass_at_k(v["n"], v["correct"], 1) for v in per.values()) / len(per)
            p16 = sum(pass_at_k(v["n"], v["correct"], 16) for v in per.values()) / len(per)
            # bound counts EVERY no-answer sample correct, not only truncated ones
            w1 = sum(pass_at_k(v["n"], min(v["n"], v["correct"] + v["no_answer"]), 1)
                     for v in per.values()) / len(per)
            w16 = sum(pass_at_k(v["n"], min(v["n"], v["correct"] + v["no_answer"]), 16)
                      for v in per.values()) / len(per)
            # accuracy over ALL samples vs over only those that terminated
            acc = sum(v["correct"] for v in per.values()) / tot
            nclean = sum(v["n_clean"] for v in per.values())
            acc_clean = (sum(v["correct_clean"] for v in per.values()) / nclean
                         if nclean else float("nan"))
            mean_tok = sum(v["tokens"] for v in per.values()) / tot
            flag = " *" if tr / tot > TRUNCATION_GATE else ""
            print(f"  {arm:16s} {tr/tot:7.1%} {(twa/tr if tr else 0):9.0%} "
                  f"{tna/tot:6.1%} {p1:7.3f} {w1:7.3f} {p16:8.3f} {w16:7.3f}{flag}")
            print(f"  {'':16s} {'accuracy: all samples':>34s} {acc:7.3f}   "
                  f"terminated-only {acc_clean:.3f}  (kept {nclean/tot:.0%}, "
                  f"mean {mean_tok:.0f} tok)")
            out[run][arm] = {
                "truncation_rate": round(tr / tot, 4),
                "truncated_still_answered": round(twa / tr, 4) if tr else None,
                "no_answer_rate": round(na / tot, 4),
                "truncated_no_answer_rate": round(tna / tot, 4),
                "truncated_with_answer_rate": round(twa / tot, 4),
                "n_samples": tot, "n_truncated": tr,
                "n_no_answer": na, "n_truncated_no_answer": tna,
                "pass@1": round(p1, 4),
                "pass@1_all_no_answer_bound": round(w1, 4),
                "pass@16": round(p16, 4),
                "pass@16_all_no_answer_bound": round(w16, 4),
                "accuracy_all_samples": round(acc, 4),
                "accuracy_terminated_only": (round(acc_clean, 4) if nclean else None),
                "fraction_samples_kept": round(nclean / tot, 4),
                "mean_gen_tokens": round(mean_tok, 1),
                "exceeds_gate": bool(tr / tot > TRUNCATION_GATE),
            }
        print()
    print("* exceeds TRUNCATION_GATE on raw truncation")
    print("'tr+no-ans' = truncated AND no extractable answer")
    print("'worst' is an ALL-no-answer bound: every sample lacking an answer counted correct\n")

    mpath = os.path.join(RESULTS, "blog_manifest.json")
    if os.path.exists(mpath):
        m = json.load(open(mpath))
        m["truncation_sensitivity"] = {
            "_about": ("Per-cell truncation diagnostics. Three distinct quantities are "
                       "kept separate: no_answer_rate (any sample without an extractable "
                       "answer, truncated or not), truncated_no_answer_rate (truncated AND "
                       "no answer), and truncated_with_answer_rate (capped but gradable). "
                       "The *_all_no_answer_bound fields count EVERY no-answer sample as "
                       "correct, which is a deliberately conservative bound and is NOT "
                       "truncation-specific. Capped samples that do contain an answer are "
                       "gradable but still right-censored: the grader takes the last boxed "
                       "answer, so further generation could have changed it."),
            "gate": TRUNCATION_GATE, "runs": out,
        }
        json.dump(m, open(mpath, "w"), indent=2)
        print(f"wrote truncation_sensitivity into {mpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
