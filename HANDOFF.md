# 🤫 暗标 · ShieldBid — HANDOFF（交接文件）

> **口令：新会话发「暗标 继续」→ 助手的第一个动作是读这份文件。**
> 代号「暗标」，产品名 ShieldBid，赛道 PRIVATE MARKETS，截止 **2026-10-28 23:59 UTC**。

## 0. 现在到哪一步了

> **⏰ LIVE STATE（2026-09-29 03:00 北京）— 接手前先读这段，确认"有没有在跑"**
> - **M4 真钱轮次已完成（DEMO-01 全流程跑通）。** 战报：`docs/DEMO_01_REPORT.md`（含 12 笔链上腿表 + 诚实局限）。
>   机器可读：`docs/demo_01_settlement.json`（揭标）、`docs/demo_01_money_trail.json`（钱流）、
>   `docs/demo_01_transactions.json`（引擎读回的账户流水）、`docs/demo_01_seller_view.json`（卖家视角读了什么）。
>   图：`docs/demo01_result.png`（最终结果卡）、`docs/demo01_status.png`（出价期状态卡）。
> - **没有任何 demo 钱包还留着钱**（余额 0，只剩 0.0001×2 的灰尘）；**没有在跑的后台进程**（收尾器跑完即退）。
> - 驱动脚本：`tools/demo_01_run.py`（`status` / `fund` / `bid` / `close` / `refund`）+ `tools/demo_01_finish.py`（收尾）。
> - 12 笔腿全部上链（链高 3,499,413 → 3,499,462），逐笔见 `docs/DEMO_01_REPORT.md` 表格；
>   钱的口径：**进去 0.032，回来 0.0307，链上手续费 ≈0.001 ZEC（≈$1.5）**。
> - 记账：`docs/demo_01_ledger.json`（出价回执+commit/salt）、`docs/demo_01_settlement.json`（揭标结果：**清算价 0.009，名额 2**）
> - **揭标已完成（2026-09-28 18:37 UTC）**：清算价 **0.009 ZEC**（统一价，名额 2）。名次
>   ① USER@Noir 0.012 → 中标，只付 0.009，退 0.003；② ROBOT-B 0.009 → 中标，正好；③ ROBOT-A 0.004 → 落标，全额退 0.004。
> - **退款/扫款腿**：用户多付 0.003 → U1（`90d35aee9490…`）；落标者 0.004 → 投标人A（`f29dbd244048…`）；
>   扫款回 U1 四笔：`0.0036`/`0.0027`/`0.0039`/`0.0175`（txid 见 `docs/demo_01_money_trail.json`）。
> - **✅ M5.1 仓库定稿已完成（2026-09-29，commit `f55e64f`）**：README / `docs/SPEC.md` / `docs/BIDDER_GUIDE.md` /
>   `web/index.html` 全部改成 v0.2「**金额即出价**（escrow-as-bid）」口径——出价 = 一笔屏蔽转账的金额，
>   memo 只作装饰、协议永不解析；`docs/web_console.png` 是竞价台渲染截图。**SPEC 版本号 = SHIELDBID/1 v0.2（冻结）**。
> - **⏭️ 下一步 = M5.2 录 2 分钟 demo + M5.3 提交材料**（计划见 `docs/M5_PLAN.md`）：
>   演示脚本 = 出价期状态卡 → 三笔出价上链 → 截止 → 揭标（清算价 0.009、名额 2）→ 多付与落标退款 →
>   U1 扫款回款。素材现成：`docs/DEMO_01_REPORT.md`（12 笔腿表）+ `docs/demo01_*.png` + 各 json。
>   → **最后一步「提交」按钮由用户自己点**（官方截止 10/28 23:59 UTC，死线留足余量）。
> - **接手第一件事**：`bash tools/engine_up.sh` 拉双引擎（主网 8000 / 测试网 8001）→
>   `python tools/engine.py height --net mainnet` 看到链高即就绪 → 然后从 M5.2 开始（不用打扰用户）。
> - **⚠️ 接手红线**：先 `python tools/demo_01_run.py status` + 读 ledger 与 **`docs/demo_01_settlement.json` + `docs/demo_01_refund_receipts.json`**，
>  **哪一步已有 txid 就绝不重发**。链上是真钱，重复出价/重复退款=白花钱。扫款段是按余额驱动的，天然幂等。
> - **⚠️ 大坑 #3（2026-09-29 发现）**：付款前**必须**先 `synchronizeAccount`，否则钱包还拿着「刚被自己花掉的那张 note」
>  去选币，节点报 `failed to validate tx … could not contextually validate`（同一钱包前几秒刚广播过付款时必现）。
>  修法：`demo_01_run.pay()` 现在**每次尝试前都 sync**，所以重试循环能自愈。
> - **⚠️ 大坑 #1（已解决，别踩回去）**：`pay` 的 `confirmations` 默认≈10，新到账的钱要等 ~10 确认才可花，
>   否则报 `No feasible note selection found`。修法：payment 里显式 `"confirmations": 1`。
> - **⚠️ 大坑 #2（2026-09-29 找到真凶）**：**绝对不要传 `srcPools`**。mutation 把它声明成标量 `Int`，
>   但任何显式取值（包括 3）都会让引擎的选笔记找不到可用 note，同样报 `No feasible note selection found`，
>   白白卡了 11 次重试。传 `[3]` 直接报类型错（`Expected input scalar Int`）。**正解 = 省略该字段**，
>   让引擎自选；demo 里所有钱都在 orchard，选出来依然是屏蔽的。
> - **⚠️ 协议已改（关键）**：备注读不出来 —— 收到的 orchard note `memo` 恒为 `null`，`memosByTransaction` 返回 `[]`。
>   → 出价改为 **金额即出价（escrow-as-bid）**：打多少钱=出多少钱，金额在链上加密；memo 只是装饰（Noir 里可留空）。
> - **电源已加固（2026-09-29 02:45）**：平衡方案下 AC 的睡眠/休眠/硬盘/显示器/无人值守全设「从不」，
>   混合睡眠关、网卡省电关；`powercfg -requests` 无阻塞项；WSL `shieldbid` Running。跑批不会因本机休眠中断。

