# -*- coding: utf-8 -*-
"""One-page visual: where the demo ZEC goes, and how it comes back."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties

CJK = None
for cand in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/simhei.ttf"):
    if Path(cand).exists():
        CJK = FontProperties(fname=cand)
        break
if CJK is None:
    CJK = FontProperties()

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

ax.text(2, 57.5, "这笔 ZEC 会去哪儿？（demo 全程）", color=TXT, fontproperties=CJK, fontsize=19, weight="bold")
ax.text(2, 52.8, "钱不是花掉，只是从你左手换到我们右手，跑完原路回你左手。", color=DIM, fontproperties=CJK, fontsize=11.5)

def box(x, y, w, h, title, lines, edge=EDGE, tcolor=TXT):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=1.6",
                                linewidth=1.4, edgecolor=edge, facecolor=BOX))
    ax.text(x + w / 2, y + h - 3.0, title, color=tcolor, fontproperties=CJK,
            fontsize=12.5, weight="bold", ha="center")
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 6.6 - i * 3.4, ln, color=DIM, fontproperties=CJK,
                fontsize=10.0, ha="center")

box(3, 33, 21, 15, "① 你的 Noir 钱包",
    ["转出 0.032 ZEC", "（≈ $49，押金）"], edge=ACC, tcolor=ACC)
box(28.5, 33, 21, 15, "② 演示钱包",
    ["我们控制的屏蔽地址", "助记词只在你电脑上"], edge=ACC, tcolor=ACC)
box(54, 33, 21, 15, "③ 揭标 + 结算",
    ["只有卖家读得到出价", "只公布清算价/名次"])
box(79.5, 33, 18, 15, "④ 退回你",
    ["打回你 Noir 地址", "≈ 0.032 ZEC"], edge=GOOD, tcolor=GOOD)

def arrow(x1, x2, y=40.5, color=ACC, txt=None):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>", mutation_scale=18,
                                 linewidth=2.0, color=color, shrinkA=0, shrinkB=0))
    if txt:
        ax.text((x1 + x2) / 2, y + 1.9, txt, color=DIM, fontproperties=CJK, fontsize=9, ha="center")

arrow(24.4, 28.1, txt="z→z 屏蔽")
arrow(49.9, 53.6, txt="加密")
arrow(75.4, 79.1, color=GOOD, txt="退款")

ax.add_patch(FancyBboxPatch((3, 20), 94.5, 9.0, boxstyle="round,pad=0.8,rounding_size=1.6",
                            linewidth=1.4, edgecolor=GOOD, facecolor="#0f1a15"))
ax.text(50, 26.3, "随时可退：你一转过去，哪怕我一步都没跑，也能立刻全额打回你的 Noir 地址。",
        color=GOOD, fontproperties=CJK, fontsize=11.5, ha="center", weight="bold")
ax.text(50, 22.6, "没有托管方、没有锁仓合约、不需要任何人同意 —— 签名权在我们手上，助记词就在你这台电脑里。",
        color=DIM, fontproperties=CJK, fontsize=10.2, ha="center")

ax.add_patch(FancyBboxPatch((3, 8.5), 94.5, 9.0, boxstyle="round,pad=0.8,rounding_size=1.6",
                            linewidth=1.4, edgecolor=WARN, facecolor="#1c1608"))
ax.text(50, 14.8, "唯一真正花掉的钱：链上手续费", color=WARN, fontproperties=CJK,
        fontsize=11.5, ha="center", weight="bold")
ax.text(50, 11.1, "你截图里写的是 0.00015 ZEC/笔（≈ ¥0.15）。全程十几笔，总共约 0.001 ZEC ≈ ¥1。",
        color=DIM, fontproperties=CJK, fontsize=10.2, ha="center")

ax.text(2, 4.0, "链上转账本身不可撤销 —— 但这一步是不可撤销地转进「我们自己控制」的钱包，不是转给第三方。",
        color=DIM, fontproperties=CJK, fontsize=9.4)

fig.savefig(OUT, facecolor=BG, bbox_inches="tight")
print("WROTE", OUT)
