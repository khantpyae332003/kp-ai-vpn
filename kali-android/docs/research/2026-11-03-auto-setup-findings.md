# Automatic Kali setup: requirements and verified findings

## User-selected workflow

The user selected first-launch Internet-based automatic download/install. After preparation, opening the app should launch the actual Kali desktop without image selection, resource configuration, manual login or a Start button. First installation and subsequent guest boot necessarily take time; show honest progress rather than an imitation desktop.

This is a new feature beyond the released0.1.1 manual-import development APK. No automatic-installer product code has been written yet.

## Verified official documentation

Official documentation repository: `https://gitlab.com/kalilinux/documentation/kali-docs.git`, inspected at commit `d3810ed3568665c9cb989f931c4d53d052ef16cb`.

- `virtualization/import-premade-qemu/index.md` specifies `kali-linux-<VERSION>-qemu-amd64.7z`, extracting a standalone QCOW2 image. Its example uses2GB RAM and two CPUs. It documents a normal guest login, so downloading and launching this image alone does **not** satisfy zero-manual-login desktop startup.
- `introduction/download-images-securely/index.md` requires authenticating `SHA256SUMS` with `SHA256SUMS.gpg` before verifying the image hash. The documented current signing-key fingerprint is `827C8569F2518CC677FECA1AED65462EC8D5E4C5`; key retrieval is `https://archive.kali.org/archive-key.asc`. This fingerprint is public verification metadata, not a credential.
- `introduction/download-official-kali-linux-images/index.md` directs users to official sources and authenticated checksums.

## Required behavior for the design

- Pin a verified release/image profile after inspecting official metadata. Do not invent image URLs, checksums, compressed/extracted sizes, boot partition details or supported guest defaults.
- Download, verify and unpack automatically to a private staging location; commit readiness atomically only after installation/provisioning succeeds. Resume or restart interrupted downloads safely; retain a valid installed guest and all user data.
- Show measured transfer progress, integrity/extraction/guest-preparation status, storage requirements and actionable retry/cancel options. Do not assume first use is instantaneous.
- Configure the guest's actual desktop auto-login and confirm its readiness. Guest provisioning must be reproducible and tested on the real Kali image; a BIOS fixture or QMP CPU RUNNING alone cannot establish this.
- Determine a feasible provisioning route after inspecting the image. One candidate is a matching verified kernel/initramfs boot profile and a private Unix serial channel for first-boot guest configuration, followed by ordinary installed-disk boots. This is a research candidate, not a validated implementation decision.
- Choose safe RAM/CPU defaults from device resources; reopen an existing live VM rather than launching another one. Preserve existing manually imported disks; do not overwrite them silently when adding a managed automatic image.
- Continue to provide guest root only. Android root and direct phone Wi-Fi hardware capabilities remain unavailable.

## Current external blocker

The cloud machine's enforced restricted HTTP policy returned proxy `403 CONNECT` for `https://cdimage.kali.org/current/` and `https://www.kali.org/get-kali/`. Therefore the actual image artifact, signed release manifest, extracted disk and guest desktop provisioning have not been inspected or validated.

A configuration draft was successfully saved adding only these official workflow destinations, preserving the existing n8n custom domain and package-manager presets:

- `www.kali.org`: official image/release documentation
- `cdimage.kali.org`: release manifests and images
- `kali.download`: official image/package download destination
- `archive.kali.org`: archive signing key and archive metadata
- `http.kali.org`: official package metadata/artifacts if matching guest boot files are required

Draft saving did not apply or publish the change. The tool returned `requires_publish: true`. The user must review/save the network changes in environment settings and publish the environment, then the affected official read-only requests must be retried. Do not bypass the network proxy, use arbitrary image mirrors, disable TLS/signature checks, or substitute a fake image to claim completion.

After network access works: inspect the exact artifact and provisioning prerequisites, complete/review the design, write the implementation plan, implement automatic setup/startup and validate actual Kali desktop readiness on Android. Existing manual APK artifacts remain available while this work is blocked.
