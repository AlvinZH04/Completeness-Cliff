"""Publication-quality figures for the blog post -> $WR_FIGDIR/*.png.

Every value is READ from committed artifacts, never hard-coded:
  * fig 1 and fig 4 come from results/blog_manifest.json (matched subsets, with
    question-level bootstrap intervals) -- see scripts/export_blog_manifest.py
  * fig 2 and fig 3 come from results/inject_*/summary.json (whole-cell aggregates)

Every panel states the question set and n it uses, because trace availability differs
by source and model, so cells are not automatically comparable.

Style: Times New Roman (Tinos, a metric-identical clone bundled in scripts/fonts/),
larger type, black value labels, explanatory prose left to the blog <figcaption>.
"""

import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MANIFEST = json.load(open(os.path.join(RESULTS, "blog_manifest.json")))

# --- register Times New Roman (Tinos) -------------------------------------
_FONTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
for _p in glob.glob(os.path.join(_FONTDIR, "Tinos-*.ttf")):
    fm.fontManager.addfont(_p)
SERIF = "Tinos"  # renders as Times New Roman

# --- palette --------------------------------------------------------------
BLUE, GREEN, MAGENTA = "#1f6dc0", "#0a7d2c", "#c14f8a"
BLACK = "#000000"
INK = "#111111"
GRAY = "#6f6e6a"
GRID = "#deddd7"
WHITE = "#ffffff"

