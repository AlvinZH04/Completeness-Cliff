"""Audit generated continuations after an injected trace.

For each (question x condition) row, classify every sample:
- answer class: correct / adopted (= trace answer; for irrelevant, the donor's) /
  other_wrong / no_answer
- target engagement: does the continuation mention numbers distinctive to the
  TARGET question (present in the target question, absent from the donor
  question and the injected trace)? A cheap-but-objective signal that the model
  actually engaged with the real question rather than continuing the trace.
- switch markers: phrases indicating the model noticed something is off.

Usage:
    python -m src.audit --injection results/inject_X/rollouts.jsonl \
        --baseline results/base_X/rollouts.jsonl \
        --cells irrelevant:prefix0.25 irrelevant:prefix1 self_wrong:prefix1 \
        --dump 3 --out docs/experiments/audit_X.md
"""

import argparse
import json
import re
from collections import defaultdict

SWITCH_PHRASES = (
    "different problem", "different question", "not the question",
    "the question asks", "the actual question", "the problem asks",
    "wait", "hold on", "actually", "hmm", "that's not", "unrelated",
    "let me re-read", "re-read the", "going back to the problem",
)

_NUM = re.compile(r"(?<![\w.])\d{2,}(?![\w.])")  # numbers with >=2 digits


def distinctive_numbers(target_q: str, donor_q: str | None, trace: str) -> set[str]:
    tgt = set(_NUM.findall(target_q))
    other = set(_NUM.findall(donor_q or "")) | set(_NUM.findall(trace or ""))
    return tgt - other


def audit_rows(inj_rows: list[dict], q_text: dict[str, str], cells: list[str],
               dump: int = 0):
    stats = defaultdict(lambda: defaultdict(float))
    examples = defaultdict(list)
    for r in inj_rows:
        if cells and r["condition"] not in cells:
            continue
        cell = r["condition"]
        tgt_q = q_text.get(r["qid"], "")
        donor_q = q_text.get(r["donor_qid"]) if r.get("donor_qid") else None
        distinct = distinctive_numbers(tgt_q, donor_q if r["source"] == "irrelevant"
                                       else None, r.get("trace_text", ""))
        for s in r["samples"]:
            cont = (s.get("thinking") or "") + "\n" + (s.get("final") or "")
            low = cont.lower()
            st = stats[cell]
            st["n"] += 1
            if s["correct"]:
                st["correct"] += 1
            elif s.get("adopted"):
                st["adopted"] += 1
            elif s.get("answer") is None:
                st["no_answer"] += 1
            else:
                st["other_wrong"] += 1
            engaged = bool(distinct) and any(d in cont for d in distinct)
            st["target_engaged"] += engaged
            st["has_distinct"] += bool(distinct)
            n_switch = sum(low.count(p) for p in SWITCH_PHRASES)
            st["switch_markers"] += n_switch
            st["any_switch"] += n_switch > 0
            st["cont_tokens"] += s.get("n_tokens", 0)
        if len(examples[cell]) < dump:
            s0 = r["samples"][0]
            examples[cell].append({
                "qid": r["qid"], "donor": r.get("donor_qid"), "gold": r["gold"],
                "trace_answer": r.get("trace_answer"), "answer": s0.get("answer"),
                "correct": s0["correct"],
                "continuation_head": ((s0.get("thinking") or s0.get("final") or "")[:1200]),
            })
    return stats, examples


def fmt(stats) -> str:
    lines = ["| cell | n | correct | adopted | other-wrong | no-ans | engaged-target | any-switch | markers/sample | mean-tok |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for cell in sorted(stats):
        st = stats[cell]
        n = st["n"]
        def pct(k):
            return f"{st[k] / n:.2f}"
        cov = st["has_distinct"] / n
        eng = (st["target_engaged"] / st["has_distinct"]) if st["has_distinct"] else float("nan")
        lines.append(
            f"| {cell} | {int(n)} | {pct('correct')} | {pct('adopted')} | "
            f"{pct('other_wrong')} | {pct('no_answer')} | {eng:.2f} (cov {cov:.2f}) | "
            f"{pct('any_switch')} | {st['switch_markers'] / n:.1f} | "
            f"{st['cont_tokens'] / n:.0f} |")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--injection", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--cells", nargs="*", default=[])
    ap.add_argument("--dump", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    with open(args.baseline) as f:
        q_text = {r["qid"]: r["question"] for r in map(json.loads, f)}
    with open(args.injection) as f:
        inj_rows = [json.loads(line) for line in f]

    stats, examples = audit_rows(inj_rows, q_text, args.cells, dump=args.dump)
    table = fmt(stats)
    print(table)

    if args.out:
        parts = ["# Continuation audit\n",
                 f"Injection: `{args.injection}`\n",
                 "engaged-target = fraction of samples whose continuation mentions a "
                 "number distinctive to the TARGET question (cov = fraction of samples "
                 "where such distinctive numbers exist). any-switch = fraction with at "
                 "least one switch/correction phrase.\n",
                 table, "\n\n## Examples (first sample per row)\n"]
        for cell, exs in sorted(examples.items()):
            parts.append(f"\n### {cell}\n")
            for e in exs:
                parts.append(
                    f"- **{e['qid']}** (donor {e['donor']}, gold {e['gold']}, "
                    f"trace_answer {e['trace_answer']}) → answer {e['answer']} "
                    f"(correct={e['correct']})\n\n  ```\n  "
                    + e["continuation_head"].replace("\n", "\n  ") + "\n  ```\n")
        with open(args.out, "w") as f:
            f.write("\n".join(parts))
        print(f"\nwrote {args.out}")
