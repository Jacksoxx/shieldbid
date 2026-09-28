# ShieldBid 本地引擎（WSL + zkool_graphql）搭建与运维

> 这份文档记录的是「一次装好、以后照着敲就能恢复」的完整流程。
> 全部在 Windows 11 + git-bash 下操作，`wsl.exe` 命令照抄即可。

## 1. 为什么需要它

ShieldBid 的卖家侧要**读出屏蔽转账里的 memo**（出价）。能解密 memo 的只有钱包本身，
所以本地必须跑一个**真正的 Zcash 钱包引擎**：

- `zkool_graphql`（Zkool 的 headless GraphQL 版，114 MB 单文件，Linux x86_64）
- 它连公共 lightwalletd 节点（不下载全链，秒级启动）
- 对外只有两个端口：`8000`=主网，`8001`=测试网

Windows 侧的 Python 工具（`tools/engine.py`、`tools/shieldbid.py`）通过
`http://127.0.0.1:<port>/graphql` 跟它说话。

## 2. 装 WSL（踩过的坑都在这里）

商店版 Ubuntu 在本机装上后**无法启动**（`Wsl/Service/E_UNEXPECTED`）。
不要跟它纠缠，直接**手动导入官方 rootfs**，一次成功：

```bash
# 1) 下载官方 Ubuntu base（约 30 MB），要带确认证书可用
mkdir -p /c/WSL
curl -sL -o C:/WSL/ubuntu-base.tar.gz \
  https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/ubuntu-base-24.04.3-base-amd64.tar.gz

# 2) 导入成一个叫 shieldbid 的发行版
wsl --import shieldbid "C:\WSL\shieldbid" "C:\WSL\ubuntu-base.tar.gz" --version 2

# 3) 进去（用 root，不需要建用户、不需要设密码）
wsl -d shieldbid -u root -- bash -lc "cat /etc/os-release; uname -r"
```

> 注意：如果之前装过坏掉的商店版，可以用 `wsl --unregister Ubuntu` 清掉。

## 3. 网络：镜像模式（关键）

本机 Windows 上跑着代理（`127.0.0.1:7897`）。WSL 默认 NAT 模式下**所有 HTTPS 会被代理中间人
解密**（curl 报 `self-signed certificate in certificate chain`）。解决办法是让 WSL 走镜像网络：

`C:\Users\XiaoSS\.wslconfig`
```ini
[wsl2]
networkingMode=mirrored
autoProxy=true
dnsTunneling=true
```

改完 `wsl --shutdown` 再启动。效果：

- 直连干净（证书链正常），代理也可用（走 CONNECT 隧道，不解密）
- WSL 里的 `127.0.0.1:8000` **在 Windows 上同一个地址能直接访问**
- **不会**把端口暴露到局域网（本机实测 192.168.1.197 / 172.18.96.1 都连不上）

### 坑：loopback 请求别走代理
WSL 内部的 `http_proxy` 会被自动注入，而 `no_proxy=127.*` **不一定匹配** 127.0.0.1，
于是对本地引擎的请求会被丢到 7897 代理上，返回 **HTTP 502**（看起来像服务挂了）。

- curl：加 `--noproxy '*'`
- Python：`urllib.request.build_opener(urllib.request.ProxyHandler({}))`（两个工具都已内置）

### 坑：不要在镜像模式里加这条 iptables
`iptables -A INPUT -p tcp --dport 8000 ! -i lo -j DROP` 会**连本机自己都挡掉**（镜像模式下
回环流量不是从 `lo` 进来的）。已经实测过，别加。

## 4. 装引擎并启动

```bash
wsl -d shieldbid -u root -- bash -lc "
  cd /root
  curl -sL -o zkool_graphql https://github.com/hhanh00/zkool2/releases/download/zkool-v6.31.0/zkool_graphql
  chmod +x zkool_graphql
  # 主网
  setsid ./zkool_graphql -d /root/sb_main.db -l https://zec.rocks:443 -p 8000 > /root/engine.log 2>&1 &
  # 测试网（免费跑流程用）
  setsid ./zkool_graphql -d /root/sb_test.db -l https://testnet.zec.rocks:443 -p 8001 -C 1 > /root/engine_test.log 2>&1 &
"
```

自检：

```bash
wsl -d shieldbid -u root -- bash -lc "pgrep -a zkool_graphql; tail -3 /root/engine.log"
cd ~/shieldbid && python tools/engine.py height --net mainnet && python tools/engine.py height --net testnet
```

## 5. 钱包与助记词（红线）

- 卖家主网钱包：账户 1，助记词在 WSL `/root/.sb_seller_mnemonic`（`chmod 600`）
- 卖家测试网钱包：账户 1（测试网库），助记词 `/root/.sb_test_seller_mnemonic`
- 助记词**只在 WSL 本地生成**：不打印、不进聊天记录、不进 git（`.gitignore` 已屏蔽）
- 钱包数据在 `/root/sb_main.db`、`/root/sb_test.db`（SQLite）
- 引擎 API **没有鉴权**（警告里写了：能访问的人拿到全部权限，包括读出助记词）。
  所以：**只许 loopback 访问**，永远不要把它暴露到公网。

## 6. 重启（电脑重启 / WSL 被关之后）

```bash
wsl -d shieldbid -u root -- bash -lc "pgrep -a zkool_graphql || (cd /root && \
  setsid ./zkool_graphql -d /root/sb_main.db -l https://zec.rocks:443 -p 8000 > /root/engine.log 2>&1 & \
  setsid ./zkool_graphql -d /root/sb_test.db -l https://testnet.zec.rocks:443 -p 8001 -C 1 > /root/engine_test.log 2>&1 &)"
```

也可以用仓库里的 `tools/engine_up.sh`（封装了上面这段）。

## 7. 引擎 GraphQL 速查（实测通过）

| 用途 | 调用 |
|---|---|
| 链高度 | `{ currentHeight }` |
| 账户列表 | `{ accounts { id name seed height balance } }` |
| 地址 | `{ addressByAccount(idAccount:1) { ua orchard sapling transparent } }` |
| **读出价**（核心） | `{ notesByAccount(idAccount:1) { height value pool memo tx { txid } } }` |
| 新建钱包 | `mutation { createAccount(newAccount:{name,key(mnemonic),passphrase:"",aindex:0,birth,pools,useInternal:false}) }` |
| 同步 | `mutation { synchronizeAccount(idAccount:1, fast:true) }` |
| **发带 memo 的屏蔽付款** | `mutation($a:Int!,$p:Payment!){ pay(idAccount:$a, payment:$p) }` |

`Payment` 输入：`{ recipients: [{ address, amount, memo }] }`。
`pay` 的 `memo` 就是出价明文（如 `BID 1.5`），上限 512 字节，只能发给屏蔽地址
（透明地址会报 `Cannot send memo to transparent recipient`）。

完整 schema 已存档：`docs/zkool_graphql_schema_full.json`。

## 8. 一次真实的出价流程（命令级）

```bash
# 卖家：拿收款屏蔽地址（拍卖地址）
python tools/engine.py addresses --net mainnet --account 1

# 投标人：发一笔带 memo 的屏蔽付款（金额随便，memo 是真正的出价）
python tools/engine.py bid --net mainnet --account 2 \
  --to <卖家orchard地址> --amount 0.01 --memo "BID 1.5"

# 卖家：同步后读出所有出价
python tools/engine.py sync --net mainnet --account 1 --balance
python tools/engine.py bids --net mainnet --account 1 --json
```
