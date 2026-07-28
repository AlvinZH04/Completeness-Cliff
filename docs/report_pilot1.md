# Can Models Answer Correctly Despite Wrong Thinking Traces?
## Pilot Round 1 Report — wrong_reason project

**Dates:** 2026-07-16 → 07-19 · **Hardware:** 2× H100 NVL · **Total generations:** 91,760 (7,040 baseline + 84,720 injection) across 6 baselines, 9 injection grids, 4 cross-domain runs
**Companion docs:** `findings.md` (living index), `conditions_and_metrics.md` (glossary), `research_plan.md`, `daily/` (chronology), `experiments/audit_*.md` (token-level audits)

> ⚠️ **Superseded in part (2026-07-25).** An external review (`README_review.md`) prompted a
> re-analysis from the raw rollouts. All headline pass@k values reproduced exactly, but three
> claims below did **not** survive and are corrected in `findings.md` § "Review corrections":
>
> 1. **§3 / Table (open-block premium).** The "+0.862" for wrong_conclusion is a whole-cell **maze**
>    number placed beside matched-subset **AIME** numbers. On a common AIME set (n=60 per model) the
>    instruct model gains **+0.443** on that condition, so "instruct premium ~0 everywhere" is wrong.
>    The real dissociation is on a complete but *foreign* rationale (+0.415 thinking vs +0.007 instruct).
> 2. **§4 (mismatch detection).** The cross-domain vs same-domain contrast (0.545 vs 0.375) compared a
>    whole-cell value against a matched-subset value. On the same 23 questions the two are
>    indistinguishable (0.389 [0.269, 0.511] vs 0.375 [0.255, 0.497]). The "blatant mismatch is escaped
>    more often" claim is **retracted**.
> 3. **Scaffold-vs-conclusion.** `wrong_conclusion` perturbs the gold answer while `self_wrong` carries
>    the rollout's own, so the wrong answer is not held fixed. The ordering stands; the causal reading
>    is downgraded to an association pending the paired fixed-answer ablation.
>
> Also: continuation budgets are finite (81,920 thinking / 16,384 instruct / 4,096 forced), adoption at
> the cliff is 0.837 open and 0.959 forced for thinking, and pass@16 of 0.043 / 0.030 is **one question**
> of 23 / 33 with bootstrap intervals [0, 0.130] and [0, 0.091]. Matched-subset aggregates with intervals
> are committed at `results/blog_manifest.json`; the corrected public write-up is `docs/blog/`.

---

## 1. Executive summary

We force models to condition on **incorrect thinking traces** — prefixes or complete rollouts, injected inside the reasoning channel — and measure whether they can still answer correctly among k sampled attempts (pass@k). Five headline results:

1. **Prefilled reasoning fully determines forced answers.** With the think channel closed, every model on every task echoes the injected trace's answer (adoption 0.97–1.00, pass@1 ≤ 0.05). There is no answer-stage override anywhere. Chain-of-thought is completely load-bearing at answer time.

2. **The "point of no return" is trace *completeness*, and it is universal.** Partial wrong prefixes mostly shift the answer distribution — pass@16 stays at 0.91–1.00 for the thinking model through 75% of its own wrong reasoning — but a *complete* wrong trace collapses pass@16 to ~0.04 for **both** the instruct and the reasoning model, even with unlimited open-ended continuation. Reasoning-RL pushes the cliff edge later (instruct begins degrading by f=0.5; thinking holds full capability to f=0.75) but does not remove the cliff. Five independent replications across two model families.

3. **Recovery is a trained disposition, not a property of having a thought channel.** Qwen3-4B-Thinking uses open continuation for genuine re-examination: its open-vs-closed premium is +0.86 on maze assertions and +0.36 on foreign traces in AIME. Qwen3-4B-Instruct's premium is ~0 everywhere. Gemma-4-E2B *generates* thought channels but gains ~nothing from them being open (premium ≈ 0 on maze) — behaviorally an instruct model under injection.

4. **What triggers recovery is mismatch detection, not correctness checking.** The thinking model escapes *blatantly alien* complete traces (maze trace in an AIME question: 0.545; math trace in a maze: 0.782) and *bare assertions without steps* (0.939 on maze) — but not wrong reasoning that looks like its own (0.024). The audit shows the mechanism: alien traces and assertions trigger 10–20k tokens of re-thinking with dozens of correction markers; the model's own completed reasoning triggers ~1k tokens and a concluding sentence, even when the model verbalizes "wait" (35% of continuations) — **seeing is not doubting**. The reasoning scaffold, not the conclusion, is what persuades.

