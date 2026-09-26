#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"

echo "[SoulSign audit] deployment target"
grep -RIn --include='project.yml' --include='*.pbxproj' --include='*.xcconfig' \
  -E 'iOS:|IPHONEOS_DEPLOYMENT_TARGET|deploymentTarget' "$ROOT" | head -80 || true

echo "[SoulSign audit] Apple auth client identity"
if grep -RIn --include='*.swift' --include='*.m' --include='*.mm' --include='*.h' \
   -E 'com\.apple\.dt\.Xcode/[0-9]|digest\.hexadecimal\(\)' "$ROOT" | head -40; then
  echo "[SoulSign audit] note: matches above may include comments/tests; build patch verifies GSAContext separately"
fi

echo "[SoulSign audit] signing implementation markers"
grep -RIn --include='*.swift' --include='*.m' --include='*.mm' \
  -E 'provisioningProfiles|embedded\.mobileprovision|appExtensions|ALTSigner|AppBundleSigner|keychain-access-groups|application-identifier|team-identifier' \
  "$ROOT" | head -120 || true
