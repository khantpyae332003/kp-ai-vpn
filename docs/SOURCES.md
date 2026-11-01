# Adding a real source feed

The finder performs public GitHub repository metadata searches immediately. Those results are unapproved leads, not downloadable configuration files. `data/sources.json` starts empty because no public redistribution feed has been provided. Arbitrary GitHub configs may contain another person's account credentials; they are never scraped into this site.

Only a source intentionally publishing WireGuard configs for public redistribution belongs in this registry. You must have explicit redistribution permission; your personal provider dashboard files are for your own device, not this public catalog.

## Registry shape

Add an entry to the `sources` array in `data/sources.json`. Replace every placeholder with the source owner's real HTTPS URLs and hostnames; the example below is a schema illustration and does not resolve to a real feed.

```json
{
  "id": "source-owner-dtac",
  "enabled": true,
  "redistribution_approved": true,
  "carrier": "dtac",
  "plan": "nopro",
  "allowed_hosts": ["SOURCE_OWNER_HOST"],
  "permission_url": "https://SOURCE_OWNER_HOST/public-redistribution-policy",
  "manifest_url": "https://SOURCE_OWNER_HOST/wireguard-manifest.json"
}
```

Carrier values: `dtac`, `true`, `ais`, `mpt`, `atom`, `mytel`, `mm-other`, `other`. Plan values: `nopro`, `standard`, `unknown`. A plan name is an upstream claim, not proof of billing/plan compatibility.

The source owner's manifest must use this shape:

```json
{
  "files": [
    {
      "name": "owner-supplied-name",
      "url": "https://SOURCE_OWNER_HOST/shared-config.conf",
      "sha256": "OPTIONAL_SHA256_OF_THE_DOWNLOADED_BYTES",
      "expires_at": "2030-01-01T00:00:00+00:00"
    }
  ]
}
```

Omit `sha256`/`expires_at` when the provider does not supply them; do not invent expiry or checksum values. Source download URLs must be public HTTPS without account tokens, query strings, embedded credentials or redirects to unlisted hosts. DNS/IP checks reject local/private targets. Max 20 sources, 40 candidate files per run, 1 MiB manifest, 128 KiB per config.

Current automatic validator accepts standard, one-peer WireGuard client configs with an IPv4 default route and public Endpoint. Shell hooks, unsupported keys/protocols, private endpoints, missing keys and malformed inputs fail before probing. The app may accept additional valid configurations that this stricter publishing pipeline declines.

Downloads are named deterministically:

- `catalog/downloads/dtac/nopro/dtac-nopro-<config-hash>.conf`
- `catalog/downloads/true/nopro/true-nopro-<config-hash>.conf`
- `catalog/downloads/ais/nopro/ais-nopro-<config-hash>.conf`

The verifier re-reads the trusted registry rather than trusting carrier or approval flags in the finder artifact. Only fresh successful WireGuard handshake + IPv4 HTTPS checks create download entries. Failed or expired items are removed when the next catalog build succeeds. The page also hides expired entries even if a scheduled run is delayed.

## Phone-only maintenance

1. GitHub → repository → `data/sources.json` → pencil → add the source entry → commit.
2. Actions → **KP VPN Catalog Agents** → check finder/verifier/deploy results. Editing this file triggers a new run.
3. The live catalog displays only successful entries. It does not certify Thai/Myanmar SIM connectivity from cloud probes.

For actual SIM evidence, put a report in `data/carrier-tests.json` with the exact canonical config `sha256`, `carrier`, `plan`, `network: "cellular"`, `result: "pass"`, UTC `tested_at`, and a public `https://github.com/...` evidence URL. It is explicitly labeled **user-reported**, and accepted only for the last 24 hours. Never include account keys or private config contents in the evidence.
