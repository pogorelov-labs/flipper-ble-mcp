---
title: GPIO Add-On Boards ("Backpacks") — Currently Available
domain: hardware
type: reference
status: detailed
summary: Current GPIO add-ons — DevBoard, VGM, Marauder/Ghost ESP, Mayhem, NRF24, CC1101, GPS, protoboards.
hardware: [devboard, vgm, esp32-marauder, nrf24, cc1101-ext, gps]
use_cases: []
related: [hardware/README.md, hardware/gpio-addons-potential.md, hardware/buying-guide.md, hardware/addons-explained.md, hardware/esp32-marauder-module.md, hardware/esp32-firmware-comparison.md, capabilities/sub-ghz.md]
tags: [backpacks, devboard, vgm, esp32, nrf24, cc1101, gps, wardriving]
last_verified: 2026-06-19
---

# GPIO Add-On Boards ("Backpacks") — Currently Available

> **TL;DR —** Catalogue of add-on modules you can buy/use today: official Wi-Fi DevBoard (ESP32-S2) and Video Game Module (RP2040), ESP32 Marauder/Ghost ESP/Mayhem boards, Predator-style multiboards, Rabbit-Labs lineup, NRF24 mousejack modules, external CC1101 amps, GPS, and protoboards — with chips, interfaces, and driver firmware. Items marked (verify) are plausible but unconfirmed.
> Pin reference & power limits: [hardware/README.md](README.md). DIY/emerging: [gpio-addons-potential.md](gpio-addons-potential.md).
> Items marked **(verify)** are plausible but not fully confirmed. Part of the [KB](../README.md).

## Summary table

