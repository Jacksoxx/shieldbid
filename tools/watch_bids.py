#!/usr/bin/env python3
"""watch_bids.py - poll the chain until the seller wallet sees a memo-carrying note.

Usage: python tools/watch_bids.py [--net mainnet|testnet] [--account 1] [--rounds 20] [--sleep 18]
Exit 0 as soon as a note with a non-empty memo shows up (the sealed bid arrived).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "engine.py"


def run(*args: str) -> str:
    p = subprocess.run([sys.executable, str(ENGINE), *args], capture_output=True, text=True)
    return (p.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default="mainnet")
    ap.add_argument("--account", type=int, default=1)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--sleep", type=int, default=18)
    a = ap.parse_args()

    for i in range(1, a.rounds + 1):
        h = run("height", "--net", a.net)
        bal = run("sync", "--net", a.net, "--account", str(a.account), "--balance")
        notes = run("notes", "--net", a.net, "--account", str(a.account))
        lines = [ln for ln in notes.splitlines() if ln.strip()]
        print(f"[{i}] height={h} | {bal.splitlines()[-1] if bal else '?'} | {len(lines)} note(s)", flush=True)
        for ln in lines:
            print("     ", ln, flush=True)
        if any("memo=" in ln and not ln.rstrip().endswith('memo=""') for ln in lines):
            print("*** MEMO NOTE ARRIVED ***", flush=True)
            print(notes)
            return 0
        time.sleep(a.sleep)
    print("no memo note after the polling window", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
