"""Generate docs/blog/x_post_drafts.txt with X character counts computed, not guessed.

X counts any URL as 23 characters regardless of length, so the length check
substitutes the link before measuring.
"""
import re

LINK = "https://alvinzh04.github.io/blog/completeness-cliff.html"
LIMIT = 280


def xlen(text):
    """X-visible length: every URL counts as 23."""
    return len(re.sub(r"https?://\S+", "x" * 23, text.strip()))


THREAD = [
    ("1/7", "fig1 (the cliff) -- carries the whole point, do not post without it",
     f"Splice an INCORRECT chain of thought into a model's reasoning and let it keep going: "
     f"can it still reach the right answer in k tries? A pilot on a matched Qwen3-4B "
     f"thinking/instruct pair.\n\nShort answer: yes, right up until the wrong reasoning is "
     f"finished.\n\n{LINK}"),

    ("2/7", "none (let the numbers stand)",
     "Through 25/50/75% of a model's OWN wrong derivation, pass@16 on AIME barely moves: "
     "1.00, 1.00, 1.00, 0.91.\n\nAt 100% it falls to 0.04, which on this subset is ONE "
     "question out of 23. Forcing an instant answer gives the same 0.04, so the open "
     "thinking budget buys nothing there."),

    ("3/7", "fig2 (who spends the open block)",
     "Is it just having a thinking mode? Partly.\n\nHanded a complete solution to a DIFFERENT "
     "question, only the reasoning-trained model starts over: +0.41 open-block premium vs "
     "+0.01 for its instruct sibling, +0.07 for Gemma.\n\nOn a generic pseudo-rationale, "
     "instruct gains +0.44 too."),

    ("4/7", "fig4 (the ordering across kinds of wrongness)",
     "Recovery (pass@1) by kind of wrongness, same 23 questions:\n\ncorrect chain w/ corrupted "
     "numbers 0.89\ngeneric pseudo-rationale 0.51\ncomplete foreign rationale ~0.38\nthe "
     "model's OWN complete wrong solution 0.02\n\nIts own finished reasoning is in a class "
     "of its own."),

    ("5/7", "fig5 (the paired ablation) -- the methodological core of the post",
     "Those bars don't hold the wrong answer fixed, so I ran one that does. Same wrong "
     "answer, four ways, recovery:\n\nbare claim 0.33\ngeneric rationale 0.39\nshort task-spec 0.53\n"
     "its own complete derivation 0.03\n\nNo scaffold explains the collapse. Completeness "
     "does."),

    ("6/7", "none",
     "If completion is what closes the argument, doubt should reopen it.\n\nAppending \"Wait, "
     "let me double-check that.\" to the finished wrong chain roughly triples pass@16 (0.07 "
     "to 0.20 thinking, 0.02 to 0.20 instruct). A neutral \"So,\" does nothing.\n\nPartial "
     "rescue, not a fix."),

    ("7/7", "none",
     f"Caveats: selected subsets of 23-33 questions, wide intervals at the edge, some "
     f"instruct cells above a 2% truncation gate.\n\nClosest prior work is Yang et al. "
     f"(2506.10979) on identify-but-fail-to-recover. Added here: pass@k, and the "
     f"completeness axis.\n\n{LINK}"),
]

SINGLES = [
    ("A", "leads with the number (tends to travel furthest)", "fig1",
     f"Feed a reasoning model 75% of its own WRONG derivation and it still solves the AIME "
     f"question within 16 tries (pass@16 0.91). Feed it the whole wrong trace and recovery "
     f"falls to 0.04: one question out of 23.\n\nCompletion, not correctness, is what "
     f"sticks.\n\n{LINK}"),
    ("B", "leads with the idea", "fig1",
     f"A model treats an unfinished rationale as a problem to work and a finished one as a "
     f"conclusion to state. What flips it is the reasoning looking complete and well-formed, "
     f"not it being right.\n\nPilot on injected wrong chains of thought:\n{LINK}"),
    ("C", "leads with the intervention", "fig5",
     f"Give a model its own finished wrong derivation and it almost never escapes.\n\nAppend "
     f"\"Wait, let me double-check that.\" and pass@16 roughly triples, 0.07 to 0.20. The "
     f"ability was there; it just wasn't deployed.\n\n{LINK}"),
]

