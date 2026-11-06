# Rootless Kali virtual machine for Android

Approved direction: a standalone Android application using QEMU software emulation, with Kali desktop display, disk-image import, start/stop, and configurable memory/CPU. Keep the existing kp-ai-vpn website unchanged.

## Goals and constraints
- Run without Android root. Guest root is confined to the virtual machine; never promise host root, Wi-Fi monitor mode, packet injection, or universal tool compatibility.
- Initial target: arm64-v8a Android phones, Android 10 or newer. This is an implementation default, not a confirmed phone specification.
- Use software emulation (TCG), not privileged KVM. Performance depends on the phone and guest architecture.
- Import a user-provided Kali virtual disk through Android's document picker and copy it into private app storage. Disk images are large and are not bundled in the APK.
- Display the guest desktop within the app. Manage VM lifecycle explicitly and provide usable diagnostics when startup fails.
- Preserve disk data on stop. Confirm forced shutdown and warn about guest filesystem damage. Do not overwrite imported disks silently.
- Guest networking uses QEMU user-mode networking. No host port forwarding by default.

## Approaches
PRoot is lightweight but does not provide real guest kernel/root behavior. QEMU, selected by the user, provides an independent guest OS with guest root at a performance cost. Remote hosting requires another machine and does not satisfy a local standalone application.

## Implementation decisions and feasibility
Prefer adapting an established open-source Android QEMU implementation (candidate: Limbo) to writing a new emulator/JNI stack. Verify upstream source, licenses, Android API/ABI support, disk formats, firmware requirements, display integration, and reproducible native build before adopting it. Ship all required runtime libraries, firmware, license notices, and corresponding-source instructions. Never download arbitrary executable engines at runtime.

Image import must explain compatible guest architecture, disk format and boot mode based on the verified engine. A root filesystem tarball alone is not a bootable VM disk. Direct Kali image download is deferred until a compatible official artifact and its signed verification procedure are established. No credentials are embedded.

## Acceptance
Produce a buildable Android project and debug APK, test import/configuration/lifecycle failure cases, and boot a compatible guest on an Android arm64 device/emulator when available. Report build verification separately from actual Android/Kali boot verification. No simulated desktop may be represented as a working Kali VM.
