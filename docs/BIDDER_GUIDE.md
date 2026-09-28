# Bidder guide — placing a sealed bid

You need one thing: **a shielded wallet with a memo field**. No account, no sign-up, no connection to this
website. The whole bid is one transfer you make from your own wallet.

> ⚠️ Screenshots in this guide are pending (they ship with the demo build). The step text below is the
> verified flow; the wallet UI wording may differ slightly per version.

---

## 1. Which wallet to use

| Wallet | Platform | Memo field | Notes |
|---|---|---|---|
| **Zashi** | iOS / Android | ✅ | simplest path, shielded by default |
| **Zkool** | Windows / macOS / Linux / Android | ✅ | desktop option |
| **Ywallet** | iOS / Android / desktop | ✅ | |
| **Zingo** | iOS / Android / desktop | ✅ | |
| Exchanges (Binance, OKX, …) | — | ❌ | withdrawals have no memo field — **a bid sent from an exchange is invalid** |
| OKX Web3 wallet | — | ❌ | no memo field |

Fund the wallet with **shielded** ZEC before you bid. If your wallet shows a separate
"shielded"/"orchard" balance, make sure the funds are there — a transfer from a transparent balance cannot
carry a memo, and it would make your bid public.

## 2. Get the lot address

Copy the unified address shown on the lot page. It starts with `u1`.

## 3. Send the bid

1. Open your wallet, choose **Send**.
2. Paste the address.
3. **Amount** = the *maximum* price you are willing to pay, in ZEC (e.g. `1.55`).
   You pay this only if you win; if the clearing price is lower you are refunded the difference.
4. Open the **Memo / Note** field and type exactly:
   ```
   BID 1.55
   ```
   Rules: `BID`, one space, the amount. Letters can be lower case. Do not use a comma as a decimal
   separator. You may append anything after it (e.g. `BID 1.55 |n=my nonce`) — it is ignored.
5. Review and send. Shielded transfers take a few seconds to a couple of minutes to confirm.

## 4. Keep your receipt

- Save the **transaction id** your wallet shows. When the seller publishes the reveal, you check your
  txid appears in the receipt list — that is how you know your bid was counted.
- Do not delete the wallet until refunds are sent.

## 5. What happens next

| When | What |
|---|---|
| During the window | nothing is public. Your amount and address are not visible to anyone but the seller. |
| At the deadline | the seller publishes a hash commitment of the sealed bids it holds. |
| At reveal | clearing price, winners, and the txid list are published. Losers get their ZEC back to the address they sent from. |

## Rules that make a bid invalid

- memo missing, unparsable, or not starting with `BID`
- sent from a transparent (t…) address, or to a transparent address
- amount below the reserve
- arrived in a block after the deadline height (the seller publishes the height)
- sent before the window opened

Invalid transfers are not bids, but they are still funds in the seller's wallet — the seller returns them in
the final batch. Don't send test dust to "check" the address; it becomes refund work.

## Questions a bidder should ask

- **Can the seller see my bid early?** Yes. The seller can decrypt from the first block. This protocol hides
  your price from *other bidders and the public*, not from the seller.
- **Can the seller change the result?** It can lie about the clearing price, but every bid it counts must be
  backed by a real transaction, and you can check your own txid is included. Choosing a seller you trust is
  still part of the deal.
