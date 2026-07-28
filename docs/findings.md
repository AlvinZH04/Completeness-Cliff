# Findings — Wrong-Trace Injection (living document)

Each finding lists the exact setting that produced it (model / dataset / cells / N /
budget / results dir) so it can be re-verified or re-run. Definitions of all
conditions & metrics: `docs/conditions_and_metrics.md`. Chronological detail:
`docs/daily/`. Status: **pilot round 1** (2026-07-16 → 07-18); updated as runs land.

## Common setup (applies unless a finding says otherwise)

- Models: `Qwen/Qwen3-4B-Thinking-2507` ("thinking") and `Qwen/Qwen3-4B-Instruct-2507`
  ("instruct"), card-recommended sampling (T=0.6/top_p=0.95/top_k=20 and
  T=0.7/top_p=0.8/top_k=20), N=16 samples/question/condition, seed 0.
- Budgets: thinking 81920 new tokens on AIME / 32768 on rg tasks; instruct 16384;
  force-closed cells 4096. vLLM 0.19.0 (FA3) offline, raw-prompt injection.
- Datasets: AIME 2024+2025 (60 qs), reasoning_gym `maze` & `mini_sudoku` (50 qs each,
  seed 20260716). Grading: math_verify on `\boxed{}` (math), `score_answer` on
  `<answer>` tags (rg); only generated tokens graded.
- Injection grid: sources {self_wrong, irrelevant, corrupted, wrong_conclusion} ×
  prefix fractions {.25, .5, .75, 1.0} open + full_closed (details/coverage rules in
  the glossary). "Matched subset" = questions solvable at baseline AND having
  self-wrong traces; primary basis for cross-source comparisons.

## Headline findings

### F1. With reasoning prefilled and answering forced, the answer IS the trace's answer
Both models, every full_closed cell, every dataset: pass@1 ≤ 0.03 with adoption
0.97–1.00 (instruct AIME: `inject_qwen3-4b-instruct_aime24_25`; thinking maze:
`inject_qwen3-4b-thinking_rg_maze`; sudoku: adoption 0.72–1.00). The trace is fully
load-bearing at answer time — no answer-stage override exists in either model.

### F2. The completeness cliff is universal — reasoning-RL moves its edge, not its existence
Matched subsets, self_wrong prefixes, pass@16 by fraction:
- Instruct AIME (n=33, baseline 0.587): 0.909 / 0.879 / 0.636 at f ≤ .75 → **0.030 at f=1.0** (open).
- **Thinking AIME (n=23, baseline 0.753): 1.000 / 1.000 / 0.913 at f ≤ .75 → 0.043 at f=1.0** (open) ≈ full_closed 0.043.
The thinking model preserves FULL pass@16 capability much deeper into its own wrong
reasoning (cliff edge pushed from ~f=.5 to ~f=.75) — but at completeness both models
collapse identically. Free continuation after a complete wrong solution recovers ~4%
in 16 attempts regardless of reasoning training. Replicated on maze and by Gemma
(F6). Settings: `inject_qwen3-4b-{instruct,thinking}_aime24_25`.
(*pass@16 = 1.0 by construction on solvable subsets.)

### F3. pass@k separates "distribution shift" from "capability destruction"
Instruct AIME matched subset: early/mid wrong prefixes leave pass@16 high (0.88–0.91
at f ≤ .5) while pass@1 drops — sampling recovers the capability. Complete wrong
reasoning collapses pass@16 itself (0.030). The k-attempt lens is what distinguishes
"usually follows the trace" from "cannot escape it" — single-sample accuracy conflates
these regimes.

### F4b. The open-block premium comes from training, not from having a thought channel (cross-family)

> **Partly corrected 2026-07-25**, see "Review corrections" C1 at the end of this file. The +0.862 below is a whole-cell maze number; on a common AIME set the instruct model gains +0.443 on wrong_conclusion, so "instruct premium ~0 everywhere" does not hold. The dissociation that survives is on a complete but *foreign* rationale.
Gemma-4-E2B-it *generates* thought channels but barely *uses* them for recovery: on
maze its open-vs-closed premium is ~zero everywhere (wrong_conclusion 0.000 ≡ 0.000
with adoption 1.0 — vs Qwen-thinking's 0.939 vs 0.077; irrelevant 0.216 ≈ 0.220;
self_wrong 0.004 ≈ 0.000, n=42), and only partial on AIME (wrong_conclusion open
0.314 vs baseline 0.355). A hybrid model with a thinking mode can still be
behaviorally an instruct model under wrong-trace injection. Distinguishes
"thought-channel format" from "re-examination disposition"; the latter is what
Qwen-style reasoning-RL installs. Setting: `inject_gemma-4-e2b_{aime24_25,rg_maze}`.

### F4. Reasoning-RL's contribution is the disposition to re-examine, not answer-time robustness
Matched-task maze comparison (both models, same trace constructions; baselines
0.941 / 0.836): open-vs-closed premium on wrong_conclusion = **+0.862 for thinking
(0.939 vs 0.077) vs +0.043 for instruct (0.043 vs 0.000)**; on irrelevant +0.184 vs
+0.002. With the channel closed both models parrot nearly identically (0.200 vs
0.180). Thinking-model recovery runs through actual re-thinking: audit shows 100%
switch-phrase incidence, ~63 correction markers, 8.5k re-thinking tokens on
wrong_conclusion. Setting: `inject_qwen3-4b-{thinking,instruct}_rg_maze`; audits
`audit_thinking_maze.md`.

### F5. Recovery scales with how much re-thinking the injection triggers
Thinking, maze: irrelevant f=.25 → 13.0k-token continuations, 0.819 correct;
irrelevant f=1.0 → 2.3k tokens, 0.384; own complete wrong trace → 0.4k tokens, 0.023.
Continuation length after injection is the proximate predictor of recovery.

