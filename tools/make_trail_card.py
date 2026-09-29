# -*- coding: utf-8 -*-
# Money-trail card for DEMO-01: all twelve on-chain legs, roomy rows (English).
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cardkit as C

DOCS = Path(__file__).resolve().parent.parent / "docs"
MT = json.loads((DOCS / "demo_01_money_trail.json").read_text(encoding="utf-8"))
LEGS = MT.get("legs", [])
SHORT = {"user": "you", "lot/seller": "seller", "bidder A": "bidder A", "bidder B": "bidder B"}

# --- PART2 ---
fig, ax = C.use_dark(11.0, 6.6)
C.T(ax, 4, 56.4, "ShieldBid", size=17, head=True, color=C.ACC)
C.fit(ax, 4, 52.4, "DEMO-01 sealed-bid round - where the money went", 74, size=21, head=True)
C.T(ax, 96, 56.4, "ZCASH MAINNET", size=13, head=True, color=C.WARN, ha="right")
C.fit(ax, 4, 48.4, "Every leg is on chain. Amounts are private; the transaction ids are public.",
      92, size=16, color=C.DIM)
COLS = ((5, 3, "i"), (9, 42, "what"), (53, 13, "amount"), (67, 17, "flow"), (85, 11, "txid"))
for x, w, label in COLS:
    C.fit(ax, x, 44.6, label, w, size=12, head=True, color=C.DIM)

# --- PART3 ---
def _n(v):
    return v if isinstance(v, str) else f"{v:g}"


y = 41.4
for leg in LEGS:
    i = str(leg.get("i", ""))
    what = str(leg.get("what", ""))
    amt = _n(leg.get("amount", ""))
    src = SHORT.get(str(leg.get("from", "")), str(leg.get("from", "")))
    dst = SHORT.get(str(leg.get("to", "")), str(leg.get("to", "")))
    tx = str(leg.get("txid", ""))
    tx = tx[:10] + ".." if len(tx) > 12 else tx
    C.fit(ax, 5, y, i, 3, size=12, color=C.DIM)
    C.fit(ax, 9, y, what, 42, size=12, color=C.TXT, wrap=1)
    C.fit(ax, 53, y, amt, 13, size=12, color=C.GOOD)
    C.fit(ax, 67, y, f"{src} -> {dst}", 17, size=12, color=C.DIM, wrap=1)
    C.fit(ax, 85, y, tx, 11, size=12, color=C.ACC)
    y -= 3.0

C.T(ax, 4, 4.4, "protocol SHIELDBID/1 - trail docs/demo_01_money_trail.json",
    size=14, color=C.DIM)

out = DOCS / "demo01_trail.png"
fig.savefig(out, dpi=150, facecolor=C.BG, bbox_inches="tight", pad_inches=0.25)
print(f"wrote {out} | {C.report()}")


