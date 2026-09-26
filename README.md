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

## v9: 外部签名器兼容包

Release 现在同时生成两个 IPA：

- `SoulSign.ipa`：默认推荐，移除 `SealTunnel.appex`，用于全能签一类只需要给主 App 重签的场景。
- `SoulSign-Full.ipa`：保留 Tunnel Extension，仅用于能够同时给主 App、Extension 和对应 entitlement/provisioning profile 完整重签的安装链。

如果之前是“安装成功，一点即退”，请优先测试 `SoulSign.ipa`。详见 `docs/EXTERNAL_SIGNING.md`。
