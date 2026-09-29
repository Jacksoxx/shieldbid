# -*- coding: utf-8 -*-
"""build_deck.py -- turn the recording canvas into the repo's public deck.

The recording canvas (spectmp/deck.html) hard-codes absolute file:// image paths
because the recorder runs it straight off disk. Hand-copying it into the repo
would (a) ship dead file:// links to every reader and (b) let the two copies drift.

This script is the one-way transform: it reads the recording canvas and writes
docs/deck.html, which

  * references the evidence PNGs *relatively*, so it works from docs/ in a clone
    and from gh-pages/deck/ on the published site;
  * gives the closing "re-check it yourself" column real, clickable links
    (repo, SPEC, the money trail, an example txid on a public explorer);
  * keeps link clicks from triggering the deck's click-to-advance handler.

    python tools/build_deck.py --src C:/Users/XiaoSS/spectmp/deck.html \
        --out docs/deck.html

Every substitution is asserted, so a changed canvas fails loudly instead of
silently producing a deck with dead paths.
"""
import argparse
import os

REPO = "https://github.com/Jacksoxx/shieldbid"
BLOB = REPO + "/blob/main/"
EXPLORER = "https://mainnet.zcashexplorer.app/transactions/"
EXAMPLE_TX = ("56bb6efa5a23841f2212211de3776f66a3231d28a230e831c0e9f6a05c715a40")

ABS_PREFIX = "file:///C:/Users/XiaoSS/shieldbid/docs/"

OLD_RECHECK = """        <div class="mono">
          <b>clone</b> the repo, open <b>web/index.html</b><br>
          <b>look up</b> any txid on a Zcash explorer<br>
          <b>diff</b> the receipt against <b>SPEC.md</b><br>
          <b>re-run</b> the engine: <b>ENGINE_SETUP.md</b><br>
          <b>check</b> the refund legs address by address
        </div>"""

NEW_RECHECK = """        <div class="mono">
          <b>clone</b> the <a href="{repo}" target="_blank">repository</a> and open <b>web/index.html</b><br>
          <b>look up</b> any txid on a <a href="{explorer}" target="_blank">Zcash explorer</a><br>
          <b>diff</b> the <a href="{blob}docs/demo_01_settlement.json" target="_blank">receipt</a> against <a href="{blob}docs/SPEC.md" target="_blank">SPEC.md</a><br>
          <b>re-run</b> the engine: <a href="{blob}docs/ENGINE_SETUP.md" target="_blank">ENGINE_SETUP.md</a><br>
          <b>check</b> the <a href="{blob}docs/demo_01_money_trail.json" target="_blank">refund legs</a> address by address
        </div>""".format(repo=REPO, blob=BLOB, explorer=EXPLORER + EXAMPLE_TX)

# file names in columns 1 and 2 -> clickable too
FILE_LINKS = {
    "<b>docs/SPEC.md</b>": '<a href="%sdocs/SPEC.md" target="_blank">docs/SPEC.md</a>' % BLOB,
    "<b>docs/BIDDER_GUIDE.md</b>": '<a href="%sdocs/BIDDER_GUIDE.md" target="_blank">docs/BIDDER_GUIDE.md</a>' % BLOB,
    "<b>docs/ENGINE_SETUP.md</b>": '<a href="%sdocs/ENGINE_SETUP.md" target="_blank">docs/ENGINE_SETUP.md</a>' % BLOB,
    "<b>web/index.html</b>": '<a href="%sweb/index.html" target="_blank">web/index.html</a>' % BLOB,
    "<b>docs/demo_01_settlement.json</b>": '<a href="%sdocs/demo_01_settlement.json" target="_blank">docs/demo_01_settlement.json</a>' % BLOB,
    "<b>docs/demo_01_money_trail.json</b>": '<a href="%sdocs/demo_01_money_trail.json" target="_blank">docs/demo_01_money_trail.json</a>' % BLOB,
    "<b>docs/demo_01_refund_receipts.json</b>": '<a href="%sdocs/demo_01_refund_receipts.json" target="_blank">docs/demo_01_refund_receipts.json</a>' % BLOB,
    "<b>docs/DEMO_01_REPORT.md</b>": '<a href="%sdocs/DEMO_01_REPORT.md" target="_blank">docs/DEMO_01_REPORT.md</a>' % BLOB,
    "<b>docs/SPEC.md §7</b>": '<a href="%sdocs/SPEC.md" target="_blank">docs/SPEC.md §7</a>' % BLOB,
}

OLD_LINK_CSS = "  #pager{position:fixed;"
NEW_LINK_CSS = """  a{color:var(--acc);text-decoration:none;border-bottom:1px dotted var(--acc)}
  a:hover{color:#8ec6ff;border-bottom-style:solid}
  #pager{position:fixed;"""

OLD_CLICK = """  document.addEventListener('click', function (e) {
    if (window.navOff) return;
    window.step("""
NEW_CLICK = """  document.addEventListener('click', function (e) {
    if (window.navOff) return;
    if (e.target && e.target.closest && e.target.closest('a')) return;  // links are links
    window.step("""

OLD_HINT = "<b id=\"pnum\">1 / 7</b> &nbsp; arrow-keys to page"
NEW_HINT = "<b id=\"pnum\">1 / 7</b> &nbsp; click or arrow-keys to page"


def sub(text, old, new, what):
    if old not in text:
        raise SystemExit("build_deck: cannot find %s -- canvas changed, fix the transform" % what)
    return text.replace(old, new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(a.src, encoding="utf-8") as f:
        html = f.read()

    n_abs = html.count(ABS_PREFIX)
    if n_abs == 0:
        raise SystemExit("build_deck: no absolute image paths found in the canvas")
    html = html.replace(ABS_PREFIX, "")          # file:///... -> relative

    # the recording canvas must stay frozen; only the public copy gains links
    if 'target="_blank"' in html:
        raise SystemExit("build_deck: src already looks like a built deck")
    html = sub(html, OLD_RECHECK, NEW_RECHECK, "the 're-check it yourself' column")
    for k, v in FILE_LINKS.items():
        html = sub(html, k, v, "file link %s" % k)
    html = sub(html, OLD_LINK_CSS, NEW_LINK_CSS, "the #pager CSS rule")
    html = sub(html, OLD_CLICK, NEW_CLICK, "the click-to-advance handler")
    html = sub(html, OLD_HINT, NEW_HINT, "the pager hint")

    # the deck lives next to the evidence PNGs wherever it is published
    missing = [p for p in ("demo01_result.png", "demo01_status.png", "demo01_trail.png",
                           "refund_flow.png", "zilkroad_bids_evidence.png")
               if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(a.out)), p))]
    if missing:
        print("WARNING: evidence PNGs not next to the output:", ", ".join(missing))

    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote %s (%d bytes) from %s -- %d absolute paths made relative"
          % (a.out, len(html.encode("utf-8")), a.src, n_abs))


if __name__ == "__main__":
    main()
