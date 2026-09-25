# SoulSign bootstrap kit

This kit turns a fresh clone of `dmjorb/MJorb` into a SoulSign source fork and adds:

- multi-Apple-ID automatic pool rotation;
- max 3 user IPA apps per Apple ID (SoulSign policy);
- renewal pinned to the app's original Apple ID;
- 24-hour expiration trigger;
- best-effort `BGAppRefreshTask` automatic renewal plus foreground fallback;
- SoulSign branding and `soulsign.png` AppIcon generation;
- manual GitHub Actions build and optional GitHub Release publishing.

## Create the source repository

```bash
unzip SoulSign-bootstrap.zip
cd SoulSign-bootstrap
./bootstrap.sh ../SoulSign
cd ../SoulSign
# Put your 1024x1024 soulsign.png here.
git init
git add .
git commit -m "Initial SoulSign fork"
```

Then create an empty GitHub repository, push this full source tree, and run
`SoulSign Build & Release` from the Actions page.

By default the source keeps the upstream iOS 16 minimum for build reliability. See
`IOS14_COMPATIBILITY.md` in the generated repo for the iOS 14/15 status.

## License

This kit is intended to modify MJorb/Seal. MJorb is AGPL-3.0. Preserve the upstream
license and notices and comply with the source-availability obligations when you
publish SoulSign binaries.
