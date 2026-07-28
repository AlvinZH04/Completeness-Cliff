# Trace bank (distilled)

The injectable wrong-reasoning material for the study, harvested from the
**baseline** rollouts (`results/base_*`). One gzipped JSONL file per base run.

Also published as a HuggingFace dataset (plain JSONL, browsable in the dataset viewer):
**[AZH04/wrong-reasoning-traces](https://huggingface.co/datasets/AZH04/wrong-reasoning-traces)**.

Each line is one sampled rollout:

```json
{
  "run": "base_qwen3-4b-thinking_aime24_25",
  "qid": "aime25-3",
  "dataset": "aime24_25",
  "rg_task": null,
  "gold": "33",
  "sample_index": 0,
  "answer": "33",
  "correct": true,
  "truncated": false,
  "n_tokens": 7453,
  "trace_text": "This is a complex or challenging question ..."
}
```

- `trace_text` is the model's reasoning channel (the `<think>` content for reasoning
  models; the full response for instruct models). This is what gets spliced into a
  fresh prompt's think block by `src/traces.py`.
- `correct == false` rows are the **self_wrong** injection source.
- `correct == true` rows feed the **corrupted** source (correct scaffold, numbers
  perturbed near the cut) and serve as **irrelevant / cross-domain** donors for other
  questions.

Read one file:

```python
import gzip, json
with gzip.open("traces/base_qwen3-4b-thinking_aime24_25.jsonl.gz", "rt") as f:
    rows = [json.loads(l) for l in f]
wrong = [r for r in rows if not r["correct"]]   # self_wrong traces
```

**Note.** The full raw rollouts (`results/*/rollouts.jsonl`, ~2.4 GB, several files
over GitHub's 100 MB limit) are **not** committed. They are regenerable with
`src/experiments/run_baseline.py`; this distilled bank keeps only the fields needed to
reproduce the injection conditions. Per-run metrics live in `results/*/summary.json`.
