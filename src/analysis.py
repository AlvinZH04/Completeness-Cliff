"""Combine baseline + injection summaries into a markdown report.

    python -m src.analysis results/base_x/summary.json results/inject_x/summary.json
"""

import argparse
import json


def fmt_cells(baseline: dict | None, injection: dict) -> str:
    ks = [k for k in ("pass@1", "pass@2", "pass@4", "pass@8", "pass@16")]
    lines = []
    header = ("| condition | nq | " + " | ".join(ks)
              + " | adopt | no-ans | trunc | mean-tok |")
    sep = "|" + "---|" * (len(ks) + 5)
    lines += [header, sep]

    def row(name: str, m: dict) -> str:
        cells = [f"{m[k]:.3f}" if k in m else "-" for k in ks]
        return (f"| {name} | {m['n_questions']} | " + " | ".join(cells)
                + f" | {m.get('adoption_rate', 0):.3f} | {m['no_answer_rate']:.3f}"
                + f" | {m['truncation_rate']:.3f} | {m.get('mean_gen_tokens', 0):.0f} |")

    if baseline:
        lines.append(row("baseline", baseline["metrics"]))
    for cell, m in injection["cells"].items():
        lines.append(row(cell, m))
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("summaries", nargs="+")
    args = ap.parse_args()

    baseline = None
    injections = []
    for path in args.summaries:
        with open(path) as f:
            s = json.load(f)
        if s.get("phase") == "baseline":
            baseline = s
        else:
            injections.append(s)

    for inj in injections:
        print(f"\n## {inj['run_name']} (model={inj['model']}, "
              f"thinking={inj['thinking_mode']}, n={inj['n_samples']})\n")
        print(fmt_cells(baseline, inj))
    if baseline and not injections:
        print(fmt_cells(None, {"cells": {"baseline": baseline["metrics"]},
                               "run_name": baseline["run_name"]}))


if __name__ == "__main__":
    main()
