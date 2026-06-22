---
title: Firmware — Overview, Comparison & Flashing
domain: firmware
type: hub
status: detailed
summary: Firmware comparison matrix, Xtreme to Momentum history, flashing/recovery, and legal/stability risks.
hardware: []
use_cases: []
related: [firmware/official.md, firmware/unleashed.md, firmware/momentum.md, firmware/roguemaster.md, legal-and-safety.md]
tags: [firmware, custom-firmware, comparison, flashing, recovery, sub-ghz, xtreme, momentum]
last_verified: 2026-06-19
---

# Firmware — Overview, Comparison & Flashing

> **TL;DR —** Compares the four main Flipper firmwares (Official, Unleashed, Momentum, RogueMaster), covers how to choose, the Xtreme→Momentum history, flashing/recovery, and legal/stability risks.
> Part of the [Flipper Zero KB](../README.md).

## What "custom firmware" changes

Stock Flipper ships **Official Firmware (OFW)** from Flipper Devices. Custom firmwares
(CFW) are GPL-3.0 forks that **unlock/expose** features OFW withholds — chiefly **Sub-GHz
regional TX restrictions**, **rolling-code save/replay**, extra radio protocols, bundled
third-party apps, and deep UI customization.

- **Only one firmware runs at a time** — flashing a CFW replaces OFW entirely (reversible).
- **Flashing is fully reversible** and the **bootloader/DFU is untouched**, so a bad flash is a recoverable *soft* brick, not a dead device.
- CFWs **track OFW** (periodic rebases) and **don't add hardware capability** — they only surface what the STM32WB + CC1101 can already do.

## Comparison matrix

| Feature | Official (OFW) | Unleashed | Momentum | RogueMaster |
|---|---|---|---|---|
| **Base / lineage** | Upstream baseline | Oldest major fork of OFW | OFW + Unleashed; **continuation of Xtreme** | OFW + Unleashed + ex-Xtreme + community plugins |
| **Sub-GHz region unlock / restricted TX** | ❌ region-locked | ✅ unlocked, extended ranges | ✅ same as Unleashed | ✅ inherited from Unleashed |
| **Rolling-code & extra protocols** | ❌ no save/send | ✅ KeeLoq, FAAC SLH, BFT Mitto… | ✅ + weather/POCSAG/TPMS, GPS | ✅ + extra community decoders |
| **Preloaded apps/plugins** | Minimal (rest via catalog) | Curated, **stable** set | Large set + Bluetooth suite | **Largest** bundle |
| **UI customization** | Minimal | Light | **Asset Packs**, menu styles, RGB | Many animation packs |
| **JS / app catalog compat** | ✅ native JS + catalog | ✅ compatible | ✅ largest JS module set | ✅ + huge bundled FAPs |
| **Stability** | ★★★★★ | ★★★★☆ (most stable CFW) | ★★★★☆ | ★★★☆☆ (most crash-prone) |
| **Maintenance** | Active, ~monthly | Very active, near-daily dev | Active, periodic stable | Active, monthly stable |
| **Best for** | Beginners, stability | RF work, reliability | Max features + customization | Everything-bundled tinkerers |

> Latest at time of writing **(verify — drifts):** OFW **1.4.3** (2025-12-05) · Unleashed **unlshd-089** (2026-05-09) · Momentum **mntm-012** (2026-01-02) · RogueMaster rolling (commit ~2026-06-18).

**Rule of thumb:** Official if unsure → **Unleashed** for unlocked RF without bloat →
**Momentum** for features + customization with good stability → **RogueMaster** if you want
everything and tolerate instability.

## Xtreme → Momentum history (important for this device)

- **Xtreme** (`Flipper-XFW/Xtreme-Firmware`) was a leading, heavily-customizable CFW.
- It was **discontinued / archived on 2024-11-19** — no further updates.
- **Momentum (Next-Flip) is the official continuation** by the same core devs; it carries Xtreme's look/feel + Asset Packs forward on a current OFW base.

**If this device runs Xtreme:** it's frozen on a 2024-era base, missing ~18 months of
updates → **migrate to Momentum** (back up the SD card first; asset packs/settings concepts
carry over).
**If it runs Unleashed:** no urgent action — it's actively maintained and the most stable
CFW. Switch to Momentum only if you want the heavier UI customization / bundled Bluetooth
suite. **Diagnose which you're on:** boot splash or `Settings → About`; an `unlshd-###`
build = Unleashed, an archived/2024 build name = Xtreme.

## Flashing & switching

**Tools (any flashes OFW or CFW; all reversible):**
- **qFlipper** (desktop, USB) — channel select or "Install from file" (`.tgz`).
- **Flipper Lab** (web, https://lab.flipper.net, WebUSB/Chromium) — official; CFWs expose channels, and Unleashed/Momentum have their own web updaters.
- **Flipper mobile app** (BLE) — channel select + update.

**Back up the microSD first** — all dumps/captures/configs/apps live there; switching FW
can change app compatibility (RogueMaster recommends clearing `/ext/apps`).

**Reversibility & recovery:**
- Normal flashing writes only the firmware partition → re-flash Official anytime to "go back."
- A bad flash = **soft brick** (recoverable), rarely a dead device.
- **DFU recovery:** unplug USB, **hold BACK + OK (~30s)** to enter STM32 DFU (blank screen is normal), connect USB, click **REPAIR** in qFlipper. 2026 OFW also has a **Recovery Mode** ("Restore Firmware"). (Exact hold-times vary — verify against current docs.)

## Risks & legality (see also [legal-and-safety](../legal-and-safety.md))
- **Sub-GHz TX legality:** unlocked FW can transmit on bands/power **restricted in your region**; compliance is entirely on you. The OFW region-lock exists for this reason.
- **Warranty/support:** CFW is generally **not officially supported**; RMA may require reverting to OFW.
- **Bleeding-edge instability:** more bundled experimental apps = more crashes (RogueMaster most; dev builds of others). Prefer **stable release** channels for daily use.

## Open questions / to research
- Decide and record **which FW this device runs** and the chosen target (likely Momentum or stay-Unleashed).
- Concrete migration checklist (SD backup layout, settings/asset-pack carry-over).
- Per-FW NFC/RFID parser differences worth caring about.

## Sources
- Awesome Flipper firmware: https://awesome-flipper.com/firmware/ · Momentum: https://awesome-flipper.com/firmware/momentum/
- OFW: https://github.com/flipperdevices/flipperzero-firmware
- Unleashed: https://github.com/DarkFlippers/unleashed-firmware · https://flipperunleashed.com · https://web.unleashethe device.com
- Momentum: https://github.com/Next-Flip/Momentum-Firmware · https://momentum-fw.dev
- Xtreme (archived 2024-11-19): https://github.com/Flipper-XFW/Xtreme-Firmware
- RogueMaster: https://github.com/RogueMaster/flipperzero-firmware-wPlugins
- Firmware update / recovery: https://docs.flipper.net/zero/basics/firmware-update · .../firmware-recovery
- HackMag overview: https://hackmag.com/security/flipper-zero-firmwarez
