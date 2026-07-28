# Research Plan: Answering Correctly Despite Wrong Reasoning

**Project:** wrong_reason · **Started:** 2026-07-16 · **Status:** active

## 1. Research question

Given a model M (instruct or reasoning) and a question q, we force M to condition on an **incorrect thinking trace** t̃ before producing its answer — either a *prefix* of t̃ (model may continue thinking) or the *entire* t̃ (optionally with the think block closed, so the model must answer immediately). Sampling k answer attempts per question, we ask: **can the model still answer correctly (pass@k)?**

This probes three things at once:
1. **Causal dependence on the trace** — is the trace load-bearing for the answer, or does the model "know" the answer regardless (post-hoc rationalization / unfaithful CoT)?
2. **Recovery ability** — can reasoning-trained models detect and override injected wrong reasoning (backtracking, "wait, actually…"), and does this differ from instruct models?
3. **Distribution vs. capability** — does wrong reasoning destroy the ability to answer (pass@k collapses for all k) or merely shift the answer distribution (pass@1 drops but pass@k recovers)?

## 2. Research sub-questions & hypotheses

| RQ | Question | Hypothesis |
|----|----------|-----------|
| RQ1 | How does accuracy degrade with injected-prefix fraction f ∈ {0.25, 0.5, 0.75, 1.0}? | Monotone decrease; later injection = more commitment to the wrong path. |
| RQ2 | Open think block (model may keep thinking) vs. force-closed `</think>` (answer immediately): how much of recovery is due to *extra thinking tokens*? | Forced-close collapses accuracy toward the wrong trace's answer (adoption); open allows recovery. The gap isolates the value of continued thinking. |
| RQ3 | Reasoning model vs. matched instruct model (Qwen3-4B-Thinking-2507 vs Qwen3-4B-Instruct-2507; Qwen3.5-4B thinking vs non-thinking mode): who recovers better? | Reasoning-trained models recover more (RL instilled backtracking behaviors). |
| RQ4 | Does the *type* of wrongness matter? | Irrelevant traces hurt less than plausible-but-wrong self-generated traces; confident wrong conclusions hurt most in forced-close. |
| RQ5 | pass@k gap vs. k: does the baseline→injected gap shrink as k grows? | If injection mainly shifts the distribution, gap shrinks with k; capability is preserved. |
| RQ6 (stretch) | Scale & difficulty effects (4B → 9B → 14B/35B-A3B; GSM8K → MATH-500 → AIME → GPQA). | Larger models recover better; recovery is harder on harder problems (wrong trace is harder to distinguish from correct). |

## 3. Experimental design

### 3.1 Conditions (the core grid)

- **injection_mode:**
  - `none` — baseline pass@k (also harvests wrong traces for `self_wrong`).
  - `prefix_open(f)` — inject first f-fraction of a wrong trace inside `<think>`, model continues freely. f ∈ {0.25, 0.5, 0.75, 1.0}.
  - `full_closed` — inject the entire wrong trace and force `</think>`; model can only emit the final answer.
- **trace_source:**
  - `self_wrong` — a wrong-final-answer rollout of the *same model on the same question* (most natural: on-distribution wrong reasoning). Harvested from baseline runs.
  - `corrupted` — a *correct* trace with an early step corrupted (numbers/operators perturbed), truncated after the corruption. Controls for "off-distribution weirdness."
  - `irrelevant` — a trace from a *different* question (derangement). Controls: is the harm from *wrongness* or just *distraction*?
  - `wrong_conclusion` — short synthetic trace confidently asserting a wrong answer ("… so the answer is clearly X."). Maximal-commitment probe.
- **Instruct-model analog:** no think tags; inject the wrong reasoning as the prefilled beginning of the assistant response, model continues. The `full_closed` analog appends the full wrong reasoning + a transition ("\n\nTherefore, the final answer is") — measured separately since channel separation doesn't exist.

### 3.2 Models (all cached locally)

