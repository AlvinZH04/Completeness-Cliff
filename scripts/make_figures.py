"""Generate pilot-1 figures for the mentor write-up -> docs/figures/*.png.

Numbers are transcribed from the matched-subset analyses recorded in
docs/daily/2026-07-1{7,8,9}.md and results/*/summary.json.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# validated palette (dataviz reference instance, light mode)
BLUE, GREEN, MAGENTA = "#2a78d6", "#008300", "#e87ba4"
INK, SEC, MUTED, GRID, BASE, SURF = ("#0b0b0b", "#52514e", "#898781",
                                     "#e1e0d9", "#c3c2b7", "#fcfcfb")

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.labelcolor": SEC, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "font.family": "DejaVu Sans",
})
import os
FIGDIR = os.environ.get("WR_FIGDIR", "docs/figures")
os.makedirs(FIGDIR, exist_ok=True)


def style(ax):
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


# ---------------------------------------------------------------- fig 1: cliff
F = [0, 0.25, 0.5, 0.75, 1.0]
think_p16 = [1.000, 1.000, 1.000, 0.913, 0.043]
instr_p16 = [1.000, 0.909, 0.879, 0.636, 0.030]
think_p1 = [0.753, 0.655, 0.486, 0.302, 0.024]
instr_p1 = [0.587, 0.536, 0.449, 0.314, 0.004]

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
for ax, (tk, it), title in zip(
        axes, [(think_p1, instr_p1), (think_p16, instr_p16)],
        ["pass@1  (single attempt)", "pass@16  (any of 16 attempts)"]):
    ax.plot(F, tk, color=BLUE, lw=2, marker="o", ms=6, zorder=3,
            label="Qwen3-4B-Thinking")
    ax.plot(F, it, color=GREEN, lw=2, marker="s", ms=6, zorder=3,
            label="Qwen3-4B-Instruct")
    ax.set_title(title, fontsize=12, color=INK, pad=10)
    ax.set_xticks(F, ["0\n(baseline)", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.04, 1.06)
    style(ax)
axes[0].set_ylabel("recovery rate")
axes[0].set_xlabel("fraction of the model's own WRONG reasoning injected (think block open)")
axes[0].xaxis.set_label_coords(1.05, -0.16)
axes[0].legend(frameon=False, fontsize=10, loc="upper right")
axes[1].annotate("the completeness cliff:\ncapability itself collapses",
                 xy=(0.965, 0.10), xytext=(0.28, 0.30), fontsize=10, color=SEC,
                 arrowprops=dict(arrowstyle="->", color=SEC, lw=1.2))
fig.suptitle("Recovery from the model's own wrong reasoning (AIME 24+25, matched subsets, N=16)",
             fontsize=13, color=INK, x=0.5, y=1.0)
fig.text(0.5, -0.045, "Partial wrong prefixes only reshape the answer distribution (pass@16 holds); a COMPLETE wrong trace destroys recoverability for both models.",
         ha="center", fontsize=9.5, color=MUTED)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig1_completeness_cliff.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------- fig 2: open-block premium
conds = ["bare wrong assertion\n(maze)", "irrelevant trace, complete\n(AIME)",
         "own wrong reasoning, complete\n(AIME)"]
prem = {
    "Qwen3-4B-Thinking": [0.862, 0.364, 0.021],
    "Qwen3-4B-Instruct": [0.043, 0.012, 0.004],
    "Gemma-4-E2B (thinking mode)": [0.000, 0.068, 0.000],
}
colors = [BLUE, GREEN, MAGENTA]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
x = range(len(conds))
w = 0.26
for i, (name, vals) in enumerate(prem.items()):
    pos = [xi + (i - 1) * (w + 0.02) for xi in x]
    bars = ax.bar(pos, vals, width=w, color=colors[i], label=name, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:+.2f}"[1:] if v >= 0 else f"{v:.2f}",
                ha="center", fontsize=9, color=SEC)
ax.set_xticks(list(x), conds)
ax.set_ylabel("open-block premium\n(pass@1, open continuation − forced answer)")
ax.set_ylim(0, 0.98)
ax.legend(frameon=False, fontsize=9.5, loc="upper right")
ax.set_title("What is the right to keep thinking worth? Only trained models use it — and never on their own finished reasoning",
             fontsize=12, color=INK, pad=12)
style(ax)
fig.text(0.5, -0.06,
         "Each bar: pass@1 gain from letting the model CONTINUE thinking after the injected wrong trace, versus forcing it to answer immediately\n"
         "(same injected content in both cases). Tall bar = the model actually uses the extra thinking to recover; near-zero = the thinking channel goes unused.",
         ha="center", fontsize=9.5, color=MUTED)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig2_open_block_premium.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------- fig 3: recovery vs re-thinking volume
pts = [  # (continuation tokens, pass@1, label, dx, dy)
    (20930, 0.76, "irrelevant, 25% prefix", -800, 0.045),
    (18660, 0.71, "bare wrong assertion", -800, -0.075),
    (18104, 0.40, "own wrong, 50% prefix", -800, 0.045),
    (9813, 0.46, "irrelevant, complete", 700, 0.03),
    (1076, 0.02, "own wrong, complete", 500, 0.05),
]
fig, ax = plt.subplots(figsize=(8.5, 4.6))
for tok, p1, lab, dx, dy in pts:
    ax.scatter(tok, p1, s=110, color=BLUE, zorder=3)
    ha = "right" if dx < 0 else "left"
    ax.annotate(lab, (tok, p1), xytext=(tok + dx, p1 + dy), fontsize=9.5,
                color=SEC, ha=ha)
ax.set_xlabel("mean continuation length after the injected trace (tokens)")
ax.set_ylabel("recovery rate (pass@1)")
ax.set_ylim(-0.05, 0.9)
ax.set_xlim(-500, 23500)
ax.set_title("Recovery tracks how much re-thinking the injection provokes\n(Qwen3-4B-Thinking on AIME; own completed reasoning provokes almost none)",
             fontsize=12, color=INK, pad=12)
style(ax)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig3_rethinking_volume.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# ------------------------------------ fig 4: which wrongness (complete, open)
labels = ["corrupted correct solution\n(right reasoning, numbers perturbed near the cut)",
          "complete solution to a MAZE problem\n(wrong domain entirely)",
          "bare claim of a wrong answer\n(“the answer is X” — no derivation)",
          "complete solution to a DIFFERENT AIME problem\n(right domain, wrong question)",
          "the model's OWN complete wrong solution\n(to this exact question)"]
vals = [0.889, 0.545, 0.514, 0.375, 0.024]
fig, ax = plt.subplots(figsize=(9.6, 4.9))
bars = ax.barh(range(len(vals))[::-1], vals, height=0.62, color=BLUE, zorder=3)
for y, v in zip(range(len(vals))[::-1], vals):
    ax.text(v + 0.012, y, f"{v:.2f}", va="center", fontsize=10, color=SEC)
ax.axvline(0.753, color=BASE, lw=1.4, ls="--", zorder=2)
ax.text(0.753, 4.55, "baseline 0.75", fontsize=9, color=MUTED, ha="center")
ax.set_yticks(range(len(vals))[::-1], labels, fontsize=9.5)
ax.set_xlabel("pass@1 with the wrong trace injected (think block open)")
ax.set_xlim(0, 1.0)
ax.grid(axis="y", visible=False)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.tick_params(length=0)
ax.set_title("The reasoning scaffold persuades, not the conclusion\n(Qwen3-4B-Thinking, AIME: what kind of wrong content is injected into the think block?)",
             fontsize=12, color=INK, pad=12)
fig.text(0.5, -0.045,
         "Each bar = a different KIND of injected wrong content. The same wrong answer is rejected when asserted without steps (0.51)\n"
         "but accepted when wrapped in the model's own plausible derivation (0.02); errors inside a correct scaffold get silently repaired (0.89).",
         ha="center", fontsize=9.5, color=MUTED)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig4_wrongness_type.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# -------------------------------------------------------- fig 0: pipeline
fig, ax = plt.subplots(figsize=(13.0, 6.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off"); ax.grid(False)

W, H = 29.5, 23  # box size
ROW1, ROW2 = 35, 4  # y of box bottoms
COLS = [1.5, 35.25, 69.0]
steps = [
    (COLS[0], ROW1, "STEP 1 · Questions",
     "60 AIME competition problems\n(2024 + 2025) and 100 reasoning-gym\npuzzles (maze, sudoku) with\nexact answer verifiers"),
    (COLS[1], ROW1, "STEP 2 · Baseline rollouts",
     "Each model answers every question\n16 times (vLLM, official sampling\nparams) → normal pass@k, and a\npool of raw reasoning traces"),
    (COLS[2], ROW1, "STEP 3 · Wrong-trace bank",
     "Keep rollouts whose final answer\nwas WRONG → the wrong reasoning\nwe inject. Also keep correct traces\n(to corrupt) and other questions'\ntraces (as irrelevant donors)"),
    (COLS[0], ROW2, "STEP 4 · Inject wrong reasoning",
     "Splice a wrong trace into a fresh\nprompt's think block. Vary: amount\n(25→100%), kind of wrongness, and\nwhether thinking may CONTINUE\nor the answer is FORCED"),
    (COLS[1], ROW2, "STEP 5 · Re-generate",
     "16 new samples per question ×\ncondition — the model picks up\nmid-thought from the injected\nwrong reasoning"),
    (COLS[2], ROW2, "STEP 6 · Grade & measure",
     "Grade ONLY newly generated tokens\n(math_verify / task verifiers) →\npass@k, adoption rate (echoed the\ntrace's answer?), token-level audit\nof what the model did next"),
]
for x0, y0, title, body in steps:
    ax.add_patch(FancyBboxPatch((x0, y0), W, H, boxstyle="round,pad=0.7",
                                fc="#cde2fb", ec=BLUE, lw=1.3))
    ax.text(x0 + W / 2, y0 + H - 3.2, title, ha="center", va="center",
            fontsize=10.5, color=INK, fontweight="bold")
    ax.text(x0 + W / 2, y0 + (H - 5.5) / 2 - 0.8, body, ha="center", va="center",
            fontsize=9.2, color=SEC, linespacing=1.45)

arrow = dict(arrowstyle="-|>", mutation_scale=16, color=SEC, lw=1.6)
mid1 = ROW1 + H / 2
mid2 = ROW2 + H / 2
ax.add_patch(FancyArrowPatch((COLS[0] + W + 0.9, mid1), (COLS[1] - 0.9, mid1), **arrow))
ax.add_patch(FancyArrowPatch((COLS[1] + W + 0.9, mid1), (COLS[2] - 0.9, mid1), **arrow))
ax.add_patch(FancyArrowPatch((COLS[2] + W / 2, ROW1 - 1.2), (COLS[0] + W / 2, ROW2 + H + 1.2),
                             connectionstyle="arc3,rad=-0.06", **arrow))
ax.add_patch(FancyArrowPatch((COLS[0] + W + 0.9, mid2), (COLS[1] - 0.9, mid2), **arrow))
ax.add_patch(FancyArrowPatch((COLS[1] + W + 0.9, mid2), (COLS[2] - 0.9, mid2), **arrow))

ax.set_title("Pipeline: inject wrong reasoning into the think block, measure recovery with pass@k",
             fontsize=13.5, color=INK, pad=12)
fig.text(0.5, -0.02,
         "Design guarantees: injected text is never graded (only what the model newly generates) · cross-source comparisons use matched question subsets ·\n"
         "high truncation triggers a budget-doubling validity check. ~75k rollouts total: Qwen3-4B-Thinking / -Instruct (matched pair) + Gemma-4-E2B, 2× H100.",
         ha="center", fontsize=9.5, color=MUTED)
fig.tight_layout()
fig.savefig(f"{FIGDIR}/fig0_pipeline.png", dpi=180, bbox_inches="tight")
plt.close(fig)

print("wrote 5 figures to", FIGDIR)
