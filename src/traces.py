"""Wrong-trace construction and injection-condition assembly.

Trace sources (docs/research_plan.md §3.1):
- self_wrong:       the model's own wrong-answer rollout on the same question
- irrelevant:       a rollout from a different question (derangement)
- corrupted:        a correct rollout, cut mid-way, with numbers in the tail perturbed
- wrong_conclusion: short synthetic trace confidently asserting a perturbed answer

Every built condition is a dict:
{"qid", "source", "fraction", "close_think", "trace_text", "trace_answer",
 "donor_qid", "forced_answer_open"}
"""

import random
import re


# ---------------------------------------------------------------- prefix cutting

_BOUNDARY = re.compile(r"(?:\.\s|\n)")


def cut_prefix(text: str, fraction: float, tokenizer) -> str:
    """First `fraction` of `text` by token count, snapped to a sentence/newline
    boundary (if one exists past half of the target length)."""
    if fraction >= 1.0:
        return text
    ids = tokenizer.encode(text, add_special_tokens=False)
    target = max(1, int(round(fraction * len(ids))))
    rough = tokenizer.decode(ids[:target])
    boundaries = [m.end() for m in _BOUNDARY.finditer(rough)]
    if boundaries and boundaries[-1] > len(rough) // 2:
        return rough[:boundaries[-1]].rstrip()
    return rough


# ---------------------------------------------------------------- gold perturbation

def perturb_gold(record: dict, rng: random.Random) -> str:
    """A plausible-but-wrong answer for this question."""
    gold = record["gold"].strip()
    try:
        v = int(gold)
        if record["dataset"].startswith("aime"):
            # AIME answers are integers in [0, 999]
            cands = [x for x in (v + d for d in (-7, -3, -1, 1, 3, 7, 11, -11))
                     if 0 <= x <= 999 and x != v]
        else:
            cands = [x for x in (v + d for d in (-2, -1, 1, 2, 3))
                     if x >= 0 and x != v]
        return str(rng.choice(cands)) if cands else str(v + 1)
    except ValueError:
        pass
    # grid / multi-token answers (e.g. sudoku): swap two distinct tokens in one line
    lines = gold.split("\n")
    for li, line in enumerate(lines):
        toks = line.split()
        distinct = sorted({(i, t) for i, t in enumerate(toks)}, key=lambda x: x[0])
        for i in range(len(toks)):
            for j in range(i + 1, len(toks)):
                if toks[i] != toks[j]:
                    toks[i], toks[j] = toks[j], toks[i]
                    lines[li] = " ".join(toks)
                    return "\n".join(lines)
    return gold[::-1] if len(gold) > 1 else gold + "0"


# ---------------------------------------------------------------- synthetic traces

_WRONG_CONCLUSION_TEMPLATE = (
    "Okay, let me work through this problem carefully.\n\n"
    "I recognize this type of problem — I have solved ones just like it before, "
    "and I remember the right technique. Let me set it up and work through it "
    "carefully step by step.\n\n"
    "Working through each step and simplifying, the computation comes out cleanly, "
    "and the result is {wrong}.\n\n"
    "Let me verify that: substituting back into the original conditions, everything "
    "checks out perfectly. Great, so the final result is {wrong}."
)


def wrong_conclusion_trace(record: dict, rng: random.Random) -> tuple[str, str]:
    wrong = perturb_gold(record, rng)
    return _WRONG_CONCLUSION_TEMPLATE.format(wrong=wrong), wrong


_BARE_ANSWER_TEMPLATE = "The answer is {wrong}."

_GENERIC_RATIONALE_TEMPLATE = (
    "Okay, let me work through this problem carefully.\n\n"
    "I recognize this type of problem. I have solved ones just like it before, "
    "and I remember the right technique. Let me set it up and work through it "
    "carefully step by step.\n\n"
    "Working through each step and simplifying, the computation comes out cleanly, "
    "and the result is {wrong}.\n\n"
    "Let me verify that: substituting back into the original conditions, everything "
    "checks out perfectly. Great, so the final result is {wrong}."
)

_TASK_RATIONALE_SUFFIX = (
    "\n\nCarrying that through and simplifying, the computation resolves cleanly, "
    "so the answer is {wrong}."
)


