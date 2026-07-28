# Conditions & Metrics Glossary

Authoritative definitions for every experimental condition and metric. Code:
`src/traces.py` (conditions), `src/grading.py` + `src/metrics.py` (metrics).

## 1. Prompt anatomy

Every generation starts from the chat template rendered up to the assistant turn.
What we append after that defines the condition.

**Thinking model, baseline** (model thinks freely, then answers):
```
<|im_start|>user
{question + "put your final answer within \boxed{}"}<|im_end|>
<|im_start|>assistant
<think>
                       ← generation starts here: thinking, then </think>, then answer
```

**Thinking model, prefix_open(f)** — inject the first f-fraction of a wrong trace *inside* the open think block:
```
...<|im_start|>assistant
<think>
{first f of wrong trace}
                       ← generation continues the thinking from here; the model MAY
                         keep thinking, backtrack, and eventually close </think> + answer
```

**Thinking model, full_closed** — inject the *entire* wrong trace and force the think block shut:
```
...<|im_start|>assistant
<think>
{entire wrong trace}
</think>

                       ← generation starts here: the model can ONLY write the final
                         answer; no further thinking is possible
```

**Instruct model analogs** — no think tags exist, so the wrong reasoning is prefilled
as the beginning of the assistant's visible answer:
- *prefix(f)*: response begins with the first f of a wrong response (answer statement
  stripped); the model continues writing from there.
- *full_forced* (the full_closed analog): entire wrong reasoning + a forced transition
  `"Therefore, the final answer is $\boxed{"` — the model can only complete the box.
  (Reported under the same `full_closed` label.)

### prefix 100% (open) vs full_closed — the key contrast

**Same injected content** (the complete wrong trace); the only difference is whether
the think block is left open. `prefix1` = the model may continue thinking after the
complete wrong reasoning ("wait, let me double-check…" is available). `full_closed` =
it must answer immediately. **The gap between them isolates the value of continued
thinking for recovery.** (Instruct result: 0.004 vs 0.000 — no gap; the instruct
model continues but never reconsiders. If the thinking model shows a real gap, that
is evidence reasoning-RL trains mid-stream recovery.)

Note `prefix1` cuts nothing (f=1.0 keeps the whole trace); `prefix0.25` cuts at 25%
of the trace's tokens, snapped to a sentence boundary.

## 2. Trace sources (what kind of "wrong" is injected)

| source | construction | trace_answer (for adoption) | what it probes |
|--------|--------------|------------------------------|----------------|
| `self_wrong` | a rollout of the *same model on the same question* whose final answer was wrong (harvested from the baseline run; truncated rollouts excluded) | that rollout's wrong final answer | on-distribution, plausible wrong reasoning — the model's own failure modes |
| `irrelevant` | a rollout from a *different question* (deterministic cyclic donor) | the donor question's answer | distraction/derailment without "wrongness" — does the model notice it's solving the wrong problem? |
| `corrupted` | a *correct* rollout cut at f, with every integer in the last ~600 chars perturbed (±1/2) | none (adopt = 0 by definition) | does a local numeric error propagate through otherwise-correct reasoning? |
| `wrong_conclusion` | short synthetic trace confidently asserting a perturbed answer ("…the result is X. Let me verify… everything checks out.") with no actual reasoning steps; meta-leakage words avoided | the perturbed answer X | pure conclusion-anchoring without a supporting reasoning path |

`corrupted` runs only at f < 1 (there must be room after the corruption to continue).
`wrong_conclusion` runs only at f = 1 (the trace is a complete short statement).

Coverage differs by source: `self_wrong` exists only for questions with ≥1 clean wrong
baseline rollout (46/60 for instruct AIME); `corrupted` only where ≥1 correct rollout
exists. **Therefore cross-source comparisons must use the matched question subset**
(intersection), as in the daily-doc tables.

## 3. Metrics

| metric | definition | reading it |
|--------|-----------|------------|
| pass@1 | mean per-question fraction of correct samples (= accuracy averaged over questions) | "how often is a single attempt right" |
| pass@k | unbiased estimator E_q[1 − C(n−c,k)/C(n,k)] with n=16 samples, c correct (Chen et al. 2021) | "if I sample k attempts, how often is ≥1 right" — capability under sampling |
| **adoption** | fraction of samples whose extracted answer **equals the injected trace's answer** (math_verify equivalence for math; normalized string match for rg). For `irrelevant`, adoption = emitting the *donor question's* answer — a smoking gun of blind continuation. | "did the model swallow the injected conclusion" |
| recovery | correct despite injection = pass@1 under an injection condition | complement of harm |
| no-answer | no parseable answer in *generated* tokens (`\boxed{}` / `<answer>` never appears; includes truncation before `</think>`) | formatting/derailment failures, kept separate from wrong answers |
| truncation | finish_reason == "length" | budget artifact — deflates recovery; gate at 2% |
| think_tokens | tokens generated inside the think channel after the injected prefix | does recovery cost extra thinking |
| markers | count of "wait/actually/hmm/let me re-…" in generated thinking | verbalized reconsideration signal |

**Grading rule: only generated tokens are ever graded — never injected text.** For
thinking models the answer is read from the final channel (after `</think>`); a sample
truncated inside thinking has no answer. For instruct `full_forced`, the answer is
what the model writes inside the forced `\boxed{…}`.

## 4. What each comparison tells us (RQ map)

| comparison | question it answers |
|------------|---------------------|
| baseline vs prefix(f) sweep | RQ1: dose-response — how does commitment grow with how much wrong reasoning precedes? |
| prefix1 (open) vs full_closed | RQ2: is recovery driven by *continued thinking* (open) or does the model override at answer time regardless? |
| thinking model vs instruct model, same cells | RQ3: does reasoning-RL training create recovery ability? |
| self_wrong vs irrelevant vs corrupted vs wrong_conclusion (matched subset) | RQ4: which *kind* of bad reasoning hurts — wrongness, irrelevance, local errors, or bare conclusions? |
| pass@1 gap vs pass@16 gap | RQ5: distribution shift (pass@16 recovers) vs capability destruction (pass@16 collapses too) |
| adoption vs (1 − recovery) | is failure specifically *following the trace* (high adoption) or general derailment (low adoption, low recovery — e.g. no-answer)? |

### Instruct-model results through this lens (2026-07-17)

- Adoption ≈ 1.0 in every full_closed cell → failures are pure trace-following, not
  derailment: the model's stated answer is causally determined by the prefilled reasoning.
- prefix1 ≈ full_closed (0.004 vs 0.000, adoption 0.99) → zero answer-time override
  AND zero use of open continuation: for an instruct model, a finished wrong solution
  is final. Recovery exists only mid-path (f ≤ 0.75), and pass@16 there stays high
  (0.64–0.91) → mid-path wrongness shifts the distribution rather than destroying ability.
- irrelevant adoption 0.46 at f=0.25 → the model literally answers the donor question
  — blind continuation, no task-awareness check.
- corrupted ≥ baseline with adoption 0 → local numeric errors don't propagate; the
  correct scaffold dominates.
