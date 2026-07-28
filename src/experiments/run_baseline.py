"""Phase 1: baseline pass@k rollouts (also harvests traces for injection).

Example:
    python -m src.experiments.run_baseline --model qwen3-4b-thinking \
        --dataset aime24_25 --n-samples 16 --max-new-tokens 81920 \
        --run-name base_qwen3-4b-thinking_aime
"""

import argparse
import json
import os
import time

from .. import data as data_mod
from ..config import MODELS, RESULTS_DIR, TRUNCATION_GATE
from ..generation import Engine, ensure_think_open, render_base_prompt
from ..grading import (count_correction_markers, extract_answer, grade,
                       split_channels)
from ..metrics import aggregate


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(MODELS))
    ap.add_argument("--dataset", required=True, choices=sorted(data_mod.DATASETS))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--n-samples", type=int, default=16)
    ap.add_argument("--max-new-tokens", type=int, default=None)
    ap.add_argument("--max-model-len", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-thinking", action="store_true",
                    help="hybrid models: run in non-thinking mode")
    ap.add_argument("--gpu-mem", type=float, default=0.9)
    ap.add_argument("--enforce-eager", action="store_true")
    ap.add_argument("--attention-backend",
                    default=os.environ.get("WR_ATTN_BACKEND"),
                    help="e.g. TRITON_ATTN when flash-attn kernels lack this arch")
    ap.add_argument("--run-name", default=None)
    args = ap.parse_args()

    cfg = MODELS[args.model]
    thinking_mode = not args.no_thinking
    is_thinking = cfg.style == "thinking" or (cfg.style == "hybrid" and thinking_mode)
    max_new = args.max_new_tokens or cfg.default_max_new_tokens
    sampling = (cfg.sampling_nothink
                if (cfg.style == "hybrid" and not thinking_mode and cfg.sampling_nothink)
                else cfg.sampling)

    run_name = args.run_name or (
        f"base_{args.model}{'' if thinking_mode else '-nothink'}_{args.dataset}")
    out_dir = RESULTS_DIR / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    records = data_mod.load(args.dataset, limit=args.limit)
    print(f"[{run_name}] {len(records)} questions, n={args.n_samples}, "
          f"max_new_tokens={max_new}", flush=True)

    engine = Engine(cfg, max_model_len=args.max_model_len,
                    gpu_memory_utilization=args.gpu_mem, seed=args.seed,
                    enforce_eager=args.enforce_eager,
                    attention_backend=args.attention_backend)

    prompts = []
    for r in records:
        p = render_base_prompt(engine.tokenizer, cfg, data_mod.user_prompt(r),
                               enable_thinking=thinking_mode)
        if is_thinking:
            p = ensure_think_open(p, cfg)
        prompts.append(p)

    t0 = time.time()
    gens = engine.generate(prompts, n=args.n_samples, max_new_tokens=max_new,
                           sampling=sampling, seed=args.seed)
    print(f"generation took {time.time() - t0:.0f}s", flush=True)

    rows, qstats = [], []
    for r, samples in zip(records, gens):
        srows = []
        for s in samples:
            truncated = s.finish_reason == "length"
            think, final = split_channels(s.text, think_open_in_prompt=is_thinking,
                                          think_closed_in_prompt=False,
                                          think_close=cfg.think_close)
            ans = extract_answer(final, r["kind"])
            correct = grade(ans, r)
            srows.append({
                "text": s.text, "n_tokens": s.n_tokens,
                "finish_reason": s.finish_reason, "truncated": truncated,
                "thinking": think, "final": final, "answer": ans,
                "correct": correct, "no_answer": ans is None,
                "markers": count_correction_markers(think),
            })
        rows.append({**r, "samples": srows})
        qstats.append({
            "n": len(srows),
            "correct": sum(s["correct"] for s in srows),
            "adopted": 0,
            "no_answer": sum(s["no_answer"] for s in srows),
            "truncated": sum(s["truncated"] for s in srows),
            "gen_tokens": [s["n_tokens"] for s in srows],
        })

    with open(out_dir / "rollouts.jsonl", "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    summary = {
        "run_name": run_name, "phase": "baseline",
        "model": args.model, "hf_id": cfg.hf_id, "thinking_mode": thinking_mode,
        "dataset": args.dataset, "n_questions": len(records),
        "n_samples": args.n_samples, "max_new_tokens": max_new,
        "sampling": vars(sampling), "seed": args.seed,
        "metrics": aggregate(qstats),
        "wrong_trace_coverage": sum(
            1 for row in rows if any(
                (not s["correct"]) and s["answer"] is not None and not s["truncated"]
                for s in row["samples"])) / len(rows),
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    m = summary["metrics"]
    print(json.dumps(m, indent=2), flush=True)
    if m["truncation_rate"] > TRUNCATION_GATE:
        print(f"WARNING: truncation rate {m['truncation_rate']:.1%} exceeds "
              f"{TRUNCATION_GATE:.0%} gate — consider raising --max-new-tokens",
              flush=True)
    print(f"done -> {out_dir}", flush=True)


if __name__ == "__main__":
    main()
