# Bounded daily AI assistance

`OPENAI_API_KEY` is read from a GitHub Actions repository secret only in the dedicated AI step on main. `OPENAI_MODEL` is an optional repository variable; default is gpt-4.1-mini. No credential is included in website assets or APK.

One Responses API request reviews all eight role summaries and rewrites the current curated lesson into simple Burmese. The input allowlist contains role IDs/statuses and the lesson title/body only. VPN config bytes, endpoint credentials, private keys, GitHub credentials and arbitrary source descriptions are never sent. Output is strict JSON and locally validated; HTML, URLs and credential-like output are rejected.

AI notes are advisory. Source authorization, SIM labels, handshake/HTTPS verification, catalog publication and bounded cleanup stay deterministic. AI does not certify SIM compatibility or package-free data. The educational rewrite retains the original official source URL.

A validated result is cached for the Bangkok calendar day. Errors use fixed public codes and a six-hour cooldown, preserving ordinary catalog publication. API errors and missing secrets do not mark AI connected. No raw API response/error body or key is logged. The request sets store=false and a bounded output-token limit.

The curated lesson bank currently contains 32 unique topics; this integration rephrases those topics and does not perform live news research or replenish verified source material automatically.
