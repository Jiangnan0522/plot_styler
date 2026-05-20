# The alpha channel and `mcolors.to_rgba(c, 0.55)`

Captured from a conversation while styling a grouped-bar figure for the
CompressIn paper. The plot used the `plot_styler` "warm" palette and wanted
bars with a translucent fill and a crisp, darker outline — the same pattern
that `plot_evidence2_swd.py` ships with. Two questions came up; the answers
are below.

---

## Q1 — Why does `mcolors.to_rgba(c, 0.55)` give us a translucent fill?

**Short answer.** `to_rgba(c, 0.55)` turns the color `c` into an
`(r, g, b, 0.55)` tuple, and matplotlib uses that alpha value to blend the
bar's fill with the background during rendering. The edge is passed a
separate fully-opaque color, so only the fill appears translucent.

In more detail:

1. Matplotlib represents every color as an **RGBA** tuple: three channels for
   red/green/blue plus a fourth **alpha** channel for opacity. Alpha ranges
   from `0` (fully transparent) to `1` (fully opaque). A bare hex string
   like `"#f2dbc3"` is implicitly `(r, g, b, 1.0)` — fully opaque.

2. `mcolors.to_rgba(c, 0.55)` does two things at once:
   - Normalizes whatever form `c` is in (hex, named color, `(r,g,b)` tuple)
     into a 4-tuple.
   - *Overrides* the alpha channel to `0.55`.
   The returned value is `(r, g, b, 0.55)`.

3. When that tuple is handed to `facecolor=`, matplotlib's renderer performs
   **alpha compositing** against whatever is already drawn behind the bar
   (the white axes background, gridlines, other bars). The final pixel color
   is the linear blend `0.55 * bar + 0.45 * background`. That blend is what
   you perceive as "translucent."

4. The edge is drawn separately using `edgecolor=`, and because we pass a
   plain RGB tuple there (no alpha override), the outline stays at alpha=1 —
   fully opaque. That asymmetry creates the "crisp outline, soft fill" look.

### Why not just use `ax.bar(..., alpha=0.55)`?

`alpha=0.55` at the artist level applies to the **entire artist** — fill,
edge, and any hatching — so the outline would become translucent too and
blur the bar boundary. `facecolor=to_rgba(c, 0.55)` is the surgical form:
it softens only the fill while leaving the edge crisp.

### Example

```python
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import plot_styler as ps

ps.use("icml", "warm")
warm = ps.load_palettes()["warm"]
c = warm[1]

fig, ax = plt.subplots(figsize=ps.figsize("icml", "column"))
ax.bar(
    [0, 1, 2], [3, 5, 4],
    facecolor=mcolors.to_rgba(c, 0.55),  # translucent fill
    edgecolor=c,                         # opaque outline, same hue
    linewidth=0.9,
)
```

---

## Q2 — What is the alpha channel?

The **alpha channel** is the fourth number in an RGBA color tuple, sitting
alongside red, green, and blue. Where R/G/B say *what color* a pixel is,
alpha says *how much of that color actually lands* on the canvas when it's
drawn. It's a scalar in `[0, 1]`:

- `0` — contributes nothing (fully transparent).
- `1` — fully replaces whatever was underneath (fully opaque).
- Anything in between — partial blending.

### The "over" compositing formula

Mechanically, when a 2D renderer draws a shape with alpha `a` on top of an
existing pixel with background color `B`, the output pixel is:

```
out = a * fg + (1 - a) * B
```

So at `alpha=0.55`, each pixel of the bar keeps 55% of its own color and
lets 45% of the background show through — that's the visual sense of
"translucent."

### Alpha is metadata, not pigment

Alpha is not a physical property of the color; it's metadata that tells the
renderer *how to combine* this color with others. Two bars with the same RGB
but different alphas look different only because of what they're sitting on
top of. If you exported the figure onto a transparent PNG background, an
`alpha=0.55` bar would still look like a 55%-strength bar — but blended
against nothing, the translucency would manifest as the bar looking
washed-out rather than showing another element through it.

### Practical matplotlib notes

- **Three ways to override alpha:**
  1. Pass a 4-tuple directly: `facecolor=(r, g, b, 0.55)`.
  2. Wrap an RGB color: `mcolors.to_rgba(c, 0.55)`.
  3. Set the artist-wide kwarg: `ax.bar(..., alpha=0.55)`.
  The first two are surgical (one channel only); the third applies to every
  visual element of the artist.

- **Export side-effect.** `alpha < 1` silently disables some rasterization
  optimizations and, for PDF/SVG output, forces matplotlib to emit
  transparency groups. Usually invisible in quality, but worth knowing if a
  reviewer complains about file size.

- **Overlap stacking.** Overlapping translucent bars *stack*. Two
  `alpha=0.55` bars on top of each other produce an effective opacity of
  `1 - (1 - 0.55)^2 ≈ 0.80`. That's why grouped bars are typically placed
  side-by-side rather than overlapping — overlap would muddy the color
  encoding.

---

## See also

- `plot_styler/plot_evidence2_swd.py` (in the CompressIn repo) — the original
  use of the translucent-fill / darker-edge pattern described here.
- Matplotlib docs: *Specifying colors* and *Colormap normalization*.
