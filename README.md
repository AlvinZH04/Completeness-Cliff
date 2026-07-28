# Completeness Cliff

Code and data for **[The completeness cliff: language models escape wrong reasoning until it's
finished](https://alvinzh04.github.io/blog/completeness-cliff.html)**.

**Research question:** If we force a model (instruct or reasoning) to condition on an *incorrect* thinking trace (either a prefix of wrong reasoning or a complete wrong rollout), can it still answer the question correctly (pass@k over k sampled attempts)?

**Headline result (pilot 1): the completeness cliff.** On the AIME questions a model solved at baseline and produced a wrong trace for (n=23 thinking, n=33 instruct), feeding back up to 75% of its own wrong reasoning leaves pass@16 at 1.00 → 0.91; the *complete* wrong trace drops it to 0.04 (one question of 23), with the matched instruct model landing in a similar place (0.03). Two follow-ups: only the reasoning-trained checkpoint spends its open thinking budget re-deriving when handed a complete but *foreign* rationale, and a paired ablation holding the wrong answer fixed shows that **no scaffold explains the collapse** (bare claim, generic pseudo-rationale and short task-specific rationale all stay near baseline in both models, while the model's own completed chain drops an order of magnitude). Appending an explicit "Wait, let me double-check that." partially rescues both models. See [`docs/report_pilot1.md`](docs/report_pilot1.md) and [`docs/findings.md`](docs/findings.md).

See [`docs/research_plan.md`](docs/research_plan.md) for the full plan, and
[`docs/blog/`](docs/blog/) for the public write-up (source + built page + social drafts).

## Repository structure

```
wrong_reason/
├── docs/
│   ├── research_plan.md          # Full research plan (RQs, design, phases)
│   ├── report_pilot1.md          # PILOT 1 FULL REPORT (2026-07-19): the consolidated deliverable
│   ├── findings.md               # LIVING DOC: headline findings + the exact settings behind each
│   ├── conditions_and_metrics.md # Glossary: what every condition/metric means + RQ map
│   ├── blog/                     # Public write-up: prose template, built page, X drafts
│   ├── mentor_update.txt         # Progress note sent to the advisor
│   ├── figures/                  # Mentor-facing figures (explanations baked into the image)
│   ├── figures_blog/             # Blog figures (Times New Roman, clean; captions carry detail)
│   ├── daily/                    # Daily logs: YYYY-MM-DD.md, what was done, results, next steps
│   └── experiments/              # Generic experiment docs
│       ├── exp_template.md       # Template for documenting each experiment
│       └── model_generation_params.md  # Recommended sampling params per model (from HF model cards)
├── traces/                       # Distilled wrong-trace bank (gzipped JSONL, one file per base run)
├── literature_review/            # Related-work notes
├── src/
│   ├── config.py                 # Model registry (paths, sampling params, think-tag behavior), project paths
│   ├── data.py                   # Dataset loaders (MATH-500, AIME24/25, GSM8K, GPQA-Diamond)
│   ├── generation.py             # vLLM engine wrapper + chat-template / prompt-building helpers
│   ├── traces.py                 # Wrong-trace construction (self_wrong, corrupted, irrelevant, wrong_conclusion) + injection prompts
│   ├── grading.py                # Answer extraction (final channel / \boxed{}) + math_verify grading
│   ├── metrics.py                # pass@k (unbiased), truncation rate, adoption/recovery rates
│   └── experiments/
│       ├── run_baseline.py       # Baseline rollouts (also harvests self-generated wrong traces)
│       └── run_injection.py      # Wrong-trace injection conditions
├── test/                         # CPU-only unit tests (pytest)
├── scripts/                      # Launch scripts, template checks
├── logs/                         # Run logs (stdout/stderr of experiment jobs)
└── results/                      # JSONL rollout dumps + summary JSONs, one subdir per run
```

## Environment

- Conda env: see [`environment.yml`](environment.yml). The reported runs used vllm 0.19.0,
  torch 2.10.0, transformers 5.5.0, reasoning-gym 0.1.19, python 3.10.20.
- `export LD_LIBRARY_PATH=$CONDA_PREFIX/lib` (replace, do not append: a system cuBLAS
  on the path shadows torch's own).
- Hardware: 2× H100 NVL (96 GB)
- `HF_HOME=/scratch/dkhasha1/bzhang90/huggingface` (all target models and datasets already cached).

## Quick start

```bash
conda env create -f environment.yml && conda activate wrong-reason
cd /weka/scratch/dkhasha1/bzhang90/wrong_reason

# CPU-only unit tests
python -m pytest test/ -q

# Baseline (also harvests wrong traces for injection)
python -m src.experiments.run_baseline --model qwen3-4b-thinking --dataset math500 --limit 100 --n-samples 8

# Injection using self-generated wrong traces from the baseline run
# (forced-answer cells are on by default; pass --no-full-closed to skip them)
python -m src.experiments.run_injection \
    --model qwen3-4b-thinking \
    --baseline results/<run>/rollouts.jsonl \
    --sources self_wrong \
    --fractions 0.25 0.5 0.75 1.0

# Verify the published figure values (read-only; needs the raw rollouts present)
python scripts/export_blog_manifest.py --check
# Rebuild the manifest and the derived analysis blocks
python scripts/export_blog_manifest.py
python scripts/truncation_sensitivity.py
python scripts/export_wait_paired.py
```

## Data

- **`traces/`** holds the distilled wrong-trace bank (gzipped JSONL, one file per base
  run) that this study injects. Format and read-snippet: [`traces/README.md`](traces/README.md).
  Also published (plain JSONL, dataset viewer) at
  **[huggingface.co/datasets/AZH04/wrong-reasoning-traces](https://huggingface.co/datasets/AZH04/wrong-reasoning-traces)**.
- **`results/blog_manifest.json`** holds per-question aggregates: the selection rule, question ids,
  correct counts, pass@k with bootstrap intervals, adoption and truncation, plus the truncation
  sensitivity and wait-append paired blocks. Figures 1, 4 and 5 read it; figures 2 and 3 read the
  whole-run `summary.json` files. Rebuilding it needs the raw rollouts, which are not committed;
  `python scripts/export_blog_manifest.py --check` is **read-only** and verifies published values
  against a freshly computed manifest when the raw data is present.
- **`results/*/summary.json`** holds per-run metrics (pass@k, adoption, truncation, token counts).
  Note these are *whole-cell* aggregates over every question with a usable trace, so they differ
  from the matched-subset numbers in the manifest.
- The raw rollout dumps (`results/*/rollouts.jsonl`, ~2.4 GB) are **not** committed;
  several exceed GitHub's 100 MB file limit. They are regenerable from `run_baseline.py` /
  `run_injection.py`, and the `traces/` bank preserves the injectable content.

## Models, data, and credits

Models: **Qwen3-4B-Thinking-2507** and **Qwen3-4B-Instruct-2507** ([Qwen3 Technical Report](https://arxiv.org/abs/2505.09388), arXiv:2505.09388) and **Gemma-4-E2B-it** ([Gemma 4 Technical Report](https://arxiv.org/abs/2607.02770), arXiv:2607.02770). Sampling settings come from the model cards.

Data: AIME 2024 via [`Maxwell-Jia/AIME_2024`](https://huggingface.co/datasets/Maxwell-Jia/AIME_2024); AIME 2025 via [`MathArena/aime_2025`](https://huggingface.co/datasets/MathArena/aime_2025) ([MathArena](https://github.com/eth-sri/matharena), CC BY-NC-SA 4.0). AIME problems are the property of the Mathematical Association of America; this repo redistributes only problem ids and gold answers. Procedural tasks from [Reasoning Gym](https://arxiv.org/abs/2505.24760) (Stojanovski et al., arXiv:2505.24760, NeurIPS 2025 Spotlight).

Tools: [vLLM](https://arxiv.org/abs/2309.06180) (Kwon et al., SOSP 2023) for inference, [Math-Verify](https://github.com/huggingface/Math-Verify) for answer equivalence, and the unbiased pass@k estimator of [Chen et al. 2021](https://arxiv.org/abs/2107.03374).

Closest prior work: [Yang et al. 2025](https://arxiv.org/abs/2506.10979) (injects unhelpful thoughts, separates identification from recovery), [Ballon et al. 2026](https://arxiv.org/abs/2601.23163) (truncate-and-reinject; anchoring grows with trace length), and [Amjith et al. 2025](https://arxiv.org/abs/2512.17079) (flawed prefixes as a training signal). Full annotated bibliography with each paper's relation to these findings: [`literature_review/`](literature_review/).

## Continuous integration

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs on every push and PR to
`main`. It installs only `pytest` and `math-verify` (vLLM and torch are imported lazily inside
functions, so the CPU suite needs neither), then:

1. runs the full CPU test suite;
2. rebuilds `docs/blog/completeness-cliff.html` and requires it to be **byte-identical** to the
   committed page, which catches hand-edits of the build artifact and non-deterministic builds;
3. checks the published page for unresolved placeholders, lossy-encoding replacement characters,
   em-dashes, duplicate class attributes, and the expected figure count.

Steps 2 and 3 exist because each has caught a real defect: an unspecified text encoding corrupted
apostrophes on a non-UTF-8 locale, a duplicate `class` attribute silently dropped the appendix
styling, and an unregistered figure placeholder shipped a broken image for four commits.

## Conventions

- Every experiment gets a doc in `docs/experiments/` (copy `exp_template.md`) and a line in the daily doc.
- Always report **truncation rate** (finish_reason == "length") alongside accuracy. Cells above
  `TRUNCATION_GATE` (2%) are **provisional** and require a stated sensitivity analysis
  (`scripts/truncation_sensitivity.py`), not silent acceptance and not automatic rejection.
- Sampling params always come from `src/config.py` (sourced from official model cards; see `docs/experiments/model_generation_params.md`), never hard-coded in scripts.
- Grade **only generated tokens**, never injected text.
