---
title: Unleashed Firmware — DarkFlippers
domain: firmware
type: reference
status: detailed
summary: Unlocked, stable, RF-focused custom firmware — the oldest OFW fork, favored for serious Sub-GHz work.
hardware: []
use_cases: []
related: [firmware/README.md, firmware/official.md, firmware/momentum.md, legal-and-safety.md]
tags: [firmware, unleashed, custom-firmware, sub-ghz, rolling-code, cc1101, stability]
last_verified: 2026-06-19
---

# Unleashed Firmware — DarkFlippers

> **TL;DR —** Unlocked, function-first custom firmware: the oldest OFW fork, removes regional Sub-GHz TX limits, adds rolling-code protocols and curated stable apps, and is widely regarded as the most stable CFW for RF work.
> See the [firmware overview & matrix](README.md). Part of the [KB](../README.md).
> **One of the two firmwares this device may currently run** — if `Settings → About` shows `unlshd-###`, it's this.

- **Repo:** https://github.com/DarkFlippers/unleashed-firmware
- **Site:** https://flipperunleashed.com · **Web installer:** https://web.unleashethe device.com (dev: https://dev.unleashethe device.com) · **Telegram:** `t.me/unleashed_fw`
- **Maintainer:** **@xMasterX** + contributors. Free/open-source, very active (near-daily dev builds, frequent stable).
- **Lineage:** First/oldest major fork of OFW; keeps OFW API + app-catalog compatibility.

## What it unlocks/adds vs Official
- **Removes regional Sub-GHz TX restrictions**; expands frequency ranges.
- **Many rolling-code protocols** with save/send (KeeLoq, FAAC SLH, BFT Mitto, etc.).
- **External CC1101 module** support.
- Enhanced **frequency analyzer** (timestamp + protocol name).
- **BadKB/BadUSB over Bluetooth (BadBT).**
- Customizable Flipper name; desktop clock + battery %; **PIN lock / lock-on-boot**.
- Improved NFC/RFID parsers + EMV; expanded IR universal remotes; name/MAC/serial spoofing.
- "SubDriving" (saving Sub-GHz capture coordinates) and advanced security options.

## Character
**Function-first** — curated, **stable** community apps only; little decorative bloat.
Widely regarded as the **most stable custom build**; favored for serious RF/Sub-GHz work.

## Install / flash
Web installer (web.unleashethe device.com), qFlipper with the release `.tgz`, or GitHub Releases / Telegram.

## Best for
Sub-GHz / RF analysis and **reliability-focused** power users who want unlocks without UI fluff.

## Open questions / to research
- Confirm this is (or isn't) the device's current FW; note the exact `unlshd-###` build.
- Unleashed vs Momentum decision for *my* use cases (RF reliability vs UI/feature breadth).
- Exact current extended frequency ranges (verify against repo docs before relying on TX).

## Sources
- https://github.com/DarkFlippers/unleashed-firmware · https://flipperunleashed.com · https://web.unleashethe device.com
- https://awesome-flipper.com/firmware/
