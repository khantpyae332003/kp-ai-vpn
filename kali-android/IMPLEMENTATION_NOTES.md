# Decisions and review record

## Decisions made during implementation

1. Used a new feature-branch repository in the existing isolated cloud workspace, without a worktree. The website checkout was preserved. There is no merge or publication to a remote repository.
2. Reused unmodified native engine libraries and firmware from the official Limbo6.0.1 APK, pinned by SHA256 and fetched over verified HTTPS. This produced a functioning QEMU baseline sooner than an unverified new JNI implementation. The cost is reliance on QEMU5.1.0 and an unverified native source rebuild. Source archives and upstream makefiles/patches accompany the app; this is explicitly a development build for trusted images.
3. Retained Android target API29 for the inherited engine/frontend compatibility in this initial sideloaded build, while compiling with SDK33. The Play-target lint finding remains visible as a warning. The cost is that this is not a Play Store-ready or modern-target-certified application.
4. Chose private copied disks and BIOS amd64 guests for the first flow; no external image download or automatic OS installation. The cost is storage duplication and the need for the user to provide a compatible disk.
5. Kept the new `feat/kali-vm` branch and source locally. This new repository has no base branch or configured remote to merge/publish into; APK/source delivery was requested. The cost is that no remote repository or store release was created.

## Review fixes

- Abandoned import staging files are reclaimed once per process before imports are accepted. Recovery is synchronized with the in-process import owner and never deletes the VM disk.
- Native diagnostics are captured to a bounded app-only log; the previous launch is preserved before retry. The startup screen can display current/previous log tails and a best-effort app-UID-filtered snapshot for the prior VM process after native exit.
- Native return sets `EXITING`, which retains the terminal result for reopening and blocks new imports/launches during the service's teardown and process exit.
- A confirmed Force stop has an own-process-only watchdog when native QMP/cleanup is stuck. The termination deadline is never armed by ordinary shutdown or by cancelling confirmation. This preserves a usable Stop control without claiming a safe guest filesystem shutdown.
- Repeated unchanged text updates are avoided to prevent accessibility-event churn; UI tests reject stale hierarchy snapshots.
- Desktop toolbar is visible by default so Android Back can return to launcher controls while the VM remains owned by the foreground service. Real Android activity behavior is checked separately from the small shared-state unit test.

## Review scope decisions

The reviewer correctly declined to infer Kali desktop/tool/network/ARM64-phone success from compilation or a BIOS fixture. Those remain unverified. Native rebuild equivalence is likewise unverified. Source archives/notices are supplied without claiming a full legal audit. Clean bootstrap/repeat was tested by the implementer. The target API29 choice is intentional and disclosed. No unrelated upstream defects are represented as fixed, and no deployment or store release was performed.

No Minor findings were deferred by the independent reviewer. Nonblocking lint warnings and the unverified capabilities above remain documented limitations.
