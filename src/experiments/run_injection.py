"""Phase 2+: wrong-trace injection conditions, driven by a baseline run.

Example:
    python -m src.experiments.run_injection --model qwen3-4b-thinking \
        --baseline results/base_qwen3-4b-thinking_aime/rollouts.jsonl \
        --sources self_wrong irrelevant corrupted wrong_conclusion \
        --fractions 0.25 0.5 0.75 1.0 --n-samples 16 --max-new-tokens 81920
"""

import argparse
import json
import os
import time
from collections import defaultdict

from .. import data as data_mod
from ..config import ANSWER_ONLY_MAX_TOKENS, MODELS, RESULTS_DIR, TRUNCATION_GATE
from ..generation import Engine, build_injection_prompt
from ..grading import (answers_match, count_correction_markers, extract_answer,
                       extract_boxed, grade, split_channels)
from ..metrics import aggregate
from ..traces import TraceBank, build_conditions, condition_name

MATH_FORCED_TRANSITION = "\n\nTherefore, the final answer is $\\boxed{"
RG_FORCED_TRANSITION = "\n\nTherefore, my final answer is:\n<answer>"


def strip_answer_statement(text: str, kind: str) -> str:
    """Remove the final-answer statement from an instruct response so the
    remaining text is injectable reasoning."""
    marker = "\\boxed{" if kind == "math" else "<answer>"
    idx = text.rfind(marker)
    if idx == -1:
        return text.strip()
    # drop the line containing the final answer
    line_start = text.rfind("\n", 0, idx)
    return text[:line_start if line_start != -1 else idx].strip()


