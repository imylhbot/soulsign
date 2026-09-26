# SoulSign GitHub-ready v10

SoulSign v10 is based on the pinned MJorb/Seal source and focuses on Apple ID authentication/signing compatibility while keeping the existing SoulSign account-pool work.

## v10 changes

- Minimum deployment target: **iOS 15.0**.
- Build-time patch for the known AltSign `s2k_fo` login regression.
- Build-time normalization of outdated GSA `com.apple.dt.Xcode/...` client tokens to `com.apple.akd/1.0` in resolved auth packages.
- Removes legacy console logging of returned Apple service tokens when that old AltSign code is present.
- Explicit package-resolution step before compile, then patches the exact package source Xcode will build.
- Keeps `SoulSign.ipa` as the complete app including `SealTunnel.appex`; `SoulSign-Lite.ipa` is also emitted for bootstrap/testing with third-party signers that cannot provision the NetworkExtension.
- Keeps pinned MJorb source in `vendor/MJorb` after the first workflow run, so the entire upstream is not downloaded every build.

## Upload

Upload/overwrite the contents of this directory into your `imylhbot/soulsign` repository, then run:

**Actions → SoulSign Build & Release → Run workflow**

The default upstream ref remains pinned to `4c24fda2c97f8d275b748ba069a9af0ba89b62d2`.

See `docs/AUTH_SIGNING_FIXES.md` for the authentication/signing rationale.

## License

MJorb/Seal is AGPL-3.0. Keep its license/notices and publish corresponding source when distributing binaries as required by that license.
