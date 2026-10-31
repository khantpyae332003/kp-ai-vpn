# KP VPN implementation decisions

User request: build a new Android app called KP VPN, independent of the unfinished reference project, with more config capacity for Thai and Myanmar SIM use. User delegated the new implementation rather than providing old files.

Chosen implementation: a small Java Android shell, bundled Burmese HTML/CSS/JS UI served only through AndroidX WebViewAssetLoader, official embeddable WireGuard GoBackend, native document picker/QR scanner, encrypted native profile storage. The UI sees metadata and traffic counters; private config is validated and retained natively. Pasted text traverses the local bridge only during import.

Alternatives considered: a web-only organizer cannot establish an Android VPN; a multi-protocol native engine would require a broader integration/testing effort. WireGuard is the initial deliverable; future protocol adapters must be explicitly added and tested rather than labeled supported without a working backend.

UI: one connection screen with a large power control, selected config name, actual backend traffic bytes, import dialog, country tags, search and favorites. No fabricated preloaded working server list or fake latency values.

Native foreground controller owns the tunnel lifecycle and notification. Android VPN permission is required. Always-on is explicitly disabled. No background startup, automatic switching or collection is claimed. The controller uses Android specialUse foreground service type; Google Play distribution requires a separate policy/readiness review.

Profile import limits protect memory and archive expansion. Archive entries are read in memory and never extracted to filesystem paths. Duplicate keys use the SHA-256 of WireGuard's canonical config serialization. Carrier labels are user-selected organization tags, not automatic SIM detection or compatibility guarantees.

Storage: Android Keystore AES key, AES/GCM/NoPadding with a fresh IV per write, AtomicFile persistence. Backups disabled. Corrupt/unreadable storage fails closed rather than silently replacing existing data. Config deletion is disabled while a tunnel is active or starting.

Residual checks: native compilation, Android lint, parser unit suite, real-device consent/notification/revocation/background lifecycle, QR camera denial, encrypted-store interruption/recovery, archive boundary tests, and real reachable/unreachable server cases. No promise of free mobile data.
