---
title: Official Firmware (OFW) — Flipper Devices
domain: firmware
type: reference
status: detailed
summary: Stock OFW from Flipper Devices — abilities, deliberate limits, and the sanctioned app catalog.
hardware: []
use_cases: []
related: [firmware/README.md, firmware/unleashed.md, firmware/momentum.md, legal-and-safety.md]
tags: [firmware, official, ofw, stock, app-catalog, stability, region-lock]
last_verified: 2026-06-19
---

# Official Firmware (OFW) — Flipper Devices

> **TL;DR —** Stock firmware from Flipper Devices: the upstream baseline all CFWs fork from, with no extra unlocks, region-locked Sub-GHz, highest stability, and the reviewed Flipper Apps Catalog.
> See the [firmware overview & matrix](README.md). Part of the [KB](../README.md).

- **Repo:** https://github.com/flipperdevices/flipperzero-firmware
- **Updater/site:** https://flipper.net · web updater https://lab.flipper.net (Flipper Lab)
- **Lineage:** The upstream baseline all CFWs fork from. GPL-3.0, written in C.

## What it does (and deliberately doesn't)
Stock experience with **no "extra" unlocks**. By design it:
- **Region-locks Sub-GHz TX** and blocks transmit on restricted bands (legal/compliance).
- **Blocks rolling-code save/send.**
- Uses a fixed device name; minimal bundled apps.

## Notable
- Native **JavaScript** support on-device.
- The sanctioned third-party app store: **Flipper Apps Catalog** (browse in Flipper Lab + mobile app; each app is reviewed before distribution).
- 2026 **Recovery Mode** (hold BACK+OK to enter → "Restore Firmware").

## Stability & maintenance
- **Highest stability** — QA'd Release / RC / Dev channels.
- Maintained by **Flipper Devices** (the company); very active, stable releases ~monthly.

## Install / flash
Mobile app (BLE), qFlipper (USB), or Flipper Lab (web/WebUSB). Pre-installed on new units.

## Best for
Anyone wanting stability and warranty-safe official support. Recommended to run for 1–2
weeks to learn the device before switching to a CFW.

## Open questions / to research
- Current OFW feature gaps that specifically motivate switching (per *my* use cases).
- What the official catalog now allows vs what only CFW app sources carry.

## Sources
- https://github.com/flipperdevices/flipperzero-firmware · https://docs.flipper.net/zero · https://lab.flipper.net