plt.rcParams.update({
    "figure.facecolor": WHITE, "axes.facecolor": WHITE, "savefig.facecolor": WHITE,
    "font.family": "serif", "font.serif": [SERIF, "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 15,
    "axes.titlesize": 16, "axes.labelsize": 15,
    "xtick.labelsize": 13.5, "ytick.labelsize": 13.5,
    "text.color": INK, "axes.labelcolor": INK,
    "axes.edgecolor": "#bfbeb8", "xtick.color": GRAY, "ytick.color": GRAY,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.9,
    "axes.axisbelow": True, "figure.dpi": 200,
})

FIGDIR = os.environ.get("WR_FIGDIR", os.path.join(ROOT, "docs", "figures_blog"))
os.makedirs(FIGDIR, exist_ok=True)


# Matplotlib stamps its own version into a PNG tEXt chunk, so a patch-version bump
# rewrites every figure with byte-different, pixel-identical content. Dropping the
# stamp keeps a regenerated figure's diff limited to figures that actually changed.
SAVE_KW = dict(bbox_inches="tight", metadata={"Software": None})


def clean(ax):
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


def cell(pair, cond):
    """Matched-subset block for one condition (baseline handled separately)."""
    e = MANIFEST["pairs"][pair]
    return e["baseline"] if cond == "baseline" else e["conditions"][cond]


def whole_cell(run, cond):
    """Whole-cell aggregate straight from a committed run summary."""
    return json.load(open(os.path.join(RESULTS, run, "summary.json")))["cells"][cond]


# ============================================================ fig 1: the cliff
FRACS = [0, 0.25, 0.5, 0.75, 1.0]
CONDS = ["baseline", "self_wrong:prefix0.25", "self_wrong:prefix0.5",
         "self_wrong:prefix0.75", "self_wrong:prefix1"]
SERIES = [("qwen3-4b-thinking/aime", "Qwen3-4B-Thinking", BLUE, "o"),
          ("qwen3-4b-instruct/aime", "Qwen3-4B-Instruct", GREEN, "s")]

fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.1), sharey=True)
for ax, k, title in zip(axes, (1, 16),
                        ["pass@1  (single attempt)", "pass@16  (any of 16 attempts)"]):
    for pair, label, color, marker in SERIES:
        vals = [cell(pair, c)[f"pass@{k}"] for c in CONDS]
        lo = [v - cell(pair, c).get(f"pass@{k}_ci95", [v, v])[0]
              for v, c in zip(vals, CONDS)]
        hi = [cell(pair, c).get(f"pass@{k}_ci95", [v, v])[1] - v
              for v, c in zip(vals, CONDS)]
        n = MANIFEST["pairs"][pair]["n_matched"]
        ax.errorbar(FRACS, vals, yerr=[lo, hi], color=color, lw=2.6, marker=marker,
                    ms=8 if marker == "o" else 7.5, zorder=3, capsize=4,
                    elinewidth=1.3, label=f"{label}  (n={n})")
    ax.set_title(title, fontsize=16, color=INK, pad=12)
    ax.set_xticks(FRACS, ["0\n(baseline)", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.06, 1.12)
    clean(ax)

tk16 = [cell("qwen3-4b-thinking/aime", c)["pass@16"] for c in CONDS]
axes[1].text(0.75, tk16[3] + 0.04, f"{tk16[3]:.2f}", ha="center", va="bottom",
             fontsize=13.5, color=BLACK, fontweight="bold")
axes[1].text(0.985, tk16[4] + 0.06, f"{tk16[4]:.2f}", ha="right", va="bottom",
             fontsize=14, color=BLACK, fontweight="bold")
axes[0].set_ylabel("recovery rate", fontsize=15, color=INK)
axes[0].set_xlabel("fraction of the model's own WRONG reasoning injected",
                   fontsize=14.5, color=INK)
axes[0].xaxis.set_label_coords(1.05, -0.15)
axes[0].legend(frameon=False, fontsize=13, loc="upper right",
               handlelength=1.6, borderaxespad=0.4)
axes[1].annotate("the completeness cliff",
                 xy=(0.93, 0.34), xytext=(0.24, 0.42), fontsize=15,
                 color=BLACK, fontweight="bold",
                 arrowprops=dict(arrowstyle="-|>", color=BLACK, lw=1.6))
fig.text(0.5, -0.03,
         "Matched subset per model: questions solved at least once at baseline that also "
         "yielded a usable wrong trace.\nBaseline pass@16 is 1.0 by that selection rule. "
         "Bars are 95% question-level bootstrap intervals.",
         ha="center", fontsize=11.5, color=GRAY)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig1_completeness_cliff.png", **SAVE_KW)
plt.close(fig)

# ================================================ fig 2: open-block premium
# One dataset (AIME), whole-cell aggregates so all three models share a question set
# on the two synthetic/foreign conditions (n=60 each).
PREM_RUNS = [("Qwen3-4B-Thinking", "inject_qwen3-4b-thinking_aime24_25", BLUE),
             ("Qwen3-4B-Instruct", "inject_qwen3-4b-instruct_aime24_25", GREEN),
             ("Gemma-4-E2B (thinking mode)", "inject_gemma-4-e2b_aime24_25", MAGENTA)]
PREM_CONDS = [
    ("wrong_conclusion", "generic pseudo-rationale\nasserting a wrong answer"),
    ("irrelevant", "complete solution to a\nDIFFERENT AIME question"),
    ("self_wrong", "the model's OWN complete\nwrong solution"),
]

fig, ax = plt.subplots(figsize=(10.8, 5.5))
w = 0.25
for i, (name, run, color) in enumerate(PREM_RUNS):
    vals, ns = [], []
    for src, _ in PREM_CONDS:
        o = whole_cell(run, f"{src}:prefix1")
        c = whole_cell(run, f"{src}:full_closed")
        vals.append(o["pass@1"] - c["pass@1"])
        ns.append(o["n_questions"])
    pos = [xi + (i - 1) * (w + 0.03) for xi in range(len(PREM_CONDS))]
    ax.bar(pos, vals, width=w, color=color, label=name, zorder=3)
    for px, v, n in zip(pos, vals, ns):
        ax.text(px, max(v, 0) + 0.016, f"{v:.2f}", ha="center", va="bottom",
                fontsize=12.5, color=BLACK, fontweight="bold")
        ax.text(px, max(v, 0) + 0.062, f"n={n}", ha="center", va="bottom",
                fontsize=9.5, color=GRAY)
ax.set_xticks(range(len(PREM_CONDS)), [lab for _, lab in PREM_CONDS],
              fontsize=13, color=INK)
ax.set_ylabel("open-block premium\n(pass@1: continue thinking - forced answer)",
              fontsize=14.5, color=INK)
ax.set_ylim(0, 0.66)
ax.legend(frameon=False, fontsize=13, loc="upper right",
          handlelength=1.3, borderaxespad=0.5)
clean(ax)
fig.text(0.5, -0.055,
         "AIME, whole-cell aggregates. The first two conditions use all 60 questions for every model; "
         "the self_wrong condition\nis limited to questions where that model produced a wrong trace, "
         "so its n differs by model.",
         ha="center", fontsize=11.5, color=GRAY)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig2_open_block_premium.png", **SAVE_KW)
plt.close(fig)

# ==================================== fig 3: recovery vs re-thinking volume
TOK_RUN = "inject_qwen3-4b-thinking_aime24_25"
# (condition, label, offset in POINTS from the dot, ha) -- offsets are in points so
# placement does not drift with the data scale, and every label gets a leader line
# so which-label-belongs-to-which-dot is never ambiguous.
PTS = [
    ("self_wrong:prefix1", "own wrong,\ncomplete", (24, 22), "left"),
    ("irrelevant:prefix1", "irrelevant,\ncomplete", (-18, 34), "right"),
    ("self_wrong:prefix0.5", "own wrong,\n50% prefix", (20, -30), "left"),
    ("wrong_conclusion:prefix1", "generic\npseudo-rationale", (-16, -32), "right"),
    ("irrelevant:prefix0.25", "irrelevant,\n25% prefix", (22, 18), "left"),
]
fig, ax = plt.subplots(figsize=(9.8, 5.4))
for cond, lab, off, ha in PTS:
    d = whole_cell(TOK_RUN, cond)
    tok, p1, n = d["mean_gen_tokens"], d["pass@1"], d["n_questions"]
    ax.scatter(tok, p1, s=170, color=BLUE, zorder=4, edgecolor=WHITE, linewidth=1.2)
    ax.annotate(f"{lab}  (n={n})", xy=(tok, p1), xytext=off,
                textcoords="offset points", fontsize=12.5, color=INK,
                ha=ha, va="center", linespacing=1.35, zorder=5,
                arrowprops=dict(arrowstyle="-|>", color="#4a4945", lw=1.2,
                                mutation_scale=14, shrinkA=2, shrinkB=10))
ax.set_xlabel("mean continuation length after the injected trace (tokens)",
              fontsize=14.5, color=INK)
ax.set_ylabel("recovery rate (pass@1)", fontsize=14.5, color=INK)
ax.set_ylim(-0.10, 0.95)
ax.set_xlim(-1500, 25500)
clean(ax)
fig.text(0.5, -0.045,
         "Qwen3-4B-Thinking on AIME, whole-cell aggregates. Five condition-level points: "
         "length and recovery co-vary here,\nwhich does not by itself establish that one causes the other.",
         ha="center", fontsize=11.5, color=GRAY)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig3_rethinking_volume.png", **SAVE_KW)
plt.close(fig)

# ==================================== fig 4: which wrongness (one common subset)
PAIR4 = "qwen3-4b-thinking/aime"
BARS = [
    ("corrupted:prefix0.75",
     "75% prefix of a CORRECT solution,\nintegers in the tail perturbed"),
    ("wrong_conclusion:prefix1",
     "generic pseudo-rationale asserting\na wrong answer (no real steps)"),
    ("irrelevant_cross:prefix1",
     "complete MAZE solution\n(wrong domain entirely)"),
    ("irrelevant:prefix1",
     "complete solution to a\nDIFFERENT AIME question"),
    ("self_wrong:prefix1",
     "the model's OWN complete wrong\nsolution (to this question)"),
]
vals = [cell(PAIR4, c)["pass@1"] for c, _ in BARS]
cis = [cell(PAIR4, c).get("pass@1_ci95") for c, _ in BARS]
labels = [lab for _, lab in BARS]
ypos = list(range(len(vals)))[::-1]

fig, ax = plt.subplots(figsize=(11.0, 5.9))
err = [[v - ci[0] for v, ci in zip(vals, cis)], [ci[1] - v for v, ci in zip(vals, cis)]]
ax.barh(ypos, vals, height=0.58, color=BLUE, zorder=3,
        xerr=err, error_kw=dict(ecolor=GRAY, elinewidth=1.3, capsize=4))
for y, v, ci in zip(ypos, vals, cis):
    ax.text(ci[1] + 0.018, y, f"{v:.2f}", va="center", ha="left",
            fontsize=14, color=BLACK, fontweight="bold")
base = cell(PAIR4, "baseline")["pass@1"]
ax.axvline(base, color=GRAY, lw=1.5, ls="--", zorder=2)
ax.text(base, 4.62, f"baseline {base:.2f}  (nothing injected)",
        fontsize=12.5, color=GRAY, ha="center")
ax.set_yticks(ypos, labels, fontsize=12.5, color=INK)
ax.set_xlabel("pass@1 with the wrong trace injected (model may keep thinking)",
              fontsize=14.5, color=INK)
ax.set_xlim(0, 1.05)
ax.grid(axis="y", visible=False)
ax.grid(axis="x", color=GRID, linewidth=0.9)
ax.tick_params(length=0)
n4 = MANIFEST["pairs"][PAIR4]["n_matched"]
fig.text(0.5, -0.05,
         f"Qwen3-4B-Thinking, AIME. All five bars use the SAME {n4} questions "
         "(solved at baseline and having a usable wrong trace),\n"
         "with 95% question-level bootstrap intervals. The two foreign-rationale "
         "conditions overlap and are not distinguishable here.",
         ha="center", fontsize=11.5, color=GRAY)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig4_wrongness_type.png", **SAVE_KW)
plt.close(fig)

# ============================================================ fig 0: pipeline
# The boxes are a fixed width and the text inside them does NOT wrap: an over-long
# line runs straight through the rounded border. Box width in points is about
# W/100 * figwidth * 72, which at this size leaves room for roughly 30 characters of
# body text and 28 of bold title. test/test_build_and_stats.py pins those limits.
fig, ax = plt.subplots(figsize=(11.2, 8.6))
ax.set_xlim(0, 100); ax.set_ylim(0, 78); ax.axis("off"); ax.grid(False)

W, H = 31.5, 33
ROW1, ROW2 = 42, 3
COLS = [0.6, 34.25, 67.9]
steps = [
    (COLS[0], ROW1, "STEP 1  ·  Questions",
     "60 AIME problems (2024 and\n2025), each with an exact\nanswer verifier. Reasoning-gym\npuzzles (maze, sudoku) were\nalso run but leave too few\nusable questions to plot"),
    (COLS[1], ROW1, "STEP 2  ·  Baseline rollouts",
     "Each model answers every\nquestion 16 times (vLLM,\nofficial sampling), giving\nnormal pass@k and a pool of\nraw reasoning traces"),
    (COLS[2], ROW1, "STEP 3  ·  Wrong-trace bank",
     "Keep rollouts whose final\nanswer was WRONG. That is the\nreasoning we inject. Also keep\ncorrect traces (to corrupt)\nand other questions' traces\n(as irrelevant donors)"),
    (COLS[0], ROW2, "STEP 4  ·  Inject the trace",
     "Splice a wrong trace into a\nfresh prompt's think block.\nVary how much of it (a quarter\nup to all), what kind of\nwrongness, and whether\nthinking may CONTINUE or stop"),
    (COLS[1], ROW2, "STEP 5  ·  Re-generate",
     "16 new samples per question\nand condition: the model picks\nup mid-thought from the\ninjected wrong reasoning"),
    (COLS[2], ROW2, "STEP 6  ·  Grade & measure",
     "Grade ONLY newly generated\ntokens (math_verify /\nverifiers), giving pass@k,\nadoption rate, and a\ntoken-level audit of what the\nmodel did next"),
]
for x0, y0, title, body in steps:
    ax.add_patch(FancyBboxPatch((x0, y0), W, H, boxstyle="round,pad=0.7",
                                fc="#e8f1fc", ec=BLUE, lw=1.5))
    ax.text(x0 + W / 2, y0 + H - 4.0, title, ha="center", va="center",
            fontsize=17, color=INK, fontweight="bold")
    ax.text(x0 + W / 2, y0 + (H - 7.4) / 2 - 0.4, body, ha="center", va="center",
            fontsize=15, color="#2e2d2b", linespacing=1.6)

arrow = dict(arrowstyle="-|>", mutation_scale=27, color="#444340", lw=2.7)
mid1, mid2 = ROW1 + H / 2, ROW2 + H / 2
ax.add_patch(FancyArrowPatch((COLS[0] + W + 0.9, mid1), (COLS[1] - 0.9, mid1), **arrow))
ax.add_patch(FancyArrowPatch((COLS[1] + W + 0.9, mid1), (COLS[2] - 0.9, mid1), **arrow))
ax.add_patch(FancyArrowPatch((COLS[2] + W / 2, ROW1 - 1.2), (COLS[0] + W / 2, ROW2 + H + 1.2),
                             connectionstyle="arc3,rad=0.06", **arrow))
ax.add_patch(FancyArrowPatch((COLS[0] + W + 0.9, mid2), (COLS[1] - 0.9, mid2), **arrow))
ax.add_patch(FancyArrowPatch((COLS[1] + W + 0.9, mid2), (COLS[2] - 0.9, mid2), **arrow))

fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig0_pipeline.png", **SAVE_KW)
plt.close(fig)


# ============================ fig 5: paired fixed-answer scaffold ablation
_AB = MANIFEST.get("paired_ablation", {})
if _AB.get("qwen3-4b-thinking"):
    AB_ARMS = [
        ("A_answer_only", "A. bare claim\n\u201cThe answer is W.\u201d"),
        ("B_generic", "B. generic pseudo-rationale\nno real work shown"),
        ("C_task_specific", "C. short task-specific\nrationale about THIS problem"),
        ("D_own_complete", "D. the model\u2019s OWN complete\nwrong derivation"),
    ]
    MODELS_AB = [("qwen3-4b-thinking", "Qwen3-4B-Thinking", BLUE),
                 ("qwen3-4b-instruct", "Qwen3-4B-Instruct", GREEN)]
    MODELS_AB = [m for m in MODELS_AB if _AB.get(m[0])]

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.6), sharey=True)
    h = 0.34
    for ax, k, title in ((axes[0], 1, "pass@1  (single attempt)"),
                         (axes[1], 16, "pass@16  (any of 16 attempts)")):
        for mi, (mkey, mlabel, color) in enumerate(MODELS_AB):
            e = _AB[mkey]
            vals, errs = [], [[], []]
            for arm, _ in AB_ARMS:
                d = e["arms"][f"{arm}:prefix1"]
                v = d[f"pass@{k}"]
                ci = d.get(f"pass@{k}_ci95", [v, v])
                vals.append(v); errs[0].append(v - ci[0]); errs[1].append(ci[1] - v)
            ypos = [len(AB_ARMS) - 1 - a + (0.5 - mi) * h for a in range(len(AB_ARMS))]
            n = e["baseline"]["n_questions"]
            ax.barh(ypos, vals, height=h, color=color, zorder=3,
                    label=f"{mlabel}  (n={n})",
                    xerr=errs, error_kw=dict(ecolor=GRAY, elinewidth=1.1, capsize=3))
            for y, v, hi in zip(ypos, vals, errs[1]):
                ax.text(v + hi + 0.025, y, f"{v:.2f}", va="center", ha="left",
                        fontsize=11.5, color=BLACK, fontweight="bold")
            ax.axvline(e["baseline"][f"pass@{k}"], color=color, lw=1.3, ls="--",
                       alpha=0.75, zorder=2)
        ax.set_title(title, fontsize=15.5, color=INK, pad=10)
        ax.set_xlim(0, 1.12)
        ax.set_ylim(-0.75, 3.75)
        ax.grid(axis="y", visible=False)
        ax.grid(axis="x", color=GRID, linewidth=0.9)
        ax.tick_params(length=0)
        ax.set_xlabel("recovery with the SAME wrong answer injected", fontsize=13.5, color=INK)
    axes[0].set_yticks(range(len(AB_ARMS))[::-1], [lab for _, lab in AB_ARMS],
                       fontsize=12, color=INK)
    axes[0].legend(frameon=False, fontsize=12, loc="lower right", borderaxespad=0.4)
    fig.text(0.5, -0.07,
             "AIME, model may keep thinking. Every arm asserts the SAME wrong answer, so only the scaffold varies. "
             "Dashed lines are each model\u2019s baseline on its own question set.\n"
             "Adding steps does not make the wrong answer stickier: A, B and C all sit near baseline in both models. "
             "Only the model\u2019s own COMPLETE derivation collapses recovery,\nand in both models its interval "
             "overlaps none of the others. 95% question-level bootstrap intervals.",
             ha="center", fontsize=11, color=GRAY)
    fig.tight_layout()
    fig.savefig(f"{FIGDIR}/fig5_paired_ablation.png", **SAVE_KW)
    plt.close(fig)
    print("wrote fig5 (paired ablation,", len(MODELS_AB), "models)")

