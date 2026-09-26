#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import re
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count < 1:
        raise RuntimeError(f"{label}: expected at least 1 match, found 0")
    if count > 1:
        print(
            f"SoulSign patch warning: {label}: found {count} matches; patching the first one",
            file=sys.stderr,
        )
    return text.replace(old, new, 1)


def _target_block_range(text: str, target_name: str) -> tuple[int, int]:
    """Return the character range of a two-space-indented XcodeGen target block."""
    header_re = re.compile(rf"(?m)^  {re.escape(target_name)}:\s*$")
    match = header_re.search(text)
    if not match:
        raise RuntimeError(f"project.yml: target '{target_name}' not found")

    start = match.start()
    pos = match.end()
    # A target ends at the next top-level key or sibling target. Nested target
    # content is indented by >= 4 spaces, so <= 2 spaces marks the boundary.
    boundary_re = re.compile(r"(?m)^(?:[^ \t\r\n][^\r\n]*|  [^ \t\r\n][^\r\n]*):\s*$")
    boundary = boundary_re.search(text, pos)
    end = boundary.start() if boundary else len(text)
    return start, end


def _patch_main_target(text: str) -> str:
    start, end = _target_block_range(text, "Seal")
    block = text[start:end]

    # Only rename the main application target. MJorb currently contains another
    # CFBundleDisplayName: Seal in a secondary target, so whole-file uniqueness
    # is intentionally NOT required here.
    if "CFBundleDisplayName: SoulSign" not in block:
        count = block.count("CFBundleDisplayName: Seal")
        if count < 1:
            raise RuntimeError("display name: main Seal target has no CFBundleDisplayName: Seal")
        block = block.replace("CFBundleDisplayName: Seal", "CFBundleDisplayName: SoulSign", 1)

    block = block.replace(
        "NSLocalNetworkUsageDescription: Seal 通过本地通道连接此设备并安装应用。",
        "NSLocalNetworkUsageDescription: SoulSign 通过本地通道连接此设备并安装应用。",
    )

    # Keep existing URL schemes for compatibility and add SoulSign exactly once.
    if re.search(r"(?m)^\s*- soulsign\s*$", block) is None:
        block, n = re.subn(
            r"(?m)^(\s*)- seal\s*$",
            r"\1- soulsign\n\1- seal",
            block,
            count=1,
        )
        if n == 0:
            print("SoulSign patch warning: main target URL scheme '- seal' not found; leaving schemes unchanged", file=sys.stderr)

    # v8 stability: do not add BGTaskScheduler keys during bootstrap.
    # Sideload/resign tools may rewrite the main bundle identifier, while a static
    # BGTask identifier remains unchanged. Keep automatic renewal in the foreground
    # until the bootstrap/signing path is proven stable on the target device.


    return text[:start] + block + text[end:]


def patch_project(repo: pathlib.Path, minimum_ios: str) -> None:
    path = repo / "project.yml"
    text = path.read_text(encoding="utf-8")

    # Keep internal target/scheme names as Seal for upstream build-script compatibility.
    text = _patch_main_target(text)

    # Keep upstream bundle identifiers and entitlement namespaces intact in v8.
    # Changing only project.yml identifiers while source/entitlement assumptions stay
    # upstream-compatible can make a re-signed app launch and immediately terminate.
    # SoulSign branding is therefore display-name/UI only for the stable bootstrap.

    # SoulSign v10 baseline is iOS 15.0.  This matches the current Anisette/SwiftUI
    # floor used by the auth stack and avoids pretending that iOS 14 is supported.
    if minimum_ios != "15.0":
        raise RuntimeError("SoulSign v10 requires --minimum-ios 15.0")

    # XcodeGen projects may express the deployment target in more than one place.
    # Normalize the common forms without changing macOS/watchOS/tvOS settings.
    text = re.sub(r'(?m)^(\s*iOS:\s*)["\']?\d+(?:\.\d+)?["\']?\s*$', r'\g<1>"15.0"', text)
    text = re.sub(r'(?m)^(\s*deploymentTarget:\s*)["\']?16(?:\.0)?["\']?\s*$', r'\g<1>"15.0"', text)
    text = re.sub(r'(?m)^(\s*IPHONEOS_DEPLOYMENT_TARGET:\s*)["\']?16(?:\.0)?["\']?\s*$', r'\g<1>"15.0"', text)

    path.write_text(text, encoding="utf-8")


