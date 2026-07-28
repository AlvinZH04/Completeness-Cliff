# Draft: results update for mentor (attach docs/figures/*.png + docs/report_pilot1.md)

> **Superseded.** Earlier draft, kept for the record. The sent version is
> `mentor_update.txt`, and several numbers here were corrected on 2026-07-25
> (see `findings.md` section "Review corrections"): the run total is 91,760
> generations, not ~75k, and two claims about the open-block premium and
> mismatch detection did not survive re-analysis.

Subject: First results — injecting wrong reasoning traces into LLMs (pass@k recovery study)

Hi [name],

Over the last few days I ran a pilot for the research direction we discussed: if we
force a model to condition on an *incorrect* thinking trace — a prefix or a complete
rollout, injected inside its reasoning channel — can it still answer correctly among
k sampled attempts? Quick summary below; the full report (methods, all tables,
limitations, round-2 plan) is attached.

**Setup (Fig 0).** Matched model pair Qwen3-4B-Thinking/Instruct-2507 plus
Gemma-4-E2B-it as a cross-family check, on AIME 2024+25 and procedural
reasoning-gym tasks (maze, sudoku). Pipeline: baseline rollouts (N=16/question,
card-recommended sampling, vLLM) → harvest the model's own wrong rollouts as a
trace bank → re-prompt with injected traces (5 wrongness types × prefix fraction
{25–100%} × think-block open/force-closed) → grade only generated tokens
(math_verify / task verifiers) → pass@k, adoption rate (did it echo the trace's
answer?), and a token-level audit of every continuation. Cross-source comparisons
use matched question subsets. ~75k rollouts total on 2 H100s.

**Main result — a "completeness cliff" (Fig 1).** Partial wrong prefixes only
reshape the answer distribution: through 75% of its own wrong reasoning, the
thinking model still solves the problem within 16 samples essentially always
(pass@16 = 1.00 → 0.91). But given 100% of the wrong trace — with unlimited room to
keep thinking — pass@16 collapses to 0.04, identical to forcing an immediate
answer, and identical for the instruct model. Reasoning training moves the cliff
edge later; it doesn't remove it. Five replications across both families.

**Why (Figs 2–4).** The right to keep thinking is only exercised selectively:
Qwen-thinking re-examines *foreign* material (open-vs-closed premium +0.86 on bare
wrong assertions, +0.36 on irrelevant traces) but spends ~nothing auditing its own
finished chain (+0.02); the instruct model and Gemma get ~zero premium anywhere —
so the disposition comes from reasoning-RL, not from having a thought channel
(Fig 2). Recovery rate tracks how much re-thinking the injection provokes: 19–21k
continuation tokens for assertions/foreign prefixes vs 1.1k for own-complete
reasoning — where the model often literally writes "wait" and then concludes anyway
(Fig 3). And the ordering over wrongness types shows the scaffold, not the
conclusion, is what persuades: the same wrong answer is rejected as a bare
assertion (0.51–0.94 recovery) but accepted when wrapped in plausible steps (0.02);
corrupted numbers inside a correct scaffold get silently repaired (Fig 4).

**Caveats:** 4B-class models only, two families/one RL recipe, model-generated
wrong traces; a few artifact cells are excluded and documented.

**Proposed next steps:** (1) a "Wait,"-append intervention after complete wrong
traces — a one-token test of the commitment interpretation; (2) scale sweep
(9B/14B/30B-A3B); (3) an R1-distill replication; (4) LLM-written reasoning-error
corruption (vs numeric). Each is ≤2 GPU-days with the existing pipeline.

Would love your read on (a) whether the completeness cliff is the right headline
claim for a write-up, and (b) which of the next steps you'd prioritize. Happy to
walk through details whenever suits.

Best,
[you]
