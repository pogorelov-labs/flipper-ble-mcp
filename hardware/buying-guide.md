---
title: GPIO Add-On Buying Guide
domain: hardware
type: reference
status: detailed
summary: Which GPIO add-on(s) to buy, by goal/persona, with a board-vs-persona comparison table.
hardware: [devboard, esp32-marauder, cc1101-ext, nrf24, gps]
use_cases: []
related: [hardware/gpio-addons-current.md, hardware/README.md, hardware/addons-explained.md, hardware/esp32-firmware-comparison.md, capabilities/sub-ghz.md, legal-and-safety.md]
tags: [buying-guide, devboard, esp32, cc1101, nrf24, gps, wardriving, decision-framework]
last_verified: 2026-06-19
---

# GPIO Add-On Buying Guide

> **TL;DR —** A decision framework (not a ranking) for which Flipper GPIO board to buy, organized by goal/persona — all-rounder, Wi-Fi/BLE testing, Sub-GHz range, hardware dev, wardriving — with golden rules (plug-and-play vs solder, power, shared SPI, legality) and a board-vs-persona comparison table. Prices are 2026 ballparks (verify).
> Boards in detail: [gpio-addons-current.md](gpio-addons-current.md) · pin/power limits: [README.md](README.md) · law/safety: [../legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md).

A **decision framework**, not a ranking — your focus isn't fixed, so start from *what you want to do* and let that pick the board. **Prices/stock drift fast** (boutique PCBs, Tindie, frequent re-spins) — treat every figure below as a **2026 ballpark `(verify)`**, not a quote.

