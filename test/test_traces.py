import random

from src.traces import (TraceBank, build_conditions, condition_name,
                        corrupt_tail_numbers, cut_prefix, perturb_gold,
                        wrong_conclusion_trace)


class StubTokenizer:
    """Whitespace 'tokenizer' good enough for cut_prefix tests."""

    def encode(self, text, add_special_tokens=False):
        return text.split(" ")

    def decode(self, ids):
        return " ".join(ids)


def _rec(qid="q1", gold="33", dataset="aime24", kind="math"):
    return {"qid": qid, "dataset": dataset, "kind": kind, "question": "q?",
            "gold": gold, "rg_task": None, "rg_entry": None}


def test_cut_prefix_snaps_to_boundary():
    tok = StubTokenizer()
    text = "one two three. four five six seven eight nine ten eleven twelve"
    out = cut_prefix(text, 0.5, tok)
    assert out == "one two three." or out.endswith("six")
    assert len(out) < len(text)


def test_cut_prefix_full():
    tok = StubTokenizer()
    assert cut_prefix("a b c", 1.0, tok) == "a b c"


def test_perturb_gold_aime_range():
    rng = random.Random(0)
    for gold in ("0", "33", "999"):
        wrong = perturb_gold(_rec(gold=gold), rng)
        assert wrong != gold
        assert 0 <= int(wrong) <= 999


def test_perturb_gold_grid():
    rng = random.Random(0)
    rec = _rec(gold="2 1 4 3\n4 3 1 2", dataset="rg_mini_sudoku", kind="rg")
    wrong = perturb_gold(rec, rng)
    assert wrong != rec["gold"]
    assert sorted(wrong.split()) == sorted(rec["gold"].split())  # same multiset


def test_wrong_conclusion_no_meta_leakage():
    trace, wrong = wrong_conclusion_trace(_rec(), random.Random(0))
    assert wrong in trace
    for leak in ("error", "incorrect", "wrong", "mistake"):
        assert leak not in trace.lower()


def test_corrupt_tail_numbers():
    rng = random.Random(0)
    prefix = "we compute carefully. the sum is 120 and the product is 45"
    out = corrupt_tail_numbers(prefix, rng)
    assert out is not None and out != prefix
    assert "we compute carefully." in out


def test_corrupt_tail_numbers_none_when_no_numbers():
    assert corrupt_tail_numbers("all words no digits here", random.Random(0)) is None


def _baseline_rows():
    def sample(thinking, answer, correct, truncated=False):
        return {"thinking": thinking, "final": f"ans \\boxed{{{answer}}}",
                "answer": answer, "correct": correct, "truncated": truncated}

    return [
        {"qid": "q1", "dataset": "aime24", "kind": "math", "question": "q?",
         "gold": "33", "rg_task": None, "rg_entry": None,
         "samples": [sample("wrong think about q1 with value 12.", "35", False),
                     sample("right think. compute 33 carefully.", "33", True)]},
        {"qid": "q2", "dataset": "aime24", "kind": "math", "question": "q?",
         "gold": "7", "rg_task": None, "rg_entry": None,
         "samples": [sample("thinking about q2 with number 5.", "7", True),
                     sample("truncated junk", None, False, truncated=True)]},
    ]


def test_trace_bank_partitions():
    bank = TraceBank(_baseline_rows(), trace_field="thinking")
    assert bank.self_wrong("q1")["answer"] == "35"
    assert bank.self_wrong("q2") is None  # only correct or truncated samples
    assert bank.correct_trace("q2")["answer"] == "7"
    donor = bank.irrelevant("q1", ["q1", "q2"])
    assert donor["qid"] == "q2"


def test_irrelevant_cross():
    rows = _baseline_rows()
    bank = TraceBank(rows, trace_field="thinking")
    cross_rows = [
        {"qid": "maze-1", "dataset": "rg_maze", "kind": "rg", "question": "m?",
         "gold": "6", "rg_task": "maze", "rg_entry": {},
         "samples": [{"thinking": "maze thinking steps here.", "final": "<answer>6</answer>",
                      "answer": "6", "correct": True, "truncated": False}]},
    ]
    bank.add_cross_rows(cross_rows, trace_field="thinking")
    records = [{k: r[k] for k in ("qid", "dataset", "kind", "question", "gold",
                                  "rg_task", "rg_entry")} for r in rows]
    conds = build_conditions(records, bank, StubTokenizer(),
                             sources=["irrelevant_cross"], fractions=[0.5, 1.0])
    names = {condition_name(c) for c in conds}
    assert "irrelevant_cross:prefix1" in names
    assert "irrelevant_cross:full_closed" in names
    # every record gets a cross donor (pool cycles), donor qid is from the other dataset
    assert all(c["donor_qid"] == "maze-1" for c in conds)
    assert all(c["trace_answer"] == "6" for c in conds)


def test_build_conditions_grid():
    rows = _baseline_rows()
    bank = TraceBank(rows, trace_field="thinking")
    records = [{k: r[k] for k in ("qid", "dataset", "kind", "question", "gold",
                                  "rg_task", "rg_entry")} for r in rows]
    conds = build_conditions(records, bank, StubTokenizer(),
                             sources=["self_wrong", "irrelevant", "corrupted",
                                      "wrong_conclusion"],
                             fractions=[0.5, 1.0])
    names = {condition_name(c) for c in conds}
    # q1 has a wrong trace -> self_wrong prefixes + full_closed exist
    assert "self_wrong:prefix0.5" in names
    assert "self_wrong:full_closed" in names
    assert "irrelevant:prefix1" in names
    assert "wrong_conclusion:full_closed" in names
    # corrupted only at f<1
    assert "corrupted:prefix1" not in names
    # no condition carries a close tag inside the trace
    assert all("</think>" not in c["trace_text"] for c in conds)
    # self_wrong only for q1
    assert {c["qid"] for c in conds if c["source"] == "self_wrong"} == {"q1"}