def patch_apps_view_model(repo: pathlib.Path) -> None:
    path = repo / "Seal/Features/Apps/AppsViewModel.swift"
    text = path.read_text(encoding="utf-8")

    # Make the existing launch check also run the SoulSign 24h threshold scan.
    old_launch = """    func performLightweightLaunchCheck() async {\n        await load(force: true)\n    }\n"""
    new_launch = """    func performLightweightLaunchCheck() async {\n        await load(force: true)\n        soulSignAutoRenewIfNeededForeground()\n    }\n"""
    text = replace_once(text, old_launch, new_launch, "launch auto-renew hook")

    old_block = """    private func continueSigningRequest(\n        for app: AppRecord,\n        availableAccounts: [AppleAccountRecord]\n    ) {\n        if app.belongsInInstalledList {\n            guard let accountID = app.accountID,\n                  let account = availableAccounts.first(where: { $0.id == accountID }) else {\n                alertFailure = ImportFailure(\n                    title: \"签名账号不可用\",\n                reason: \"上次签名这个应用的 Apple ID 已被删除或凭据失效。\",\n                recovery: \"在「我的」中重新添加原 Apple ID，或用当前账号重新签名安装\",\n                    code: \"SEAL-AUTH-104c\"\n                )\n                return\n            }\n            startSigning(app: app, account: account)\n        } else if let activeAccountID,\n                  let account = availableAccounts.first(where: { $0.id == activeAccountID }) {\n            startSigning(app: app, account: account)\n        } else if availableAccounts.count == 1, let account = availableAccounts.first {\n            startSigning(app: app, account: account)\n        } else {\n            accountSelectionApp = app\n        }\n    }\n"""

    new_block = """    // MARK: - SoulSign account pool\n\n    private static let soulSignMaxAppsPerAccount = 3\n    private static let soulSignLastAssignedAccountKey = \"soulsign.accountPool.lastAssignedAccountID\"\n\n    private func soulSignAssignedAppCount(for accountID: UUID) -> Int {\n        installedApps.filter { app in\n            app.isSeal == false && app.accountID == accountID\n        }.count\n    }\n\n    private func soulSignAccountHasCapacity(_ account: AppleAccountRecord) -> Bool {\n        soulSignAssignedAppCount(for: account.id) < Self.soulSignMaxAppsPerAccount\n    }\n\n    private func soulSignRememberAssignedAccount(_ id: UUID) {\n        UserDefaults.standard.set(id.uuidString, forKey: Self.soulSignLastAssignedAccountKey)\n    }\n\n    private func soulSignAutomaticAccount(from availableAccounts: [AppleAccountRecord]) -> AppleAccountRecord? {\n        let accountsWithCapacity = availableAccounts.filter(soulSignAccountHasCapacity)\n        guard accountsWithCapacity.isEmpty == false else { return nil }\n\n        // First balance by current top-level app count. Among equally used accounts,\n        // continue after the previously assigned account to provide deterministic rotation.\n        let minimumCount = accountsWithCapacity\n            .map { soulSignAssignedAppCount(for: $0.id) }\n            .min() ?? 0\n        let leastUsedIDs = Set(accountsWithCapacity.filter {\n            soulSignAssignedAppCount(for: $0.id) == minimumCount\n        }.map(\\.id))\n\n        let lastID = UserDefaults.standard\n            .string(forKey: Self.soulSignLastAssignedAccountKey)\n            .flatMap(UUID.init(uuidString:))\n\n        if let lastID, let lastIndex = availableAccounts.firstIndex(where: { $0.id == lastID }) {\n            for offset in 1...availableAccounts.count {\n                let candidate = availableAccounts[(lastIndex + offset) % availableAccounts.count]\n                if leastUsedIDs.contains(candidate.id), soulSignAccountHasCapacity(candidate) {\n                    return candidate\n                }\n            }\n        }\n\n        return accountsWithCapacity.first(where: { leastUsedIDs.contains($0.id) })\n    }\n\n    private func soulSignCapacityFailure() -> ImportFailure {\n        ImportFailure(\n            title: \"Apple ID 配额已满\",\n            reason: \"当前所有可用 Apple ID 都已由 SoulSign 分配了 3 个 IPA。\",\n            recovery: \"添加新的 Apple ID，或移除不再使用的已签名应用\",\n            code: \"SOUL-POOL-003\"\n        )\n    }\n\n    private func continueSigningRequest(\n        for app: AppRecord,\n        availableAccounts: [AppleAccountRecord]\n    ) {\n        if app.belongsInInstalledList {\n            // Renewal never rotates an existing app to a different ID automatically.\n            guard let accountID = app.accountID,\n                  let account = availableAccounts.first(where: { $0.id == accountID }) else {\n                alertFailure = ImportFailure(\n                    title: \"签名账号不可用\",\n                    reason: \"上次签名这个应用的 Apple ID 已被删除或凭据失效。\",\n                    recovery: \"在「我的」中重新添加原 Apple ID，或手动选择账号重新签名安装\",\n                    code: \"SEAL-AUTH-104c\"\n                )\n                return\n            }\n            startSigning(app: app, account: account)\n            return\n        }\n\n        guard let account = soulSignAutomaticAccount(from: availableAccounts) else {\n            alertFailure = soulSignCapacityFailure()\n            return\n        }\n        soulSignRememberAssignedAccount(account.id)\n        Task { [weak self] in await self?.selectActiveAccount(id: account.id) }\n        startSigning(app: app, account: account)\n    }\n"""
    text = replace_once(text, old_block, new_block, "account-pool allocator")

    # Defense-in-depth: guard direct startSigning(...) entry when the current upstream
    # exposes the expected helper. Do not bind this patch to a large surrounding block:
    # MJorb has changed that async path in recent commits. The automatic allocator above
    # remains the primary policy path even if this optional guard cannot be inserted.
    start_guard = """        if app.belongsInInstalledList == false, app.isSeal == false, soulSignAccountHasCapacity(account) == false {
            alertFailure = soulSignCapacityFailure()
            return
        }
        if app.belongsInInstalledList == false {
            soulSignRememberAssignedAccount(account.id)
        }
"""
    start_re = re.compile(
        r"(?m)^(?P<indent>\s*)(?:private\s+)?func\s+startSigning\(\s*app:\s*AppRecord,\s*account:\s*AppleAccountRecord\s*\)\s*\{\s*$"
    )
    start_match = start_re.search(text)
    if start_match:
        probe = text[start_match.end():start_match.end() + 1200]
        if "soulSignAccountHasCapacity(account)" not in probe:
            text = text[:start_match.end()] + "\n" + start_guard + text[start_match.end():]
    else:
        print(
            "SoulSign patch warning: direct-sign capacity guard anchor not found; "
            "continuing with account-pool allocator",
            file=sys.stderr,
        )

    # Manual account picker must also honor capacity for a new app.
    old_select = """    func selectAccount(_ account: AppleAccountRecord, for app: AppRecord) {\n        accountSelectionApp = nil\n        Task { [weak self] in\n"""
    new_select = """    func selectAccount(_ account: AppleAccountRecord, for app: AppRecord) {\n        if app.belongsInInstalledList == false, app.isSeal == false, soulSignAccountHasCapacity(account) == false {\n            accountSelectionApp = nil\n            alertFailure = soulSignCapacityFailure()\n            return\n        }\n        if app.belongsInInstalledList == false {\n            soulSignRememberAssignedAccount(account.id)\n        }\n        accountSelectionApp = nil\n        Task { [weak self] in\n"""
    if old_select in text:
        text = text.replace(old_select, new_select, 1)
    else:
        print(
            "SoulSign patch warning: manual picker capacity guard anchor not found; automatic allocator remains active",
            file=sys.stderr,
        )

    # Insert foreground/background renewal helpers immediately before the existing refreshAll.
    marker = """    func refreshAll() {\n        startBatchRefresh()\n    }\n"""
    renewal_helpers = """    // MARK: - SoulSign expiration / automatic renewal\n\n    private func soulSignHasAppExpiring(within hours: Double = 24, now: Date = Date()) -> Bool {\n        let deadline = now.addingTimeInterval(hours * 60 * 60)\n        return installedApps.contains { app in\n            guard app.isSeal == false, app.accountID != nil, let expiry = app.expiryDate else { return false }\n            return expiry <= deadline\n        }\n    }\n\n    func soulSignAutoRenewIfNeededForeground() {\n        guard soulSignHasAppExpiring(), batchRefreshTask == nil, signingTask == nil else { return }\n        startBatchRefresh()\n    }\n\n    /// Called by BGAppRefreshTask. iOS decides whether/when this task gets CPU time.\n    /// The existing batch-renewal path intentionally disables interactive 2FA, so this\n    /// only succeeds when saved Apple ID sessions and the local install channel are usable.\n    @discardableResult\n    func soulSignAutoRenewInBackground() async -> Bool {\n        await load(force: true)\n        guard soulSignHasAppExpiring() else { return true }\n        guard batchRefreshTask == nil, signingTask == nil, renewalCoordinator != nil else { return false }\n        guard await refreshSigningChannel() else { return false }\n\n        batchRefreshSession = BatchRefreshSession()\n        await runBatchRefresh()\n\n        guard let status = batchRefreshSession?.status else { return false }\n        switch status {\n        case .completed(let result):\n            return result.failed == 0\n        case .preparing, .running, .preparingSealUpdate, .failed:\n            return false\n        }\n    }\n\n""" + marker
    text = replace_once(text, marker, renewal_helpers, "auto renewal helpers")

    path.write_text(text, encoding="utf-8")


def patch_readme(repo: pathlib.Path) -> None:
    path = repo / "README.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    banner = """> **SoulSign fork** — this repository is derived from MJorb/Seal (AGPL-3.0). SoulSign adds Apple-ID pooling (3 user IPAs per ID), automatic account rotation, iOS 15 support, Apple-auth compatibility fixes, 24-hour expiry renewal policy, foreground renewal checks, and SoulSign branding. Upstream notices are retained below.\n\n"""
    if not text.startswith("> **SoulSign fork**"):
        text = banner + text
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--minimum-ios", default="15.0")
    args = parser.parse_args()
    repo = pathlib.Path(args.repo).resolve()

    for required in [repo / "project.yml", repo / "Seal/Features/Apps/AppsViewModel.swift", repo / "Seal/App/SealApp.swift"]:
        if not required.exists():
            raise RuntimeError(f"required upstream file not found: {required}")

    patch_project(repo, args.minimum_ios)
    patch_apps_view_model(repo)
    patch_readme(repo)
    print("SoulSign patch applied successfully")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SoulSign patch failed: {exc}", file=sys.stderr)
        raise
