# Bidder guide — placing a sealed bid

You need one thing: **a shielded ZEC balance you can send from**. No account, no sign-up, no
connection to this website, no special software. The whole bid is one transfer you make from your
own wallet.

> **The amount you send *is* your bid.** It is encrypted end-to-end by Zcash's shielded pool: the
> seller can read it, nobody else can — not other bidders, not the explorer, not us.

---

## 1. Which wallet to use

Any wallet that can send **shielded (z→z)** ZEC works. A memo field is *not* required anymore.

| Wallet | Platform | Notes |
|---|---|---|
| **Zodl** | iOS / Android | ECC's wallet, shielded by default |
| **Ywallet** | iOS / Android / desktop | send from the shielded balance |
| **Edge Wallet** | iOS / Android | shielded ZEC send |
| **Zkool** | Windows / macOS / Linux / Android | desktop option |
| **Zingo!** | iOS / Android / desktop | send from the shielded balance |
| **Nighthawk** | Android | send from the shielded balance |
| **Noir** (used in our live demo) | iOS / Android | shielded pool wallet, worked end to end |
| Exchanges (OKX, Binance, …) | — | a withdrawal lands on a **transparent** address; you must shield it in your own wallet first |
| OKX Web3 wallet, most hardware-wallet flows | — | no shielded (u1) send path — it can only pay a t1 address, so it **cannot** place a bid |

**Self-test (5 seconds):** open your wallet's *Send* screen. If it offers no shielded/private send and
you cannot paste a `u1` recipient, that wallet cannot bid — move your ZEC into one of the wallets above.
The official wallet list lives at [z.cash/ecosystem](https://z.cash/ecosystem/?wallets=#tag-wallets).

**Fund the wallet with shielded ZEC before you bid.** If your wallet shows a separate
"shielded"/"orchard" balance, make sure the funds are *there*: a transfer from a transparent balance
is public on chain and is not a valid bid.

## 2. Get the lot address

Copy the unified address on the lot page. It starts with `u1`.

## 3. Send the bid

1. Open your wallet → **Send**.
2. Paste the lot address.
3. **Amount = the maximum price you are willing to pay**, in ZEC (e.g. `1.55`).
   You pay this only if you win; if the clearing price is lower, **the difference is refunded to the
   address you sent from**.
4. (Optional) If your wallet has a memo field, you may type `BID 1.55` for your own readability. It
   is **not read by the protocol** — the amount is the bid. Leave it empty if you prefer.
5. Review and send. Shielded transfers confirm in seconds to a couple of minutes.

## 4. Keep your receipt

- Save the **transaction id** your wallet shows.
- You check your own txid against the published receipt list — that is how you know your bid was
  counted. The seller cannot silently drop a bid that has a txid: the commitment is published before
  the reveal.
- Do not delete the wallet until refunds have arrived.

## 5. What happens next

| When | What |
|---|---|
| During the window | **nothing is public.** Your amount, your address and even the number of bidders are invisible to everyone but the seller. |
| At the deadline | the seller freezes the bid set at a published block height and publishes a hash commitment of it. |
| At reveal | the clearing price (the lowest winning bid) and the winners' ranks are published. Winners pay the clearing price; overpayments and losing escrows are returned as shielded payouts. |

## Rules that make a bid invalid

- sent from or to a **transparent** (`t…`) address, or as an exchange withdrawal
- amount **below the reserve**
- arrived in a block **after** the published deadline height, or before the window opened

Invalid transfers are not bids, but they are still funds in the seller's wallet — the seller returns
them in the settlement batch. Please don't send test dust to "check" the address; it becomes refund
work.

## Questions a bidder should ask

- **Can the seller see my bid early?** Yes. The seller holds the lot keys and can decrypt from the
  first block. This protocol hides your price from *other bidders and the public*, not from the
  seller.
- **Can the seller change the result?** It can lie about the arithmetic behind the published clearing
  price — third parties cannot recompute encrypted amounts. What it cannot do without being caught is
  drop or add a bid: every revealed bid must carry a real txid, the commitment is published before
  the reveal, and you can check your own txid and your own commit/salt. **Choosing a seller you trust
  is still part of the deal.**
- **Can I cancel my bid?** No. A sent shielded transfer is final — only bid a price you are happy to
  pay.