# ===================================================== social card (Open Graph)
# Exactly 1200x630, the size link unfurlers crop to. bbox_inches="tight" would
# resize the canvas and break that, so this one figure saves without it.
fig = plt.figure(figsize=(6.0, 3.15), dpi=200)
fig.patch.set_facecolor(WHITE)
fig.text(0.055, 0.885, "The completeness cliff", fontsize=25, color=INK,
         fontweight="bold", va="top", family="serif")
fig.text(0.055, 0.745,
         "Language models escape wrong reasoning until it is finished",
         fontsize=12.5, color=GRAY, va="top", family="serif")

axc = fig.add_axes([0.055, 0.145, 0.60, 0.50])
for pair, label, color, marker in SERIES:
    v = [cell(pair, c)["pass@16"] for c in CONDS]
    axc.plot(FRACS, v, color=color, lw=2.2, marker=marker, ms=5, label=label)
axc.set_xticks(FRACS, ["0", "25%", "50%", "75%", "100%"], fontsize=8, color=GRAY)
axc.set_yticks([0, 0.5, 1.0], ["0", ".5", "1"], fontsize=8, color=GRAY)
axc.set_ylim(-0.08, 1.15)
axc.set_xlabel("fraction of the model's own wrong reasoning injected",
               fontsize=8.5, color=GRAY, labelpad=2)
