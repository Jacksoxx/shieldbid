# 暗标行动 · HANDOFF

> **用法**：新会话第一句话发「**暗标 继续**」，我先读这个文件再开工。
> 最后更新：2026-09-29（M1 完成）

## 0. 这是什么

用户（松松，Qihao Xiao，X 大号 JACKSOxx，**完全不懂代码**）参加 **ZECATHON**（Zcash 隐私黑客松，$10 万奖金池）的参赛作品。
赛道：**PRIVATE MARKETS**。作品：**ShieldBid —— 密封竞价台**。

- 截标：**2026-10-28 23:59 UTC**
- 提交账号：站点 handle **@JACKSOxx**（Google 登录 **xiaoqihao2@gmail.com**，姓名 Qihao Xiao，Telegram @jacksoxx，国家 China）
- 站点：https://thezecathon.com/ （注册已完成，赛道未选，提交时才勾）
- 分工：**代码/部署/文档/demo 全部由助手做**，用户只做：注册（已完成）、demo 时当一次出价人、10/28 点提交。
- 红线：不连钱包、不签名、不点 claim；私钥不进聊天；助手不碰用户密码。

## 1. 一句话产品

出价 = 一笔**屏蔽（z→z）转账 + memo 里写 `BID 1.55`**。金额只有卖家能读；
截止后卖家**只公布清算价和名次**，输家的金额和身份永不公开；截止时对全部封标做哈希承诺，防赖皮。

**为什么是这个**：主办方自己的市场把报价全公开（实测 `/bids` 16 条公开报价共 22.71 ZEC ≈ $34,928），
而且他们那场"盲拍"官方原话是"截止前可随时查看或提高出价"、有玩家原话"连续分析了别人出价 7 小时后才提交"。
他们的赛道原话就是 *sealed-bid auctions … price should be public and the participants should not*。
→ 我们是**补他们的洞，不是另开一个市场**（不撞车、不违反"existing products are not"规则）。

## 2. 技术脊柱（都已核实到源码级，别重新怀疑）

| 事实 | 证据 |
|---|---|
| memo **只能**挂 z→z 屏蔽转账，上限 **512 字节**；往透明地址发 memo 会被拒 | Zallet 源码 `MAX_MEMO_BYTES = 512`、`Cannot send memo to transparent recipient` |
| 卖家读金额路径 A（官方换代栈）| Zallet RPC `z_listunspent` 每条返回 **`memoStr`**（`list_unspent.rs`）；`z_viewtransaction` 同样带 memo |
| 卖家读金额路径 B（本机可跑，**Windows 友好**）| Zkool GraphQL：`Transaction.outputs { pool vout value address memo }`（`rust/src/graphql/query.rs`）；发款 `pay(recipients:[{address,amount,memo}])` |
| 本机环境 | 有 python/git；**无 Docker、无 WSL 发行版、无 Rust**。Zallet 只发 Linux 二进制 → 本机走 Zkool 轻客户端（连公共 lightwalletd，**不需要全节点**） |
| 公共 lightwalletd | `zec.rocks` / `na.lightwalletd.com` / `eu.lightwalletd.com` / `mainnet.lightwalletd.com` TCP 443 全通 |
| 出价人门槛 | ✅ Zashi / Zkool / Ywallet / Zingo（有备注栏）；❌ 交易所提币、OKX Web3 钱包（无备注栏） |

**诚实局限（必须写进 README，别美化）**：卖家仍是可信方；实时最高价做不到（金额加密）；NFT/资产交割不在范围内。

## 3. 目录与产物

- 仓库：`C:\Users\XiaoSS\shieldbid`（git 已初始化，M1 已提交 `97765bb`）
  - `README.md`、`LICENSE`(MIT)、`.gitignore`
  - `docs/SPEC.md` —— 协议 v0.1（memo 格式、承诺公式、reveal.json schema、验算步骤、威胁模型）
  - `docs/BIDDER_GUIDE.md` —— 出价人教程（截图待补）
  - `web/index.html` —— 竞价台（单文件、暗色、可直接上 GitHub Pages）
  - `docs/board_v0.png` —— M1 页面截图
- 方案书：`C:\Users\XiaoSS\snowmoon\zecathon\PLAN_v1.md`
- 注册取证：`C:\Users\XiaoSS\snowmoon\zecathon\site_pages_logged_in.txt`

## 4. 里程碑（用户要求：到点提醒他开新会话）

| # | 内容 | 状态 |
|---|---|---|
| M1 | 仓库 + 协议 v0.1 + 竞价台页面 + 出价人教程 | ✅ 2026-09-29 |
| M2 | **真钱包发真 memo → 卖家读到**（主网极小金额或测试网，先跑通再谈自动化）| ⬜ 下一步 |
| M3 | 揭标 CLI `tools/shieldbid.py`（引擎：zkool / manual 两种）+ 承诺哈希 + 排名/退款清单 | ⬜ |
| M4 | `tools/verify_reveal.py` + 页面上线（GitHub Pages）+ README 收尾 | ⬜ |
| M5 | 2 分钟 demo 视频 + 找外人按教程复测 | ⬜ |
| M6 | 10/28 用户点提交（内容全部备好） | ⬜ |

## 5. 下一步（M2 具体动作）

1. 装 `zkool_graphql` 引擎（Linux 二进制 → 需要 WSL 或最便宜的小服务器；**动系统前先问用户**）。
   - 备选：Zkool 桌面版（Windows .exe）人工看 memo —— 不装任何东西，但揭标不自动。
2. 卖家侧建一个**新钱包**（专用于本作品），拿到 UA，写进 `web/index.html` 的 lot 数据。
3. 用户手机装 Zashi（或 Zkool），发一笔极小金额带 `BID x` 的 memo 到那个 UA。
4. 用引擎读出 memo → 落盘截图/日志 → M2 完成。
5. demo 资金：**优先测试网**；要真钱就 0.01 ZEC 级（≈$15），用户拍板。

## 6. 花的钱与额度

- 项目本身：**0 元**（测试网或几分钱手续费）。
- AI token：b.ai 余额 14,008,927 积分（9/29 查），本月已用 991,073。整套项目估 100 万–300 万积分。
- **省 token 铁律**：每完成一个里程碑就开新会话（上下文从 10 万降到 1.5 万 ≈ 省 85%）；长文档写文件不刷屏；大文件用脚本读、只回看关键行。

## 7. 浏览器（做任何网页操作时）

fx profile 调试浏览器 `http://127.0.0.1:9223`（X 已登录 @JAcksoxx_x；Google 已登录 xiaoqihao2@gmail.com；chat.b.ai 已登录）。
挂了用 `python ~/AppData/Local/hermes/scripts/start_fx_browser.py` 重启。**绝不另开新 Chrome**。用完随手关标签。
