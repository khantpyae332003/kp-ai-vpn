# KP VPN 0.2

Android WireGuard client and phone-first configuration library for Thai, Myanmar and Global SIM labels.

Website: https://khantpyae332003.github.io/kp-ai-vpn/

- Modern network shield branding and readable Burmese UI.
- Verified APK download metadata and preview release pipeline.
- SIM country/carrier/plan filters, cloud handshake + HTTPS checks, local configuration builder and checker.
- Eight bounded pipeline roles: finder, verifier, classifier, publisher, daily lessons, health, security and integrity.
- Three independent public-site monitors and mobile/desktop browser checks.

## Run checks

```sh
python -m unittest discover -s tests
node --test tests/*.test.cjs
```

## Pipeline

```sh
python -m agents.finder --discover
sudo python -m agents.verifier
python -m agents.pipeline --out catalog
```

Preserve catalog/daily-history.json. GitHub Actions handles schedules, verification, commits and deployment. See docs/WORKFLOW.md and docs/RELEASE.md.

## Scope

Cloud tests do not certify actual SIM service or package-free data. Only approved sources are eligible. Public shared configurations remain original archive links; private keys are not redistributed. AI credentials are not configured, and the dashboard says so. The APK is a debug-signed preview; prior signing identity is unavailable.
