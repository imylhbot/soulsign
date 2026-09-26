#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
REF="${MJORB_REF:-4c24fda2c97f8d275b748ba069a9af0ba89b62d2}"
URL="${MJORB_URL:-https://github.com/dmjorb/MJorb.git}"
DEST="$ROOT/vendor/MJorb"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [[ -f "$DEST/project.yml" && -f "$DEST/.soulsign-upstream-ref" ]] && \
   [[ "$(tr -d '\r\n' < "$DEST/.soulsign-upstream-ref")" == "$REF" ]]; then
  echo "[SoulSign] Vendored MJorb already matches $REF"
  exit 0
fi

rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
git clone --filter=blob:none --no-checkout "$URL" "$TMP/upstream"
git -C "$TMP/upstream" fetch --depth 1 origin "$REF"
git -C "$TMP/upstream" checkout --detach FETCH_HEAD
SHA="$(git -C "$TMP/upstream" rev-parse HEAD)"
mkdir -p "$DEST"
cp -R "$TMP/upstream/." "$DEST/"
rm -rf "$DEST/.git"
printf '%s\n' "$SHA" > "$DEST/.soulsign-upstream-ref"
find "$DEST" -type d \( -name build -o -name DerivedData -o -name target -o -name .build \) -prune -exec rm -rf {} + 2>/dev/null || true

echo "[SoulSign] Vendored MJorb $SHA into $DEST"
