---
title: Migration Walkthrough — Xtreme → Momentum
domain: firmware
type: guide
status: detailed
summary: Step-by-step — back up SD, flash Momentum, restore, re-enable add-ons, verify (frontier Stage 0).
hardware: [flipper-internal, cc1101-ext, esp32-marauder]
use_cases: []
related: [firmware/momentum.md, my-setup.md, frontier-roadmap.md, resources/mcp-setup-claude-code.md, firmware/README.md]
tags: [migration, momentum, xtreme, flashing, sd-backup, recovery, stage-0]
last_verified: 2026-06-19
---

# Migration Walkthrough — Xtreme → Momentum

> **TL;DR —** Step-by-step to move this device off EOL **Xtreme `XFW-0053`** onto **Momentum**: back up the microSD → flash → restore asset pack → re-enable the CC1101 + Marauder → verify. Fully reversible; the flash does **not** wipe the SD.
> [firmware hub](README.md) · [Momentum](momentum.md) · [my rig](../my-setup.md) · [Stage 0 of the frontier roadmap](../frontier-roadmap.md). Part of the [KB](../README.md).

> **Status — ✅ Done on this rig (2026-06-19).** Migrated to Momentum `mntm-dev` (commit `8ed809fb` · API 87.1); SD verified intact; pre-flash backup at `~/flipper-backup-2026-06-19/the device-sd`. This doc stays as the reusable walkthrough — re-flashing, switching to the Release channel, or recovery. See [my-setup §2](../my-setup.md).

This is **Stage 0** of the [frontier-roadmap](../frontier-roadmap.md): a current, RPC-clean firmware is the foundation for everything (incl. AI control). Xtreme is archived (2024-11-19); Momentum is the same team's successor and keeps Asset Packs / look-and-feel.

## Before you start
- Mac + USB-C cable, charged Flipper, ~30 min.
- Pick a flash tool: **Momentum Web Updater** (Chromium, easiest) · **qFlipper** (`.tgz`) · **mobile app** (BLE).
- Confirm you're on Xtreme: **Settings → About** (or the boot splash).
- The firmware flash writes only the firmware partition — **your microSD data persists** — but back it up anyway (safety + app-compat can change).

## Step 1 — Back up the microSD (do not skip)
- **Option A (simplest):** power off → eject the microSD → insert in the Mac → copy the **entire card** to a dated folder (e.g. `~/flipper-backup-2026-06-19/`). Confirm the `/ext` tree copied: `subghz/ nfc/ lfrfid/ infrared/ ibutton/ badusb/ apps/ apps_data/ dolphin*/` (+ your asset pack).
- **Option B:** qFlipper → File manager → drag `/ext` to the Mac (no card removal; slower).
- **Option C (scripted):** [pyFlipper](https://github.com/wh00hw/pyFlipper) / `storage` over USB ([notable-apps-and-data](../resources/notable-apps-and-data.md)).
- ✅ **Verify the backup folder is non-empty** (has your saved `.sub`/`.nfc`/etc.) before continuing.

## Step 2 — Note what to restore
Current **asset pack** name + any custom settings (Sub-GHz freq list, PIN/lock-on-boot, device name). Screenshot `Settings` if unsure.

## Step 3 — Flash Momentum
**Web Updater (recommended):**
1. In **Chrome/Edge**, open the Momentum Web Updater (from https://momentum-fw.dev → Update). `(verify current URL)`
2. Connect the Flipper via USB and **quit qFlipper / close any Flipper Lab tab** (only one app can hold the port).
3. Pick the **Release** channel → Install/Update → grant the **WebUSB** prompt → wait ~5–10 min (the screen shows progress and reboots). **Don't unplug.**

**Alt — qFlipper:** download the latest `mntm-0xx` `.tgz` from momentum-fw.dev / GitHub → qFlipper → **Install from file** → pick the `.tgz`.
**Alt — mobile app:** select the Momentum channel → update over BLE.

## Step 4 — First boot + restore
- It boots Momentum; your SD data is intact.
- **Re-apply your asset pack** (Momentum Settings → Interface/Asset Pack).
- Check your apps launch; reinstall any FAPs that error from the catalog (Flipper Lab / mobile app).

## Step 5 — Re-enable your add-ons
- **CC1101 (433):** plug the board onto **GPIO pins 1-8** → `GPIO → 5V on GPIO → ON` → `Sub-GHz → Radio Settings → Module → External`. (See [my-setup §5](../my-setup.md).)
- **ESP32 Marauder:** reinstall the **WiFi Marauder** companion app from the catalog; confirm it talks to the board.

## Step 6 — Verify (Stage 0 done)
- `Settings → About` shows **`mntm-0xx`**.
- Quick functional checks: read an NFC tag · send an IR code · read your own LF fob — confirm nothing regressed.
- ✅ **You're frontier-ready** → proceed to [Stage 1: AI control setup](../resources/mcp-setup-claude-code.md).

## If something goes wrong (recovery)
- **Soft-brick / stuck:** **DFU** — unplug USB, hold **BACK + OK (~30 s)** (blank screen is normal), connect USB, qFlipper → **REPAIR**. 2026 OFW also has **Recovery Mode → "Restore Firmware."** (Hold-times vary — verify.)
- **Rollback:** re-flash Xtreme / OFW / Unleashed anytime; your **SD backup** restores all data. Nothing here is one-way.

## macOS notes
- qFlipper for macOS: https://flipper.net/pages/downloads. The Web Updater needs a **Chromium** browser (Safari WebUSB is limited).
- Only **one** host app can hold the serial port at a time — close others before flashing.

## Open questions / to research
- Confirm the current Momentum **Web Updater URL** + latest stable tag past `mntm-012` `(verify)`.
- Whether my Xtreme asset pack drops straight into Momentum's pack folder or needs reformatting `(verify)`.
- Post-migration: re-confirm external-CC1101 + WiFi-Marauder both work on the Momentum build.

## Sources
- Momentum: https://momentum-fw.dev · https://github.com/Next-Flip/Momentum-Firmware
- Firmware update / recovery (official): https://docs.flipper.net/zero/basics/firmware-update · .../firmware-recovery
- qFlipper / downloads: https://flipper.net/pages/downloads
