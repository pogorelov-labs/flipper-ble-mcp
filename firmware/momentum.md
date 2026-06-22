---
title: Momentum Firmware — Next-Flip (successor to Xtreme)
domain: firmware
type: reference
status: detailed
summary: Feature-rich Xtreme successor — capabilities by domain plus an honest is-it-the-best verdict.
hardware: []
use_cases: []
related: [firmware/README.md, firmware/unleashed.md, firmware/roguemaster.md, my-setup.md, legal-and-safety.md]
tags: [firmware, momentum, xtreme, custom-firmware, asset-packs, bluetooth, sub-ghz, customization]
last_verified: 2026-06-19
---

# Momentum Firmware — Next-Flip (successor to Xtreme)

> **TL;DR —** Feature-rich, customizable, stable all-rounder built on Unleashed's unlocks — the direct continuation of the discontinued Xtreme, with Asset Packs, the most complete Bluetooth suite, the largest JS module set, and an honest "is it the best?" verdict.
> See the [firmware overview & matrix](README.md) · siblings [unleashed](unleashed.md), [roguemaster](roguemaster.md). For my rig: [my-setup.md](../my-setup.md). Part of the [KB](../README.md).
> **The migration target for this device (currently on the discontinued Xtreme).**

- **Repo:** https://github.com/Next-Flip/Momentum-Firmware · **Site:** https://momentum-fw.dev · **Wiki:** https://momentum-fw.dev/wiki · **Web updater:** https://momentum-fw.dev/update
- **Maintainer:** Next-Flip — the **original Xtreme developers**. Actively maintained (stable ~every few months + frequent devbuilds). Discord + Ko-fi/PayPal.
- **Lineage:** Official Firmware **+ most Unleashed features**, then Momentum's own additions. A **direct continuation of Xtreme**.
- **Philosophy (its 3 pillars):** **Feature-rich · Stable · Customizable** — it deliberately balances all three rather than maximizing any one.

---

## Capabilities by domain

### Sub-GHz / RF
- **Region-unlocked TX + extended ranges:** ~**281–361, 378–481, 749–962 MHz** _(TX on restricted bands may be illegal where you are — [legal-and-safety](../legal-and-safety.md))_.
- **More protocols + decoders:** weather stations, **POCSAG** pager, **TPMS** tire sensors.
- **Rolling-code protocol support** (capture/save/replay of more schemes, e.g. KeeLoq/FAAC SLH). ⚠️ This adds protocol *coverage* — it does **not** defeat properly-implemented rolling-code security; ignore "breaks every rolling code" hype. See [theory/rolling-codes.md](../theory/rolling-codes.md).
- **External CC1101 module** support, **frequency analyzer**, **GPS "SubDriving"** (geotag captures), duplicate-detection/ignore, autosave + history. (Directly relevant to my 433 CC1101 board — [my-setup.md](../my-setup.md).)

### NFC / RFID
- **NFC Type 4 / NTAG4xx / DESFire NDEF** support, enhanced parsers, **EMV** card read (public info), and an **NFC Maker** app for crafting tags.

### Infrared
- Full universal-remote + learn/replay (shared OFW base); see [capabilities/infrared.md](../capabilities/infrared.md).

