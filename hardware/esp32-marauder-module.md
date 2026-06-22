---
title: ESP32-WROOM Marauder Backpack — Module Reference
domain: hardware
type: reference
status: detailed
summary: The ESP32-WROOM Marauder backpack hardware — GPIO 9-18 mount (3V3), the freeze fix, BOOT/RST buttons, dual-SD, flashing.
hardware: [esp32-marauder]
use_cases: []
related: [wifi/README.md, hardware/esp32-firmware-comparison.md, my-setup.md, hardware/gpio-addons-current.md, hardware/addons-explained.md, wifi/wpa-handshake-pmkid.md]
tags: [esp32, marauder, wroom, gpio, uart, microsd, flashing]
last_verified: 2026-06-21
---

# ESP32-WROOM Marauder Backpack — Module Reference

> **TL;DR —** Everything about the *physical* ESP32-WROOM "Flipper Zero" Marauder backpack on this rig: it mounts on **GPIO pins 9–18**, is **3V3-powered (pin 9) so it needs NO "5V on GPIO,"** **freezes the Flipper if hot-mounted while powered on** (power off first), has **BOOT + RST** buttons (for flashing only), and carries **its own microSD** for PCAP captures. What you *do* with it (scans/handshakes/deauth) lives in the [wifi sub-domain](../wifi/README.md).
> Rig: [my-setup §4](../my-setup.md) · firmware options: [esp32-firmware-comparison](esp32-firmware-comparison.md) · attacks: [wifi hub](../wifi/README.md). Part of the [KB](../README.md).

