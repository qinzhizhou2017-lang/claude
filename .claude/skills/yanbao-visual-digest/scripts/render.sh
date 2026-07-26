#!/usr/bin/env bash
# Render an HTML file to a 4-page A4 PDF via headless Chromium (backgrounds + embedded fonts).
#
# Usage: render.sh <input.html> <output.pdf>
#
# The HTML should define @page { size:A4; margin:0 } and its own .page blocks with
# page-break-after. Fonts/images are loaded relative to the HTML file (file://), so keep
# qr.png and fonts/ next to it. Override the browser with CHROME=/path/to/chrome.
set -eu

HTML="${1:?need input .html}"
OUT="${2:?need output .pdf}"

# locate a chromium/chrome binary
CHROME="${CHROME:-}"
if [ -z "$CHROME" ]; then
  for c in \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    /opt/pw-browsers/chromium-*/chrome-linux/chrome \
    /opt/pw-browsers/chromium/chrome-linux/chrome ; do
    if [ -n "$c" ] && [ -x "$c" ]; then CHROME="$c"; break; fi
  done
fi
[ -n "$CHROME" ] && [ -x "$CHROME" ] || { echo "no chromium/chrome found; set CHROME=/path/to/chrome" >&2; exit 1; }

ABS="$(cd "$(dirname "$HTML")" && pwd)/$(basename "$HTML")"
rm -f "$OUT"
"$CHROME" --headless=new --no-sandbox --disable-gpu \
  --no-pdf-header-footer --allow-file-access-from-files \
  --run-all-compositor-stages-before-draw --virtual-time-budget=8000 \
  --print-to-pdf="$OUT" "file://$ABS" 2>/dev/null

echo "wrote $OUT ($(wc -c < "$OUT") bytes) using $CHROME"