### Bluetooth / BadUSB ("most complete Bluetooth suite")
- **Bad-KB / Bad-Keyboard:** keystroke injection over **USB and BLE**, with spoofing of MAC/display-name (BLE) and manufacturer/product/**VID/PID** (USB).
- **BLE Spam** (nearby-device prank/advertising) and **FindMy Flipper** (Apple FindMy/AirTag-style tracking/emulation).

### Customization / UI (its signature strength)
- **Asset Packs** — swap animations/icons/fonts on-device, no recompile.
- **8 main-menu styles**, **control center** with quick toggles, **RGB backlight + rainbow**, VGM color options.
- **Advanced file browser/manager** (cut/copy/paste, **search**, sorting), **keybind remapping**, extended keyboard with cursor movement, improved error messages (show source paths).

### Development / automation
- **Largest JavaScript module set** (UsbDisk/mass-storage, Storage, GUI, BLE, SubGHz, i2c/spi, …) — build workflows/scripts **without C**. See [topics/tinkering.md](../topics/tinkering.md).

### Management & security
- **Momentum Settings** app — central on-device config (Interface / Protocols / Misc).
- **~183 preinstalled external apps** (as of Apr 2025) _(verify current count)_; **app-catalog compatible** (Flipper Lab apps + WiFi Marauder etc. install fine).
- Security: **lock-on-boot**, **reset-on-false-PIN**.

## Stability & install
- **Stable + feature-rich** — more polished than RogueMaster; prefer stable releases over devbuilds for daily use.
- **Install:** Momentum [web updater](https://momentum-fw.dev/update), Flipper Lab/mobile app, or qFlipper `.tgz`. Reversible; back up the SD first ([firmware/README.md](README.md)).

---

## Is Momentum the best? (honest verdict)

**There is no single "best" — it depends on your priority:**

| If your top priority is… | Best pick | Why |
|---|---|---|
| Stability + official support/warranty | **Official** | QA'd, no unlocks, sanctioned |
| Lean, rock-solid RF/Sub-GHz, minimal UI | **[Unleashed](unleashed.md)** | The RF-purist base; least bloat, very stable |
| **Most features + deep customization, still stable (all-rounder)** | **Momentum** | The do-everything daily driver |
| Max bundled apps/games, tolerant of crashes | **[RogueMaster](roguemaster.md)** | Largest pile, least stable |

**Momentum is the best *all-rounder*** and the most popular "everything + nice UI" choice — but note:
- Its **RF capability ≈ Unleashed** (it's built on Unleashed's unlocks). You don't gain Sub-GHz *power/range* vs Unleashed — you gain **UI, customization, Bluetooth suite, JS, and apps**. It's slightly heavier in return.
- For **pure stability**, Official/Unleashed have a small edge.

**Verdict for THIS rig → yes, Momentum is the best fit:**
1. **Direct Xtreme successor** — your familiar UI + Asset Packs carry over; it's the intended upgrade path off the EOL Xtreme.
2. **Full RF unlocks + external-CC1101 support + extended ranges** — covers your 433 SMA board ([my-setup.md](../my-setup.md)).
3. **App-catalog compatible** — your **WiFi Marauder** app installs and works.
4. **Most customization** + the Momentum Settings app — matches what you had on Xtreme.

The only reason to pick **Unleashed** instead would be wanting a leaner, maximally-stable RF-only tool and not caring about UI/customization. Coming from Xtreme, **Momentum** is the natural, best choice.

## Migration note (from Xtreme)
Xtreme is archived (2024-11-19), frozen on a 2024 OFW base. Back up the SD → flash Momentum → re-apply an asset pack → re-enable add-ons (Sub-GHz **Module → External**, reinstall WiFi Marauder). Most settings concepts carry over. Full checklist in [my-setup.md](../my-setup.md).

## Open questions / to research
- Confirm latest stable past mntm-012 and any new capabilities since Dec 2025.
- Momentum-specific apps/JS modules worth using for my Sub-GHz + Wi-Fi workflows.
- Any Momentum quirks with my external CC1101 / Marauder vs Unleashed.

## Sources
- https://momentum-fw.dev · https://momentum-fw.dev/wiki · https://github.com/Next-Flip/Momentum-Firmware
- mntm-012 writeup: https://secburg.com/posts/flipper-momentum-012-released/
- Comparison: https://awesome-flipper.com/firmware/ · https://awesome-flipper.com/firmware/momentum/
- Pentest firmware pick: https://www.spartanssec.com/post/flipper-zero-choosing-the-best-firmware-for-pentesting
