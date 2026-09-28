# ShieldBid — protocol spec v0.1

Status: draft, subject to change before ZECATHON submission (2026-10-28).

## 1. Terms

| Term | Meaning |
|---|---|
| **Lot** | One sale: an item, a public reserve price, a deadline, and one seller-controlled unified address (UA). |
| **Sealed bid** | A shielded (z→z) Zcash transfer to the lot's UA whose memo carries the bid amount. |
| **Clearing price** | The lowest winning bid. Winners pay this price, not their own bid (uniform-price auction). |
| **Reveal** | The seller's signed publication of clearing price, winners, and the receipt list. |

## 2. Bid memo format

Memo must be UTF-8 text (Zcash memos allow 512 bytes; a bid uses < 32).

```
BID <amount>            e.g.  BID 1.55
BID <amount> |n=<nonce> e.g.  BID 1.55 |n=f3a91c
```

Rules:

- Case-insensitive `BID` token, single space, decimal amount with `.` separator, 1–8 decimal places.
- Amount is in **ZEC**, not zatoshis.
- The first well-formed `BID …` in the memo wins; trailing text is ignored so bidders can add a note to themselves.
- A memo that does not parse is **not** a bid. The transfer is still received and must be refunded.
- Memos are only transmitted on **shielded → shielded** transfers. Wallets refuse (or silently drop) memos to transparent receivers. A bid sent from or to a transparent address is invalid.

## 3. Public information

Published on the board at window open:

- item, public reserve, deadline (UTC), the seller UA.

Publicly visible on-chain to a third party: **nothing useful**. Header counts exist for shielded transfers, but the receiver, amount and memo are encrypted, so a third party cannot attribute a transaction to this lot.

Published during the window (seller's choice, attested not proven):

- number of bids received (recommended — it is public information the seller *can* honestly attest; it does not leak amounts).

## 4. Commitment at the deadline

At (or within a short grace period after) the deadline the seller freezes its inbox view of the lot's UA and publishes:

```
commitment = SHA-256( join("\n", sorted(sha256(memo_bytes_i))) )
```

where the index runs over every incoming note of the lot's UA with a well-formed `BID` memo, received in a block with height ≤ `deadline_height`.

- Sorting is byte-lexicographic over the hex digests, so anyone can recompute it.
- The commitment is published **before** any amount is revealed. It binds the seller to the set it later reveals.
- The seller also publishes `deadline_height` (the block height marking the cut-off), so "late" is objective.

## 5. Reveal

The seller publishes `reveal.json`:

```json
{
  "schema": "shieldbid/reveal/1",
  "lot": "001",
  "deadline_height": 26123456,
  "commitment": "sha256:…",
  "reserve_zec": "1.20",
  "clearing_zec": "1.42",
  "received": [
    { "txid": "…", "memo_sha256": "…", "amount_zec": "1.55", "status": "winner" },
    { "txid": "…", "memo_sha256": "…", "amount_zec": "1.30", "status": "refunded" }
  ],
  "refunds": [ { "txid": "…", "to": "<address used by bidder>", "amount_zec": "1.30" } ],
  "note": "losers' amounts are published only because they must be refunded; identities are not linked"
}
```

Deliberate choices:

- **Clearing price + winner count** are always public.
- Per-bid amounts are published **only when a refund requires it**. The bidder chose to be identified by the address they sent from; nothing links that address to an identity.
- No name, handle, or X account is ever attached to a bid by this protocol.

## 6. Verification (anyone, no wallet needed)

1. Recompute the commitment from `received[].memo_sha256` → must equal `commitment`.
2. Every `txid` must be a real transaction, in a block with height ≤ `deadline_height`, paying the lot UA.
3. Each bidder checks **their own txid is in `received`** — this is the anti-omission check, and it needs no third party.
4. `clearing_zec` must equal the minimum `amount_zec` among the winners, and every received bid ≥ reserve that is not a winner must be marked refunded.

`tools/verify_reveal.py` performs 1 and 4 automatically; 3 is a manual check the board links to.

## 7. Threat model — what this does and does not fix

| Threat | Covered? |
|---|---|
| Rival bidder front-running your price | **Yes** — amounts never touch public state. |
| Seller reading amounts before the deadline | **No** — the seller can decrypt from the first block. The window closes the door on *front-running by others*, not on seller curiosity. Amounts only matter once bidding closes. |
| Seller inventing extra bids to raise the clearing price | **Detectable** — every revealed bid must carry a txid that pays the lot UA; an invented bid has no transaction. |
| Seller silently dropping a bid | **Detectable** — the bidder has their own txid. |
| Seller changing the set after the deadline | **Detectable** — the commitment is published first and is hash-bound. |
| Bidder retracting a bid after the deadline | **No** — a sent shielded transfer is final. This is why the bid amount must be a price the bidder is happy to pay. |
| Funds held by the seller and not refunded | **No** — custody is the seller's. Mitigation: seller publishes refund batch txids. |

This honesty is load-bearing: the ZECATHON rules make leaking privacy a disqualification, and the
"works" criterion rewards a tool whose limits are stated rather than hidden.

## 8. Open questions

- Zcash lacks a native NFT/asset standard on mainnet today (ZSA is not live), so a lot's *item* is
  referenced off-chain by id/URI. Settlement of the item stays outside this protocol on purpose.
- A fully trustless variant would add a script/escrow (P2SH or ZSA-aware) — out of scope for v0.1.
