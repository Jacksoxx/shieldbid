# -*- coding: utf-8 -*-
# Shared card kit: dark palette, pixel fonts, and text that always fits its box.
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from matplotlib.patches import FancyBboxPatch, Rectangle

BG, BOX, EDGE = "#0b0f14", "#141c26", "#2b3a4a"
TXT, DIM, GOOD, WARN, BAD, ACC = "#e6edf3", "#8b98a5", "#3fb950", "#d29922", "#f85149", "#4ea1ff"

FONTDIR = Path(__file__).resolve().parent / "fonts"
HEAD, TEXT = "Silkscreen", "VT323"
WARNINGS: list[str] = []


def use_fonts() -> None:
    for f in FONTDIR.glob("*.ttf"):
        fm.fontManager.addfont(str(f))


def use_dark(w: float = 10.0, h: float = 5.6, xlim: float = 100.0, dpi: int = 150):
    """Figure + axes in the ShieldBid dark palette; y goes 0..h/w*xlim by default."""
    use_fonts()
    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, xlim)
    ax.set_ylim(0, h / w * xlim)
    ax.axis("off")
    return fig, ax


def _px_per_unit(ax) -> tuple:
    x0 = ax.transData.transform((0, 0))
    x1 = ax.transData.transform((1, 1))
    return (x1[0] - x0[0]), (x1[1] - x0[1])


def units_per_pt(ax) -> float:
    _, ppu = _px_per_unit(ax)
    return (ax.figure.dpi / 72.0) / ppu


def text_width(ax, s: str, size: float, head: bool = False, weight: str = "normal") -> float:
    """Width of s in axis units, measured from the font outlines (no renderer needed,
    so the value is stable no matter when it is called).  The outline measurement comes
    out ~1/1.3 of the advance the renderer really uses (side bearings, hinting), so the
    factor below keeps every shrink/wrap decision on the safe side."""
    fp = FontProperties(family=HEAD if head else TEXT, size=size, weight=weight)
    pts = TextPath((0, 0), s, prop=fp).get_extents().width
    fig_w_in = ax.figure.get_size_inches()[0]
    x0, x1 = ax.get_xlim()
    in_per_unit = fig_w_in / (x1 - x0)
    return (pts / 72.0) / in_per_unit * 1.33


def T(ax, x, y, s, color=TXT, size=13, weight="normal", ha="left", head=False, alpha=1.0, va="baseline"):
    return ax.text(x, y, s, color=color, fontsize=size, weight=weight, ha=ha, va=va,
                   family=HEAD if head else TEXT, alpha=alpha)


def fit(ax, x, y, s, w, color=TXT, size=14, weight="normal", head=False, ha="left",
        min_size=8.0, wrap=2, lead=1.45, check=True):
    """Draw s inside the box [x, x+w]: shrink to fit, wrap if shrinking is not enough."""
    lines, used = [s], float(size)
    for _ in range(48):                               # measure -> shrink -> re-measure
        widest = max(text_width(ax, ln, used, head, weight) for ln in lines)
        if widest <= w:
            break
        if used > min_size:
            used = max(min_size, round(used * w / widest * 0.98 * 2) / 2)
        elif wrap > 1 and len(lines) == 1 and " " in s:
            lines = _wrap(ax, s, w, used, head, weight, wrap)
        else:
            break
    if check and max(text_width(ax, ln, used, head, weight) for ln in lines) > w:
        WARNINGS.append(f"overflow: {lines[0][:40]!r} in {w:.1f}u @{used:g}pt")
    yy = y
    for i, ln in enumerate(lines):
        ax.text(x, yy, ln, color=color, fontsize=used, weight=weight, ha=ha,
                family=HEAD if head else TEXT)
        yy -= used * units_per_pt(ax) * lead
    return used


def _wrap(ax, s, w, size, head, weight, max_lines):
    words = s.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if cur and text_width(ax, trial, size, head, weight) > w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def box(ax, x, y, w, h, edge=EDGE, fill=BOX, round_=0.0, lw=1.0):
    if round_:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={round_}",
                                    linewidth=lw, edgecolor=edge, facecolor=fill))
    else:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=edge, lw=lw))


def panel(ax, x, y, w, h, title=None, edge=EDGE, fill=BOX, tcolor=DIM, head=True, round_=0.0):
    box(ax, x, y, w, h, edge=edge, fill=fill, round_=round_)
    if title:
        fit(ax, x + 2.5, y + h - 2.4, title, w - 5, color=tcolor, size=12, head=head)


def report() -> str:
    return "ok" if not WARNINGS else "; ".join(WARNINGS)
