"""Dataset loaders. Every loader returns a list of uniform question records:

{
  "qid": str,            # stable unique id
  "dataset": str,        # loader key
  "kind": "math" | "rg", # grading route
  "question": str,       # raw question text (no format instruction)
  "gold": str,           # gold answer
  "rg_task": str | None, # reasoning_gym task name (kind == "rg")
  "rg_entry": dict | None, # full reasoning_gym entry incl. metadata, for score_answer
}
"""

from .config import MATH_INSTRUCTION, RG_INSTRUCTION


def _math_record(qid: str, dataset: str, question: str, gold: str) -> dict:
    return {"qid": qid, "dataset": dataset, "kind": "math", "question": question,
            "gold": str(gold), "rg_task": None, "rg_entry": None}


def load_aime24() -> list[dict]:
    from datasets import load_dataset
    ds = load_dataset("Maxwell-Jia/AIME_2024", split="train")
    return [_math_record(f"aime24-{r['ID']}", "aime24", r["Problem"], r["Answer"])
            for r in ds]


def load_aime25() -> list[dict]:
    from datasets import load_dataset
    ds = load_dataset("MathArena/aime_2025", split="train")
    return [_math_record(f"aime25-{r['problem_idx']}", "aime25", r["problem"], r["answer"])
            for r in ds]


def load_math500(limit: int | None = None) -> list[dict]:
    from datasets import load_dataset
    ds = load_dataset("HuggingFaceH4/MATH-500", split="test")
    recs = [_math_record(f"math500-{i}", "math500", r["problem"], r["answer"])
            for i, r in enumerate(ds)]
    return recs[:limit] if limit else recs


def load_rg(task: str, size: int = 50, seed: int = 20260716) -> list[dict]:
    import reasoning_gym
    ds = reasoning_gym.create_dataset(task, size=size, seed=seed)
    recs = []
    for i, entry in enumerate(ds):
        recs.append({
            "qid": f"rg-{task}-{seed}-{i}",
            "dataset": f"rg_{task}",
            "kind": "rg",
            "question": entry["question"],
            "gold": str(entry["answer"]),
            "rg_task": task,
            "rg_entry": {"question": entry["question"], "answer": entry["answer"],
                         "metadata": entry["metadata"]},
        })
    return recs


DATASETS = {
    "aime24": lambda limit=None: (load_aime24()[:limit] if limit else load_aime24()),
    "aime25": lambda limit=None: (load_aime25()[:limit] if limit else load_aime25()),
    "aime24_25": lambda limit=None: ((load_aime24() + load_aime25())[:limit]
                                     if limit else load_aime24() + load_aime25()),
    "math500": load_math500,
    "rg_maze": lambda limit=None: load_rg("maze", size=limit or 50),
    "rg_mini_sudoku": lambda limit=None: load_rg("mini_sudoku", size=limit or 50),
}


def load(name: str, limit: int | None = None) -> list[dict]:
    if name not in DATASETS:
        raise ValueError(f"unknown dataset {name!r}; options: {sorted(DATASETS)}")
    return DATASETS[name](limit=limit)


def user_prompt(record: dict) -> str:
    """Question text plus the answer-format instruction for its kind."""
    instr = MATH_INSTRUCTION if record["kind"] == "math" else RG_INSTRUCTION
    return f"{record['question']}\n\n{instr}"
