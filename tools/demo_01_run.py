#!/usr/bin/env python3
"""DEMO-01 runner: fund -> sealed bids -> close -> refund, on Zcash mainnet.

Protocol SHIELDBID/1 (escrow-as-bid):

  * one lot = one shielded (z->z) receiving address;
  * a bid = a shielded transfer to that address, and the AMOUNT is the bid;
  * amounts inside the shielded pool are encrypted: no third party can read the
    bid, the bidder, or the number of losing bidders;
  * the lot wallet owns the viewing key, so it reads every bid locally;
  * clearing = uniform price (every winner pays the lowest winning bid), losers
    are refunded in full, winners get their overpayment back;
  * refunds are plain shielded payments, so nothing about the loser ever becomes
    public (not even the amount).

Every step writes to docs/demo_01_ledger.json (the receipts) so the round can be
audited later: chain + receipts = verifiable, amounts stay private to the parties.

Usage:
  python tools/demo_01_run.py status
  python tools/demo_01_run.py fund
  python tools/demo_01_run.py bid --account 2 --amount 0.004 --bidder ROBOT-A
  python tools/demo_01_run.py close
  python tools/demo_01_run.py refund --leg winners|losers|sweep
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import engine  # noqa: E402

LEDGER = REPO / "docs" / "demo_01_ledger.json"
SETTLEMENT = REPO / "docs" / "demo_01_settlement.json"
PRIVATE = Path(os.path.expanduser("~/.shieldbid"))
NET = "mainnet"


# ---------------------------------------------------------------- engine helpers
def url() -> str:
    return engine.url_for(NET, None)


def sync(account: int) -> int:
    return int(engine.gql(url(), engine.M_SYNC, {"a": account}, timeout=600)["synchronizeAccount"])


def balance(account: int) -> Decimal:
    b = engine.gql(url(), engine.Q_BAL, {"a": account})["balanceByAccount"]
    return Decimal(str(b["total"]))


def notes(account: int) -> list[dict]:
    return engine.gql(url(), engine.Q_NOTES, {"a": account})["notesByAccount"]


def addresses(account: int) -> dict:
    return engine.gql(url(), engine.Q_ADDR, {"a": account})["addressByAccount"]


def pay(account: int, to: str, amount: Decimal | str, memo: str | None = None) -> str:
    rec: dict = {"address": to, "amount": str(Decimal(str(amount)))}
    if memo:
        rec["memo"] = memo
    # NOTE (2026-09-29): do NOT pass `srcPools`. The mutation types it as a scalar Int, and any
    # explicit value (3 included) makes the engine answer `No feasible note selection found`
    # because its note-selection then looks in a pool this wallet has no notes in. Omitting it
    # lets the engine pick from the pools we actually hold (orchard). Every funded demo note is
    # orchard, so the chosen - and the resulting output - stay shielded.
    # Also: `confirmations: 1` is required, the engine default is ~10 and then refuses to spend
    # a freshly received note ("No feasible note selection found" again).
    payment = {"recipients": [rec], "confirmations": 1}
    return engine.gql(url(), engine.M_PAY, {"a": account, "p": payment}, timeout=600)["pay"]


# ---------------------------------------------------------------- ledger helpers
def load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def save_ledger(led: dict) -> None:
    LEDGER.write_text(json.dumps(led, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def commit_of(bidder: str, amount: str, salt: str) -> str:
    raw = f"{bidder}|{amount}|{salt}".encode()
    return hashlib.sha256(raw).hexdigest()


def refund_address() -> str:
    p = PRIVATE / "buyer_u1_address.txt"
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("u1") and len(line) > 100:
            return line
    raise SystemExit(f"no U1 refund address found in {p}")


def account_orchard(account: int) -> str:
    return addresses(account)["orchard"]


# ---------------------------------------------------------------- commands
def cmd_status(a) -> int:
    led = load_ledger()
    print(f"auction {led['auction_id']}  protocol {led['protocol']}  slots={led['slots']} "
          f"reserve={led['reserve']} ZEC")
    for bid in led["bids"]:
        print(f"  bid {bid['bidder']:<10} {bid['amount']:>9} ZEC  tx={bid['txid'][:16]}…")
    print("\nwallets (seller=1 holds the escrow, 2/3 are the bidders' wallets):")
    for acct, role in ((1, "LOT/seller"), (2, "bidder A"), (3, "bidder B")):
        h = sync(acct)
        print(f"  account {acct} ({role:<11}) height={h} balance={balance(acct)} ZEC")
    print("\nnotes visible to the lot wallet (account 1) — the sealed bids it can read:")
    for n in notes(1):
        tx = n.get("tx") or {}
        print(f"  value={n['value']:>10} pool={n['pool']} height={n['height']} "
              f"tx={(tx.get('txid') or '')[:16]}…")
    return 0


def cmd_fund(a) -> int:
    """Give bidder B working capital from bidder A's wallet (demo funding leg)."""
    amount = Decimal(a.amount)
    to = account_orchard(3)
    sync(2)
    bal = balance(2)
    print(f"bidder A wallet balance before funding: {bal} ZEC")
    if bal < amount + Decimal("0.0002"):
        raise SystemExit("not enough in account 2 to fund bidder B")
    txid = pay(2, to, amount)
    print(f"funded bidder B with {amount} ZEC  txid={txid}")
    return 0


