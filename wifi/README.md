---
title: Wi-Fi (ESP32 Marauder) — Research Hub
domain: wifi
type: hub
status: detailed
summary: Hub: Wi-Fi capability map — which use-case lives in which doc.
hardware: [esp32-marauder]
use_cases: [UC-31, UC-32, UC-33, UC-34, UC-35, UC-36, UC-37, UC-38, UC-54]
related: [wifi/wpa-handshake-pmkid.md, wifi/own-network-audit.md, wifi/deauth.md, wifi/evil-portal.md, wifi/recon-and-attacks.md]
tags: [wifi, marauder, esp32, capability-map, hub, pentest]
last_verified: 2026-06-19
---

# Wi-Fi (ESP32 Marauder) — Research Hub

> **TL;DR —** Index hub for Wi-Fi/BLE on the ESP32 Marauder backpack; maps each use-case (scan, sniff, WPA capture, deauth, evil portal, spam, analyzer, wardrive, detect) to its deep-dive doc.
> Board: [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md) · use-cases [../my-use-cases.md](../my-use-cases.md) · framing [../topics/security-pentest.md](../topics/security-pentest.md). Part of the [KB](../README.md).

Wi-Fi on this rig is **not** native to the Flipper — it runs on the **ESP32-WROOM Marauder**
backpack (2.4 GHz only, onboard microSD for PCAP), driven over UART by the **WiFi Marauder** app.
**Authorized networks only** ([../legal-and-safety.md](../legal-and-safety.md)).

## Wi-Fi capability map (where each use-case lives)
| Use-case | UC | Deep-dive | Also covered |
|---|---|---|---|
| **WPA handshake / PMKID capture** | UC-33 | **[wpa-handshake-pmkid.md](wpa-handshake-pmkid.md)** ✅ | — |
| ↳ **Audit my own Wi-Fi** (how-to) | UC-33 | **[own-network-audit.md](own-network-audit.md)** ✅ | — |
| **Scan / recon** | UC-31 | **[recon-and-attacks.md](recon-and-attacks.md)** ✅ | agent/MCP recipe: **[marauder-mcp-scan.md](marauder-mcp-scan.md)** ✅ |
| **Sniff → PCAP** | UC-32 | **[recon-and-attacks.md](recon-and-attacks.md)** ✅ | — |
| **Deauthentication** | UC-34 | **[deauth.md](deauth.md)** ✅ | — |
| **Beacon/probe/SSID spam** | UC-35 | **[recon-and-attacks.md](recon-and-attacks.md)** ✅ | — |
| **Evil Portal** | UC-36 | **[evil-portal.md](evil-portal.md)** ✅ | — |
| **Channel/signal analyzer** | UC-37 | **[recon-and-attacks.md](recon-and-attacks.md)** ✅ | — |
| **Wardrive (no GPS)** | UC-38 | **[recon-and-attacks.md](recon-and-attacks.md)** ✅ | — |
| **Detect deauth / defensive** | UC-54 | **[recon-and-attacks.md](recon-and-attacks.md)** ✅ | — |

## Docs
- **[wpa-handshake-pmkid.md](wpa-handshake-pmkid.md)** — ✅ how WPA-PSK capture + offline cracking works.
- **[own-network-audit.md](own-network-audit.md)** — ✅ runnable mini-guide: audit your own PSK (capture → hcxtools → hashcat).
- **[deauth.md](deauth.md)** — ✅ deauthentication: the 802.11 flaw, the Marauder tool, PMF defense.
- **[evil-portal.md](evil-portal.md)** — ✅ rogue-AP captive-portal credential harvesting + defenses.
- **[recon-and-attacks.md](recon-and-attacks.md)** — ✅ the rest of the Marauder toolset: scan/recon, sniff→PCAP, beacon spam, channel analyzer, wardrive, detect-deauth.
- **[marauder-mcp-scan.md](marauder-mcp-scan.md)** — ✅ guide: the agent recipe to run `scanap` over the **BLE MCP** (Marauder seizes USB) and read the full network list from the SD log.

## Open questions / to research
- All Wi-Fi use-cases now have deep-dives (recon/sniff/spam/analyzer/wardrive/detect in [recon-and-attacks.md](recon-and-attacks.md)).
- Confirm my Marauder build's exact tool menu + version.
- BLE-side tools (AirTag/skimmer detection, spam) may deserve a sibling `ble.md`.

## Sources
- Marauder wiki: https://github.com/justcallmekoko/ESP32Marauder/wiki
