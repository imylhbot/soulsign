# SoulSign GitHub-ready v8

Upload the **contents of this folder** to `imylhbot/soulsign` and run **SoulSign Build & Release**.

## v8 changes

- Launch-stability reset: keeps MJorb's original bundle identifiers/entitlement namespace.
- Removes SoulSign's launch-time `BGTaskScheduler` registration; foreground 24-hour renewal remains.
- Adds `SoulSign-diagnostics.txt` to every build for crash/IPA inspection.
- Adds `tools/make_ota_manifest.py` and OTA installation notes based on the local-IPA + HTTPS-manifest pattern.
- Adds vendored-upstream support. On the first v8 run Actions downloads the pinned MJorb commit and attempts to commit a clean copy under `vendor/MJorb`; later builds use that local copy instead of cloning upstream again.
- Rust/Cargo/RustBridge caches are retained and the workflow skips RustBridge rebuild when verification already passes.

## Important

`SoulSign.ipa` produced by Actions is still an **unsigned** IPA. It must be signed with a profile valid for the device, including any nested extensions/entitlements, before installation. OTA manifest installation is only a transport for an already-signed IPA; it does not repair invalid signing.

If SoulSign still closes immediately after signing/installing, download `SoulSign-diagnostics.txt` from the same Release and export the iPhone crash `.ips` file from **Settings -> Privacy & Security -> Analytics & Improvements -> Analytics Data**. Those two files allow the next fix to target the actual exception/dylib/entitlement failure.
