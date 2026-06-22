---
title: GPIO Add-Ons Explained — Plain Words, Use Cases & Pros/Cons
domain: hardware
type: reference
status: detailed
summary: Plain-words use-cases + pros/cons for each Flipper GPIO add-on — GPS, NRF24, CC1101, BLE sniffer, thermal, geiger.
hardware: [devboard, vgm, esp32-marauder, nrf24, cc1101-ext, nrf52840, gps]
use_cases: []
related: [hardware/gpio-addons-current.md, hardware/esp32-marauder-module.md, hardware/gpio-addons-potential.md, hardware/buying-guide.md, hardware/README.md, bluetooth/ble-sniffer-addon.md, my-setup.md]
tags: [add-ons, gpio, use-cases, pros-cons, sensors, plain-language]
last_verified: 2026-06-21
---

# GPIO Add-Ons Explained — Plain Words, Use Cases & Pros/Cons

> **TL;DR —** A plain-English tour of the Flipper's GPIO add-ons — for each one: what it actually is, what you'd use it for, and the pros/cons — covering off-the-shelf boards (GPS, NRF24, CC1101+amp, BLE sniffer, IR blaster, multiboards, camera), DIY sensor backpacks (thermal grid, ToF, environment, geiger, LoRa, logic analyzer), and the things people ask for that **aren't** a Flipper thing (directional mics, lasers, true thermal cams, SDR).
> Pick one by goal: [buying-guide.md](buying-guide.md) · terse specs + links: [gpio-addons-current.md](gpio-addons-current.md) · DIY/limits: [gpio-addons-potential.md](gpio-addons-potential.md) · pins/power: [README.md](README.md). Part of the [KB](../README.md).

The one fact that governs everything below ([README.md](README.md)): the Flipper's 18-pin header is a **3.3 V MCU breakout**, not an SDR or a compute platform. Anything that speaks **I²C / SPI / UART at 3.3 V** is fair game; anything needing real RF, video, or heavy compute has to be **offloaded to a companion chip** (ESP32/RP2040). All of these share the one header, so it's **one backpack at a time**. **Prices are 2026 ballparks `(verify)`**, not quotes.

## How to read this
Each entry has the same shape: **plain words** (what it is), **use it for**, **pros**, **cons**, **good to know** (interface · price · firmware/app). This doc is the *explainer* lens — for a buy decision by persona use the [buying-guide.md](buying-guide.md); for chips/interfaces/links use [gpio-addons-current.md](gpio-addons-current.md).

---

## Off-the-shelf add-ons (buy today)

### GPS module
**Plain words:** a satellite-positioning chip on a board — the same thing in your phone's maps — that tells the Flipper where it is.
- **Use it for:** logging *where* you saw each Wi-Fi network or Sub-GHz signal ("wardriving" / "subdriving") to map them later; basic position/speed readout.
- **Pros:** cheap; simple UART wiring; pairs with an ESP32 board to turn scans into a map.
- **Cons:** useless indoors / needs sky view; slow first "cold start" (minutes); adds location only — it captures nothing on its own.
- **Good to know:** UART · ~$10–25 · `[NMEA] GPS` app (works on Momentum). See [gpio-addons-current.md](gpio-addons-current.md).

### NRF24 module
**Plain words:** a tiny 2.4 GHz radio that talks the same language as many cheap wireless keyboards and mice.
- **Use it for:** testing whether *your own* wireless keyboard/mouse is unencrypted — and if so, injecting keystrokes ("MouseJack").
- **Pros:** very cheap; demonstrates a real, common flaw convincingly.
- **Cons:** only old/unencrypted HID gear; legally sensitive (your own devices only); bare modules need careful wiring.
- **Good to know:** SPI · ~$5–15 · authorized targets only → [../legal-and-safety.md](../legal-and-safety.md).

