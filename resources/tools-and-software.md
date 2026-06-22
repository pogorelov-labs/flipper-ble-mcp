---
title: Tools & Software (Desktop / Web / Mobile)
domain: resources
type: resource-list
status: detailed
summary: qFlipper, Flipper Lab, flashers, and an SD-backup checklist
hardware: []
use_cases: []
related: [resources/best-github-repos.md, resources/learning-and-docs.md, firmware/README.md]
tags: [tools, qflipper, flipper-lab, flashing, backup, esp32, dev-tooling]
last_verified: 2026-06-19
---

# Tools & Software (Desktop / Web / Mobile)

> **TL;DR —** The apps to manage, flash, and build for the Flipper — qFlipper, Flipper Lab, mobile, per-CFW web updaters, ESP32 flashers, file/asset/dev tools — plus a microSD backup checklist to run before any firmware change.
> See [best repos](./best-github-repos.md) · [firmware](../firmware/README.md) · [learning & docs](./learning-and-docs.md). Part of the [KB](../README.md).

## Backup FIRST — microSD checklist (do this before flashing)
Flashing rarely wipes the SD, but a bad flash, a bootloop, or a wrong region setting can. Make a known-good copy before any firmware change.
1. Power off the Flipper; pop the **microSD** and put it in your computer (card reader).
2. **Copy the entire card** to a dated folder, e.g. `flipper-backup-2026-06-19/` — don't move, copy.
3. Especially confirm these survive: `subghz/`, `nfc/`, `infrared/`, `lfrfid/`, `ibutton/`, `badusb/`, `apps/`, `apps_data/`, and `*.keys` (esp. **`nfc/assets/*.nfc`** user dicts and any SecPlus/keeloq keys).
4. Separately export device **settings/dump** via qFlipper (Backup) so DFU repair can restore pairing/region.
5. Eject cleanly. Keep ≥1 backup off the card. Then flash.
6. After flashing, if assets look wrong, use qFlipper to **repair/restore** rather than re-flashing blindly.

## Core apps — what each is for
| Tool | URL | Purpose | OS |
|---|---|---|---|
| **qFlipper** | https://flipper.net/pages/downloads | Official desktop: update FW, file manager, **screen streaming + remote control**, settings backup, **DFU repair** of bricked/broken installs. Use for recovery and bulk file work. | Win / macOS / Linux (Flathub) |
| **Flipper Lab** | https://lab.flipper.net | Official web app: browse/install apps from the catalog and **web-flash firmware** over WebUSB. Fastest for app installs. | Chromium browser (Chrome/Edge) |
| **App Catalog** | https://lab.flipper.net/apps · https://catalog.flipperzero.one | Reviewed community apps (the source Flipper Lab + mobile app install from). | Web / in-app |
| **Flipper Mobile** (iOS/Android) | App Store / Google Play · https://flipper.net | BLE pairing + control, install apps **over Bluetooth**, file transfer, firmware update on the go, hub/news. Use when no PC handy. | iOS / Android |

**Picking one:** day-to-day app installs → **Flipper Lab** (or mobile over BLE). Firmware recovery, screen capture, large file moves → **qFlipper**. Custom-firmware-specific updates → the per-CFW web updaters below.

## Firmware-specific web updaters
| Updater | URL | Notes |
|---|---|---|
| **Unleashed** (web installer) | https://web.unleashethe device.com | Your CFW. Picks release/dev channel + extra-apps pack; WebUSB flash. Dev builds: https://dev.unleashethe device.com |
| **Momentum** | https://momentum-fw.dev | Xtreme successor; flash via site or Flipper Lab channel. Most customizable UX. |
| **RogueMaster** | https://flipper.roguemaster.org *(verify)* / via Flipper Lab | Kitchen-sink build; large download. Also flashable through Lab. |
| **OFW updates** | qFlipper / Flipper Lab | Stock channel for comparison/rollback. |

## ESP32 / backpack flashers
| Tool | URL | Purpose | OS |
|---|---|---|---|
| **FZEE Flasher** | https://fzeeflasher.com | Web flasher for Flipper Dev Board + many ESP32 variants; picks Marauder/GhostESP versions. Easiest. | Chromium (Web Serial) |
| **FZEasyMarauderFlash** | https://github.com/SkeletonMan03/FZEasyMarauderFlash | Python CLI to flash Marauder onto the WiFi Devboard / ESP32; cross-platform. | Win / macOS / Linux |
| **0xchocolate/flipperzero-esp-flasher** | https://github.com/0xchocolate/flipperzero-esp-flasher | On-Flipper FAP that flashes the attached ESP via the Flipper itself (no PC). | Flipper app |

## File generation / conversion
| Tool | URL | Purpose | OS |
|---|---|---|---|
| **Flipper Maker** | https://flippermaker.github.io | Generate `.sub` / `.ir` / NFC and other files in-browser. | Web |
| **flipper_toolbox** (evilpete) | https://github.com/evilpete/flipper_toolbox | Scripts to convert/generate signal files (Sub-GHz, IR, Pulse Plotter, etc.). | Python |
| **FlipperMfkey** (noproto) | https://github.com/noproto/FlipperMfkey | On-device MIFARE Classic key recovery → writes user dict (no PC). | Flipper app |
| **mfkey32v2** (equipter) | https://github.com/equipter/mfkey32v2 | Desktop: pull `.mfkey32.log`, compute keys, push to NFC user dict. | Python |

## Animation / asset tools
| Tool | URL | Purpose | OS |
|---|---|---|---|
| **FlipperAnimationManager** (Ooggle) | https://github.com/Ooggle/FlipperAnimationManager | GUI to build/preview/manage boot + idle animations and packs. | Win / Linux (Qt) |
| **Talking-Sasquach pack** | https://github.com/skizzophrenic/Talking-Sasquach | Ready-made animation assets + creation notes. | Assets |

## Dev tooling
| Tool | URL | Purpose | OS |
|---|---|---|---|
| **ufbt** | https://github.com/flipperdevices/flipperzero-ufbt | Micro build tool: scaffold, build, and deploy a single FAP fast. | pip (Win/macOS/Linux) |
| **Full SDK / fbt** | https://github.com/flipperdevices/flipperzero-firmware | Full firmware build for deep work / new protocols. | Win/macOS/Linux |

## Open questions / to research
- Confirm the current canonical RogueMaster web-updater URL (flagged *(verify)*).
- Verify Flipper Lab WebUSB still requires Chromium-only (Firefox WebUSB status).
- Decide a default personal flow: Unleashed web-updater for FW, Flipper Lab for apps, qFlipper for recovery — document any gotchas.
- Check whether the mobile app can now flash CFW directly, or only OFW.
- Note exact SD paths that hold cracked NFC keys so backups never miss them.

## Sources
- https://flipper.net/pages/downloads · https://docs.flipper.net/zero/qflipper · https://lab.flipper.net
- https://web.unleashethe device.com · https://momentum-fw.dev
- https://fzeeflasher.com · https://github.com/SkeletonMan03/FZEasyMarauderFlash
- https://flippermaker.github.io · https://github.com/Ooggle/FlipperAnimationManager · https://github.com/flipperdevices/flipperzero-ufbt
