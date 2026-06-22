---
title: Bluetooth (BLE) — Research Hub
domain: bluetooth
type: hub
status: detailed
summary: Hub for Bluetooth on this rig — Classic vs BLE, and the BLE use-case map across the sub-domain docs.
hardware: [flipper-internal, esp32-marauder]
use_cases: [UC-39, UC-29, UC-40, UC-30, UC-64, UC-41]
related: [bluetooth/interception.md, bluetooth/ble-spam.md, bluetooth/airtag-tracker-detection.md, bluetooth/ble-sniffer-addon.md, bluetooth/classic.md]
tags: [bluetooth, ble, bluetooth-classic, advertising, recon, hub]
last_verified: 2026-06-19
---

# Bluetooth (BLE) — Research Hub

> **TL;DR —** Bluetooth on this rig is advertising-layer recon and spam (Flipper built-in BLE + ESP32 Marauder), not connection interception. Routes you to the right doc for each BLE use case, plus Classic vs BLE basics.
> Board: [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md) · BLE apps: [../firmware/momentum.md](../firmware/momentum.md) · use-cases [../my-use-cases.md](../my-use-cases.md). Part of the [KB](../README.md).

Bluetooth on this rig is **advertising-layer recon + spam**, not interception. The Flipper's own BLE
(STM32WB) is **broadcast-detection / HID-peripheral only**; the **ESP32 Marauder** adds BLE/Classic
**device scanning, spam, and detection**. Neither sniffs or decrypts established connections — that's
the whole point of [interception.md](interception.md). **Authorized/own devices only** ([../legal-and-safety.md](../legal-and-safety.md)).

## Classic vs BLE (quick)
| | Bluetooth Classic (BR/EDR) | Bluetooth LE |
|---|---|---|
| Used for | audio, file transfer | sensors, wearables, beacons, trackers, locks |
| Channels | 79 | 40 (3 advertising + 37 data) |
| On this rig | Marauder can *list* Classic devices | the main focus (scan/spam/detect) |

## BLE use-case map (where each lives)
| Use-case | UC | Doc | Notes |
|---|---|---|---|
| **Bluetooth interception (reality)** | UC-39 | **[interception.md](interception.md)** ✅ | advertising recon vs connection sniffing |
| BLE scan / sniff (advertising) | UC-39 | [interception.md](interception.md) §5 ✅ | MAC/name/RSSI/UUID/mfr-data |
| **BLE Spam** | UC-29 | **[ble-spam.md](ble-spam.md)** ✅ | advertising-flood pairing popups; nuisance, not a hack |
| **AirTag / tracker detection** | UC-40 | **[airtag-tracker-detection.md](airtag-tracker-detection.md)** ✅ | defensive / anti-stalking |
| **FindMy Flipper** | UC-30 | **[airtag-tracker-detection.md](airtag-tracker-detection.md)** ✅ | inverse: broadcast Flipper as a Find My tag |
| **BLE connection sniffing** (add-on) | UC-64 | **[ble-sniffer-addon.md](ble-sniffer-addon.md)** ✅ | needs nRF52840/Sniffle — the real-capture upgrade |
| Bluetooth skimmer detection | UC-41 | *(see [security-pentest](../topics/security-pentest.md))* | defensive |
| **Bluetooth Classic** (KNOB/BIAS) | — | **[classic.md](classic.md)** ✅ | mostly out of this rig's reach |

## Docs
- **[interception.md](interception.md)** — ✅ the honest reality of "intercepting Bluetooth": advertising vs connection sniffing, pairing crypto (LE Legacy/crackle vs LE Secure Connections), the hardware that does it, and my rig's limits.
- **[ble-spam.md](ble-spam.md)** — ✅ BLE Spam (UC-29): advertising-flood pairing popups (Sour Apple / Fast Pair / Swift Pair), the iOS 17.2 story, why it's nuisance not compromise.
- **[airtag-tracker-detection.md](airtag-tracker-detection.md)** — ✅ AirTag/tracker detection (UC-40) + FindMy Flipper (UC-30): how Find My works, anti-stalking detection, rig limits.
- **[ble-sniffer-addon.md](ble-sniffer-addon.md)** — ✅ the upgrade to real connection capture: nRF52840 / Sniffle / Flipper-BLE-Sniffer, setup + crackle.
- **[classic.md](classic.md)** — ✅ Bluetooth Classic (BR/EDR): KNOB, BIAS, BlueBorne — and why the rig can't touch it.

## Open questions / to research
- Promote **Bluetooth skimmer detection** (UC-41) to its own deep-dive (currently in [security-pentest](../topics/security-pentest.md)).
- ~~A `classic.md` for Bluetooth Classic~~ → done: [classic.md](classic.md).
- Decide whether to actually buy the nRF52840 sniffer ([ble-sniffer-addon.md](ble-sniffer-addon.md)) — cheapest path to real BLE capture.

## Sources
- See [interception.md](interception.md) sources (Nordic Academy, Sniffle, crackle, Marauder wiki, Flipper BLE limits).
