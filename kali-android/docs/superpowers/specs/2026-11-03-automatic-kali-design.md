# Automatic Kali desktop setup

The user selected first-use Internet download and explicitly requested autonomous execution without further questions. This opts out of further design/plan approval rounds. Continue on the existing local feature branch and preserve the manual0.1.1 app's disks.

## Outcome

Opening the app performs download, integrity verification, guest filesystem preparation and desktop startup automatically. Later opens return to a running desktop or boot the installed guest. No image picker, resource configuration, login/password entry or Start button is required for the ordinary path. First use and cold boot have real transfer/preparation time; display measured progress and never a simulated desktop.

## Chosen approach

The original official Kali download endpoints remain blocked by enforced cloud egress policy. A different, supported distribution is available through allowed Docker registry endpoints: **Kasm Technologies' Kali Rolling Desktop1.19.0**, a vendor-published Kali-based desktop containing Kali packages. This is not the official Kali QEMU image and must be attributed accurately. Registry manifest digest: `sha256:e1734859c9c508c41c0f30cb33cfa56c9d9a7044a4250dc9ae0be078792623d4`; six ordered layers total4,753,409,720 compressed bytes before transport deduplication. Verify every immutable layer digest. Source publishers: `kasmtech/workspaces-images` and `kasmtech/workspaces-core-images`.

Use a matching, verified Debian Linux amd64 kernel and a small custom initramfs to boot a real Linux VM with guest root, then provision the vendor root filesystem locally. The image remains Kali userspace/repositories; the VM kernel is Debian Linux. The existing Limbo/QEMU native engine and SDL desktop frontend remain, with software emulation and no Android root. A fully offline APK was rejected by the user's selected Internet-first approach; a fake PRoot root environment does not meet the guest-kernel requirement.

## Data and trust

- Pin producer repository, manifest, ordered layers, byte sizes, SHA256 values and validated whiteout metadata in an APK asset. Do not discover mutable latest images on a phone.
- Authenticate Docker's public registry via anonymous scoped tokens; never log tokens or signed CDN query strings. Keep TLS validation and do not forward registry credentials to another origin.
- Download to private staging files with validated range-resume behavior, strict size/hash checks and atomic receipt publication. Enforce actual storage/RAM requirements discovered during image preparation. Show download size before/while transfer and provide cancellation.
- New managed volume lives separately from `files/kali.disk`. Never format an existing unrecognized or mismatched volume or overwrite user disks. Only a newly created managed disk with its expected identity can be initialized.
- Guest setup reads verified image layers through read-only virtual drives, applies OCI whiteouts, preserves ownership/modes and records completion. Use a private Unix serial channel for progress and a desktop-ready marker. Do not equate QMP RUNNING with a ready desktop.
- Configure local desktop auto-login and passwordless guest administrative access for the existing vendor user in the newly provisioned guest. Do not expose host ports or Android privileges. Preserve published licenses and provide boot-payload corresponding-source metadata/artifacts.

## Execution and lifecycle

- Add an automatic bootstrap launcher with progress/error/cancel UI. Keep manual controls as Advanced and preserve their data.
- Boot assets are copied/verified privately. The managed guest uses direct kernel/initramfs boot, a writable sparse ext4 volume, temporary read-only layer drives and a private serial socket.
- A desktop activity retains the real SDL surface while displaying a preparation overlay; remove the overlay only after the guest reports the actual XFCE session ready.
- Use a foreground download service and the existing VM foreground service. Reuse the process-owned session and block duplicate starts. A failed/interrupted setup must retry safely; a completed guest must not be reinstalled.
- Retain the confirmed-only force-stop watchdog. Target Android10+, ARM64 initially; disclose old engine/16KiB-device and physical-phone validation limits.

## Acceptance

Verify producer rootfs identity and installed tools, boot the actual Kali-based desktop with no manual login, exercise download/hash/resume/whiteout/storage/identity/cancellation logic, build/sign the APK and validate Android integration. Use a host QEMU/NBD-backed Android test if copying the full guest into the test AVD would exceed storage; this transport belongs in test tooling, not the default phone workflow. Keep unverified physical-phone/network/tool capabilities distinct. Do not label a loader-only APK as a working Kali release.
