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
