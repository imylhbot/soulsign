#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_URL="${MJORB_URL:-https://github.com/dmjorb/MJorb.git}"
UPSTREAM_REF="${MJORB_REF:-main}"
TARGET_DIR="${1:-SoulSign}"
MIN_IOS="${SOULSIGN_MIN_IOS:-16.0}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if [[ -e "$TARGET_DIR" && -n "$(ls -A "$TARGET_DIR" 2>/dev/null || true)" ]]; then
  echo "error: target directory '$TARGET_DIR' is not empty" >&2
  exit 2
fi

mkdir -p "$TARGET_DIR"
echo "[SoulSign] Cloning MJorb ($UPSTREAM_REF)..."
git clone --depth 1 --branch "$UPSTREAM_REF" "$UPSTREAM_URL" "$TMP_DIR/upstream"

# Copy the complete upstream source so the resulting GitHub repository remains a
# real source fork instead of a binary-only wrapper. Do not copy upstream .git.
cp -R "$TMP_DIR/upstream/." "$TARGET_DIR/"
rm -rf "$TARGET_DIR/.git"

mkdir -p "$TARGET_DIR/.soulsign-tools"
cp "$SCRIPT_DIR/tools/apply_soulsign.py" "$TARGET_DIR/.soulsign-tools/"
cp "$SCRIPT_DIR/tools/install_icon.sh" "$TARGET_DIR/.soulsign-tools/"
cp "$SCRIPT_DIR/overlay/SoulSign/SoulSignBackgroundRenewal.swift" "$TARGET_DIR/Seal/App/"
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

cat > "$TARGET_DIR/SOULSIGN_UPSTREAM.md" <<EOF
# SoulSign upstream

SoulSign is based on MJorb/Seal.

- Upstream: $UPSTREAM_URL
- Bootstrap ref requested: $UPSTREAM_REF
- SoulSign bootstrap generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Keep the upstream copyright/license notices. MJorb is AGPL-3.0; if you distribute
SoulSign binaries, publish the corresponding SoulSign source as required by the
license.
EOF

cat > "$TARGET_DIR/README_SOULSIGN.md" <<'EOF'
# SoulSign

SoulSign is an on-device IPA signing/renewal fork built on MJorb/Seal.

## SoulSign additions

- Apple ID account pool with automatic rotation.
- Maximum 3 top-level user IPA apps assigned to each Apple ID by SoulSign policy.
- Existing apps always renew with their original recorded Apple ID when possible.
- Expiration scan with a 24-hour renewal threshold.
- Foreground auto-renew trigger and best-effort iOS BGAppRefreshTask renewal.
- Local notification support remains provided by the upstream expiration scheduler.
- Root `soulsign.png` can be converted into the AppIcon set during GitHub Actions.
- Manual GitHub Actions build; optional Release publication by entering a tag.

## Important iOS behavior

A 7-day validity period is the normal free-development provisioning behavior, but
Apple ultimately controls profile/certificate validity and account limits. SoulSign
records the real profile expiry returned by the signing flow rather than assuming
that every signing operation is exactly seven days.

Background renewal on iOS is **best effort**. iOS decides when a BGAppRefreshTask is
launched. SoulSign therefore also checks immediately when the app becomes active and
keeps the expiration notification fallback.

## Build

1. Put your square `soulsign.png` in the repository root (1024x1024 recommended).
2. Push the complete generated repository to GitHub.
3. Open **Actions -> SoulSign Build & Release -> Run workflow**.
4. Leave `release_tag` blank to only produce a downloadable Actions artifact.
5. Enter a tag such as `v0.1.0` to also create/update a GitHub Release containing
   `SoulSign.ipa` and its SHA-256 file.

The workflow builds an unsigned IPA, matching the upstream distribution model. You
then install/sign SoulSign using your existing bootstrap/sideload method.
EOF

cat <<EOF
[SoulSign] Ready: $TARGET_DIR
Next:
  1. cd '$TARGET_DIR'
  2. put soulsign.png in the repo root
  3. git init && git add . && git commit -m 'Initial SoulSign fork'
  4. push to your GitHub repository
EOF