- ✅ **M1** 协议规格 + 公开竞价台页面 + 投标人指南 + git 仓库
- ✅ **M2（本轮完成）** 本地 Zcash 引擎跑通：
  - WSL 装好（`shieldbid` 发行版），绕过商店版无法启动的坑（见 `docs/ENGINE_SETUP.md`）
  - `zkool_graphql` 引擎主网(8000)+测试网(8001)在跑，连公共节点
  - **卖家主网钱包**已建（账户 1），拿到 orchard 收款地址
  - **测试网卖家钱包**已建（测试网账户 1）
  - Windows ↔ WSL 打通：`python tools/engine.py` 能直接读链高/账户/地址/余额
  - ~~验证了核心机制：memo 能从 `notesByAccount` 直接解密读出（出价就是 memo）~~ ← **已推翻**：
    引擎对本钱包**收到**的 orchard note `memo` 恒返回 `null`，`memosByTransaction` 返回 `[]`
    → 出价机制改为「金额即出价」
  - 投标路径 dry-run 通过（带 memo 的屏蔽付款请求成形）
- ✅ **M3（本轮完成）** 投标人钱包就位 + 收款口可用了：
  - **主网投标人**：账户 2「SB Bidder A」→ 透明收款 `t1Pm2n2YGULXbZcgXAH3aCsY9mvTNZyD2dB`，
    orchard `u1e6cwevnrssknku3jncgn59jwuztnz9asckcmv0x6ndtcyxesfet5q7djy7n3a06u0trdwchpgs2qqgw086747j7kzlug6yqh0vpjpgyj`
  - **测试网投标人**：账户 2「SB Bidder Test」（tmUQNLuKA95bHgBvuXZ3PyJGmdqoLK8Fz6c）
  - `engine.py` 新增 `newaccount`（本地生成 24 词助记词 → `~/.shieldbid/<name>.mnemonic`，chmod 600）
    与 `shield`（透明 → 自己 orchard，一次性屏蔽，交易所提币进来的第一步）
  - 助记词文件在 **Windows** `C:\Users\XiaoSS\.shieldbid\`（.gitignore 之外，绝不入库）
- ✅ **M4（2026-09-29 凌晨完成）**：真钱密封竞价轮次 DEMO-01 在 Zcash 主网**跑通全流程**
  - 用户用 **Noir 手机钱包**亲手发两笔：出价 `0.012` → 卖家钱包；注资 `0.02` → 投标人A
  - 机器人 A/B 出价 `0.004` / `0.009`；揭标（清算价 = 最低中标价 = `0.009`）；中标者退多付、落标者全额退
  - 收尾：`demo_01_finish.py` 把三个 demo 钱包余额全部扫回**用户固定 U1**（余额现为 0）
  - **战报 `docs/DEMO_01_REPORT.md`（12 笔链上腿全表）；钱的口径：进去 0.032 / 回来 0.0307 / 手续费 ≈0.001**
- 🔄 **M5（下一步，计划见 `docs/M5_PLAN.md`）**：repo 定稿 → demo 视频 → 提交材料 → ⚠️ **「提交」按钮用户自己点**

## 1. 卖家收款地址（拍卖地址）

| 网络 | 地址 |
|---|---|
| 主网 orchard（卖家收款） | `u1s8xflwcl60d0ck2z028duyrfh5zr0tufjq07skymr9u64j6fd2s2dg2l854puzlq0vwy4xutwp2exph6hvtxw9ukaqpwfswdvgq26ksf` |
| 测试网 orchard（卖家收款） | `utest1ypl0gg5kgzvec8zfnylrz89xk70h3nlplwjwlx68qcapepkt3c2f0fntyzwf69czx5eu6dqzshy6vl20kd97x05gm8glyyg8cv7shxz4` |
| 主网投标人（注资口，t→自屏蔽） | `t1Pm2n2YGULXbZcgXAH3aCsY9mvTNZyD2dB` |
| 主网投标人 orchard | `u1e6cwevnrssknku3jncgn59jwuztnz9asckcmv0x6ndtcyxesfet5q7djy7n3a06u0trdwchpgs2qqgw086747j7kzlug6yqh0vpjpgyj` |

- 主网钱包助记词：WSL 里 `/root/.sb_seller_mnemonic`（chmod 600，**不打印不进 git**）
- 测试网钱包助记词：`/root/.sb_test_seller_mnemonic`
- 钱包库：`/root/sb_main.db`、`/root/sb_test.db`
- 助记词是**唯一**能拿回钱的东西 → 只存在 WSL 本地，不要往聊天里贴、不要提交到仓库

## 2. 环境怎么恢复（电脑重启后）

```bash
bash ~/shieldbid/tools/engine_up.sh          # 两个引擎都起来（已在跑就跳过）
cd ~/shieldbid && python tools/engine.py height --net mainnet
```

引擎挂了看：`wsl -d shieldbid -u root -- bash -lc "tail -20 /root/engine.log"`

完整原理、坑、GraphQL 速查表都在 **`docs/ENGINE_SETUP.md`**（这份必读）。

## 3. 工具现状

| 文件 | 作用 | 状态 |
|---|---|---|
| `tools/engine.py` | 引擎 CLI：height/accounts/addresses/balance/sync/notes/bids/bid | ✅ 可用 |
| `tools/shieldbid.py` | 卖家侧拍卖逻辑：init/ingest/commit/reveal/verify/demo | ✅ 逻辑通过，读取已改接真 schema |
| `tools/engine_up.sh` | 一键拉起引擎 | ✅ |
| `web/index.html` | 公开竞价台（暗色） | ✅ |
| `docs/SPEC.md` | 协议规格（含诚实局限） | ✅ |
| `docs/BIDDER_GUIDE.md` | 投标人傻瓜教程 | ✅ |
| `docs/zkool_graphql_schema_full.json` | 实测 API 全量 schema | ✅ |

## 4. 核心命令（记这三条就够）

```bash
# 卖家：看收款地址
python tools/engine.py addresses --net mainnet --account 1