### F6. Shared blind spot: no model distrusts its own completed reasoning — cross-family
self_wrong prefix1 (open) ≈ full_closed in every model × task measured: Qwen instruct
AIME 0.004/0.000; Qwen instruct maze 0.000/0.000 (n=20); Qwen thinking maze
0.023/0.008 (n=8); **Gemma-4-E2B thinking AIME 0.023/0.023 (n=49) and maze 0.004/0.000 (n=42); Qwen
thinking AIME 0.024/0.003 with pass@16 0.043 (n=23–28) — five independent
replications across two families, now including the strongest reasoning model
tested on the hardest task.** Audit texture (thinking AIME): after own-complete
reasoning, 35% of continuations say "wait" but average 1.2 correction markers and
1.1k tokens — verbalized hesitation without re-examination ("seeing ≠ doubting");
after a bare assertion: 100% switch, 75 markers, 18.7k tokens, 0.71 recovery.
**Anatomy of the rare escapes:** ALL 9 thinking-model successes in self_wrong:prefix1
come from ONE question (aime25-18, gold 82 vs trace 54) where (a) baseline is 15/16 —
a near-certain prior ("I recall … the number is 82"; possible AIME-25 contamination),
AND (b) the injected trace *surrenders* rather than concludes ("I give up and go with
… 54"). Hedged trace endings alone don't rescue (7/28 traces hedge; only this one
recovered). Instruct's only 2/448 escapes: a question with a cheap checkable
certificate (subset sum must equal 2024) caught by its habitual "### Verification"
ritual. Recovery from complete wrong reasoning, when it happens at all, requires an
EXTERNAL anchor — a near-certain prior or a verifiable certificate — never unprompted
distrust of the chain itself. Contrast with F4's
wrong_conclusion recovery: **a bare wrong conclusion is rejected; the same wrongness
wrapped in plausible steps is accepted. The scaffold persuades, not the conclusion.**
Setting for Gemma: `inject_gemma-4-e2b_aime24_25`, thinking via `<|think|>` system
token, N=16 (note its 15.9% baseline no-answer floor).

### F7. The completeness effect is structural, not a competence effect
Thinking, mini_sudoku — baseline pass@1 = 1.000 (fully saturated): complete foreign
trace (irrelevant prefix1 open) still captures the model → 0.113, adoption 0.861;
partial prefixes shrugged off (0.938–0.959); bare wrong assertion fully rejected
(1.000). Even at perfect task competence, a finished-looking chain suppresses
re-examination. Setting: `inject_qwen3-4b-thinking_rg_mini_sudoku`.

### F8. Domain mismatch gates recovery (user-suggested cross-domain test) — both directions confirmed

> **Retracted in part 2026-07-25**, see "Review corrections" C2. The AIME-side contrast compared a whole-cell value (0.545, n=60) against a matched-subset value (0.375, n=23). Recomputed on the same 23 questions the two are indistinguishable (0.389 vs 0.375, overlapping intervals).
Thinking model, fractions .25/1.0 + closed, both directions
(`inject_qwen3-4b-thinking_rg_maze_cross`, `inject_qwen3-4b-thinking_aime_cross`):
a complete ALIEN trace is escapable — maze q × AIME trace: 0.782 (83% of baseline;
adoption 0.129); AIME q × maze trace: 0.545 (66% of baseline; adoption 0.290; 88%
switch phrases, 10.6k re-think tokens) — while complete SAME-domain traces capture
the model (maze 0.384; instruct AIME 0.024). Recovery is gated on a
mismatch-detection signal, not reasoning ability; detection is easier when the trace
is blatantly foreign, and recovery from alien traces is harder (but still large) on
harder problems. full_closed stays at floor in both directions (0.029 / 0.015 —
the model will write a maze step-count as an AIME answer when denied thinking).
Audits: `audit_thinking_{maze,aime}_cross.md`.
**Cross-family: the mismatch reflex is also trained, not free** — Gemma-4-E2B on
maze × complete AIME trace recovers only 0.091 (adoption 0.64; vs Qwen 0.782), and
its cross-domain capture is *deeper* than same-domain (0.091 < 0.216), the opposite
ordering from Qwen. Setting: `inject_gemma-4-e2b_{rg_maze,aime}_cross`.

### F9. Instruct models notice but cannot act (noticing ≠ recovering)
Instruct AIME audit (`audit_instruct_aime.md`): after a 25% irrelevant prefix, 80% of
continuations contain switch phrases and 57% re-engage the target question's numbers
(5.8k tokens) — yet only 7% end correct (45% adopt donor answer, 45% end elsewhere
wrong). Awareness without the ability to cleanly restart. Extends Yang et al. 2025's
identification-vs-recovery gap with token-level evidence.

### F10. Local numeric corruption of correct reasoning does not propagate
Both models, all tasks: corrupted cells ≥ baseline (instruct AIME 0.567–0.780 vs
0.587 matched baseline; maze/sudoku 0.92–1.00). Models silently repair perturbed
numbers; the mostly-correct scaffold helps more than the corruption hurts. (Caveat:
rule-based ±1/2 integer perturbation in the trace tail — reasoning-error corruption
per 2512.17079 not yet tested.)

### F11. Irrelevant reasoning is more damaging than wrong-but-relevant reasoning (instruct)
Instruct AIME matched subset f=.25: irrelevant 0.085 vs self_wrong 0.536; adoption
0.46 = literally emits the donor question's answer. Blind continuation dominates.
(For thinking models the ordering reverses at f=1.0: irrelevant 0.384 > self_wrong
0.023 — foreignness helps escape; see F6/F8.)

## Methodological discoveries

