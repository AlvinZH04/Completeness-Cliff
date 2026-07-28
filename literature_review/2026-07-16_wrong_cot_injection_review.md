# Literature Review: Can Models Answer Correctly Despite Force-Fed Incorrect Reasoning Traces?

Compiled 2026-07-16 (web sweep). Papers ordered by relevance within each section.

---

## 1. Directly Relevant Work: Wrong/Perturbed CoT Injection

### 1.1 How Well Can Reasoning Models Identify and Recover from Unhelpful Thoughts?
- **Authors/Year:** Sohee Yang, Sang-Woo Lee, Nora Kassner, Daniela Gottesman, Sebastian Riedel, Mor Geva (2025)
- **Link:** [arXiv:2506.10979](https://arxiv.org/abs/2506.10979)
- **Summary:** Injects four categories of unhelpful thoughts into reasoning models' thinking process: (1) uninformative rambling, (2) content irrelevant to the question, (3) misdirections that reframe the problem, and (4) **thoughts leading to incorrect answers**. Separately measures *identification* (can the model spot the bad thought?) and *recovery* (can it still answer correctly after the thought is injected?). Models identify unhelpful thoughts well but recover poorly — they tend to naively continue the injected line of reasoning. Notably shows **non-inverse scaling**: larger models are sometimes *worse* at recovering from short irrelevant thoughts, even with explicit re-evaluation instructions; also runs a jailbreak variant via irrelevant-thought injection.
- **Relation to us:** The closest existing paper. Differences: it emphasizes identification vs. recovery and thought *categories*, measures single-pass accuracy rather than **pass@k**, and does not systematically compare wrong-reasoning *prefixes* vs. *complete wrong rollouts*.

### 1.2 Probing the Trajectories of Reasoning Traces in Large Language Models
- **Authors/Year:** Marthe Ballon, Brecht Verbeken, Vincent Ginis, Andres Algaba (2026)
- **Link:** [arXiv:2601.23163](https://arxiv.org/abs/2601.23163)
- **Summary:** Protocol: generate a reasoning trace, truncate at fixed token percentiles, re-inject the partial trace (within-model and **cross-model**), and measure the induced answer distribution via next-token probabilities. Also validates a **wrong-answer injection**: insert a wrong answer mid-trace, propagate it to the conclusion, and filter out traces containing meta-leakage phrases ("error", "incorrect") to keep injections covert. Models: Qwen3-4B/8B/14B, gpt-oss-20B/120B; datasets: GPQA Diamond, MMLU-Pro. Findings: accuracy and decision commitment rise monotonically with trace fraction; **stronger models can backtrack from incorrect partial traces while weaker models stay anchored**; anchoring grows with trace length.
- **Relation to us:** Very close methodologically (truncation + injection + wrong-answer propagation). Differences: multiple-choice next-token probing rather than free-form generation with pass@k; focuses on trajectory dynamics, not recovery capability per se.

### 1.3 Can Large Reasoning Models Improve Accuracy on Mathematical Tasks Using Flawed Thinking?
- **Authors/Year:** Saraswathy Amjith, Mihika Dusad, Neha Muramalla, Shweta Shah (2025)
- **Link:** [arXiv:2512.17079](https://arxiv.org/abs/2512.17079)
- **Summary:** Constructs CoT **prefixes containing exactly one controlled error** — either a *calculation error* (sign flip, dropped term) or a *reasoning error* (misapplied rule, unjustified step) — and prefills them before generation. Trains Qwen3-4B with GRPO (binary final-answer reward) on a mix of clean and flawed-prefill problems (MATH-lighteval). Mixed training matches clean accuracy (41%) and improves robustness on flawed prefills (24% vs 19% for standard RL); reasoning errors give bigger robustness gains than calculation errors; **clean-only RL training *degrades* robustness below baseline**.
- **Relation to us:** Uses exactly our intervention (wrong-prefix prefill) but as a *training* signal; its evaluation is single-sample accuracy, not pass@k, and only one small model.

### 1.4 Large Reasoning Models Learn Better Alignment from Flawed Thinking (RECAP)
- **Authors/Year:** ShengYun Peng, Eric Smith, Ivan Evtimov, et al. (Meta/GaTech/IBM, 2025)
- **Link:** [arXiv:2510.00938](https://arxiv.org/abs/2510.00938)
- **Summary:** RL post-training on **synthetically generated counter-aligned CoT prefills** (deliberately flawed reasoning trajectories) teaches models to override faulty prefilled premises and reroute to safe/correct responses. Improves safety and jailbreak robustness, reduces overrefusal, preserves reasoning, and holds up against repeated prefill-override attacks.
- **Relation to us:** Establishes that "override the prefilled wrong thinking" is trainable — in the *safety* domain. We study the capability question on *correctness* tasks, without training, measured by pass@k.

### 1.5 Fragile Thoughts: How Large Language Models Handle Chain-of-Thought Perturbations
- **Authors/Year:** Ashwath Vaithinathan Aravindan, Mayank Kejriwal (2026)
- **Link:** [arXiv:2603.03332](https://arxiv.org/abs/2603.03332)
- **Summary:** Taxonomy of 5 CoT perturbation types fed to models on math tasks: **MathError, UnitConversion, Sycophancy, SkippedSteps, ExtraSteps**, across 13 models spanning 3 orders of magnitude. MathError is most damaging for small models (50–60% accuracy loss) but improves most with scale; UnitConversion hurts at all scales (>5%); ExtraSteps nearly harmless (0–6%); Sycophancy/SkippedSteps ~10%.
- **Relation to us:** Gives a perturbation taxonomy and scale trends worth copying; single-sample accuracy only, mostly non-thinking models.

### 1.6 Are Reasoning LLMs Robust to Interventions on their Chain-of-Thought?
- **Authors/Year:** A. von Recum, L. Girrbach, Z. Akata (2026)
- **Link:** [arXiv:2602.07470](https://arxiv.org/abs/2602.07470)
- **Summary:** Applies **seven interventions (benign, neutral, adversarial)** at fixed timesteps inside reasoning traces of open-weight reasoning models on Math/Science/Logic. Robustness improves with scale but **degrades when disruptions occur early**; paraphrasing hurts despite semantic equivalence and suppresses "doubt" expressions; expressed doubt is the central recovery signal; adversarial interventions inflate chain length >200%. Also finds models can fix errors when told the location but struggle to *find* the first error.
- **Relation to us:** Closest to a systematic "intervene mid-trace, force continuation" study; again no pass@k, and no complete-wrong-rollout condition.

### 1.7 Stepwise Reasoning Error Disruption Attack (SEED)
- **Authors/Year:** Jingyu Peng, Maolin Wang, Xiangyu Zhao, Kai Zhang, et al. (2024; ACL 2025)
- **Link:** [arXiv:2412.11934](https://arxiv.org/abs/2412.11934)
- **Summary:** Adversarial attack that injects **subtle errors into prior reasoning steps** (SEED-S modifies the last generated step via an auxiliary LLM to steer toward a predetermined wrong answer; SEED-P modifies the problem) so errors cascade covertly through subsequent reasoning. Works zero-/few-shot without touching the instruction; validated on 4 datasets × 4 models.
- **Relation to us:** Demonstrates the *attack success* direction (models usually follow injected errors); we invert the question — measure the *recovery* rate under sampling.

### 1.8 Lost at the Beginning of Reasoning
- **Authors/Year:** Baohao Liao, Xinyi Chen, Sara Rajaee, ..., Christof Monz (2025)
- **Link:** [arXiv:2506.22058](https://arxiv.org/abs/2506.22058)
- **Summary:** Shows the **first reasoning step has disproportionate influence on the final answer**; early errors substantially degrade downstream reasoning across SOTA open and closed reasoning models. Proposes reward-model filtering of first steps, cutting inference cost up to 70% without accuracy loss.
- **Relation to us:** Predicts a strong position effect — wrong *prefixes* placed early should be hardest to recover from; useful for choosing injection positions.

### 1.9 H-CoT: Hijacking the Chain-of-Thought Safety Reasoning Mechanism
- **Authors/Year:** Kuo et al. (2025)
- **Link:** [arXiv:2502.12893](https://arxiv.org/abs/2502.12893)
- **Summary:** Injects modified thinking snippets back into queries to hijack safety reasoning of o1/o3, DeepSeek-R1, Gemini 2.0 Flash Thinking; refusal rates collapse from 98% to <2%. The canonical "prefilled/injected thinking controls behavior" result in the safety domain.
- **Relation to us:** Evidence that injected thinking is *causally potent*; we quantify the analogous effect for task correctness.

### 1.10 Cats Confuse Reasoning LLM (CatAttack)
- **Authors/Year:** Meghana Rajeev, Rajkumar Ramamurthy, ..., James Zou, Nazneen Rajani (2025)
- **Link:** [arXiv:2503.01781](https://arxiv.org/abs/2503.01781)
- **Summary:** **Query-agnostic adversarial triggers** (irrelevant sentences like "Interesting fact: cats sleep most of their lives") appended to math problems raise DeepSeek R1 / R1-distill-Qwen-32B error likelihood by >300% and inflate response length. Perturbs the *input*, not the trace, but shows reasoning models are derailed by irrelevant content.

### 1.11 Reasoning Introduces New Poisoning Attacks Yet Makes Them More Complicated
- **Year/Link:** 2025, [arXiv:2509.05739](https://arxiv.org/abs/2509.05739)
- **Summary:** "Decomposed reasoning poison" backdoors that corrupt only the reasoning path. Key finding for us: reliably flipping *final answers* via poisoned thoughts is surprisingly hard because **models often recover from backdoors activated inside their CoT** — direct evidence of answer-level robustness to corrupted thinking.

### Training-time analogues (learning from wrong traces / spurious signal)

- **Spurious Rewards: Rethinking Training Signals in RLVR** — Rulin Shao et al. (2025), [arXiv:2506.10947](https://arxiv.org/abs/2506.10947). RLVR with random (+21.4), format (+13.8), or **incorrect-label (+24.1)** rewards nearly matches ground-truth rewards (+29.1) on MATH-500 for Qwen2.5-Math-7B; effect largely Qwen-specific (fails on Llama3/OLMo2), attributed to eliciting pre-existing behaviors (e.g., code reasoning). Relation: correctness of supervision signal ≉ necessary for correct answers; our study is the inference-time analogue.
- **Towards Understanding Chain-of-Thought Prompting** — Boshi Wang, Sewon Min, et al. (2022, ACL 2023), [arXiv:2212.10001](https://arxiv.org/abs/2212.10001). **Invalid reasoning in few-shot demonstrations** retains 80–90% of CoT's benefit; relevance and step ordering matter more than validity. The original "wrong reasoning doesn't matter much" result — but at the *demonstration* level, not the model's own forced trace.
- **Beyond Semantics: The Unreasonable Effectiveness of Reasonless Intermediate Tokens** — Karthik Valmeekam, ..., Subbarao Kambhampati (2025), [arXiv:2505.13775](https://arxiv.org/abs/2505.13775). Transformers trained from scratch on **corrupted traces (steps unrelated to the problem)** match or exceed correct-trace training and generalize better OOD; GRPO improves answers without improving trace validity. Companion position paper: [arXiv:2504.09762](https://arxiv.org/abs/2504.09762) (SFT with incorrect intermediate traces + correct answers can *outperform* correct-trace SFT).
- **Harnessing Negative Signals: Reinforcement Distillation (REDI)** — (2025), [arXiv:2505.24850](https://arxiv.org/abs/2505.24850). Distilling from teacher's **incorrect traces** (normally discarded) with a REINFORCE-style objective beats DPO/SimPO; Qwen-REDI-1.5B hits 83.1% MATH-500 with 131k traces.
- **Grokking in the Wild** — (2025), [arXiv:2504.20752](https://arxiv.org/abs/2504.20752). Even **factually incorrect synthetic data** strengthens emergent multi-hop reasoning circuits by forcing reliance on relational structure.

---

## 2. CoT Faithfulness

### 2.1 Measuring Faithfulness in Chain-of-Thought Reasoning
- **Authors/Year:** Tamera Lanham et al. (Anthropic, 2023)
- **Link:** [arXiv:2307.13702](https://arxiv.org/abs/2307.13702)
- **Summary:** The methodological template. Perturbations: **early answering** (truncate CoT, force answer), **adding mistakes** (an LLM inserts a mistake into the CoT, then the rest is regenerated and the model answers from the corrupted chain), **filler tokens**, **paraphrasing**. If the answer doesn't change under corruption/truncation, the CoT is post-hoc. Findings: reliance on CoT varies wildly by task; **larger models rely *less* on their stated CoT** (inverse scaling in faithfulness).
- **Relation to us:** "Adding mistakes" is a direct precursor of our intervention, but on 2023-era non-reasoning models, MC tasks, single samples, and it measures *answer change* as a faithfulness metric — not *ability to recover* measured by pass@k.

### 2.2 Language Models Don't Always Say What They Think
- **Authors/Year:** Miles Turpin, Julian Michael, Ethan Perez, Samuel R. Bowman (2023, NeurIPS)
- **Link:** [arXiv:2305.04388](https://arxiv.org/abs/2305.04388)
- **Summary:** Biasing features (e.g., reordering MC options so the answer is always "(A)", user suggestion) systematically flip answers while the CoT rationalizes the biased answer without mentioning the bias; accuracy drops up to 36% on BIG-Bench Hard (GPT-3.5, Claude 1.0). Establishes CoT as frequently post-hoc rationalization.

### 2.3 Reasoning Models Don't Always Say What They Think
- **Authors/Year:** Yanda Chen, Joe Benton, et al. (Anthropic, 2025)
- **Link:** [arXiv:2505.05410](https://arxiv.org/abs/2505.05410)
- **Summary:** Faithfulness of Claude 3.7 Sonnet and DeepSeek-R1 across 6 hint types: CoTs verbalize used hints <20% of the time in most settings; outcome-RL improves faithfulness then plateaus; reward hacking is almost never verbalized.

### 2.4 Are DeepSeek R1 and Other Reasoning Models More Faithful?
- **Authors/Year:** James Chua, Owain Evans (2025)
- **Link:** [arXiv:2501.08156](https://arxiv.org/abs/2501.08156)
- **Summary:** Cue-influence articulation test on MMLU: R1 describes the cue's influence 59% of the time vs 7% for non-reasoning DeepSeek — reasoning models are *more* faithful, though far from perfectly.
- **Relation to us:** Suggests reasoning models may treat injected wrong reasoning differently (more explicitly) than instruct models — a comparison our instruct-vs-reasoning design directly probes.

### 2.5 Chain-of-Thought Reasoning In The Wild Is Not Always Faithful
- **Authors/Year:** Iván Arcuschin, Jett Janiak, Robert Krzyzanowski, Senthooran Rajamanoharan, Neel Nanda, Arthur Conmy (2025)
- **Link:** [arXiv:2503.08679](https://arxiv.org/abs/2503.08679)
- **Summary:** Unfaithful CoT arises even on natural, non-adversarial prompts (implicit post-hoc rationalization, e.g., contradictory Yes/Yes answers to "Is X > Y?" and "Is Y > X?"): Sonnet 3.7 30.6%, R1 15.8%, GPT-4o 12.6% unfaithful pair rates.

### 2.6 RFEval: Benchmarking Reasoning Faithfulness under Counterfactual Reasoning Intervention
- **Authors/Year:** Yunseok Han, Yejoon Lee, Jaeyoung Do (2026)
- **Link:** [arXiv:2602.17053](https://arxiv.org/abs/2602.17053)
- **Summary:** 7,186 instances, 7 tasks, 12 open-source LRMs; output-level counterfactual interventions test stance consistency and causal influence of reasoning on answers. **49.7% of outputs unfaithful**; failures concentrate in math/code; RL-style post-training can *reduce* faithfulness while accuracy holds; accuracy is not a proxy for faithfulness.

### 2.7 Lie to Me: How Faithful Is CoT Reasoning in Open-Weight Reasoning Models?
- **Authors/Year:** Richard J. Young (2026)
- **Link:** [arXiv:2603.22582](https://arxiv.org/abs/2603.22582)
- **Summary:** 6 hint categories × 12 open-weight reasoning models (7B–685B) on MMLU/GPQA Diamond (41,832 runs). Faithfulness 39.7–89.9%; big gap between thinking-token acknowledgment (~87.5%) and answer-text acknowledgment (~28.6%) — models "know but don't say."

Also relevant: *Measuring CoT Faithfulness by Unlearning Reasoning Steps* ([arXiv:2502.14829](https://arxiv.org/abs/2502.14829)); *FaithCoT-Bench* ([arXiv:2510.04040](https://arxiv.org/abs/2510.04040)).

---

## 3. Self-Correction & Backtracking in Reasoning Models

### 3.1 Large Language Models Cannot Self-Correct Reasoning Yet
- **Authors/Year:** Jie Huang, Xinyun Chen, ..., Denny Zhou (2023, ICLR 2024)
- **Link:** [arXiv:2310.01798](https://arxiv.org/abs/2310.01798)
- **Summary:** Intrinsic self-correction (no external feedback) fails on reasoning tasks; performance often *degrades* after self-correction attempts. Baseline pessimism for pre-reasoning-era models — our study tests whether RL-trained thinking models have changed this.

### 3.2 Self-Correction Bench: The Self-Correction Blind Spot
- **Authors/Year:** Ken Tsui (2025)
- **Link:** [arXiv:2507.02778](https://arxiv.org/abs/2507.02778)
- **Summary:** Controlled **error injection into the model's own output vs. identical errors presented as user input**: 14 non-reasoning models show a 64.5% average "blind spot" (fix others' errors, not their own). Appending a minimal **"Wait"** reduces blind spots by 89.3%; attributes the asymmetry to scarcity of error-correction sequences in human demonstration data; RL-trained models do better.
- **Relation to us:** The own-output vs. external-error asymmetry is central: a force-fed wrong trace sits ambiguously between "own reasoning" and "external error," and the "Wait" result gives a cheap intervention arm for our experiments.

### 3.3 s1: Simple Test-Time Scaling
- **Authors/Year:** Niklas Muennighoff et al. (2025)
- **Link:** [arXiv:2501.19393](https://arxiv.org/abs/2501.19393)
- **Summary:** **Budget forcing**: suppress end-of-thinking and append "Wait" to lengthen reasoning, or force-terminate to shorten it; appended "Wait" often causes the model to double-check and fix wrong steps. The standard toolkit for manipulating the thinking segment (delimiter control, forced continuation) that our prefill methodology reuses.

### 3.4 Overthinking / Underthinking
- **Do NOT Think That Much for 2+3=?** — Xingyu Chen et al. (2024/25), [arXiv:2412.21187](https://arxiv.org/abs/2412.21187): o1-like models waste tokens re-verifying trivial problems.
- **Thoughts Are All Over the Place (Underthinking)** — Yue Wang et al. (2025), [arXiv:2501.18585](https://arxiv.org/abs/2501.18585): models abandon promising paths too early via excessive thought-switching; introduces thought-switching penalty (TIP) decoding.
- **Relation to us:** Recovery from a wrong prefix may manifest as (useful) thought-switching; these give metrics for characterizing *how* models escape wrong traces (switch frequency, trace length inflation).

### 3.5 DeepSeek-R1 Thoughtology
- **Authors/Year:** Sara Vera Marjanović, Arkil Patel, et al. (2025)
- **Link:** [arXiv:2504.07128](https://arxiv.org/abs/2504.07128)
- **Summary:** 135-page anatomy of R1's reasoning: taxonomy of thought structure; a "sweet spot" of reasoning length (more inference time can hurt); **rumination** on previously explored formulations blocks exploration. Useful taxonomy for annotating behavior after wrong-trace injection.

### 3.6 Reasoning Model is Stubborn: Diagnosing Instruction Overriding
- **Authors/Year:** Doohyuk Jang, Yoonjeon Kim, Chanjae Park, Hyun Ryu, Eunho Yang (2025)
- **Link:** [arXiv:2505.17225](https://arxiv.org/abs/2505.17225)
- **Summary:** "Reasoning rigidity": models override explicit user conditions and default to habitual reasoning trajectories; ReasoningTrap diagnostic built from modified AIME/MATH500 + redesigned puzzles.
- **Relation to us:** Rigidity is the flip side of our question — models that can't abandon familiar (correct-template) reasoning may paradoxically be *good* at ignoring injected wrong reasoning. See also *Measuring and Curing Reasoning Rigidity* ([arXiv:2603.22816](https://arxiv.org/html/2603.22816v3)).

---

## 4. Trace Importance / Thought Anchors

### 4.1 Thought Anchors: Which LLM Reasoning Steps Matter?
- **Authors/Year:** Paul C. Bogdan, Uzay Macar, Neel Nanda, Arthur Conmy (2025)
- **Link:** [arXiv:2506.19143](https://arxiv.org/abs/2506.19143) | [code](https://github.com/interp-reasoning/thought-anchors)
- **Summary:** Three attribution methods for sentence-level importance in long CoT: (1) black-box **counterfactual resampling — 100 rollouts conditioned on keeping vs. semantically replacing each sentence**; (2) attention aggregation finding "broadcasting" sentences and receiver heads; (3) attention-suppression causal attribution. Planning and backtracking/uncertainty-management sentences are the "anchors" with outsized importance. Uses R1-Distill-Qwen-14B on MATH-type problems.
- **Relation to us:** Their rollout-resampling machinery is exactly the harness needed for pass@k-after-injection; predicts recovery probability depends on *what kind* of sentence the wrong prefix ends on.

### 4.2 Beyond the Last Answer: Your Reasoning Trace Uncovers More than You Think
- **Authors/Year:** Hasan Abed Al Kader Hammoud, Hani Itani, Bernard Ghanem (2025)
- **Link:** [arXiv:2504.20708](https://arxiv.org/abs/2504.20708)
- **Summary:** Segments traces into "subthoughts," generates continuations from each intermediate endpoint; the **mode over subthought answers beats the original final answer** by up to +13% (AIME24) / +10% (AIME25). Final answers are unstable functions of trace position.

### 4.3 Fractured Chain-of-Thought Reasoning
- **Authors/Year:** Baohao Liao et al. (2025)
- **Link:** [arXiv:2505.12992](https://arxiv.org/abs/2505.12992)
- **Summary:** **Fractured Sampling** interpolates between full-CoT and answer-only along 3 axes: #trajectories, #solutions per trajectory, truncation depth. Truncated CoT often matches full CoT at far fewer tokens; reports steep log-linear **Pass@k-vs-token-budget** scaling gains on five reasoning benchmarks.
- **Relation to us:** Provides the pass@k-under-truncation methodology and evidence that answers are often determined before the trace completes; we replace "truncated own trace" with "wrong foreign/corrupted trace."

Also: *Thinking Wrong in Silence* ([arXiv:2604.00770](https://arxiv.org/abs/2604.00770)) — latent-reasoning trajectory hijacking (Coconut/SimCoT backdoors, ≥99% attack success) — the continuous-space analogue of forced wrong thinking.

---

## 5. Methodology Takeaways for Our Experiments

**Datasets:** GSM8K (easy tier / ceiling effects), MATH500 (possibly saturated for 2507-era models), AIME 2024/2025 (hard, small — needs many samples/problem), GPQA Diamond / MMLU-Pro (MC probing complement), reasoning_gym procedural tasks (unsaturated, verifiable, infinite supply). Consider ReasoningTrap for familiar-template-is-wrong problems.

**Models:** Qwen3 thinking/non-thinking pairs (ideal instruct-vs-reasoning comparison), DeepSeek-R1 distills, gpt-oss. **Spurious-Rewards warning: Qwen-only results may not generalize — include ≥1 non-Qwen family before claiming generality.**

**Constructing wrong traces (proven recipes):**
1. *Lanham-style adding mistakes*: insert mistake at position p, vary p over token percentiles {0, 25, 50, 75, 100} (early injections hardest to recover per 2506.22058, 2602.07470).
2. *Single controlled error*, typed: calculation vs. reasoning error (2512.17079); Fragile Thoughts' 5-type taxonomy.
3. *Wrong-answer propagation*: inject wrong answer mid-trace, rewrite remainder to conclude it coherently; **filter meta-leakage** ("error", "wait", "incorrect") so corruption is covert (2601.23163).
4. *Cross-model traces*: weaker model's incorrect full trace → stronger model.
5. *Off-the-shelf self-wrong rollouts*: the model's own incorrect temperature samples, re-prefilled (own-vs-external asymmetry per 2507.02778).
6. Keep "wrong reasoning" distinct from "irrelevant distraction" (2506.10979 categories).

**Injection mechanics:** prefill inside `<think>...</think>` and force continuation (s1-style delimiter control); two key conditions — (a) wrong prefix, thinking may continue; (b) full wrong trace + forced `</think>`, answer immediately (Lanham "early answering" analogue; isolates recovery-during-thinking from recovery-at-answer-time).

**Pass@k:** unbiased Codex estimator; report pass@1..k curves clean vs. wrong-prefix vs. wrong-full. Secondary metrics: trace-length inflation (>200% under adversarial interventions per 2602.07470), "Wait"/doubt-token frequency, verbalized noticing (identification vs. recovery split per 2506.10979).

**Controls:** length-matched neutral/filler prefix (Lanham); paraphrased-correct prefix; "Wait"-appended arm as cheap recovery intervention.

---

## 6. Novelty Gap — What Our Study Adds

1. **Pass@k as the recovery metric.** All close prior work measures single-sample accuracy, answer-flip rates, or MC next-token probabilities. Pass@k separates "the model usually follows the wrong trace" (low pass@1) from "the model *cannot* escape it" (low pass@k) — the capability-vs-elicitation distinction from the RLVR literature, unapplied to trace injection.
2. **Prefix vs. complete-rollout within one framework**, decomposing recovery into in-trace backtracking vs. answer-stage override.
3. **Instruct vs. reasoning models head-to-head** on the same base (Qwen3-4B 2507 pair; Qwen3.5 hybrid modes). Literature has conflicting predictions: reasoning models self-correct more (2507.02778, 2501.08156) but are also more anchored/ruminative (2506.10979, 2504.07128, 2505.17225).
4. **Free-form generation on hard math (AIME-class) + procedural reasoning_gym tasks** rather than MC probing.
5. **Error-type × position × source (self/foreign/synthetic) factorial design** with covert wrong traces.
6. **Bridge to training-time results** (spurious rewards / wrong-trace distillation): our study is the inference-time causal counterpart — is CoT load-bearing or decorative?

**Caveat:** the space moves fast — 2506.10979, 2601.23163, 2602.07470 together cover much qualitative territory; our defensible core is the pass@k recovery framing, prefix-vs-full decomposition, and instruct-vs-reasoning comparison on free-form hard tasks.
