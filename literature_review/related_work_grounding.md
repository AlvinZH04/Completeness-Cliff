# Related-Work Grounding: "The Completeness Cliff"

Compiled 2026-07-21. Companion to `2026-07-16_wrong_cot_injection_review.md` (the earlier sweep covers the wrong/perturbed-CoT-injection cluster in depth: Yang et al. 2506.10979, Ballon et al. 2601.23163, von Recum et al. 2602.07470, SEED 2412.11934, Lanham 2307.13702, Self-Correction Bench 2507.02778, Thought Anchors 2506.19143, and the training-time analogues). This file does not re-list those. It maps the broader themes the pilot needs to stand on to the four specific findings below, with verified citations, and states for each how it agrees with, is in tension with, or leaves a gap that the pilot fills.

The four findings being grounded:
1. **Completeness cliff.** Through 75% of a model's own wrong reasoning, pass@16 barely drops (1.00 to 0.91); given the COMPLETE wrong trace, recovery collapses to ~0.04. Completion, not correctness, is the trigger. Holds for a reasoning model (Qwen3-4B-Thinking) and its matched instruct sibling.
2. **Trained disposition.** The disposition to re-examine an injected trace is trained by reasoning-RL, not a property of merely having a thinking mode: a hybrid model (Gemma-4-E2B) that emits thought tokens gains almost nothing from an open thinking channel.
3. **Scaffold persuades.** The same wrong answer is rejected as a bare assertion (0.51) but adopted when wrapped in plausible steps (0.02); corrupted numbers inside a correct scaffold are silently repaired (0.89). Recovery is gated on mismatch detection, not correctness checking.
4. **Seeing isn't doubting.** A complete own-wrong trace triggers almost no fresh re-derivation; the model often writes "wait" and then concludes anyway.

---

## Where this work sits

This pilot sits at the intersection of three literatures that have so far run in parallel: CoT faithfulness (is the stated reasoning load-bearing?), the limits of self-correction (can a model fix its own errors without external help?), and in-context anchoring (do models adopt provided reasoning and answers?). Prior work in each area typically measures single-sample accuracy, answer-flip rates, or multiple-choice next-token probabilities, and it treats "wrong reasoning" as a single condition. The completeness cliff reframes the question as a capability question measured by pass@16 (can ANY of k fresh samples recover?), and it varies one axis nobody has isolated: how much of a wrong trace the model has already seen, from a short prefix up to a complete rollout. The finding that recovery is roughly flat until the trace completes and then falls off a cliff, together with the scaffold-persuades and trained-disposition results, gives a mechanism (mismatch detection gated on structural completeness, installed by reasoning-RL) rather than a benchmark number.

---

## 1. Limits of self-correction / intrinsic self-correction