### M1. High truncation can be intrinsic non-termination, not budget shortage
Instruct AIME truncation 12.4% at 16k budget vs 11.5% at 32k with IDENTICAL pass@k
(0.783 pass@16 both) — repetition loops on unsolvable problems expand to fill any
budget. Rule: gate on truncation, but before rerunning, check whether doubling the
budget moves pass@k. Setting: `base_qwen3-4b-instruct_aime24_25{,_32k}`.

### M2. Answer-collision artifact on small-answer-space tasks
Maze same-dataset irrelevant full_closed showed pass@1 0.200 with adoption 1.00 —
donor step-counts collide with gold ~20% by chance; cross-domain AIME donors (0–999)
put the true forced-answer floor at 0.029. Use cross-domain donors or collision
filtering when the answer space is small.

### M3. Cross-source comparisons need matched question subsets
self_wrong exists only where the model fails at baseline; corrupted only where it
succeeds — raw cell means mix different question difficulty. All cross-source claims
above use the matched subset (or state coverage).

### M4. Environment provenance matters for throughput claims
`reasoning_gym` env's vllm 0.17 shipped an FA3 build for sm_52 → silent fallback
pressure on H100 (triton backend ~2.2k tok/s). `ssrm_hopper` (vllm 0.19, FA3 sm_90)
≈ 2–4×. Same seeds reproduced identical smoke pass@1 across envs.

## Status: PILOT ROUND 1 COMPLETE (2026-07-19)

All planned runs finished. The thinking AIME grid confirmed: RQ2 open-block premium
on hard math = +0.364 for foreign traces vs +0.021 for own-complete traces (thinking),
vs ≈0 everywhere (instruct); RQ3 largest gap at irrelevant f=.25 (0.633 vs 0.085,
matched). Full consolidated report: **`docs/report_pilot1.md`**.

Round-2 candidates: harder rg configs (bigger mazes/sudoku for self_wrong supply),
reasoning-error (vs numeric) corruption, "Wait"-append intervention arm, N=32 winner
cells, scale sweep (Qwen3.5-9B/14B/30B-A3B), R1-distill lineage, cross-model traces
(weak→strong), forced-close stop-string fix, GPQA/GSM8K tiers.

---

## Review corrections (2026-07-25)

External code+blog review of commit `c001902` (`README_review.md`). Every checkable claim
was verified against the raw rollouts before acting. Corrections that changed a published
claim, not just its wording:

**C1. Figure 2 mixed question sets, and the corrected version tells a different story.**
The published "+0.86 open-block premium" for wrong_conclusion came from the whole 50-question
**maze** cell, while the other bars used the 23-question matched **AIME** subset. Recomputed on
AIME with a common 60-question set for all three models:

| condition | thinking | instruct | gemma |
|---|---|---|---|
| generic pseudo-rationale (wrong_conclusion) | +0.494 | **+0.443** | +0.126 |
| complete solution to a different question (irrelevant) | **+0.415** | +0.007 | +0.068 |
| own complete wrong solution (self_wrong) | +0.018 (n=28) | +0.003 (n=46) | +0.000 (n=49) |

So F4b as previously stated ("the instruct model gains ~0 everywhere") is **wrong**: on a
generic pseudo-rationale the instruct model gains nearly as much as the thinking model. The
real dissociation is on a **complete but foreign rationale**, where only the reasoning-trained
checkpoint re-derives. Revised claim: reasoning training is associated with discarding material
that looks like a real derivation but does not belong; it is not a general "only trained models
use the think block" effect.

**C2. Cross-domain vs same-domain mismatch is not distinguishable.** The published contrast
(maze trace 0.545 vs different-AIME 0.375) compared a whole-cell n=60 value against a matched
n=23 value. On the same 23 questions: **0.389 [0.269, 0.511] vs 0.375 [0.255, 0.497]**. The
"blatant mismatch is escaped more often than subtle mismatch" part of F5 is **retracted**;
mismatch-detection gating is not supported by this comparison.

**C3. The scaffold claim is an association, not a controlled result.** `wrong_conclusion`
perturbs the gold answer while `self_wrong` carries the rollout's own answer, so the wrong
answer is not held fixed across conditions; they also differ in length, task specificity, and
provenance. The ordering stands; the causal reading does not. Paired fixed-answer ablation
specified in `docs/blog/` section 6 is now the top round-2 priority.

**C4. Figure 4's "corrupted" bar was mislabeled.** `build_conditions` skips corrupted fractions
>= 1.0, so that bar is a **75% prefix of a correct solution with tail integers perturbed**, not a
complete trace.

**C5. Smaller factual fixes.** Generation count is **91,760** (7,040 baseline + 84,720
injection), not "~75k". Continuation budgets are finite: 81,920 (thinking AIME), 16,384
(instruct AIME), 4,096 forced; "unlimited" was wrong. Adoption at the cliff is 0.837 open /
0.959 forced for thinking and 0.992 / 0.970 for instruct, not "near 1.0" everywhere. pass@16 of
0.043 and 0.030 are **one question** out of 23 and 33; with bootstrap intervals of [0, 0.130]
and [0, 0.091] they are "similar", not "identical". Pass@16 near zero means access under this
protocol collapses, not that the capability is gone.

**Artifact added.** `results/blog_manifest.json` now carries the matched-subset aggregates
(selection rule, question ids, per-question correct counts, pass@k with question-level bootstrap
intervals, adoption, truncation) for every figure. `scripts/make_figures_blog.py` reads it
instead of hard-coded arrays, and `scripts/export_blog_manifest.py --check` re-verifies that the
published values reproduce from raw rollouts. All ten checked figure values reproduce exactly.