## What it is
A third-party **ESP32-WROOM** plug-on board ("Flipper Zero" + dolphin silkscreen) with an **onboard microSD** slot, a **10-pin** male header, and **no USB port**. WROOM = **2.4 GHz Wi-Fi + classic/BLE only — no 5 GHz**. It runs **[Marauder](https://github.com/justcallmekoko/ESP32Marauder)** firmware and is driven from the Flipper's **WiFi Marauder** companion app over UART.

**Capabilities (2.4 GHz):** AP/station scan, sniff, **WPA handshake + PMKID capture → PCAP**, deauth, beacon/probe spam, **Evil Portal**, some BLE recon. Workflows: [wifi/wpa-handshake-pmkid](../wifi/wpa-handshake-pmkid.md), [wifi/recon-and-attacks](../wifi/recon-and-attacks.md), [wifi/evil-portal](../wifi/evil-portal.md).

## Mounting — GPIO pins 9–18 (the UART/3V3 side)
- The 10-pin header seats on **pins 9–18**: **3V3 (pin 9)**, GND (11, 18), **UART TX (pin 13) / RX (pin 14)**, plus the rest of that row.
- **Powered from 3V3 (pin 9), which is always on → you do NOT need "5V on GPIO."** The +5V pin is **pin 1**, on the opposite **1–8** SPI side (used by the CC1101) — this board can't reach it.
- ⚠️ **It MUST land on 9–18, leaving 1–8 free.** If it sits on the **1–8 side it hijacks the SD's shared SPI bus** → boot **"Mounting SD card Failed"** (the Flipper's own SD, *not* the Marauder's). No damage — power off and reseat on 9–18. (Learned the hard way 2026-06-21.)
- The CC1101 (1–8) and Marauder (9–18) are both full-width backpacks → **only one mounts at a time** ([my-setup §6](../my-setup.md)).
- Pinout verified 2026-06-21: pin 1 = +5V, pin 9 = +3V3, pin 13 = TX, pin 14 = RX, GND = 8/11/18 ([Flipper GPIO docs](https://docs.flipper.net/zero/gpio-and-modules)).

## ⚠️ Power OFF before mounting (the freeze)
Hot-mounting/removing the backpack while the Flipper is **powered on** can **freeze it** — and the hang **survives unplugging**, so only a reboot clears it. Cause: pin 9 (3V3) is **always live**, so seating the board hits the rail with the ESP32's startup inrush *and* dumps boot chatter onto the Flipper's RX (pin 14) — a running MCU can latch up.
- **Fix:** power the Flipper **fully OFF** before mounting *or* removing. Off = no live rail at insertion.
- **Force-reboot if frozen:** hold **LEFT + BACK ~5 s** (SD/data unaffected).
- If after a clean mount the app still can't see the ESP32, check **Settings → Expansion Modules** — that background service also listens on the UART (13/14) and can fight the Marauder app for it.

## The two buttons (BOOT + RST)
Standard ESP32 buttons, reached through the case cutouts:

| Button | Does |
|---|---|
| **RST / EN** | reboots the ESP32 (harmless; restarts Marauder) |
| **BOOT (GPIO0)** | held *during* a reset → **firmware-flash (download) mode**; a momentary press while running does nothing |

- **Not used in normal operation** — the app drives everything over UART; only needed for reflashing.
- **Identify which is which empirically:** with the app connected, tap one — if the app drops/reconnects it's **RST**; if nothing happens it's **BOOT**. There's no reliable position convention.

## Two microSD cards — why both
The backpack's SD belongs to the **ESP32**; the Flipper's SD belongs to the **STM32**. Separate chips, separate buses — neither reads the other's card.

| Card | Holds |
|---|---|
| **Flipper SD** (STM32) | the WiFi Marauder *companion app* + text results returned over UART + your Flipper data |
| **Marauder SD** (ESP32) | the heavy **PCAP captures** (sniff / WPA handshake / PMKID) |

Why the ESP32 needs its own: the UART bridge is only **~11 KB/s (115200 baud)** — fine for commands and text, a bottleneck for packet capture. The ESP32 writes PCAPs **directly to its local SD** at full speed. **Upshot:** to get a capture onto a computer, pull the **Marauder's** card — the Flipper's won't have it.

## Flashing the ESP32 (no USB → via the Flipper)
This board has **no USB port**, so it's flashed **through the Flipper** with **[FZEasyMarauderFlash](https://github.com/SkeletonMan03/FZEasyMarauderFlash)**:
- Pick the **ESP32-WROOM** target (uses `old_hardware.bin`).
- **Hold BOOT** during the flash if it doesn't auto-enter download mode (no USB DTR/RTS to do it automatically).
- Keep the **companion app version matched** to the ESP32 firmware. Alternatives (FlipperHTTP / Ghost ESP): [esp32-firmware-comparison](esp32-firmware-comparison.md).

## Using it
1. Power OFF → mount on 9–18 → power ON (no 5V toggle).
2. **Apps → GPIO → [ESP32] WiFi Marauder** — it handshakes with the ESP32 (shows a firmware version).
3. Start with a **passive AP scan** + list (text over UART — no SD needed). Captures (PCAP) come later and land on the Marauder SD.
4. Run the Flipper on **USB** — Wi-Fi TX draws real current.

## Safety / legal
- **Passive** scan/sniff = listening to beacons everyone broadcasts → legal, low-risk.
- **Active** deauth / beacon-spam / **Evil Portal** = TX attacks → **your own networks only**, with authorization ([legal-and-safety](../legal-and-safety.md), [wifi/own-network-audit](../wifi/own-network-audit.md)).

## Open questions / to research
- Exact ESP32-WROOM variant + flash size on this specific board `(verify)`.
- Which keyhole cutout is BOOT vs RST on this case (resolve empirically per above).
- Whether the current Marauder build adds BLE features beyond recon on WROOM `(verify)`.
- Best PCAP-offload workflow (pull SD vs serial dump) for this no-USB board.

## Sources
- Marauder (Flipper): https://github.com/justcallmekoko/ESP32Marauder/wiki/flipper-zero
- Flasher: https://github.com/SkeletonMan03/FZEasyMarauderFlash
- Flipper GPIO pinout: https://docs.flipper.net/zero/gpio-and-modules
- This rig: [my-setup §4](../my-setup.md) · attacks: [wifi hub](../wifi/README.md)
