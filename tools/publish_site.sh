#!/usr/bin/env bash
# Publish web/index.html to the gh-pages branch — this is the "usable demo" link the
# ZECATHON submission points at: https://jacksoxx.github.io/shieldbid/
#
# Why a separate branch instead of the built-in options:
#   * Pages for a project site only accepts the paths "/" or "/docs" from a branch, and
#     the console lives in web/ — publishing "/" would serve the README as the site.
#   * Actions-based deployment needs to push .github/workflows/pages.yml, which the
#     device-flow token is not allowed to do ("without `workflow` scope").
#   * gh-pages keeps web/index.html as the single source of truth: nothing is duplicated
#     inside main's tree, and this script regenerates the published copy.
set -euo pipefail

OWNER="Jacksoxx"
R="C:/Users/XiaoSS/shieldbid"
REMOTE="https://github.com/${OWNER}/shieldbid.git"
T="C:/Users/XiaoSS/AppData/Local/Temp/shieldbid-site"
GH="/c/Program Files/GitHub CLI/gh.exe"
DOCS_URL="https://github.com/${OWNER}/shieldbid/blob/main/docs/"

cd "$R"

rm -rf "$T"; mkdir -p "$T"

# The console links to ../docs/SPEC.md and ../docs/BIDDER_GUIDE.md. That is correct when
# the file is opened from disk, but on a published project site "../" escapes the site
# root and the links 404. Point them at the rendered docs on GitHub instead.
echo "=== rewriting relative doc links for the published copy ==="
sed -e "s#\.\./docs/#${DOCS_URL}#g" web/index.html > "$T/index.html"
grep -o "https://github.com/${OWNER}/shieldbid/blob/main/docs/[A-Za-z_]*\.md" "$T/index.html" | sort -u

# serve the files exactly as committed (no Jekyll processing)
: > "$T/.nojekyll"

# a self-contained single file: no local css/js/img may be referenced, or the live demo breaks
echo "=== local asset refs (must be empty) ==="
grep -o -E '(src|href)="[^"]*"' "$T/index.html" | grep -v -E 'https?://|data:|^href="#|mailto:' || echo "(none)"

# The page links the walkthrough video at /shieldbid/demo.mp4, so it ships with the site:
# a submission needs a public video link and this keeps it on the same static host.
MP4="C:/Users/XiaoSS/spectmp/ShieldBid-DEMO-01-walkthrough.mp4"
if [ -f "$MP4" ]; then
  cp "$MP4" "$T/demo.mp4"
  echo "video: $(wc -c < "$T/demo.mp4") bytes -> https://${OWNER}.github.io/shieldbid/demo.mp4"
else
  echo "video: MISSING at $MP4 - the link on the page will 404"
fi

cd "$T"
git init -q -b gh-pages
git config user.name "Qihao Xiao"
git config user.email "86060929+${OWNER}@users.noreply.github.com"
git add -A
git commit -q -m "site: publish the bidder console (generated from web/index.html)"
git push -f -q "$REMOTE" gh-pages
echo "published commit: $(git rev-parse --short HEAD)"

echo "=== trigger a Pages build ==="
"$GH" api -X POST "/repos/${OWNER}/shieldbid/pages/builds" --jq '"build: " + .status' 2>&1 | head -2

echo "=== wait for the site ==="
for i in $(seq 1 12); do
  sleep 20
  # note: `curl | grep` can fail under `set -e`/pipefail (no 3-digit code), so guard both steps
  CODE=$(curl -s --noproxy "*" -o /dev/null -w '%{http_code}' --max-time 20 "https://${OWNER}.github.io/shieldbid/" 2>/dev/null || true)
  CODE=$(printf '%s' "$CODE" | grep -o '[0-9]\{3\}' | head -1 || true)
  CODE=${CODE:-000}
  echo "t+$((i * 20))s site_http=$CODE"
  [ "$CODE" = "200" ] && break
done

echo "=== verify the live HTML ==="
curl -s --noproxy "*" --max-time 25 "https://${OWNER}.github.io/shieldbid/" -o "C:/Users/XiaoSS/AppData/Local/Temp/live.html"
echo "bytes=$(wc -c < 'C:/Users/XiaoSS/AppData/Local/Temp/live.html')"
grep -o -i '<title>[^<]*</title>' "C:/Users/XiaoSS/AppData/Local/Temp/live.html"
echo "doc links on the live page:"
grep -o "https://github.com/${OWNER}/shieldbid/blob/main/docs/[A-Za-z0-9_]*\.\(md\|json\)" "C:/Users/XiaoSS/AppData/Local/Temp/live.html" | sort -u

echo "=== verify the video link ==="
curl -s --noproxy "*" -o /dev/null -w 'demo.mp4 http=%{http_code} type=%{content_type} bytes=%{size_download}\n' --max-time 90 "https://${OWNER}.github.io/shieldbid/demo.mp4" || true

echo "=== no future dates left in the published copy (must be empty) ==="
grep -o "2026-10-05\|2026-09-30\|1\.20 <small>" "C:/Users/XiaoSS/AppData/Local/Temp/live.html" || echo "(none)"
echo "SITE_URL=https://${OWNER}.github.io/shieldbid/"
echo "REPO_URL=https://github.com/${OWNER}/shieldbid"
echo "DONE-SITE"