### External CC1101 + amplifier (LNA/PA)
**Plain words:** a beefed-up version of a 433/Sub-GHz board — same radio, but with an amplifier and a bigger external antenna for more range.
- **Use it for:** reaching Sub-GHz devices (garage remotes, sensors, TPMS) from farther than the internal radio or a basic plug-on board.
- **Pros:** noticeably better receive/range; clean SMA antenna; uses the **stock Sub-GHz app** ("external module").
- **Cons:** if you already own a plain CC1101 board this is an upgrade, not a new capability; "2 km!" claims are marketing; **amplified TX can break RF-power/band law fast**.
- **Good to know:** SPI (shared bus) · ~$15–70 · e.g. Rabbit-Labs "Flux Capacitor" `(verify)`. → [../capabilities/sub-ghz.md](../capabilities/sub-ghz.md).

### BLE sniffer (nRF52840 dongle / TI Sniffle)
**Plain words:** a dedicated Bluetooth-Low-Energy listening device that does the one BLE job the Flipper *can't* do alone.
- **Use it for:** actually following and decoding a live Bluetooth connection (smart locks, wearables, beacons) — not just seeing that it exists.
- **Pros:** real packet capture into Wireshark; fills a genuine gap in the Flipper's abilities.
- **Cons:** more a "plug into your laptop" tool than a slick backpack; learning curve; you read raw packets.
- **Good to know:** USB dongle · ~$10–50 · see [../bluetooth/ble-sniffer-addon.md](../bluetooth/ble-sniffer-addon.md).

### IR blaster (high-power)
**Plain words:** a much stronger version of the Flipper's built-in infrared "remote control" emitter.
- **Use it for:** controlling/powering off TVs and projectors across a large room, where the Flipper's short-range IR gives up.
- **Pros:** big range boost; same easy "universal remote" use; totally legal and harmless.
- **Cons:** still line-of-sight only (IR is invisible light); narrow use case; overlaps a built-in feature.
- **Good to know:** ~$15–40 · Rabbit-Labs Poltergeist / Slim Shady `(verify SKU naming)` → [../capabilities/infrared.md](../capabilities/infrared.md).

### Multiboard ("Predator" style)
**Plain words:** an all-in-one backpack that crams Wi-Fi (ESP32), long-range Sub-GHz (CC1101), and GPS onto a single board.
- **Use it for:** serious wardriving/mapping without swapping boards — Wi-Fi + radio + location in one.
- **Pros:** convenience; one purchase replaces several backpacks; usually an OLED screen.
- **Cons:** the radios **share one SPI bus**, so they often can't all run at once; "Predator" isn't one trusted product — quality varies by vendor; pricier.
- **Good to know:** ~$40–125 `(verify vendor)` · runs Marauder / Ghost ESP. → [gpio-addons-current.md](gpio-addons-current.md).

### Camera backpack (ESP32-CAM / Mayhem Fin)
**Plain words:** a small camera module whose picture shows up on the Flipper's screen.
- **Use it for:** a novelty live feed or a cheap inspection/experiment cam.
- **Pros:** cheap; fun; the Mayhem version also bundles radios, a flashlight, and microSD.
- **Cons:** the Flipper screen is **128×64 black-and-white**, so the image is a blurry gray blob — not real photography or surveillance.
- **Good to know:** UART · ESP32-CAM ~$10; Mayhem Fin is a DIY open-hardware build `(verify)`.

---

## DIY sensor backpacks (real, but niche/hobbyist)

These follow the I²C/SPI/UART sensor path in [gpio-addons-potential.md](gpio-addons-potential.md); most need a community FAP whose state you should confirm.

### Thermal "camera" (AMG8833 / MLX90640 grid sensor)
**Plain words:** a heat sensor that reads temperature across a tiny grid — people call it a thermal camera, but it's closer to a grid of heat-detecting pixels.
- **Use it for:** spotting warm vs cold — a person in a room, an overheating component, a draft.
- **Pros:** genuinely "sees" heat; cheap entry into thermal imaging.
- **Cons:** resolution is **8×8 or 32×24** — a fuzzy heat blob, nothing like a real FLIR image; needs a community app that may be stale `(verify)`.
- **Good to know:** I²C · AMG8833 ~$25–40 / MLX90640 ~$30–60.