out = []
w = out.append
w("X POST DRAFTS: The completeness cliff")
w("=" * 38)
w(f"Link: {LINK}")
w("")
w("BEFORE POSTING, two gates:")
w("  1. The blog file must be live on the homepage, or the link 404s.")
w("  2. github.com/AlvinZH04/Completeness-Cliff must be PUBLIC. The post links to it")
w("     as the code repository; it is private as of this writing.")
w("")
w("Character counts below are computed, not estimated: X counts any URL as 23 chars")
w("regardless of length, and every draft here is measured that way against the 280 limit.")
w("Optional tags: @Alibaba_Qwen (Qwen3), @GoogleDeepMind (Gemma).")
w("")
w("REVISED 2026-07-28 for the restructured post. Claims that must NOT be posted, each")
w("retracted by a later experiment in this project:")
w("  - \"Instruct gains ~0 everywhere\" (it gains +0.44 on a generic pseudo-rationale)")
w("  - \"Recovery is gated on mismatch detection\" (cross-domain and same-domain land on")
w("    top of each other on a common question set)")
w("  - \"The paired fixed-answer ablation is the next run\" (it has been run; it is now")
w("    the strongest result in the post and post 5/7 below carries it)")
w("")
w("FIGURE PLAN FOR THE THREAD")
w("-" * 38)
w("  1/7  fig1_completeness_cliff.png the headline; the thread is much weaker without it")
w("  3/7  fig2_open_block_premium.png who actually spends the extra thinking")
w("  4/7  fig4_wrongness_type.png   the ordering across kinds of wrongness")
w("  5/7  fig5_paired_ablation.png  same wrong answer, four scaffolds")
w("  Held back: fig0 (pipeline) and fig3 (recovery vs continuation length). Both are")
w("  explanatory rather than persuasive, and four images across seven posts already")
w("  gives every scroll-stop a visual. Use fig0 only if replying to a method question.")
w("  All live in docs/figures_blog/.")
w("")
w("=" * 38)
w("THREAD (recommended: the finding is multi-part and the caveats belong inline)")
w("=" * 38)
for tag, img, body in THREAD:
    n = xlen(body)
    flag = "" if n <= LIMIT else f"   *** OVER BY {n - LIMIT} ***"
    w("")
    w(f"[{tag}]  ({n} chars){flag}")
    w(f"  image: {img}")
    w("-" * 38)
    w(body)
w("")
w("=" * 38)
w("SINGLE POSTS (if you'd rather not thread)")
w("=" * 38)
for tag, note, img, body in SINGLES:
    n = xlen(body)
    flag = "" if n <= LIMIT else f"   *** OVER BY {n - LIMIT} ***"
    w("")
    w(f"DRAFT {tag}: {note}  ({n} chars){flag}")
    w(f"  image: {img}")
    w("-" * 38)
    w(body)
w("")
w("=" * 38)
w("Posting notes")
w("=" * 38)
w("- The thread is the better fit: the result is multi-part, and posts 5 and 7 keep the")
w("  ablation and the prior-work credit inside the thread instead of buried in the blog.")
w("- Post 5/7 is the one that answers the obvious objection (\"isn't this just a")
w("  plausible-looking scaffold?\"). Do not drop it to shorten the thread.")
w("- Every number above is in results/blog_manifest.json and reproduces from raw rollouts")
w("  via scripts/export_blog_manifest.py --check.")
w("- Yang et al. arXiv:2506.10979 is cited by number in 7/7 because the credit should be")
w("  legible without a click.")

text = "\n".join(out) + "\n"
open("docs/blog/x_post_drafts.txt", "w", encoding="utf-8").write(text)

over = [t for t, _, b in THREAD if xlen(b) > LIMIT] + [t for t, _, _, b in SINGLES if xlen(b) > LIMIT]
print("wrote docs/blog/x_post_drafts.txt")
print("thread lengths:", [xlen(b) for _, _, b in THREAD])
print("single lengths:", [xlen(b) for _, _, _, b in SINGLES])
print("OVER LIMIT:", over or "none")
