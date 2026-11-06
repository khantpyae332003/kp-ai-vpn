# Kali real-device verification implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. User has explicitly opted out of further design questions.

**Goal:** Build the actual rootless Kali Android candidate in GitHub Actions and observe one bounded physical-device first setup before offering any APK as validated.

**Architecture:** Mirror the reviewed app sources under `kali-android/`, leaving the website unchanged. Split the existing pinned initramfs into four source payload pieces below GitHub's individual-file limit and reconstruct it with SHA256 verification before the normal bootstrap/build. A Python standard-library Appium client uses only GitHub secrets to upload the built APK and observe its normal UI on one Samsung Galaxy S23 Ultra Android13 session. Account must report Free/trial; never purchase or upgrade a plan.

**Tech stack:** GitHub Actions, pinned existing Android/Java toolchain and native runtime, Python3 urllib, BrowserStack Appium W3C API.

## Constraints

- No APK release until first setup, actual guest root/sudo/readiness, visible desktop and data-retaining reopen are demonstrated.
- Free/trial account only, one physical session, maximum45minutes, guaranteed best-effort session cleanup.
- No Android root, resource override, substituted filesystem, injected READY or privileged guest shortcut.
- Existing mixed-version cloud observation is separate evidence and remains running.
- No username/key, raw HTTP error body or signed download URL in reports/screenshots.
- Native dependencies are fetched by the existing checksum-pinned bootstrap. Full corresponding-source bundles remain retained in the original workspace for final packaging; this CI mirror excludes those large tarballs.

## Tasks

- [x] 1. Create minimal app source mirror and hash-verified split payload restoration. Test good reconstruction and refusal of corrupted payload while preserving an existing output.
- [x] 2. Build exact mirrored candidate in Actions, run existing core tests/lint and verify APK assets. Retain candidate and digest as internal test artifacts, not a validated release.
- [ ] 3. Add Appium observation with real API error handling, bounded free-plan device selection and retained screenshot/XML evidence. Report FAILURE/INCOMPLETE rather than success when provisioning or a resource check stops.
- [ ] 4. Inspect actual evidence, test root/tools and shutdown/reopen, repair any real defect, then rerun affected checks. Keep release withheld until these gates pass.

## Validation

Test local deterministic payload/client boundaries before pushing. Read actual Actions status and sanitized test evidence; a successful build or created session alone is not an app pass. Visual inspection remains mandatory. Initial device entitlement was authenticated through account API; plan Free,5parallel capacity,0running,43Android entries.

Build evidence: Actions run42298176848 completed successfully in1m35s, including40core tests/build/lint/packaged boot hashes. The source mirror matches414original tracked files byte-for-byte. Upstream inherited whitespace is preserved rather than changing vendor patches. A readiness navigation review found Bootstrap's onResume reopening the SDL desktop when Back returns; fix/regression is required before spending device time. Run attempt IDs isolate observation files. Unknown session-creation results must never claim confirmed cleanup. Credential redirects are rejected, with a real loopback HTTP regression.

Navigation regression: initial SDK-fetch setup failed because test JVM lacked inherited proxy/trust settings (not counted as a behavioral RED). After trusted HTTPS Maven setup, the real Bootstrap lifecycle test failed because returning relaunched ManagedDesktopActivity. Removing the onResume opened=false reset fixed it; fresh activity auto-launch is retained. Full local41JUnit tests/build/lint pass; no native guest was stopped. Candidate version0.2.3.

First actual Free-plan phone session started in run42300739526 (uploaded APK SHA6e04ae20ecc60230eab8846d2adcb16c3a35c205e85d82161bf50760bc36a521); device API reported Samsung SM-S918B, Android13/API33,1080x2316. The observer incorrectly traversed only adb-style <node> elements, while Appium can use class-name XML tags. A class-tag regression failed then passed after tag-agnostic traversal. The first session was deliberately stopped with DELETE confirmed after roughly3minutes; no root/desktop success is claimed. The corrected observation will be a new cold session, not a continuation of the first. All8helper tests pass.

Corrected XML run42301562998 confirmed the real Appium class-tag hierarchy and actual com.kp.kali download progress (layer1,78MiB). It ended because screenshot Base64 decoding raised binascii.Error; no PNG was saved, while real XML was saved. This is a screenshot-transport failure, not a Kali app failure. Session DELETE was confirmed. A line-wrapped Base64 screenshot regression reproduced failure then passed after whitespace normalization, optional PNG data-URI prefix handling and strict PNG-signature validation. Screenshot-only capture failures now preserve real XML and keep observation running, with an explicit missing-image error; they cannot qualify visual review/release. All9helper tests pass. Next run is again a new cold session, not resumed app data.

Run42302378168 reached actual first setup on Samsung S23Ultra: the full4.75GB pinned download completed, bundled Linux booted/mounted its private ext4 filesystem in~21guestseconds, first large layer extracted and tools-layer5 began. It was still extracting at the observer's own45minute deadline; statusTIME_LIMIT_INCOMPLETE with DELETE confirmed. This is not a BrowserStack-imposed45minute limit and not a demonstrated app crash. No root/sudo/desktop proof was obtained and no APK is released. One further bounded Free-plan attempt targets catalog-listed S24UltraAndroid14 (newer CPU and12GB-class memory) with48minute observation,55minute job cap. It is a new cold setup and not a resumed volume. Free-plan guard remains mandatory; paid plans are never used automatically.
