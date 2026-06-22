# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

The first release — pending rig verification before it is tagged **v0.1.0**.

### Added
- Wireless **MCP server** (38 tools) driving a Flipper Zero over Bluetooth LE — device/power info,
  screenshot, button injection, file read/write, app launch, app-driven Sub-GHz/IR transmit (gated),
  GPIO, BadUSB (gated), and a read-only scheduled **health-watch**.
- Resident BLE daemon — held connection over a token-authed `0600` Unix socket for fast, serialized calls.
- `ORIENT → EXECUTE → CAPTURE` operating **skill** + the **`/flipper-learn`** capture command.
- Prebuilt **knowledge base** (seed, ~70 docs) + a per-install `kb-local/` overlay — the self-evolving loop.
- `app/build_app.sh` — ad-hoc-signed macOS Bluetooth helper bundle (no Apple Developer account needed).
- `scripts/snapshot.sh` — curated public-release snapshot from the private KB.
- Release automation (PyPI Trusted Publishing + MCP registry), community-health files, quality gates, this changelog.

### Fixed
- Deterministic KB index build (sort docs by path) so generated artifacts are byte-identical across OSes.
- **Installability:** vendored the Flipper protobuf message classes (BSD-3, protobuf-only) under `_proto/` and dropped the `flipperzero-protobuf` dependency — it transitively pinned `numpy==1.22.3`, which has no modern wheel and blocked a clean `pip install` on macOS arm64.

[Unreleased]: https://github.com/pogorelov-labs/flipper-ble-mcp/commits/main
