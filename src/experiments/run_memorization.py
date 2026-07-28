"""Memorization / contamination probes for the AIME question set.

Motivation: under a COMPLETE own-wrong trace the thinking model recovers on exactly
one question (aime25-18, 14/16), and its continuations say things like "I recall the
answer is 82". If that escape is recall rather than reasoning, the question should
look memorized on probes that never let the model derive anything.

Two probes, both cheap:

  answer_noreason : force an immediate answer with the thinking channel closed and no
                    room to work. Accuracy here cannot come from derivation, so a high
                    score means the answer is retrievable, not computed.

  prefix_complete : hand the model the first `--prefix-frac` of the raw problem text
                    with NO chat template and let it continue greedily. Overlap with
                    the true remainder measures whether the problem statement itself
                    was in training data (verbatim recall of the question, which is
                    the cleanest contamination signal available without the corpus).

Comparing AIME 2024 against AIME 2025 gives a built-in control: a training-cutoff
effect should show up as higher scores on the older year.

    python -m src.experiments.run_memorization --model qwen3-4b-thinking
"""

import argparse
import difflib
import json
import os

from .. import data as data_mod
from ..config import MODELS, RESULTS_DIR
from ..generation import Engine, build_injection_prompt
from ..grading import extract_answer, grade

MATH_FORCED_TRANSITION = "\n\nTherefore, the final answer is $\\boxed{"


def overlap(generated: str, truth: str) -> dict:
    """How much of the true remainder did the model reproduce?"""
    gen = " ".join(generated.split())
    tru = " ".join(truth.split())
    if not tru:
        return {"ratio": 0.0, "longest_match_chars": 0, "longest_match_frac": 0.0}
    window = gen[:max(len(tru), 1)]
    sm = difflib.SequenceMatcher(None, window, tru, autojunk=False)
    m = sm.find_longest_match(0, len(window), 0, len(tru))
    return {"ratio": round(sm.ratio(), 4),
            "longest_match_chars": m.size,
            "longest_match_frac": round(m.size / len(tru), 4)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--dataset", default="aime24_25",
                    choices=sorted(data_mod.DATASETS))
    ap.add_argument("--n-samples", type=int, default=16)
    ap.add_argument("--prefix-frac", type=float, default=0.4)
    ap.add_argument("--max-model-len", type=int, default=None)
    ap.add_argument("--gpu-mem", type=float, default=0.9)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--run-name", default=None)
    args = ap.parse_args()

    cfg = MODELS[args.model]
    is_thinking = cfg.style == "thinking"
    records = data_mod.load(args.dataset)
    run_name = args.run_name or f"memorization_{args.model}_{args.dataset}"
    out_dir = RESULTS_DIR / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = Engine(cfg, max_model_len=args.max_model_len,
                    gpu_memory_utilization=args.gpu_mem, seed=args.seed)

    # ---------------------------------------------------------- probe 1
    prompts = []
    for r in records:
        # instruct: the transition is prefilled into the response. thinking: the think
        # block is closed first, then the same transition is appended, so both model
        # types are forced to emit a boxed answer immediately with no room to derive.
        trace = "" if is_thinking else MATH_FORCED_TRANSITION
        pr = build_injection_prompt(engine.tokenizer, cfg, data_mod.user_prompt(r),
                                    trace, close_think=True, thinking_mode=is_thinking)
        if is_thinking:
            pr = pr + MATH_FORCED_TRANSITION
        prompts.append(pr)
    print(f"[{run_name}] probe 1: forced immediate answer, {len(prompts)} questions "
          f"x {args.n_samples}", flush=True)
    gens1 = engine.generate(prompts, n=args.n_samples, max_new_tokens=256,
                            sampling=cfg.sampling, seed=args.seed)

    # ---------------------------------------------------------- probe 2
    raw_prefixes, remainders = [], []
    for r in records:
        q = r["question"].strip()
        cut = max(1, int(len(q) * args.prefix_frac))
        raw_prefixes.append(q[:cut])
        remainders.append(q[cut:])
    print(f"[{run_name}] probe 2: raw prefix completion at {args.prefix_frac:.0%}, greedy",
          flush=True)

    class _Greedy:
        temperature, top_p, top_k, min_p, presence_penalty = 0.0, 1.0, -1, 0.0, 0.0
    gens2 = engine.generate(raw_prefixes, n=1, max_new_tokens=256,
                            sampling=_Greedy(), seed=args.seed)

    # ---------------------------------------------------------- score
    rows = []
    for r, g1, pref, rem, g2 in zip(records, gens1, raw_prefixes, remainders, gens2):
        n_correct = 0
        answers = []
        for s in g1:
            pred = extract_answer(MATH_FORCED_TRANSITION + s.text, r["kind"])
            answers.append(pred)
            if pred is not None and grade(pred, r):
                n_correct += 1
        ov = overlap(g2[0].text, rem)
        rows.append({
            "qid": r["qid"], "dataset": r["dataset"], "gold": r["gold"],
            "noreason_correct": n_correct, "noreason_n": len(g1),
            "noreason_acc": round(n_correct / len(g1), 4),
            "noreason_answers": answers,
            "noreason_raw_sample": g1[0].text[:300],
            "prefix_frac": args.prefix_frac,
            "prefix_overlap": ov,
            "prefix_continuation": g2[0].text[:600],
        })

    with open(out_dir / "memorization.jsonl", "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_year = {}
    for row in rows:
        by_year.setdefault(row["dataset"], []).append(row)
    summary = {"run_name": run_name, "model": args.model, "hf_id": cfg.hf_id,
               "n_questions": len(rows), "n_samples": args.n_samples,
               "prefix_frac": args.prefix_frac, "by_dataset": {}}
    for ds, rs in sorted(by_year.items()):
        summary["by_dataset"][ds] = {
            "n": len(rs),
            "mean_noreason_acc": round(sum(x["noreason_acc"] for x in rs) / len(rs), 4),
            "n_solved_noreason": sum(1 for x in rs if x["noreason_correct"] > 0),
            "mean_prefix_ratio": round(
                sum(x["prefix_overlap"]["ratio"] for x in rs) / len(rs), 4),
            "mean_longest_match_frac": round(
                sum(x["prefix_overlap"]["longest_match_frac"] for x in rs) / len(rs), 4),
        }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary["by_dataset"], indent=2))
    top = sorted(rows, key=lambda x: (-x["noreason_acc"],
                                      -x["prefix_overlap"]["longest_match_frac"]))[:8]
    print("\nmost-memorized-looking questions (by no-reasoning accuracy):")
    for x in top:
        print(f"  {x['qid']:22s} noreason={x['noreason_acc']:.2f} "
              f"prefix_ratio={x['prefix_overlap']['ratio']:.3f} "
              f"longest={x['prefix_overlap']['longest_match_frac']:.3f}")
    print(f"\nwrote {out_dir}")


if __name__ == "__main__":
    main()
