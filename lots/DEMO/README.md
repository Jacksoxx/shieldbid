# `lots/DEMO` — offline fixtures, not mainnet

The files in this directory are the **synthetic fixtures** the CLI workbench writes during a
`tools/shieldbid.py` dry run: a made-up lot (reserve `1.20 ZEC`), five invented memo lines, and a
placeholder address (`u1demo0000…`). The `aaaaaaaa…` / `bbbbbbbb…` transaction ids are deliberately
non-real so that nobody can mistake a fixture for a receipt.

Nothing here is a claim about any chain. The real, mined round is **DEMO-01**, kept separately:

| What | Where |
|---|---|
| Round report (all 12 legs) | [`docs/DEMO_01_REPORT.md`](../../docs/DEMO_01_REPORT.md) |
| Settlement: clearing price, ranking, txids | [`docs/demo_01_settlement.json`](../../docs/demo_01_settlement.json) |
| Money trail | [`docs/demo_01_money_trail.json`](../../docs/demo_01_money_trail.json) |
| Seller-side view read from the lot wallet | [`docs/demo_01_seller_view.json`](../../docs/demo_01_seller_view.json) |

Every txid in those files resolves on Zcash mainnet.
