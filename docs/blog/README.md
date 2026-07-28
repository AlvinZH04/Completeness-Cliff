# Blog post: "The completeness cliff"

Public write-up of pilot 1, for a general technical audience.

| file | what it is |
|---|---|
| `cliff_template.html` | **Source of truth for the prose.** Self-contained HTML (CSS inline) with `__FIG0__` .. `__FIG4__` placeholders where the figures go. Edit this. |
| `completeness-cliff.html` | **Built page.** The template with all five figures inlined as base64, so it ships as one static file with no external assets. Generated, do not hand-edit. |
| `x_post_drafts.txt` | X/Twitter drafts (one thread, three single-post options), each verified at or under 280 characters. |

## Rebuild after editing

```bash
python scripts/make_figures_blog.py     # regenerate docs/figures_blog/*.png (only if figures changed)
python scripts/build_blog_post.py       # inline figures -> completeness-cliff.html
```

The build script warns if an em-dash slips into the built page (house style avoids them).

## Publish

Copy the built file into the homepage repo (`AlvinZH04/AlvinZH04.github.io`) and push:

```bash
cp docs/blog/completeness-cliff.html <homepage>/blog/completeness-cliff.html
```

The homepage `index.html` links it from both the News and Blog sections. Live URL once
pushed: https://alvinzh04.github.io/blog/completeness-cliff.html
(the X drafts link there, so post only after the page is live).

## Content notes

- Figures come from `scripts/make_figures_blog.py` (Times New Roman via the bundled Tinos
  face, larger type, black value labels). The mentor-facing variants in `docs/figures/` bake
  their explanations into the image; the blog versions stay clean and let the
  `<figcaption>` carry the detail.
- Numbers trace back to `docs/findings.md` and `docs/report_pilot1.md`, which cite the exact
  runs in `results/*/summary.json`.
- Related work for the claims is in `literature_review/related_work_grounding.md`.