5. **pass@k is the right lens.** Single-sample accuracy conflates "usually follows the wrong trace" with "cannot escape it." The k-attempt framing separates distribution shift (partial prefixes: pass@1 drops, pass@16 holds) from capability destruction (complete traces: both collapse) — the distinction on which all conclusions above rest.

---

## 2. Research questions and verdicts

| RQ | Question | Verdict |
|----|----------|---------|
| RQ1 | Dose-response in prefix fraction f? | Monotone decline for both models; thinking model's pass@16 fully preserved to f=.75, then cliff (§4.1) |
| RQ2 | Open vs force-closed think block? | Premium is large for Qwen-thinking on foreign traces/assertions, ~0 for instruct and Gemma, ~0 for anyone on own-complete traces (§4.2) |
| RQ3 | Thinking vs instruct (matched pairs)? | Massive gaps mid-path and on foreign traces (0.633 vs 0.085 at irrelevant f=.25); identical at the completeness cliff (§4.3) |
| RQ4 | Does the type of wrongness matter? | Yes, ordered by *how much re-thinking it triggers*: alien ≫ assertion ≫ same-domain-irrelevant ≫ own-wrong; local numeric corruption doesn't propagate at all (§4.4) |
| RQ5 | Distribution shift vs capability loss? | Partial = distribution shift; complete = capability destruction (§4.1, §4.5) |
| RQ6 | Scale effects? | Not tested this round (all ≤4B-class); round-2 item |

---

## 3. Methods

### 3.1 Models

| model | role | sampling (card-recommended) | budget |
|-------|------|------------------------------|--------|
| Qwen/Qwen3-4B-Thinking-2507 | reasoning | T=0.6, top_p=.95, top_k=20 | 81920 (AIME) / 32768 (rg) |
| Qwen/Qwen3-4B-Instruct-2507 | matched instruct | T=0.7, top_p=.8, top_k=20 | 16384 |
| google/gemma-4-E2B-it | non-Qwen hybrid (2.3B eff.) | T=1.0, top_p=.95, top_k=64 | 32768 |

All N=16 samples/question/condition, seed 0, vLLM 0.19.0 (FA3) offline with raw-string prompts. Gemma thinking via `<|think|>` system token; channel markers `<|channel>thought…<channel|>` (special tokens; generated with `skip_special_tokens=False`).

### 3.2 Tasks

