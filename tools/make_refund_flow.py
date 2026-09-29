# -*- coding: utf-8 -*-
# One-page visual: where the demo ZEC goes, and how it comes back (English).
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cardkit as C
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "docs" / "refund_flow.png"

fig, ax = C.use_dark(w=11.0, h=6.2, xlim=100)

C.fit(ax, 2, 57.0, "Where the ZEC goes (DEMO-01, end to end)", 60, size=22, head=True, color=C.TXT)
C.fit(ax, 2, 52.4, "Nothing is spent: the ZEC moves into the auction wallet and comes back the same way.",
      92, size=18, color=C.DIM)


def box(x, y, w, h, title, lines, edge=C.EDGE, tcolor=C.TXT):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=1.6",
                                linewidth=1.4, edgecolor=edge, facecolor=C.BOX))
    C.fit(ax, x + w / 2, y + h - 3.2, title, w - 2.2, size=13, head=True, color=tcolor, ha="center")
    for i, ln in enumerate(lines):
        C.fit(ax, x + w / 2, y + h - 7.0 - i * 3.6, ln, w - 2, size=16, color=C.DIM, ha="center")


box(2.5, 33, 22, 15, "1. bidder wallet",
    ["sends one shielded transfer", "the amount IS the bid"], edge=C.ACC, tcolor=C.ACC)
box(27, 33, 22, 15, "2. shielded pool",
    ["z to z, amounts encrypted", "txid + height public"], edge=C.ACC, tcolor=C.ACC)
box(51.5, 33, 22, 15, "3. auction wallet",
    ["seller reads the amounts", "nobody else can"])
box(76, 33, 21.5, 15, "4. refunds",
    ["losing bids sent back", "overpayment too"], edge=C.GOOD, tcolor=C.GOOD)


def arrow(x1, x2, y=40.5, color=C.ACC):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=18,
                                 linewidth=2.0, color=color, shrinkA=0, shrinkB=0))


arrow(25.4, 26.1)
arrow(49.9, 50.6)
arrow(74.4, 75.1, color=C.GOOD)

ax.add_patch(FancyBboxPatch((3, 19), 94.5, 10.5, boxstyle="round,pad=0.8,rounding_size=1.6",
                            linewidth=1.4, edgecolor=C.GOOD, facecolor="#0f1a15"))
C.fit(ax, 50, 27.0, "Refunds are plain shielded transfers.",
      88, size=17, head=True, color=C.GOOD, ha="center")
C.fit(ax, 50, 23.6, "No escrow. No lockup.", 88, size=17, head=True, color=C.GOOD, ha="center")
C.fit(ax, 50, 20.4, "Back to the bidder's own address; nothing is held.",
      88, size=15, color=C.DIM, ha="center")

ax.add_patch(FancyBboxPatch((3, 8.5), 94.5, 9.0, boxstyle="round,pad=0.8,rounding_size=1.6",
                            linewidth=1.4, edgecolor=C.WARN, facecolor="#1c1608"))
C.fit(ax, 50, 14.6, "The only ZEC actually spent: chain fees", 88, size=17, head=True,
      color=C.WARN, ha="center")
C.fit(ax, 50, 10.8, "12 transactions, ~$1.50 in total; about 0.00015 ZEC each.",
      88, size=16, color=C.DIM, ha="center")

C.fit(ax, 2, 4.0, "On-chain transfers cannot be undone - which is why the demo keeps the round "
      "small and refunds every losing bid.", 96, size=15, color=C.DIM)

fig.savefig(OUT, facecolor=C.BG, bbox_inches="tight")
print("wrote", OUT, "|", C.report())
