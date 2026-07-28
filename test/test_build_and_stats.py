"""Regression tests for the fourth review's build and statistics bugs.

Each test here corresponds to a defect that shipped:
  * "effective loss" was the all-no-answer rate, with no truncation predicate, so a
    cell with 0% truncation reported 8.3% "truncated and no answer";
  * the appendix table emitted a duplicate class attribute, so over-gate cells were
    never styled;
  * the HTML build used the platform's default encoding, which corrupted curly
    apostrophes on a cp936 locale.
"""

import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "results", "blog_manifest.json")
BUILT = os.path.join(ROOT, "docs", "blog", "completeness-cliff.html")

pytestmark = pytest.mark.skipif(
    not os.path.exists(MANIFEST), reason="manifest not present in this checkout")


def _manifest():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------- truncation statistic naming

def test_truncation_block_separates_the_three_quantities():
    ts = _manifest().get("truncation_sensitivity")
    assert ts, "manifest must carry a truncation_sensitivity block"
    for run, cells in ts["runs"].items():
        for arm, v in cells.items():
            for field in ("no_answer_rate", "truncated_no_answer_rate",
                          "truncated_with_answer_rate"):
                assert field in v, f"{run}/{arm} missing {field}"
            assert "effective_loss_rate" not in v, \
                f"{run}/{arm} still carries the mislabeled effective_loss_rate"


def test_truncated_no_answer_never_exceeds_truncation():
    """The bug: a 0%-truncation cell reported 8.3% 'truncated and no answer'."""
    ts = _manifest()["truncation_sensitivity"]
    for run, cells in ts["runs"].items():
        for arm, v in cells.items():
            assert v["truncated_no_answer_rate"] <= v["truncation_rate"] + 1e-9, (
                f"{run}/{arm}: truncated-and-no-answer "
                f"({v['truncated_no_answer_rate']}) exceeds truncation "
                f"({v['truncation_rate']})")


def test_truncated_no_answer_never_exceeds_no_answer():
    ts = _manifest()["truncation_sensitivity"]
    for run, cells in ts["runs"].items():
        for arm, v in cells.items():
            assert v["truncated_no_answer_rate"] <= v["no_answer_rate"] + 1e-9


def test_bound_is_named_as_an_all_no_answer_bound():
    ts = _manifest()["truncation_sensitivity"]
    some = next(iter(next(iter(ts["runs"].values())).values()))
    assert "pass@1_all_no_answer_bound" in some
    assert "pass@1_worst_case" not in some, "the ambiguous name must be gone"


def test_integer_counts_are_published_alongside_rates():
    ts = _manifest()["truncation_sensitivity"]
    for run, cells in ts["runs"].items():
        for arm, v in cells.items():
            assert v["n_samples"] > 0
            assert v["n_truncated_no_answer"] <= v["n_no_answer"] <= v["n_samples"]


# ------------------------------------------------------ wait-append paired block

def test_wait_paired_block_makes_the_sign_tests_reconstructible():
    wp = _manifest().get("wait_append_paired")
    assert wp, "manifest must carry wait_append_paired"
    runs = [k for k in wp if not k.startswith("_")]
    assert runs, "at least one wait run must be present"
    for tag in runs:
        for arm, a in wp[tag]["arms"].items():
            assert a["solved_by_question"], f"{tag}/{arm} has no per-question outcomes"
            if arm == "W0_unchanged":
                continue
            paired = a["paired_vs_W0_unchanged"]
            assert paired["n_gained"] == len(paired["gained_question_ids"])
            assert paired["n_lost"] == len(paired["lost_question_ids"])
            assert 0.0 <= paired["one_sided_p"] <= 1.0
            assert paired["two_sided_p"] >= paired["one_sided_p"] - 1e-12


