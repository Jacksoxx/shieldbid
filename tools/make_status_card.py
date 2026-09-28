# -*- coding: utf-8 -*-
"""Status card for DEMO-01: what has been bid so far, in one dark image."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

CJK = None
for cand in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"):
    if Path(cand).exists():
        CJK = FontProperties(fname=cand)
        break

REPO = Path(__file__).resolve().parents[1]
LED = json.loads((REPO / "docs" / "demo_01_ledger.json").read_text(encoding="utf-8"))
OUT = REPO / "docs" / "demo01_status.png"

BG, BOX, EDGE = "#0b0f14", "#141c26", "#2b3a4a"
TXT, DIM, GOOD, WARN = "#e6edf3", "#8b98a5", "#3fb950", "#d29922"

fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 56)
ax.axis("off")

ax.text(4, 50.5, "暗标 · ShieldBid  DEMO-01", color=TXT, fontproperties=CJK, fontsize=20, weight="bold")
ax.text(4, 46.2, "密封竞价：出价金额在链上加密，只有拍卖钱包读得到。", color=DIM,
        fontproperties=CJK, fontsize=11.5)
ax.text(96, 50.5, "Zcash 主网", color=WARN, fontproperties=CJK, fontsize=11, ha="right")

ax.add_patch(plt.Rectangle((4, 33.5), 92, 9.6, facecolor=BOX, edgecolor=EDGE, lw=1))
cols = [(7, "出价人"), (30, "金额 (ZEC)"), (50, "链上交易"), (74, "身份/来源")]
for x, h in cols:
    ax.text(x, 40.4, h, color=DIM, fontproperties=CJK, fontsize=10.5)
y = 36.6
for b in LED["bids"]:
    ax.text(7, y, b["bidder"], color=TXT, fontproperties=CJK, fontsize=11.5)
    ax.text(30, y, f"{b['amount']}", color=GOOD, fontproperties=CJK, fontsize=11.5, weight="bold")
    ax.text(50, y, f"{b['txid'][:10]}…", color=DIM, fontproperties=CJK, fontsize=10)
    src = "手机钱包手发" if b["bidder"].startswith("USER") else "脚本机器人"
    ax.text(74, y, src, color=DIM, fontproperties=CJK, fontsize=10)
    y -= 3.2

ax.add_patch(plt.Rectangle((4, 12), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(7, 26.5, "规则", color=DIM, fontproperties=CJK, fontsize=10.5)
ax.text(7, 22.4, f"名额 {LED['slots']} 个 · 保留价 {LED['reserve']} ZEC",
        color=TXT, fontproperties=CJK, fontsize=11.5)
ax.text(7, 18.6, "统一价格清算：中标者都按最低中标价付",
        color=TXT, fontproperties=CJK, fontsize=10.5)
ax.text(7, 14.8, "输家的出价与身份永不公开", color=GOOD, fontproperties=CJK, fontsize=10.5, weight="bold")

ax.add_patch(plt.Rectangle((52, 12), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(55, 26.5, "你的钱", color=DIM, fontproperties=CJK, fontsize=10.5)
ax.text(55, 22.4, "0.012 ZEC 已出价（≈ \$18）", color=TXT, fontproperties=CJK, fontsize=11.5)
ax.text(55, 18.6, "预计只付 0.009，多出的 0.003 退回你", color=GOOD,
        fontproperties=CJK, fontsize=10.5, weight="bold")
ax.text(55, 14.8, "唯一损耗：链上手续费 ≈ ¥1 全程", color=DIM, fontproperties=CJK, fontsize=10.5)

ax.text(4, 7, f"协议 SHIELDBID/1 · 拍卖号 {LED['auction_id']} · 出价数 {len(LED['bids'])}",
        color=DIM, fontproperties=CJK, fontsize=10)
ax.text(4, 3, "收款/退款地址 = 你的固定 U1（只有你和我看得到）", color=DIM,
        fontproperties=CJK, fontsize=10, alpha=0.85)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("wrote", OUT)
