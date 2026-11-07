# KP VPN 0.2.0 validation

GitHub Actions staging build: https://github.com/khantpyae332003/kp-ai-vpn/actions/runs/42394555292

- Android compilation, native parser/importer/label tests, lintDebug and assembleDebug passed.
- Five Node UI model tests passed.
- Chromium at 390x844 verified import dialog, country/search filters, legacy Global metadata, injection safety, 48px button targets, website action and no horizontal overflow.
- Home/import screenshots were inspected after CI. These screenshots test bundled UI, not the Android bridge or live SIM connectivity.
- The Noto Sans Myanmar font and its license notice are bundled by CI.

The app uses versionCode2 / versionName0.2.0 and the existing com.khant.kpvpn application ID. This is a newly debug-signed preview; the previous private signing key was unavailable, so in-place upgrade compatibility is not established. No keystore or VPN config credentials are distributed with the release.

Actual device tests still required: Android VPN consent, notification/camera permission acceptance and denial, QR import, encrypted profile recovery, background/process lifecycle, live tunnel DNS/routing, network switches and real Thai/Myanmar cellular SIM service. Tunnel UP and cloud HTTPS checks do not certify package-free mobile data.