| Model | Role |
|-------|------|
| Qwen3-4B-Thinking-2507 | primary reasoning model |
| Qwen3-4B-Instruct-2507 | matched instruct control (same base, same data era) |
| Qwen3.5-4B | hybrid — thinking & non-thinking mode within *one* set of weights (cleanest within-model contrast) |
| DeepSeek-R1-0528-Qwen3-8B | different reasoning-training lineage (generalization check) |
| Qwen3.5-9B, Qwen3-14B / Qwen3-30B-A3B-Thinking-2507 | scale-up (stretch) |
| google/gemma-4-E2B-it (user-suggested 2026-07-17) | non-Qwen generalization check — hybrid via `<\|think\|>` control token; needs think-marker adapter (task #6) |

### 3.3 Datasets (decided 2026-07-16 with user)

- **AIME 2024 + 2025** (Maxwell-Jia/AIME_2024, MathArena/aime_2025) — primary hard tier, 60 qs, integer answers (clean grading via math_verify).
- **reasoning_gym procedural tasks** (`maze`, `mini_sudoku`; package v0.1.19) — primary non-math tier: unsaturated, infinite seeded supply, exact verifiers (`score_answer`). 50 qs each, seed 20260716.
- **MATH-500** — backup/if-time only (likely saturated for 2507-era models).
- **GSM8K / GPQA-Diamond** — stretch, later.

### 3.4 Sampling & measurement

- N = 16 samples per question per condition (user: at least 16; 32 acceptable for final numbers). pass@k via the unbiased estimator (Chen et al. 2021): pass@k = E_q[1 − C(n−c, k)/C(n, k)].
- Sampling params per official model cards — see `docs/experiments/model_generation_params.md`. Never greedy (k-attempt setting requires diversity; cards warn against greedy for thinking models).
- Max new tokens: 32,768 default (81,920 for AIME if truncation > 2%). **Always record truncation rate** = fraction of samples with `finish_reason == "length"`; flag any cell > 2%.

### 3.5 Metrics

| Metric | Definition |
|--------|-----------|
| pass@k | unbiased estimator, k ∈ {1, 2, 4, 8, (16)} |
| Δpass@k | baseline − injected, per cell |
| adoption rate | fraction of samples whose answer ≡ the injected trace's wrong answer |
| recovery rate | P(sample correct \| wrong-trace condition) = pass@1 under injection |
| no-answer rate | no parseable answer in *generated* tokens (separate from wrong) |
| truncation rate | finish_reason == "length" |
| post-injection think length | tokens generated inside `<think>` after the injected prefix |
| correction markers | frequency of "wait"/"actually"/"hmm"/"let me re-" in the continuation |

**Grading:** grade only *generated* tokens (never the injected text). For thinking models, extract from the final channel (after `</think>`); `\boxed{}` → math_verify equivalence (AIME: integer match). Truncated-before-`</think>` samples count as no-answer.

### 3.6 Implementation notes

- vLLM offline `LLM` API, raw-string prompts: render the chat template (`add_generation_prompt=True`, correct `enable_thinking` kwarg), then string-append `<think>\n` + injected trace prefix (+ `\n</think>\n\n` for full_closed). Per-model think-tag behavior is registered in `src/config.py` and verified by `scripts/check_templates.py` (Thinking-2507 templates already end with `<think>\n`; hybrid models don't).
- Prefix cuts at fraction f of *tokens*, snapped to the nearest sentence/newline boundary.
- Trace pairing is deterministic (seeded) so conditions are comparable across runs.

## 4. Phased schedule (next few hours, autonomous)

| Phase | What | Output |
|-------|------|--------|
| 0 (done) | Repo setup, code, CPU tests, template checks, GPU smoke test | this repo |
| 1 | **Baselines**: primary model on MATH-500(100) + AIME24/25, N=8 → harvests `self_wrong` traces; verify truncation rate | `results/baseline_*` |
| 2 | **Injection pilot**: `self_wrong`, f ∈ {0.25, 0.5, 0.75, 1.0} + `full_closed`, N=8 | `results/inject_*` |
| 3 | **Instruct/non-thinking contrast** on the same questions & traces | `results/inject_*` |
| 4 | Analysis notebook-style script → pass@k curves, adoption vs f; write up in daily doc | `docs/daily/2026-07-16.md`, plots in `results/` |

Compute estimate (pilot, 4B model, 2× H100): baseline ≈ 160 q × 8 = 1,280 gens; injection ≈ 5 conditions × 1,280 = 6,400 gens (mostly shorter continuations). Roughly 3–5 h wall-clock; phases 1–2 fit comfortably; run models on separate GPUs in parallel where possible.

## 5. Risks & mitigations

- **Truncation confound** — wrong prefixes may inflate think length past the budget → monitor truncation per cell; raise budget or report separately.
- **self_wrong availability** — easy questions yield few wrong rollouts → fall back to `corrupted`/`wrong_conclusion` for those; report coverage.
- **Prompt-format bugs** (off-by-one think tags) — template check script + unit tests before any GPU run.
- **Contamination of "recovery"** — model might ignore the prefix trivially if formatting looks foreign → keep traces on-distribution (self_wrong primary), inspect samples qualitatively.

## 6. Novelty positioning (to be refined by literature review)

Prior CoT-faithfulness work (early answering, adding mistakes — Lanham et al.) largely predates RL-trained *reasoning* models and measured single-sample accuracy. Our angle: (a) pass@k lens separating capability from distribution shift, (b) matched thinking/instruct pairs and hybrid single-weight models, (c) recovery *dynamics* (open vs. closed think block, prefix fraction sweep, correction markers). See `literature_review/` once the sweep completes.
