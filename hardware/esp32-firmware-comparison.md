---
title: ESP32 Backpack Firmware — Bruce vs Ghost ESP vs Marauder
domain: hardware
type: reference
status: detailed
summary: Bruce vs Ghost ESP vs Marauder — which firmware to flash on an ESP32 Flipper backpack.
hardware: [esp32-marauder]
use_cases: []
related: [hardware/gpio-addons-current.md, hardware/buying-guide.md, wifi/README.md, bluetooth/README.md, legal-and-safety.md]
tags: [esp32, wroom, marauder, ghost-esp, bruce, firmware, flashing, wifi]
last_verified: 2026-06-19
---

# ESP32 Backpack Firmware — Bruce vs Ghost ESP vs Marauder

> **TL;DR —** Compares the three serious ESP32 backpack firmwares — Marauder, Ghost ESP, Bruce — feature-by-feature and specifically for a screenless ESP32-WROOM (2.4 GHz, no screen), with flashing/switching steps and a recommendation. On a WROOM only the Wi-Fi/BLE features are real; Marauder is the default, Ghost ESP worth comparing, Bruce wants a screen.
> Board: [gpio-addons-current.md](gpio-addons-current.md) · Wi-Fi hub [../wifi/README.md](../wifi/README.md) · BLE [../bluetooth/README.md](../bluetooth/README.md). Part of the [KB](../README.md).

My Wi-Fi backpack is an **ESP32-WROOM** (2.4 GHz only, onboard microSD, **no screen**), driven over UART by the Flipper. It's reflashable, so the question is *which* firmware to run. This doc compares the three serious choices — **Marauder**, **Ghost ESP**, **Bruce** — and is honest about what each gives me on a *screenless WROOM* specifically. **Authorized targets / own gear only** ([../legal-and-safety.md](../legal-and-safety.md)).

## TL;DR for my board
- **Marauder** — best Flipper-driven Wi-Fi/BLE on a WROOM; UART-native, mature companion app. Keep this as the default.
- **Ghost ESP** — runs great headless via its Flipper app too; broader Wi-Fi/BLE suite (karma, WPA3 checks, live Wireshark, BLE/AirTag, GPS wardrive). Worth flashing to compare.
- **Bruce** — the widest multi-tool (adds IR / Sub-GHz / RFID-NFC), but it's built **around a screen**; headless WROOM use is a *subset* over WebUI/serial and is not the experience Bruce is designed for. Mostly irrelevant on my hardware.

## What each is / origin

| | **Marauder** | **Ghost ESP** (Revival) | **Bruce** |
|---|---|---|---|
| Author / project | **justcallmekoko** | orig. **Spooks4576** → **GhostESP-Revival** fork | **pr3y / BruceDevices** |
| Origin story | The OG ESP32 Wi-Fi/BLE pentest fw; Flipper companion over UART | Wi-Fi/BLE suite with an **LVGL on-device UI**; broad board support | "Predatory" **multi-tool** fw, **M5Stack-origin** (Cardputer/Sticks/Cores), now many boards |
| Stack | Arduino-ESP32 | **ESP-IDF / FreeRTOS** | Arduino-ESP32 |
| Primary use model | **Flipper companion** (also standalone w/ screen builds) | On-device UI **or** Flipper companion **or** web dashboard | **On-device** (screen + buttons); headless is secondary |
| Maintenance (2026) | Active (unified single-UART PCAP+text path, recent API fixes) | Active fork; orig. repo archived **2025-04-22** | Very active (~36 releases, latest ~May 2026) |
| Repo | github.com/justcallmekoko/ESP32Marauder | github.com/GhostESP-Revival/GhostESP · ghostesp.net | github.com/BruceDevices/firmware · bruce.computer |

## Feature-comparison matrix

Legend: ✅ yes · ➖ partial / conditional · ❌ no · *(hw)* = only if the board carries that peripheral.

