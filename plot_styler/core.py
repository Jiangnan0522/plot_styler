"""Activate conference-specific matplotlib styles and compute figure sizes.

Typical usage:

    import plot_styler as ps

    ps.use("acl", palette="muted")
    fig, ax = plt.subplots(figsize=ps.figsize("acl", "column"))

    # Two subfigures side-by-side in a single ACL column:
    fig, ax = plt.subplots(figsize=ps.figsize("acl", "column", fraction=0.5))

    # Switch palette mid-script — only affects plots created afterwards:
    ps.set_palette("colorblind_safe")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
from cycler import cycler

_PACKAGE_ROOT = Path(__file__).resolve().parent
_STYLES_DIR = _PACKAGE_ROOT / "styles"
_WIDTHS_PATH = _PACKAGE_ROOT / "widths.json"
_PALETTES_PATH = _PACKAGE_ROOT / "palettes.json"

GOLDEN = (1 + 5 ** 0.5) / 2  # 1.618…

# Which style sheet to load for each conference name.
_CONFERENCE_TO_STYLE = {
    "acl":     "acl",
    "emnlp":   "acl",
    "naacl":   "acl",
    "neurips": "neurips",
    "iclr":    "neurips",
    "icml":    "neurips",
}


def load_widths() -> dict:
    with open(_WIDTHS_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_palettes() -> dict:
    with open(_PALETTES_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


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


def use(conference: str, palette: str = "default") -> None:
    """Apply base style + the given conference's overrides + a palette."""
    key = conference.lower()
    if key not in _CONFERENCE_TO_STYLE:
        raise KeyError(
            f"Unknown conference '{conference}'. "
            f"Known: {sorted(_CONFERENCE_TO_STYLE)}"
        )
    base = _STYLES_DIR / "base.mplstyle"
    conf = _STYLES_DIR / f"{_CONFERENCE_TO_STYLE[key]}.mplstyle"
    plt.style.use([str(base), str(conf)])
    set_palette(palette)


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
