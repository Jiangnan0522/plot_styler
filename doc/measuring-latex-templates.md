# Measuring widths and font sizes from a LaTeX template

You need three numbers per conference to populate `plot_styler`:

1. **Body font size**, in pt — decides which `.mplstyle` to use (or whether to
   add a new one).
2. **`\columnwidth`**, in pt → inches — the width a single-column figure
   occupies. Only relevant for two-column templates (ACL, EMNLP, NAACL).
3. **`\textwidth`**, in pt → inches — the width a full-width figure occupies
   (single-column templates, or a `figure*` spanning both columns in a
   two-column template).

This doc covers how to extract each one reliably, and the conversion to
inches that `widths.json` expects.

---

## Prerequisites

- A compilable `.tex` file using the conference template (even an empty one
  with just `\documentclass{…}` and `\begin{document}…\end{document}` works).
- `pdflatex` or `latexmk` available.

All commands below go into the `.tex` source; you read the answer from the
compilation log (stdout or the `.log` file).

---

## Step 1 — Body font size

The body font size determines which mplstyle to use:

- 11pt body → use `acl.mplstyle`
- 10pt body → use `neurips.mplstyle`
- Anything else → make a new style sheet

### Quickest: check the documentclass

Open the conference's main `.tex` (often named e.g. `acl.tex`, `neurips.tex`)
and look at its `\documentclass` line:

```latex
\documentclass[11pt,a4paper]{article}     % → 11pt body
\documentclass{article}                   % → 10pt body (article default)
```

If the conference ships a `.cls` file (e.g. `acl.cls`) instead of a `.sty`,
grep it for the `\LoadClass[…]{article}` line — the option list there is
authoritative.

### Robust: ask LaTeX directly

If you're not sure whether the style file overrides the class's default,
add this inside `\begin{document}` and recompile:

```latex
\makeatletter
\typeout{=== body font size = \f@size pt ===}
\makeatother
```

The log line `=== body font size = 11.0 pt ===` (or similar) is the real
current font size at that point in the document.

---

## Step 2 — Column and text widths

Add the following after `\begin{document}` (and, if the template uses
`\maketitle` or `\twocolumn` there, *after* those — widths can change):

```latex
\typeout{==== columnwidth = \the\columnwidth ====}
\typeout{==== textwidth   = \the\textwidth   ====}
```

Recompile and read the log:

```
==== columnwidth = 241.14749pt ====
==== textwidth   = 469.75499pt ====
```

These numbers are in `pt` (LaTeX points, not PostScript points).

> **Alternative, interactive**: `\showthe\columnwidth` prints the value and
> stops compilation at a `?` prompt. Press Enter to continue. Use `\typeout`
> for non-interactive / batch runs; use `\showthe` for a quick one-off peek.

### Where to put the `\typeout` lines matters

`\columnwidth` is a *context-dependent* length:

| Context | Value of `\columnwidth` |
|---|---|
| Two-column document body | half text width (minus gutter) |
| Inside `figure*` (two-col doc) | equals `\textwidth` |
| Inside a `minipage{\somewidth}` | equals `\somewidth` |
| Single-column document body | equals `\textwidth` |

Measure in the same context you plan to place your figure. For the two values
`plot_styler` stores (`column` and `text`), measure both in the document body
*outside* any `figure*` or `minipage` — that gives the values you'll pass to
`\includegraphics[width=\columnwidth]` and `\includegraphics[width=\textwidth]`
respectively.

---

## Step 3 — Convert pt to inches

LaTeX points are **not** PostScript/DTP points. The conversion is:

```
1 inch = 72.27 pt     (LaTeX / TeX pt)
1 inch = 72.00 pt     (PostScript / Adobe pt — NOT what LaTeX uses)
```

So:

```
inches = pt_value / 72.27
```

Examples:

- `241.14749 pt / 72.27 ≈ 3.3366 in` → round to `3.34`
- `469.75499 pt / 72.27 ≈ 6.5006 in` → round to `6.50`

Two decimal places is sufficient — the last one is within `0.01 in ≈ 0.7 pt`,
well below what's visible.

---

## Step 4 — Update `widths.json`

Open `plot_styler/widths.json` and edit the conference entry in place:

```json
{
  "acl": { "column": 3.17, "text": 6.30 }
}
```

Because the library is installed editable, the new numbers take effect on the
next `import plot_styler` — no reinstall needed.

If the conference has a **different body font** from any existing
mplstyle, also:

1. Add `plot_styler/styles/<conference>.mplstyle` with the appropriate
   `font.size`, `axes.labelsize`, `xtick.labelsize`, etc.
2. Register it in `plot_styler/core.py` → `_CONFERENCE_TO_STYLE`.

---

## Conference cheat sheet

These are the values the library currently ships with. They are standard
defaults for the *official* style files; double-check against the specific
year's release if you care about the last decimal place.

| Conference | Columns | Body | `\columnwidth` | `\textwidth` |
|---|---|---|---|---|
| ACL / EMNLP / NAACL | 2 | 11 pt | ~241 pt (3.17 in) | ~468 pt (6.30 in) |
| NeurIPS            | 1 | 10 pt | = textwidth       | ~397 pt (5.50 in) |
| ICLR               | 1 | 10 pt | = textwidth       | ~397 pt (5.50 in) |
| ICML (2026)        | 2 | 10 pt | ~235 pt (3.25 in) | ~488 pt (6.75 in) |

---

## Common pitfalls

- **Wrong unit**. Dividing by 72 instead of 72.27 gives a figure ~0.4% too
  small. Usually invisible but can shift a tight layout just enough for text
  to run past the edge. Use 72.27.
- **Measuring before `\twocolumn`**. In `article` with a conference style that
  switches to two-column mode inside `\maketitle`, measuring in the preamble
  or before the title gives the single-column value. Always measure after the
  title.
- **Confusing `\linewidth` and `\columnwidth`**. `\linewidth` is the current
  line width, which in lists, quotes, or minipages is smaller than
  `\columnwidth`. For top-level figures they're equal; if in doubt, use
  `\columnwidth`.
- **Trusting rounded values from a paper's README**. Many conference READMEs
  quote "single-column width: 3.25 in" rounded. For camera-ready work,
  measure the actual year's template.
- **Caching old values**. If you edit `widths.json` while a Python process
  is already running (e.g., in a Jupyter kernel), `load_widths()` is called
  each time `figsize()` runs so it picks up the new values — but if you
  stored `ps.figsize(...)` output in a variable, that variable is stale.
  Re-call `figsize()` after the edit.