| Capability | **Marauder** | **Ghost ESP** | **Bruce** |
|---|---|---|---|
| **Wi-Fi attacks** (scan, deauth, beacon/probe spam, PMKID/handshake, evil portal, sniff→PCAP) | ✅ full | ✅ full **+ karma, WPA3 checks, live Wireshark-over-USB** | ✅ (scan, deauth, beacon spam, evil portal, sniff/PCAP, ARP spoof, Wireguard) |
| **BLE** | ✅ scan + spam, some detect | ✅ scan/capture, spam, **AirTag spoof, Flipper detect** | ✅ scan, **BadBLE (Ducky)**, multi-OS spam, kbd emulation |
| **IR** (TX/RX) | ❌ | ➖ learn/replay *(hw IR)* | ✅ *(hw IR)* — capture/replay remotes |
| **Sub-GHz** (315/433/868/915) | ❌ | ➖ via **CC1101** *(hw)* | ✅ via **CC1101** *(hw)* — scan, copy, replay, custom payloads, jam, spectrum |
| **RFID / NFC** | ❌ | ➖ NFC / MIFARE attacks *(hw, e.g. PN532)* | ✅ *(hw)* — 125 kHz + 13.56, read/write/clone/emulate, Amiibo, Chameleon-style |
| **2.4 GHz / NRF24** | ❌ (uses ESP radio only) | ➖ NRF24 noted *(hw)* | ✅ *(hw)* — jam + **mousejack** |
| **GPS / wardrive** | ✅ *(hw GPS)* → log | ✅ *(hw GPS)* → **WiGLE CSV** | ✅ *(hw GPS)* |
| **On-device UI / screen** | ➖ standalone screen builds exist | ✅ **full LVGL** (touch/kbd/encoder) + web dashboard | ✅ **rich TFT UI — its whole design** |
| **Flipper-companion vs standalone** | ✅ **Flipper app** (best-in-class) | ✅ **Flipper app** + standalone + web | ➖ standalone-first; headless/Flipper use limited *(verify)* |
| **Board support incl. C5/C6 5 GHz** | Wide ESP32 family; some 5 GHz on C5/C6 builds *(verify per-build)* | **40+ boards**; explicit **WROOM/S2/S3/C3/C5/C6**, 2.4 **& 5 GHz** on C5/C6 | M5Stack + Lilygo (Cardputer, Sticks, Cores, T-Deck, T-Embed…), 15+ targets; **screen-bearing** |
| **Active maintenance** | ✅ | ✅ | ✅ |

5 GHz is a **chip** capability (C5/C6 dual-band), not a firmware trick — **WROOM is 2.4 GHz only** no matter what you flash.

## On a screenless ESP32-WROOM (my board) specifically