def cmd_bid(a) -> int:
    """A robot bidder submits a sealed bid: a shielded transfer to the lot wallet."""
    led = load_ledger()
    amount = str(Decimal(a.amount))
    to = account_orchard(1)
    sync(a.account)
    bal = balance(a.account)
    print(f"bidder wallet {a.account} balance before bid: {bal} ZEC")
    if bal < Decimal(amount) + Decimal("0.0002"):
        raise SystemExit(f"wallet {a.account} cannot cover a bid of {amount}")
    txid = pay(a.account, to, amount)
    salt = secrets.token_hex(8)
    led["bids"].append({
        "bidder": a.bidder,
        "amount": amount,
        "txid": txid,
        "height": sync(a.account),
        "how": f"shielded z->z transfer from demo wallet account {a.account} (no memo)",
        "salt": salt,
        "commit": commit_of(a.bidder, amount, salt),
    })
    save_ledger(led)
    print(f"SEALED BID submitted: {a.bidder} -> {amount} ZEC  txid={txid}")
    print("(the amount is encrypted on-chain: no third party can read this bid)")
    return 0


def cmd_close(a) -> int:
    """Seller reads the sealed bids, then publishes the clearing price + receipts."""
    led = load_ledger()
    slots = int(led["slots"])
    reserve = Decimal(str(led["reserve"]))
    # 1. seller reads its own wallet: these are the sealed bids, invisible to outsiders
    received = notes(1)
    total_in = sum(Decimal(str(n["value"])) for n in received)
    print(f"lot wallet holds {len(received)} shielded note(s), total {total_in} ZEC "
          f"(= escrow from the bids, readable only here)")

    # 2. rank the bids from the ledger, cross-checked against the chain
    bids = sorted(led["bids"], key=lambda b: Decimal(str(b["amount"])), reverse=True)
    if len(bids) < slots:
        raise SystemExit("fewer bids than slots - nothing to clear")
    clearing = Decimal(str(bids[slots - 1]["amount"]))
    if clearing < reserve:
        raise SystemExit(f"clearing {clearing} below reserve {reserve}: lot is unsold")

    winners, losers = bids[:slots], bids[slots:]
    plan = []
    for i, b in enumerate(bids, 1):
        amt = Decimal(str(b["amount"]))
        win = i <= slots
        refund = (amt - clearing) if win else amt
        plan.append({
            "rank": i,
            "bidder": b["bidder"],
            "amount": str(amt),
            "result": "win" if win else "lose",
            "pays": str(clearing) if win else "0",
            "refund": str(refund),
            "txid": b["txid"],
            "commit": b.get("commit"),
            "salt": b.get("salt"),
        })

    out = {
        "protocol": led["protocol"],
        "auction_id": led["auction_id"],
        "network": NET,
        "rule": led["settlement_rule"],
        "reserve": str(reserve),
        "slots": slots,
        "bids_received": len(bids),
        "clearing_price": str(clearing),
        "escrow_in_lot_wallet": str(total_in),
        "payout_to_seller": str(clearing * slots),
        "total_refund": str(sum(Decimal(p["refund"]) for p in plan)),
        "privacy_note": ("public: number of bidders is NOT published; losers and their "
                         "amounts are never revealed; only clearing price + winners' rank are"),
        "settlement": plan,
        "closed_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    SETTLEMENT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nCLEARING PRICE = {clearing} ZEC (uniform price, {slots} slots)")
    for p in plan:
        print(f"  #{p['rank']} {p['bidder']:<10} bid {p['amount']:>8} -> {p['result']:<5} "
              f"pays {p['pays']:>8} refund {p['refund']}")
    print(f"\nreceipts written to {SETTLEMENT}")
    return 0


def cmd_refund(a) -> int:
    """Escrow sits in the lot wallet, so every refund leg pays out from account 1."""
    led = load_ledger()
    st = json.loads(SETTLEMENT.read_text(encoding="utf-8"))
    refund_to = refund_address()
    sync(1)
    print(f"lot wallet escrow before refunds: {balance(1)} ZEC")

    legs = [p for p in st["settlement"] if p["result"] == "lose"] if a.leg == "losers" else \
           [p for p in st["settlement"] if p["result"] == "win"] if a.leg == "winners" else []
    for p in legs:
        amt = Decimal(p["refund"])
        if amt <= 0:
            print(f"  {p['bidder']}: pays the clearing price, nothing to refund")
            continue
        dest = account_orchard(2) if p["bidder"] == "ROBOT-A" else refund_to
        txid = pay(1, dest, amt)
        p["refund_txid"] = txid
        label = "user (winner overpayment)" if p["bidder"].startswith("USER") else p["bidder"]
        print(f"  refunded {amt} ZEC to {label}  txid={txid}")
    SETTLEMENT.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if a.leg == "sweep":
        print("\ndemo wind-down: sweeping the demo wallets back to the user's address")
        total = Decimal("0")
        for acct, name in ((1, "lot/seller"), (2, "bidder A"), (3, "bidder B")):
            sync(acct)
            bal = balance(acct)
            fee = Decimal("0.0002")
            if bal <= fee:
                print(f"  account {acct} ({name}): {bal} ZEC - dust, nothing to sweep")
                continue
            send = bal - fee
            txid = pay(acct, refund_to, send)
            total += send
            print(f"  account {acct} ({name}): swept {send} ZEC  txid={txid}")
        print(f"swept {total} ZEC back to the user's address {refund_to[:20]}…")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="demo_01_run", description="ShieldBid DEMO-01 runner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(f=cmd_status)
    p = sub.add_parser("fund"); p.add_argument("--amount", default="0.012"); p.set_defaults(f=cmd_fund)
    p = sub.add_parser("bid")
    p.add_argument("--account", type=int, required=True)
    p.add_argument("--amount", required=True)
    p.add_argument("--bidder", required=True)
    p.set_defaults(f=cmd_bid)
    sub.add_parser("close").set_defaults(f=cmd_close)
    p = sub.add_parser("refund"); p.add_argument("--leg", choices=["winners", "losers", "sweep"],
                                                default="winners"); p.set_defaults(f=cmd_refund)

    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    raise SystemExit(main())
