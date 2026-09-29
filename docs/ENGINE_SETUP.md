# ShieldBid local engine (WSL + zkool_graphql) — setup & operations

> This document records the full "install once, rebuild by copy-paste later" procedure.
> Everything runs on Windows 11 under git-bash; the `wsl.exe` commands can be copied verbatim.

## 1. Why it is needed

ShieldBid's seller side has to **read the memo inside a shielded transfer** (that memo *is* the bid).
Only a wallet can decrypt a memo, so the machine must run a **real Zcash wallet engine**:

- `zkool_graphql` (the headless GraphQL build of Zkool — a single 114 MB Linux x86_64 binary)
- it talks to public lightwalletd nodes (no full-chain download, starts in seconds)
- it exposes exactly two ports: `8000` = mainnet, `8001` = testnet

The Windows-side Python tools (`tools/engine.py`, `tools/shieldbid.py`) talk to it over
`http://127.0.0.1:<port>/graphql`.

## 2. Installing WSL (every pitfall we hit is here)

The Store version of Ubuntu installed on this machine **refuses to start**
(`Wsl/Service/E_UNEXPECTED`). Do not fight it — **import the official rootfs manually**,
which worked first try:

```bash
# 1) download the official Ubuntu base (~30 MB); needs a working CA store
mkdir -p /c/WSL
curl -sL -o C:/WSL/ubuntu-base.tar.gz \
  https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/ubuntu-base-24.04.3-base-amd64.tar.gz

# 2) import it as a distro named shieldbid
wsl --import shieldbid "C:\WSL\shieldbid" "C:\WSL\ubuntu-base.tar.gz" --version 2

# 3) enter it (as root; no user account, no password needed)
wsl -d shieldbid -u root -- bash -lc "cat /etc/os-release; uname -r"
```

> Note: if a broken Store install is already present, clear it with `wsl --unregister Ubuntu`.

## 3. Networking: mirrored mode (critical)

A proxy runs on the Windows host (`127.0.0.1:7897`). Under WSL's default NAT mode **all HTTPS is
MITM-decrypted by the proxy** (curl fails with `self-signed certificate in certificate chain`).
The fix is to put WSL on a mirrored network:

`C:\Users\XiaoSS\.wslconfig`
```ini
[wsl2]
networkingMode=mirrored
autoProxy=true
dnsTunneling=true
```

Then `wsl --shutdown` and start again. Result:

- direct connections are clean (valid certificate chain) and the proxy still works (CONNECT tunnel, no decryption)
- `127.0.0.1:8000` inside WSL **is reachable from Windows at the very same address**
- the port is **not** exposed to the LAN (measured on this machine: both 192.168.1.197 and 172.18.96.1 refused)

### Pitfall: never send loopback requests through the proxy
`http_proxy` is injected inside WSL, and `no_proxy=127.*` does **not necessarily match** 127.0.0.1,
so requests to the local engine get pushed into the 7897 proxy and come back **HTTP 502**
(which looks exactly like a dead service).

- curl: add `--noproxy '*'`
- Python: `urllib.request.build_opener(urllib.request.ProxyHandler({}))` (both tools already do this)

### Pitfall: do not add this iptables rule in mirrored mode
`iptables -A INPUT -p tcp --dport 8000 ! -i lo -j DROP` **blocks the host itself too** (in mirrored
mode loopback traffic does not arrive on `lo`). Measured — do not add it.

## 4. Installing and starting the engine

```bash
wsl -d shieldbid -u root -- bash -lc "
  cd /root
  curl -sL -o zkool_graphql https://github.com/hhanh00/zkool2/releases/download/zkool-v6.31.0/zkool_graphql
  chmod +x zkool_graphql
  # mainnet
  setsid ./zkool_graphql -d /root/sb_main.db -l https://zec.rocks:443 -p 8000 > /root/engine.log 2>&1 &
  # testnet (for dry runs, costs nothing)
  setsid ./zkool_graphql -d /root/sb_test.db -l https://testnet.zec.rocks:443 -p 8001 -C 1 > /root/engine_test.log 2>&1 &
"
```

Health check:

```bash
wsl -d shieldbid -u root -- bash -lc "pgrep -a zkool_graphql; tail -3 /root/engine.log"
cd ~/shieldbid && python tools/engine.py height --net mainnet && python tools/engine.py height --net testnet
```

## 5. Wallets and mnemonics (red lines)

- Seller mainnet wallet: account 1, mnemonic at WSL `/root/.sb_seller_mnemonic` (`chmod 600`)
- Seller testnet wallet: account 1 (testnet DB), mnemonic at `/root/.sb_test_seller_mnemonic`
- Mnemonics are **generated inside WSL only**: never printed, never pasted into a chat, never committed
  to git (`.gitignore` covers them)
- Wallet data lives in `/root/sb_main.db` and `/root/sb_test.db` (SQLite)
- The engine API has **no authentication** (its own warning says so: whoever can reach it has full
  rights, including reading the mnemonic out). Therefore: **loopback access only** — never expose it
  to the public internet.

## 6. Restart (after a reboot or after WSL was shut down)

```bash
wsl -d shieldbid -u root -- bash -lc "pgrep -a zkool_graphql || (cd /root && \
  setsid ./zkool_graphql -d /root/sb_main.db -l https://zec.rocks:443 -p 8000 > /root/engine.log 2>&1 & \
  setsid ./zkool_graphql -d /root/sb_test.db -l https://testnet.zec.rocks:443 -p 8001 -C 1 > /root/engine_test.log 2>&1 &)"
```

The repo also ships `tools/engine_up.sh`, which wraps the command above.

## 7. Engine GraphQL cheat sheet (all verified against the live engine)

| Purpose | Call |
|---|---|
| Chain height | `{ currentHeight }` |
| Account list | `{ accounts { id name seed height balance } }` |
| Addresses | `{ addressByAccount(idAccount:1) { ua orchard sapling transparent } }` |
| **Read bids** (the core call) | `{ notesByAccount(idAccount:1) { height value pool memo tx { txid } } }` |
| Create wallet | `mutation { createAccount(newAccount:{name,key(mnemonic),passphrase:"",aindex:0,birth,pools,useInternal:false}) }` |
| Sync | `mutation { synchronizeAccount(idAccount:1, fast:true) }` |
| **Send a shielded payment with a memo** | `mutation($a:Int!,$p:Payment!){ pay(idAccount:$a, payment:$p) }` |

`Payment` input: `{ recipients: [{ address, amount, memo }] }`.
The `memo` field of `pay` carries the bid in plaintext (e.g. `BID 1.5`), max 512 bytes, and may only
be sent to a shielded address (a transparent recipient returns
`Cannot send memo to transparent recipient`).

The full archived schema: `docs/zkool_graphql_schema_full.json`.

## 8. A real bidding round, command by command

```bash
# seller: fetch the receiving shielded address (the auction address)
python tools/engine.py addresses --net mainnet --account 1

# bidder: send one shielded payment with a memo (the amount is arbitrary; the memo is the bid)
python tools/engine.py bid --net mainnet --account 2 \
  --to <seller orchard address> --amount 0.01 --memo "BID 1.5"

# seller: sync, then read every bid received
python tools/engine.py sync --net mainnet --account 1 --balance
python tools/engine.py bids --net mainnet --account 1 --json
```
