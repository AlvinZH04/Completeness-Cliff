"""Answer extraction and grading.

Rules (see docs/research_plan.md §3.5):
- Grade ONLY generated tokens, never injected text.
- Thinking models: the answer lives in the final channel (after </think>).
  If generation was truncated before </think>, there is no answer.
- kind == "math": last \\boxed{...} in the final channel, graded with math_verify.
- kind == "rg":  <answer>...</answer> tags, graded with reasoning_gym score_answer.
"""

import re
from functools import lru_cache

from .config import THINK_CLOSE


def split_channels(generated: str, think_open_in_prompt: bool,
                   think_closed_in_prompt: bool,
                   think_close: str = THINK_CLOSE) -> tuple[str, str | None]:
    """Return (thinking_continuation, final_channel_or_None) for generated text.

    think_open_in_prompt: the prompt left the model inside an open think block
      (thinking baseline or open-prefix injection) -> generated text is thinking
      until the close marker, then final channel.
    think_closed_in_prompt: prompt already closed the think block (full_closed) ->
      the whole generation is the final channel.
    Neither (instruct models): whole generation is the final channel.
    """
    if think_closed_in_prompt or not think_open_in_prompt:
        return "", generated
    if think_close in generated:
        think, final = generated.split(think_close, 1)
        return think, final
    return generated, None  # truncated inside thinking: no answer channel


def extract_boxed(text: str) -> str | None:
    """Content of the last \\boxed{...} with balanced braces."""
    idx = text.rfind("\\boxed{")
    if idx == -1:
        return None
    i = idx + len("\\boxed{")
    depth = 1
    out = []
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
        i += 1
    return "".join(out) if depth == 0 else None


def extract_tagged(text: str, tag: str = "answer") -> str | None:
    """Content of the last <tag>...</tag> block (DOTALL)."""
    matches = re.findall(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    return matches[-1].strip() if matches else None


@lru_cache(maxsize=1)
def _math_verify():
    from math_verify import parse, verify
    return parse, verify


def grade_math(pred: str | None, gold: str) -> bool:
    if pred is None:
        return False
    parse, verify = _math_verify()
    try:
        gold_p = parse(f"\\boxed{{{gold}}}")
        pred_p = parse(f"\\boxed{{{pred}}}")
        return bool(verify(gold_p, pred_p))
    except Exception:
        return False


_RG_SCORERS: dict[str, object] = {}


def _rg_scorer(task: str):
    if task not in _RG_SCORERS:
        import reasoning_gym
        _RG_SCORERS[task] = reasoning_gym.create_dataset(task, size=1, seed=0)
    return _RG_SCORERS[task]


def grade_rg(pred: str | None, record: dict) -> bool:
    if pred is None:
        return False
    scorer = _rg_scorer(record["rg_task"])
    try:
        return float(scorer.score_answer(answer=pred, entry=record["rg_entry"])) >= 1.0
    except Exception:
        return False


def extract_answer(final_channel: str | None, kind: str) -> str | None:
    if final_channel is None:
        return None
    if kind == "math":
        return extract_boxed(final_channel)
    return extract_tagged(final_channel)


def grade(pred: str | None, record: dict) -> bool:
    if record["kind"] == "math":
        return grade_math(pred, record["gold"])
    return grade_rg(pred, record)


def answers_match(a: str | None, b: str | None, kind: str) -> bool:
    """Used for adoption rate: does the produced answer equal the trace's answer?"""
    if a is None or b is None:
        return False
    if kind == "math":
        return grade_math(a, b)
    return " ".join(a.split()) == " ".join(b.split())


CORRECTION_MARKERS = ("wait", "actually", "hmm", "let me re", "re-examine",
                      "recheck", "double-check", "mistake", "that's wrong",
                      "hold on", "on second thought")


def count_correction_markers(thinking_text: str) -> int:
    low = thinking_text.lower()
    return sum(low.count(m) for m in CORRECTION_MARKERS)
