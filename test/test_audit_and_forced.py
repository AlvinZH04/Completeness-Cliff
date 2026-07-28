"""Regression tests for two fragile helpers flagged in review.

1. `extract_forced` used to end a math answer at the first `}`, truncating any
   nested-brace answer such as \\frac{1}{2}.
2. `audit_rows` used to read `args.dump` from a module-level global that only
   exists on the CLI path, so importing and calling it raised NameError.
"""

from src.audit import audit_rows, distinctive_numbers
from src.experiments.run_injection import extract_forced


# ---------------------------------------------------------------- extract_forced

def test_forced_math_plain_integer():
    assert extract_forced("33} and then some prose", "math") == "33"


def test_forced_math_keeps_nested_braces():
    # the prompt already opened \boxed{, so the continuation carries the inside
    assert extract_forced("\\frac{1}{2}} trailing text", "math") == "\\frac{1}{2}"


def test_forced_math_nested_deeper():
    got = extract_forced("\\frac{\\sqrt{3}}{2}} done", "math")
    assert got == "\\frac{\\sqrt{3}}{2}"


def test_forced_math_unclosed_falls_back():
    assert extract_forced("42", "math") == "42"


def test_forced_math_empty_is_none():
    assert extract_forced("", "math") is None


def test_forced_tagged_answer():
    assert extract_forced("up right down</answer> extra", "rg") == "up right down"


# -------------------------------------------------------------------- audit_rows

def _row(condition="self_wrong:prefix1", correct=False, adopted=True):
    return {
        "qid": "q1", "condition": condition, "source": "self_wrong",
        "donor_qid": None, "gold": "33", "trace_answer": "54",
        "trace_text": "some wrong reasoning ending in 54",
        "samples": [{
            "thinking": "wait, let me check 1234 again", "final": "the answer is 54",
            "answer": "54", "correct": correct, "adopted": adopted, "n_tokens": 100,
        }],
    }


def test_audit_rows_callable_without_cli_globals():
    stats, examples = audit_rows([_row()], {"q1": "target question 1234"}, [])
    st = stats["self_wrong:prefix1"]
    assert st["n"] == 1
    assert st["adopted"] == 1
    # dump defaults to 0, so nothing is collected
    assert all(len(v) == 0 for v in examples.values())


def test_audit_rows_dump_is_explicit():
    _, examples = audit_rows([_row()], {"q1": "target question 1234"}, [], dump=2)
    assert len(examples["self_wrong:prefix1"]) == 1
    assert examples["self_wrong:prefix1"][0]["qid"] == "q1"


def test_audit_rows_respects_cell_filter():
    stats, _ = audit_rows([_row()], {"q1": "q"}, ["irrelevant:prefix1"])
    assert dict(stats) == {}


def test_audit_rows_counts_target_engagement():
    # 1234 is distinctive to the target question (absent from the trace)
    stats, _ = audit_rows([_row()], {"q1": "target question 1234"}, [])
    st = stats["self_wrong:prefix1"]
    assert st["has_distinct"] == 1
    assert st["target_engaged"] == 1


def test_distinctive_numbers_excludes_trace_and_donor():
    assert distinctive_numbers("uses 1234 and 55", None, "trace mentions 55") == {"1234"}
