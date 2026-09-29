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

NAME = {"USER@Noir": "you (phone wallet)"}

fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 56)
ax.axis("off")

ax.text(4, 51, "ShieldBid · DEMO-01 sealed-bid round", color=TXT, fontsize=20, weight="bold")
ax.text(4, 47, "Bids are encrypted on-chain: only the auction wallet can read the amounts.",
        color=DIM, fontsize=11.5)
ax.text(96, 51, "Zcash mainnet", color=WARN, fontsize=11, ha="right")

# bid table: box must contain the header row and all bid rows
ax.add_patch(plt.Rectangle((4, 30.5), 92, 13.4, facecolor=BOX, edgecolor=EDGE, lw=1))
cols = [(7, "Bidder"), (32, "Bid (ZEC)"), (52, "on-chain tx"), (76, "sent how")]
for x, h in cols:
    ax.text(x, 41.0, h, color=DIM, fontsize=10.5)
y = 37.6
for b in LED["bids"]:
    ax.text(7, y, NAME.get(b["bidder"], b["bidder"]), color=TXT, fontsize=11.5)
    ax.text(32, y, f"{b['amount']}", color=GOOD, fontsize=11.5, weight="bold")
    ax.text(52, y, f"{b['txid'][:10]}…", color=DIM, fontsize=10)
    src = "by hand, phone wallet" if b["bidder"].startswith("USER") else "script robot"
    ax.text(76, y, src, color=DIM, fontsize=10)
    y -= 3.0

ax.add_patch(plt.Rectangle((4, 10), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(7, 25.0, "RULES", color=DIM, fontsize=10.5)
ax.text(7, 21.4, f"{LED['slots']} slots · reserve {LED['reserve']} ZEC", color=TXT, fontsize=11.5)
ax.text(7, 18.2, "Uniform price: every winner", color=TXT, fontsize=10.5)
ax.text(7, 16.4, "pays the lowest winning bid", color=TXT, fontsize=10.5)
ax.text(7, 13.4, "Losing bids and identities stay private", color=GOOD, fontsize=10.5, weight="bold")

ax.add_patch(plt.Rectangle((52, 10), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(55, 25.0, "YOUR MONEY", color=DIM, fontsize=10.5)
ax.text(55, 21.4, "bid 0.012 ZEC (~ $18)", color=TXT, fontsize=11.5)
ax.text(55, 18.2, "you pay only 0.009 — 0.003", color=GOOD, fontsize=10.5, weight="bold")
ax.text(55, 16.4, "came back to you", color=GOOD, fontsize=10.5, weight="bold")
ax.text(55, 13.4, "only loss: chain fees ≈ $1", color=DIM, fontsize=10)

ax.text(4, 6.2, f"protocol SHIELDBID/1 · auction {LED['auction_id']} · {len(LED['bids'])} bids",
        color=DIM, fontsize=10)
ax.text(4, 2.6, "receiving / refund address = your own U1 wallet (never published in the repo)",
        color=DIM, fontsize=10, alpha=0.85)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("wrote", OUT)