WROOM = **2.4 GHz Wi-Fi + BLE, no screen, no extra radios** unless the PCB physically adds them (mine doesn't carry IR/CC1101/RFID). So IR / Sub-GHz / RFID / NRF24 rows above are **N/A for me** regardless of firmware — only the Wi-Fi and BLE columns are real on this hardware.

- **Marauder + WiFi Marauder app** — the natural fit. UART-native, mature, and recent builds route **PCAP + text over a single serial channel** (no dual-UART wiring). All Wi-Fi recon/attack + BLE tools surface in the Flipper UI; PCAPs land on the Flipper SD (or the board's microSD). This is what [../wifi/README.md](../wifi/README.md) is already built around.
- **Ghost ESP + Flipper app** — also fully usable headless on a WROOM: the on-device LVGL UI simply isn't drawn, and I drive everything from the **Flipper companion** (or web dashboard / USB). Gains over Marauder on *this* board are software-only: **karma, WPA3 compliance checks, live Wireshark-over-USB, richer BLE/AirTag, WiGLE-CSV wardrive** (the wardrive still needs an external GPS).
- **Bruce** — runnable on a bare WROOM, but Bruce is **built around a screen + buttons**. There's an explicit **headless mode** (control via **WebUI + serial**: `wifi add <ssid> <pass>` → `info` for the IP → browse to it) that exposes a **subset** of features, and its headless sample env targets **ESP32-S3**, not WROOM. There's **no first-class Bruce Flipper-companion app** the way Marauder/Ghost ESP have *(verify)*. On my screenless WROOM most of Bruce's draw (IR/Sub-GHz/RFID/NFC, the slick TFT UI) is unreachable — so it's the weakest pick here.
- **FlipperHTTP** (jblanked) — different category: not an attack suite but a **Wi-Fi/HTTP bridge** firmware (WROOM is a supported target) that lets Flipper apps/scripts do HTTP/Wi-Fi. Flash it when an app needs *networking* (web requests, app stores, NTP) rather than RF attacks. Worth keeping on the shortlist as a "second hat" for the same board.

## Flashing & switching

- **One firmware at a time** — these overwrite the whole ESP32 app image. Reflashing is **fully reversible**: flash another later, nothing on the Flipper or microSD is harmed.
- **Easiest (macOS):** web flashers in **Chrome/Edge** (Web Serial) — **FZEE Flasher** (fzeeflasher.com) and the project web installers (Ghost ESP, Bruce, Spacehuhn ESP Web Tool) pick board + firmware and flash over USB, no toolchain.
- **Repeatable / scriptable:** **FZEasyMarauderFlash** (SkeletonMan03) — Python helper that fetches the right Marauder build and shells out to esptool.
- **Manual:** `esptool.py` (or `pip install esptool`) with the `bootloader.bin` / `partitions.bin` / firmware `.bin` + offsets from the release. Hold **BOOT** while plugging USB if the board doesn't auto-enter download mode; pick the right `/dev/cu.*` port on macOS.
- Quick fw swap = just re-run a web flasher with the other firmware; no need to erase first (the flasher handles it).

## Recommendation (for my WROOM)
1. **Keep Marauder** as the daily driver for **Flipper-driven Wi-Fi** — it's what my Wi-Fi docs assume and it's the smoothest UART companion.
2. **Flash Ghost ESP** to a spare moment and compare: on this 2.4 GHz/no-screen board the upside is the **extra Wi-Fi/BLE tooling + live Wireshark**, all drivable from the Flipper. Low-risk since flashing is reversible.
3. **Skip Bruce on this board** — it really wants a **screen-bearing** device (Cardputer/T-Embed/CYD). Revisit Bruce only if I get such a board; on a screenless WROOM it's strictly worse than Marauder/Ghost ESP.
4. Keep **FlipperHTTP** in mind as a reflash-on-demand option when I need Wi-Fi *networking* for an app rather than attacks.

## Open questions / to research
- Confirm there is still **no first-class Bruce Flipper-companion app** (headless WebUI/serial only) as of mid-2026 — currently flagged **(verify)**.
- Does Ghost ESP's Flipper app expose **every** feature the LVGL UI does on a screenless board, or are some UI-only?
- Which exact Marauder build is on my board now (menu + version) — needed to confirm the single-UART PCAP path is present.
- For a *future* 5 GHz board (C5/C6): Marauder vs Ghost ESP 5 GHz maturity — cross-check with [gpio-addons-current.md](gpio-addons-current.md) open questions.
- Does any of these expose **BLE-side** tooling worth a dedicated note in [../bluetooth/README.md](../bluetooth/README.md)?

## Sources
- Marauder: https://github.com/justcallmekoko/ESP32Marauder · Flipper: https://github.com/justcallmekoko/ESP32Marauder/wiki/flipper-zero · app: https://github.com/justcallmekoko/flipperzero-wifi-marauder
- Ghost ESP: https://ghostesp.net/ · https://github.com/GhostESP-Revival/GhostESP
- Bruce: https://github.com/BruceDevices/firmware · https://bruce.computer/ · headless: https://wiki.bruce.computer/controlling-device/headless-mode/ · serial: https://github.com/BruceDevices/firmware/wiki/Serial
- FlipperHTTP: https://github.com/jblanked/FlipperHTTP
- Flashing: https://github.com/SkeletonMan03/FZEasyMarauderFlash · https://fzeeflasher.com/ · https://docs.spacehuhn.com/blog/espwebtool/
- Comparison context: https://www.mobile-hacker.com/2024/12/23/exploring-marauder-bruce-and-ghost-esp-on-cheap-yellow-device/
