#!/usr/bin/env python3
"""DEMO-01 finisher: unattended close -> loser refund -> wind-down sweep.

Safe to re-run: every act is driven by what the chain shows, not by bookmarks.

    python tools/demo_01_finish.py

Acts
  1. close  - the lot wallet reads its shielded notes and publishes the receipts
              (clearing price + who won + how much each bidder gets back)
  2. refund - the loser's escrow goes back to its own demo wallet; the winner's
              overpayment goes back to the user's phone-wallet address
  3. sweep  - whatever is still sitting in the three demo wallets is sent to the
              user's own shielded address, so the demo wallets end up empty

Hard-won rules baked in (see HANDOFF.md):
  * never pass `srcPools` to the pay mutation           -> "No feasible note selection found"
  * always pass `confirmations: 1`                      -> otherwise ~10 blocks of waiting
  * one payment per wallet at a time, wait for it to be
    mined before the next one from the same wallet      -> otherwise the node rejects the
                                                          second one as a mempool double spend
  * a payment that returns anything but a 64-hex txid
    counts as a failure (demo_01_run.pay raises)
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
DJC = Decimal("0.0002")          # tolerance when comparing money on chain


def log(*a) -> None:
    print(*a, flush=True)


def chain_height() -> int:
    import engine
    return int(engine.gql(d.url(), "{ currentHeight }")["currentHeight"])


def synced_balance(account: int) -> Decimal:
    d.sync(account)
    return d.balance(account)


def newest_notes(account: int) -> tuple[int, int, int]:
    """(count, newest height, chain height) after a fresh sync."""
    d.sync(account)
    notes = d.notes(account)
    return len(notes), (max(int(n["height"]) for n in notes) if notes else 0), chain_height()


def wait_confirmed(account: int, rounds: int = 40, sleep: int = 20) -> bool:
    """Wait until the wallet's newest note has at least one confirmation."""
    for _ in range(rounds):
        cnt, best, tip = newest_notes(account)
        log(f"    acct {account}: {cnt} note(s), newest h={best}, chain={tip}")
        if cnt and tip - best >= 1:
            return True
        time.sleep(sleep)
    return False


def wait_balance(account: int, target: Decimal, rounds: int = 40, sleep: int = 20) -> bool:
    """Wait until the wallet's balance reaches `target` (used to confirm a spend landed)."""
    for _ in range(rounds):
        bal = synced_balance(account)
        log(f"    acct {account}: balance={bal} (waiting for {target})")
        if bal >= target - DJC:
            return True
        time.sleep(sleep)
    return False


def pay(account: int, to: str, amount: Decimal, tries: int = 8) -> str | None:
    """One payment, retried while the engine's view of the wallet catches up.

    `No feasible note selection found` right after a fresh sync means the money really is
    gone (the engine just listed a note it already spent) — retrying that is pointless, so
    bail out and let the caller re-measure the balance instead.
    """
    for i in range(tries):
        try:
            txid = d.pay(account, to, amount)
            log(f"    sent {amount} ZEC from acct {account} -> {to[:16]}…  txid={txid}")
            return txid
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            log(f"    attempt {i}: {msg[:150]}")
            if "No feasible note selection found" in msg and i >= 1:
                log("    -> spendable funds are gone; re-measuring instead of retrying")
                return None
            time.sleep(45)
    return None


def settlement() -> dict:
    return json.loads(d.SETTLEMENT.read_text(encoding="utf-8"))


RECEIPTS = REPO / "docs" / "demo_01_refund_receipts.json"


def known_receipts() -> dict:
    """Refund/transfer legs that already landed on chain, so they are never paid twice."""
    if not RECEIPTS.exists():
        return {}
    return json.loads(RECEIPTS.read_text(encoding="utf-8")).get("receipts", {})


