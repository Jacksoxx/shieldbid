# ShieldBid — sealed bids on Zcash

**PRIVATE MARKETS · ZECATHON entry**

A bid is a shielded Zcash transfer with a memo. Only the seller can read the amount.
When the window closes the seller reveals the **clearing price and the ranking — nothing else**.
Losers' amounts and identities are never published.

> Track brief we are answering (ZECATHON, PRIVATE MARKETS): *sealed-bid auctions … the price should be
> public and the participants should not.*

---

## Why this exists

On the marketplace this was built against, offers and auction bids are **public**:

| Observation | Value |
|---|---|
| Public open offers on the bid book (measured 2026-09-29) | 16 offers, top 3.38 ZEC, 22.71 ZEC total (≈$34,928) |
| Organiser's own blind auction wording | *"existing bids can be viewed or raised at any time before the auction ends"* |
| Participant description of that auction | *"after analysing other people's bid amounts for 7 hours, I finally submitted my bid"* |

Everyone's intent is on a public wall. ShieldBid moves the price discovery into a shielded memo:
unlinkable, encrypted, and readable only by the seller.

---

## Protocol (v0.1)

1. **Lot published** — item, public reserve price, deadline, and one **unified address (UA)** belonging to the seller.
2. **Bid = shielded → shielded transfer with a memo.** Memo text:
   ```
   BID <amount in ZEC>
   ```
   e.g. `BID 1.55`. An optional nonce can be appended (`BID 1.55 |n=f3a91c`). Anything after the amount is ignored.
3. **No public book.** There is no list of bids. Not even the number of bids is visible on-chain to a third party.
4. **Commitment at the deadline.** The seller publishes `SHA256` over the sorted set of sealed memos it decrypted.
5. **Reveal.** The seller publishes: clearing price, winner, the count, and the **list of received txids / memo hashes**.
   Each bidder checks their own txid is in that list — the seller cannot silently drop or add a bid.
6. **Refunds** — losing bids are returned to the address they came from; the memo of the refund can carry `REFUND <lot>`.

### What is *not* claimed

- **The seller is still a trusted party.** Nothing here removes the need to trust the seller to reveal honestly —
  the commitment makes dishonesty *detectable*, not impossible.
- **A live "current high bid" is impossible.** Amounts are encrypted; the seller cannot honestly publish a running
  high bid before reveal. We do not fake one.
- **Asset settlement is out of scope.** ShieldBid settles the *price discovery*; moving the asset stays wherever
  the sale happens.

---

## Repo layout

```
web/index.html      the public board (single file, deploys to GitHub Pages as-is)
docs/SPEC.md        protocol spec v0.1
docs/BIDDER_GUIDE.md  screenshot-level wallet instructions for bidders
tools/              seller-side reveal CLI (wallet-engine adapters)  ← in progress
```

## Seller-side wallet engines

The reveal tool reads decrypted memos from whichever engine is available:

| Engine | Reads memos via | Platforms |
|---|---|---|
| `zkool` (light client, no full node) | GraphQL `Transaction.outputs { memo }` | Linux / macOS / Windows |
| `zallet` (official successor to `zcashd`) | RPC `z_listunspent` → `memoStr` | Linux only today |
| `manual` | paste from any wallet UI | any |

## Verify a reveal yourself

```bash
python tools/verify_reveal.py --commitment reveal.json --lot lot.json
```

(script lands with the reveal CLI; the spec section in `docs/SPEC.md` defines the exact hash input)

## Status

- [x] protocol spec v0.1
- [x] public board (static, no backend)
- [ ] bidder flow end-to-end on mainnet (small amounts)
- [ ] reveal CLI (`tools/shieldbid.py`) with `zkool` + `manual` engines
- [ ] commitment / verification story
- [ ] 2-minute demo video

MIT licensed.

---

*This is an independent ZECATHON submission. It is not affiliated with, and does not repackage, any existing
product; the marketplace referenced above is used only as evidence that the problem is real.*