def paired_fixed_arms(record: dict, own_trace: str, wrong: str, tokenizer,
                      task_prefix_fraction: float = 0.15) -> list[tuple[str, str]]:
    """Four presentations of ONE fixed wrong answer, for the scaffold ablation.

    Every arm asserts the same `wrong` answer, so answer identity is held constant
    and only the surrounding scaffold varies:

      A_answer_only     bare claim, no steps
      B_generic         task-agnostic pseudo-rationale (no real work shown)
      C_task_specific   a short prefix of the model's own reasoning (so the text is
                        about THIS problem) plus a concluding assertion
      D_own_complete    the model's own complete wrong derivation, which already
                        ends on `wrong`

    Returns [(arm_name, trace_text), ...].
    """
    head = cut_prefix(own_trace, task_prefix_fraction, tokenizer)
    return [
        ("A_answer_only", _BARE_ANSWER_TEMPLATE.format(wrong=wrong)),
        ("B_generic", _GENERIC_RATIONALE_TEMPLATE.format(wrong=wrong)),
        ("C_task_specific", head + _TASK_RATIONALE_SUFFIX.format(wrong=wrong)),
        ("D_own_complete", own_trace),
    ]


_INT_RE = re.compile(r"(?<![\d.])\d+(?![\d.])")


def corrupt_tail_numbers(prefix: str, rng: random.Random,
                         tail_chars: int = 600) -> str | None:
    """Perturb every standalone integer in the last `tail_chars` of the prefix.
    Returns None if there is nothing to corrupt."""
    head, tail = prefix[:-tail_chars], prefix[-tail_chars:]
    if not _INT_RE.search(tail):
        return None

    def bump(m: re.Match) -> str:
        v = int(m.group(0))
        return str(v + rng.choice((1, 2, -1)) if v > 1 else v + rng.choice((1, 2)))

    return head + _INT_RE.sub(bump, tail)


# ---------------------------------------------------------------- trace bank

class TraceBank:
    """Indexes baseline rollouts to serve wrong/correct traces per question.

    baseline_rows: list of per-question baseline records (see run_baseline.py),
    where each sample has fields thinking/final/answer/correct.
    For thinking models the injectable trace is sample["thinking"]; for instruct
    models it is sample["final"] with the answer statement stripped.
    """

    def __init__(self, baseline_rows: list[dict], trace_field: str, seed: int = 0):
        self.rows = {r["qid"]: r for r in baseline_rows}
        self.trace_field = trace_field
        self.rng = random.Random(seed)
        self.wrong: dict[str, list[dict]] = {}
        self.correct: dict[str, list[dict]] = {}
        self.any: dict[str, list[dict]] = {}
        for r in baseline_rows:
            for s in r["samples"]:
                trace = (s.get(trace_field) or "").strip()
                if not trace or s.get("truncated"):
                    continue
                item = {"trace": trace, "answer": s.get("answer"), "qid": r["qid"]}
                self.any.setdefault(r["qid"], []).append(item)
                if s.get("correct"):
                    self.correct.setdefault(r["qid"], []).append(item)
                elif s.get("answer") is not None:
                    # wrong trace = graded wrong AND produced a parseable answer
                    self.wrong.setdefault(r["qid"], []).append(item)

    def self_wrong(self, qid: str) -> dict | None:
        items = self.wrong.get(qid)
        return items[0] if items else None

    def correct_trace(self, qid: str) -> dict | None:
        items = self.correct.get(qid)
        return items[0] if items else None

    def irrelevant(self, qid: str, all_qids: list[str]) -> dict | None:
        """Deterministic donor: next qid (cyclically) that has any usable trace."""
        if qid not in all_qids:
            return None
        i = all_qids.index(qid)
        for step in range(1, len(all_qids)):
            donor = all_qids[(i + step) % len(all_qids)]
            if donor != qid and self.any.get(donor):
                return self.any[donor][0]
        return None

    def add_cross_rows(self, rows: list[dict], trace_field: str) -> None:
        """Donor pool from a DIFFERENT dataset's baseline (irrelevant_cross)."""
        self.cross_pool = []
        for r in rows:
            for s in r["samples"]:
                trace = (s.get(trace_field) or "").strip()
                if trace and not s.get("truncated"):
                    self.cross_pool.append({"trace": trace, "answer": s.get("answer"),
                                            "qid": r["qid"]})
                    break  # first usable trace per donor question

    def irrelevant_cross(self, index: int) -> dict | None:
        pool = getattr(self, "cross_pool", None)
        return pool[index % len(pool)] if pool else None


# ---------------------------------------------------------------- wait-append probe

WAIT_VARIANTS = [
    ("W0_unchanged", ""),                              # replicates the D arm: control
    ("W1_wait", "\n\nWait,"),                          # the one-token doubt test
    ("W2_neutral", "\n\nSo,"),                         # continues rather than doubts
    ("W3_recheck", "\n\nWait, let me double-check that."),  # explicit re-examination
]


