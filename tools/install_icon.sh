#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
ICON="$ROOT/soulsign.png"

if [[ ! -f "$ICON" ]]; then
  echo "[SoulSign] soulsign.png not found; keeping upstream AppIcon."
  exit 0
fi

APPICON_DIR="$(find "$ROOT/Seal" -type d -name 'AppIcon.appiconset' -print -quit)"
if [[ -z "$APPICON_DIR" ]]; then
  ASSETS="$(find "$ROOT/Seal" -type d -name '*.xcassets' -print -quit)"
  if [[ -z "$ASSETS" ]]; then
    ASSETS="$ROOT/Seal/Resources/Assets.xcassets"
    mkdir -p "$ASSETS"
    [[ -f "$ASSETS/Contents.json" ]] || printf '{"info":{"author":"xcode","version":1}}\n' > "$ASSETS/Contents.json"
  fi
  APPICON_DIR="$ASSETS/AppIcon.appiconset"
  mkdir -p "$APPICON_DIR"
fi

python3 - "$ICON" <<'PY'
import sys
from pathlib import Path
try:
    from PIL import Image
except Exception:
    sys.exit(0)
p=Path(sys.argv[1])
im=Image.open(p)
if im.width != im.height:
    raise SystemExit("soulsign.png must be square")
if im.width < 1024:
    print("warning: soulsign.png is smaller than 1024x1024; release icon quality may be reduced")
PY

# Generate all common iPhone/iPad icon raster sizes using macOS built-in sips.
declare -A SIZES=(
  [icon-20@2x.png]=40 [icon-20@3x.png]=60
  [icon-29@2x.png]=58 [icon-29@3x.png]=87
  [icon-40@2x.png]=80 [icon-40@3x.png]=120
  [icon-60@2x.png]=120 [icon-60@3x.png]=180
  [icon-20-ipad.png]=20 [icon-20@2x-ipad.png]=40
  [icon-29-ipad.png]=29 [icon-29@2x-ipad.png]=58
  [icon-40-ipad.png]=40 [icon-40@2x-ipad.png]=80
  [icon-76-ipad.png]=76 [icon-76@2x-ipad.png]=152
  [icon-83.5@2x-ipad.png]=167 [icon-1024.png]=1024
)
for file in "${!SIZES[@]}"; do
  px="${SIZES[$file]}"
  sips -s format png -z "$px" "$px" "$ICON" --out "$APPICON_DIR/$file" >/dev/null
done

cat > "$APPICON_DIR/Contents.json" <<'JSON'
{
  "images" : [
    {"idiom":"iphone","size":"20x20","scale":"2x","filename":"icon-20@2x.png"},
    {"idiom":"iphone","size":"20x20","scale":"3x","filename":"icon-20@3x.png"},
    {"idiom":"iphone","size":"29x29","scale":"2x","filename":"icon-29@2x.png"},
    {"idiom":"iphone","size":"29x29","scale":"3x","filename":"icon-29@3x.png"},
    {"idiom":"iphone","size":"40x40","scale":"2x","filename":"icon-40@2x.png"},
    {"idiom":"iphone","size":"40x40","scale":"3x","filename":"icon-40@3x.png"},
    {"idiom":"iphone","size":"60x60","scale":"2x","filename":"icon-60@2x.png"},
    {"idiom":"iphone","size":"60x60","scale":"3x","filename":"icon-60@3x.png"},
    {"idiom":"ipad","size":"20x20","scale":"1x","filename":"icon-20-ipad.png"},
    {"idiom":"ipad","size":"20x20","scale":"2x","filename":"icon-20@2x-ipad.png"},
    {"idiom":"ipad","size":"29x29","scale":"1x","filename":"icon-29-ipad.png"},
    {"idiom":"ipad","size":"29x29","scale":"2x","filename":"icon-29@2x-ipad.png"},
    {"idiom":"ipad","size":"40x40","scale":"1x","filename":"icon-40-ipad.png"},
    {"idiom":"ipad","size":"40x40","scale":"2x","filename":"icon-40@2x-ipad.png"},
    {"idiom":"ipad","size":"76x76","scale":"1x","filename":"icon-76-ipad.png"},
    {"idiom":"ipad","size":"76x76","scale":"2x","filename":"icon-76@2x-ipad.png"},
    {"idiom":"ipad","size":"83.5x83.5","scale":"2x","filename":"icon-83.5@2x-ipad.png"},
    {"idiom":"ios-marketing","size":"1024x1024","scale":"1x","filename":"icon-1024.png"}
  ],
  "info" : {"author":"xcode","version":1}
}
JSON

echo "[SoulSign] AppIcon generated from soulsign.png -> $APPICON_DIR"
