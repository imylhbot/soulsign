# iOS 14 compatibility status

SoulSign's feature design is compatible with the iOS 14 BackgroundTasks API, but the
current upstream signing stack is **not** a clean iOS 14 build target:

- MJorb/Seal currently declares iOS 16 as its minimum deployment target.
- The MJorb AnisetteKit package currently declares iOS 15 as its minimum.
- Current SideSign also declares iOS 15 as its minimum.
- Lowering only `IPHONEOS_DEPLOYMENT_TARGET` would therefore create a misleading
  "iOS 14 supported" build that does not actually compile/run reliably.

The bootstrap keeps iOS 16 as the stable default. `SOULSIGN_MIN_IOS=15.0` enables an
experimental deployment-target change for compatibility work, but it still needs a
real GitHub Actions build/test pass because upstream SwiftUI APIs may require guards.

## Proper iOS 14 port

For a real iOS 14 release, use one of these approaches:

1. Backport/replace local Anisette with an implementation that builds on iOS 14, then
   guard all iOS 15/16-only UI/runtime APIs with availability checks; or
2. Use a remote Anisette provider only on iOS 14 while keeping local Anisette on newer
   systems, and make the Apple-account client depend on a small provider protocol.

SoulSign should not claim iOS 14 support until that branch compiles on an iOS 14 SDK
compatible toolchain and is tested on a real iOS 14 device.
