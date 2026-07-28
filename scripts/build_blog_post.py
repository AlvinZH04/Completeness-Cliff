"""Build the self-contained blog post from its template + the blog figures.

The template (docs/blog/cliff_template.html) carries the prose and CSS with
__FIG0__ .. __FIG4__ placeholders. This script inlines each figure from
docs/figures_blog/ as a base64 data URI, so the published page is a single file
with no external assets (the homepage serves it as one static HTML file).

Usage:
    python scripts/make_figures_blog.py     # regenerate the figures first
    python scripts/build_blog_post.py       # -> docs/blog/completeness-cliff.html

Publish by copying the built file into the homepage repo:
    cp docs/blog/completeness-cliff.html <homepage>/blog/completeness-cliff.html
"""

import base64
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "docs", "blog", "cliff_template.html")
FIGDIR = os.path.join(ROOT, "docs", "figures_blog")
OUT = os.path.join(ROOT, "docs", "blog", "completeness-cliff.html")

FIGURES = {
    "__FIG0__": "fig0_pipeline.png",
    "__FIG1__": "fig1_completeness_cliff.png",
    "__FIG2__": "fig2_open_block_premium.png",
    "__FIG3__": "fig3_rethinking_volume.png",
    "__FIG4__": "fig4_wrongness_type.png",
    "__FIG5__": "fig5_paired_ablation.png",
}


def truncation_table() -> str:
    """Render the appendix truncation table from the committed manifest, so the
    appendix cannot drift from the artifacts the way transcribed numbers do."""
    mpath = os.path.join(ROOT, "results", "blog_manifest.json")
    m = json.load(open(mpath, encoding="utf-8"))
    ts = m.get("truncation_sensitivity")
    if not ts:
        return "<p>(no truncation_sensitivity block in the manifest)</p>"
    label = {
        "ablation_paired_qwen3-4b-thinking_aime": "Ablation, thinking (16k budget)",
        "ablation_paired_qwen3-4b-instruct_aime": "Ablation, instruct (16k)",
        "ablation_paired_qwen3-4b-instruct_aime_32k": "Ablation, instruct (32k rerun)",
        "waitappend_qwen3-4b-instruct_aime": "Intervention, instruct (16k)",
        "waitappend_qwen3-4b-instruct_aime_32k": "Intervention, instruct (32k rerun)",
    }
    order = ["ablation_paired_qwen3-4b-thinking_aime",
             "ablation_paired_qwen3-4b-instruct_aime",
             "ablation_paired_qwen3-4b-instruct_aime_32k",
             "waitappend_qwen3-4b-instruct_aime",
             "waitappend_qwen3-4b-instruct_aime_32k"]
    gate = ts.get("gate", 0.02)
    rows = []
    for run in order:
        cells = ts["runs"].get(run)
        if not cells:
            continue
        rows.append(f'<tr><td colspan="7" class="grp">{label.get(run, run)}</td></tr>')
        for arm, v in cells.items():
            ncls = "n over" if v.get("exceeds_gate") else "n"
            ans = v.get("truncated_still_answered")
            rows.append(
                f"<tr><td>{arm.split('_')[0]} {' '.join(arm.split('_')[1:])}</td>"
                f'<td class="{ncls}">{v["truncation_rate"]:.1%}</td>'
                f'<td class="n">{("%.0f%%" % (100*ans)) if ans is not None else "n/a"}</td>'
                f'<td class="n">{v["truncated_no_answer_rate"]:.1%}</td>'
                f'<td class="n">{v["mean_gen_tokens"]:,.0f}</td>'
                f'<td class="n">{v["accuracy_all_samples"]:.3f}</td>'
                f'<td class="n">{(("%.3f" % v["accuracy_terminated_only"]) if v.get("accuracy_terminated_only") is not None else "n/a")}'
                f' <span class="kept">({v["fraction_samples_kept"]:.0%})</span></td></tr>')
    return (
        '<div class="tw"><table class="d"><thead><tr>'
        "<th>cell</th><th class=\"n\">truncated</th><th class=\"n\">of those, answered</th>"
        "<th class=\"n\">truncated, no answer</th><th class=\"n\">mean tokens</th>"
        "<th class=\"n\">accuracy</th><th class=\"n\">terminated only</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
        f'<p class="mono" style="color:var(--muted)">Red marks a cell above the project\u2019s '
        f'{gate:.0%} truncation gate. "Truncated, no answer" counts samples that hit the cap '
        "<em>and</em> produced no extractable answer, which are the only ones scored as outright "
        "failures; the rest were capped but still gradable, though a longer continuation could "
        "have changed the answer they were graded on. The last column recomputes accuracy over "
        "just the samples that terminated on their own, with the share kept in brackets; it "
        "conditions on termination, which the arms themselves affect, so read it as descriptive."
        "</p>")


def main() -> int:
    html = open(TEMPLATE, encoding="utf-8").read()
    for token, fname in FIGURES.items():
        path = os.path.join(FIGDIR, fname)
        if not os.path.exists(path):
            print(f"missing figure: {path}\nrun scripts/make_figures_blog.py first")
            return 1
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        html = html.replace(token, f"data:image/png;base64,{b64}")

    html = html.replace("__TRUNC_TABLE__", truncation_table())

    leftover = sorted(set(re.findall(r"__FIG\d+__", html)))
    if leftover:
        print(f"unreplaced placeholders: {leftover}\n"
              f"add them to FIGURES in {os.path.basename(__file__)}")
        return 1

    # house style: no em-dashes in published prose
    for bad in ("—", "&mdash;"):
        if bad in html:
            print(f"warning: em-dash ({bad!r}) present in built page")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
