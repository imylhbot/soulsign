# SoulSign OTA installation notes

The reference installation flow supplied for 全能签 uses an Apple OTA manifest:

1. The IPA is already signed and provisioned for the target device.
2. The signer keeps a localhost HTTP server alive (the example uses 127.0.0.1:24302).
3. The manifest is delivered over HTTPS and its software-package URL points back to the localhost IPA.
4. iOS is opened with `itms-services://?action=download-manifest&url=<https manifest url>`.

This is an installation transport, not a signing bypass. A malformed signature,
missing embedded provisioning profile, bad nested-extension signature, or entitlement
mismatch can still install and then terminate at launch (or fail installation).

`tools/make_ota_manifest.py` can generate the XML manifest for a signed IPA. SoulSign
v8 does not depend on the third-party plist.nuosike.com encoder. A production in-app
implementation should either use a trusted HTTPS manifest endpoint you control or a
well-audited equivalent, while serving the signed IPA from the app's localhost server.