# 投标人：投一个密封报价（0.01 ZEC 金额 + BID 1.5 出价写进 memo）
python tools/engine.py bid --net mainnet --account 2 \
    --to <卖家地址> --amount 0.01 --memo "BID 1.5"

# 卖家：同步 + 读出所有出价
python tools/engine.py sync --net mainnet --account 1 --balance
python tools/engine.py bids --net mainnet --account 1 --json
```

## 5. 铁律（踩过才知道）

1. **loopback 请求绕开代理**：curl 加 `--noproxy '*'`，Python 用 `ProxyHandler({})`。
   否则请求被丢到 7897 代理 → 假的 **HTTP 502**，看起来像引擎挂了。
2. **不要在 WSL 里给 8000 加 iptables `! -i lo` 那条**，镜像模式下会把自己也挡住。
3. **引擎 API 无鉴权**（能读出助记词）：只许本机 loopback，永不公网。
4. 从 git-bash 里给 WSL 传命令时，`\$var` 会被吞掉 → **一律写脚本文件再 `bash file.sh`**。
5. 写进 WSL 的脚本要先 `sed -i 's/\r$//'` 去掉 CRLF。
6. 引擎日志里 `no authentication` 是预期警告，不是错误。

## 6. 还没解决 / 下一轮要干

**下一轮 = M5，逐项清单在 `docs/M5_PLAN.md`（照它勾）**。这里只留"坑"和"已知局限"：

1. ✅ ~~测试网拿币~~ → **绕过**：直接用主网真钱跑（DEMO-01 总共只花 ≈0.001 ZEC 手续费）。
2. ✅ ~~真 memo 端到端~~ → **已推翻该路线**：引擎对本钱包收到的 orchard note `memo` 恒 `null`，
   `memosByTransaction` 返回 `[]` → 协议改成「**金额即出价**」，memo 降级为装饰。
   ⚠️ **不要再回去试 memo 出价**，会浪费一整轮。
3. ✅ 揭标 CLI 已用真实数据跑过（`docs/demo_01_settlement.json`，含 commit/salt 承诺）。
   - ⚠️ **留着的诚实局限**（写进 SPEC/README，别藏）：第三方**不可能**验算"卖家有没有改公布金额"
     （金额本身加密，这是隐私的代价）。已给的是**出价人自查**（拿自己 commit/salt 对名单）+ 明文写入 SPEC。
4. ⏳ 录 2 分钟 demo（M5.2；旁白用 TTS，用户只需确认稿 + 点发布）。
5. ⏳ README/仓库定稿（M5.1；含安全自查：`git log --all | grep -i mnemonic` 必须为空）。
6. ⏳ 提交：thezecathon.com → SUBMIT PROJECT（表单 JS 渲染，用调试浏览器填，**👤 点提交**）。

## 7. 定位一句话（对外口径）

> Zilkroad 的 `/bids` 把出价**摊在桌面上**（金额、总额、均价人人可见）；
> ShieldBid 用 Zcash 屏蔽转账 + 加密 memo，把同一件事**锁进密室**：
> 只有卖家看得到金额，截止后只公布清算价与名次，输家的金额和身份永不公开。
> 不是另做一个拍卖站，是给市场补上缺的那一层隐私。
