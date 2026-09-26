#!/usr/bin/env bash
set -euo pipefail

SRC_IPA="${1:-build/SoulSign-Full.ipa}"
DST_IPA="${2:-build/SoulSign.ipa}"

if [[ ! -f "$SRC_IPA" ]]; then
  echo "error: source IPA not found: $SRC_IPA" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

ditto -x -k "$SRC_IPA" "$TMP"
APP="$(find "$TMP/Payload" -maxdepth 1 -type d -name '*.app' | head -1)"
if [[ -z "$APP" || ! -d "$APP" ]]; then
  echo "error: no .app found in IPA" >&2
  exit 3
fi

# External-signing compatibility profile:
# The MJorb/Seal full build embeds SealTunnel.appex. Many generic on-device
# signers only provision/sign the main application and do not create a second
# valid provisioning profile for a NetworkExtension target. iOS can then kill
# the application before normal app code runs. The compatibility IPA removes
# the embedded tunnel extension so the signer only has one executable app
# bundle to provision.
if [[ -d "$APP/PlugIns/SealTunnel.appex" ]]; then
  rm -rf "$APP/PlugIns/SealTunnel.appex"
  echo "[SoulSign] Removed embedded SealTunnel.appex for external-signer IPA"
fi

# Remove an empty PlugIns directory if the tunnel was the only extension.
if [[ -d "$APP/PlugIns" ]] && [[ -z "$(find "$APP/PlugIns" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  rmdir "$APP/PlugIns"
fi

# This build is intentionally unsigned. Remove stale signature/provision files
# if an upstream build ever starts carrying them, so the downstream signer can
# build a fresh signing graph.
find "$APP" -type d -name '_CodeSignature' -prune -exec rm -rf {} + 2>/dev/null || true
find "$APP" -type f -name 'embedded.mobileprovision' -delete 2>/dev/null || true

mkdir -p "$(dirname "$DST_IPA")"
rm -f "$DST_IPA"
(
  cd "$TMP"
  zip -qry "$OLDPWD/$DST_IPA" Payload
)

echo "[SoulSign] External-signer IPA created: $DST_IPA"
du -h "$DST_IPA" || true
