"""pass@k and aggregate metrics."""

import math


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al. 2021).

    n = samples drawn, c = correct among them, k <= n.
    """
    if k > n:
        raise ValueError(f"k={k} > n={n}")
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def aggregate(question_results: list[dict], ks: tuple[int, ...] = (1, 2, 4, 8, 16)) -> dict:
    """question_results: [{"n": int, "correct": int, "adopted": int,
    "no_answer": int, "truncated": int, "gen_tokens": [int, ...]}, ...]"""
    if not question_results:
        return {"n_questions": 0}
    out: dict = {"n_questions": len(question_results)}
    n_min = min(q["n"] for q in question_results)
    for k in ks:
        if k <= n_min:
            out[f"pass@{k}"] = sum(pass_at_k(q["n"], q["correct"], k)
                                   for q in question_results) / len(question_results)
    total = sum(q["n"] for q in question_results)
    out["n_samples"] = total
    out["accuracy"] = sum(q["correct"] for q in question_results) / total
    out["adoption_rate"] = sum(q.get("adopted", 0) for q in question_results) / total
    out["no_answer_rate"] = sum(q.get("no_answer", 0) for q in question_results) / total
    out["truncation_rate"] = sum(q.get("truncated", 0) for q in question_results) / total
    toks = [t for q in question_results for t in q.get("gen_tokens", [])]
    if toks:
        out["mean_gen_tokens"] = sum(toks) / len(toks)
        out["max_gen_tokens"] = max(toks)
    return out
