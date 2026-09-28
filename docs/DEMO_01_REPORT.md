# DEMO-01 — a real sealed-bid round on Zcash mainnet (receipts)

**Status: complete.** 3 sealed bids, uniform-price clearing, every refund and the wind-down sweep
are on chain. Nothing of the user's money is left in a demo wallet, and no third party could ever
read a single bid amount.

| | |
|---|---|
| Protocol | `SHIELDBID/1` — escrow-as-bid: the **amount** of a shielded z→z transfer *is* the bid |
| Network | Zcash **mainnet** |
| Bids | 3 (🤖 ROBOT-A `0.004`, **user, sent by hand from a phone wallet** `0.012`, 🤖 ROBOT-B `0.009`) |
| Slots | 2 · reserve `0.003` |
| Clearing price | **`0.009` ZEC** (uniform price = lowest winning bid) |
| Closed | 2026-09-28T18:37:46Z, height 3,499,452 |
| Money in / out | in `0.032` → out `0.0307`, chain fees ≈ `0.001` |

## What the chain shows, and what it does not

* **Public:** the lot address, the txids, the fact that some shielded transfers happened.
* **Never public:** the bid amounts, who bid, and *how many* people bid. An explorer sees
  "shielded → shielded" and nothing else.
* The seller's wallet is the only place the amounts ever existed in the clear —
  see `docs/demo_01_seller_view.json`. That wallet is empty now by design.

## Clearing

| # | Bidder | Bid | Result | Pays | Refund |
|---|---|---|---|---|---|
| 1 | user (phone wallet) | 0.012 | win | 0.009 | 0.003 |
| 2 | ROBOT-B | 0.009 | win | 0.009 | 0.000 |
| 3 | ROBOT-A | 0.004 | lose | 0 | 0.004 |

Winners pay the *lowest winning bid*, so the user's overpayment came back; the loser got its
escrow back in full. Losers are refunded with a plain shielded payment, so even the fact that a
given address lost stays hidden. Full receipts: `docs/demo_01_settlement.json`.

## Every leg (12 transactions, all mined)

| # | What | Amount | From → To | txid | Height |
|---|---|---|---|---|---|
| 1 | user's bid (sent by hand) | 0.012 | user → lot | `56bb6efa5a23…` | 3,499,413 |
| 2 | user funds the demo bidders | 0.020 | user → bidder A | `5c60b3448db4…` | 3,499,430 |
| 3 | top-up to bidder B | 0.012 | bidder A → bidder B | `a14355bf9522…` | 3,499,438 |
| 4 | ROBOT-B bid | 0.009 | bidder B → lot | `91fefe434537…` | 3,499,451 |
| 5 | ROBOT-A bid | 0.004 | bidder A → lot | `4f7926eeadc0…` | 3,499,451 |
| 6 | overpayment refund | 0.003 | lot → **user U1** | `90d35aee9490…` | 3,499,452 |
| 7 | loser refunded in full | 0.004 | lot → bidder A | `f29dbd244048…` | 3,499,454 |
| 8 | wind-down sweep | 0.0036 | bidder A → **user U1** | `359082d37b80…` | 3,499,454 |
| 9 | wind-down sweep | 0.0027 | bidder B → **user U1** | `feea0b1d60be…` | 3,499,454 |
| 10 | wind-down sweep | 0.0039 | bidder A → **user U1** | `4441d21eccbc…` | 3,499,462 |
| 11 | wind-down sweep (lot remainder) | 0.0175 | lot → **user U1** | `27e1379728d9…` | 3,499,462 |
| 12 | memo experiment (see below) | 0.0005 | lot → lot | `c13e2e4b73ae…` | 3,499,418 |

Machine-readable: `docs/demo_01_money_trail.json` (legs), `docs/demo_01_transactions.json`
(read back from the engine's `transactionsByAccount`, not typed by hand).

## Two protocol findings that came out of this round

1. **The memo cannot carry a bid.** A received orchard note reads back `memo = null` and
   `memosByTransaction` returns `[]`, with the engine at v6.31.0 — the node does not hand the
   memo to the wallet. So `SHIELDBID/1` was redesigned around **escrow-as-bid**: the amount is the
   bid. This is *better*: no wallet support needed, no format to agree on, and the amount is
   already encrypted. The memo field stays in the UI as decoration only.
2. **A fresh outbound payment needs a fresh account sync.** Paying twice in a row from one wallet
   without `synchronizeAccount` in between makes the node reject the transaction
   (`could not contextually validate`: the wallet was still offering a note it had just spent).
   `demo_01_run.pay()` now syncs on every attempt, so retries self-heal.

## Honest limits (also in `docs/SPEC.md`)

* **No live "current high bid".** Zallet/Zkool have no streaming view; a bidder cannot be shown
  the standing price during the round — by design of a *sealed* round, and technically impossible here.
* **The seller could tamper with the published clearing price.** Bidders can only check their own
  receipt and the commit/reveal record, not the seller's arithmetic. The commit hash + salt per bid
  (`docs/demo_01_ledger.json`) let a bidder prove what it bid after the fact.
* Fees: ≈ 0.0001 ZEC per shielded leg. 12 legs ≈ 0.001 ZEC ≈ $1.5.

## Reproduce

```bash
python tools/demo_01_run.py status                 # what the ledger already has
python tools/demo_01_finish.py                     # wait → close → refund → sweep (idempotent)
python tools/make_result_card.py                   # docs/demo01_result.png
```
