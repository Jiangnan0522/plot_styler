"""Render sample figures for each conference style to verify the library."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plot_styler as ps

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

x = np.linspace(0, 2 * np.pi, 200)


def sample_plot(ax):
    for k, label in enumerate([r"$\sin x$", r"$\cos x$", r"$\sin 2x$", r"$\cos 2x$"]):
        ax.plot(x, np.sin((k + 1) * x + k * 0.3), label=label)
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$f(x)$")
    ax.legend(ncols=2)


def render(conference, region, fraction, fname):
    ps.use(conference)
    fig, ax = plt.subplots(figsize=ps.figsize(conference, region, fraction=fraction))
    sample_plot(ax)
    fig.savefig(OUT / fname)
    plt.close(fig)


if __name__ == "__main__":
    render("acl",     "column", 1.0, "acl_column.pdf")
    render("acl",     "column", 0.5, "acl_halfcolumn.pdf")
    render("acl",     "text",   1.0, "acl_text.pdf")
    render("neurips", "text",   1.0, "neurips_full.pdf")
    render("neurips", "text",   0.5, "neurips_half.pdf")
    print(f"Wrote {len(list(OUT.glob('*.pdf')))} PDFs to {OUT}")