## Start minimal (read this first)
- **Just learning GPIO / electronics?** Don't buy a backpack yet. Get a **proto board + jumpers + a breadboard** (~$5–15) and poke the buses/ADC/PWM directly. Nothing here needs a co-processor. → [README.md](README.md), [../topics/tinkering.md](../topics/tinkering.md)
- **First *powered* board, want zero risk?** The **official ESP32-S2 Wi-Fi DevBoard (~$49 official / ~$60 retail)** is the safe default: first-party, USB-C powered, documented, and useful even before any hacking (it's a wireless **SWD debug probe/flasher** out of the box; flash Marauder later for Wi-Fi).
- **Golden rules before buying:**
  1. **Plug-and-play vs solder** — pre-assembled boards (DevBoard, Rabbit-Labs, multiboards) need no soldering; bare modules (NRF24, some CC1101) may.
  2. **Power** — Wi-Fi/ESP boards spike current; **run the Flipper from USB** and expect to flip **5V on GPIO → ON** ([README.md](README.md)).
  3. **Shared SPI** — on multiboards, **CC1101 + NRF24 + microSD share one SPI bus**; they generally **don't all run at once**. Wi-Fi (UART/own MCU) is independent of that.
  4. **Legality** — Wi-Fi deauth, RF range-extension, and TX in restricted bands are **regulated/illegal without authorization**. Test only your own gear. → [../legal-and-safety.md](../legal-and-safety.md), [../topics/security-pentest.md](../topics/security-pentest.md)

## By persona

### (a) All-rounder / just explore
- **Buy:** **Official ESP32-S2 DevBoard** + a **proto board/jumpers**. Optionally one **CC1101+NRF24 combo (~$30)** later.
- **Why:** safest powered entry, first-party support, doubles as a flasher/debugger; proto board covers GPIO/sensor learning with no extra silicon. Grows with you.
- **FW/app:** stock (Black Magic/CMSIS-DAP) → flash **Marauder** or **Ghost ESP** when curious about Wi-Fi.
- **Gotchas:** S2 is **2.4 GHz only** (no 5 GHz). Power from USB for Wi-Fi.

### (b) Wi-Fi & BLE security testing
- **Buy:** an **ESP32-C5 board** for **dual-band Wi-Fi 6 (2.4 + 5 GHz)** — e.g. **Rabbit-Labs Poltergeist / ESP32-C5 Multi-Board**, **Ghost ESP-supported C5/C6** boards. Budget alt: any **ESP32-S2/S3 Marauder** board (2.4 GHz).
- **Why:** 5 GHz needs a C5/C6-class chip; S2/S3 can't do it. C5 boards unlock modern-AP testing, WPA3 probing, evil-portal, PCAP/Wireshark-over-USB.
- **Price band:** **~$25–45** (S2/S3 single-radio) → **~$60–125** (C5 multi-radio).
- **FW/app:** **ESP32 Marauder** or **Ghost ESP (Revival)** + companion app. Pick by board support; both do deauth/handshake/evil-portal.
- **Gotchas:** **legality is the headline** — deauth/handshake capture is an *active* attack; **authorized targets only** ([../legal-and-safety.md](../legal-and-safety.md)). 5 GHz draw is high → USB power. Marauder vs Ghost ESP support per board differs `(verify)`.

### (c) Sub-GHz range & RF work
- **Buy:** **External CC1101 module with SMA + (LNA/PA)** — e.g. **Rabbit-Labs Flux Capacitor (CC1101 + LNA, clean 5 V)**, or generic external CC1101 SMA boards.
- **Why:** external antenna + low-noise/amplified front end → far better RX and longer TX than the internal 433-tuned trace, while using the **stock Sub-GHz app** ("external module").
- **Price band:** **~$15–40** (bare external CC1101) → **~$40–70+** (LNA/PA + quality SMA).
- **FW/app:** stock Sub-GHz (enable external module) on Unleashed/Xtreme/RogueMaster/Momentum.
- **Gotchas:** **amplified TX can break RF-power/band law fast** — receive-focus is safer; treat "2000 ft" claims as marketing. Uses the **shared GPIO SPI**. → [../capabilities/sub-ghz.md](../capabilities/sub-ghz.md)

### (d) Hardware / electronics dev & debugging
- **Buy:** **Official ESP32-S2 DevBoard** (as an **SWD probe/flasher**) + a **proto board** + jumpers; optional **logic-level sensors** (I²C/1-Wire/UART).
- **Why:** the DevBoard's stock firmware is a **Black Magic + CMSIS-DAP wireless/USB debug probe** for ARM targets — genuinely useful for embedded dev. Proto board exposes SPI/I²C/UART/1-Wire/ADC/PWM ([README.md](README.md)).
- **Price band:** **DevBoard ~$49–60**; proto/jumpers **~$5–15**.
- **FW/app:** stock DevBoard fw for SWD; GPIO/sensor apps + your own FAP for custom I/O.
- **Gotchas:** **3.3 V logic, NOT 5 V-tolerant** — level-shift 5 V parts; respect ~20 mA/pin and the 5 W total. ADC is **slow 12-bit reads**, not a DAQ/scope.

### (e) Wardriving / GPS mapping
- **Buy:** an **ESP32 + GPS combo**. Best value/feature: an **ESP32-C5 multiboard with onboard GPS** (Rabbit-Labs C5 Multi-Board ~$125; **ESP32 Marauder 5G "Apex 5" ~$99** adds 2× Sub-GHz + NRF24 + GPS). Budget: **ESP32 board + separate UART GPS module (~$10–20)**.
- **Why:** wardriving = ESP32 captures Wi-Fi/BLE while GPS geotags it; an all-in-one PCB avoids wiring and frees the bus. 5 GHz (C5) sees more modern APs.
- **Price band:** **~$30 (DIY ESP32+GPS)** → **~$99–125 (integrated C5 + GPS multiboard)**.
- **FW/app:** **Marauder/Ghost ESP** (Wi-Fi+wardrive) + **[NMEA] GPS** app; "subdriving" geotags Sub-GHz too.
- **Gotchas:** logging is generally passive (legal-er) but **check local law**; GPS needs sky view + cold-start time; integrated boards still share SPI for CC1101/NRF24/SD.

## Comparison table

| Board | Best persona fit | Chip(s) / radios | ~Price (2026, verify) | Notes |
|---|---|---|---|---|
| **Official Wi-Fi DevBoard** | a, b (2.4G), d | ESP32-**S2** | **~$49 / $60 retail** | Safest first board; SWD probe + flasher stock; flash Marauder for Wi-Fi. 2.4 GHz only |
| **Proto board + jumpers** | a, d | none | **~$5–15** | Best GPIO/electronics *learning*; no co-processor; hot-swap modules |
| **ESP32-S2/S3 Marauder board** | b (budget) | ESP32-S2/S3 | **~$25–45** | Cheap Wi-Fi/BLE attacks; **no 5 GHz** |
| **Rabbit-Labs Poltergeist** | b | ESP32-**C5** | **~$60–90** `(verify)` | Dual-band **Wi-Fi 6**, BLE spam, 940 nm IR TX/RX, OLED; Ghost ESP |
| **Rabbit-Labs ESP32-C5 Multi-Board** | b, c, e | ESP32-C5 + CC1101 + GPS | **~$125** | Wi-Fi 6 + Sub-GHz + GPS in one; Marauder; shared-SPI caveat |
| **ESP32 Marauder 5G "Apex 5"** | b, c, e | ESP32-C5 + 2× Sub-GHz + NRF24 + GPS | **~$99** | Most radios per dollar; dual Sub-GHz (433/868) + NRF24 + GPS |
| **"Predator"/3-in-1 combos** | b, c, e | ESP32 + CC1101 + GPS (+NRF24) | **~$40–90** `(verify)` | Many vendors (FlipMods/MTools/Rek5); nickname, not one product; shared SPI |
| **External CC1101 (+LNA/PA, SMA)** | c | TI CC1101 | **~$15–70** | Range/RX boost via stock Sub-GHz; amplified TX = legal risk |
| **Rabbit-Labs Flux Capacitor** | c | CC1101 + LNA | **~$40–70** `(verify)` | Clean 5 V supply, low-noise → cleaner long-range RX |
| **NRF24 / CC1101+NRF24 combo** | a, b | nRF24L01+ / Si24R1 (+CC1101) | **~$10–30** | MouseJack HID injection + 2.4 GHz sniff; combo ~$30; bare module may need soldering |
| **GPS module (standalone)** | e | u-blox/ATGM336H/Beitian NMEA | **~$10–20** | Add GPS to any ESP32 board over UART; pairs with [NMEA] GPS app |

> One board can't do everything at full tilt: **Wi-Fi (ESP, own MCU/UART) is independent**, but **CC1101 + NRF24 + microSD contend on the shared SPI bus** — buy for the radios you'll actually run *together*.

## Open questions / to research
- Live 2026 street prices/stock for Poltergeist, Flux Capacitor, Apex 5, and the C5 Multi-Board (boutique drift).
- Which C5/C6 boards are best-supported *today* by Marauder vs Ghost ESP Revival for 5 GHz.
- Real concurrency on multiboards: which radio combos actually co-run vs SPI-mux switching.
- Whether the official DevBoard sees a 2026 chip refresh (S2 vs S3/C-series).
- Cheapest reliable plug-and-play GPS-integrated wardriving board under ~$60.
- IR-blaster-only SKUs (Slim Shady / Masta-Blasta) naming/availability `(verify)`.

## Sources
- Board details + links: [gpio-addons-current.md](gpio-addons-current.md)
- Official DevBoard: https://flipper.net/products/wifi-devboard · https://docs.flipper.net/zero/wifi-devboard
- Rabbit-Labs ESP32-C5 multiboard (CNX, 2026-03): https://www.cnx-software.com/2026/03/16/rabbit-labs-flipper-zero-esp32-c5-multi-board-features-cc1101-gps-and-dual-band-wi-fi-6/
- ESP32 Marauder 5G "Apex 5" (CNX, 2026-02): https://www.cnx-software.com/2026/02/11/esp32-marauder-5g-apex-5-module-for-flipper-zero-combines-esp32-c5-two-sub-ghz-radios-nrf24-and-gps/
- Rabbit-Labs store: https://rabbit-labs.com/product-category/flipper-gpio-boards/ · Ghost ESP boards: https://ghostesp.net/boards.html · Marauder builds: https://esp32marauder.com/builds.html
- 5GHz board comparison (5Ghost vs Marauder): https://www.pingequa.com/blogs/product-updates-news/flipper-zero-5ghz-5ghost-vs-esp32-marauder