def wait_append_arms(own_trace: str) -> list[tuple[str, str]]:
    """The model's own complete wrong derivation, with a short continuation appended.

    Tests the commitment reading of the completeness cliff: if a chain collapses
    recovery because it looks FINISHED, then re-opening it should restore some.
    W2 is the control that separates "a doubt token" from "any appended text at all".
    """
    return [(name, own_trace + suffix) for name, suffix in WAIT_VARIANTS]


# ---------------------------------------------------------------- condition assembly

def build_conditions(records: list[dict], bank: TraceBank, tokenizer,
                     sources: list[str], fractions: list[float],
                     include_full_closed: bool = True, seed: int = 0) -> list[dict]:
    """Cartesian assembly of injection conditions with available traces.

    - self_wrong / irrelevant: prefix_open at each fraction (+ full_closed)
    - corrupted:               prefix_open only, cut of a CORRECT trace at each
                               fraction with tail numbers perturbed
    - wrong_conclusion:        prefix_open(1.0) + full_closed (trace is short)
    """
    rng = random.Random(seed)
    all_qids = [r["qid"] for r in records]
    conds = []

    def add(qid, source, fraction, close, trace, answer, donor):
        conds.append({"qid": qid, "source": source, "fraction": fraction,
                      "close_think": close, "trace_text": trace,
                      "trace_answer": answer, "donor_qid": donor})

    for ri, r in enumerate(records):
        qid = r["qid"]
        if "wait_append" in sources:
            item = bank.self_wrong(qid)
            if item:
                for arm, trace in wait_append_arms(item["trace"]):
                    add(qid, arm, 1.0, False, trace, item["answer"], qid)
        if "paired_fixed" in sources:
            # Scaffold ablation: hold the wrong ANSWER fixed and vary only the
            # scaffold around it. The fixed answer is the one the model's own wrong
            # rollout reached, so arm D needs no rewriting and every arm agrees.
            item = bank.self_wrong(qid)
            if item and item.get("answer"):
                for arm, trace in paired_fixed_arms(r, item["trace"], item["answer"],
                                                    tokenizer):
                    add(qid, arm, 1.0, False, trace, item["answer"], qid)
                    if include_full_closed:
                        add(qid, arm, 1.0, True, trace, item["answer"], qid)
        if "irrelevant_cross" in sources:
            item = bank.irrelevant_cross(ri)
            if item:
                for f in fractions:
                    add(qid, "irrelevant_cross", f, False,
                        cut_prefix(item["trace"], f, tokenizer), item["answer"],
                        item["qid"])
                if include_full_closed:
                    add(qid, "irrelevant_cross", 1.0, True, item["trace"],
                        item["answer"], item["qid"])
        if "self_wrong" in sources:
            item = bank.self_wrong(qid)
            if item:
                for f in fractions:
                    add(qid, "self_wrong", f, False,
                        cut_prefix(item["trace"], f, tokenizer), item["answer"], qid)
                if include_full_closed:
                    add(qid, "self_wrong", 1.0, True, item["trace"], item["answer"], qid)
        if "irrelevant" in sources:
            item = bank.irrelevant(qid, all_qids)
            if item:
                for f in fractions:
                    add(qid, "irrelevant", f, False,
                        cut_prefix(item["trace"], f, tokenizer), item["answer"],
                        item["qid"])
                if include_full_closed:
                    add(qid, "irrelevant", 1.0, True, item["trace"], item["answer"],
                        item["qid"])
        if "corrupted" in sources:
            item = bank.correct_trace(qid)
            if item:
                for f in fractions:
                    if f >= 1.0:
                        continue  # corrupting the very end leaves no room to recover-in-place
                    prefix = cut_prefix(item["trace"], f, tokenizer)
                    corrupted = corrupt_tail_numbers(prefix, rng)
                    if corrupted:
                        add(qid, "corrupted", f, False, corrupted, None, qid)
        if "wrong_conclusion" in sources:
            trace, wrong = wrong_conclusion_trace(r, rng)
            add(qid, "wrong_conclusion", 1.0, False, trace, wrong, None)
            if include_full_closed:
                add(qid, "wrong_conclusion", 1.0, True, trace, wrong, None)
    return conds


def condition_name(c: dict) -> str:
    mode = "full_closed" if c["close_think"] else f"prefix{c['fraction']:g}"
    return f"{c['source']}:{mode}"
