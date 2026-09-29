# -*- coding: utf-8 -*-
"""One-page visual: where the demo ZEC goes, and how it comes back (English)."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parents[1] / "docs" / "refund_flow.png"

BG = "#0b0f14"
BOX = "#141c26"
EDGE = "#2b3a4a"
ACC = "#4ea1ff"
GOOD = "#3ddc97"
WARN = "#ffb340"
TXT = "#e6edf3"
DIM = "#8b98a5"

fig, ax = plt.subplots(figsize=(11, 6.2), dpi=170)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis("off")

ax.text(2, 57.5, "Where the ZEC goes (DEMO-01, end to end)", color=TXT, fontsize=19, weight="bold")
ax.text(2, 52.8, "Nothing is spent: the ZEC moves into the auction wallet and comes back the same way.",
        color=DIM, fontsize=11.5)


def box(x, y, w, h, title, lines, edge=EDGE, tcolor=TXT):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=1.6",
                                linewidth=1.4, edgecolor=edge, facecolor=BOX))
    ax.text(x + w / 2, y + h - 3.0, title, color=tcolor, fontsize=12.5, weight="bold", ha="center")
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 6.6 - i * 3.4, ln, color=DIM, fontsize=10.0, ha="center")


box(3, 33, 21, 15, "1. bidder wallet",
    ["sends one shielded transfer", "the amount IS the bid"], edge=ACC, tcolor=ACC)
box(28.5, 33, 21, 15, "2. shielded pool",
    ["z to z, amounts encrypted", "only txid + height public"], edge=ACC, tcolor=ACC)
box(54, 33, 21, 15, "3. auction wallet",
    ["seller reads the amounts", "nobody else can"])
box(79.5, 33, 18, 15, "4. refunds",
    ["losing bids sent back", "overpayment too"], edge=GOOD, tcolor=GOOD)


def arrow(x1, x2, y=40.5, color=ACC, txt=None):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=18,
                                 linewidth=2.0, color=color, shrinkA=0, shrinkB=0))
    if txt:
        ax.text((x1 + x2) / 2, y + 1.9, txt, color=DIM, fontsize=9, ha="center")


arrow(24.4, 28.1, txt="z to z")
arrow(49.9, 53.6, txt="sealed")
arrow(75.4, 79.1, color=GOOD, txt="refund")

ax.add_patch(FancyBboxPatch((3, 20), 94.5, 9.0, boxstyle="round,pad=0.8,rounding_size=1.6",
                            linewidth=1.4, edgecolor=GOOD, facecolor="#0f1a15"))
ax.text(50, 26.3, "Refunds are plain shielded transfers straight back to the bidder's own address: no escrow, no lockup.",
        color=GOOD, fontsize=11.5, ha="center", weight="bold")
ax.text(50, 22.6, "One of the three demo bids was sent by hand from a phone wallet running Noir.",
        color=DIM, fontsize=10.2, ha="center")

ax.add_patch(FancyBboxPatch((3, 8.5), 94.5, 9.0, boxstyle="round,pad=0.8,rounding_size=1.6",
                            linewidth=1.4, edgecolor=WARN, facecolor="#1c1608"))
ax.text(50, 14.8, "The only ZEC actually spent: chain fees", color=WARN,
        fontsize=11.5, ha="center", weight="bold")
ax.text(50, 11.1, "About 0.00015 ZEC per transaction: 12 transactions in the round, ~0.001 ZEC (~$1.50) in total.",
        color=DIM, fontsize=10.2, ha="center")

ax.text(2, 4.0, "On-chain transfers cannot be undone - which is why the demo keeps the round small and refunds every losing bid.",
        color=DIM, fontsize=9.4)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("WROTE", OUT)