**C6 (found 2026-07-25, while auditing the corrected Figure 2).** The `wrong_conclusion:full_closed`
cells that the open-block premium subtracts are **answer-budget truncated** and are not a sound
baseline: 53% truncation / 43% no-answer for thinking, 52% / 57% for Gemma (`ANSWER_ONLY_MAX_TOKENS`
= 4096). A forced baseline depressed by samples that never emit an answer inflates the premium above
it, so the pseudo-rationale premiums (+0.49 thinking, +0.13 Gemma) are **upper bounds**; scoring only
answering samples puts the thinking value nearer +0.14. The **instruct** bar is unaffected (90%
truncation but no_answer 0.000 and adoption 1.000: it boxes its answer immediately, then rambles), so
its +0.44 is real. The middle group, which carries the trained-disposition dissociation, is clean
(0.4% truncation for thinking). **Rerun required**: forced-close cells with stop strings on
`</think>`-adjacent answer emission, or a larger answer budget, for `wrong_conclusion:full_closed`
(all three models) and `irrelevant:full_closed` (instruct, 18.4%).

---

## Paired fixed-answer ablation (2026-07-26) and the memorization probes

### F12. No scaffold explains the collapse; the model's OWN completed chain is the variable

> **Heading and conclusion corrected 2026-07-27** (see T2). The original wording, "the scaffold
> hypothesis is refuted", was too strong: paired differences among A/B/C are real and reverse
> across models. What the data support is that no scaffold explains the D-arm collapse, which is
> an order of magnitude larger.

Run `ablation_paired_qwen3-4b-thinking_aime`, 28 AIME questions, 16 samples, model free to
keep thinking. Every arm asserts the **same** wrong answer (the one that model's own wrong
rollout reached), so answer identity is constant and only the scaffold varies.

| arm | pass@1 [95% CI] | pass@16 | adoption | mean tokens |
|---|---|---|---|---|
| A bare claim, no steps | 0.326 [0.221, 0.435] | 0.821 | 0.616 | 31,622 |
| B generic pseudo-rationale | 0.391 [0.255, 0.529] | 0.750 | 0.402 | 23,794 |
| C short task-specific rationale | 0.533 [0.391, 0.674] | 0.750 | 0.228 | 26,492 |
| D the model's OWN complete derivation | **0.031 [0.000, 0.094]** | **0.036** | 0.850 | 1,079 |

Baseline on the same 28 questions: pass@1 0.618, pass@16 0.821.

**Adding a scaffold does not make a wrong answer stickier.** B and C sit at or above the bare
claim A, and the most task-specific scaffold (C) is the easiest of the three to escape. Only
D collapses recovery, and its interval overlaps none of the others. Arm A leaves pass@16 at
0.821, *exactly* the baseline: a bare wrong assertion costs no capability at all.

This supersedes the earlier "the reasoning scaffold persuades, not the conclusion" claim
(previously F5/blog section 6), which was confounded because `wrong_conclusion` perturbed the
gold answer while `self_wrong` carried the rollout's own. The surviving variable is the same
one as the completeness cliff: reasoning that is the model's own, about this problem, and
**finished**. Arm C behaves like the left side of the cliff (it is effectively a short
prefix); arm D behaves like the right edge.

Truncation is clean where it matters: all four open arms <= 0.2%. The C6 fix worked, with
`B_generic:full_closed` at 0.9% truncation against the old 4096-budget cell's 53%. One cell,
`A_answer_only:full_closed`, is unusable (96% truncation, 90% no-answer): a bare claim plus a
forced `</think>` leaves the thinking model nothing to work with and it rambles to the cap.

### F13. The rare escape shows no sign of memorization on these probes

> **Heading corrected 2026-07-27** (see T5). "Is NOT memorization" overstates what two probes can
> establish. They find no direct answer retrieval and no verbatim question recall; they cannot rule
> out paraphrased or partial memorization.

Runs `memorization_qwen3-4b-{thinking,instruct}_aime24_25`, all 60 AIME questions. Two probes:
forced immediate answer with the think block closed and a prefilled `\boxed{` (no room to
derive), and greedy continuation of the raw problem text from a 40% prefix with no chat
template (verbatim contamination).

Under the complete own-wrong trace exactly one question recovers, **aime25-18** (gold 82,
14/16). It is not memorized on either probe:

- Forced immediate answer: the thinking model says **12** every time, the instruct model says
  **6** every time. No-reasoning accuracy 0.000 for both, against a best-question score of 0.19.
- Question-text recall: longest-match 0.015, the **lowest of all 60 questions**.
- No training-cutoff signature: AIME 2024 vs 2025 longest-match is 0.093 vs 0.078 (thinking)
  and 0.109 vs 0.099 (instruct).

The thinking model's raw forced output is diagnostic: `"12}$. Wait, no, hold on, I need to
think carefully here. Let me start over."` The answer is not retrievable without reasoning.
The "I recall the answer is 82" phrasing seen in winning continuations is better read as
confabulated justification than as retrieval.

**What does distinguish the escaping question, and why it is still unexplained.** It is
extreme on both measurable axes: joint-highest baseline accuracy (0.938) and the most hedging
in its injected trace (4 markers, rank 1/28). But neither is sufficient. Seven other questions
share the 0.938 baseline and recover 0.000, and `aime25-2` has both a 0.938 baseline and 3
hedge markers yet also recovers 0.000. With a single escape out of 28, any post-hoc feature
that happens to be extreme will look explanatory, so this is reported as a negative result
plus two correlates, not a mechanism.

### F12b. The ablation replicates on the instruct model (overlapping question set)

> **Corrected 2026-07-27** (see T3). This entry called the instruct set disjoint from the thinking
> set. It is not: the thinking model's 28 questions are a complete subset of the instruct model's 46.

Run `ablation_paired_qwen3-4b-instruct_aime`, 46 questions, baseline pass@1 0.421 / pass@16 0.717.

