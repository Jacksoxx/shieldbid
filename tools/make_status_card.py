# -*- coding: utf-8 -*-
"""Status card for DEMO-01: what has been bid so far, in one dark image (English)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
LED = json.loads((REPO / "docs" / "demo_01_ledger.json").read_text(encoding="utf-8"))
OUT = REPO / "docs" / "demo01_status.png"

BG, BOX, EDGE = "#0b0f14", "#141c26", "#2b3a4a"
TXT, DIM, GOOD, WARN = "#e6edf3", "#8b98a5", "#3fb950", "#d29922"

NAME = {"USER@Noir": "you (Noir phone wallet)"}

fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 56)
ax.axis("off")

ax.text(4, 50.5, "ShieldBid · DEMO-01 sealed-bid round", color=TXT, fontsize=20, weight="bold")
ax.text(4, 46.2, "Bids are encrypted on-chain: only the auction wallet can read the amounts.",
        color=DIM, fontsize=11.5)
ax.text(96, 50.5, "Zcash mainnet", color=WARN, fontsize=11, ha="right")

ax.add_patch(plt.Rectangle((4, 33.5), 92, 9.6, facecolor=BOX, edgecolor=EDGE, lw=1))
cols = [(7, "Bidder"), (30, "Bid (ZEC)"), (50, "on-chain tx"), (74, "sent how")]
for x, h in cols:
    ax.text(x, 40.4, h, color=DIM, fontsize=10.5)
y = 36.6
for b in LED["bids"]:
    ax.text(7, y, NAME.get(b["bidder"], b["bidder"]), color=TXT, fontsize=11.5)
    ax.text(30, y, f"{b['amount']}", color=GOOD, fontsize=11.5, weight="bold")
    ax.text(50, y, f"{b['txid'][:10]}…", color=DIM, fontsize=10)
    src = "by hand, phone wallet" if b["bidder"].startswith("USER") else "script robot"
    ax.text(74, y, src, color=DIM, fontsize=10)
    y -= 3.2

ax.add_patch(plt.Rectangle((4, 12), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(7, 26.5, "RULES", color=DIM, fontsize=10.5)
ax.text(7, 22.4, f"{LED['slots']} slots · reserve {LED['reserve']} ZEC", color=TXT, fontsize=11.5)
ax.text(7, 18.6, "Uniform price: every winner", color=TXT, fontsize=10.5)
ax.text(7, 16.6, "pays the lowest winning bid", color=TXT, fontsize=10.5)
ax.text(7, 14.8, "Losing bids and identities stay private", color=GOOD, fontsize=10.5, weight="bold")

ax.add_patch(plt.Rectangle((52, 12), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(55, 26.5, "YOUR MONEY", color=DIM, fontsize=10.5)
ax.text(55, 22.4, "bid 0.012 ZEC (~ $18)", color=TXT, fontsize=11.5)
ax.text(55, 18.6, "you pay only 0.009 — 0.003", color=GOOD, fontsize=10.5, weight="bold")
ax.text(55, 16.6, "came back to you", color=GOOD, fontsize=10.5, weight="bold")
ax.text(55, 14.8, "only loss: chain fees ≈ $1 for the round", color=DIM, fontsize=10)

ax.text(4, 7, f"protocol SHIELDBID/1 · auction {LED['auction_id']} · {len(LED['bids'])} bids",
        color=DIM, fontsize=10)
ax.text(4, 3, "receiving / refund address = your own U1 wallet (never published in the repo)",
        color=DIM, fontsize=10, alpha=0.85)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("wrote", OUT)
