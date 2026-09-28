#!/usr/bin/env python3
"""ShieldBid seller tool — sealed-bid auctions on Zcash.

Protocol: docs/SPEC.md (shieldbid v0.1)
Engines:  zkool GraphQL server, or `manual` (memos pasted from any wallet UI).

Subcommands
    init     create a lot (item, reserve, deadline, seller unified address)
    ingest   import decrypted incoming notes: engine=manual|zkool
    commit   freeze the sealed set and print the hash commitment
    reveal   rank bids, compute clearing price, emit reveal.json + refund list
    verify   re-check a reveal.json (anyone can run this, no wallet needed)
    demo     end-to-end rehearsal on synthetic memos (no chain)

Nothing here needs the seller's spending key: `ingest` consumes decrypted memo text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCHEMA = "shieldbid/reveal/1"
BID_RE = re.compile(r"\bBID\s+([0-9]+(?:\.[0-9]{1,8})?)", re.IGNORECASE)
NONCE_RE = re.compile(r"\|\s*n\s*=\s*([^\s|]+)", re.IGNORECASE)


# ---------------------------------------------------------------- amounts

def fmt_zec(d: Decimal) -> str:
    """Canonical ZEC string: no trailing zeros, never scientific notation."""
    s = format(d.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def parse_amount(text: str) -> Decimal | None:
    try:
        d = Decimal(text)
    except InvalidOperation:
        return None
    if d.is_nan() or d <= 0:
        return None
    return d


# ---------------------------------------------------------------- memo parsing

def parse_memo(memo: str) -> dict:
    """Return {'ok':True,'amount':Decimal,'nonce':str|None} or {'ok':False,'reason':...}"""
    if memo is None:
        return {"ok": False, "reason": "empty memo"}
    text = memo.replace("\x00", "").strip()
    if not text:
        return {"ok": False, "reason": "empty memo"}
    m = BID_RE.search(text)
    if not m:
        return {"ok": False, "reason": "no BID <amount> token"}
    amt = parse_amount(m.group(1))
    if amt is None:
        return {"ok": False, "reason": "unparsable amount"}
    nonce = NONCE_RE.search(text)
    return {"ok": True, "amount": amt, "nonce": nonce.group(1) if nonce else None,
            "raw": text}


def memo_digest(memo: str) -> str:
    """SHA-256 over the memo text as it was received (NUL padding stripped)."""
    return hashlib.sha256((memo or "").replace("\x00", "").encode("utf-8")).hexdigest()


def commitment_of(digests: list[str]) -> str:
    """SPEC §4: SHA-256 of the newline-joined, byte-sorted per-memo digests."""
    body = "\n".join(sorted(digests))
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- lot store

def lot_dir(root: Path, lot: str) -> Path:
    return root / "lots" / lot


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- engines

def clean_memo(raw) -> str:
    """zkool hands back the memo as a JSON-quoted string padded with NUL bytes."""
    if raw is None:
        return ""
    s = str(raw).replace("\\u0000", "").replace("\x00", "")
    if s[:1] == '"' and s[-1:] == '"':
        try:
            s = json.loads(s)
        except Exception:
            pass
    return s.strip()


def fetch_zkool(url: str, account: int) -> list[dict]:
    """Read received shielded notes (with decrypted memos) from the local zkool engine.

    Verified against the LIVE schema: notesByAccount(idAccount) -> Note { height pool
    value address memo tx { txid height } }. Only the wallet owner can decrypt these;
    everyone else sees ciphertext. The engine clears the bid once it is spent.
    """
    query = """
    query($a: Int!) {
      notesByAccount(idAccount: $a) {
        id height pool value address memo
        tx { txid height }
      }
    }"""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    payload = json.dumps({"query": query, "variables": {"a": account}}).encode()
    req = urllib.request.Request(url, data=payload,
                                headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=120) as r:
        data = json.loads(r.read().decode("utf-8"))
    if "errors" in data:
        raise RuntimeError(f"graphql error: {data['errors']}")
    out = []
    for n in data["data"]["notesByAccount"] or []:
        memo = clean_memo(n.get("memo"))
        if not memo:
            continue
        tx = n.get("tx") or {}
        out.append({"txid": tx.get("txid"), "height": n.get("height"),
                    "memo": memo, "value": n.get("value"),
                    "pool": n.get("pool"), "address": n.get("address")})
    return out


def read_manual(path: Path) -> list[dict]:
    """Read memos from a file: JSONL of {txid, height, memo} or one memo per line."""
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("{"):
            obj = json.loads(line)
            rows.append({"txid": obj.get("txid", f"manual-{i}"),
                         "height": obj.get("height"),
                         "memo": obj.get("memo", "")})
        else:
            rows.append({"txid": f"manual-{i}", "height": None, "memo": line})
    return rows


# ---------------------------------------------------------------- commands

def cmd_init(a) -> int:
    root = Path(a.root)
    d = lot_dir(root, a.lot)
    lot = {
        "schema": "shieldbid/lot/1",
        "lot": a.lot,
        "item": a.item,
        "seller": a.seller,
        "address": a.address,
        "reserve_zec": fmt_zec(Decimal(a.reserve)),
        "deadline": a.deadline,
        "deadline_height": None,
        "winners": a.winners,
        "seed": hashlib.sha256(f"{a.lot}|{a.address}".encode()).hexdigest()[:16],
    }
    save_json(d / "lot.json", lot)
    print(f"lot {a.lot} created -> {d / 'lot.json'}")
    print(f"  item     {lot['item']}")
    print(f"  reserve  {lot['reserve_zec']} ZEC   winners {lot['winners']}")
    print(f"  address  {lot['address']}")
    return 0


def cmd_ingest(a) -> int:
    d = lot_dir(Path(a.root), a.lot)
    lot = load_json(d / "lot.json")
    rows = fetch_zkool(a.url, a.account) if a.engine == "zkool" else read_manual(Path(a.file))

    h = lot.get("deadline_height")
    bids, rejects = [], []
    for r in rows:
        p = parse_memo(r.get("memo", ""))
        rec = {"txid": r.get("txid"), "height": r.get("height"),
               "memo_sha256": memo_digest(r.get("memo", ""))}
        if not p["ok"]:
            rec["invalid_reason"] = p["reason"]
            rejects.append(rec)
        elif h and r.get("height") and int(r["height"]) > int(h):
            rec["invalid_reason"] = f"height {r['height']} > deadline_height {h}"
            rejects.append(rec)
        else:
            rec.update({"amount_zec": fmt_zec(p["amount"]), "nonce": p["nonce"]})
            bids.append(rec)
    save_json(d / "inbox.json", {"schema": "shieldbid/inbox/1", "lot": a.lot,
                                 "bids": bids, "rejects": rejects})
    print(f"ingest: {len(bids)} valid bid(s), {len(rejects)} refund-only transfer(s)")
    for b in sorted(bids, key=lambda x: Decimal(x["amount_zec"]), reverse=True):
        print(f"  {b['txid'][:16]}…  {b['amount_zec']} ZEC")
    for r in rejects:
        print(f"  {str(r['txid'])[:16]}…  REFUND  ({r['invalid_reason']})")
    print(f"commitment now: {commitment_of([b['memo_sha256'] for b in bids])}")
    return 0


def cmd_commit(a) -> int:
    d = lot_dir(Path(a.root), a.lot)
    inbox = load_json(d / "inbox.json")
    com = commitment_of([b["memo_sha256"] for b in inbox["bids"]])
    if a.height:
        lot = load_json(d / "lot.json")
        lot["deadline_height"] = int(a.height)
        save_json(d / "lot.json", lot)
    save_json(d / "commitment.json", {"lot": a.lot, "commitment": com,
                                      "count": len(inbox["bids"]),
                                      "deadline_height": load_json(d / "lot.json").get("deadline_height")})
    print(f"SEALED — {len(inbox['bids'])} bid(s)")
    print(f"commitment {com}")
    print("publish this before revealing anything (SPEC §4).")
    return 0


def cmd_reveal(a) -> int:
    d = lot_dir(Path(a.root), a.lot)
    lot, inbox = load_json(d / "lot.json"), load_json(d / "inbox.json")
    comfile = d / "commitment.json"
    com = load_json(comfile)["commitment"] if comfile.exists() else None

    reserve = Decimal(lot["reserve_zec"])
    eligible = [b for b in inbox["bids"] if Decimal(b["amount_zec"]) >= reserve]
    below = [b for b in inbox["bids"] if Decimal(b["amount_zec"]) < reserve]
    eligible.sort(key=lambda b: Decimal(b["amount_zec"]), reverse=True)

    winners = eligible[: lot["winners"]]
    losers = eligible[lot["winners"]:]
    if not winners:
        clearing = None
    else:
        clearing = min(Decimal(w["amount_zec"]) for w in winners)

    received = []
    for b in eligible + below:
        if b in winners:
            status = "winner"
        elif Decimal(b["amount_zec"]) < reserve:
            status = "below_reserve"
        else:
            status = "refunded"
        received.append({"txid": b["txid"], "memo_sha256": b["memo_sha256"],
                         "amount_zec": b["amount_zec"], "status": status,
                         "height": b.get("height")})

    refunds = []
    for b in losers:
        amt = Decimal(b["amount_zec"]) - (clearing or 0) if b in winners else Decimal(b["amount_zec"])
        refunds.append({"txid": b["txid"], "amount_zec": fmt_zec(Decimal(b["amount_zec"])),
                        "kind": "outbid_refund"})
    for b in below:
        refunds.append({"txid": b["txid"], "amount_zec": fmt_zec(Decimal(b["amount_zec"])),
                        "kind": "below_reserve_refund"})
    for r in inbox["rejects"]:
        refunds.append({"txid": r["txid"], "amount_zec": None, "kind": "invalid_memo_refund"})

    out = {
        "schema": SCHEMA, "lot": lot["lot"], "item": lot["item"],
        "address": lot["address"], "reserve_zec": lot["reserve_zec"],
        "deadline": lot["deadline"], "deadline_height": lot.get("deadline_height"),
        "commitment": com, "clearing_zec": fmt_zec(clearing) if clearing else None,
        "winners": len(winners), "received": received, "refunds": refunds,
        "note": ("losers are listed only because their funds must be returned; "
                 "no identity, handle or address is attached to any bid by this protocol"),
    }
    save_json(d / "reveal.json", out)
    print(f"REVEAL lot {lot['lot']} — {lot['item']}")
    print(f"  bids {len(inbox['bids'])}, eligible {len(eligible)}, winners {len(winners)}")
    print(f"  clearing price {out['clearing_zec'] or '—'} ZEC (reserve {lot['reserve_zec']})")
    for w in winners:
        print(f"  WIN  {w['txid'][:16]}…  {w['amount_zec']} ZEC")
    for b in losers:
        print(f"  out  {b['txid'][:16]}…  {b['amount_zec']} ZEC -> refund")
    for b in below:
        print(f"  low  {b['txid'][:16]}…  {b['amount_zec']} ZEC -> refund (below reserve)")
    print(f"  {len(refunds)} refund(s) queued, {len(inbox['rejects'])} invalid memo transfer(s)")
    print(f"wrote {d / 'reveal.json'}")
    return 0


def cmd_verify(a) -> int:
    path = Path(a.file)
    r = load_json(path)
    problems, checks = [], []

    digests = [x["memo_sha256"] for x in r["received"]]
    rec_com = commitment_of(digests)
    checks.append(("commitment matches received set", rec_com == r["commitment"]))
    if rec_com != r["commitment"]:
        problems.append(f"commitment mismatch: reveal says {r['commitment']}, recomputed {rec_com}")

    winners = [x for x in r["received"] if x["status"] == "winner"]
    checks.append(("winner count matches", len(winners) == r["winners"]))
    if winners and r["clearing_zec"]:
        mn = min(Decimal(w["amount_zec"]) for w in winners)
        checks.append(("clearing = lowest winning bid", mn == Decimal(r["clearing_zec"])))
        if mn != Decimal(r["clearing_zec"]):
            problems.append(f"clearing {r['clearing_zec']} != min winner {fmt_zec(mn)}")
    checks.append(("no winner below reserve",
                   all(Decimal(w["amount_zec"]) >= Decimal(r["reserve_zec"]) for w in winners)))

    unrefunded = [x["txid"] for x in r["received"]
                  if x["status"] not in ("winner",) and Decimal(x["amount_zec"]) >= Decimal(r["reserve_zec"])
                  and x["txid"] not in {f["txid"] for f in r["refunds"]}]
    checks.append(("every losing eligible bid is refunded", not unrefunded))
    if unrefunded:
        problems.append(f"bid(s) marked refunded but missing from refunds[]: {unrefunded[:3]}")

    checks.append(("no duplicate txids",
                   len({x['txid'] for x in r['received']}) == len(r['received'])))

    print(f"verify {path.name} (schema {r['schema']}, lot {r['lot']})")
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if problems:
        print("\nPROBLEMS")
        for p in problems:
            print("  -", p)
        return 1
    print("\nall local checks passed. Remaining manual check: your own txid appears in received[].")
    return 0


def cmd_demo(a) -> int:
    """Full rehearsal with synthetic memos — proves the pipeline without a chain."""
    import tempfile
    root = Path(a.root or tempfile.mkdtemp(prefix="shieldbid-demo-"))
    lot = "DEMO"
    d = lot_dir(root, lot)
    save_json(d / "lot.json", {
        "schema": "shieldbid/lot/1", "lot": lot, "item": "zkSNARKs #9631",
        "seller": "@JACKSOxx", "address": "u1demo" + "0" * 50,
        "reserve_zec": "1.20", "deadline": "2026-10-05T18:00:00Z",
        "deadline_height": 26123456, "winners": 1, "seed": "demo",
    })
    memos = [
        {"txid": "aa" * 32, "height": 26123300, "memo": "BID 1.55"},
        {"txid": "bb" * 32, "height": 26123310, "memo": "bid 1.42 |n=f3a91c"},
        {"txid": "cc" * 32, "height": 26123320, "memo": "BID 1.05"},
        {"txid": "dd" * 32, "height": 26123330, "memo": "hello"},
        {"txid": "ee" * 32, "height": 26123400, "memo": "BID 2.00"},
    ]
    p = d / "memos.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(m) for m in memos) + "\n", encoding="utf-8")

    class NS: pass
    ns = NS(); ns.root = str(root); ns.lot = lot; ns.engine = "manual"; ns.file = str(p)
    ns.url = None; ns.account = 0
    print("== ingest =="); cmd_ingest(ns)
    ns.height = None
    print("\n== commit =="); cmd_commit(ns)
    ns.file = str(d / "reveal.json")
    print("\n== reveal =="); cmd_reveal(ns)
    print("\n== verify =="); rc = cmd_verify(ns)

    print("\n== tamper test: swap a revealed amount ==")
    r = load_json(d / "reveal.json")
    r["received"][1]["amount_zec"] = "1.50"
    save_json(d / "tampered.json", r)
    ns.file = str(d / "tampered.json")
    rc2 = cmd_verify(ns)
    print(f"\ntamper detected: {rc2 == 1}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="shieldbid", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="lot workspace root (default: .)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.set_defaults(f=cmd_init)
    p.add_argument("--lot", required=True); p.add_argument("--item", required=True)
    p.add_argument("--address", required=True); p.add_argument("--seller", default="")
    p.add_argument("--reserve", required=True); p.add_argument("--deadline", required=True)
    p.add_argument("--winners", type=int, default=1)

    p = sub.add_parser("ingest"); p.set_defaults(f=cmd_ingest)
    p.add_argument("--lot", required=True)
    p.add_argument("--engine", choices=["manual", "zkool"], default="manual")
    p.add_argument("--file", help="manual: jsonl or one memo per line")
    p.add_argument("--url", default="http://127.0.0.1:8080", help="zkool graphql endpoint")
    p.add_argument("--account", type=int, default=0)

    p = sub.add_parser("commit"); p.set_defaults(f=cmd_commit)
    p.add_argument("--lot", required=True); p.add_argument("--height", type=int)

    p = sub.add_parser("reveal"); p.set_defaults(f=cmd_reveal)
    p.add_argument("--lot", required=True)

    p = sub.add_parser("verify"); p.set_defaults(f=cmd_verify)
    p.add_argument("--file", required=True)

    p = sub.add_parser("demo"); p.set_defaults(f=cmd_demo)

    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
