# Automatic Kali desktop development build

The launcher prepares a private VM without Termux, Android root, an image picker or a guest password prompt. First preparation downloads approximately4.75GB of compressed layers, verifies every SHA256, pads read-only virtual drives to512 bytes, and allocates a sparse32GiB root volume. At least18GiB free app storage and4GiB reported RAM are currently required. An8GiB phone is recommended. Software emulation can be very slow; this is a development build.

## Provenance

Userspace: Kasm Technologies `kasmweb/kali-rolling-desktop:1.19.0`, amd64 manifest `sha256:e1734859c9c508c41c0f30cb33cfa56c9d9a7044a4250dc9ae0be078792623d4`. This is the publisher's Kali-based desktop distribution, not Kali's official QEMU image. `/etc/os-release` identifies Kali Rolling2026.3. Inspected installed packages include XFCE4.20.1, LightDM1.33.1, nmap7.99, sqlmap1.10.9, Hydra9.7, John1.9, aircrack-ng1.7 and Metasploit6.5.3. Package presence does not guarantee every tool's operation in a VM.

Kernel: Debian `linux-image-6.1.0-54-amd64` version6.1.190-1, with matching modules. The kernel is not Kali's customized kernel. A minimal BusyBox init program installs verified OCI layers as real guest root, configures local XFCE autologin and passwordless guest sudo, then boots systemd. `Root Terminal` opens an administrator shell inside the VM. Android hardware permissions are unchanged: phone Wi-Fi monitor/injection, Android kernel access and arbitrary USB hardware are not provided by guest root.

The APK pins its boot kernel/initramfs hashes and OCI profile. Downloads use TLS and a scoped anonymous registry token. Cross-origin redirects strip Authorization. Completed desktop data is kept under app-private `files/managed`; the old manual `files/kali.disk` is separate. Uninstalling the app deletes private guest data.

## Build

Existing Android toolchain setup: see BUILDING.md. Run:

```
python3 scripts/gradle.py :kali-core:test :kali-app:assembleDebug :kali-app:lintDebug
```

The gzip initramfs is named `initrd.bin` to prevent Android asset packaging from transparently decompressing `.gz` files. The boot assets are bundled in `engine/kali-app/src/main/assets/managed/`. Rebuild them using `tools/guest/build-payload.py` after preparing the unprivileged Docker builder described below. No privileged host mounts are required.

The builder is Debian bookworm-slim with authenticated Debian packages `qemu-system-x86 qemu-utils e2fsprogs linux-image-amd64 busybox-static cpio curl`. Mount the session CA read-only, preserve the configured proxy and use `Acquire::https::CaInfo` for HTTPS apt. Bind the project's `.tools/auto-setup` to `/work`. Give `/guestroot` an executable18GiB tmpfs. Container name is `kp-kali-build`; Docker's local socket is used explicitly.

`tools/guest/fetch-rootfs.py` retrieves the immutable OCI manifest and layers, checks their exact SHA256/length, validates archive paths, applies ordered OCI whiteouts inside a chroot and records the profile. It uses the producer registry distribution route, not a proxy for blocked Kali image URLs. Download tokens/signed CDN query strings must never be logged. `tools/guest/build-payload.py` constructs the initramfs, matching module tree, layer metadata and boot profile. The full modules tree is included so the first guest can copy matching modules into its persistent root. Full initramfs is approximately121MB compressed.

Matching Debian corresponding-source packages are supplied in `sources/guest/` with SHA256SUMS. They were downloaded using authenticated apt source metadata: Linux6.1.190-1, BusyBox1.35.0-4+deb12u1, e2fsprogs1.47.0-2, util-linux2.38.1-5+deb12u3 and glibc2.36-9+deb12u14. Debian binary rebuild suffixes (+b1/+b2) do not change the source versions. Use the Debian package build instructions and included source rules to rebuild. Existing Limbo/QEMU corresponding sources remain under sources/ with their own manifest; a full native Android rebuild remains unverified.

## Recovery and readiness

Transfers retain `.part` files for resume and publish only verified sector-padded payloads. Ready receipts skip the large image downloads on subsequent starts. Storage capacity is checked before first preparation; retries do not reapply the initial reservation after their own files consume space. Installation is idempotent until the guest completion marker is written. UUID/profile mismatches preserve the disk. Previously ready volumes are explicitly forbidden from entering the formatting branch, even if their UUID becomes unreadable.

QMP CPU execution does not count as desktop readiness. The guest must report root UID0, sudo UID0 and a matching manifest digest after the local user's XFCE session and panel exist. The setup overlay stays visible until that proof. Serial errors/logs are available via Advanced diagnostics. Shutdown uses guest ACPI first; confirmed force stop retains the disk but can damage unsaved guest work.

The native engine is older QEMU5.1/Limbo6.0.1. Use trusted guest images only. Newer Android16KiB-page devices and actual ARM64 phone performance remain unverified.