AIME 2024+2025 (60 qs, integer answers, math_verify grading); reasoning_gym `maze` and `mini_sudoku` (50 qs each, seed 20260716, exact verifiers). Baselines all card-consistent (Qwen-thinking AIME pass@1 0.822 ≈ card's ~81; zero truncation at the 81920 budget).

### 3.3 Conditions (full definitions: `conditions_and_metrics.md`)

Sources × modes: {**self_wrong** (model's own wrong rollout), **irrelevant** (another question's trace), **corrupted** (correct trace, tail numbers perturbed), **wrong_conclusion** (bare confident assertion), **irrelevant_cross** (other-*domain* trace)} × {prefix_open at f ∈ {.25,.5,.75,1.0}, full_closed}. Only generated tokens are graded. **Matched-subset methodology:** cross-source comparisons use the intersection of questions that are solvable at baseline AND have self-wrong traces (instruct AIME n=33; thinking AIME n=23) because trace sources have difficulty-confounded coverage.

### 3.4 Metrics

pass@k (unbiased, k ≤ 16), adoption (answer ≡ injected trace's answer, math_verify equivalence), no-answer, truncation (gated at 2% with a budget-doubling validity check), post-injection think tokens, correction-marker counts, and a lexical target-engagement audit (`src/audit.py`).

---

## 4. Results

### 4.1 Dose-response and the completeness cliff (RQ1, RQ5)

Self-wrong prefixes, matched subsets, **pass@1 → pass@16**:

| f | thinking AIME (base .753/1.0) | instruct AIME (base .587/1.0) |
|---|-------------------------------|-------------------------------|
| .25 | .655 → **1.000** | .536 → .909 |
| .50 | .486 → **1.000** | .449 → .879 |
| .75 | .302 → .913 | .314 → .636 |
| 1.0 (open) | .024 → **.043** | .004 → .030 |
| closed | .003 → .043 | .000 → .000 |

Through 75% of its own wrong reasoning, the thinking model retains **full** pass@16 capability (sampling always recovers) — the wrong prefix only reshapes the answer distribution. At completeness, capability itself is destroyed, identically for both models. Reasoning training widens the recoverable region; it does not eliminate the cliff.

### 4.2 The open-block premium (RQ2)

pass@1, prefix-1.0-open minus full_closed (same injected content, only continuation right differs):

| condition | Qwen thinking | Qwen instruct | Gemma |
|-----------|---------------|----------------|-------|
| wrong_conclusion (maze) | **+0.862** | +0.043 | 0.000 |
| irrelevant (AIME, matched) | **+0.364** | +0.012 | +0.062 (maze −0.004) |
| self_wrong (AIME, matched) | +0.021 | +0.004 | +0.023 (AIME), +0.004 (maze) |

The premium exists only where (a) the model was trained to re-examine (Qwen-thinking) AND (b) the trace is recognizably not-its-own-completed-reasoning. Continued thinking is a *conditional* resource — models spend it on foreign material, never on auditing their own finished chains.

### 4.3 Thinking vs instruct, matched (RQ3)

Largest gaps (matched subsets, pass@1): irrelevant f=.25 on AIME **0.633 vs 0.085**; maze wrong_conclusion open **0.939 vs 0.043**; irrelevant f=1.0-open AIME 0.375 vs 0.042. Zero gaps: every full_closed cell; self_wrong f=1.0 (0.024 vs 0.004). With thinking denied, or with own-complete reasoning injected, the reasoning model behaves exactly like the instruct model.

### 4.4 Type of wrongness (RQ4) — ordered by triggered re-thinking

Thinking model, complete traces (open), with audit texture:

| injected content | pass@1 | continuation | switch phrases |
|------------------|--------|--------------|----------------|
| corrupted correct scaffold | ≥ baseline (.889–.952) | repairs silently | — |
| alien-domain trace (maze→AIME) | .545 | 10.6k tokens | 88% |
| bare wrong assertion (AIME) | .514 (maze: .939) | 18.7k tokens | 100% |
| same-domain irrelevant (AIME) | .375 | 9.8k tokens | 79% |
| own wrong reasoning (AIME) | **.024** | **1.1k tokens** | 35% (tokenistic) |

Recovery probability tracks continuation length — i.e., how much re-thinking the injection provokes. Notably: numeric corruption never propagates (models silently fix perturbed numbers; the mostly-correct scaffold *helps*, +0.14 over baseline), and the model's own completed reasoning provokes almost nothing — including when the model literally writes "wait" and concludes anyway (**seeing ≠ doubting**; `audit_thinking_aime.md`).

Instruct-model counterpart (`audit_instruct_aime.md`): **noticing without acting** — at irrelevant f=.25, 80% of continuations verbalize the mismatch and 57% re-engage the real question's numbers across 5.8k tokens, yet only 7% end correct; 45% still land on the donor answer and 45% on a third wrong answer.

### 4.5 Cross-family: Gemma-4-E2B (non-Qwen check)

Replicates: dose-response, the completeness cliff (open ≡ closed exactly, n=49 AIME + n=42 maze), corrupted-scaffold help, forced-answer adoption. Does NOT replicate: the open-block premium (≈0 on maze even for bare assertions — 0.000 vs Qwen's 0.939) and the mismatch reflex (complete alien trace on maze: 0.091 recovery vs Qwen's 0.782 — and cross-domain capture is *deeper* than same-domain, 0.091 < 0.216, the opposite ordering from Qwen). **A thought-channel format without reasoning-RL confers no injection robustness.** The universal results (F1/F2/F6/F10) are properties of autoregressive conditioning; the recovery behaviors (F4/F8) are properties of specific training.

---

## 5. Discussion

**Relation to prior work** (full review: `literature_review/`): Yang et al. 2025 (2506.10979) found reasoning models identify unhelpful thoughts but recover poorly; our audits add token-level mechanism (identification without re-examination) and our pass@k lens shows *where* recovery capability survives (partial prefixes) vs vanishes (completeness). Ballon et al. 2026 (2601.23163) found anchoring grows with trace fraction via MC probing; we confirm on free-form hard math and locate a sharp cliff rather than smooth growth — the fraction sweep matters less than whether the chain *concludes*. Lanham et al.'s early-answering/adding-mistakes framework predates reasoning models; our matched thinking/instruct pairs show their "post-hoc" reading now splits: answers are fully trace-determined at answer time (maximal faithfulness in one sense) while trace *content* can be causally overridden mid-stream by trained models. The Spurious-Rewards caveat (Qwen-specific effects) proved prescient — every *recovery* behavior we measured is Qwen-specific; every *vulnerability* is universal.

**Interpretation.** The results are consistent with a simple picture: an autoregressive model treats a completed-looking reasoning chain as a commitment device — the strongest next-token evidence about what the answer will be — regardless of the chain's correctness. Training (Qwen-style reasoning-RL) installs *interrupt conditions* (foreign content, missing derivation steps) that trigger re-thinking before the commitment point, but no model tested has an interrupt condition for "my own completed reasoning might be wrong." That is precisely the self-verification gap that self-correction literature documents at the response level, now shown to persist inside the thinking channel of RL-trained reasoners at their point of maximal capability (pass@16 = 1.0 questions).

**Practical implications.** (a) Prefill/injection attacks on reasoning channels are near-deterministic answer-steering primitives if the trace is complete and plausible — relevant to agent security. (b) Truncating/continuing another model's (or an earlier turn's) completed reasoning is unsafe as a compute-saving strategy; cutting at ≤75% is categorically safer than reusing finished chains. (c) Fresh sampling beats trace-repair: at any partial corruption level, resampling recovers (pass@16 ≈ 1.0) while the model cannot audit a finished chain.

---

## 6. Limitations

1. **Scale**: all models ≤4B-class; RQ6 untested. 2. **Two families**, one reasoning-RL recipe; "trained disposition" claims need an R1-lineage replication. 3. Some **thin cells** (Qwen-thinking maze self_wrong n=8) — flagged inline; the load-bearing versions are well-powered (n=23–49). 4. **Artifacts**, all documented and bounded: wrong_conclusion:full_closed rambling (31–53% truncation for thinking/Gemma; cell excluded from claims), Gemma's 15.9% AIME no-answer floor, maze same-domain answer collisions (~20%; cross-domain numbers used instead), baseline pass@16 = 1.0 by construction on matched subsets. 5. **Corruption type**: only rule-based numeric perturbation (reasoning-error corruption pending). 6. Injected traces are model-generated or templated, not human-written wrong reasoning.

---

## 7. Round-2 proposal (priority order)

1. **Scale sweep** (Qwen3.5-9B, Qwen3-14B, 30B-A3B-Thinking): does the completeness cliff move, and does the Yang-et-al. non-inverse-scaling effect appear? (2 GPU-days)
2. **R1-distill lineage** (DeepSeek-R1-0528-Qwen3-8B, cached): is the re-examination disposition recipe-general or Qwen-RL-specific? (1 GPU-day)
3. **"Wait"-append intervention**: force-append "Wait," after complete self-wrong traces — does a 1-token nudge unlock the re-examination the model doesn't initiate? Cheap, directly tests the commitment-device interpretation. (0.5 GPU-day)
4. **Reasoning-error corruption** (misapplied rule mid-trace, LLM-generated) vs our numeric corruption — does *logical* corruption propagate where arithmetic doesn't? (1 GPU-day)
5. Harder rg configs (larger mazes/9×9 sudoku) for self_wrong supply; N=32 on cliff-adjacent cells (f ∈ {.75, .9, 1.0} fine-grained — locate the cliff precisely); forced-close stop-string fix.
6. Stretch: cross-model traces (weak→strong), GPQA tier, activation-level probes of the "commitment" signal.

---

## Appendix: run provenance

| run | dir (`results/`) | role |
|-----|------------------|------|
| Qwen-thinking AIME base / inject | `base/inject_qwen3-4b-thinking_aime24_25` | §4.1–4.4 |
| Qwen-instruct AIME base (+32k) / inject | `base_qwen3-4b-instruct_aime24_25{,_32k}`, `inject_…` | §4.1–4.4, M1 |
| Qwen thinking/instruct maze | `{base,inject}_qwen3-4b-{thinking,instruct}_rg_maze` | §4.2–4.3 |
| Qwen thinking mini_sudoku | `{base,inject}_qwen3-4b-thinking_rg_mini_sudoku` | F7 |
| Qwen cross-domain | `inject_qwen3-4b-thinking_{rg_maze,aime}_cross` | §4.4 |
| Gemma AIME/maze/cross | `{base,inject}_gemma-4-e2b_*` | §4.5 |

Env: `ssrm_hopper` (vllm 0.19.0, FA3 sm_90) after migrating from `reasoning_gym` (broken sm_52 FA3 build — see daily 07-16 gotchas). All CPU tests: 26 passing.
