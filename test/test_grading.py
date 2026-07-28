from src.grading import (answers_match, count_correction_markers, extract_boxed,
                         extract_tagged, grade_math, split_channels)


def test_extract_boxed_simple():
    assert extract_boxed("the answer is \\boxed{42}.") == "42"


def test_extract_boxed_nested_and_last():
    text = "first \\boxed{1} then \\boxed{\\frac{1}{2}}"
    assert extract_boxed(text) == "\\frac{1}{2}"


def test_extract_boxed_missing():
    assert extract_boxed("no box here") is None
    assert extract_boxed("unbalanced \\boxed{1 + 2") is None


def test_extract_tagged():
    assert extract_tagged("bla <answer>6</answer>") == "6"
    assert extract_tagged("<answer>1 2\n3 4</answer>") == "1 2\n3 4"
    assert extract_tagged("<answer>a</answer> ... <answer>b</answer>") == "b"
    assert extract_tagged("nothing") is None


def test_grade_math_equivalence():
    assert grade_math("0.5", "\\frac{1}{2}")
    assert grade_math("33", "33")
    assert not grade_math("34", "33")
    assert not grade_math(None, "33")


def test_split_channels_thinking_open():
    think, final = split_channels("reasoning...</think>\n\nAnswer: \\boxed{7}",
                                  think_open_in_prompt=True,
                                  think_closed_in_prompt=False)
    assert "reasoning" in think
    assert "\\boxed{7}" in final


def test_split_channels_truncated_thinking():
    think, final = split_channels("endless reasoning", think_open_in_prompt=True,
                                  think_closed_in_prompt=False)
    assert final is None


def test_split_channels_closed_in_prompt():
    think, final = split_channels("The answer is \\boxed{7}",
                                  think_open_in_prompt=True,
                                  think_closed_in_prompt=True)
    assert think == ""
    assert final == "The answer is \\boxed{7}"


def test_split_channels_custom_marker_gemma():
    text = "reasoning about the sum<channel|>The answer is \\boxed{391}"
    think, final = split_channels(text, think_open_in_prompt=True,
                                  think_closed_in_prompt=False,
                                  think_close="<channel|>")
    assert think == "reasoning about the sum"
    assert "\\boxed{391}" in final


def test_split_channels_instruct():
    _, final = split_channels("plain response", think_open_in_prompt=False,
                              think_closed_in_prompt=False)
    assert final == "plain response"


def test_answers_match():
    assert answers_match("0.5", "1/2", "math")
    assert answers_match("1 2\n3 4", "1  2\n3   4", "rg")
    assert not answers_match(None, "5", "math")


def test_correction_markers():
    assert count_correction_markers("Wait, actually that is wrong. Hmm.") >= 3