axc.set_ylabel("pass@16", fontsize=8.5, color=GRAY, labelpad=2)
axc.legend(frameon=False, fontsize=7.5, loc="lower left", handlelength=1.3)
axc.grid(axis="x", visible=False)
axc.tick_params(length=0)

drop = cell("qwen3-4b-thinking/aime", "self_wrong:prefix1")["pass@16"]
axc.annotate("the floor drops out", xy=(0.99, drop + 0.04), xytext=(0.30, 0.26),
             fontsize=9, color=BLACK, fontweight="bold", family="serif",
             ha="left", va="center",
             arrowprops=dict(arrowstyle="-|>", color=BLACK, lw=1.1,
                             mutation_scale=8, shrinkA=3, shrinkB=4))
fig.text(0.70, 0.545,
         "A model given part of its\nown faulty reasoning\nrecovers almost every time.\n"
         "Given all of it, it almost\nnever does.",
         fontsize=10.5, color=INK, va="top", family="serif", linespacing=1.55)
fig.text(0.70, 0.175, "Alvin Zhang  ·  Johns Hopkins",
         fontsize=9, color=GRAY, va="top", family="serif")
fig.savefig(f"{FIGDIR}/social_card.png", metadata={"Software": None})
plt.close(fig)
print("wrote social card (1200x630)")

print("wrote blog figures to", FIGDIR)
