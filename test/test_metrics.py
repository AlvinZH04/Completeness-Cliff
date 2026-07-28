import math

import pytest

from src.metrics import aggregate, pass_at_k


def test_pass_at_k_edges():
    assert pass_at_k(16, 0, 1) == 0.0
    assert pass_at_k(16, 16, 1) == 1.0
    assert pass_at_k(16, 1, 16) == 1.0  # any correct sample -> pass@n == 1
    assert pass_at_k(4, 4, 4) == 1.0


def test_pass_at_k_known_value():
    # n=2, c=1, k=1 -> 0.5
    assert math.isclose(pass_at_k(2, 1, 1), 0.5)
    # n=4, c=2, k=2 -> 1 - C(2,2)/C(4,2) = 1 - 1/6
    assert math.isclose(pass_at_k(4, 2, 2), 1 - 1 / 6)


def test_pass_at_k_rejects_k_gt_n():
    with pytest.raises(ValueError):
        pass_at_k(4, 1, 8)


def test_aggregate():
    qs = [
        {"n": 4, "correct": 2, "adopted": 1, "no_answer": 0, "truncated": 1,
         "gen_tokens": [10, 20, 30, 40]},
        {"n": 4, "correct": 0, "adopted": 4, "no_answer": 2, "truncated": 0,
         "gen_tokens": [5, 5, 5, 5]},
    ]
    m = aggregate(qs, ks=(1, 2, 4))
    assert m["n_questions"] == 2
    assert math.isclose(m["accuracy"], 2 / 8)
    assert math.isclose(m["adoption_rate"], 5 / 8)
    assert math.isclose(m["no_answer_rate"], 2 / 8)
    assert math.isclose(m["truncation_rate"], 1 / 8)
    assert math.isclose(m["pass@1"], (0.5 + 0.0) / 2)
    assert "pass@8" not in m  # k capped by smallest n
