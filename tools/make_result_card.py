# -*- coding: utf-8 -*-
"""Final result card for DEMO-01 (settlement + money trail), dark image, English."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
ST = json.loads((REPO / "docs" / "demo_01_settlement.json").read_text(encoding="utf-8"))
MT = json.loads((REPO / "docs" / "demo_01_money_trail.json").read_text(encoding="utf-8"))
OUT = REPO / "docs" / "demo01_result.png"

BG, BOX, EDGE = "#0b0f14", "#141c26", "#2b3a4a"
TXT, DIM, GOOD, WARN, BAD = "#e6edf3", "#8b98a5", "#3fb950", "#d29922", "#f85149"

fig, ax = plt.subplots(figsize=(11, 6.4), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 64)
ax.axis("off")


def box(x, y, w, h):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=BOX, edgecolor=EDGE, lw=1))


def T(x, y, s, color=TXT, size=10, weight="normal", ha="left"):
    ax.text(x, y, s, color=color, fontsize=size, weight=weight, ha=ha)


# ------------------------------------------------------------------ header
T(4, 58.5, "ShieldBid - DEMO-01 sealed-bid result", size=19, weight="bold")
T(4, 54.2, "Bids are encrypted on-chain; only the auction wallet can read them.",
  color=DIM, size=10)
T(4, 51.9, "Losing amounts and identities are never published.", color=DIM, size=10)
T(96, 58.5, "Zcash mainnet", color=WARN, size=11, ha="right")
T(96, 55.4, f"clearing price {ST['clearing_price']} ZEC", color=GOOD, size=11,
  weight="bold", ha="right")

# ------------------------------------------------------------------ results
box(4, 30, 56, 20)
T(7, 47.2, "Reveal - uniform price: every winner pays the lowest winning bid",
  color=DIM, size=10.5)
for x, label in ((7, "rank"), (15, "bidder"), (37, "bid"), (46, "pays"), (54, "refund")):
    T(x, 43.9, label, color=DIM, size=10)

y = 40.3
for row in ST["settlement"]:
    win = row["result"] == "win"
    name = row["bidder"].replace("USER@Noir", "you (Noir wallet)")
    T(7, y, f"#{row['rank']}", color=GOOD if win else BAD, size=11.5, weight="bold")
    T(15, y, name, size=11.5)
    T(37, y, row["amount"], size=11.5)
    T(46, y, f"{float(row['pays']):.3f}", color=GOOD if win else BAD, size=11.5, weight="bold")
    T(54, y, f"{float(row['refund']):.3f}", color=DIM, size=11.5)
    y -= 3.5

T(7, 31.9, f"{ST['slots']} slots - reserve {ST['reserve']} ZEC - {ST['bids_received']} bids "
           f"received (the count itself is never published)", color=DIM, size=9.5)

# ------------------------------------------------------------------ money
box(62, 30, 34, 20)
T(65, 47.2, "your money", color=DIM, size=10.5)
T(65, 43.9, f"in  {MT['in_total_from_user']} ZEC (bid 0.012 + float 0.02)", size=10.5)
T(65, 40.3, f"out {MT['out_to_user']} ZEC (5 legs, all to your U1)", color=GOOD,
  size=11, weight="bold")
T(65, 36.7, f"cost ~{MT['chain_fees_approx']} ZEC chain fees (all of it)", color=DIM, size=10)
T(65, 33.1, "no escrow, no lockup, nothing bought", color=GOOD, size=10)

# ------------------------------------------------------------------ trail
box(4, 5, 92, 22)
T(7, 24.2, "every leg is on-chain (amounts visible only to the parties, txids public)",
  color=DIM, size=10.5)
y = 20.6
for leg in MT["legs"]:
    T(7, y, f"{leg['i']:>2}", color=DIM, size=8.5)
    T(12, y, leg["what"], size=8.5)
    T(45, y, f"{leg['amount']} ZEC", color=GOOD if leg["to"].startswith("user") else TXT, size=9)
    T(57, y, f"{leg['from']} -> {leg['to']}", color=DIM, size=8.5)
    T(79, y, f"{leg['txid'][:12]}...", color=DIM, size=8)
    y -= 1.28

T(4, 2, "protocol SHIELDBID/1 - receipt docs/demo_01_settlement.json - "
        "trail docs/demo_01_money_trail.json", color=DIM, size=9.5)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("wrote", OUT)
