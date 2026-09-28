#!/usr/bin/env python3
"""DEMO-01 finisher: unattended close -> refunds -> wind-down sweep.

Runs the last three acts of the live demo round and is safe to re-run: every leg
skips work that already has an on-chain receipt (settlement json / refund_txid).

    python tools/demo_01_finish.py

Acts
  1. wait until every sealed-bid escrow note in the lot wallet is spendable (1 conf)
  2. `close`  - seller reads the sealed bids, publishes clearing price + receipts
  3. `refund` - winners' overpayment (user, back to the phone wallet's U1) and the
                loser's full escrow (back to their own demo wallet from the same lot wallet)
  4. wind-down `sweep` - any ZEC still sitting in the three demo wallets goes to the
                user's own shielded address; the demo wallets are left empty
"""
from __future__ import annotations

import json
import sys
import time
from decimal import Decimal
from pathlib import Path

REPO = Path.home() / "shieldbid"
sys.path.insert(0, str(REPO / "tools"))
import demo_01_run as d  # noqa: E402

FEE = Decimal("0.0002")


def log(*a) -> None:
    print(*a, flush=True)


def chain_height() -> int:
    import engine
    return int(engine.gql(d.url(), "{ currentHeight }")["currentHeight"])


def spendable(account: int) -> bool:
    """True when the wallet holds a note with at least one confirmation."""
    d.sync(account)
    notes = d.notes(account)
    if not notes:
        return False
    h = chain_height()
    best = max(int(n["height"]) for n in notes)
    log(f"    acct {account}: {len(notes)} note(s) total={d.balance(account)} ZEC, "
        f"newest h={best}, chain={h}")
    return h - best >= 1


def wait_spendable(account: int, rounds: int = 30, sleep: int = 20) -> bool:
    for _ in range(rounds):
        if spendable(account):
            return True
        time.sleep(sleep)
    return False


def settlement() -> dict:
    return json.loads(d.SETTLEMENT.read_text(encoding="utf-8"))


def act_close() -> None:
    if d.SETTLEMENT.exists():
        st = settlement()
        log(f"  close: already done (clearing price {st['clearing_price']} ZEC)")
        return
    log("  close: seller wallet reads its shielded notes and publishes receipts")
    d.main(["close"])


def act_refund() -> None:
    st = settlement()
    for leg in ("winners", "losers"):
        todo = [p for p in st["settlement"]
                if p["result"] == ("win" if leg == "winners" else "lose")
                and "refund_txid" not in p and Decimal(str(p["refund"])) > 0]
        if not todo:
            log(f"  refund/{leg}: nothing left to pay")
            continue
        log(f"  refund/{leg}: {len(todo)} leg(s)")
        if not wait_spendable(1):
            log("  !! lot wallet never became spendable - stopping before refunds")
            raise SystemExit(1)
        d.main(["refund", "--leg", leg])


def act_sweep() -> None:
    log("  sweep: emptying the three demo wallets back to the user's shielded address")
    refund_to = d.refund_address()
    total = Decimal("0")
    for acct, name in ((1, "lot/seller"), (2, "bidder A"), (3, "bidder B")):
        if not wait_spendable(acct, rounds=20):
            log(f"    acct {acct} ({name}): never became spendable - skipped")
            continue
        txid = None
        for attempt in range(6):
            d.sync(acct)
            bal = d.balance(acct)
            if bal <= FEE:
                log(f"    acct {acct} ({name}): {bal} ZEC - dust, nothing to sweep")
                break
            try:
                txid = d.pay(acct, refund_to, bal - FEE)
            except Exception as exc:  # noqa: BLE001 - pending change notes show up in `total`
                log(f"    acct {acct} sweep attempt {attempt} deferred: {str(exc)[:120]}")
                time.sleep(45)
                continue
            total += bal - FEE
            log(f"    acct {acct} ({name}): swept {bal - FEE} ZEC  txid={txid}")
            break
        if txid is None and bal > FEE:
            log(f"    !! acct {acct} ({name}): sweep did not go through, {bal} ZEC still there")
    log(f"  swept {total} ZEC to {refund_to[:24]}…")


def main() -> int:
    log("== DEMO-01 finisher ==")
    st = settlement()
    ledger = d.load_ledger()
    log(f"auction {ledger['auction_id']}  bids={len(ledger['bids'])}  "
        f"slots={ledger['slots']}  rule={ledger['settlement_rule']}")

    log("[1/4] waiting for the sealed bids to confirm in the lot wallet")
    if not wait_spendable(1):
        log("!! lot wallet never became spendable - aborting")
        return 1
    if not d.SETTLEMENT.exists():
        log("      escrow notes in the lot wallet:")
        for n in d.notes(1):
            log(f"        value={n['value']:>10} pool={n['pool']} h={n['height']}")

    log("[2/4] close")
    act_close()

    log("[3/4] refunds")
    act_refund()

    log("[4/4] wind-down sweep")
    act_sweep()

    st = settlement()
    log("== receipts ==")
    for p in st["settlement"]:
        log(f"  #{p['rank']} {p['bidder']:<9} bid {p['amount']:>8} -> {p['result']:<5} "
            f"pays {p['pays']:>8} refund {p['refund']:>8} tx={p.get('refund_txid', '-')}")
    log("clearing price:", st["clearing_price"], "ZEC")
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