| arm | pass@1 [95% CI] | pass@16 | adoption |
|---|---|---|---|
| A bare claim | 0.406 [0.307, 0.508] | 0.674 | 0.431 |
| B generic pseudo-rationale | 0.307 [0.224, 0.397] | 0.717 | 0.590 |
| C short task-specific rationale | 0.379 [0.277, 0.484] | 0.696 | 0.311 |
| D own complete derivation | **0.003 [0.000, 0.008]** | **0.022** | 0.995 |

Same shape on a disjoint question set: A, B and C all sit at or near baseline, D collapses,
and D's interval overlaps none of the others. **What does not replicate is the ordering among
A, B and C.** The thinking model recovers best from the task-specific scaffold (C 0.533) and
the instruct model best from the bare claim (A 0.406), and within each model those three lie
inside one another's intervals. The supported claim is therefore the negative one: adding a
scaffold does not increase stickiness. Any ranking among the non-D arms is noise at this n.

**The forced cells are degenerate for the instruct model** and carry no information: all four
arms give pass@1 0.000 with adoption 0.974 to 1.000 and a mean of 4 generated tokens. With the
answer expression prefilled and stop strings active, the model simply closes the box on the
trace's answer. This is the "prefilled reasoning fully determines forced answers" result from
round 1, now in its sharpest form, but it means the instruct open-vs-forced premium cannot be
computed from this run.

### F14. The "Wait,"-append intervention does NOT undo the cliff (thinking model, N=16)

Run `waitappend_qwen3-4b-thinking_aime`, 28 questions, open condition. The model's own
complete wrong derivation with a short continuation appended:

| arm | pass@1 [95% CI] | pass@16 [95% CI] | questions recovered | mean tokens |
|---|---|---|---|---|
| W0 unchanged (control) | 0.025 [0.000, 0.074] | 0.036 [0.000, 0.107] | 1/28 | 1,056 |
| W1 + "Wait," | 0.036 [0.002, 0.085] | 0.143 [0.036, 0.286] | 4/28 | 1,575 |
| W2 + "So," (control) | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/28 | 1,010 |
| W3 + "Wait, let me double-check that." | 0.025 [0.002, 0.051] | 0.143 [0.036, 0.286] | 4/28 | 1,570 |

Baseline on these questions is pass@1 0.618 / pass@16 0.821, so the intervention recovers a
small fraction of the lost ground at best. **pass@1 is unchanged** (0.025 to 0.036, intervals
almost entirely overlapping). At pass@16 both doubt variants move 1/28 to 4/28, and the paired
comparison is strictly dominating: "Wait," recovers 3 questions the control loses and loses
none (`aime24-2024-II-12`, `aime25-23`, `aime25-25`).

**But this design cannot establish that.** With 3 discordant pairs a one-sided sign test gives
p = 0.125, and 3 is the maximum obtainable here, so even a perfect result could not reach
p < 0.05. The experiment is underpowered by construction: with N=16, pass@16 per question is
binary, so the statistic is 1/28 against 4/28. A follow-up at N=64 is running to give pass@16
real per-question resolution.

Two things are informative regardless of power:

1. **The neutral control goes to zero.** Appending "So," removes even the control's single
   escape (0/28). So whatever is happening tracks the semantics of the appended token, not the
   mere fact that the chain no longer ends at a terminal boundary. That is the control that
   makes a positive W1 interpretable, and it earns its cost here.
2. **The doubt token buys very little re-derivation.** W1 and W3 generate about 1,570 tokens
   against the control's 1,056, versus the 18,000 to 32,000 that foreign or partial traces
   provoke. The model says "Wait," and then concludes anyway. This is the "seeing is not
   doubting" result again, now with the doubt token supplied for free.

Read against Tsui (arXiv:2507.02778), where appending "Wait" cuts the self-correction blind
spot by 89.3%: that result is on non-reasoning models correcting errors in their own output,
not on a reasoning model handed its own completed chain. The cliff does not appear to be a
formatting artifact that a doubt token can undo.

### F14b. The intervention DOES work on the instruct model (and the control stays null)

Run `waitappend_qwen3-4b-instruct_aime`, 46 questions, open condition. Baseline on these
questions: pass@1 0.421 / pass@16 0.717.

| arm | pass@1 [95% CI] | pass@16 [95% CI] | questions | paired sign test | mean tokens |
|---|---|---|---|---|---|
| W0 unchanged | 0.003 [0.000, 0.008] | 0.022 [0.000, 0.065] | 1/46 | reference | 941 |
| W1 + "Wait," | **0.046 [0.014, 0.087]** | 0.174 [0.065, 0.283] | 8/46 | **p = 0.008** | 2,563 |
| W2 + "So," (control) | 0.008 [0.000, 0.022] | 0.043 [0.000, 0.109] | 2/46 | p = 0.500 | 2,329 |
| W3 + "Wait, let me double-check that." | 0.027 [0.010, 0.052] | 0.196 [0.087, 0.326] | 9/46 | **p = 0.004** | 2,357 |

