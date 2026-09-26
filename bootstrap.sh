#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_URL="${MJORB_URL:-https://github.com/dmjorb/MJorb.git}"
UPSTREAM_REF="${MJORB_REF:-4c24fda2c97f8d275b748ba069a9af0ba89b62d2}"
TARGET_DIR="${1:-SoulSign}"
MIN_IOS="${SOULSIGN_MIN_IOS:-16.0}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENDOR_DIR="${MJORB_VENDOR_DIR:-$SCRIPT_DIR/vendor/MJorb}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ -e "$TARGET_DIR" && -n "$(ls -A "$TARGET_DIR" 2>/dev/null || true)" ]]; then
  echo "error: target directory '$TARGET_DIR' is not empty" >&2
  exit 2
fi

mkdir -p "$TARGET_DIR"

if [[ -f "$VENDOR_DIR/project.yml" ]]; then
  echo "[SoulSign] Using vendored MJorb source: $VENDOR_DIR"
  if [[ -f "$VENDOR_DIR/.soulsign-upstream-ref" ]]; then
    VENDORED_REF="$(tr -d '\r\n' < "$VENDOR_DIR/.soulsign-upstream-ref")"
    echo "[SoulSign] Vendored upstream ref: $VENDORED_REF"
  fi
  cp -R "$VENDOR_DIR/." "$TARGET_DIR/"
  rm -rf "$TARGET_DIR/.git"
  UPSTREAM_SHA="${VENDORED_REF:-$UPSTREAM_REF}"
else
  echo "[SoulSign] Vendored source missing; cloning MJorb ($UPSTREAM_REF)..."
  git clone --filter=blob:none --no-checkout "$UPSTREAM_URL" "$TMP_DIR/upstream"
  git -C "$TMP_DIR/upstream" fetch --depth 1 origin "$UPSTREAM_REF"
  git -C "$TMP_DIR/upstream" checkout --detach FETCH_HEAD
  UPSTREAM_SHA="$(git -C "$TMP_DIR/upstream" rev-parse HEAD)"
  echo "[SoulSign] Upstream commit: $UPSTREAM_SHA"
  cp -R "$TMP_DIR/upstream/." "$TARGET_DIR/"
  rm -rf "$TARGET_DIR/.git"
fi

mkdir -p "$TARGET_DIR/.soulsign-tools"
cp "$SCRIPT_DIR/tools/apply_soulsign.py" "$TARGET_DIR/.soulsign-tools/"
cp "$SCRIPT_DIR/tools/install_icon.sh" "$TARGET_DIR/.soulsign-tools/"
mkdir -p "$TARGET_DIR/.github/workflows"
if [[ ! -f "$SCRIPT_DIR/.github/workflows/soulsign-build.yml" ]]; then
  echo "error: missing SoulSign workflow: $SCRIPT_DIR/.github/workflows/soulsign-build.yml" >&2
  exit 3
fi
cp "$SCRIPT_DIR/.github/workflows/soulsign-build.yml" "$TARGET_DIR/.github/workflows/soulsign-build.yml"
cp "$SCRIPT_DIR/docs/IOS14_COMPATIBILITY.md" "$TARGET_DIR/IOS14_COMPATIBILITY.md"
cp "$SCRIPT_DIR/docs/SECURITY.md" "$TARGET_DIR/SOULSIGN_SECURITY.md"

python3 "$TARGET_DIR/.soulsign-tools/apply_soulsign.py" \
  --repo "$TARGET_DIR" \
  --minimum-ios "$MIN_IOS"

cat > "$TARGET_DIR/SOULSIGN_UPSTREAM.md" <<EOF2
# SoulSign upstream

SoulSign is based on MJorb/Seal.

- Upstream: $UPSTREAM_URL
- Bootstrap ref requested: $UPSTREAM_REF
- Upstream source used: $UPSTREAM_SHA
- SoulSign bootstrap generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Keep the upstream copyright/license notices. MJorb is AGPL-3.0; if you distribute
SoulSign binaries, publish the corresponding SoulSign source as required by the
license.
EOF2

echo "[SoulSign] Ready: $TARGET_DIR"
