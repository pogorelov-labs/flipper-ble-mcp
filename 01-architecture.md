---
title: Flipper Zero — Architecture & Capability Map
domain: core
type: reference
status: detailed
summary: Hardware block map, STM32WB MCU, radios, software stack, SD layout, and full capability map.
hardware: [flipper-internal]
use_cases: []
related: [hardware/README.md, firmware/README.md, capabilities/sub-ghz.md, topics/tinkering.md]
tags: [architecture, stm32wb, radios, gpio, filesystem, capability-map]
last_verified: 2026-06-19
---

# Flipper Zero — Architecture & Capability Map

> **TL;DR —** What's inside the device and what each block does — STM32WB MCU, the fixed-function radios/interfaces, the software stack, and the SD layout — plus the full map of what it can actually do.
> Conceptual index — every block links to its deep-dive: [hardware](hardware/README.md), [firmware](firmware/README.md), [tinkering](topics/tinkering.md). Part of the [KB](README.md).

The Flipper Zero is a battery-powered, microcontroller-based multitool. It is **not an SDR**
and **not a general-purpose computer** — it's an STM32 MCU wired to a set of fixed-function
radios and interfaces, with a gamified UI ("the dolphin"). Custom firmware (Unleashed/Xtreme/
Momentum/RogueMaster) unlocks and exposes what this hardware can already do; it does not add
hardware capability. Heavy compute (Wi-Fi, 2.4 GHz, fast logic capture, video) is deliberately
pushed onto **companion MCUs** over GPIO — see the rationale at the bottom.

---

## Hardware block map

