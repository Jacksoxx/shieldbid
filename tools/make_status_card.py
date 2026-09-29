# -*- coding: utf-8 -*-
# Status card for DEMO-01: what has been bid so far, in one dark image (English).
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cardkit as C

REPO = Path(__file__).resolve().parents[1]
LED = json.loads((REPO / "docs" / "demo_01_ledger.json").read_text(encoding="utf-8"))
ST = json.loads((REPO / "docs" / "demo_01_settlement.json").read_text(encoding="utf-8"))
OUT = REPO / "docs" / "demo01_status.png"

NAME = {"USER@Noir": "you (Noir wallet)"}
mine = [b for b in LED["bids"] if b["bidder"].startswith("USER")][0]
clearing = ST["clearing_price"]
refund = round(float(mine["amount"]) - float(clearing), 3)

fig, ax = C.use_dark(w=10.0, h=5.6, xlim=100)

# ------------------------------------------------------------------ header
C.fit(ax, 4, 52.6, "ShieldBid · DEMO-01 sealed-bid round", 60, size=22, head=True, color=C.TXT)
C.fit(ax, 4, 48.4, "Bids are encrypted on-chain: only the auction wallet can read the amounts.",
      72, size=18, color=C.DIM)
C.fit(ax, 96, 52.6, "Zcash mainnet", 22, size=12, head=True, color=C.WARN, ha="right")

# ------------------------------------------------------------------ bid table
C.box(ax, 4, 30.5, 92, 14.4)
for x, w, h in ((7, 24, "Bidder"), (32, 18, "Bid (ZEC)"), (52, 22, "on-chain tx"), (76, 18, "sent how")):
    C.fit(ax, x, 42.4, h, w, size=11, head=True, color=C.DIM)
y = 38.6
for b in LED["bids"]:
    C.fit(ax, 7, y, NAME.get(b["bidder"], b["bidder"]), 24, size=15, color=C.TXT)
    C.fit(ax, 32, y, f"{b['amount']}", 18, size=15, color=C.GOOD, head=True)
    C.fit(ax, 52, y, f"{b['txid'][:10]}…", 22, size=15, color=C.DIM)
    src = "by hand, Noir wallet" if b["bidder"].startswith("USER") else "script robot"
    C.fit(ax, 76, y, src, 18, size=15, color=C.DIM)
    y -= 3.2

# ------------------------------------------------------------------ rules
C.panel(ax, 4, 10, 44, 18, "RULES")
C.fit(ax, 7, 21.6, f"{LED['slots']} slots · reserve {LED['reserve']} ZEC", 38, size=15, color=C.TXT)
C.fit(ax, 7, 18.4, "Uniform price: every winner pays the lowest winning bid", 38, size=15,
      color=C.TXT, wrap=2, lead=1.5)
C.fit(ax, 7, 13.2, "Losing bids and identities stay private", 38, size=12, head=True, color=C.GOOD)

# ------------------------------------------------------------------ your money
C.panel(ax, 52, 10, 44, 18, "YOUR MONEY")
C.fit(ax, 55, 21.6, f"bid {mine['amount']} ZEC (~ $18)", 38, size=15, color=C.TXT)
C.fit(ax, 55, 18.4, f"you pay only {clearing} — {refund} came back to you", 38, size=15,
      color=C.GOOD, wrap=2, lead=1.5)
C.fit(ax, 55, 13.2, "only loss: chain fees ~ $1", 38, size=15, color=C.DIM)

# ------------------------------------------------------------------ footer
C.fit(ax, 4, 6.4, f"protocol SHIELDBID/1 · auction {LED['auction_id']} · {len(LED['bids'])} bids",
      92, size=14, color=C.DIM)
C.fit(ax, 4, 2.8, "receiving / refund address = your own U1 wallet (never published in the repo)",
      92, size=14, color=C.DIM)

fig.savefig(OUT, facecolor=C.BG, bbox_inches="tight")
print("wrote", OUT, "|", C.report())
