# -*- coding: utf-8 -*-
# Settlement card for DEMO-01: who won, what they pay, what comes back (English).
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cardkit as C

C.use_fonts()
ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ST = json.loads((DOCS / "demo_01_settlement.json").read_text(encoding="utf-8"))
MT = json.loads((DOCS / "demo_01_money_trail.json").read_text(encoding="utf-8"))

SHORT = {"USER@Noir": "you (Noir wallet)"}
fig, ax = C.use_dark(11.0, 5.6)
C.T(ax, 4, 48.0, "ShieldBid", size=17, head=True, color=C.ACC)
C.fit(ax, 4, 43.8, "DEMO-01 sealed-bid round - the settlement", 46, size=22, head=True)
C.T(ax, 96, 48.0, "ZCASH MAINNET", size=13, head=True, color=C.WARN, ha="right")
C.fit(ax, 96, 43.8, f"clearing price {ST['clearing_price']} ZEC", 34, size=15, color=C.TXT, ha="right")
C.fit(ax, 4, 40.4, "Bids are encrypted on chain; only the auction wallet can read them.",
      92, size=16, color=C.DIM)
C.fit(ax, 4, 37.2, "Losing amounts and identities are never published.", 92, size=16, color=C.DIM)
# --- results table ---
C.box(ax, 4, 10.0, 52, 25.4)
C.fit(ax, 7, 32.0, "Reveal - uniform price: winners pay the lowest winning bid",
      46, size=16, color=C.DIM)
for x, w, label in ((7, 5, "rank"), (14, 19, "bidder"), (35, 9, "bid"),
                    (46, 8, "pays"), (55, 6, "refund")):
    C.fit(ax, x, 27.8, label, w, size=11, head=True, color=C.DIM)
def _n(v):
    return v if isinstance(v, str) else f"{v:g}"


for i, r in enumerate(ST.get("settlement", [])):
    y = 24.0 - i * 4.0
    C.fit(ax, 7, y, str(r.get("rank", "")), 5, size=15, color=C.DIM)
    C.fit(ax, 14, y, SHORT.get(r.get("bidder", ""), str(r.get("bidder", ""))), 19, size=16,
          color=C.GOOD if i == 0 else C.TXT)
    C.fit(ax, 35, y, _n(r.get("amount", 0)), 9, size=16, color=C.GOOD)
    C.fit(ax, 46, y, _n(r.get("pays", 0)), 8, size=16, color=C.TXT)
    C.fit(ax, 55, y, _n(r.get("refund", 0)), 6, size=16, color=C.TXT)
note = (f"{ST['slots']} slots - reserve {_n(ST['reserve'])} ZEC - "
        f"{ST['bids_received']} bids received")
C.fit(ax, 7, 14.2, note, 50, size=16, color=C.WARN, wrap=1)

# --- your money ---
C.panel(ax, 63.5, 10.0, 32.5, 25.4, "Your money")
C.fit(ax, 66, 28.4, f"in {_n(MT['in_total_from_user'])} ZEC", 28, size=20, color=C.TXT)
C.fit(ax, 66, 24.4, f"bid {_n(ST['settlement'][0]['amount'])} + float 0.02", 28, size=15, color=C.DIM)
C.fit(ax, 66, 20.0, f"out {_n(MT['out_to_user'])} ZEC", 28, size=20, color=C.GOOD)
C.fit(ax, 66, 16.0, "5 legs, all to your U1", 28, size=15, color=C.DIM)
C.fit(ax, 66, 12.6, "cost -0.001 ZEC in chain fees", 28, size=15, color=C.DIM)
C.fit(ax, 66, 10.4, "no escrow, no lockup, nothing bought", 28, size=14, color=C.GOOD)

C.T(ax, 4, 5.0, f"protocol SHIELDBID/1 - receipt docs/demo_01_settlement.json",
    size=14, color=C.DIM)

out = DOCS / "demo01_result.png"
fig.savefig(out, dpi=150, facecolor=C.BG, bbox_inches="tight", pad_inches=0.25)
print(f"wrote {out} | {'overflow: ' + '; '.join(C.WARNINGS) if C.WARNINGS else 'ok'}")

