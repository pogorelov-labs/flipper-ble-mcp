# Roadmap

Where **flipper-ble-mcp** is headed. A living document — open an issue or discussion to shape it.
Priorities, not deadlines (no dates on purpose).

**Today (v0.1.0, beta):** a macOS MCP server (38 tools) that drives a Flipper Zero over Bluetooth LE,
a KB-aware operating skill, and a prebuilt + self-evolving knowledge base. Published, CI-green.

## Now — harden v0.1.x (trust & release)
Make the first release *trustworthy and installable*, not feature-rich.
- [ ] **Rig-verified release** — confirm the published toolkit drives a real Flipper end-to-end, then tag **v0.1.0** + a GitHub Release.
- [ ] **Release automation** — PyPI **Trusted Publishing** (OIDC, no stored token) + auto-publish to the **MCP registry** on tag.
- [ ] **CI maturity** — macOS test matrix (3.11 / 3.13), a coverage gate, full ruff lint + format.
- [ ] **Test coverage** — unit tests for the pure layers (protobuf framing, status decoding, health thresholds).
- [ ] **Demo** — a short GIF of Claude driving the device (the README's one gap).

## 0.2 — robustness & depth
- [ ] Broaden tests over the daemon's framing / command-demux logic (the hard-won correctness machinery).
- [ ] Prune the legacy per-call CLI handlers in `ble_worker` now superseded by the resident daemon.
- [ ] Optional protobuf-binding regen for push events / richer fields (deferred from v0.1 — modest value, real risk; gated behind tests).
- [ ] Grow the seed KB from real `/flipper-learn` captures (the self-evolving loop → PR-back).

## 0.3 — reach
- [ ] **Cross-platform.** `bleak` already supports Linux (BlueZ) and Windows (WinRT); the blocker is the macOS-specific TCC app-bundle that holds the Bluetooth entitlement. Design a per-OS Bluetooth-permission path so non-macOS users can run it.
- [ ] Community launch — awesome-flipperzero, awesome-mcp-servers, the MCP-registry listing, write-ups.
- [ ] First-class examples / recipes per capability domain.

## Later / exploring
- [ ] **Fleet (M5)** — orchestrate Flipper + ESP32 (Marauder / Ghost-ESP) as a second controllable node.
- [ ] Scheduled/unattended **defensive** monitoring jobs (read-only; never unattended transmit).
- [ ] A community KB-contribution flow so collective session learnings compound into the shipped seed.

## Non-goals
- **Not** a turnkey attack/pentest framework. Capabilities are dual-use and **gated**: every transmit / write / HID action is human-approved per call, scoped to your own authorized targets on legal bands.
- **No autonomous RF/IR transmit or BadUSB**, ever. The agent proposes; a human approves.
- Not a replacement for on-device firmware/apps — this is host-side control + knowledge.

## Influence the roadmap
Issues and discussions are welcome (see the templates). The fastest way to move an item is a focused
PR — see [CONTRIBUTING.md](CONTRIBUTING.md), including how to PR a learned-KB entry back into the seed.