### Time-of-Flight distance sensor (VL53L0X)
**Plain words:** a sensor that bounces invisible light off objects to measure distance — a tiny "lidar."
- **Use it for:** distance/range measuring, simple presence detection, robotics tinkering.
- **Pros:** cheap; accurate at short range; easy I²C.
- **Cons:** very short range (~2 m); single point, not a 3D scan; a maker toy more than a security tool.
- **Good to know:** I²C · ~$5–10.

### Environment sensors (BME280, IMU, light/UV)
**Plain words:** small chips that measure temperature, humidity, air pressure, motion, or light.
- **Use it for:** a pocket weather/air readout; logging motion or tilt; learning electronics.
- **Pros:** dirt cheap; lots of existing apps; easy to chain several together by address.
- **Cons:** nothing to do with security/RF — purely hobby/maker; the small screen limits how you view data.
- **Good to know:** I²C · ~$5–10 each.

### Geiger counter
**Plain words:** a radiation detector wired to the Flipper so it can count radioactive "clicks."
- **Use it for:** measuring background radiation; checking rocks, old clock dials, etc.; science/education.
- **Pros:** a genuinely useful niche instrument; satisfying project.
- **Cons:** the tube is the expensive part; mostly DIY with community firmware `(verify)`; not a mainstream accessory.
- **Good to know:** GPIO pulse input · ~$30–60+.

### LoRa module (SX127x / SX126x)
**Plain words:** a long-range, low-power radio meant for sending tiny messages over kilometers.
- **Use it for:** experimenting with long-distance, low-bandwidth messaging/telemetry.
- **Pros:** impressive range for the power; growing community interest.
- **Cons:** experimental on Flipper — driver/app support is immature `(verify)`; regional frequency/legal rules; not plug-and-play.
- **Good to know:** SPI · ~$8–20.

### Logic analyzer
**Plain words:** using the Flipper's pins to watch the electrical 1s-and-0s on another device's wires.
- **Use it for:** reverse-engineering or debugging electronics — seeing how two chips talk.
- **Pros:** basically free (an app + pins you already have); great learning tool.
- **Cons:** **low speed only** — it can't keep up with fast modern buses; a real USB logic analyzer is far more capable.
- **Good to know:** built-in GPIO + a FAP. → [../topics/tinkering.md](../topics/tinkering.md).

---

## Not really a Flipper thing

People ask for these a lot; they don't have a real path on this hardware ([gpio-addons-potential.md](gpio-addons-potential.md) → "What is NOT realistic"):

- **Directional microphones** — there's no meaningful audio-input chain. You *could* hang an analog mic on an ADC pin, but there's no app or practical use. Effectively not a thing.
- **Lasers** — no laser add-on exists. The closest is the **infrared emitter** (invisible light for remotes). Toggling a laser diode from a GPIO pin is a wiring stunt, not a tool.
- **True thermal cameras, full video, SDR (software-defined radio)** — all need dedicated hardware the Flipper can't host. The Flipper is **not** an SDR (no wideband I/Q); that work belongs on a laptop with proper gear.

## Open questions / to research
- Current best-maintained Flipper FAPs for AMG8833/MLX90640 thermal and for Geiger tubes (and their resolution/refresh limits) `(verify)`.
- LoRa-on-Flipper state of the art — which app/repo, real range, legality by region.
- Whether any community project gives a usable analog-mic or audio-capture path (likely no).
- Live 2026 prices/availability for IR-blaster-only and amplified-CC1101 SKUs `(verify)`.

## Sources
- Board specs + canonical links: [gpio-addons-current.md](gpio-addons-current.md) · DIY/limits: [gpio-addons-potential.md](gpio-addons-potential.md) · buy-by-goal: [buying-guide.md](buying-guide.md)
- GPIO & modules (official): https://docs.flipper.net/zero/gpio-and-modules
- Awesome Flipper — modules catalogue: https://awesome-flipper.com
- BLE sniffing background: [../bluetooth/ble-sniffer-addon.md](../bluetooth/ble-sniffer-addon.md)
