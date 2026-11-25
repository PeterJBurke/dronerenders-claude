#!/usr/bin/env bash
# Refresh the board models (and the pin table) of this render site from a StackF765 checkout.
#
#   ./sync-models.sh [/path/to/stackf765-checkout]      default: /root/fcclaude
#
# Copies docs/boards/{lower,upper,service}/*.glb (the GLB files KiCad exports from the design)
# into fc/models/ and regenerates fc/assets/pin-data.js from gen/upper.py and gen/lower.py
# (revision C: both Dupont headers are on the upper board; the lower board has none).
# Nothing is committed or pushed; review `git status`, then commit and push yourself.
set -euo pipefail
SRC="${1:-/root/fcclaude}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HERE/fc/models"
for b in lower upper service; do
  f="$SRC/docs/boards/$b/$b.glb"
  [ -s "$f" ] || { echo "missing or empty: $f" >&2; exit 1; }
  # a GLB starts with the ASCII magic "glTF" and stores its own total length in bytes 8-11;
  # refuse a file that is still being written
  magic="$(head -c 4 "$f")"
  declared="$(od -An -tu4 -j8 -N4 "$f" | tr -d ' ')"
  actual="$(stat -c %s "$f")"
  if [ "$magic" != "glTF" ] || [ "$declared" != "$actual" ]; then
    echo "not a complete GLB (still being exported?): $f" >&2; exit 1
  fi
  cp "$f" "$HERE/fc/models/$b.glb.tmp"
  mv "$HERE/fc/models/$b.glb.tmp" "$HERE/fc/models/$b.glb"
  echo "copied $b.glb ($actual bytes)"
done
if [ -f "$SRC/gen/upper.py" ] && [ -f "$SRC/gen/lower.py" ]; then
  python3 "$HERE/tools/make-pin-data.py" "$SRC"
else
  echo "gen/upper.py / gen/lower.py not found in $SRC: pin table left unchanged" >&2
fi
git -C "$HERE" status --short -- fc/models fc/assets/pin-data.js || true
