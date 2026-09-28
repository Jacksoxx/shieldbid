"""Generate QR PNGs for the demo auction addresses, straight from the live engine."""
import json
import subprocess
import sys
from pathlib import Path

import qrcode

ENGINE = Path.home() / "shieldbid" / "tools" / "engine.py"
OUT = Path.home() / "AppData" / "Local" / "Temp" / "sb_qr"


def addr(account: int) -> dict:
    r = subprocess.run([sys.executable, str(ENGINE), "addresses", "--net", "mainnet",
                        "--account", str(account)], capture_output=True, text=True,
                       encoding="utf-8")
    d = {}
    for line in r.stdout.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def qr(text: str, name: str) -> Path:
    q = qrcode.QRCode(box_size=8, border=3)
    q.add_data(text)
    q.make(fit=True)
    p = OUT / name
    q.make_image(fill_color="black", back_color="white").save(p)
    return p


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    seller = addr(1)
    bidder = addr(2)
    plan = [
        ("qr_1_seller_bid.png", seller["orchard"], "SELLER (bid goes here)"),
        ("qr_2_bidder_fund.png", bidder["orchard"], "BIDDER (fund the robots)"),
    ]
    for name, text, label in plan:
        p = qr(text, name)
        print(f"{label}\n  file: {p}\n  addr: {text}\n")
    json.dump({"seller": seller, "bidder": bidder}, open(OUT / "addresses.json", "w"), indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
