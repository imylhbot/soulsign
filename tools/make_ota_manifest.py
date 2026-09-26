#!/usr/bin/env python3
"""Generate an Apple OTA installation manifest for an ALREADY SIGNED IPA.

This does not sign an IPA and does not make an invalid provisioning profile valid.
The package URL must point to the signed IPA. For an on-device signer, a common
pattern is an HTTPS manifest whose software-package asset points to a localhost
HTTP server that the signer keeps alive while iOS installs the package.
"""
import argparse, plistlib
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--ipa-url', required=True)
p.add_argument('--icon-url')
p.add_argument('--bundle-id', required=True)
p.add_argument('--bundle-version', default='1')
p.add_argument('--title', default='SoulSign App')
p.add_argument('--output', default='manifest.plist')
a=p.parse_args()
assets=[{'kind':'software-package','url':a.ipa_url}]
if a.icon_url:
    assets += [
        {'kind':'display-image','url':a.icon_url,'needs-shine':True},
        {'kind':'full-size-image','url':a.icon_url,'needs-shine':True},
    ]
manifest={'items':[{'assets':assets,'metadata':{
    'kind':'software','title':a.title,'subtitle':a.title,
    'bundle-identifier':a.bundle_id,'bundle-version':a.bundle_version,
}}]}
with open(a.output,'wb') as f:
    plistlib.dump(manifest,f,fmt=plistlib.FMT_XML,sort_keys=False)
print(Path(a.output).resolve())
