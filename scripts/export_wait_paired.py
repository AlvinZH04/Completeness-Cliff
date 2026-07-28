"""Emit the wait-append paired statistics into the manifest.

The fourth review noted that the intervention's sign tests appeared only in prose:
the committed summaries hold whole-cell aggregates, so a clean-clone reader could
not see which questions changed or recompute the p-values. This script writes, for
every arm and budget, the per-question outcome plus the paired comparison against
the unchanged control, including the gained and lost question ids.

    python scripts/export_wait_paired.py
"""

from __future__ import annotations

import json
import os
import sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics import pass_at_k  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MANIFEST = os.path.join(RESULTS, "blog_manifest.json")

ARMS = ["W0_unchanged", "W1_wait", "W2_neutral", "W3_recheck"]
RUNS = [
    ("thinking_16k", "waitappend_qwen3-4b-thinking_aime"),
    ("thinking_n64", "waitappend_n64_qwen3-4b-thinking_aime"),
    ("instruct_16k", "waitappend_qwen3-4b-instruct_aime"),
    ("instruct_32k", "waitappend_qwen3-4b-instruct_aime_32k"),
]
CONTROL = "W0_unchanged"


def per_question(run, cond):
    out = {}
    path = os.path.join(RESULTS, run, "rollouts.jsonl")
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["condition"] != cond:
                continue
            s = r["samples"]
            out[r["qid"]] = {
                "n_correct": sum(bool(x.get("correct")) for x in s),
                "n_samples": len(s),
                "n_truncated": sum(bool(x.get("truncated")) for x in s),
            }
    return out


def sign_test(gained: int, lost: int) -> dict:
    n = gained + lost
    if n == 0:
        return {"n_discordant": 0, "one_sided_p": 1.0, "two_sided_p": 1.0}
    one = sum(comb(n, i) for i in range(max(gained, lost), n + 1)) / 2 ** n
    return {"n_discordant": n, "one_sided_p": round(one, 6),
            "two_sided_p": round(min(1.0, 2 * one), 6)}


def main() -> int:
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    block = {"_about": (
        "Per-question outcomes and paired sign tests for the wait-append intervention. "
        "'solved' means at least one of the question's samples was correct, which is the "
        "unit the paired test uses. Sign tests are directional (pre-specified: the "
        "intervention should not reduce recovery); both one- and two-sided values are "
        "given. Gained/lost question ids are listed so the tests are reconstructible "
        "without the raw rollouts.")}

    for tag, run in RUNS:
        if not os.path.exists(os.path.join(RESULTS, run, "rollouts.jsonl")):
            print(f"skip {tag}: no rollouts")
            continue
        ctrl = per_question(run, f"{CONTROL}:prefix1")
        entry = {"run": run, "arms": {}}
        print(f"=== {tag} ({run}) ===")
        for arm in ARMS:
            pq = per_question(run, f"{arm}:prefix1")
            if not pq:
                continue
            a = {
                "n_questions": len(pq),
                "solved_by_question": {q: (v["n_correct"] > 0) for q, v in sorted(pq.items())},
                "correct_count_by_question": {q: v["n_correct"] for q, v in sorted(pq.items())},
                "samples_by_question": {q: v["n_samples"] for q, v in sorted(pq.items())},
                "truncated_by_question": {q: v["n_truncated"] for q, v in sorted(pq.items())},
                "pass@1": round(sum(pass_at_k(v["n_samples"], v["n_correct"], 1)
                                    for v in pq.values()) / len(pq), 4),
                "pass@16": round(sum(pass_at_k(v["n_samples"], v["n_correct"], 16)
                                     for v in pq.values()) / len(pq), 4),
                "n_solved": sum(1 for v in pq.values() if v["n_correct"] > 0),
            }
            if arm != CONTROL:
                gained = sorted(q for q in pq
                                if pq[q]["n_correct"] > 0 and ctrl.get(q, {}).get("n_correct", 0) == 0)
                lost = sorted(q for q in ctrl
                              if ctrl[q]["n_correct"] > 0 and pq.get(q, {}).get("n_correct", 0) == 0)
                a["paired_vs_" + CONTROL] = {
                    "gained_question_ids": gained, "lost_question_ids": lost,
                    "n_gained": len(gained), "n_lost": len(lost),
                    **sign_test(len(gained), len(lost)),
                }
                t = a["paired_vs_" + CONTROL]
                print(f"  {arm:14s} pass@16={a['pass@16']:.3f}  {t['n_gained']} gained / "
                      f"{t['n_lost']} lost  one-sided p={t['one_sided_p']:.4f}  "
                      f"two-sided p={t['two_sided_p']:.4f}")
            else:
                print(f"  {arm:14s} pass@16={a['pass@16']:.3f}  (control)")
            entry["arms"][arm] = a
        block[tag] = entry
        print()

    manifest["wait_append_paired"] = block
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"wrote wait_append_paired into {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