Unlike the thinking model, this is a real effect. The pass@1 intervals for W0 and W1 do not
overlap, and both doubt variants gain 7 to 8 questions while losing none. The neutral control
is null on the same questions (2 gained, 1 lost, p = 0.500) despite generating a comparable
number of extra tokens (2,329 against W1's 2,563), which rules out "any appended text" and
"more tokens" as the explanation. What matters is that the appended text expresses doubt.

**It is a partial rescue, not a cure.** W1 reaches pass@16 0.174 against a baseline of 0.717,
so roughly a quarter of the lost ground, and pass@1 0.046 against 0.421. The cliff survives
the intervention.

**A cross-model dissociation worth flagging, tentatively.** The intervention is significant on
the instruct model (p = 0.008) and not detectable on the thinking model (1/28 to 4/28,
p = 0.125, underpowered). A natural reading is that supplying doubt helps the model that lacks
a trained re-examination disposition, and adds little to the model that already has one and
already writes "wait" spontaneously (F5, "seeing is not doubting"). That is consistent with
F4b, but the two models differ in baseline, in question set, and in how much room they have to
improve, so this is a hypothesis rather than a result. The N=64 thinking run will say whether
the thinking effect is genuinely absent or merely small.

### F14c. At N=64 the thinking model responds to the explicit instruction (directional test)

> **Qualified 2026-07-27** (see T4). The p-values here are one-sided. The thinking W3 result is
> two-sided p = 0.070, so directional and suggestive rather than conventionally significant.

Run `waitappend_n64_qwen3-4b-thinking_aime`, same 28 questions, 64 samples per cell. This was
run because F14's N=16 design was underpowered by construction, and it revises F14.

| arm | pass@1 [95% CI] | pass@16 [95% CI] | questions | paired sign test |
|---|---|---|---|---|
| W0 unchanged | 0.024 [0.001, 0.069] | 0.069 [0.009, 0.156] | 4/28 | reference |
| W1 + "Wait," | 0.032 [0.003, 0.074] | 0.133 [0.036, 0.251] | 6/28 | p = 0.312 |
| W2 + "So," (control) | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/28 | p = 0.062 (harmful) |
| W3 + "Wait, let me double-check that." | 0.026 [0.008, 0.051] | **0.201 [0.091, 0.327]** | 10/28 | **p = 0.035** |

**This corrects F14 and the first version of F14b's interpretation.** At N=16 the thinking
effect looked absent; with four times the samples the *explicit* re-check instruction is a real
effect, roughly tripling pass@16 from 0.069 to 0.201 (4 to 10 questions, 7 gained and 1 lost).
The bare "Wait," remains undetectable on this model (p = 0.312). Note also that the control
itself moved from 1/28 to 4/28 once pass@16 was estimated from 64 samples rather than being
a binary per question, which is exactly the coarseness F14 flagged.

**Revised cross-model picture.** The earlier reading, that supplying doubt only helps the model
lacking a trained re-examination disposition, is **not supported**:

| intervention | thinking | instruct |
|---|---|---|
| + "Wait," | 0.069 to 0.133, p = 0.312 | 0.022 to 0.174, **p = 0.008** |
| + "Wait, let me double-check that." | 0.069 to 0.201, **p = 0.035** | 0.022 to 0.196, **p = 0.004** |
| + "So," (control) | 0.069 to 0.000, p = 0.062 | 0.022 to 0.043, p = 0.500 |

Both models are partially rescued by an explicit instruction to re-check. The dissociation is
narrower than claimed: only the *minimal* cue separates them, with the instruct model responding
to a bare "Wait," and the thinking model needing to be told what to do with it. A plausible
reading is that the thinking model already emits "wait" spontaneously (F5), so one more adds no
information, whereas an explicit directive does. In both models the neutral continuation never
helps and on the thinking model it removes every escape.

**Still a partial rescue.** Best case is pass@16 0.201 against a baseline of 0.821 for thinking
and 0.196 against 0.717 for instruct, so roughly a quarter of the lost ground in both. The
cliff is not undone by any of these.

---

## Third-review corrections (2026-07-27)

External review of `264a29b` (`THIRD_REVIEW.md`). Every claim below was verified against
the committed artifacts before acting. All of them held.

**T1. The 2% truncation gate was bypassed in the new analysis.** `analyze_paired_ablation.py`
warned only above 15% and hard-coded every baseline question's truncation count to zero.
Fixed: it now imports `TRUNCATION_GATE` from `src.config` and computes baseline truncation
from the sample records. The affected cells, none of which were disclosed:

| run | arm | truncation |
|---|---|---|
| instruct ablation | A / C / D | 10.1% / 10.9% / 5.4% |
| instruct wait-append | W0 / W1 / W2 / W3 | 5.6% / 13.5% / 13.9% / 12.5% |

The thinking cells are clean (<= 0.2%). Both instruct runs are now labelled provisional in
the blog and need a longer-budget rerun.

**T2. "The scaffold hypothesis is refuted" was too strong, and "any A/B/C ranking is noise"
was wrong.** Because every arm runs on the same questions, the correct comparison is paired.
Paired bootstrap differences in pass@1:

| comparison | difference | 95% paired interval | |
|---|---|---|---|
| thinking C minus A | +0.208 | [+0.085, +0.328] | real |
| thinking C minus B | +0.143 | [+0.051, +0.234] | real |
| instruct B minus A | -0.099 | [-0.160, -0.042] | real |
| thinking B minus A | +0.065 | [-0.020, +0.156] | n.s. |
| instruct C minus A | -0.027 | [-0.092, +0.033] | n.s. |
| instruct C minus B | +0.072 | [-0.015, +0.156] | n.s. |

Scaffold presentation has real but modest effects that **reverse across models**: the short
task-specific rationale helps the thinking model, the generic pseudo-rationale hurts the
instruct model. The supported claim is that no scaffold explains the D-arm collapse, which is
an order of magnitude larger, not that scaffolding does nothing. F12 is corrected accordingly.

**T3. The two ablation question sets are not disjoint.** The thinking model's 28 questions are
a complete **subset** of the instruct model's 46. F12b called this a replication "on a disjoint
question set"; it is a cross-model replication on overlapping problems.

**T4. The reported p-values are one-sided and were not labelled as such.** Two-sided values:
thinking W3 0.070 (not 0.035), instruct W1 0.016, instruct W3 0.008. The thinking result is
therefore suggestive rather than conventionally significant, and F14c's "real effect" wording
overstated it. The blog now states the direction and both values.

**T5. The memorization section contained a factual error.** The thinking model answers 12 on
**13 of 16** samples, not all 16; the remainder are 30, 24 and 4. "Rules out memorization" is
replaced with the supported claim: these probes find no direct answer retrieval and no verbatim
question recall, and cannot rule out paraphrased or partial memorization. Neither model card
gives a training cutoff precise enough to make the 2024-vs-2025 contrast a clean contamination
test.

**T6. `export_blog_manifest.py --check` could destroy a valid manifest.** It wrote its freshly
computed output before running the check, so on a checkout without raw rollouts the documented
command replaced the committed artifact with an incomplete one. `--check` is now read-only.

**T7. Reproducibility wording corrected.** Figures 1, 4 and 5 read the manifest; figures 2 and 3
read whole-run summaries; the wait-append paired statistics were not in the manifest at all; the
published dataset is the baseline trace bank, not the ablation continuations. The blog no longer
says "everything here is reproducible".

**T8.** The HuggingFace dataset card linked to the unpublished blog URL, which returns 404. The
card now leads with the repository and marks the blog link as forthcoming.

### T1b. Truncation sensitivity: the raw rate overstates the damage

> **Statistic corrected 2026-07-28** (see T1d). The "effective loss" column in the first version of
> this entry was computed as the rate of ALL no-answer samples, with no truncation predicate, so the
> thinking own-complete row read 8.3% against 0% truncation. The manifest now separates
> `no_answer_rate`, `truncated_no_answer_rate` and `truncated_with_answer_rate`.

`scripts/truncation_sensitivity.py`, written into the manifest under
`truncation_sensitivity`. The distinction that matters is not whether a sample hit the token
cap, but whether it hit the cap *without* emitting an extractable answer, since only those are
scored as failures.

| run | cell | raw trunc | truncated but still answered | effective loss |
|---|---|---|---|---|
| instruct ablation | A / C / D | 10.1% / 10.9% / 5.4% | 72% / 74% / 95% | **2.9% / 3.3% / 0.3%** |
| instruct wait-append | W0 / W1 / W2 / W3 | 5.6% / 13.5% / 13.9% / 12.5% | 90% / 80% / 75% / 78% | **0.5% / 2.7% / 3.5% / 2.7%** |

Worst-case bound, counting every no-answer sample as correct (a deliberately absurd
assumption, since those samples ran to the cap without producing an answer):

- Ablation: A 0.406 to 0.435, D 0.003 to 0.005. The **D-arm collapse is untouched**, still two
  orders of magnitude.
- Intervention: W1 pass@16 0.174 to 0.348 against W0 0.022 to 0.109. The **W1 > W0 direction
  survives** the bound.

The bias also runs in the helpful direction: within each run the arms with *more* truncation are
the *higher*-recovery ones (A and C in the ablation, W1 and W3 in the intervention), so losing
those samples understates the reported effects rather than manufacturing them.

**The one comparison this does not fully protect** is the W2 neutral control, which has the
highest effective loss (3.5%) and whose null result is what licenses the "doubt semantics, not
extra text" reading. Under the worst-case bound its pass@16 would reach 0.239. That is why the
32k reruns were run rather than resting on this analysis alone.

**A separate artifact this surfaced:** thinking `D_own_complete` shows 0% truncation but an 8.3%
no-answer rate, so its lost samples are not a budget problem at all. Those are continuations that
terminate without a parseable answer, which is a grading-coverage question rather than a
truncation one, and is not addressed by a longer budget.

### T1c. The 32k reruns: results replicate, truncation is intrinsic, the control is clean

Both instruct runs rerun at a 32,768-token budget (originals kept for comparison).

**Truncation does not respond to the budget.** Ablation arm A 10.1% to 10.5%, arm C 10.9% to
13.0%, arm D unchanged at 5.4%; intervention arms 13.5% to 13.6%, 13.9% to 13.9%, 12.5% to
12.1%. Mean generation length rose substantially over the same change (ablation A 8,793 to
10,483 tokens, C 6,920 to 9,285, D 918 to 1,809), so the model expands to fill the budget and a
roughly constant fraction still reaches the cap. This reproduces M1 and settles the question:
**no budget brings these cells under the 2% gate**, so the gate is the wrong instrument for this
model rather than these cells being invalid. The remedy is the sensitivity analysis in T1b, not
more compute.

**The ablation replicates under different generation settings.** pass@1 A 0.406 to 0.376,
B 0.307 to 0.299, C 0.379 to 0.376, D 0.003 to 0.004; pass@16 within noise throughout. The
D-arm collapse is untouched.

**The intervention holds and the neutral control is now exactly null**, which was the one thing
the worst-case bound could not protect:

| arm | pass@16 16k | pass@16 32k | paired vs W0 at 32k |
|---|---|---|---|
| W0 unchanged | 0.022 | 0.022 | reference |
| W1 + "Wait," | 0.174 | **0.196** | 8 gained, 0 lost, one-sided p = 0.004 (two-sided 0.008) |
| W2 + "So," | 0.043 | **0.022** | 1 gained, 1 lost, p = 0.750 |
| W3 + re-check | 0.196 | 0.196 | 8 gained, 0 lost, one-sided p = 0.004 (two-sided 0.008) |

At 16k the control sat slightly above the untouched chain (0.043 vs 0.022), which was the
residual worry. At 32k it lands on 0.022, *identical* to it, while both doubt arms hold or
improve and their tests tighten. The reading that the effect tracks the semantics of the
appended text rather than its presence is now on firm ground for the instruct model.

**Terminated-only accuracy** (samples that ended on their own) is reported per cell in the blog
appendix and in the manifest under `truncation_sensitivity`. Arms with real recovery score
slightly higher on that subset, consistent with runaway samples being the harder questions; the
own-complete arm is unchanged at 0.003.

---

## Fourth-review corrections (2026-07-28)

External review of `92c61f4` (`FOURTH_REVIEW.md`). Verified before acting; the substantive
findings held.

**T1d. The "effective loss" statistic was mislabeled, and the label was load-bearing.**
`truncation_sensitivity.py` documented the quantity as "truncated AND no extractable answer" but
implemented it as `sum(1 for x in s if x.get("answer") is None)`, with no truncation predicate.
The contradiction was visible in the committed manifest: the thinking own-complete cell reported
8.3% "effective loss" against **0.0%** truncation. The manifest now stores
`no_answer_rate`, `truncated_no_answer_rate` and `truncated_with_answer_rate` separately, with
integer numerators alongside the rates, and the conservative bound is renamed
`*_all_no_answer_bound` because it counts every no-answer sample as correct, not only truncated
ones. Corrected values: instruct ablation C is 2.9% truncated-and-no-answer at 16k (not 3.3%) and
3.3% at 32k (not 3.7%).

**T2d. Three overclaims removed from the appendix.**

- *"Nothing is lost"* when a capped sample already contains an answer. Wrong: `extract_boxed`
  takes the **last** boxed answer, so a cut-off trajectory could have revised it. Capped samples
  are gradable but still right-censored, and the appendix now says so.
- *"Intrinsic non-termination"* and *"no amount of extra budget"*. Two cap values cannot support
  an asymptotic claim. The supported statement is that doubling 16,384 to 32,768 did not reduce
  truncation in these cells while the aggregates stayed stable.
- *"Independent replication"*. The rerun holds model, prompts, question set, sample count,
  sampling parameters and seed 0 fixed and changes only the cap. It is a budget-sensitivity
  check. Reframed throughout, and the appendix is retitled "budget sensitivity and
  right-censoring".

Also corrected: the terminated-only column conditions on termination, which the arms themselves
affect (doubt and scaffold arms change generation length), so it selects a different subset per
column. It is now labelled descriptive rather than a robustness estimator, with a per-sample
16k-to-32k transition analysis named as the proper next check.

**T3d. The wait-append paired tests are now reconstructible.** They previously existed only in
prose. `scripts/export_wait_paired.py` writes per-question solved/correct/samples/truncated
counts for every arm and budget, plus the gained and lost question ids and both one- and
two-sided sign-test values, into `blog_manifest.json` under `wait_append_paired`. All four runs
are covered and every value matches what was reported.

**T4d. Two build bugs.** The appendix table emitted `<td class="n" class="over">`; browsers keep
the first attribute, so the over-gate cells were never styled red despite the caption saying so.
Fixed to a single `class="n over"`. The build also read and wrote text without an explicit
encoding, which corrupted the curly apostrophes on a `cp936` Windows locale; all HTML and JSON
I/O now passes `encoding="utf-8"`.

**T5d. Documentation consistency.** The original F12, F12b, F13 and F14c headings still asserted
the retracted claims, so a reader met the strong version first. Each is now corrected in place
with a pointer to the entry that supersedes it, following the F8 precedent. The README's manifest
coverage, `--check` semantics and truncation policy now match the blog and the scripts: above-gate
cells are **provisional pending a stated sensitivity analysis**, rather than "invalidating a run".

### T6d. The 32k reruns are only partially sample-aligned, so the requested transition analysis is not valid

The fourth review recommended a per-sample 16k-to-32k transition analysis. That requires
sample *i* of the 32k run to be the same trajectory as sample *i* of the 16k run. It is not.
`scripts/budget_alignment_audit.py` measures it (written into the manifest under
`budget_alignment`):

| arm | terminated at 16k and byte-identical at 32k | truncated at 16k and extended at 32k |
|---|---|---|
| W0 unchanged | 693/695 (99.7%) | 22/41 (54%) |
| W1 "Wait," | 540/637 (84.8%) | 15/99 (15%) |
| W2 "So," | 626/634 (98.7%) | 43/102 (42%) |
| W3 re-check | 568/644 (88.2%) | 12/92 (13%) |
| ablation A bare | **2/662 (0.3%)** | 0/74 (0%) |
| ablation B generic | 249/722 (34.5%) | 0/14 (0%) |
| ablation C task-specific | **20/656 (3.0%)** | 2/80 (2.5%) |
| ablation D own-complete | 678/696 (97.4%) | 26/40 (65%) |

**Cause.** Both runs use seed 0 and identical sampling parameters, but the rerun raised
`max_model_len` from 49,152 to 81,920 alongside the cap. vLLM is not bitwise reproducible
across that change: KV-cache block allocation and batch composition differ, and small
numerical differences compound. Divergence tracks generation length almost monotonically
(D 918 mean tokens, 97.4% identical; B 5,862, 34.5%; C 6,920, 3.0%; A 8,793, 0.3%).

**Consequence.** The transition analysis cannot be done as specified, and specifically the
samples that would answer the question (truncated at 16k, given more room at 32k) are the ones
that diverge most: extension rates are 0% to 65%. On the aligned subset the transitions are
almost entirely wrong-to-wrong, because alignment selects the short, already-settled samples.
Reporting those transitions as if they characterised the censored samples would be misleading.

**A partial upside.** For the ablation arms with near-zero alignment, the 32k run is effectively
a *fresh draw* rather than a continuation, so its agreement with the 16k aggregates (A 0.406 vs
0.376, D 0.003 vs 0.004) is closer to a re-sample replication than the fourth review assumed
when it called the rerun non-independent. That is not independence by design, which the review
was right about, but it is more than a re-scoring of the same trajectories.

**Fixed alongside.** Run summaries did not record `max_model_len`, which is exactly the
parameter responsible here, so the config difference was invisible in the committed artifacts.
`run_injection.py` now records `max_model_len` and `forced_max_tokens`.
