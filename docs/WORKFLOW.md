# Eight-role publishing pipeline

Run `python -m agents.finder --discover --out work`, then `python -m agents.verifier --input work --out catalog`, then `python -m agents.pipeline --out catalog`.

Finder considers the enabled trusted source registry. Verifier independently authorizes provenance and performs a WireGuard handshake plus IPv4 HTTPS probe. Classifier uses registry carrier/plan metadata and current hash-matched cellular reports. Publisher emits metadata and original commit-pinned archive links only. Daily writer selects one unused official-documentation lesson per Asia/Bangkok date. Health, security and integrity monitors report and withhold stale or invalid generated catalog entries; they never edit application code.

Retain `catalog/daily-history.json` across scheduled builds. The writer reuses the same day's post on retries and never recycles an exhausted lesson bank; it retains the last post and reports `needs_content`. Do not reset history during deployment. The 32-post bank is curated educational material, not carrier-package or free-data certification. Publication is deterministic; `ai.configured` remains false. No API key is required.

`country` means SIM country: TH (dtac, true, ais), MM (mpt, atom, mytel, mm-other), GLOBAL (other). It never indicates the VPN server location. Only an exact configuration hash, carrier, plan, cellular network, pass result and evidence URL within 24 hours can produce a user-reported SIM pass. This does not certify free data. No source beyond the existing approved registry is automatically authorized.

Outputs include `index.json`, per-carrier indexes, `summary.json`, `agents.json` and `daily.json`. Monitor health refers to generated metadata freshness; remote deployment availability must be tested after deployment. Empty catalogs are valid warning states, not fabricated successful connections.
