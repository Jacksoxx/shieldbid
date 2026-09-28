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


def cmd_bid(a) -> int:
    """Bidder side: send a shielded payment whose memo is the sealed bid."""
    memo = a.memo
    if a.memo_file:
        memo = Path(a.memo_file).read_text(encoding="utf-8").strip()
    if not memo:
        print("need --memo or --memo-file", file=sys.stderr)
        return 2
    payment = {"recipients": [{"address": a.to, "amount": str(Decimal(a.amount)), "memo": memo}]}
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
    p = sub.add_parser("bid", parents=[common]); p.add_argument("--account", type=int, required=True)
    p.add_argument("--to", required=True); p.add_argument("--amount", required=True)
    p.add_argument("--memo"); p.add_argument("--memo-file"); p.add_argument("--src-pools", type=int)
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(f=cmd_bid)

    a = ap.parse_args(argv)
    if a.cmd == "height":
        print(gql(url_for(a.net, a.port), "{ currentHeight }")["currentHeight"])
        return 0
    return a.f(a)


if __name__ == "__main__":
    raise SystemExit(main())
