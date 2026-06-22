---
title: GPIO Add-Ons — Potential / DIY / Emerging
domain: hardware
type: reference
status: detailed
summary: DIY GPIO add-ons — I²C/SPI/UART sensors, displays, LoRa, BLE sniffer, logic analyzer, and design limits.
hardware: [nrf52840]
use_cases: []
related: [hardware/README.md, hardware/gpio-addons-current.md, hardware/buying-guide.md, hardware/addons-explained.md, bluetooth/ble-sniffer-addon.md]
tags: [diy, sensors, i2c, spi, uart, lora, logic-analyzer, ble-sniffer]
last_verified: 2026-06-19
---

# GPIO Add-Ons — Potential / DIY / Emerging

> **TL;DR —** What you can build or attach beyond off-the-shelf backpacks — I²C/SPI/UART sensors, displays, LoRa, an nRF52840 BLE-connection sniffer, a low-speed logic analyzer, custom protoboards — plus what's NOT realistic (true SDR, heavy STM32 compute) and the 3.3 V / current / bus-sharing constraints to design around.
> Pin reference: [hardware/README.md](README.md). Current boards: [gpio-addons-current.md](gpio-addons-current.md).
> Part of the [KB](../README.md).

The 18-pin header is a generic **3.3 V** MCU breakout, so most 3.3 V peripherals are fair game.

## Realistic DIY directions

- **I²C sensors (pins 15/16):** temp/humidity (BME280, SHT3x, AHT20), pressure, **IMUs**
  (MPU-6050, ICM-series), ToF distance (VL53L0X), light/UV, RTCs, OLED/e-paper. Easiest path —
  many sensor FAPs exist; chain multiple by address.
- **SPI peripherals (pins 2–6):** SD cards, extra radios (CC1101, NRF24, even **LoRa SX127x/
  SX126x** — emerging, niche), small TFT displays. One CS-selected device at a time; watch SPI
  contention and the current budget.
- **UART peripherals (pins 13/14 or 15/16):** GPS, ESP32/ESP8266 co-processors, serial sensors,
  GNSS, LTE/Cat-M modems, serial bridges, console logging. Most flexible DIY path (USART menu +
  UART-bridge apps).
- **Displays:** secondary I²C/SPI OLED/TFT/e-paper status screen.
- **Logic analyzer / signal work:** GPIO pins as a **basic logic analyzer / sniffer** (existing
  FAPs), bit-banged protocols, PWM, simple ADC capture on analog-capable pins (PA7/PA6/PA4/PC3).
  Good for **low-speed** digital RE; **not** a high-rate analyzer.
- **LoRa:** SX1276/SX1262 over SPI is feasible and appearing in community projects — treat as
  experimental; verify driver/app support, antenna, power.
- **BLE connection sniffer:** the rig can't follow/decrypt BLE connections; an **nRF52840** dongle
  (nRF Sniffer) or **Sniffle** (TI CC26x2) can — incl. a Flipper-hosted add-on. See
  [../bluetooth/ble-sniffer-addon.md](../bluetooth/ble-sniffer-addon.md).
- **Custom backpacks:** use official proto boards or a KiCAD template to design sensor hubs,
  relays, actuators, or NFC/RFID front-ends.

## What is NOT realistic
- **SDR.** The Flipper is **not an SDR** — no wideband I/Q. "SDR-adjacent" here means
  fixed-function transceivers (CC1101, NRF24, ESP32 Wi-Fi/BLE). True SDR belongs on a paired host.
- **Heavy compute on the STM32.** Wi-Fi/5 GHz/camera/video must be **offloaded** to a companion
  MCU (ESP32/RP2040); the Flipper is the UI/host.

## Constraints to design around
- **3.3 V logic only** — level-shift any 5 V sensor I/O. The 5 V pin **powers** peripherals, it's not a logic level.
- **Current budget:** 3V3 and 5V each ≤ **1.2 A**; per-pin ~**20 mA**; total I/O ≤ **5 W**. Run high-draw boards (ESP32 TX, amplified radios) with the Flipper **USB-powered**.
- **5 V must be toggled on** in the GPIO menu (battery/USB-sourced).
- **Bus sharing:** shared SPI/CS/SD pins limit simultaneous multi-radio use (firmware-mediated).

## Open questions / to research
- Concrete first DIY project to validate the toolchain (e.g., I²C BME280 read via a FAP or JS).
- LoRa-on-Flipper state of the art (which repo/app, range, legality).
- Best logic-analyzer FAP and its sample-rate ceiling.

## Sources
- GPIO & modules: https://docs.flipper.net/zero/gpio-and-modules
- Developer docs (external hardware): https://developer.flipper.net
- Proto boards: https://flipper.net/products/proto-boards
