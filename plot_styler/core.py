"""Activate conference-specific matplotlib styles and compute figure sizes.

Typical usage:

    import plot_styler as ps

    ps.use("acl", palette="muted")
    fig, ax = plt.subplots(figsize=ps.figsize("acl", "column"))

    # Two subfigures side-by-side in a single ACL column:
    fig, ax = plt.subplots(figsize=ps.figsize("acl", "column", fraction=0.5))

    # Pre-tuned typography for shrunken figures (~1/3 or ~1/4 of column/text):
    ps.use("acl", palette="muted", size="small")
    ps.use("icml", palette="warm", size="tiny")

    # Switch palette mid-script — only affects plots created afterwards:
    ps.set_palette("colorblind_safe")
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
from cycler import cycler

_PACKAGE_ROOT = Path(__file__).resolve().parent
_STYLES_DIR = _PACKAGE_ROOT / "styles"
_WIDTHS_PATH = _PACKAGE_ROOT / "widths.json"
_PALETTES_DIR = _PACKAGE_ROOT / "palettes"
# Accept #RRGGBB or #RRGGBBAA. The optional alpha group is greedy, so an
# 8-char hex like #f2dbc3ff matches in full rather than being clipped to 6.
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?\b")

GOLDEN = (1 + 5 ** 0.5) / 2  # 1.618…

# Which style sheet to load for each conference name.
_CONFERENCE_TO_STYLE = {
    "acl":     "acl",
    "emnlp":   "acl",
    "naacl":   "acl",
    "neurips": "neurips",
    "iclr":    "neurips",
    "icml":    "icml",
}

# Size variants that can be layered on top of the conference sheet.
# `normal` loads only the conference sheet; the others additionally load
# `<stem>-<size>.mplstyle` from styles/, which carries reduced font sizes
# and lighter strokes for figures that occupy ~1/3 (small) or ~1/4 (tiny)
# of a column or text width.
_VALID_SIZES = ("normal", "small", "tiny")


def load_widths() -> dict:
    with open(_WIDTHS_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_palettes() -> dict:
    """Scan palettes/ for .txt files; return {stem: [hex, ...]}.

    Each file contributes one palette, named after its filename stem.
    Hex values are extracted in file order via a regex, so lines like
    `# my comment` are ignored unless they contain a valid #RRGGBB.
    """
    palettes = {}
    for path in sorted(_PALETTES_DIR.glob("*.txt")):
        colors = _HEX_RE.findall(path.read_text())
        if colors:
            palettes[path.stem] = colors
    return palettes


def set_palette(name: str) -> List[str]:
    """Change matplotlib's color cycle to the named palette.

    Only affects plots created after this call — existing Axes keep their
    assigned colors. Returns the list of hex colors now in the cycle.
    """
    palettes = load_palettes()
    if name not in palettes:
        raise KeyError(
            f"Unknown palette '{name}'. Known: {sorted(palettes)}"
        )
    colors = palettes[name]
    plt.rcParams["axes.prop_cycle"] = cycler(color=colors)
    return colors


def use(
    conference: str, palette: str = "default", size: str = "normal"
) -> None:
    """Apply base style + the given conference's overrides + a palette.

    `size` selects an optional pre-tuned variant for shrunken figures:
    "small" (~1/3 of column/text) or "tiny" (~1/4). The variant sheet is
    layered on top of the conference sheet, so it only needs to carry deltas.
    """
    key = conference.lower()
    if key not in _CONFERENCE_TO_STYLE:
        raise KeyError(
            f"Unknown conference '{conference}'. "
            f"Known: {sorted(_CONFERENCE_TO_STYLE)}"
        )
    if size not in _VALID_SIZES:
        raise ValueError(
            f"Unknown size '{size}'. Known: {_VALID_SIZES}"
        )
    base = _STYLES_DIR / "base.mplstyle"
    conf_stem = _CONFERENCE_TO_STYLE[key]
    sheets = [str(base), str(_STYLES_DIR / f"{conf_stem}.mplstyle")]
    if size != "normal":
        variant = _STYLES_DIR / f"{conf_stem}-{size}.mplstyle"
        if not variant.exists():
            raise FileNotFoundError(
                f"Missing size sheet for {conf_stem}/{size}: {variant}"
            )
        sheets.append(str(variant))
    plt.style.use(sheets)
    set_palette(palette)


# ---------------------------------------------------------------------------
# Textbox styles for in-plot stats annotations
# ---------------------------------------------------------------------------
#
# Each style is a subclass of TextBoxStyle that defines a `_BBOX` class
# attribute — the dict of kwargs passed to ax.text(..., bbox=...).
# The `textbox()` factory below looks up a style by name in _TEXTBOX_STYLES
# and returns a fresh dict (so callers can mutate without affecting others).
#
# To add a style: subclass TextBoxStyle with a new `_BBOX`, then register
# it in _TEXTBOX_STYLES. No other changes needed.


class TextBoxStyle:
    """Base class for textbox styles.

    Subclasses override the ``_BBOX`` class attribute with a dict of kwargs
    to pass to ``ax.text(..., bbox=...)``. Instances are never created — the
    style itself is a singleton, encoded as class-level state.
    """

    _BBOX: dict = {}

    @classmethod
    def build(cls, **overrides) -> dict:
        """Return a fresh bbox dict, with kwargs overriding class defaults."""
        return {**cls._BBOX, **overrides}


class RoundTextBox(TextBoxStyle):
    """Rounded, semi-transparent white box with a grey border.

    The classic stats-annotation style — readable without overpowering plot
    content. Use as the default unless the figure has a strong reason to
    differ.
    """

    _BBOX = {
        "boxstyle": "round,pad=0.3",
        "facecolor": "white",
        "edgecolor": "grey",
        "alpha": 0.75,
    }


class SquareTextBox(TextBoxStyle):
    """Sharp-cornered counterpart to ``RoundTextBox``.

    Use when the figure's visual language already favors right angles
    (heatmaps, contingency tables, lattice plots).
    """

    _BBOX = {
        "boxstyle": "square,pad=0.3",
        "facecolor": "white",
        "edgecolor": "grey",
        "alpha": 0.75,
    }


class MinimalTextBox(TextBoxStyle):
    """Borderless, faint white backdrop — visible only as a soft wash.

    Use when the annotation must not visually compete with dense plot
    content (small multiples, overlaid time series). The reduced ``alpha``
    and absent edge keep the box from reading as a foreground element.
    """

    _BBOX = {
        "boxstyle": "round,pad=0.2",
        "facecolor": "white",
        "edgecolor": "none",
        "alpha": 0.5,
    }


_TEXTBOX_STYLES: dict = {
    "round": RoundTextBox,
    "square": SquareTextBox,
    "minimal": MinimalTextBox,
}


def textbox(style: str = "round", **overrides) -> dict:
    """Return a bbox dict for ``ax.text(..., bbox=...)`` annotations.

    A factory that dispatches to one of the registered ``TextBoxStyle``
    subclasses. A fresh dict is returned on each call, so callers may
    mutate the result freely.

    Args:
        style: registered style name. Built-in: ``"round"`` (default),
               ``"square"``, ``"minimal"``. To add a style, subclass
               ``TextBoxStyle`` and register it in ``_TEXTBOX_STYLES``.
        **overrides: per-call overrides (e.g. ``alpha=0.9``,
                     ``edgecolor="black"``, or any ``FancyBboxPatch`` kwarg).

    Example::

        ax.text(0.97, 0.97, "p < 1e-4", transform=ax.transAxes,
                ha="right", va="top", bbox=ps.textbox())
        ax.text(..., bbox=ps.textbox("square", alpha=0.9))
        ax.text(..., bbox=ps.textbox("minimal"))
    """
    if style not in _TEXTBOX_STYLES:
        raise KeyError(
            f"Unknown textbox style '{style}'. "
            f"Known: {sorted(_TEXTBOX_STYLES)}"
        )
    return _TEXTBOX_STYLES[style].build(**overrides)


def figsize(
    conference: str,
    region: str = "text",
    fraction: float = 1.0,
    aspect: float = 1 / GOLDEN,
    gutter: float = 0.1,
) -> Tuple[float, float]:
    """Return (width, height) in inches for a figure in `conference`.

    Args:
        conference: key from widths.json (e.g. "acl", "neurips").
        region:     "column" or "text" — which width from widths.json to use.
        fraction:   width fraction of that region. For two side-by-side
                    subfigures use fraction=0.5; for three use 1/3.
        aspect:     height/width ratio. Defaults to 1/golden ratio.
        gutter:     horizontal gap (inches) between side-by-side subfigures.
                    Subtracted proportionally from the total width.
    """
    key = conference.lower()
    widths = load_widths()
    if key not in widths:
        raise KeyError(f"Unknown conference '{conference}'. Known: {sorted(widths)}")
    if region not in widths[key]:
        raise KeyError(
            f"Region '{region}' not set for '{conference}'. "
            f"Available: {sorted(widths[key])}"
        )
    if not 0 < fraction <= 1:
        raise ValueError(f"fraction must be in (0, 1], got {fraction}")

    total = widths[key][region]
    n_subfigs = 1.0 / fraction
    usable = total - gutter * (n_subfigs - 1)
    w = usable * fraction
    return (w, w * aspect)
