# KP VPN Hub — file catalog agents

A file-first KP VPN website with carrier-filtered WireGuard listings and concise Burmese help. The 2026-11-01 redesign removes unrelated chat, contact forms, generic safety cards and daily tips at the user’s request. It uses a dark green palette, mobile SIM controls, a genuine refresh action, and collapsed learning/source sections.

## Actual capabilities

- Agent 1 searches public repository metadata and reads explicitly approved redistribution manifests.
- Agent 2 independently checks the trusted source registry, validates standard one-peer WireGuard configs, and tests a real handshake plus IPv4 HTTPS through an isolated Linux network namespace.
- Successful files are grouped by carrier and source plan label; no fabricated downloads are included.
- Thai dtac/True/AIS nopro categories and Myanmar carrier filters are built into the page.
- User-reported SIM evidence is separated from cloud server verification, keyed to the exact config hash and limited to 24 hours.
- A Burmese guide explains supported file types, finding provider configs, importing them into KP VPN, and why renaming/changing carrier labels cannot change authentication, routing or SIM eligibility.

These agents are deterministic Python automation jobs, **not configured LLM agents**. No AI service/API key has been set up and private configs are not sent to an AI provider. GitHub public-search discovery works without an LLM subscription.

## Status and limits

A real public archive source is configured in `data/sources.json`: Delta-Kronecker/ProtonVPN-WireGuard-configuration. Its author explicitly offers public normal-use configs. The workflow tests up to 20 entries per source/run, rechecks up to eight previously successful entries first, and rotates new entries. Up to four probes run concurrently in independent namespaces. Server-passed entries link to the original commit-pinned ZIP and identify the exact member to use; shared keys are not republished in this repository. No successful entries are claimed until the live tests actually pass. Carrier is `other` and plan `standard`; no actual SIM hardware or nopro certification is available.

KP VPN v0.1 supports WireGuard `.conf`, ZIP containers of those files, and QR payloads containing the config text. It does not connect OpenVPN, VMess/VLESS/Trojan/Shadowsocks, or proprietary `.ehi/.hc/.hat` files.

## Workflow

`.github/workflows/catalog.yml` schedules every 30 minutes (`*/30 * * * *`), supports manual runs, and runs on relevant source edits. Scheduled GitHub Actions are best-effort and can be delayed or disabled by repository settings/inactivity. The workflow must be on the default branch to run on schedule.

Jobs: finder → verifier (including tests/UI checks and changed-only catalog commits) → Pages deployment. GitHub Pages must allow Actions deployments; the workflow does not silently change account or repository settings. Catalog commits stage only `catalog/`, never source registries or private temporary probe files. The deployment artifact includes only index, assets and public catalog.

## Local checks

```sh
python3 -m unittest discover -s tests -v
python3 -m agents.finder
python3 -m agents.verifier --offline
node --check assets/catalog.js
```

`--offline` never marks a server as working. Real probe execution requires Linux root/CAP_NET_ADMIN, `wireguard-tools`, `iproute2`, and `curl`; it does not change the host's default route. Browser QA uses pinned Playwright in CI. No Python dependencies beyond the standard library.

## References

- https://www.wireguard.com/quickstart/
- https://www.wireguard.com/netns/
- https://protonvpn.com/support/wireguard-configurations
- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

## Own-config creation

The website includes a browser-local WebCrypto X25519 client-config builder and detailed Burmese provider/VPS instructions. Public-key derivation is independently checked using Node crypto in `tests/builder.test.cjs`. Private keys stay in browser memory and the locally downloaded `.conf`, with no localStorage, telemetry or network submission. A real server and registered client public key remain required; generated files are not marked server-verified. Static `.conf.example` client/server templates are educational placeholders.

The `*/30 * * * *` schedule applies all 24 hours in UTC. Each run completes and exits; GitHub Actions is not a continuously running daemon. Queue delays, platform outages and repository scheduling policies still apply.
