# Automatic Kali Desktop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. The user explicitly requested no further questions; proceed autonomously and keep a ledger.

**Goal:** First-open automatic preparation and subsequent automatic startup of a real Kali-based desktop VM.

**Architecture:** Pin Kasm's Kali OCI root filesystem, boot it using a verified Debian kernel/initramfs, and adapt the existing QEMU/SDL app with a managed setup launcher and guest progress/readiness protocol.

**Tech Stack:** Android Java/SDK33, existing Limbo/QEMU5.1 native libraries, Java HTTP/filesystem core, Linux guest scripts, Docker-isolated build tooling.

**Spec:** `docs/superpowers/specs/2026-11-03-automatic-kali-design.md`

## Global Constraints
- Android10+ ARM64; no Android root, no Termux, no user image-selection/login step for the happy path.
- Preserve existing `files/kali.disk` and valid managed guest data.
- Pin OCI manifest `sha256:e1734859c9c508c41c0f30cb33cfa56c9d9a7044a4250dc9ae0be078792623d4`; no disabled TLS/digest/package verification.
- Attribute the desktop to Kasm's Kali-based image and the kernel to Debian. No claim of the official Kali QEMU image.
- Use the existing cloud checkout; no worktree or remote publishing required.

## Review Focus
- Cross-origin redirects must not leak registry tokens.
- Partial downloads, invalid ranges and corrupt bodies must not publish verified receipts.
- Existing/unknown volumes must never be silently reformatted.
- Guest CPU RUNNING is insufficient to dismiss the setup overlay.
- Reopening, cancellation and process death must not start duplicate guests or reinstall completed ones.

### Task1: Produce and prove the guest boot profile
**Files:** `tools/guest/`, `guest/`, `engine/kali-app/src/main/assets/managed/`, `docs/automatic-setup-build.md`.
**Interfaces:** Produces `profile.json` (producer/digest, ordered layer digests/sizes/whiteouts, kernel/initrd/module payload hashes, minimum storage, volume size) and guest progress lines `KP:PHASE:<name>` / `KP:DESKTOP_READY:<manifest-digest>` on a private serial socket.
- [ ] Fetch producer metadata and blobs using the existing proxy, verify SHA256 before use and validate archive paths/whiteouts. Inspect `/etc/os-release`, required desktop components and actual installed Kali tools.
- [ ] Prepare kernel/initramfs/modules and corresponding-source metadata from authenticated Debian packages. Build isolated root filesystem/volume without modifying the website or using privileged host mounts.
- [ ] Implement idempotent guest provisioning, managed-volume identity checks, desktop auto-login and actual XFCE-readiness reporting. Preserve failures as diagnostics.
- [ ] Boot the real guest with host QEMU and capture its desktop/root identity. Diagnose boot failures before registering a ready profile.

### Task2: Verified, resumable managed setup core
**Files:** `engine/kali-core/src/main/java/com/kp/kali/core/` and corresponding JUnit tests.
**Interfaces:** `VerifiedTransfer.download(...)` commits only exact-size SHA256-verified padded payloads; a managed receipt tracks image identity/UUID/stage; a serial protocol parser emits readiness only for the selected image.
- [ ] Write failing tests for interrupted/range-restarted downloads, bad size/hash, cross-origin authorization stripping, cancellation, identity mismatch and incorrect/premature readiness.
- [ ] Implement the minimum tested transfer/state/storage/receipt/protocol behavior; use atomic writes and bounded progress.
- [ ] Run the complete core suite and verify the affected tests fail before implementation and pass afterwards.

### Task3: Automatic Android workflow and real VM integration
**Files:** `BootstrapActivity.java`, download service/controller, managed desktop activity, `KaliRuntime.java`, `KaliMachineBridge.java`, manifest/resources and Android smoke tooling.
**Interfaces:** Consumes Task1 profile/assets and Task2 core; starts one managed guest with direct kernel boot and private serial progress, preserving the Advanced manual path.
- [ ] Integrate automatic download and safe volume creation with foreground notification, honest progress and retry/cancel behavior.
- [ ] Build managed QEMU boot arguments, consume actual guest status and overlay the real SDL surface until XFCE is ready. Auto-return/open on normal launch without a manual setup step.
- [ ] Verify restart/reopen, cancellation, guest readiness and data preservation. Use actual Linux/Kali evidence rather than the BIOS fixture.
- [ ] Run core tests/build/lint/signature checks, request one fresh read-only review, fix material findings, package APK/source and report exact validation limits.