def main() -> int:
    log("== DEMO-01 finisher ==")
    led = d.load_ledger()
    log(f"auction {led['auction_id']}  bids={len(led['bids'])}  slots={led['slots']}  "
        f"rule={led['settlement_rule']}")
    refund_to = d.refund_address()

    # ---------------------------------------------------------------- 1. close
    if d.SETTLEMENT.exists():
        st = settlement()
        log(f"[1/3] close: already published (clearing price {st['clearing_price']} ZEC)")
    else:
        log("[1/3] close: lot wallet reads its shielded notes and publishes the receipts")
        if not wait_confirmed(1):
            log("!! lot wallet never showed a confirmed note - aborting")
            return 1
        log("      escrow notes currently in the lot wallet:")
        for n in d.notes(1):
            log(f"        value={n['value']:>10} pool={n['pool']} h={n['height']}")
        d.main(["close"])
        st = settlement()

    # ---------------------------------------------------------------- 2. refunds
    log("[2/3] refunds")
    plan = {p["bidder"]: p for p in st["settlement"]}
    done = known_receipts()
    for bidder, rec in done.items():
        if bidder in plan and "refund_txid" not in plan[bidder]:
            plan[bidder]["refund_txid"] = rec["txid"]
            log(f"      {bidder}: refund already on chain ({rec['txid'][:16]}…, h={rec.get('height')})")

    a = plan.get("ROBOT-A")                       # the loser: full escrow back
    if a and Decimal(str(a["refund"])) > 0 and "refund_txid" not in a:
        if synced_balance(2) >= Decimal(str(a["refund"])) + DJC:
            log("      bidder A already holds its refund on chain")
            a["refund_txid"] = "on-chain (see account 2 transactions)"
        else:
            log(f"      paying the loser back: {a['refund']} ZEC -> bidder A's own wallet")
            txid = pay(1, d.account_orchard(2), Decimal(str(a["refund"])))
            if txid:
                a["refund_txid"] = txid
    else:
        log("      loser leg: nothing to do")

    for name in ("USER@Noir", "ROBOT-B"):
        p = plan.get(name)
        if p and Decimal(str(p["refund"])) > 0 and "refund_txid" not in p:
            log(f"      winner {name}: overpayment {p['refund']} ZEC -> user's shielded address")
            txid = pay(1, refund_to, Decimal(str(p["refund"])))
            if txid:
                p["refund_txid"] = txid
        elif p:
            log(f"      winner {name}: pays the clearing price, nothing to refund")

    st["user_refund_address"] = refund_to
    st["refund_note"] = ("escrow sat in the lot wallet; every refund is a shielded payout from it. "
                         "The user's phone wallet gets the overpayment, the losing robot gets its "
                         "escrow back in its own demo wallet, then the wind-down sweep returns "
                         "everything else to the user.")
    d.SETTLEMENT.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------------------------------------------------------- 3. sweep
    # Balance-driven and therefore idempotent: whatever sits in a demo wallet goes home.
    # Several passes because a refund leg that was still in the mempool when the previous
    # pass synced shows up as an *extra* note one block later (that is how acct 2 kept
    # 0.004 from the loser refund after its sweep had already run).
    log("[3/3] wind-down sweep: demo wallets -> user's shielded address")
    total = Decimal("0")
    for p in range(1, 4):
        moved = Decimal("0")
        if p > 1:
            # give the mempool a block to clear so the engine's note list stops showing
            # notes that the previous pass already spent
            time.sleep(150)
        for acct, name in ((2, "bidder A"), (3, "bidder B"), (1, "lot/seller")):
            if not wait_confirmed(acct, rounds=30):
                log(f"    acct {acct} ({name}): nothing confirmed to spend - skipped")
                continue
            bal = synced_balance(acct)
            if bal <= FEE:
                log(f"    acct {acct} ({name}): {bal} ZEC - dust, nothing to sweep")
                continue
            send = bal - FEE
            txid = pay(acct, refund_to, send)
            if txid:
                moved += send
                log(f"    acct {acct} ({name}): swept {send} ZEC")
            else:
                log(f"    !! acct {acct} ({name}): {bal} ZEC still sitting there")
        total += moved
        if moved == 0:
            break
        log(f"  pass {p}: {moved} ZEC moved")
    log(f"  swept {total} ZEC back to {refund_to[:24]}…")
    log("  final balances (after a fresh sync):")
    for acct, name in ((1, "lot/seller"), (2, "bidder A"), (3, "bidder B")):
        log(f"    acct {acct} ({name}): {synced_balance(acct)} ZEC left")

    st["sweep_total"] = str(total)
    d.SETTLEMENT.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log("done - full receipts in", d.SETTLEMENT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
