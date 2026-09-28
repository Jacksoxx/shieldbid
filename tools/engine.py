#!/usr/bin/env python3
"""engine.py - thin CLI for the ShieldBid local Zcash engine (zkool_graphql in WSL).

Two engines are expected:
  mainnet -> http://127.0.0.1:8000/graphql   (db /root/sb_main.db, lwd https://zec.rocks:443)
  testnet -> http://127.0.0.1:8001/graphql   (db /root/sb_test.db, lwd https://testnet.zec.rocks:443)

Every call bypasses system proxies on purpose: on this machine a local HTTP proxy
(127.0.0.1:7897) otherwise swallows loopback traffic and answers 502.

Seller side  : accounts / addresses / sync / bids   (read the sealed memos)
Bidder side  : bid                                    (send a shielded payment + memo)
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from decimal import Decimal
from pathlib import Path

PORTS = {"mainnet": 8000, "testnet": 8001}


def url_for(net: str, port: int | None) -> str:
    p = port or PORTS.get(net, 8000)
    return f"http://127.0.0.1:{p}/graphql"


def gql(url: str, query: str, variables: dict | None = None, timeout: int = 300) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
    return data["data"]


Q_ACCOUNTS = "{ accounts { id name height balance } }"
Q_ADDR = "query($a:Int!){ addressByAccount(idAccount:$a){ ua orchard sapling transparent diversifierIndex } }"
Q_BAL = "query($a:Int!){ balanceByAccount(idAccount:$a){ height total orchard sapling transparent } }"
M_SYNC = "mutation($a:Int!){ synchronizeAccount(idAccount:$a, fast:true) }"
M_PAY = "mutation($a:Int!,$p:Payment!){ pay(idAccount:$a, payment:$p) }"

Q_NOTES = """
query($a:Int!){
  notesByAccount(idAccount:$a){
    id height pool value address memo
    tx { txid height time }
  }
}"""


def cmd_accounts(a) -> int:
    d = gql(url_for(a.net, a.port), Q_ACCOUNTS)
    for acc in d["accounts"]:
        print(f'{acc["id"]:>3}  {acc["name"]:<22} height={acc["height"]}  {acc["balance"]} ZEC')
    return 0


def cmd_addresses(a) -> int:
    d = gql(url_for(a.net, a.port), Q_ADDR, {"a": a.account})
    addr = d["addressByAccount"]
    for k, v in addr.items():
        print(f"{k:>18}: {v}")
    return 0


def cmd_sync(a) -> int:
    print("synced to height", gql(url_for(a.net, a.port), M_SYNC, {"a": a.account})["synchronizeAccount"])
    return cmd_balance(a) if a.balance else 0


def cmd_balance(a) -> int:
    d = gql(url_for(a.net, a.port), Q_BAL, {"a": a.account})["balanceByAccount"]
    print(f'height={d["height"]} total={d["total"]} orchard={d["orchard"]} '
          f'sapling={d["sapling"]} transparent={d["transparent"]}')
    return 0


def cmd_notes(a) -> int:
    """Raw note dump (debugging): every received note, memo shown or marked empty."""
    d = gql(url_for(a.net, a.port), Q_NOTES, {"a": a.account})
    for n in d["notesByAccount"]:
        memo = (n.get("memo") or "").strip()
        tx = n.get("tx") or {}
        print(f'pool={n["pool"]} height={n["height"]} value={n["value"]} '
              f'txid={(tx.get("txid") or "")[:16]} memo="{memo[:80]}"')
    return 0


def cmd_bids(a) -> int:
    """Seller side: every received shielded note whose memo is a ShieldBid line."""
    d = gql(url_for(a.net, a.port), Q_NOTES, {"a": a.account})
    rows = []
    for n in d["notesByAccount"]:
        memo = (n.get("memo") or "").strip()
        if not memo:
            continue
        tx = n.get("tx") or {}
        rows.append({"txid": tx.get("txid"), "height": n["height"],
                     "memo": memo, "value": n["value"]})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"{len(rows)} note(s) carry a memo")
        for r in rows:
            print(f'  h{r["height"]}  {r["value"]} ZEC  "{r["memo"][:60]}"  {(r["txid"] or "")[:16]}')
    if a.out:
        Path(a.out).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print("wrote", a.out)
    return 0


QW = Path(__file__).with_name("bip39_english.txt")


def new_mnemonic() -> str:
    """24-word BIP-39 mnemonic, generated locally. Only ever written to a key file."""
    import hashlib
    import secrets
    words = QW.read_text(encoding="utf-8").split()
    ent = secrets.token_bytes(32)
    bits = "".join(f"{b:08b}" for b in ent) + f"{hashlib.sha256(ent).digest()[0]:08b}"
    return " ".join(words[int(bits[i * 11:(i + 1) * 11], 2)] for i in range(24))


def cmd_newaccount(a) -> int:
    """Create a wallet account in the engine, with a fresh mnemonic saved to a key file."""
    slug = "".join(c if c.isalnum() else "_" for c in a.name).lower()
    key_file = Path(a.key_file) if a.key_file else Path.home() / ".shieldbid" / f"{slug}.mnemonic"
    if a.mnemonic_file:
        mn = Path(a.mnemonic_file).read_text(encoding="utf-8").strip()
    else:
        mn = new_mnemonic()
    height = gql(url_for(a.net, a.port), "{ currentHeight }")["currentHeight"]
    newacc = {"name": a.name, "key": mn, "passphrase": "", "aindex": a.aindex,
              "birth": height - 5, "pools": 7, "useInternal": False}
    aid = gql(url_for(a.net, a.port),
              "mutation C($n: NewAccount!){ createAccount(newAccount: $n) }",
              {"n": newacc})["createAccount"]
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(mn + "\n", encoding="utf-8")
    try:
        key_file.chmod(0o600)
    except OSError:
        pass
    print(f"created account {aid} ({a.name}) at height {height}")
    print(f"mnemonic -> {key_file}   (the only way to recover funds; never paste it anywhere)")
    return cmd_addresses(argparse.Namespace(net=a.net, port=a.port, account=aid))


def cmd_shield(a) -> int:
    """Move an account's transparent funds into its own orchard pool (single tx).

    Bidders who receive ZEC on a t-address (e.g. withdrawn from an exchange) shield it
    first, so the bid itself leaves the orchard pool as a fully shielded z->z payment.
    """
    bal = gql(url_for(a.net, a.port), Q_BAL, {"a": a.account})["balanceByAccount"]
    addr = gql(url_for(a.net, a.port), Q_ADDR, {"a": a.account})["addressByAccount"]
    amount = Decimal(a.amount) if a.amount else Decimal(bal["transparent"]) - Decimal("0.0002")
    if amount <= 0:
        print(f"nothing to shield: transparent balance {bal['transparent']} ZEC", file=sys.stderr)
        return 1
    payment = {"recipients": [{"address": addr["orchard"], "amount": str(amount)}], "srcPools": 0}
    if a.dry_run:
        print(json.dumps({"query": M_PAY, "variables": {"a": a.account, "p": payment}},
                         ensure_ascii=False, indent=2))
        return 0
    print("shield txid:", gql(url_for(a.net, a.port), M_PAY, {"a": a.account, "p": payment})["pay"])
    print(f"moved {amount} ZEC from transparent -> orchard of account {a.account}")
    return 0


def cmd_bid(a) -> int:
    """Bidder side: send a shielded payment whose memo is the sealed bid."""
    memo = a.memo
    if a.memo_file:
        memo = Path(a.memo_file).read_text(encoding="utf-8").strip()
    if memo is None:
        print("need --memo or --memo-file", file=sys.stderr)
        return 2
    rec = {"address": a.to, "amount": str(Decimal(a.amount))}
    if memo:
        rec["memo"] = memo
    payment = {"recipients": [rec]}
    if a.src_pools is not None:
        payment["srcPools"] = a.src_pools
    if a.dry_run:
        print(json.dumps({"query": M_PAY, "variables": {"a": a.account, "p": payment}},
                         ensure_ascii=False, indent=2))
        return 0
    txid = gql(url_for(a.net, a.port), M_PAY, {"a": a.account, "p": payment})["pay"]
    print("broadcast txid:", txid)
    print("memo:", memo.splitlines()[0][:120])
    return 0


BECH_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values):
    gen = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    chk = 1
    for v in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            if (top >> i) & 1:
                chk ^= gen[i]
    return chk


def _bech32_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _base58_decode(s):
    alpha = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = 0
    for ch in s:
        n = n * 58 + alpha.index(ch)
    pad = len(s) - len(s.lstrip("1"))
    return b"\x00" * pad + n.to_bytes((n.bit_length() + 7) // 8, "big")


def check_address(addr: str) -> dict:
    """Offline address sanity check. Catches typos BEFORE money moves.

    Unified/shielded addresses (u1..., utest1...) are Bech32m; the 90-char limit of
    plain Bech32 does not apply to UAs (ZIP-316), so we verify the checksum and shape only.
    Transparent addresses (t1/t3) are Base58Check.
    """
    a = addr.strip()
    out = {"address": a, "length": len(a)}
    if not a:
        return {**out, "ok": False, "why": "empty"}
    low = a.lower()
    if low.startswith(("u1", "utest1", "uregtest1", "ztestsapling", "zs1")):
        if a.lower() != a and a.upper() != a:
            return {**out, "ok": False, "why": "mixed case (bech32 must be uniform case)"}
        pos = low.rfind("1")
        hrp, data = low[:pos], low[pos + 1:]
        if hrp not in ("u", "utest", "uregtest", "ztestsapling", "zs") or len(data) < 7:
            return {**out, "ok": False, "why": "bad prefix or too short"}
        vals = []
        for ch in data:
            if ch not in BECH_CHARSET:
                return {**out, "ok": False, "why": f"illegal char {ch!r}"}
            vals.append(BECH_CHARSET.index(ch))
        ok_chk = _bech32_polymod(_bech32_expand(hrp) + vals) == 0x2BC830A3
        payload_bits = len(vals) - 6
        return {**out, "ok": ok_chk, "kind": "shielded/UA (bech32m)", "hrp": hrp,
                "payload_bytes": (payload_bits * 5) // 8,
                "why": "bech32m checksum OK" if ok_chk else "CHECKSUM MISMATCH - typo?"}
    if low.startswith(("t1", "t3", "tm", "t2")):
        try:
            raw = _base58_decode(a)
        except ValueError as e:
            return {**out, "ok": False, "why": f"base58 decode failed: {e}"}
        good = len(raw) == 26 and hashlib.sha256(hashlib.sha256(raw[:-4]).digest()).digest()[:4] == raw[-4:]
        return {**out, "ok": good, "kind": "transparent (base58check)",
                "why": "base58check OK" if good else "CHECKSUM MISMATCH - typo?"}
    return {**out, "ok": False, "why": "unrecognized address prefix"}


def cmd_validate(a) -> int:
    for addr in a.address:
        r = check_address(addr)
        flag = "OK  " if r["ok"] else "BAD "
        print(f"{flag}{r.get('kind', '?')} len={r['length']} {r.get('why', '')}")
        print(f"     {addr}")
    return 0 if all(check_address(x)["ok"] for x in a.address) else 1


def cmd_send(a) -> int:
    """Settlement side: a plain shielded payment with no memo.

    This is the refund leg — losers get their escrow back as a z->z shielded payment,
    and the bidder's own address is the only thing the seller needs (no identity link).
    """
    rec = {"address": a.to, "amount": str(Decimal(a.amount))}
    if a.memo:
        rec["memo"] = a.memo
    payment = {"recipients": [rec]}
    if a.src_pools is not None:
        payment["srcPools"] = a.src_pools
    if a.dry_run:
        print(json.dumps({"query": M_PAY, "variables": {"a": a.account, "p": payment}},
                         ensure_ascii=False, indent=2))
        return 0
    txid = gql(url_for(a.net, a.port), M_PAY, {"a": a.account, "p": payment})["pay"]
    print("broadcast txid:", txid)
    print(f"sent {Decimal(a.amount)} ZEC -> {a.to}  (no memo: private refund)")
    return 0


def main(argv=None) -> int:
    # --net/--port are accepted both before and after the subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--net", choices=list(PORTS), default=argparse.SUPPRESS)
    common.add_argument("--port", type=int, default=argparse.SUPPRESS)

    ap = argparse.ArgumentParser(prog="engine", description="ShieldBid engine CLI",
                                 parents=[common])
    ap.set_defaults(net="mainnet", port=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name, fn in (("accounts", cmd_accounts), ("height", None)):
        p = sub.add_parser(name, parents=[common])
        if fn:
            p.set_defaults(f=fn)

    p = sub.add_parser("addresses", parents=[common]); p.add_argument("--account", type=int, required=True); p.set_defaults(f=cmd_addresses)
    p = sub.add_parser("balance", parents=[common]); p.add_argument("--account", type=int, required=True); p.set_defaults(f=cmd_balance)
    p = sub.add_parser("sync", parents=[common]); p.add_argument("--account", type=int, required=True)
    p.add_argument("--balance", action="store_true"); p.set_defaults(f=cmd_sync)
    p = sub.add_parser("notes", parents=[common]); p.add_argument("--account", type=int, required=True); p.set_defaults(f=cmd_notes)
    p = sub.add_parser("bids", parents=[common]); p.add_argument("--account", type=int, required=True)
    p.add_argument("--json", action="store_true"); p.add_argument("--out")
    p.set_defaults(f=cmd_bids)
    p = sub.add_parser("newaccount", parents=[common]); p.add_argument("--name", required=True)
    p.add_argument("--aindex", type=int, default=0); p.add_argument("--key-file")
    p.add_argument("--mnemonic-file"); p.set_defaults(f=cmd_newaccount)
    p = sub.add_parser("shield", parents=[common]); p.add_argument("--account", type=int, required=True)
    p.add_argument("--amount"); p.add_argument("--dry-run", action="store_true"); p.set_defaults(f=cmd_shield)
    p = sub.add_parser("bid", parents=[common]); p.add_argument("--account", type=int, required=True)
    p.add_argument("--to", required=True); p.add_argument("--amount", required=True)
    p.add_argument("--memo"); p.add_argument("--memo-file"); p.add_argument("--src-pools", type=int)
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(f=cmd_bid)
    p = sub.add_parser("send", parents=[common]); p.add_argument("--account", type=int, required=True)
    p.add_argument("--to", required=True); p.add_argument("--amount", required=True)
    p.add_argument("--memo"); p.add_argument("--src-pools", type=int)
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(f=cmd_send)
    p = sub.add_parser("validate", parents=[common]); p.add_argument("address", nargs="+")
    p.set_defaults(f=cmd_validate)

    a = ap.parse_args(argv)
    if a.cmd == "height":
        print(gql(url_for(a.net, a.port), "{ currentHeight }")["currentHeight"])
        return 0
    return a.f(a)


if __name__ == "__main__":
    raise SystemExit(main())
