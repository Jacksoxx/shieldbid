# -*- coding: utf-8 -*-
"""Final result card for DEMO-01 (settlement + money trail), dark image."""
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


# ------------------------------------------------------------------ header
ax.text(4, 58.5, "暗标 · ShieldBid  DEMO-01 揭标结果", color=TXT, fontproperties=CJK,
        fontsize=19, weight="bold")
ax.text(4, 54.2, "密封竞价：出价金额在链上加密，只有拍卖钱包读得到；输家的金额和身份永不公开。",
        color=DIM, fontproperties=CJK, fontsize=11)
ax.text(96, 58.5, "Zcash 主网", color=WARN, fontproperties=CJK, fontsize=11, ha="right")
ax.text(96, 54.2, f"清算价 {ST['clearing_price']} ZEC", color=GOOD, fontproperties=CJK,
        fontsize=11, ha="right", weight="bold")

# ------------------------------------------------------------------ results
box(4, 30, 56, 21)
ax.text(7, 47.6, "揭标（统一价：中标者都按最低中标价付）", color=DIM, fontproperties=CJK, fontsize=10.5)
ax.text(7, 44.2, "名次", color=DIM, fontproperties=CJK, fontsize=10)
ax.text(15, 44.2, "出价人", color=DIM, fontproperties=CJK, fontsize=10)
ax.text(34, 44.2, "出价", color=DIM, fontproperties=CJK, fontsize=10)
ax.text(43, 44.2, "实付", color=DIM, fontproperties=CJK, fontsize=10)
ax.text(51, 44.2, "退回", color=DIM, fontproperties=CJK, fontsize=10)

y = 40.6
for row in ST["settlement"]:
    win = row["result"] == "win"
    name = row["bidder"].replace("USER@Noir", "你（Noir 手机钱包）")
    ax.text(7, y, f"#{row['rank']}", color=GOOD if win else BAD, fontproperties=CJK,
            fontsize=11.5, weight="bold")
    ax.text(15, y, name, color=TXT, fontproperties=CJK, fontsize=11.5)
    ax.text(34, y, row["amount"], color=TXT, fontproperties=CJK, fontsize=11.5)
    ax.text(43, y, row["pays"], color=GOOD if win else BAD, fontproperties=CJK,
            fontsize=11.5, weight="bold")
    ax.text(51, y, row["refund"], color=DIM, fontproperties=CJK, fontsize=11.5)
    y -= 3.9

ax.text(7, 32.2, f"名额 {ST['slots']} 个 · 保留价 {ST['reserve']} ZEC · 收到出价 {ST['bids_received']} 笔"
                 f"（出价笔数不公开）",
        color=DIM, fontproperties=CJK, fontsize=10)

# ------------------------------------------------------------------ money
box(62, 30, 34, 21)
ax.text(65, 47.6, "你的钱", color=DIM, fontproperties=CJK, fontsize=10.5)
ax.text(65, 44.2, f"进去 {MT['in_total_from_user']} ZEC（出价 0.012 + 注资 0.02）",
        color=TXT, fontproperties=CJK, fontsize=11)
ax.text(65, 40.6, f"回来 {MT['out_to_user']} ZEC（5 笔，全打到你的 U1）",
        color=GOOD, fontproperties=CJK, fontsize=11.5, weight="bold")
ax.text(65, 37, f"损耗 ≈ {MT['chain_fees_approx']} ZEC 链上手续费",
        color=DIM, fontproperties=CJK, fontsize=11)
ax.text(65, 33.4, "零托管 · 零锁仓 · 没花钱买任何东西",
        color=GOOD, fontproperties=CJK, fontsize=10.5)

# ------------------------------------------------------------------ trail
box(4, 5, 92, 22)
ax.text(7, 24.2, "每一笔都在链上（金额只有当事人看得见，txid 公开可查）",
        color=DIM, fontproperties=CJK, fontsize=10.5)
y = 20.6
for leg in MT["legs"]:
    ax.text(7, y, f"{leg['i']:>2}", color=DIM, fontproperties=CJK, fontsize=9)
    ax.text(12, y, leg["what"], color=TXT, fontproperties=CJK, fontsize=10)
    ax.text(45, y, f"{leg['amount']} ZEC", color=GOOD if leg["to"].startswith("user") else TXT,
            fontproperties=CJK, fontsize=10)
    ax.text(57, y, f"{leg['from']} → {leg['to']}", color=DIM, fontproperties=CJK, fontsize=9.5)
    ax.text(80, y, f"{leg['txid'][:12]}…", color=DIM, fontproperties=CJK, fontsize=8.5)
    y -= 1.28

ax.text(4, 2, "协议 SHIELDBID/1 · 收据 docs/demo_01_settlement.json · 钱流 docs/demo_01_money_trail.json",
        color=DIM, fontproperties=CJK, fontsize=9.5, alpha=0.85)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("wrote", OUT)
