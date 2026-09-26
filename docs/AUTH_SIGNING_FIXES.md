# SoulSign Apple ID / signing fixes (v10)

SoulSign v10 uses iOS 15.0 as the minimum deployment target.

## Authentication fixes

The build patches the *resolved authentication package source* before compiling:

1. `s2k_fo` GSA accounts: the SHA-256 password digest is encoded as 64-byte lowercase ASCII hex before PBKDF2. This fixes the AltSign regression where `digest.hexadecimal()` decoded arbitrary digest bytes and produced an invalid SRP proof.
2. Current Apple GSA edge compatibility: embedded `com.apple.dt.Xcode/<version>` client tokens are changed to `com.apple.akd/1.0`. The rest of the persisted Anisette machine identity is left untouched.
3. Legacy AltSign console logging of the returned service token is removed.

The patch runs after Swift package resolution so it changes the code that is actually compiled, not only SoulSign UI code.

## Session / identity policy

Do not regenerate the Anisette machine identity between sign-ins and do not silently switch Anisette identities for an existing session. Apple sessions are tied to the machine identity. SoulSign should reuse the saved session/token until Apple rejects it, then perform an explicit full sign-in/2FA flow.

Passwords and verification codes must not be persisted. Long-lived session material belongs in Keychain / the upstream secure credential store.

## Signing policy

A correct IPA signing pipeline must provision and sign every code bundle, not only the main executable:

- main `.app`
- every `.appex`
- embedded frameworks / dylibs / helper executables

Each app/extension must receive the provisioning profile matching its final bundle identifier. Entitlements must be rewritten from the actual profile, especially `application-identifier`, `com.apple.developer.team-identifier` and `keychain-access-groups`.

SoulSign keeps the upstream complete signing path for this reason. `SoulSign-Lite.ipa` (if produced for third-party bootstrap signing) is only a bootstrap compatibility build and is not a substitute for recursive signing of user IPAs.
