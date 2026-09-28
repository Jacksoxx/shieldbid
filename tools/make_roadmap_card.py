# -*- coding: utf-8 -*-
"""M5 roadmap card: 9/29 -> 10/28 deadline, dark, single PNG."""
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

BG, BOX, EDGE = "#0b0f14", "#141c26", "#2b3a4a"
TXT, DIM, GOOD, ACCENT, WARN = "#e6edf3", "#8b98a5", "#3fb950", "#58a6ff", "#d29922"

fig, ax = plt.subplots(figsize=(11.5, 6.6), dpi=150)
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 100)
ax.set_ylim(0, 66)
ax.axis("off")

ax.text(4, 61, "暗标 · ShieldBid — 到 10/28 的作战计划", color=TXT, fontproperties=CJK,
        fontsize=19, weight="bold")
ax.text(4, 56.6, "M4 已完成：主网真钱跑完一轮（12 笔链上交易，钱已全部回你钱包）",
        color=GOOD, fontproperties=CJK, fontsize=11.5)
ax.text(96, 61, "截止 10/28 23:59 UTC", color=WARN, fontproperties=CJK, fontsize=11, ha="right")
ax.text(96, 56.6, "自有死线 10/14", color=DIM, fontproperties=CJK, fontsize=11, ha="right")

# ---------------------------------------------------------------- timeline
ax.plot([8, 92], [47.5, 47.5], color=EDGE, lw=3, solid_capstyle="round")
steps = [
    (14, "9/29 – 30", "仓库定稿", "README（英文为主）\n安全自查 · 截图\n推 GitHub", GOOD),
    (36, "9/30 – 10/2", "录 demo 视频", "2 分钟\n屏幕录制 + 语音旁白\n（不放真人脸）", ACCENT),
    (58, "10/2 – 5", "写好提交材料", "名字 / 赛道\n描述 / repo / demo 链接\n填好停在最后一步", ACCENT),
    (80, "10/5 – 14", "缓冲 + 加分项", "第二轮实盘\n透明 vs 屏蔽对照图\n英文润色", WARN),
]
for x, when, what, detail, col in steps:
    ax.add_patch(plt.Circle((x, 47.5), 1.5, facecolor=col, edgecolor=BG, lw=2, zorder=5))
    ax.text(x, 51.5, when, color=col, fontproperties=CJK, fontsize=11, ha="center", weight="bold")
    ax.add_patch(plt.Rectangle((x - 10, 26), 20, 21, facecolor=BOX, edgecolor=EDGE, lw=1))
    ax.text(x, 44, what, color=TXT, fontproperties=CJK, fontsize=12.5, ha="center", weight="bold")
    ax.text(x, 34.5, detail, color=DIM, fontproperties=CJK, fontsize=9.8, ha="center", va="center")

# ---------------------------------------------------------------- split
ax.add_patch(plt.Rectangle((4, 4), 44, 18, facecolor=BOX, edgecolor=EDGE, lw=1))
ax.text(7, 18.6, "【我全包】你不用管", color=ACCENT, fontproperties=CJK, fontsize=12, weight="bold")
for i, t in enumerate([
    "仓库、README、截图、安全自查",
    "录视频 + 生成中英旁白 + 剪辑",
    "填 submission 表单（停最后一步）",
    "第二轮实盘 + 对照图 + 润色",
]):
    ax.text(7, 15 - i * 2.9, "· " + t, color=TXT, fontproperties=CJK, fontsize=10.5)

ax.add_patch(plt.Rectangle((52, 4), 44, 18, facecolor=BOX, edgecolor=WARN, lw=1.2))
ax.text(55, 18.6, "【只有你能做】就这 3 件", color=WARN, fontproperties=CJK, fontsize=12, weight="bold")
for i, t in enumerate([
    "GitHub：给我授权 / 或网页上传一次",
    "视频旁白：你确认稿子后点发布",
    "最后：检查一遍，亲手点「提交」",
]):
    ax.text(55, 15 - i * 2.9, f"{i+1}. " + t, color=TXT, fontproperties=CJK, fontsize=10.5)
ax.text(55, 6.2, "每次只占用你几分钟；我不碰你任何密码/私钥", color=DIM, fontproperties=CJK, fontsize=9.5)

ax.text(4, 1.2, "明早新窗口发「暗标 继续」→ 我自动读 HANDOFF + docs/M5_PLAN.md 接着干",
        color=DIM, fontproperties=CJK, fontsize=10)

out = Path(__file__).resolve().parents[1] / "docs" / "M5_ROADMAP.png"
fig.savefig(out, facecolor=BG, bbox_inches="tight")
print("wrote", out)