def extract_forced(generated: str, kind: str) -> str | None:
    """Answer for instruct 'forced' conditions where the prompt already opened
    the answer expression."""
    if kind == "math":
        # The prompt already emitted "\boxed{", so rebuild it and reuse the
        # balanced-brace extractor: a bare find("}") would cut \frac{1}{2} short.
        pred = extract_boxed("\\boxed{" + generated)
        if pred is None:
            end = generated.find("}")
            pred = generated[:end if end != -1 else None]
        return pred.strip().strip("$ ") or None
    end = generated.find("</answer>")
    pred = generated[:end if end != -1 else None].strip()
    return pred or None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--baseline", required=True,
                    help="path to baseline rollouts.jsonl (trace source + question set)")
    ap.add_argument("--sources", nargs="+", default=["self_wrong"],
                    choices=["self_wrong", "irrelevant", "corrupted",
                             "wrong_conclusion", "irrelevant_cross",
                             "paired_fixed", "wait_append"])
    ap.add_argument("--cross-baseline", default=None,
                    help="rollouts.jsonl of a DIFFERENT dataset; donor pool for irrelevant_cross")
    ap.add_argument("--fractions", nargs="+", type=float, default=[0.25, 0.5, 0.75, 1.0])
    ap.add_argument("--no-full-closed", action="store_true")
    ap.add_argument("--n-samples", type=int, default=16)
    ap.add_argument("--max-new-tokens", type=int, default=None)
    ap.add_argument("--max-model-len", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-thinking", action="store_true")
    ap.add_argument("--gpu-mem", type=float, default=0.9)
    ap.add_argument("--enforce-eager", action="store_true")
    ap.add_argument("--attention-backend",
                    default=os.environ.get("WR_ATTN_BACKEND"),
                    help="e.g. TRITON_ATTN when flash-attn kernels lack this arch")
    ap.add_argument("--forced-max-tokens", type=int, default=None,
                    help="token budget for forced-answer cells (default: config value)")
    ap.add_argument("--run-name", default=None)
    args = ap.parse_args()

    cfg = MODELS[args.model]
    thinking_mode = not args.no_thinking
    is_thinking = cfg.style == "thinking" or (cfg.style == "hybrid" and thinking_mode)
    max_new = args.max_new_tokens or cfg.default_max_new_tokens
    sampling = (cfg.sampling_nothink
                if (cfg.style == "hybrid" and not thinking_mode and cfg.sampling_nothink)
                else cfg.sampling)

    with open(args.baseline) as f:
        baseline_rows = [json.loads(line) for line in f]
    records = [{k: row[k] for k in
                ("qid", "dataset", "kind", "question", "gold", "rg_task", "rg_entry")}
               for row in baseline_rows]
    rec_by_qid = {r["qid"]: r for r in records}

    run_name = args.run_name or (
        f"inject_{args.model}{'' if thinking_mode else '-nothink'}"
        f"_{records[0]['dataset']}_{'-'.join(args.sources)}")
    out_dir = RESULTS_DIR / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = Engine(cfg, max_model_len=args.max_model_len,
                    gpu_memory_utilization=args.gpu_mem, seed=args.seed,
                    enforce_eager=args.enforce_eager,
                    attention_backend=args.attention_backend)

    if is_thinking:
        trace_field = "thinking"
    else:
        trace_field = "inj_trace"
        for row in baseline_rows:
            for s in row["samples"]:
                s["inj_trace"] = strip_answer_statement(s.get("final") or "",
                                                        row["kind"])

    bank = TraceBank(baseline_rows, trace_field=trace_field, seed=args.seed)
    if args.cross_baseline:
        with open(args.cross_baseline) as f:
            cross_rows = [json.loads(line) for line in f]
        if not is_thinking:
            for row in cross_rows:
                for s in row["samples"]:
                    s["inj_trace"] = strip_answer_statement(s.get("final") or "",
                                                            row["kind"])
        bank.add_cross_rows(cross_rows, trace_field=trace_field)
    conds = build_conditions(records, bank, engine.tokenizer, sources=args.sources,
                             fractions=args.fractions,
                             include_full_closed=not args.no_full_closed,
                             seed=args.seed)
    if not conds:
        raise SystemExit("no injection conditions could be built (empty trace bank?)")

    by_cell = defaultdict(list)
    for c in conds:
        by_cell[condition_name(c)].append(c)
    print(f"[{run_name}] {len(conds)} (question x condition) items across "
          f"{len(by_cell)} cells: "
          f"{ {k: len(v) for k, v in sorted(by_cell.items())} }", flush=True)

    for c in conds:
        rec = rec_by_qid[c["qid"]]
        trace = c["trace_text"]
        forced = False
        if not is_thinking and c["close_think"]:
            trace = trace + (MATH_FORCED_TRANSITION if rec["kind"] == "math"
                             else RG_FORCED_TRANSITION)
            forced = True
        c["forced_answer_open"] = forced
        c["prompt"] = build_injection_prompt(
            engine.tokenizer, cfg, data_mod.user_prompt(rec), trace,
            close_think=c["close_think"], thinking_mode=thinking_mode)

    forced_answer_prefill = any(c.get("forced_answer_open") for c in conds)

    # closed/forced conditions only need an answer; open ones may think at length
    open_conds = [c for c in conds if not c["close_think"]]
    closed_conds = [c for c in conds if c["close_think"]]
    t0 = time.time()
    forced_budget = args.forced_max_tokens or ANSWER_ONLY_MAX_TOKENS
    # Stop as soon as the answer expression closes: without this, forced cells ramble
    # to the cap and a large share emit no extractable answer at all (findings.md C6).
    forced_stop = ["}$", "}\n", "</answer>"] if forced_answer_prefill else None
    for group, budget, stop in ((open_conds, max_new, None),
                                (closed_conds, forced_budget, forced_stop)):
        if not group:
            continue
        gens = engine.generate([c["prompt"] for c in group], n=args.n_samples,
                               max_new_tokens=budget, sampling=sampling,
                               seed=args.seed, stop=stop)
        for c, samples in zip(group, gens):
            c["gens"] = samples
    print(f"generation took {time.time() - t0:.0f}s", flush=True)

    rows = []
    cell_qstats = defaultdict(list)
    for c in conds:
        rec = rec_by_qid[c["qid"]]
        srows = []
        for s in c["gens"]:
            truncated = s.finish_reason == "length"
            if c["forced_answer_open"]:
                think, final, ans = "", s.text, extract_forced(s.text, rec["kind"])
            else:
                think, final = split_channels(
                    s.text, think_open_in_prompt=is_thinking,
                    think_closed_in_prompt=c["close_think"],
                    think_close=cfg.think_close)
                ans = extract_answer(final, rec["kind"])
            correct = grade(ans, rec)
            adopted = answers_match(ans, c["trace_answer"], rec["kind"])
            srows.append({
                "text": s.text, "n_tokens": s.n_tokens,
                "finish_reason": s.finish_reason, "truncated": truncated,
                "thinking": think, "final": final, "answer": ans,
                "correct": correct, "adopted": adopted, "no_answer": ans is None,
                "markers": count_correction_markers(think),
                "think_tokens": len(engine.tokenizer.encode(
                    think, add_special_tokens=False)) if think else 0,
            })
        cell = condition_name(c)
        rows.append({
            "qid": c["qid"], "dataset": rec["dataset"], "kind": rec["kind"],
            "gold": rec["gold"], "condition": cell, "source": c["source"],
            "fraction": c["fraction"], "close_think": c["close_think"],
            "donor_qid": c["donor_qid"], "trace_answer": c["trace_answer"],
            "trace_text": c["trace_text"], "samples": srows,
        })
        cell_qstats[cell].append({
            "n": len(srows),
            "correct": sum(s["correct"] for s in srows),
            "adopted": sum(s["adopted"] for s in srows),
            "no_answer": sum(s["no_answer"] for s in srows),
            "truncated": sum(s["truncated"] for s in srows),
            "gen_tokens": [s["n_tokens"] for s in srows],
        })

    with open(out_dir / "rollouts.jsonl", "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    cell_metrics = {cell: aggregate(qs) for cell, qs in sorted(cell_qstats.items())}
    summary = {
        "run_name": run_name, "phase": "injection",
        "model": args.model, "hf_id": cfg.hf_id, "thinking_mode": thinking_mode,
        "baseline": args.baseline, "sources": args.sources,
        "fractions": args.fractions, "n_samples": args.n_samples,
        "max_new_tokens": max_new, "max_model_len": args.max_model_len,
        "forced_max_tokens": forced_budget,
        "sampling": vars(sampling), "seed": args.seed,
        "cells": cell_metrics,
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    for cell, m in cell_metrics.items():
        flag = (" TRUNC!" if m["truncation_rate"] > TRUNCATION_GATE else "")
        print(f"{cell:36s} nq={m['n_questions']:3d} pass@1={m.get('pass@1', 0):.3f} "
              f"adopt={m['adoption_rate']:.3f} noans={m['no_answer_rate']:.3f} "
              f"trunc={m['truncation_rate']:.3f}{flag}", flush=True)
    print(f"done -> {out_dir}", flush=True)


if __name__ == "__main__":
    main()
