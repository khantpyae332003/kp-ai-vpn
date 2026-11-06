# KP Kali VM for Android — development build

A standalone Android front end to the actual Limbo/QEMU engine. No Termux or Android root is needed. This project is separate from `kp-ai-vpn`.

**Release withheld:** existing APKs are development candidates. Full Android install, visible desktop and reopen verification must finish before an APK is offered as validated.

## Automatic setup — version0.2.2 development build

Install and open the APK. The default launcher automatically downloads the pinned Kasm Kali-based desktop, installs it into a private VM and opens XFCE without an image picker or password prompt. First setup needs about4.75GB Internet download,18GiB free storage and4GiB reported RAM;8GiB RAM is recommended. A Root Terminal shortcut provides guest administrator access. This uses a Debian kernel and Kasm's Kali userspace, not an official Kali QEMU appliance. See [automatic setup details](docs/automatic-setup-build.md) and [actual validation limits](VALIDATION.md).

Real Kali XFCE and guest root/sudo were demonstrated in host QEMU. Android testing has verified the complete pinned download and actual Linux kernel boot in a6GiB software emulator. Versions0.2.1/0.2.2 fix missing Linux boot ROMs, idle serial disconnects and protocol loss when diagnostic logging fails, with real Android regressions. Full automatic Android installation, its visible desktop and an ARM64 phone remain unverified; see `VALIDATION.md`.

## Advanced manual import (retained)

1. Install the debug APK on an Android10+ ARM64 phone. x86_64 is also packaged for emulator testing. This initial engine supports conventional 4 KiB-page devices; 16 KiB-page devices have not been verified.
2. Obtain a trusted **standalone amd64 BIOS bootable** Kali QCOW2 or raw PC disk. Verify its publisher's signatures/checksums, and extract any ZIP/7z wrapper first. ISO installers, ARM images, NetHunter rootfs tarballs, VMDK/VDI, encrypted/backed QCOW2 disks and UEFI-only disks are not supported by this first import flow. A file with the right extension alone is not enough.
3. Choose the disk in the app. It is copied into private app storage. Keep enough free space for both the imported disk and future guest disk growth. Import validates the basic disk header; it does not authenticate the OS or prove that the disk boots Kali.
4. Choose RAM and CPUs; default is at most half of physical phone RAM, capped at1024MiB. Up to4096MiB and four CPUs are allowed subject to phone resources. Kali's desktop can require 2GB or more. Start the VM; software emulation may take several minutes or be impractical on low-memory phones.
5. Use the embedded desktop's keyboard/mouse controls. Android Back returns to the VM controls while the foreground service retains the guest. Log in with the account belonging to **your image** and use `sudo` inside Kali. No default password is hardcoded in the app. Available root privileges belong to the guest only.
6. Shut down inside the guest or request guest shutdown in the launcher. If it does not power off, save your work before confirming Force stop. Stopping the guest may close the app to unload native libraries; reopen to run it again. The private disk is retained. Replacing it discards the previous guest data after successful import; uninstalling the app deletes the disk.

In version0.1.1, a confirmed Force stop also arms a five-second watchdog that closes this app's own process if the native engine cannot exit. Graceful shutdown and its timeout alone never arm this watchdog. Abrupt stopping can corrupt the guest filesystem, as the confirmation dialog explains.

## Limits

Guest root does not grant Android root, phone Wi-Fi monitor mode, hardware packet injection or host kernel access. User-mode guest networking is used without forwarded host ports. Tools depending on unavailable hardware will not work; there is no promise that all Kali tools work. The APK bundles its boot kernel/initramfs; the managed flow downloads the pinned Kali desktop layers for automatic installation. It is not affiliated with Kali Linux or Offensive Security.

The original native engine is QEMU5.1.0 from Limbo6.0.1. Use trusted local images only; this is not a production-hardened VM isolation boundary or a Play Store release. Current verification results are recorded in `VALIDATION.md`, including distinctions between compilation, emulator guest execution, and untested Kali/physical-phone boot.

If startup exits unexpectedly, reopen the app and choose **Startup diagnostics**. Logs are bounded, private to the app, and the previous launch is preserved before retrying. Android may clear cached files or old system logs, so diagnostics are best-effort. Unfinished disk-import staging files are recovered on the next process launch; the existing VM disk is kept.

Build instructions: [BUILDING.md](BUILDING.md). Licensing: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
