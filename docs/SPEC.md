# ShieldBid — protocol spec `SHIELDBID/1` (v0.2)

Status: **frozen for the ZECATHON submission (2026-10-28)**.
v0.2 is the design that actually ran on Zcash mainnet — see `docs/DEMO_01_REPORT.md`.

## 1. Terms

| Term | Meaning |
|---|---|
| **Lot** | One sale: an item, a public reserve price, a deadline (UTC), and one seller-controlled unified address (UA). |
| **Sealed bid** | A shielded (z→z) Zcash transfer to the lot's UA. **The transferred amount is the bid.** |
| **Escrow** | The same transfer. Bids sit in the seller's lot UA until the reveal; the bid *is* the deposit. |
| **Clearing price** | The lowest winning bid. Winners pay this price, not their own bid (uniform-price auction). |
| **Reveal** | The seller's publication of the clearing price, the winners' ranks, and the receipt list. |
| **Receipt** | `(txid, amount, status, commit, salt)` for one bid — what a bidder checks. |

## 2. What a bid is

```
bid  =  shielded → shielded transfer, amount = the bidder's price in ZEC, to the lot UA
```

Rules:

- **The amount is the bid.** Nothing has to be parsed, encoded, or agreed on: Zcash already encrypts
  the amount of a shielded transfer to the receiver.
- Only **shielded → shielded** transfers count. A bid sent from or to a transparent (`t…`) address,
  or from an exchange withdrawal, is not a bid (and must be refunded).
- Amount must be **≥ the published reserve**.
- The transfer must be mined in a block with height **≤ `deadline_height`**, and mined after the
  window opened.
- **`memo` is decoration.** A note may carry `BID <amount>` for human readability in wallet UIs, but
  the protocol never reads it. *(Why: on engine v6.31.0 a received orchard note reads back
  `memo = null` and `memosByTransaction` returns `[]` — the node does not hand memos to the wallet.
  Escrow-as-bid removes that dependency entirely.)*
- Invalid transfers are not bids, but they are still funds in the seller's UA — the seller returns
  them in the settlement batch.

## 3. Public information

Published when the window opens:

- item, public reserve, deadline (UTC), the lot UA.

Visible on-chain to a third party:

- **Nothing useful.** The chain shows that some shielded transfers happened. The receiver, the
  amount and the memo are encrypted, and shielded transfers are not attributable to this lot, so a
  third party cannot tell whether a given transaction was a bid — **or how many bids exist**.

Deliberate non-publications: the bid count, the amounts, the bidder list, any standing/"current
high" price. (The seller *may* attest a bid count; it is attested, not proven, and it is optional.)

## 4. Commitment at the deadline

The seller freezes its view of the lot UA at the published `deadline_height` and publishes, **before
any amount is revealed**:

```
commitment = "sha256:" + sha256( join("\n", sorted( sha256(leg_i) for leg_i in received ) ) )
leg_i      = "shieldbid/receipt/1|<txid>|<output_index>"
```

- Sorting is byte-lexicographic over the hex digests, so anyone can recompute it.
- The commitment binds the seller to **the set** it later reveals: it cannot add or drop a leg after
  publishing the hash.
- The seller also publishes `deadline_height`, so "late" is objective rather than a judgement call.

## 5. Reveal

The seller publishes `reveal.json`:

```json
{
  "schema": "shieldbid/reveal/1",
  "lot": "DEMO-01",
  "network": "mainnet",
  "deadline_height": 3499452,
  "commitment": "sha256:…",
  "reserve_zec": "0.003",
  "slots": 2,
  "clearing_zec": "0.009",
  "bids_received": 3,
  "received": [
    { "rank": 1, "txid": "…", "amount_zec": "0.012", "status": "winner",
      "pays_zec": "0.009", "refund_zec": "0.003", "commit": "…", "salt": "…" },
    { "rank": 3, "txid": "…", "amount_zec": "0.004", "status": "refunded",
      "pays_zec": "0", "refund_zec": "0.004" }
  ],
  "payouts": [ { "txid": "…", "amount_zec": "0.003", "kind": "overpayment" },
               { "txid": "…", "amount_zec": "0.004", "kind": "loser-refund" } ]
}
```

Deliberate choices:

- **Clearing price and the winners' ranks are outside the privacy set** — the auction is
  settled with them. Names, handles and X accounts are **never** attached to a bid by this protocol.
- Amounts appear in the reveal **only because settlement requires it** (a winner's overpayment and a
  loser's refund are both sized by the amount). A bidder is identified by the shielded address it
  sent from, which nothing links to an identity.
- **Settlement is uniform-price**: every winner pays `clearing_zec`; overpayments and losing escrows
  are returned as **shielded payouts**, so even "this address lost" stays hidden.

## 6. Verification — what anyone can check

| Check | Who can do it | Needs a wallet? |
|---|---|---|
| Recompute the commitment from the revealed legs | anyone | no |
| Every `txid` is a real, mined transaction ≤ `deadline_height` | anyone | no |
| Every `txid` pays the lot UA | anyone (with a view of the lot UA) | no |
| `clearing_zec` = the lowest winning amount | anyone | no |
| The seller did **not** drop or invent **my** bid | the bidder (own txid + own commit/salt) | yes |
| The seller did **not** inflate the amounts in the reveal | **nobody** — see §7 | — |

`tools/shieldbid.py commit|reveal|verify` performs the commitment/consistency checks;
`tools/demo_01_run.py` produced the DEMO-01 records.

## 7. Threat model — what this does and does not fix

| Threat | Covered? |
|---|---|
| A rival bidder front-running your price / reading your intent | **Yes** — amounts never touch public state. |
| The public (or other bidders) learning how many people bid | **Yes** — shielded transfers are unlinkable to the lot. |
| The seller decrypting your amount early | **No** — the seller holds the lot keys and can decrypt from the first block. The sealed window hides your price from *everyone else*, not from the seller. |
| The seller lying about the arithmetic behind the clearing price | **No — detectable only if it also tampers with a receipt.** The amounts exist in ciphertext on chain; a third party can never recompute them from chain data alone. This is the explicit price of privacy. |
| The seller inventing extra bids to raise the clearing price | **Detectable** — every revealed leg must be backed by a real txid paying the lot UA, and the pre-published commitment is hash-bound. |
| The seller silently dropping a bid | **Detectable** — the bidder holds its own txid, and the commitment was published first. |
| The seller changing the bid set after the deadline | **Detectable** — commitment first, set second. |
| A bidder retracting a bid after the deadline | **No** — a sent shielded transfer is final. Hence: only bid a price you are happy to pay. |
| A bidder being linked to an identity | **No** — as long as the source address is not itself tied to an identity. Bidding from an address you have already doxxed re-identifies you. |
| Escrow held by the seller and never refunded | **No** — custody is the seller's. Mitigation: the seller publishes the payout txids. |

This honesty is load-bearing: the ZECATHON rules make leaking privacy a disqualification, and a tool
whose limits are stated is worth more than one that claims more than it has.

## 8. Open questions / out of scope for v0.2

- **No live "current high bid" is possible**, by construction: the amounts are encrypted, so the
  seller cannot honestly publish a standing price before reveal. We do not fake one.
- Zcash has no live mainnet asset/NFT standard (ZSA is not live), so the lot's *item* is referenced
  off-chain by id/URI; **asset settlement is out of scope**.
- A trustless variant would put the escrow in a script (P2SH or ZSA-aware) instead of the seller's
  wallet — a v0.3 direction, deliberately not attempted here.
