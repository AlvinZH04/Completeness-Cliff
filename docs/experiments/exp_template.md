# EXP-NNN: <short title>

- **Date:** YYYY-MM-DD
- **Author:** (person or Claude session)
- **Status:** planned | running | done | abandoned
- **Results dir:** `results/<run_name>/`
- **Log:** `logs/<run_name>.log`

## Goal

Which RQ from `docs/research_plan.md` does this address? What will we learn?

## Setup

| Field | Value |
|-------|-------|
| Model(s) | |
| Dataset(s) / limit | |
| Conditions | injection_mode × trace_source × fractions |
| N samples / question | |
| max_new_tokens | |
| Sampling params | (reference config key; note any deviation from model card) |
| Seed | |
| Command | `python -m src.experiments.... ` |

## Results

| Condition | pass@1 | pass@8 | adoption | no-answer | truncation |
|-----------|--------|--------|----------|-----------|------------|

## Sanity checks

- [ ] Truncation rate < 2% per cell (if not: note & action)
- [ ] Inspected ≥ 5 raw samples per condition (formatting sane, injection rendered correctly)
- [ ] Baseline pass@1 in expected range for this model/dataset

## Takeaways

- What did we learn? Surprises? Follow-ups?
