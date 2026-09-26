# SoulSign external-signing builds

Every successful workflow publishes two IPA variants:

- `SoulSign.ipa` — **recommended for generic/on-device signers**. The embedded
  `SealTunnel.appex` NetworkExtension is removed before packaging. This avoids a
  common failure mode where the main app receives a valid provisioning profile
  but the extension does not, which can cause iOS to terminate the app before
  normal launch code executes.
- `SoulSign-Full.ipa` — preserves `SealTunnel.appex`. Use this only with a
  signing/install pipeline that explicitly provisions and signs the main app,
  the embedded NetworkExtension, all frameworks, and their entitlements.

Both artifacts are intentionally unsigned when published by GitHub Actions.
A downstream signer still needs to create a valid development/ad-hoc signing
chain before installation.

The compatibility IPA is intended to stabilize launch first. Features that
require the embedded tunnel/local-device transport can be unavailable until the
OTA localhost/manifest installation path is fully wired into SoulSign.
