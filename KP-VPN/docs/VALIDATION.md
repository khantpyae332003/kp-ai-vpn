# Validation and device test handoff

## Automated evidence

GitHub Actions builds the Android APK from `kp-vpn-new` in `khantpyae332003/kp-ai-vpn`:
https://github.com/khantpyae332003/kp-ai-vpn/actions

An earlier revision (`58886afc06600837494b8b406494f98deb0b27a7`, run `41207180899`) successfully ran Android compilation, the seven parser/importer unit tests, Android lint and APK assembly, plus four UI model tests. Later source changes fix worker-thread storage and disconnect lifecycle behavior; check the current branch's latest run for their build result.

The final pipeline also runs a Chromium UI check at 390×844: opening the import dialog, country/search filtering, inert display of an HTML-like profile name, no horizontal overflow, and no JavaScript page errors. It records home/import screenshots for visual inspection. These checks test the bundled UI, not Android bridge/VPN behavior.

Local validation: four Node UI model tests, JS syntax checks, XML parsing and workflow YAML parsing. The local environment lacks Android SDK/build tools and blocks their downloads; actual native compilation runs in GitHub Actions. Read-only code review found and led to fixes for stale foreground notifications after backend DOWN and main-thread storage lock contention. Disconnect errors now restore actual backend state.

The pipeline bundles Noto Sans Myanmar before UI checks and APK assembly. License notices are included with that font. The app is a debug test build and has not been published to Google Play.

## Still needs real Android device testing

- First VPN consent acceptance/denial; notification permission acceptance/denial.
- Camera granted/denied; importing a valid WireGuard QR.
- Batch .conf and ZIP import; duplicate/invalid counts and import near capacity.
- App close/reopen and encrypted profile recovery; interrupted writes.
- Start/stop with a valid reachable WireGuard server; independent verification of routing and DNS.
- Unreachable/revoked server config; no claim that tunnel UP proves internet connectivity.
- Disconnect through notification, Android VPN settings, or by starting another VPN; confirm no stale controller notification.
- Background operation, Android process reclaim, network changes and restart behavior.
- Actual Thai/Myanmar SIM networks. Carrier tags are organization labels only.

No working server configs are bundled. There is no evidence or promise of free mobile data, automatic failover, multi-protocol connectivity or always-on VPN.
