# Real automatic setup test

Use only the disposable `kali-auto-test` API29 x86_64 AVD. The runner refuses other AVDs, physical phones and a root adbd shell. It clears only that emulator's `com.kp.kali` app data. At least6GiB emulated RAM and48GiB virtual userdata are configured; sparse physical storage still needs enough real host space for approximately17GiB of new data. No KVM is available in this workspace, so transfers/provisioning can be very slow.

`run-managed-setup.py` installs the exact artifact APK, records its SHA256 and the Android resources, launches the ordinary app and observes real private files and guest serial output. It uses no test image, NBD disk, resource-check override or fabricated readiness. `--watch-only` resumes observation without clearing data/installing again. The default deadline is90minutes; `--minutes` can extend it. It stops the disposable app before the cloud host runs out of disk space.

Readiness requires the production completion receipt plus the exact guest ROOT_UID0, SUDO_UID0 and manifest-specific DESKTOP_READY lines. Only then are an Android screenshot and live QMP framebuffer captured; cold mode records PASS and observation mode records OBSERVED_READY. Visual inspection is still required. A host QEMU screenshot is never counted as this Android test.

## Cloud network setup

The emulator needs the same configured session proxy/CA trust as other cloud tools. No TLS or digest checks are disabled. `prepare-session-trust.py` copies public session CAs into a temporary test trust directory and bind-mounts it into the userdebug emulator's zygote mount namespace, then returns adbd to UID2000. Root here is emulator maintenance only; the app still runs as its normal Android UID. Verified OS partitions and the published APK remain unchanged. This setup is not needed on a normal phone using public Internet certificate chains.

Resolve the configured proxy hostname on the cloud host and set its IP/port as Android's global HTTP proxy. Clear the emulator CLI proxy first to avoid double-proxying. Do not print credentials or signed blob redirect URLs. This session's proxy is unauthenticated. The test-only NetworkProbe instrumentation emits only app UID, endpoint hosts, HTTP status and exception class; it never emits tokens or signed URLs. `auth.docker.io`, `registry-1.docker.io` and the producer's `production.cloudfront.docker.com` route were observed successfully through the configured proxy.

Initial test failure: the emulator CLI proxy still required resolving the registry host through unavailable guest DNS; the production app correctly stopped without publishing a verified layer. The boundary probe identified UnknownHostException. Setting Android's global proxy fixed it; no production download code changed. Attempting adb remount/disable-verity on this SDK image caused a vbmeta-digest reboot loop, so generated OS overlays were reset and the temporary namespace trust method used instead.

## Interruption cases

The actual Cancel download control was pressed during a real image transfer. A fresh UI hierarchy reported cancellation, the139209388-byte `.part` remained and the volume receipt remained ready=false. Retry/resume was then pressed; subsequent observed bytes exceeded the retained offset. The app was backgrounded during download to exercise its foreground service. When all verified blobs are published, the observer returns to the ordinary launcher for normal automatic guest startup. This is a cold setup with deliberate interruptions, not an uninterrupted run.

Artifacts/logs are under `.tools/managed-smoke` and `.tools/auto-setup`; they are test evidence, not a claim of successful desktop until the current run has terminal readiness evidence and its actual screenshots have been inspected. Real ARM64 phones and16KiB-page devices remain outside this emulator's coverage.

## Evidence integrity

Each invocation creates a unique `run-*` directory. `CURRENT.json` points to its `status.json`; only that current terminal status applies. Old legacy PASS files/screenshots are archived, not reused. Failures and interruptions write explicit terminal states. Six filesystem/subprocess tests in `test_run_evidence.py` cover stale success, observer labeling, installed-APK mismatch, stopped guest and legacy evidence.

Both the selected artifact and the installed APK are SHA256 checked; installed bytes are hashed using the ordinary app UID. `QmpStatusProbe` is a test-only headless Java entry point in the Android test APK, run with app_process/run-as. It does not attach instrumentation or stop the target app. It queries the private live QMP server and captures a guest framebuffer. A missing/stopped VM cannot satisfy that gate. The actual pre-boot negative control rejected nonexistent QMP.

`--watch-only` can produce `OBSERVED_READY`, never a clean-install PASS: it observes stored guest readiness plus a live guest, without establishing how setup began. Cold mode additionally clears only the dedicated test app data and tracks the native guest process during verification. Captured app screenshots and guest framebuffer still require visual inspection before claiming the display works. A source file or old receipt alone is never proof of a current desktop.

## Long observation and transport regression

A long observation can use `--minutes 2880 --status-file artifacts/Android-verification-status.json`. The report includes its checked-at UTC timestamp, tested APK hash and current guest phase. RUNNING is never a pass; an old timestamp is stale evidence. Run the observer in a distinct process session with redirected log output when it must survive an interactive shell. It still requires the emulator and cloud environment to remain available.

`SerialLogFailureProbe` is another headless entry point. Use the production APK plus test APK on its app_process classpath, under run-as. It starts an isolated socket and an unwritable directory-backed diagnostic log, then sends only two PHASE messages. It never accesses the real guest socket/volume or emits readiness. Red was observed with the installed0.2.1 code; green used the candidate0.2.2 APK's extracted dex in a separate process. That is a transport regression, not an APK-update or complete desktop test.

## Transient observation timeouts

The November6 continuation found actual layer5 extraction in the same guest process despite the previous observer's30-second ADB read timeout. `adb_transport.py` retries only explicitly whitelisted private reads (`cat`, `ls`, `pwd`, `sha256sum`, `du`), up to three attempts. Timed-out partial output is discarded. Mutations and the live QMP probe are never implicitly retried. Two real subprocess tests cover successful fresh data after transient read timeouts and the prohibition on repeating mutations; run all8 Python tests with `python3 -m unittest discover -s tests/android -p 'test_*.py'`.

A local detached supervision job may resume observation after a bounded ADB-timeout failure. It preserves each failed run and uses watch-only mode, so it cannot establish a continuous cold PASS. Any guest error, APK mismatch, storage guard or other failure stops that job. Candidate APK and visible-desktop/reopen checks remain required before release.
