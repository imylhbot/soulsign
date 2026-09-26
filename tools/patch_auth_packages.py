#!/usr/bin/env python3
"""Patch resolved Apple-auth packages for current Apple GSA behavior.

This intentionally patches *resolved package source* rather than only SoulSign UI code,
so the fixes are applied to the code that actually talks to Apple.

Fixes applied when the corresponding source is present:
1. s2k_fo PBKDF2 input: SHA256 digest must be ASCII lower-hex (64 bytes), not hex-decoded.
2. GSA client identity: com.apple.dt.Xcode/... is rejected by Apple's edge in current flows;
   use the AuthKit/akd identity token instead.
3. Avoid logging auth/service tokens in the classic Objective-C AltSign implementation.

The script is idempotent and fails only if an AltSign/SideSign checkout is found but the
known broken s2k_fo implementation is still present after patching.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

TEXT_EXTS={'.swift','.m','.mm','.h','.hpp','.c','.cc','.cpp'}


def iter_sources(root: pathlib.Path):
    if not root.exists():
        return
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in TEXT_EXTS:
            try:
                yield p, p.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue


def patch_file(path: pathlib.Path, text: str) -> tuple[str,list[str]]:
    changes=[]
    original=text

    # SideStore issue #1448: on the s2k_fo path this call used a decoder with the
    # opposite semantics.  SideStore's reported fix uses CoreCryptoBridge's encoder.
    broken='let inputDigest: Data = isHexadecimal ? digest.hexadecimal() : digest'
    fixed='let inputDigest: Data = isHexadecimal ? Data(digest.hexEncodedString().utf8) : digest'
    if broken in text:
        text=text.replace(broken,fixed)
        changes.append('fixed s2k_fo digest encoding')

    # Cover formatting variants of the same regression.
    text2,n=re.subn(
        r'let\s+inputDigest\s*:\s*Data\s*=\s*isHexadecimal\s*\?\s*digest\.hexadecimal\(\)\s*:\s*digest',
        fixed,
        text,
    )
    if n:
        text=text2
        if 'fixed s2k_fo digest encoding' not in changes:
            changes.append('fixed s2k_fo digest encoding')

    # Apple began rejecting X-MMe-Client-Info values that name Xcode. Replace only
    # the embedded client application token; keep model/OS values supplied by the
    # anisette identity untouched so a persisted machine identity remains stable.
    text2,n=re.subn(r'com\.apple\.dt\.Xcode/[0-9][0-9A-Za-z._-]*', 'com.apple.akd/1.0', text)
    if n:
        text=text2
        changes.append(f'replaced Xcode client token ({n})')

    # Also cover a common literal without a version suffix.
    text2,n=re.subn(r'com\.apple\.dt\.Xcode(?=[)>"\'])', 'com.apple.akd', text)
    if n:
        text=text2
        changes.append(f'replaced bare Xcode client token ({n})')

    # Old AltSign logs the actual xcode auth token. Do not leak it to console logs.
    token_log_re=re.compile(r'NSLog\(@"Got token for %@!\\nExpires: %@\\nValue: %@\\n",\s*app,\s*expirationDate,\s*token\s*\);')
    text2,n=token_log_re.subn('NSLog(@"Got token for %@; expires: %@", app, expirationDate);', text)
    if n:
        text=text2
        changes.append('removed auth token logging')

    if text != original:
        path.write_text(text, encoding='utf-8')
    return text,changes


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', action='append', required=True, help='Root to scan; may be repeated')
    args=ap.parse_args()

    candidate_files=[]
    changed=0
    for raw in args.root:
        root=pathlib.Path(raw).expanduser().resolve()
        if not root.exists():
            print(f'[auth-patch] skip missing root: {root}')
            continue
        for path,text in iter_sources(root):
            lower=str(path).lower()
            # Keep scan reasonably targeted while still catching vendored auth packages.
            if not any(k in lower for k in ('altsign','sidesign','anisette','gsacontext','authentication')):
                continue
            candidate_files.append(path)
            _,changes=patch_file(path,text)
            if changes:
                changed+=1
                print(f'[auth-patch] {path}: ' + '; '.join(changes))

    print(f'[auth-patch] scanned {len(candidate_files)} candidate files; changed {changed}')

    # Hard fail only on the known broken implementation if it survived.
    leftovers=[]
    for raw in args.root:
        root=pathlib.Path(raw).expanduser().resolve()
        if not root.exists():
            continue
        for path,text in iter_sources(root):
            if 'digest.hexadecimal()' in text and 'isHexadecimal' in text and 'GSA' in str(path):
                leftovers.append(str(path))
    if leftovers:
        print('[auth-patch] ERROR: broken s2k_fo implementation still present:', file=sys.stderr)
        for p in leftovers:
            print('  '+p, file=sys.stderr)
        return 21
    return 0

if __name__=='__main__':
    raise SystemExit(main())