| Board | Chip / HW | Interface | Capabilities it adds | Driver firmware / app | Source |
|---|---|---|---|---|---|
| Official **Wi-Fi DevBoard** | ESP32-S2-WROVER | UART + SWD (3V3) | Flash/debug Flipper & other MCUs (SWD); Wi-Fi attacks if reflashed | Black Magic + CMSIS-DAP (stock); Marauder/Ghost ESP (community) | [docs](https://docs.flipper.net/zero/wifi-devboard) |
| Official **Video Game Module** | RP2040 | VGM connector (3V3) | DVI-D 640×480 video out, 6-axis IMU, games, RP2040 dev | Flipper VGM apps | [docs](https://docs.flipper.net/zero/video-game-module) |
| **ESP32 Marauder** boards | ESP32 / S2/S3 | UART (3V3/5V) | Wi-Fi deauth/beacon-spam/PMKID & handshake capture, evil portal, BLE | Marauder + companion app | [repo](https://github.com/justcallmekoko/ESP32Marauder) |
| **Ghost ESP** boards | ESP32 / C5/C6 | UART (3V3/5V) | Wi-Fi 2.4/5 GHz suite, evil portal, GPS wardriving, Wireshark stream | Ghost ESP fw + app | [repo](https://github.com/GhostESP-Revival/GhostESP) |
| **Mayhem Fin** (eried) | ESP32-CAM (+NRF24/CC1101) | UART + SPI | Wi-Fi/BLE, 2 MP camera, microSD, NRF24/CC1101 radios, sensors | mayhem fork fw + apps | [repo](https://github.com/eried/flipperzero-mayhem) |
| **"Predator"/multiboards** | ESP32 + CC1101 + GPS (+NRF24) | UART + SPI | Wi-Fi + external Sub-GHz + GPS wardriving in one PCB | Marauder/Ghost ESP + Sub-GHz/GPS apps | multiple vendors |
| **Rabbit-Labs Poltergeist** | ESP32-C5 | UART, USB-C | Dual-band Wi-Fi 6, deauth, BLE spam, 940 nm IR blaster+RX, microSD, OLED | Ghost ESP | [link](https://rabbit-labs.com/product/rabbit-labs-poltergeist-5ghz-wifi-board/) |
| **Rabbit-Labs ESP32-C5 Multi-Board** | ESP32-C5 + CC1101 + GPS | UART + SPI, microSD | Wi-Fi 6 + Sub-GHz + GPS wardriving | Marauder | [Tindie](https://www.tindie.com/products/sometoms/flipper-zero-esp32-c5-multi-board/) |
| **Rabbit-Labs Flux Capacitor** | CC1101 + LNA | SPI (5V) | Amplified/low-noise external Sub-GHz (extended range) | Stock Sub-GHz (external CC1101) | [link](https://rabbit-labs.com/product/rabbit-labs-flux-capacitor-amplified-cc1101/) |
| **NRF24 modules** | nRF24L01+ / Si24R1 | SPI | 2.4 GHz sniffing, **MouseJack** (HID injection vs vulnerable kbd/mice) | NRF24 sniff/mousejack apps | [info](https://awesome-flipper.com/extra/module/nrf24/) |
| **External CC1101 + amps** | TI CC1101 (+PA/LNA, SMA) | SPI | Extended Sub-GHz TX/RX range (315/433/868/915 MHz) | Stock Sub-GHz ("external module") | [Tindie](https://www.tindie.com/products/bpmcircuits/cc1101-flipper-zero-sub-ghz-module-extended-range/) |
| **GPS modules** | u-blox/ATGM336H/Beitian NMEA | UART | Location, mapping, wardriving/subdriving | [NMEA] GPS app / wardriver | [app](https://lab.flipper.net/apps/gps_nmea) |
| **Proto / breadboard** | bare PCB | all buses | DIY breakout, hot-swap modules | n/a | [store](https://flipper.net/products/proto-boards) |

## Detail

### Official Wi-Fi DevBoard (ESP32-S2)
Flipper's first-party backpack. Uses **3V3, GND, UART (13/14), SWD (10/12)**; USB-C onboard.
Stock firmware = **Black Magic Debug + CMSIS-DAP**, turning Flipper+board into a **wireless/USB
SWD debug probe & flasher** (its own STM32 OTA + external ARM targets). Reflashable with
**Marauder / Ghost ESP / Evil Portal** for Wi-Fi 2.4 GHz testing (Wi-Fi attack fw is **not**
shipped — you flash it). *You don't need this board to update Flipper firmware.* The 2026 unit
keeps the **ESP32-S2** base _(verify "refresh" claims)_.
Docs: https://docs.flipper.net/zero/wifi-devboard · https://developer.flipper.net/flipperzero/doxygen/dev_board.html

### Official Video Game Module (RP2040 / VGM)
Co-developed with Raspberry Pi; **RP2040** core. Dedicated **VGM connector** (11 GPIO, I²C/SPI/
UART passthrough, USB-C host/device). **DVI-D 640×480@60**, **ICM-42688-P 6-axis IMU**, open
firmware/schematics. Beyond games it's a general **RP2040 dev platform** on the Flipper.
Docs: https://docs.flipper.net/zero/video-game-module

### ESP32 Marauder boards
Third-party ESP32 backpacks running **ESP32 Marauder** (Wi-Fi/BLE offensive fw). UART + companion
app. Capabilities: **deauth, beacon/probe spam, PMKID & WPA handshake capture, sniffing, evil
portal**, some **BLE**; with GPS → wardriving. Authorized assessments / RF education only.
Repo: https://github.com/justcallmekoko/ESP32Marauder/wiki/flipper-zero

### Ghost ESP boards / firmware
Alternative ESP32 fw + companion app (LVGL UI, 40+ boards). Original repo archived 2025-04-22;
continued as **"Revival."** Runs on **ESP32-C5/C6** (dual-band). Wi-Fi **2.4 & 5 GHz**, evil
portal, WPA3 testing, PCAP, **live Wireshark over USB**, BLE detection, **GPS wardriving**.
Repo: https://github.com/GhostESP-Revival/GhostESP · App: https://lab.flipper.net/apps/ghost_esp

### Mayhem Fin (eried)
Long-running "everything" backpack. **ESP32(-CAM)** over UART; v2+ adds **NRF24 + CC1101** over
SPI, 3V/5V sensor headers, **2 MP camera + PSRAM, microSD, flashlight**. Wi-Fi/BLE, camera
capture (low-res preview on the Flipper screen), NRF24 mousejacking, extended Sub-GHz, sensor I/O.
Open hardware (DIY build files). Repo: https://github.com/eried/flipperzero-mayhem

### "Predator" / multiboard combos (ESP32 + CC1101 + GPS)
A **category** of 3-/4-in-1 combos from many vendors (FlipMods, MTools, Rek5 Lab, etc.).
"Predator" is a colloquial nickname, not one canonical product **(verify)**. Combines Marauder/
Ghost-ESP Wi-Fi, **external long-range Sub-GHz (CC1101)**, **GPS wardriving**, sometimes NRF24 +
OLED. **Caveat:** SPI is shared (CC1101/NRF24/SD), so radios don't all run simultaneously.
Ref: https://www.cnx-software.com/2025/01/16/flipmods-combo-is-a-3-in-1-flipper-zero-expansion-module-with-esp32-gps-and-cc1101-modules/

### Rabbit-Labs lineup
Vendor with a unified footprint + open SDK (https://rabbit-labs.com/):
- **Poltergeist** — ESP32-C5; dual-band **Wi-Fi 6**, deauth + BLE spam, **940 nm IR blaster+RX**, microSD, OLED; runs Ghost ESP.
- **ESP32-C5 Multi-Board** — ESP32-C5 + **CC1101 (855–925 MHz)** + GPS + microSD; runs Marauder; ~$125, ~Mar 2026.
- **Flux Capacitor** — **CC1101 + LNA**, clean 5 V supply → cleaner/longer-range external Sub-GHz.
- **Slim Shady / Masta-Blasta** — high-output **IR blaster** **(verify SKU naming)**.

### NRF24 modules (mousejacking)
**nRF24L01+** (or Si24R1 clone) over **SPI** (MOSI=PA7/2, MISO=PA6/3, CSN=PA4/4, SCK=PB3/5,
CE=PB2/6, VCC=3V3/9). Sniff nRF24 addresses + **MouseJack** keystroke injection into unencrypted
wireless HID. Audit *your own* devices only.
Info: https://awesome-flipper.com/extra/module/nrf24/

### External CC1101 modules & power amps
External **CC1101** boards with **SMA antenna**, sometimes **PA/LNA**, over **SPI**; enabled via
Sub-GHz "external module." Same protocols as internal radio but **much greater range** (vendors
cite ~70–150 m; treat huge "2000 ft" claims as best-case marketing). Range extension can raise
**RF-power compliance** issues — use responsibly. Broadly supported on Unleashed/RogueMaster/Momentum.
Ref: https://cyberredcell.nl/flipper-zero-increasing-sub-ghz-range-with-cc1101-and-external-antenna/

### GPS modules (wardriving / mapping)
NMEA serial GPS (u-blox NEO-6M/7M, ATGM336H, Beitian, Adafruit) or TinyGPS boards over **UART**
(3V3/9, GND/11, TX/13, RX/14; default 9600 baud). Live position via **[NMEA] GPS** app;
**wardriving** (geo-tag Wi-Fi/BLE with ESP boards) and **"subdriving"** (geotag Sub-GHz captures).
App: https://lab.flipper.net/apps/gps_nmea · Wardriver: https://github.com/Sil333033/flipperzero-wardriver

### Prototyping / breadboard
Official **Proto Boards** + many unofficial protoboards/breadboard kits. Pass-through to all 18
pins for hot-swappable custom modules + GPIO diagnostics.
Store: https://flipper.net/products/proto-boards · KiCAD: https://github.com/lomalkin/flipperzero-protoboards-kicad

## Open questions / to research
- **Which board(s) to actually buy** for my goals (single ESP32-S2 DevBoard vs a multiboard vs CC1101-only).
- Simultaneous-radio limits on shared-SPI multiboards (what actually co-runs).
- Current best ESP32 fw for 5 GHz on C5/C6 (Marauder vs Ghost ESP Revival) — verify.

## Sources
- See inline links above + Awesome Flipper modules: https://awesome-flipper.com · Wi-Fi DevBoard: https://docs.flipper.net/zero/wifi-devboard · VGM: https://docs.flipper.net/zero/video-game-module