| Block | Part / spec | What it enables | Deep-dive |
|---|---|---|---|
| **MCU** | **STM32WB55RG** — dual core: Cortex-M4 @64 MHz (apps) + Cortex-M0+ @32 MHz (radio/BLE stack); 1024 KB shared flash, 256 KB shared SRAM | Runs Flipper OS (Furi over FreeRTOS); hosts apps (FAPs) + JS engine | [hardware/README.md](hardware/README.md) |
| **Sub-GHz radio** | **TI CC1101** transceiver + antenna; 315 / 433 / 868 / 915 MHz bands; ASK/OOK, 2-FSK; ≤20 dBm TX | Read/replay/brute-force remotes, sensors, gates; protocol decoders | [capabilities/sub-ghz.md](capabilities/sub-ghz.md) |
| **NFC (HF)** | **ST25R3916** front-end, 13.56 MHz; ISO14443A/B, ISO15693, FeliCa | Read/emulate/write HF cards (MIFARE Classic/Ultralight, NTAG, DESFire, etc.) | [capabilities/nfc-rfid.md](capabilities/nfc-rfid.md) |
| **RFID (LF)** | **125 kHz** — no dedicated chip; analog front-end + MCU bit-bang; AM/OOK | Read/emulate/write EM4100, HID Prox, Indala access cards (T5577 cloning) | [capabilities/nfc-rfid.md](capabilities/nfc-rfid.md) |
| **Infrared** | TX LED 940 nm (~300 mW); RX 950 nm demod, 38 kHz learning | Universal remote; capture/replay any consumer IR | [capabilities/infrared.md](capabilities/infrared.md) |
| **iButton / 1-Wire** | 1-Wire on GPIO pin 17 | Read/emulate Dallas DS1990A, Cyfral, Metakom keys | [capabilities/ibutton.md](capabilities/ibutton.md) |
| **GPIO** | 18-pin header: UART, SPI, I²C, 1-Wire, SWD; 3V3 + 5V power | Drive external modules; logic-analyzer/UART; debug other MCUs | [hardware/gpio-addons-current.md](hardware/gpio-addons-current.md) |
| **Bluetooth LE** | BLE **5.4** via STM32WB radio core; ≤4 dBm TX, 2 Mbps | BLE HID (BadBT keyboard), BLE scan/spam (CFW), app control | [capabilities/badusb.md](capabilities/badusb.md) |
| **USB** | USB-C, USB 2.0 full-speed (12 Mbps) | USB HID (BadUSB), CDC serial/CLI, mass storage, charging | [capabilities/badusb.md](capabilities/badusb.md) |
| **Storage** | microSD (≤256 GB) | Dumps, captures, apps, asset packs → [filesystem](#sd-card-filesystem-ext) | — |
| **Display** | 1.4" monochrome LCD, 128×64, sunlight-readable | UI | — |
| **Inputs** | 5-way D-pad + Back button | Navigation | — |
| **Feedback** | RGB LED, vibro motor, piezo speaker | Signals/alerts | — |
| **Power** | ~2100 mAh LiPo + battery-management IC (fuel gauge) | up to ~28 days idle; ~1 week typical use | — |

## MCU deep-dive: STM32WB55RG

The whole device hangs off one **dual-core wireless STM32WB55RG**. The two cores share flash
and RAM but have strictly separated jobs:

| Core | Clock | Role | Who programs it |
|---|---|---|---|
| **Cortex-M4** ("application core", CPU1) | 64 MHz | Runs the entire Flipper OS: Furi, FreeRTOS, GUI, all apps/FAPs, the JS engine, every peripheral driver | Flipper firmware (you flash this) |
| **Cortex-M0+** ("radio/network core", CPU2) | 32 MHz | Runs ST's sealed **wireless coprocessor (FUS + BLE stack)** for Bluetooth LE 5.4 | ST binary blob; flashed separately, normally untouched |

- **Memory:** 1024 KB flash and 256 KB SRAM, *shared* between cores. The BLE stack and FUS
  (Firmware Update Services) live in upper flash; the Flipper app firmware occupies the rest.
  This is why firmware images quote a flash budget and why the radio stack version is updated
  on its own track.
- **Inter-core comms:** the two cores talk over a hardware IPCC mailbox + shared SRAM2 (ST's
  "transparent mode"). Apps never touch the radio core directly — they call BLE through Furi's
  HAL, which marshals to CPU2. (verify exact IPCC channel mapping)
- **Why it matters:** Wi-Fi, Thread/Zigbee, and any 2.4 GHz beyond BLE are **not** in this
  silicon. The M0+ only does the ST BLE stack. That hard limit is the architectural reason
  Wi-Fi/2.4 GHz attacks require an external ESP32 board (see [rationale](#why-offload-to-companion-mcus)).

## Software stack (top → bottom)

| Layer | What lives here | Notes |
|---|---|---|
| **Apps / scripts** | FAPs (Flipper Application Packages, `.fap`) + on-device **JavaScript** | Installable from the catalog (Flipper Lab / mobile app) or built from source with `ufbt`. See [tinkering](topics/tinkering.md). |
| **Asset packs / UI** | Animations (`.bm` frames + `meta.txt`), icons, fonts | Heavily customizable on Momentum/RogueMaster → [asset packs](topics/tinkering.md). |
| **Furi core services** | Flipper's service layer over **FreeRTOS**: the **record/registry** store (named singletons like `gui`, `storage`, `notification`), **message queues**, **threads**, **view dispatcher / GUI** (views, view-ports, the `Gui` compositor) | "Furi" = Flipper Universal Registry Implementation; this is the app-facing OS API. |
| **HAL + drivers** | STM32WB HAL, radio drivers (**CC1101**, **ST25R3916**), LF front-end, IR, USB + BLE stacks | Hardware abstraction; FAPs go through HAL, not registers. |
| **Bootloader / DFU** | Recovery layer: bootloader + DFU; not overwritten by normal flashing | Makes bricks recoverable over USB-C. See [firmware/README.md](firmware/README.md). |

### Boot + firmware-update flow
1. **Bootloader** runs first (separate from the OS): checks for a pending update on the SD card,
   shows the splash, then jumps to the main firmware.
2. **Normal OTA update** (mobile app / qFlipper): a self-update package is staged on the SD card;
   on reboot the bootloader applies it. Radio stack (CPU2) updates go through ST's **FUS** and are
   a distinct step from the M4 firmware.
3. **Recovery / DFU:** holding a button combo drops the STM32 into **USB DFU**; qFlipper can then
   reflash bootloader + firmware over USB-C even on a soft-bricked device. The bootloader region is
   deliberately not touched by routine flashes, so recovery almost always works.
4. **Custom firmware** is just a different main-firmware image flashed by the same paths; it does
   not modify the ST radio blob.

### SD card filesystem (`/ext`)
The microSD is mounted at **`/ext`** (internal flash storage is `/int`). Each capability owns a
top-level folder; apps get a code dir and a data dir:

| Path | Contents |
|---|---|
| `/ext/subghz/` | Saved `.sub` captures; `subghz/assets/` holds protocol/freq config |
| `/ext/nfc/` | Saved `.nfc` cards (MIFARE, NTAG, DESFire…); `nfc/assets/` for keys/dicts |
| `/ext/lfrfid/` | Saved `.rfid` 125 kHz keys (EM4100, HID, Indala) |
| `/ext/infrared/` | `.ir` remotes; `infrared/assets/` = universal-remote libraries |
| `/ext/ibutton/` | Saved `.ibtn` 1-Wire keys |
| `/ext/badusb/` | Ducky `.txt` payloads (and `badusb/assets/` keyboard layouts) |
| `/ext/apps/` | Installed FAPs, organized by category (`apps/Sub-GHz`, `apps/Tools`, …) |
| `/ext/apps_data/` | Per-app persistent data/config (kept separate from the `.fap` binary) |
| `/ext/dolphin/` (or `/ext/asset_packs/` on Momentum) | Animations / asset packs |
| `/ext/music_player/` | `.fmf` ringtone/music files |

### "Dolphin" gamification
The on-screen dolphin is the device's pet/avatar and its core game loop:
- **XP / levels:** using real features (read sub-GHz, scan NFC, save an IR remote, etc.) grants XP.
  Stock firmware caps around **level 30** (Momentum extends the curve). Level gates which
  animations the current asset pack may play.
- **Mood / "butthurt":** a separate anger counter ("butthurt") rises when the device is idle/ignored
  and falls with use; it drives the pet's emotional state and which animations show. CFWs expose
  toggles (e.g. "unlock anims") and dolphin-level editors.
- It's cosmetic/engagement only — it does not gate radio or hardware functions.

### Why offload to companion MCUs
The STM32WB55RG is a low-power MCU, not an applications processor: one 64 MHz M4, 256 KB RAM, no
Wi-Fi, no fast ADC pipeline, no video out. So the design pattern is to keep the Flipper as the UI +
controller and bolt heavier silicon onto the GPIO header:

| Companion | Why it's needed | Typical use |
|---|---|---|
| **ESP32 / ESP32-S2** (Wi-Fi DevBoard, Marauder) | WB55 has no Wi-Fi; the M0+ only runs BLE | Wi-Fi recon/attacks (Marauder), Black Magic/DAPLink SWD bridge |
| **ESP32 (Multi-pass / EvilPortal)** | offload 2.4 GHz + captive portals | Deauth/portal tooling |
| **RP2040 (Video Game Module / VGM)** | WB55 has no DVI/HDMI and limited PIO | DVI video out, IMU/motion projects |
| **CC1101 external** | extends/cleans up sub-GHz front-end | wider/cleaner RF |

This keeps the core device cheap, low-power, and battery-friendly while making bandwidth-heavy
features opt-in add-ons. See [gpio-addons-current.md](hardware/gpio-addons-current.md) and
[gpio-addons-potential.md](hardware/gpio-addons-potential.md).

## Capability map (what you can actually *do*)
- **RF / wireless:** Sub-GHz remotes & sensors → [sub-ghz](capabilities/sub-ghz.md); rolling-code theory → [rolling-codes](theory/rolling-codes.md); 2.4 GHz/Wi-Fi/BLE via add-ons → [gpio-addons-current](hardware/gpio-addons-current.md).
- **Access control / cards:** HF NFC + LF 125 kHz + iButton → [nfc-rfid](capabilities/nfc-rfid.md), [ibutton](capabilities/ibutton.md).
- **IR control:** universal remote → [infrared](capabilities/infrared.md).
- **HID / host attacks:** BadUSB & BadBT → [badusb](capabilities/badusb.md).
- **Hardware hacking:** GPIO/UART/SPI/I²C, SWD debugging, sensors, logic analyzer → [hardware](hardware/README.md), [tinkering](topics/tinkering.md).
- **Security testing:** red-team framing & authorization → [security-pentest](topics/security-pentest.md), [legal-and-safety](legal-and-safety.md).

## Open questions / to research
- Exact NFC chipset depth (FeliCa/ISO15693 emulation limits) and which attacks are firmware-gated vs hardware-limited.
- LF RFID write matrix (T5577 cloning) — what's reliably writable vs read-only.
- Precise STM32WB flash partition map (bootloader / FUS / BLE stack / app firmware sizes) and IPCC channel mapping `(verify)`.
- Display controller part number and exact battery-management/fuel-gauge IC (for low-level notes).
- Whether the dolphin level cap and butthurt timing differ between Unleashed/Xtreme/Momentum.

## Sources
- Tech specs: https://docs.flipper.net/zero/development/hardware/tech-specs
- Schematics: https://docs.flipper.net/zero/development/hardware/schematic
- GPIO & modules: https://docs.flipper.net/zero/gpio-and-modules
- Developer docs (Furi/firmware): https://developer.flipper.net
- Pet dolphin: https://docs.flipper.net/zero/basics/dolphin
- SD card examples: https://github.com/flipperdevices/flipperzero-sd-card-examples
- STM32WB55 product page: https://www.st.com/en/microcontrollers-microprocessors/stm32wb55rg.html
