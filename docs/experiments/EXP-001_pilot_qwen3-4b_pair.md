# EXP-001: Pilot — wrong-trace injection, Qwen3-4B 2507 pair, AIME + reasoning_gym

- **Date:** 2026-07-16/17
- **Author:** Claude (autonomous session) with user-approved design
- **Status:** running
- **Results dir:** `results/{base,inject}_qwen3-4b-{thinking,instruct}_{aime24_25,rg_maze,rg_mini_sudoku}/`
- **Log:** `logs/pilot_gpu0.log`, `logs/pilot_gpu1.log`

## Goal

RQ1–RQ4 first pass: how much does injected wrong thinking hurt pass@k; prefix-fraction dose-response; open vs force-closed think block; thinking vs instruct model; wrongness type.

## Setup

| Field | Value |
|-------|-------|
| Models | qwen3-4b-thinking (Qwen3-4B-Thinking-2507), qwen3-4b-instruct (Qwen3-4B-Instruct-2507) |
| Datasets | aime24_25 (60 qs), rg_maze (50 qs, seed 20260716), rg_mini_sudoku (50 qs, bonus) |
| Conditions | baseline; {self_wrong, irrelevant} × prefix{.25,.5,.75,1} + full_closed; corrupted × prefix{.25,.5,.75}; wrong_conclusion × {prefix1, full_closed} |
| N samples/question | 16 |
| max_new_tokens | thinking: 81920 (AIME) / 32768 (rg); instruct: 16384; closed conditions: 4096 |
| Sampling | per model card (config.py): thinking T=0.6/p=0.95/k=20; instruct T=0.7/p=0.8/k=20 |
| Seed | 0 |
| Command | `bash scripts/run_pilot_gpu0.sh` (thinking×AIME), `bash scripts/run_pilot_gpu1.sh` (rest) |

## Results

**Instruct model (AIME 24+25) — done 2026-07-17 09:00.** Headline table and takeaways in `docs/daily/2026-07-16.md` (matched-subset analysis, 33 qs). One-line version: forced answering after wrong reasoning → total adoption (pass@1 = 0); clean prefix dose-response with a point of no return at f=1.0 (even open-ended); irrelevant traces hurt far more than wrong-but-relevant ones; corrupted correct scaffolds *help*; pass@k shows early prefixes shift the distribution while complete wrong reasoning destroys capability.

**Thinking model (AIME 24+25)** — baseline running on GPU0 (old env, ~80%); injection grid queued under ssrm_hopper (scripts/run_inject_gpu0_v2.sh). The key comparison — does thinking-RL training create the recovery ability the instruct model lacks at f=1.0? — lands when that grid completes.

**Thinking model (rg_maze) — done 2026-07-17 20:05.** Headline: recovery is thinking-driven (wrong_conclusion open 0.939 vs closed 0.077); recovery scales with triggered re-thinking volume; but the model does NOT distrust its own completed reasoning (self_wrong prefix1 0.023 ≈ closed 0.008, n=8) — a bare wrong conclusion is rejected while the same wrongness with plausible steps is accepted. Details in daily doc; audit in `audit_thinking_maze.md`.

**instruct rg_maze / mini_sudoku** — continuing in scripts/run_pilot_gpu1_v2.sh queue.

## Sanity checks

- [ ] Truncation < 2% per cell — **FAILED for instruct 16k budget** (3–18% per open cell; baseline 12.4%) → 32k rerun queued; treat current instruct recovery numbers as slight underestimates.
- [ ] Inspect ≥ 5 raw samples per condition (pending — do before final writeup)
- [x] Baseline pass@1 in expected range: instruct 0.548 (card ~0.47 AIME25; ours 0.481 AIME25 / 0.615 AIME24) ✓

## Takeaways

See daily doc. Design notes for next revision: (1) add `}` / `</answer>` stop strings for forced instruct conditions (90% benign truncation in wrong_conclusion:full_closed); (2) report matched-subset numbers as primary (composition confound across trace sources); (3) baseline pass@16 = 1.0 by construction on the solvable subset — state this explicitly.
