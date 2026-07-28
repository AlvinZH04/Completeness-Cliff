"""Cross-model comparison on a COMMON question set (review item: "add a common-question
analysis for direct model comparisons").

Figure 1 compares Qwen3-4B-Thinking on its 23-question matched subset against
Qwen3-4B-Instruct on its 33-question subset. Those are different questions, so the two
curves are not strictly comparable. This script recomputes both models on the
intersection of their matched subsets, straight from results/blog_manifest.json (the
per-question correct counts are already there, so no raw rollouts are needed).

Writes the result back into the manifest under "common_subsets" and prints a table.

    python scripts/common_subset_analysis.py
"""

from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics import pass_at_k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(ROOT, "results", "blog_manifest.json")

PAIRINGS = [
    ("aime", "qwen3-4b-thinking/aime", "qwen3-4b-instruct/aime"),
    ("maze", "qwen3-4b-thinking/maze", "qwen3-4b-instruct/maze"),
]
CONDS = ["baseline", "self_wrong:prefix0.25", "self_wrong:prefix0.5",
         "self_wrong:prefix0.75", "self_wrong:prefix1"]
BOOT_ROUNDS, BOOT_SEED = 10000, 0


def block(entry, cond):
    return entry["baseline"] if cond == "baseline" else entry["conditions"].get(cond)


def restrict(entry, cond, qids):
    """Per-question (n_correct, n_samples) for `cond`, restricted to `qids`."""
    b = block(entry, cond)
    if not b:
        return None
    cc, ns = b["correct_count_by_question"], b["samples_by_question"]
    return {q: (cc[q], ns[q]) for q in qids if q in cc}


def stats(per_q, ks=(1, 16)):
    out = {"n_questions": len(per_q)}
    rng = random.Random(BOOT_SEED)
    items = list(per_q.values())
    for k in ks:
        usable = [(c, n) for c, n in items if n >= k]
        if not usable:
            out[f"pass@{k}"] = None
            continue
        out[f"pass@{k}"] = round(sum(pass_at_k(n, c, k) for c, n in usable) / len(usable), 4)
        if len(usable) > 1:
            means = []
            for _ in range(BOOT_ROUNDS):
                draw = [usable[rng.randrange(len(usable))] for _ in range(len(usable))]
                means.append(sum(pass_at_k(n, c, k) for c, n in draw) / len(draw))
            means.sort()
            out[f"pass@{k}_ci95"] = [round(means[int(0.025 * BOOT_ROUNDS)], 4),
                                     round(means[int(0.975 * BOOT_ROUNDS)], 4)]
    return out


def main() -> int:
    m = json.load(open(MANIFEST_PATH))
    m.setdefault("common_subsets", {})

    for tag, a_label, b_label in PAIRINGS:
        a, b = m["pairs"].get(a_label), m["pairs"].get(b_label)
        if not (a and b):
            print(f"skip {tag}: missing a pair")
            continue
        common = sorted(set(a["matched_question_ids"]) & set(b["matched_question_ids"]))
        print(f"\n=== {tag}: common question set ===")
        print(f"  {a_label}: n={a['n_matched']}   {b_label}: n={b['n_matched']}   "
              f"intersection: n={len(common)}")
        if not common:
            continue

        entry = {
            "models": [a_label, b_label],
            "rule": ("intersection of the two models' matched subsets: solved at least once at "
                     "baseline by BOTH models and having a usable self_wrong trace for BOTH"),
            "question_ids": common,
            "n_common": len(common),
            "by_model": {},
        }
        print(f"\n  {'condition':24s} {'thinking p@1':>13s} {'p@16':>16s} | "
              f"{'instruct p@1':>13s} {'p@16':>16s}")
        rows = {}
        for label, e in ((a_label, a), (b_label, b)):
            rows[label] = {}
            for cond in CONDS:
                sub = restrict(e, cond, common)
                if sub:
                    rows[label][cond] = stats(sub)
            entry["by_model"][label] = rows[label]

        for cond in CONDS:
            ra, rb = rows[a_label].get(cond), rows[b_label].get(cond)
            if not (ra and rb):
                continue
            fa = f"{ra['pass@16']:.3f} {ra.get('pass@16_ci95', '')}"
            fb = f"{rb['pass@16']:.3f} {rb.get('pass@16_ci95', '')}"
            print(f"  {cond:24s} {ra['pass@1']:13.3f} {fa:>16s} | "
                  f"{rb['pass@1']:13.3f} {fb:>16s}")

        m["common_subsets"][tag] = entry

    with open(MANIFEST_PATH, "w") as f:
        json.dump(m, f, indent=2)
    print(f"\nwrote common_subsets into {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
