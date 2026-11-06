# Kali Android Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Deliver an Android app running a genuine QEMU guest without Android root.

**Architecture:** Adapt a verified Android QEMU implementation, retaining its native engine and embedded desktop viewer. Add a focused Kali import/setup flow and resource configuration, with VM state held independently of activity recreation.

**Tech Stack:** Android SDK/NDK, upstream-compatible Gradle/JDK, QEMU TCG, embedded guest display; application language follows the selected upstream.

**Spec:** `docs/superpowers/specs/2026-11-02-kali-android-design.md`

## Global Constraints
- Android 10+ and arm64-v8a are initial defaults.
- No Android root or KVM requirement; no fake guest-root or hardware-access claims.
- Keep `/workspace/kp-ai-vpn` unchanged. Work under `/workspace/kali-android`.
- Preserve TLS and artifact verification. No bundled passwords or secret values.
- Respect upstream licenses and preserve source provenance.

## Review Focus
- Nonbootable or incompatible imports must produce clear diagnostics.
- Low storage and interrupted imports must not replace a valid disk.
- Activity recreation must not duplicate or terminate a running VM accidentally.
- Resource limits and duplicate Start requests must be validated.
- Forced stop must warn about guest filesystem damage and retain disks.

### Task 1: Establish a real Android QEMU baseline
**Files:** `upstream/`, `BUILDING.md`, `THIRD_PARTY_NOTICES.md`, upstream build files.
**Interfaces:** Produces a pinned, licensed engine source tree and the documented Android build command; record the upstream VM launch/display APIs for Task 3.
- [x] Inspect official upstream Limbo source and release/build documentation; verify ABI, minimum Android API, embedded display, firmware, disk formats, and engine packaging. Record the exact commit and license.
- [x] Installed the pinned SDK/JDK/Gradle through verified sources and built the baseline with unmodified official native libraries. **Deviation:** native NDK source recompilation was not verified; the pinned release runtime and corresponding source are supplied instead (see IMPLEMENTATION_NOTES.md).
- [x] Verify the APK contains arm64 engine libraries and required runtime assets; document what was built versus device-tested. If the engine cannot be built or licensed for this use, diagnose and resolve before presenting an app as functional.

### Task 2: Safe Kali import and VM configuration
**Files:** application import/configuration components, associated tests, user instructions (exact source paths follow the upstream inspection in Task 1).
**Interfaces:** Produces a persisted private disk path plus validated guest architecture, memory MiB, CPU count and boot mode for the upstream launch API.
- [x] Write failing tests for unsupported image type, low storage, interrupted copy, invalid resource limits, and replacing an existing disk.
- [x] Implement document-picker import using a staging file, available-space checks, cancellation cleanup, and explicit replacement confirmation. Validate file metadata against the supported upstream disk/boot formats.
- [x] Implement persisted configuration with bounds constrained by the engine and available device resources. Explain guest root and hardware limitations in the setup flow.
- [x] Ran import/resource/recovery tests and actual Android orphan recovery. **Not verified:** a large real-image import through the Android document picker.

### Task 3: Desktop and VM lifecycle
**Files:** application launch controls, lifecycle service, upstream display integration, tests, `README.md`.
**Interfaces:** Consumes Task 2 configuration and Task 1 launch/display API; exposes stopped/starting/running/stopping/error states to the UI.
- [x] Write failing tests for duplicate start, launch error propagation, activity recreation, graceful shutdown timeout, and confirmed force stop retaining the disk.
- [x] Integrate the engine and desktop viewer. Keep lifecycle ownership outside the activity, use an Android-compliant foreground service/notification while running, and disable conflicting controls during transitions.
- [x] Wire Start, graceful shutdown and confirmed force stop to actual engine operations. Show actionable startup logs without leaking credentials.
- [x] Run tests, assemble the debug APK and inspect packaged ABI/assets. Booted the labelled native BIOS fixture on Android. **Not verified:** real Kali OS boot, guest sudo/tool/network behavior, full desktop usability, and a physical ARM64 phone.
- [x] Deliver APK, reproducible build instructions, license/source information, and explicit unverified checks or blockers. Never describe compilation alone as a successful Kali boot.
