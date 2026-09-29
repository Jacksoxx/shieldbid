# ShieldBid — DEMO-01 narration script (English)

Target length: about **2 minutes 30 seconds**. Six segments, one per screen state.
Spoken language: **English** (the audience is the review panel). Subtitles: burned-in English (same text).

Numbers used here are the ones that actually ran on Zcash mainnet — see `docs/DEMO_01_REPORT.md`
and `docs/demo_01_settlement.json`. Public bid book figures are captured in
`docs/zilkroad_bids_evidence.png` (measured 2026-09-29).

---

## Segment 1 — the problem (30 s)

**On screen:** Zilkroad bid book screenshot, the three summary figures boxed.

> On the marketplace this was built against, bids are a public open book. When I measured it,
> fifteen open offers sat in plain sight: a top bid of 3.38 ZEC, and about 21.81 ZEC of total open
> value. Anyone can read every number and raise the price against you — one participant wrote that
> it took him seven hours of studying other people's bids before he dared to submit his own.
> ShieldBid puts the price back inside an encrypted note.

## Segment 2 — the lot, and how a bid is placed (35 s)

**On screen:** the live lot page: lot header, `Place a sealed bid`, the seller's u1 address, the Copy
button pressed once, the three steps, the wallet list.

> This is a live lot: DEMO-01. The reserve is public, the number of sealed bids is public, and the
> reveal moment is public — everything else is not. To bid, you open a wallet with a shielded
> balance and send one shielded transfer to the seller's unified address. No form, no contract call,
> no memo to parse: the amount you send is the bid. It lands in the shielded pool, so the chain
> records that a transfer happened, and nothing about how much, or between whom.

## Segment 3 — what the seller sees (25 s)

**On screen:** `docs/demo01_status.png` (the sealed round card).

> Three bids arrived in this round: 0.012, 0.009 and 0.004 ZEC. One of them was sent by hand from a
> phone wallet running Noir. The auction wallet syncs, and only the seller can read those amounts.
> This is the round afterwards: three bids, two slots, and no outside observer can see any of the
> numbers.

## Segment 4 — the reveal (30 s)

**On screen:** `docs/demo01_result.png` — settlement table, then the money trail legs.

> At the reveal, only two things are published: the clearing price and the ranking. This round
> cleared at 0.009 ZEC under a uniform-price rule: every winner pays that price, the losing bidder
> gets a full refund, and the winner's overpayment comes back too. Losing amounts and identities are
> never published. Here is the settlement receipt and the money trail — twelve legs, every
> transaction id public, every amount private.

## Segment 5 — honest limits (30 s)

**On screen:** limits slide (text, from SPEC section 7).

> What ShieldBid does not do. There is no live highest-bid figure: the amounts are encrypted, so
> nobody — not even the seller — can compute it honestly. The seller is a trusted party: they decide
> the clearing price, and a third party cannot verify it from the chain alone. And a bid cannot be
> withdrawn. Privacy has a price, and this is it.

## Segment 6 — wrap (20 s)

**On screen:** `docs/refund_flow.png`, then the repository file list of the README.

> The whole round ran on Zcash mainnet: twelve transactions and about 0.001 ZEC of chain fees,
> roughly a dollar fifty. The protocol spec, the engine, the receipts and the address a bidder sends
> to are all in the repository.

---

### Delivery notes

- One TTS voice, steady pace (~150 words per minute), no music.
- Every on-screen figure is either a real transaction or a real page capture; nothing is mocked up.
- The bid the demo wallet placed is **0.012 ZEC**, the clearing price is **0.009 ZEC**, and the
  losing bids were refunded in full — all three are visible in `docs/demo_01_money_trail.json`.
