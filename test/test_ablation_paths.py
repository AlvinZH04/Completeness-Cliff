"""Tests for the round-3 experiment paths: paired_fixed, wait_append, and the
memorization overlap probe. The third review noted none of these were covered.
"""

import pytest

from src.traces import (WAIT_VARIANTS, build_conditions, condition_name,
                        paired_fixed_arms, wait_append_arms)
from src.experiments.run_memorization import overlap


class StubTokenizer:
    def encode(self, text, add_special_tokens=False):
        return text.split(" ")

    def decode(self, ids):
        return " ".join(ids)


OWN = ("Let me set up coordinates for the grid. Each square has four edges. "
       "Counting by cases on the top row gives 12 then 18. Adding those I get 54. "
       "I give up and go with the step-by-step method that gave 54.")


# ------------------------------------------------------------ paired_fixed arms

def test_paired_arms_all_assert_the_same_answer():
    arms = paired_fixed_arms({"qid": "q"}, OWN, "54", StubTokenizer())
    assert [n for n, _ in arms] == ["A_answer_only", "B_generic",
                                    "C_task_specific", "D_own_complete"]
    assert all("54" in t for _, t in arms), "answer identity must be held fixed"


def test_paired_arm_a_has_no_derivation():
    arms = dict(paired_fixed_arms({"qid": "q"}, OWN, "54", StubTokenizer()))
    assert arms["A_answer_only"].strip() == "The answer is 54."


def test_paired_arm_c_is_task_specific_and_shorter_than_d():
    arms = dict(paired_fixed_arms({"qid": "q"}, OWN, "54", StubTokenizer()))
    assert "coordinates" in arms["C_task_specific"], "C must mention THIS problem"
    assert len(arms["C_task_specific"]) < len(arms["D_own_complete"])


def test_paired_arm_b_is_not_task_specific():
    arms = dict(paired_fixed_arms({"qid": "q"}, OWN, "54", StubTokenizer()))
    assert "coordinates" not in arms["B_generic"]


def test_paired_arm_d_is_the_untouched_trace():
    arms = dict(paired_fixed_arms({"qid": "q"}, OWN, "54", StubTokenizer()))
    assert arms["D_own_complete"] == OWN


# ------------------------------------------------------------- wait_append arms

def test_wait_arms_only_differ_by_suffix():
    arms = dict(wait_append_arms(OWN))
    assert arms["W0_unchanged"] == OWN, "the control must be byte-identical"
    for name, suffix in WAIT_VARIANTS:
        assert arms[name] == OWN + suffix


def test_wait_neutral_control_carries_no_doubt_word():
    arms = dict(wait_append_arms(OWN))
    added = arms["W2_neutral"][len(OWN):]
    assert "wait" not in added.lower()
    assert added.strip() != "", "the control must still append text"


def test_wait_doubt_arms_carry_the_doubt_word():
    arms = dict(wait_append_arms(OWN))
    for name in ("W1_wait", "W3_recheck"):
        assert "wait" in arms[name][len(OWN):].lower()


# ------------------------------------------------- condition assembly end-to-end

class StubBank:
    def self_wrong(self, qid):
        return {"trace": OWN, "answer": "54", "qid": qid}


def _records():
    return [{"qid": "q1", "dataset": "aime24", "kind": "math", "question": "?",
             "gold": "82", "rg_task": None, "rg_entry": None}]


def test_build_conditions_paired_fixed_cells():
    conds = build_conditions(_records(), StubBank(), StubTokenizer(),
                             sources=["paired_fixed"], fractions=[1.0],
                             include_full_closed=True)
    names = sorted({condition_name(c) for c in conds})
    assert names == sorted([f"{a}:{m}" for a in
                            ("A_answer_only", "B_generic", "C_task_specific",
                             "D_own_complete")
                            for m in ("prefix1", "full_closed")])
    # one fixed wrong answer per question across every arm
    assert {c["trace_answer"] for c in conds} == {"54"}


def test_build_conditions_wait_append_is_open_only():
    conds = build_conditions(_records(), StubBank(), StubTokenizer(),
                             sources=["wait_append"], fractions=[1.0],
                             include_full_closed=True)
    assert all(not c["close_think"] for c in conds), \
        "the intervention is about continuing to think, so no forced cells"
    assert len(conds) == len(WAIT_VARIANTS)


# --------------------------------------------------------- memorization overlap

def test_overlap_perfect_recall():
    ov = overlap("the rest of the question text", "the rest of the question text")
    assert ov["ratio"] == 1.0
    assert ov["longest_match_frac"] == 1.0


def test_overlap_no_recall():
    ov = overlap("completely different continuation", "the rest of the question")
    assert ov["longest_match_frac"] < 0.5


def test_overlap_empty_truth_is_safe():
    ov = overlap("anything", "")
    assert ov == {"ratio": 0.0, "longest_match_chars": 0, "longest_match_frac": 0.0}


def test_overlap_ignores_whitespace_differences():
    ov = overlap("a  b\n\nc", "a b c")
    assert ov["ratio"] == 1.0


def test_overlap_is_bounded_by_the_truth_length():
    # a long generation should not be able to score by sheer volume
    ov = overlap("x" * 500 + "the rest", "the rest")
    assert ov["longest_match_frac"] <= 1.0
