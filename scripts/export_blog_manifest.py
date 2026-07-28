"""Export the matched-subset aggregates behind the blog figures to a committable manifest.

Why this exists: the raw rollout dumps are too large to commit, and the per-run
`summary.json` files hold whole-cell aggregates over every question that had a usable
trace. The blog figures instead use *matched subsets* (see below), so neither artifact
lets a reader recheck the published numbers. This script reads the raw rollouts once
and writes `results/blog_manifest.json`, which is small, contains no question text, and
carries per-question correct counts so pass@k and bootstrap intervals can be recomputed.

Matched subset (per model, per dataset):
    questions solved at least once at baseline  AND  having a usable self_wrong trace.
Baseline pass@16 is therefore 1.0 by construction on this subset; that is a property of
the selection rule, not a result.

Usage:
    python scripts/export_blog_manifest.py            # all pairs found under results/
    python scripts/export_blog_manifest.py --check    # also verify figure values match
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics import pass_at_k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(RESULTS, "blog_manifest.json")

# (label, baseline run, injection run) triples the blog draws on
PAIRS = [
    ("qwen3-4b-thinking/aime", "base_qwen3-4b-thinking_aime24_25",
     "inject_qwen3-4b-thinking_aime24_25"),
    ("qwen3-4b-instruct/aime", "base_qwen3-4b-instruct_aime24_25",
     "inject_qwen3-4b-instruct_aime24_25"),
    ("gemma-4-e2b/aime", "base_gemma-4-e2b_aime24_25",
     "inject_gemma-4-e2b_aime24_25"),
    ("qwen3-4b-thinking/maze", "base_qwen3-4b-thinking_rg_maze",
     "inject_qwen3-4b-thinking_rg_maze"),
    ("qwen3-4b-instruct/maze", "base_qwen3-4b-instruct_rg_maze",
     "inject_qwen3-4b-instruct_rg_maze"),
    ("gemma-4-e2b/maze", "base_gemma-4-e2b_rg_maze",
     "inject_gemma-4-e2b_rg_maze"),
]

# cross-domain runs (a trace from a different DOMAIN, e.g. a maze trace inside an AIME
# question). Folded into the same pair so every bar can share one question set.
CROSS = {
    "qwen3-4b-thinking/aime": "inject_qwen3-4b-thinking_aime_cross",
    "gemma-4-e2b/aime": "inject_gemma-4-e2b_aime_cross",
    "qwen3-4b-thinking/maze": "inject_qwen3-4b-thinking_rg_maze_cross",
    "gemma-4-e2b/maze": "inject_gemma-4-e2b_rg_maze_cross",
}

BOOT_ROUNDS = 10000
BOOT_SEED = 0


def read_jsonl(path):
    with open(path) as f:
        for line in f:
            yield json.loads(line)


def baseline_counts(run):
    """qid -> (n_correct, n_samples)."""
    path = os.path.join(RESULTS, run, "rollouts.jsonl")
    out = {}
    for r in read_jsonl(path):
        s = r["samples"]
        out[r["qid"]] = (sum(bool(x.get("correct")) for x in s), len(s))
    return out


def injection_cells(run):
    """condition -> qid -> dict(n_correct, n_samples, n_adopted, n_truncated)."""
    path = os.path.join(RESULTS, run, "rollouts.jsonl")
    cells = defaultdict(dict)
    for r in read_jsonl(path):
        s = r["samples"]
        cells[r["condition"]][r["qid"]] = {
            "n_correct": sum(bool(x.get("correct")) for x in s),
            "n_samples": len(s),
            "n_adopted": sum(bool(x.get("adopted")) for x in s),
            "n_truncated": sum(bool(x.get("truncated")) for x in s),
        }
    return cells


def mean_pass_at_k(per_q, k):
    """Unbiased pass@k averaged over questions; None if no question has n >= k."""
    vals = [pass_at_k(v["n_samples"], v["n_correct"], k)
            for v in per_q.values() if v["n_samples"] >= k]
    return sum(vals) / len(vals) if vals else None


def bootstrap_ci(per_q, k, rounds=BOOT_ROUNDS, seed=BOOT_SEED):
    """Percentile bootstrap over questions (the unit of analysis)."""
    items = [v for v in per_q.values() if v["n_samples"] >= k]
    if len(items) < 2:
        return None
    rng = random.Random(seed)
    n = len(items)
    means = []
    for _ in range(rounds):
        draw = [items[rng.randrange(n)] for _ in range(n)]
        means.append(sum(pass_at_k(d["n_samples"], d["n_correct"], k)
                         for d in draw) / n)
    means.sort()
    return [round(means[int(0.025 * rounds)], 4), round(means[int(0.975 * rounds)], 4)]


def summarize(per_q, ks=(1, 16)):
    tot_s = sum(v["n_samples"] for v in per_q.values())
    block = {
        "n_questions": len(per_q),
        "n_generations": tot_s,
        "correct_count_by_question": {q: v["n_correct"] for q, v in sorted(per_q.items())},
        "samples_by_question": {q: v["n_samples"] for q, v in sorted(per_q.items())},
    }
    for k in ks:
        p = mean_pass_at_k(per_q, k)
        block[f"pass@{k}"] = round(p, 4) if p is not None else None
        ci = bootstrap_ci(per_q, k)
        if ci:
            block[f"pass@{k}_ci95"] = ci
    if tot_s:
        block["adoption_rate"] = round(
            sum(v.get("n_adopted", 0) for v in per_q.values()) / tot_s, 4)
        block["truncation_rate"] = round(
            sum(v.get("n_truncated", 0) for v in per_q.values()) / tot_s, 4)
    return block


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify published figure values against a freshly computed "
                         "manifest WITHOUT writing it (read-only)")
    args = ap.parse_args()

    manifest = {
        "_about": (
            "Matched-subset aggregates behind the blog figures. Matched subset = questions "
            "solved at least once at baseline AND having a usable self_wrong trace, per "
            "model and dataset. Baseline pass@16 is 1.0 by construction on this subset. "
            "pass@k uses the unbiased estimator (Chen et al. 2021) averaged over questions; "
            "intervals are percentile bootstraps over questions."
        ),
        "bootstrap": {"rounds": BOOT_ROUNDS, "seed": BOOT_SEED, "unit": "question"},
        "pairs": {},
    }

    for label, base_run, inj_run in PAIRS:
        bpath = os.path.join(RESULTS, base_run, "rollouts.jsonl")
        ipath = os.path.join(RESULTS, inj_run, "rollouts.jsonl")
        if not (os.path.exists(bpath) and os.path.exists(ipath)):
            print(f"skip {label}: missing raw rollouts (regenerate to include it)")
            continue

        base = baseline_counts(base_run)
        cells = injection_cells(inj_run)
        self_wrong_qids = set()
        for cond, per_q in cells.items():
            if cond.startswith("self_wrong"):
                self_wrong_qids |= set(per_q)
        solvable = {q for q, (c, _) in base.items() if c > 0}
        matched = sorted(solvable & self_wrong_qids)

        entry = {
            "model": base_run.split("_", 1)[1].rsplit("_", 1)[0],
            "source_runs": {"baseline": base_run, "injection": inj_run},
            "max_new_tokens": {
                "open": json.load(open(os.path.join(RESULTS, inj_run, "summary.json")))
                .get("max_new_tokens"),
                "forced": 4096,
            },
            "selection_rule": "solved >=1x at baseline AND has a usable self_wrong trace",
            "matched_question_ids": matched,
            "n_matched": len(matched),
            "n_questions_total": len(base),
            "baseline": summarize({q: {"n_correct": base[q][0], "n_samples": base[q][1]}
                                   for q in matched}),
            "conditions": {},
        }
        mset = set(matched)
        for cond in sorted(cells):
            sub = {q: v for q, v in cells[cond].items() if q in mset}
            if sub:
                entry["conditions"][cond] = summarize(sub)

        # fold in the cross-domain run on the SAME matched subset, so every figure bar
        # can be read off one common question set
        cross_run = CROSS.get(label)
        if cross_run:
            cpath = os.path.join(RESULTS, cross_run, "rollouts.jsonl")
            if os.path.exists(cpath):
                entry["source_runs"]["cross"] = cross_run
                for cond, per_q in injection_cells(cross_run).items():
                    sub = {q: v for q, v in per_q.items() if q in mset}
                    if sub:
                        entry["conditions"][cond] = summarize(sub)

        manifest["pairs"][label] = entry
        print(f"{label:26s} matched n={len(matched):3d} of {len(base):3d}  "
              f"conditions={len(entry['conditions'])}")

    if args.check:
        # read-only: never overwrite a valid committed manifest from a checkout
        # whose raw rollouts are missing (that would silently destroy the artifact)
        print("--check is read-only; not writing the manifest")
    else:
        with open(OUT, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\nwrote {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")

    if args.check:
        print("\n=== figure-value check (blog vs manifest) ===")
        expect = {
            "qwen3-4b-thinking/aime": {
                "baseline": (0.753, 1.000),
                "self_wrong:prefix0.25": (0.655, 1.000),
                "self_wrong:prefix0.5": (0.486, 1.000),
                "self_wrong:prefix0.75": (0.302, 0.913),
                "self_wrong:prefix1": (0.024, 0.043),
            },
            "qwen3-4b-instruct/aime": {
                "baseline": (0.587, 1.000),
                "self_wrong:prefix0.25": (0.536, 0.909),
                "self_wrong:prefix0.5": (0.449, 0.879),
                "self_wrong:prefix0.75": (0.314, 0.636),
                "self_wrong:prefix1": (0.004, 0.030),
            },
        }
        bad = 0
        for label, conds in expect.items():
            e = manifest["pairs"].get(label)
            if not e:
                print(f"  {label}: MISSING from manifest"); bad += 1; continue
            for cond, (p1, p16) in conds.items():
                got = e["baseline"] if cond == "baseline" else e["conditions"].get(cond)
                if not got:
                    print(f"  {label} {cond}: MISSING"); bad += 1; continue
                d1 = abs(got["pass@1"] - p1)
                d16 = abs(got["pass@16"] - p16)
                flag = "ok " if max(d1, d16) < 0.002 else "MISMATCH"
                if flag != "ok ":
                    bad += 1
                print(f"  {flag} {label:24s} {cond:22s} "
                      f"pass@1 {got['pass@1']:.3f} vs {p1:.3f} | "
                      f"pass@16 {got['pass@16']:.3f} vs {p16:.3f} (n={got['n_questions']})")
        print("all figure values reproduce" if bad == 0 else f"{bad} mismatches")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
