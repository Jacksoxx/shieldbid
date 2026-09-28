# 🤫 暗标 · ShieldBid — HANDOFF（交接文件）

> **口令：新会话发「暗标 继续」→ 助手的第一个动作是读这份文件。**
> 代号「暗标」，产品名 ShieldBid，赛道 PRIVATE MARKETS，截止 **2026-10-28 23:59 UTC**。

## 0. 现在到哪一步了

- ✅ **M1** 协议规格 + 公开竞价台页面 + 投标人指南 + git 仓库
- ✅ **M2（本轮完成）** 本地 Zcash 引擎跑通：
  - WSL 装好（`shieldbid` 发行版），绕过商店版无法启动的坑（见 `docs/ENGINE_SETUP.md`）
  - `zkool_graphql` 引擎主网(8000)+测试网(8001)在跑，连公共节点
  - **卖家主网钱包**已建（账户 1），拿到 orchard 收款地址
  - **测试网卖家钱包**已建（测试网账户 1）
  - Windows ↔ WSL 打通：`python tools/engine.py` 能直接读链高/账户/地址/余额
  - **验证了核心机制**：memo 能从 `notesByAccount` 直接解密读出（出价就是 memo）
  - 投标路径 dry-run 通过（带 memo 的屏蔽付款请求成形）
- ✅ **M3（本轮完成）** 投标人钱包就位 + 收款口可用了：
  - **主网投标人**：账户 2「SB Bidder A」→ 透明收款 `t1Pm2n2YGULXbZcgXAH3aCsY9mvTNZyD2dB`，
    orchard `u1e6cwevnrssknku3jncgn59jwuztnz9asckcmv0x6ndtcyxesfet5q7djy7n3a06u0trdwchpgs2qqgw086747j7kzlug6yqh0vpjpgyj`
  - **测试网投标人**：账户 2「SB Bidder Test」（tmUQNLuKA95bHgBvuXZ3PyJGmdqoLK8Fz6c）
  - `engine.py` 新增 `newaccount`（本地生成 24 词助记词 → `~/.shieldbid/<name>.mnemonic`，chmod 600）
    与 `shield`（透明 → 自己 orchard，一次性屏蔽，交易所提币进来的第一步）
  - 助记词文件在 **Windows** `C:\Users\XiaoSS\.shieldbid\`（.gitignore 之外，绝不入库）
- ⏭️ **M4（下一步）**：用户转 ~0.02 ZEC 到投标人地址 → 屏蔽 → 发 3 笔**真** memo 出价 → 卖家读出 → 揭标 → 录 demo

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

1. **测试网拿币**：要找 Zcash 测试网水龙头（zecfaucet.com 是 JS 页面，没探到 API）。
   备选：主网真钱（0.01–0.03 ZEC，≈$15–45）直接跑，更省事但花钱。
2. **真 memo 端到端**：测试网或主网，让"投标人钱包 → 卖家地址 + memo → 卖家读出"跑一次真交易。
3. 揭标 CLI 用**真实**数据跑（`shieldbid.py reveal`），加哈希承诺。
   - ⚠️ 遗留：`verify` 的篡改测试目前测不出「卖家改了公布金额」——因为金额本身加密，
     第三方**不可能**验算（这是隐私的代价，不是 bug）。要做的是加**出价人自查**
     （投标人拿自己的 memo 原文核对：是否在名单里 + 公布金额是否与自己的 memo 一致），
     并在 SPEC 写明这条诚实局限。
4. 录 2 分钟 demo 视频（需要用户配合：手机装 Zashi/Zkool、出一次价）。
5. README 定稿（含 `docs/zilkroad_bids_evidence.png` 证据图、诚实局限一节）。
6. 提交：thezecathon.com → SUBMIT PROJECT（名字/赛道/repo/demo 链接），用户点提交。

## 7. 定位一句话（对外口径）

> Zilkroad 的 `/bids` 把出价**摊在桌面上**（金额、总额、均价人人可见）；
> ShieldBid 用 Zcash 屏蔽转账 + 加密 memo，把同一件事**锁进密室**：
> 只有卖家看得到金额，截止后只公布清算价与名次，输家的金额和身份永不公开。
> 不是另做一个拍卖站，是给市场补上缺的那一层隐私。
