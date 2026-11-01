# KP VPN file catalog

Extend the existing GitHub Pages page without removing its language toggle, contact/chat or daily-tip marker. Add a readable catalog and Burmese learning guide. Existing app supports WireGuard conf, QR payloads and ZIP containers only.

Use GitHub Actions and two bounded Python automation agents rather than inventing AI API credentials: finder discovers public repository metadata and reads operator-approved distribution manifests; verifier independently fetches approved configs, validates them, tests a real WireGuard handshake plus HTTPS egress in an isolated Linux network namespace, then publishes a fresh catalog and grouped download names. These are deterministic automation agents, not LLM agents. No private configuration is sent to any AI service.

Group by Thai dtac/True/AIS and Myanmar MPT/ATOM/Mytel/Other. nopro is a source claim, not a detected billing property. SIM test reports must refer to exact config SHA and recent cellular tests; label them as user-reported. Cloud verification never claims actual SIM/no-package verification. Guide explains finding provider configs and why renaming files or changing carrier tags does not alter connectivity.

Public discovery results have no credentials or downloaded configs. Redistribution requires an explicitly enabled source and recorded permission URL; account-specific keys are never swept from arbitrary GitHub repositories. The initial approved source list is empty because no authorized public distribution feed has been supplied. Show zero real downloads honestly, while discovery and guide work immediately.

Schedule every 30 minutes on default main, plus manual and source-edit triggers. Only catalog output is auto-committed on changes; deploy the existing GitHub Pages branch normally. Failed checks do not publish working claims. Rebuild removes stale/failed downloads and retains per-run provenance and status. Fixed limits: 20 sources, 40 candidates, 128 KiB configs, 1 MiB manifests, 15-second probes, max age 24h.

Alternative: an LLM-only search/check system cannot prove tunnel or SIM compatibility. A dedicated SIM device test farm could certify carrier behavior but is not available. Use bounded scripts and explicit evidence now; add trusted feeds and device testing later.
