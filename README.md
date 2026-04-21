# plot_styler

Reusable matplotlib styling for NLP / ML conference papers (ACL, EMNLP, NAACL,
NeurIPS, ICLR, ICML). One `pip install -e .`, one `import plot_styler`, and
figures come out at the right width with the right font size for the target
template — no per-project copy-pasting of rc settings.

## Install

```bash
pip install -e /users/k21025815/storage/misc/plot_styler
```

Editable install is recommended: edits to `widths.json` and `.mplstyle` files
take effect immediately across every project that imports the package.

## Usage

```python
import matplotlib.pyplot as plt
import plot_styler as ps

ps.use("acl")                                         # activates base + acl style
fig, ax = plt.subplots(figsize=ps.figsize("acl", "column"))
ax.plot(...)
fig.savefig("myplot.pdf")                             # pdf is the default savefig format
```

More sizing cases:

```python
# Two subfigures side-by-side inside one ACL column:
ps.figsize("acl", "column", fraction=0.5)

# Full text width (spans both columns) in ACL:
ps.figsize("acl", "text")

# Default NeurIPS figure (single-column templates only have "text"):
ps.figsize("neurips", "text")

# Three subfigures across NeurIPS text width, custom aspect ratio:
ps.figsize("neurips", "text", fraction=1/3, aspect=0.8)
```

Conference aliases: `emnlp`, `naacl` → ACL style; `iclr`, `icml` → NeurIPS style.

See `examples/demo.py` for a runnable end-to-end example.

## Design logic

The library rests on one principle and three consequences.

### The principle: never let LaTeX scale the figure

Produce every figure at the exact width it will occupy in the final PDF, and
include it without scaling (`\includegraphics{fig.pdf}` or `[width=\columnwidth]`
at the figure's natural width). This is what keeps font sizes in figures
matching the paper's body typography, line widths crisp, and PDFs small.

### Consequence 1: the conference, not the author, sets font size

Font size inside a figure is anchored to the paper's body font. That's 11pt for
ACL/EMNLP/NAACL, 10pt for NeurIPS/ICLR/ICML. Everything in figures (ticks,
labels, legend) is then scaled around that anchor — typically 1–2pt below body.
These values live in `styles/acl.mplstyle` and `styles/neurips.mplstyle`.

### Consequence 2: concatenation changes width, not font

When you put two figures side-by-side in LaTeX, each one is narrower, but the
paper's body font is still 10 or 11pt — so the figure font must not change
either. Halving the width must *not* halve `font.size`. This is why the library
has a single style sheet per conference and only the `figsize()` helper varies
per figure. There is no `acl-halfcolumn.mplstyle` and should not be one.

### Consequence 3: widths must come from the actual template

The widths in `widths.json` are starting estimates. For camera-ready work you
should measure the real values from the template you're submitting to and
edit `widths.json` in place (no reinstall needed thanks to `pip install -e`).

See **[`doc/measuring-latex-templates.md`](doc/measuring-latex-templates.md)**
for the full procedure: how to extract body font size, `\columnwidth`, and
`\textwidth`, including the correct pt → inch conversion (72.27, not 72) and
the common pitfalls around context-dependent lengths.

## What the style sheets actually set

`base.mplstyle` — universal across all conferences:

- Sans-serif font family (Helvetica → Arial → DejaVu Sans fallback) so figures
  contrast with the serif body text.
- STIX math font (`mathtext.fontset: stix`) — Times-compatible so `$\alpha$` in
  a figure blends with `$\alpha$` in body text.
- `pdf.fonttype: 42` / `ps.fonttype: 42` — embeds TrueType fonts. This is
  critical: arXiv and IEEE Xplore reject PDFs with Type 3 fonts, and many
  viewers can't select text in them.
- Colorblind-ish palette: `#30A9DE #E53A40 #090707 #EFDC05` (placeholder, tune
  later).
- Spines (top/right off), light grid, sensible line/marker widths, no legend
  frame, `constrained_layout` on.
- `savefig.format: pdf`, `savefig.bbox: tight`.

`acl.mplstyle` — for 11pt body templates: `font.size: 9`, ticks/legend at 8.

`neurips.mplstyle` — for 10pt body templates: `font.size: 8`, ticks/legend at 7.

## Layout

```
plot_styler/
├── pyproject.toml
├── plot_styler/
│   ├── __init__.py          # exposes use, figsize, load_widths, GOLDEN
│   ├── core.py              # the API
│   ├── widths.json          # per-conference widths in inches — edit freely
│   └── styles/
│       ├── base.mplstyle
│       ├── acl.mplstyle
│       └── neurips.mplstyle
└── examples/
    └── demo.py              # renders five sample PDFs
```

## API

| Function | Purpose |
|---|---|
| `ps.use(conference)` | Load base + conference style. |
| `ps.figsize(conference, region, fraction=1.0, aspect=1/GOLDEN, gutter=0.1)` | Compute `(w, h)` in inches. `region` is a key in `widths.json` (usually `"column"` or `"text"`). `fraction` is the width share for side-by-side subfigures. `gutter` is the inches of horizontal gap between them. |
| `ps.load_widths()` | Return the widths dict, e.g. for custom calculations. |
| `ps.GOLDEN` | `(1 + √5) / 2`, used as the default aspect. |

## Extending to a new conference

1. Measure widths from the template — see
   [`doc/measuring-latex-templates.md`](doc/measuring-latex-templates.md).
2. Add a new entry to `widths.json`:
   ```json
   "mynewconf": { "text": 6.00 }
   ```
3. If the body font matches ACL (11pt) or NeurIPS (10pt), add an alias in
   `plot_styler/core.py` → `_CONFERENCE_TO_STYLE`.
4. Otherwise add a new `styles/mynewconf.mplstyle` that sets `font.size` and
   related size fields to match the new body font, and register it.