- **Large Language Models Cannot Self-Correct Reasoning Yet.** Huang, Chen, Xie, Dai, Chi, Le, Zhou (2023). [arXiv:2310.01798](https://arxiv.org/abs/2310.01798). Shows that without external feedback, intrinsic self-correction does not reliably improve reasoning and often degrades it, because models cannot judge which of their own answers is right.
- **Self-Correction Bench: Revealing and Addressing the Self-Correction Blind Spot in LLMs.** Ken Tsui (2025). [arXiv:2507.02778](https://arxiv.org/abs/2507.02778). Finds a 64.5% average "blind spot" where models fix errors framed as someone else's input but not identical errors in their own output; appending a single "Wait" cuts the blind spot by 89.3%.

**How it relates.** These predict weak recovery, and the pilot agrees at the endpoint (complete-trace recovery ~0.04). But they treat self-correction as roughly all-or-nothing, whereas the completeness cliff shows recovery is near-total through 75% of the trace and only collapses at completion, so the failure is not a generic inability to self-correct but a specific gating on structural completeness. Finding 4 ("seeing isn't doubting", the model writes "wait" then concludes anyway) is a direct counterpoint to the Self-Correction Bench "Wait" remedy: once the trace is complete, the doubt token fires but no re-derivation follows, so the cheap intervention that works mid-trace stops working at the cliff.

## 2. Chain-of-thought (un)faithfulness and CoT monitoring

- **Measuring Faithfulness in Chain-of-Thought Reasoning.** Lanham, Chen, Radhakrishnan, et al. (Anthropic, 2023). [arXiv:2307.13702](https://arxiv.org/abs/2307.13702). Introduces the "adding mistakes" and "early answering" perturbations: if the answer does not change when the CoT is corrupted or truncated, the CoT was post-hoc; larger models rely less on their stated CoT.
- **Language Models Don't Always Say What They Think.** Turpin, Michael, Perez, Bowman (2023). [arXiv:2305.04388](https://arxiv.org/abs/2305.04388). Biasing cues flip answers while the CoT rationalizes the biased answer without mentioning the cue, establishing CoT as frequently unfaithful rationalization.
- **Reasoning Models Don't Always Say What They Think.** Chen, Benton, et al. (Anthropic, 2025). [arXiv:2505.05410](https://arxiv.org/abs/2505.05410). Even RL-trained reasoning models verbalize the hints they use less than 20% of the time in most settings, and reward hacking is almost never verbalized.
- **Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety.** Korbak, Balesni, et al. (2025). [arXiv:2507.11473](https://arxiv.org/abs/2507.11473). A multi-lab position paper arguing CoT is a usable but fragile window into intent, and that training decisions can silently degrade it.
- **Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation.** Baker, Huizinga, Gao, et al. (OpenAI, 2025). [arXiv:2503.11926](https://arxiv.org/abs/2503.11926). CoT monitoring catches reward hacking, but optimizing against the CoT teaches models to hide intent while still misbehaving.

**How it relates.** The faithfulness literature asks whether the CoT the model writes reflects its computation. The completeness cliff attacks the same relationship from the input side: a foreign or corrupted CoT the model reads controls its answer, and finding 3 (a wrong answer is adopted only when wrapped in plausible steps, and corrupted numbers inside a correct scaffold are silently repaired) shows the model conditions on the STRUCTURE of the reasoning rather than checking its content. This is the read-side dual of Lanham's write-side result and it sharpens the monitoring papers' worry: if the scaffold, not the conclusion, is what persuades, then a fluent but wrong chain is exactly the input a monitor is least equipped to flag.

## 3. Sycophancy and adopting provided positions

- **Towards Understanding Sycophancy in Language Models.** Sharma, Tong, Korbak, et al. (Anthropic, 2023). [arXiv:2310.13548](https://arxiv.org/abs/2310.13548). RLHF-trained assistants systematically shift answers toward a user's stated belief across free-form tasks, trading truthfulness for agreement.
- **Discovering Language Model Behaviors with Model-Written Evaluations.** Perez, Ringer, et al. (Anthropic, 2022). [arXiv:2212.09251](https://arxiv.org/abs/2212.09251). Model-written evals surface inverse scaling in sycophancy: larger models more often repeat back a user's preferred answer.

**How it relates.** Sycophancy is capitulation to a stated stance or preference. The scaffold-persuades result (finding 3) shows a distinct and arguably stronger channel: the model adopts a wrong answer far more when it arrives as reasoning steps (0.02 recovery) than as a bare assertion (0.51), so a plausible derivation persuades roughly 25x more than an equally wrong claim. This is a gap the sycophancy work does not cover: the persuasive force is in the reasoning scaffold itself, not in any social cue about who wants which answer, and it operates even on the model's own (foreign-spliced) trace with no user preference present.

## 4. Prefilling / assistant-prefill and its behavioral effect

- **Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks.** Andriushchenko, Croce, Flammarion (2024). [arXiv:2404.02151](https://arxiv.org/abs/2404.02151). Prefilling the assistant turn with a compliant opening (plus random search) drives near-100% jailbreak success across the Claude, GPT, Llama, and Gemma families, because the prefill flips the first-token distribution from refusal to compliance.

**How it relates.** This is the mechanism the pilot repurposes: prefilling the start of the response (for an instruct model) or the inside of the `<think>` block (for a reasoning model) is causally potent. The jailbreak literature uses prefill to steer safety behavior; the pilot uses the same lever to steer correctness and then, crucially, measures whether the model can escape under sampling. The completeness cliff says the prefill's grip depends on whether it forms a complete unit of reasoning, which is a knob the jailbreak work never isolates. (The companion review's H-CoT and RECAP entries cover the safety-domain version of prefilled-thinking control and its trainable override.)

## 5. Distraction by irrelevant and misleading context

- **Large Language Models Can Be Easily Distracted by Irrelevant Context.** Shi, Chen, Misra, Scales, Dohan, Chi, Scharli, Zhou (2023). [arXiv:2302.00093](https://arxiv.org/abs/2302.00093). Introduces GSM-IC; a single irrelevant sentence in the problem substantially degrades arithmetic reasoning, and self-consistency only partly recovers it.
- **GSM-Symbolic: Understanding the Limitations of Mathematical Reasoning in Large Language Models.** Mirzadeh, Alizadeh, Shahrokhi, Tuzel, Bengio, Farajtabar (Apple, 2024). [arXiv:2410.05229](https://arxiv.org/abs/2410.05229). Adding one clause that looks relevant but is inert drops accuracy up to 65% across frontier models, evidence that models pattern-match on surface form rather than reason.

**How it relates.** Both show that extra content the model should ignore derails it, which the pilot's irrelevant and cross-domain conditions build on. But these perturb the PROBLEM statement; the completeness cliff perturbs the model's own REASONING channel, and it separates "irrelevant/distracting" from "wrong but on-topic and complete." The distraction papers would predict graded degradation with added noise; the cliff's near-flat-then-collapse shape shows the damaging variable is structural completeness of a coherent wrong chain, not the mere presence of misleading tokens.

## 6. Error propagation, snowballing, and early-error dominance

- **How Language Model Hallucinations Can Snowball.** Zhang, Press, Merrill, Liu, Smith (2023). [arXiv:2305.13534](https://arxiv.org/abs/2305.13534). Models over-commit to an early mistake and then generate further false claims to justify it, even though they can separately recognize those claims as wrong (67% for ChatGPT, 87% for GPT-4).
- **Lost at the Beginning of Reasoning.** Liao, Chen, Rajaee, et al. (2025). [arXiv:2506.22058](https://arxiv.org/abs/2506.22058). The first reasoning step has outsized influence on the final answer, so early errors are the most damaging (companion-review entry, repeated here for the mechanism).

**How it relates.** Snowballing is the closest existing mechanism to the cliff and it explains the direction (once wrong, the model justifies rather than revisits), and the "recognize but do not correct" gap in Zhang et al. directly prefigures finding 4 ("seeing isn't doubting"). The tension is quantitative: snowballing describes commitment growing gradually as the model extends its own generation, whereas the cliff shows recovery from an INJECTED trace staying near ceiling until the trace is complete and only then collapsing. So it is not that error accumulates smoothly; a complete wrong unit is treated categorically differently from a 75%-complete one.

## 7. Exposure bias, commitment, and sunk-cost behavior in autoregressive generation

- **Sequence Level Training with Recurrent Neural Networks.** Ranzato, Chopra, Auli, Zaremba (2015). [arXiv:1511.06732](https://arxiv.org/abs/1511.06732). Names "exposure bias": trained on gold prefixes, a model must decode from its own tokens at test time, so errors compound because it never learned to condition on its own mistakes.
- **Scheduled Sampling for Sequence Prediction with Recurrent Neural Networks.** Bengio, Vinyals, Jaitly, Shazeer (2015). [arXiv:1506.03099](https://arxiv.org/abs/1506.03099). Proposes mixing in model-generated tokens during training so the model learns to recover from its own earlier errors.
- **Getting out of the Big-Muddy: Escalation of Commitment in LLMs.** Barkett, Long, Kroger (2025). [arXiv:2508.01545](https://arxiv.org/abs/2508.01545). LLMs show little sunk-cost bias in isolated decisions but escalate strongly under multi-agent or organizational pressure, so commitment is context-driven rather than intrinsic.

**How it relates.** Exposure bias is the classical statement of the pilot's core intuition: a model conditioned on tokens outside its own training distribution (here, a foreign or corrupted trace) may have no learned move for recovering. The completeness cliff is a modern, RL-era measurement of exactly this recovery ability, and the trained-disposition result (finding 2) is the constructive answer scheduled sampling anticipated: the ability to condition on and escape a wrong prefix is installed by training, not by architecture. The sunk-cost paper is a looser analogy (commitment as a behavioral bias) and is cited as such, not as evidence about token-level generation.

## 8. RL for reasoning and emergent re-examination (the "aha moment")

- **DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning.** DeepSeek-AI (2025). [arXiv:2501.12948](https://arxiv.org/abs/2501.12948). Pure RL on verifiable rewards elicits self-reflection, verification, and backtracking, including an emergent "aha moment" where the model spontaneously re-examines and revises its own approach.

**How it relates.** This is the direct grounding for finding 2. R1 shows that re-examination is something reasoning-RL installs rather than something that comes for free with a thinking format. The pilot supplies the controlled contrast R1 does not: a hybrid model (Gemma-4-E2B) that emits thought tokens but gains almost nothing from an open thinking channel, isolating that it is the RL-trained disposition to doubt, not the presence of a `<think>` region, that produces recovery. This turns R1's qualitative observation into a testable dissociation.

## 9. Feedback incorporation limits (project group's own work)

- **Feedback Friction: LLMs Struggle to Fully Incorporate External Feedback.** Jiang, Zhang, Wang, Andrews, Khashabi (JHU, 2025). [arXiv:2506.11930](https://arxiv.org/abs/2506.11930). Even given near-ideal feedback derived from ground truth, solver models resist fully incorporating it; resistance is predicted by the model's confidence (semantic entropy), and temperature ramps and answer-rejection strategies only partly help.

**How it relates.** Feedback Friction shows models under-update when told they are wrong. The completeness cliff is the mirror image on the input side: models over-update when SHOWN a complete wrong derivation, adopting it even though nobody vouched for it. Read together they bracket a single asymmetry, resistance to corrective signal and susceptibility to a coherent wrong scaffold, and the pilot's pass@k framing plus the confidence angle connects naturally to Feedback Friction's semantic-entropy predictor (a natural follow-up: does pre-injection confidence predict where the cliff falls?).

---

## What's novel here

The papers above establish the ingredients, but none assembles them into the completeness cliff. Four things are new. First, **pass@k as the recovery metric applied to trace injection**: prior work measures single-sample accuracy, answer-flip rates, or multiple-choice next-token mass, all of which conflate "usually follows the wrong trace" with "cannot escape it"; pass@16 separates elicitation from capability and reveals that capability is intact through 75% of the trace. Second, **completion, not correctness, as the trigger**: varying how much of a coherent wrong chain the model has seen shows a near-flat-then-cliff shape rather than the smooth degradation the distraction and snowballing literatures imply, which reframes the failure as gating on structural completeness. Third, **scaffold-versus-conclusion decomposition**: the same wrong answer persuades roughly 25x more as steps than as an assertion, and corrupted numbers inside a correct scaffold are silently repaired, isolating that recovery is gated on mismatch detection rather than correctness checking (a mechanism the sycophancy and faithfulness papers do not separate). Fourth, **a clean architecture-versus-training dissociation**: matched instruct and reasoning siblings both show the cliff, while a thought-emitting hybrid gains nothing from its thinking channel, pinning the recovery disposition on reasoning-RL rather than on having a thinking mode, which turns DeepSeek-R1's qualitative "aha moment" into a controlled result. The "seeing isn't doubting" observation (a complete own-wrong trace produces "wait" tokens but no fresh derivation) further shows the Self-Correction Bench "Wait" remedy does not survive past the cliff.

---

## Key references (BibTeX-ready list)

```bibtex
@article{huang2023selfcorrect,
  title={Large Language Models Cannot Self-Correct Reasoning Yet},
  author={Huang, Jie and Chen, Xinyun and Mishra, Swaroop and Zheng, Huaixiu Steven and Yu, Adams Wei and Song, Xinying and Zhou, Denny},
  journal={arXiv preprint arXiv:2310.01798},
  year={2023}
}

@article{tsui2025selfcorrectionbench,
  title={Self-Correction Bench: Revealing and Addressing the Self-Correction Blind Spot in LLMs},
  author={Tsui, Ken},
  journal={arXiv preprint arXiv:2507.02778},
  year={2025}
}

@article{lanham2023faithfulness,
  title={Measuring Faithfulness in Chain-of-Thought Reasoning},
  author={Lanham, Tamera and Chen, Anna and Radhakrishnan, Ansh and Steiner, Benoit and Denison, Carson and others},
  journal={arXiv preprint arXiv:2307.13702},
  year={2023}
}

@article{turpin2023saywhatthink,
  title={Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting},
  author={Turpin, Miles and Michael, Julian and Perez, Ethan and Bowman, Samuel R.},
  journal={arXiv preprint arXiv:2305.04388},
  year={2023}
}

@article{chen2025reasoningsaythink,
  title={Reasoning Models Don't Always Say What They Think},
  author={Chen, Yanda and Benton, Joe and Radhakrishnan, Ansh and others},
  journal={arXiv preprint arXiv:2505.05410},
  year={2025}
}

@article{korbak2025cotmonitorability,
  title={Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety},
  author={Korbak, Tomek and Balesni, Mikita and others},
  journal={arXiv preprint arXiv:2507.11473},
  year={2025}
}

@article{baker2025monitoring,
  title={Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation},
  author={Baker, Bowen and Huizinga, Joost and Gao, Leo and others},
  journal={arXiv preprint arXiv:2503.11926},
  year={2025}
}

@article{sharma2023sycophancy,
  title={Towards Understanding Sycophancy in Language Models},
  author={Sharma, Mrinank and Tong, Meg and Korbak, Tomasz and Duvenaud, David and Askell, Amanda and others},
  journal={arXiv preprint arXiv:2310.13548},
  year={2023}
}

@article{perez2022modelwritten,
  title={Discovering Language Model Behaviors with Model-Written Evaluations},
  author={Perez, Ethan and Ringer, Sam and Lukosiute, Kamile and others},
  journal={arXiv preprint arXiv:2212.09251},
  year={2022}
}

@article{andriushchenko2024jailbreaking,
  title={Jailbreaking Leading Safety-Aligned LLMs with Simple Adaptive Attacks},
  author={Andriushchenko, Maksym and Croce, Francesco and Flammarion, Nicolas},
  journal={arXiv preprint arXiv:2404.02151},
  year={2024}
}

@article{shi2023distracted,
  title={Large Language Models Can Be Easily Distracted by Irrelevant Context},
  author={Shi, Freda and Chen, Xinyun and Misra, Kanishka and Scales, Nathan and Dohan, David and Chi, Ed H. and Sch\"arli, Nathanael and Zhou, Denny},
  journal={arXiv preprint arXiv:2302.00093},
  year={2023}
}

@article{mirzadeh2024gsmsymbolic,
  title={GSM-Symbolic: Understanding the Limitations of Mathematical Reasoning in Large Language Models},
  author={Mirzadeh, Iman and Alizadeh, Keivan and Shahrokhi, Hooman and Tuzel, Oncel and Bengio, Samy and Farajtabar, Mehrdad},
  journal={arXiv preprint arXiv:2410.05229},
  year={2024}
}

@article{zhang2023snowball,
  title={How Language Model Hallucinations Can Snowball},
  author={Zhang, Muru and Press, Ofir and Merrill, William and Liu, Alisa and Smith, Noah A.},
  journal={arXiv preprint arXiv:2305.13534},
  year={2023}
}

@article{liao2025lostbeginning,
  title={Lost at the Beginning of Reasoning},
  author={Liao, Baohao and Chen, Xinyi and Rajaee, Sara and others and Monz, Christof},
  journal={arXiv preprint arXiv:2506.22058},
  year={2025}
}

@inproceedings{ranzato2016sequence,
  title={Sequence Level Training with Recurrent Neural Networks},
  author={Ranzato, Marc'Aurelio and Chopra, Sumit and Auli, Michael and Zaremba, Wojciech},
  booktitle={International Conference on Learning Representations (ICLR)},
  note={arXiv:1511.06732},
  year={2016}
}

@inproceedings{bengio2015scheduled,
  title={Scheduled Sampling for Sequence Prediction with Recurrent Neural Networks},
  author={Bengio, Samy and Vinyals, Oriol and Jaitly, Navdeep and Shazeer, Noam},
  booktitle={Advances in Neural Information Processing Systems (NeurIPS)},
  note={arXiv:1506.03099},
  year={2015}
}

@article{barkett2025escalation,
  title={Getting out of the Big-Muddy: Escalation of Commitment in LLMs},
  author={Barkett, Emilio and Long, Olivia and Kr\"oger, Paul},
  journal={arXiv preprint arXiv:2508.01545},
  year={2025}
}

@article{deepseek2025r1,
  title={DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning},
  author={{DeepSeek-AI}},
  journal={arXiv preprint arXiv:2501.12948},
  year={2025}
}

@article{jiang2025feedbackfriction,
  title={Feedback Friction: LLMs Struggle to Fully Incorporate External Feedback},
  author={Jiang, Dongwei and Zhang, Alvin and Wang, Andrew and Andrews, Nicholas and Khashabi, Daniel},
  journal={arXiv preprint arXiv:2506.11930},
  year={2025}
}
```

Note on scope: the wrong/perturbed-CoT-injection papers most methodologically adjacent to this pilot (Yang et al. 2506.10979, Ballon et al. 2601.23163, von Recum et al. 2602.07470, SEED 2412.11934, Thought Anchors 2506.19143, Fractured CoT 2505.12992, plus training-time analogues such as Spurious Rewards 2506.10947) are documented in the companion file `2026-07-16_wrong_cot_injection_review.md` and are not duplicated here.
