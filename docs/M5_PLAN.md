# M5 执行计划 —— 把 DEMO-01 变成能提交的参赛作品

> 今天：2026-09-29（北京） · 截止：**2026-10-28 23:59 UTC**
> 自有死线：**10-14 全部就绪**，后两周只留缓冲（防引擎挂、防录视频翻车）
> 分工：🤖 = 凤霞自己做（用户不用管）；👤 = 必须用户亲手做

---

## 一句话目标

把「ShieldBid 在 Zcash 主网真实跑完一轮密封竞价」做成三样东西交出去：
**① 能跑的开源 repo ② 2 分钟 demo 视频 ③ 提交表单**（最后点提交 = 👤）。

---

## M5.1 仓库定稿（9/29–9/30，🤖 全自动）

- [ ] `README.md` 定稿（英文为主 + 中文附注，评委看英文）：
  - 一句话定位（见 HANDOFF §7）→ 30 秒看懂
  - **DEMO-01 真实链上证据表**（12 笔腿 + txid + 链高），直接引 `docs/DEMO_01_REPORT.md`
  - 快速上手三条命令（起引擎 / 出价 / 揭标）
  - **诚实局限一节**（必须留）：没有实时最高价、卖家可篡改公布价、第三方不能验算
  - 截图区：`docs/demo01_result.png`、竞价台页面、卖家视角收据
- [ ] 截图补充：用调试浏览器（`127.0.0.1:9223`）打开本地 `web/index.html`，截暗色竞价台 → `docs/web_console.png`
- [ ] 安全自查（**提交前必做**）：
  - `git log --all --stat | grep -i mnemonic` 必须为空
  - `.gitignore` 覆盖 `*.mnemonic`、`buyer_u1_address.txt`、`*.db`
  - repo 里搜不到任何 24 词、私钥、`u1…` 用户主地址（用户 U1 只在 `~/.shieldbid/`）
- [ ] GitHub 推上去：`gh` 目前**未认证**（`gh auth status` exit 1）
  - 方案 A：👤 给我一个 GitHub token（或跑一次 `gh auth login`）→ 🤖 建仓推送
  - 方案 B（不用授权）：🤖 打包 zip + 写好 README，👤 在 GitHub 网页上传
- [ ] LICENSE 已存在，确认年份/署名（Qihao Xiao）

## M5.2 demo 视频（9/30–10/2，🤖 录 + 👤 确认稿）

**形式**：屏幕录制 + 凤霞 TTS 英文/中文旁白（不放真人脸），2 分钟
**内容脚本（2:00）**

| 时间 | 画面 | 台词要点 |
|---|---|---|
| 0:00–0:20 | zilkroad `/bids` 页面 | 别人的出价摊在桌面上：金额、总额、均价人人可见 |
| 0:20–0:50 | ShieldBid 竞价台 | 同一件事锁进密室：出价 = 一笔屏蔽转账，金额 = 出价 |
| 0:50–1:30 | `docs/demo01_result.png` + 区块浏览器 | **这不是 PPT，是真钱**：12 笔链上腿、清算价 0.009、多付退回、输家全额退 |
| 1:30–2:00 | 卖家视角收据 + 诚实局限 | 只有卖家看得到金额；链上永远看不到出价人是谁、有几个人 |

- [ ] 录制：`ffmpeg gdigrab` 截屏（🤖）；若 👤 本机有 OBS 也可用来录，我出脚本
- [ ] 旁白：`text_to_speech`（英文版 + 中文版各一）
- [ ] 合成：ffmpeg 拼 mp4 → `demo/shieldbid_demo.mp4`
- [ ] 上传：YouTube（未列出）或 X 帖子引用 —— **发布动作 = 👤**

## M5.3 提交材料（10/2–10/5，🤖 起草 + 👤 点提交）

提交入口：`thezecathon.com` → SUBMIT PROJECT（表单是 JS 渲染的，🤖 用调试浏览器填）

| 字段 | 草稿 |
|---|---|
| Project name | **ShieldBid** |
| Track | **PRIVATE MARKETS** |
| One-liner | Sealed-bid auctions on Zcash: the bid *is* a shielded transfer, so the amount never hits the chain in the clear. |
| Description | 3 段：问题（公开竞价台泄漏策略）/ 机制（escrow-as-bid + 统一清算价 + 只公布清算价与名次）/ 证据（DEMO-01 主网 12 笔腿，收据齐全） |
| Repo | GitHub 链接（M5.1 产出） |
| Demo | 视频链接（M5.2 产出） |
| Team | Qihao Xiao · China · X [@JAcksoxx_x](https://x.com/JAcksoxx_x) · TG @jacksoxx |
| 备注 | 诚实局限一句话（评委吃这套） |

- [ ] 🤖 用调试浏览器打开表单、填好、**停在最后一步不点**
- [ ] 👤 检查一遍 → **点提交** → 🤖 立刻截图存证 `docs/submission_receipt.png`
- [ ] 备用：10/28 当天再确认一次提交状态（防表单回滚/邮件未收到）

## M5.4 加分项（10/5–10/14，有空才做，别耽误上面）

- [ ] **第二轮实盘**证明可重复（三个机器人 + 👤 再出一次价，把 `DEMO-02` 收据并排展示）
- [ ] **对照图**：同一笔金额，透明地址页能看到数字 vs 屏蔽地址页只有"shielded" → 一张图讲完隐私
- [ ] 英文 README 润色（找 `humanizer` 技能去掉 AI 腔）
- [ ] X 宣传帖（带图/引用，走 👤 大号；**不公布方法细节**，写"正常玩家"口径）

---

## 风险与对策

| 风险 | 对策 |
|---|---|
| 引擎/钱包重启后同步慢 | 录 demo 前一天先拉起，`engine_up.sh` + 读余额确认 |
| 视频工具没装 | 首选 ffmpeg gdigrab（已装）；OBS 备选 |
| GitHub 认证卡住 | 走方案 B（网页上传），不阻塞 |
| 评委只读英文 | README 英文为主；视频英文旁白 |
| 主办方有争议（ZachXBT） | 只讲自己技术，不评论任何人 |
| 时间不够 | 死线 10/14 就绪；10/28 前只要 👤 点一次提交 |

---

## 明早新会话的第一个动作（按序）

1. `bash ~/shieldbid/tools/engine_up.sh` → `python tools/engine.py height --net mainnet`（确认引擎活着）
2. 读 `HANDOFF.md` §0 + 本文件
3. 从 **M5.1** 开始做（README 定稿 + 安全自查），**不需要打扰用户**
4. 需要用户时，一次只说一件：**先问这三件** ——
   - GitHub 有没有账号 / 愿不愿意给我 token（或网页上传）
   - 本机有没有 OBS（没有我就用 ffmpeg）
   - demo 视频旁白要**英文**还是**中英双语**
