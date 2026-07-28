"""Audit whether the 32k reruns are sample-aligned with the 16k runs.

The fourth review asked for a per-sample 16k-to-32k transition analysis, which
requires that sample i of the 32k run be the same trajectory as sample i of the 16k
run (identical when it terminated under the smaller cap, an extension when it did
not). That assumption has to be tested rather than assumed, because vLLM is not
bitwise reproducible when the memory configuration changes: the reruns raised
max_model_len from 49,152 to 81,920 along with the cap, which changes KV-cache block
allocation and batch composition, and tiny numerical differences compound over long
generations.

This script measures, per arm:
  * among samples that terminated at 16k, how many are byte-identical at 32k;
  * among samples truncated at 16k, how many 32k outputs extend the 16k prefix;
  * the aligned subset's outcome transitions, where alignment holds.

    python scripts/budget_alignment_audit.py
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MANIFEST = os.path.join(RESULTS, "blog_manifest.json")

PAIRS = [
    ("intervention", "waitappend_qwen3-4b-instruct_aime",
     "waitappend_qwen3-4b-instruct_aime_32k",
     ["W0_unchanged", "W1_wait", "W2_neutral", "W3_recheck"]),
    ("ablation", "ablation_paired_qwen3-4b-instruct_aime",
     "ablation_paired_qwen3-4b-instruct_aime_32k",
     ["A_answer_only", "B_generic", "C_task_specific", "D_own_complete"]),
]
# a truncated 16k text is treated as extended if the 32k text reproduces it up to a
# small tail tolerance (the final tokens can differ where the cap fell mid-token)
TAIL_TOLERANCE = 50


def load(run, cond):
    out = {}
    with open(os.path.join(RESULTS, run, "rollouts.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["condition"] == cond:
                out[r["qid"]] = r["samples"]
    return out


def main() -> int:
    block = {"_about": (
        "Sample-level alignment between the 16k runs and the 32k reruns. vLLM is not "
        "bitwise reproducible across a max_model_len change even at a fixed seed, so the "
        "reruns are only partially paired with the originals. Alignment degrades with "
        "generation length, which means the longest-generating arms are effectively fresh "
        "draws rather than continuations. A per-sample transition analysis is therefore "
        "only valid on the aligned subset, whose size is reported here."),
        "tail_tolerance_chars": TAIL_TOLERANCE, "pairs": {}}

    for label, r16, r32, arms in PAIRS:
        if not all(os.path.exists(os.path.join(RESULTS, r, "rollouts.jsonl"))
                   for r in (r16, r32)):
            print(f"skip {label}: missing rollouts")
            continue
        print(f"=== {label}: {r16}  vs  {r32} ===")
        print(f"  {'arm':16s} {'terminated@16k identical':>26s} {'truncated@16k extended':>24s}"
              f" {'transitions on aligned pairs':>30s}")
        entry = {}
        for arm in arms:
            a, b = load(r16, f"{arm}:prefix1"), load(r32, f"{arm}:prefix1")
            ident = identn = ext = extn = 0
            cc = cw = wc = ww = 0          # correct/wrong transitions on aligned pairs
            for q in sorted(set(a) & set(b)):
                for s16, s32 in zip(a[q], b[q]):
                    t16, t32 = s16.get("text", ""), s32.get("text", "")
                    aligned = False
                    if s16.get("truncated"):
                        extn += 1
                        if t32.startswith(t16[:max(0, len(t16) - TAIL_TOLERANCE)]):
                            ext += 1
                            aligned = True
                    else:
                        identn += 1
                        if t16 == t32:
                            ident += 1
                            aligned = True
                    if aligned:
                        o, n = bool(s16.get("correct")), bool(s32.get("correct"))
                        cc += o and n; cw += o and not n
                        wc += (not o) and n; ww += (not o) and (not n)
            entry[arm] = {
                "terminated_at_16k": identn, "identical_at_32k": ident,
                "identical_rate": round(ident / identn, 4) if identn else None,
                "truncated_at_16k": extn, "extended_at_32k": ext,
                "extended_rate": round(ext / extn, 4) if extn else None,
                "aligned_transitions": {"correct_to_correct": cc, "correct_to_wrong": cw,
                                        "wrong_to_correct": wc, "wrong_to_wrong": ww},
            }
            print(f"  {arm:16s} {ident:>9d}/{identn:<7d} ({ident/max(identn,1):5.1%}) "
                  f"{ext:>8d}/{extn:<6d} ({ext/max(extn,1):5.1%})"
                  f"   c>c {cc} c>w {cw} w>c {wc} w>w {ww}")
        block["pairs"][label] = {"run_16k": r16, "run_32k": r32, "arms": entry}
        print()

    m = json.load(open(MANIFEST, encoding="utf-8"))
    m["budget_alignment"] = block
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)
    print(f"wrote budget_alignment into {MANIFEST}")
    print("\nNOTE: where alignment is low the 32k run is a fresh draw, not a continuation,")
    print("so its agreement with the 16k aggregates is closer to a re-sample check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
