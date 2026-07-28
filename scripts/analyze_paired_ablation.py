"""Analyse the paired fixed-answer scaffold ablation.

All four arms assert the SAME wrong answer on the SAME questions, so differences
between them isolate the effect of the scaffold around that answer:

    A_answer_only     bare claim, no steps
    B_generic         task-agnostic pseudo-rationale
    C_task_specific   short prefix of the model's own reasoning + a conclusion
    D_own_complete    the model's own complete wrong derivation

Writes results into results/blog_manifest.json under "paired_ablation" and prints
a table with question-level bootstrap intervals.

    python scripts/analyze_paired_ablation.py
"""

from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics import pass_at_k  # noqa: E402
from src.config import TRUNCATION_GATE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MANIFEST = os.path.join(RESULTS, "blog_manifest.json")

ARMS = [("A_answer_only", "bare claim, no steps"),
        ("B_generic", "task-agnostic pseudo-rationale"),
        ("C_task_specific", "short task-specific rationale"),
        ("D_own_complete", "the model's own complete derivation")]
RUNS = [("qwen3-4b-thinking", "ablation_paired_qwen3-4b-thinking_aime"),
        ("qwen3-4b-instruct", "ablation_paired_qwen3-4b-instruct_aime")]
BOOT, SEED = 10000, 0


def per_question(run, condition):
    path = os.path.join(RESULTS, run, "rollouts.jsonl")
    out = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r["condition"] != condition:
                continue
            s = r["samples"]
            out[r["qid"]] = {
                "n_correct": sum(bool(x.get("correct")) for x in s),
                "n_samples": len(s),
                "n_adopted": sum(bool(x.get("adopted")) for x in s),
                "n_trunc": sum(bool(x.get("truncated")) for x in s),
                "tokens": sum(x.get("n_tokens", 0) for x in s),
            }
    return out


def summarize(per_q):
    if not per_q:
        return None
    vals = list(per_q.values())
    tot = sum(v["n_samples"] for v in vals)
    out = {
        "n_questions": len(per_q),
        "correct_count_by_question": {q: v["n_correct"] for q, v in sorted(per_q.items())},
        "samples_by_question": {q: v["n_samples"] for q, v in sorted(per_q.items())},
        "adoption_rate": round(sum(v["n_adopted"] for v in vals) / tot, 4),
        "truncation_rate": round(sum(v["n_trunc"] for v in vals) / tot, 4),
        "mean_gen_tokens": round(sum(v["tokens"] for v in vals) / tot, 1),
    }
    rng = random.Random(SEED)
    for k in (1, 16):
        usable = [v for v in vals if v["n_samples"] >= k]
        if not usable:
            continue
        out[f"pass@{k}"] = round(
            sum(pass_at_k(v["n_samples"], v["n_correct"], k) for v in usable) / len(usable), 4)
        means = []
        for _ in range(BOOT):
            d = [usable[rng.randrange(len(usable))] for _ in range(len(usable))]
            means.append(sum(pass_at_k(v["n_samples"], v["n_correct"], k) for v in d) / len(d))
        means.sort()
        out[f"pass@{k}_ci95"] = [round(means[int(0.025 * BOOT)], 4),
                                 round(means[int(0.975 * BOOT)], 4)]
    return out


def main() -> int:
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    manifest.setdefault("paired_ablation", {})
    manifest["paired_ablation"]["_about"] = (
        "Paired fixed-answer scaffold ablation. Every arm asserts the SAME wrong answer "
        "(the one the model's own wrong rollout reached) on the SAME questions, so "
        "differences isolate the scaffold rather than the conclusion. Intervals are "
        "percentile bootstraps over questions.")

    for model, run in RUNS:
        if not os.path.exists(os.path.join(RESULTS, run, "rollouts.jsonl")):
            print(f"skip {model}: {run} not finished yet")
            continue
        entry = {"run": run, "arms": {}}
        print(f"\n=== {model} ({run}) ===")

        # baseline on exactly the ablation's question set, as a reference line
        qids = set(per_question(run, f"{ARMS[0][0]}:prefix1"))
        base_path = os.path.join(RESULTS, f"base_{model}_aime24_25", "rollouts.jsonl")
        if os.path.exists(base_path) and qids:
            bq = {}
            with open(base_path) as f:
                for line in f:
                    r = json.loads(line)
                    if r["qid"] in qids:
                        sm = r["samples"]
                        bq[r["qid"]] = {
                            "n_correct": sum(bool(x.get("correct")) for x in sm),
                            "n_samples": len(sm), "n_adopted": 0,
                            "n_trunc": sum(bool(x.get("truncated")) for x in sm),
                            "tokens": sum(x.get("n_tokens", 0) for x in sm)}
            entry["baseline"] = summarize(bq)
            bl = entry["baseline"]
            print(f"  baseline on these {bl['n_questions']} questions: "
                  f"pass@1={bl['pass@1']:.3f} pass@16={bl['pass@16']:.3f}")
        for mode, label in (("prefix1", "OPEN (may keep thinking)"),
                            ("full_closed", "FORCED (answer immediately)")):
            print(f"  --- {label} ---")
            print(f"  {'arm':18s} {'n':>3s} {'pass@1':>7s} {'ci95':>16s} "
                  f"{'pass@16':>8s} {'adopt':>7s} {'trunc':>7s} {'tokens':>8s}")
            for arm, desc in ARMS:
                cond = f"{arm}:{mode}"
                st = summarize(per_question(run, cond))
                if not st:
                    continue
                entry["arms"][cond] = st
                ci = st.get("pass@1_ci95", [0, 0])
                warn = ("  <- EXCEEDS TRUNCATION_GATE"
                        if st["truncation_rate"] > TRUNCATION_GATE else "")
                print(f"  {arm:18s} {st['n_questions']:3d} {st['pass@1']:7.3f} "
                      f"[{ci[0]:.3f}, {ci[1]:.3f}] {st['pass@16']:8.3f} "
                      f"{st['adoption_rate']:7.3f} {st['truncation_rate']:7.3f} "
                      f"{st['mean_gen_tokens']:8.0f}{warn}")
        manifest["paired_ablation"][model] = entry

    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nwrote paired_ablation into {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