def test_paired_counts_match_the_per_question_outcomes():
    """Recompute gained/lost from the committed per-question data."""
    wp = _manifest()["wait_append_paired"]
    for tag in [k for k in wp if not k.startswith("_")]:
        arms = wp[tag]["arms"]
        ctrl = arms["W0_unchanged"]["solved_by_question"]
        for arm, a in arms.items():
            if arm == "W0_unchanged":
                continue
            solved = a["solved_by_question"]
            gained = sorted(q for q in solved if solved[q] and not ctrl.get(q, False))
            lost = sorted(q for q in ctrl if ctrl[q] and not solved.get(q, False))
            assert gained == a["paired_vs_W0_unchanged"]["gained_question_ids"]
            assert lost == a["paired_vs_W0_unchanged"]["lost_question_ids"]


# ------------------------------------------------------------------ built page

@pytest.mark.skipif(not os.path.exists(BUILT), reason="built page not present")
class TestBuiltPage:
    def _html(self):
        with open(BUILT, encoding="utf-8") as f:
            return f.read()

    def test_no_duplicate_class_attributes(self):
        """The bug: <td class="n" class="over"> silently dropped the styling."""
        html = self._html()
        assert 'class="n" class=' not in html
        assert not re.search(r'<td[^>]*\bclass="[^"]*"[^>]*\bclass=', html)

    def test_over_gate_cells_are_actually_styled(self):
        html = self._html()
        assert 'class="n over"' in html, \
            "no cell carries the over-gate style, but cells do exceed the gate"

    def test_no_placeholders_survive(self):
        html = self._html()
        assert not re.findall(r"__[A-Z_]+__", html)

    def test_utf8_is_lossless(self):
        """cp936 corruption turned the curly apostrophe into a replacement char."""
        html = self._html()
        assert "�" not in html, "replacement characters present: encoding was lossy"
        assert "’" in html, "curly apostrophes should survive the build"

    def test_house_style_has_no_em_dashes(self):
        html = self._html()
        assert "—" not in html and "&mdash;" not in html


# ------------------------------------------------- pipeline figure text fitting

class TestPipelineFigureText:
    """The pipeline figure draws into fixed-width boxes, so its text does not wrap
    automatically: an over-long line runs straight through the rounded border. That
    happened when the type was enlarged, so the limits are pinned here. They are
    derived from the box geometry in make_figures_blog.py (box width in points is
    about W/100 * figwidth * 72, against Times at the chosen size).
    """

    MAX_TITLE_CHARS = 28
    MAX_BODY_LINE_CHARS = 30

    def _steps(self):
        import re
        src = os.path.join(ROOT, "scripts", "make_figures_blog.py")
        with open(src, encoding="utf-8") as f:
            s = f.read()
        blk = s[s.index("steps = ["):s.index("for x0, y0, title, body in steps")]
        titles = re.findall(r'"(STEP[^"]*)"', blk)
        bodies = re.findall(r'"((?:[^"\\]|\\.)*)"\),', blk)
        assert len(titles) == 6 and len(bodies) == 6, "expected six pipeline steps"
        return titles, bodies

    def test_titles_fit_their_boxes(self):
        titles, _ = self._steps()
        for t in titles:
            shown = t.replace("\\u00b7", ".")
            assert len(shown) <= self.MAX_TITLE_CHARS, (
                f"pipeline title {shown!r} is {len(shown)} chars, over the "
                f"{self.MAX_TITLE_CHARS} that fit the box")

    def test_body_lines_fit_their_boxes(self):
        _, bodies = self._steps()
        for b in bodies:
            for line in b.replace("\\n", "\n").split("\n"):
                assert len(line) <= self.MAX_BODY_LINE_CHARS, (
                    f"pipeline body line {line!r} is {len(line)} chars, over the "
                    f"{self.MAX_BODY_LINE_CHARS} that fit the box")

    def test_no_arrow_notation_in_the_figure(self):
        titles, bodies = self._steps()
        for text in titles + bodies:
            assert "->" not in text and "\\u2192" not in text, \
                f"arrow notation in the pipeline figure: {text!r}"
