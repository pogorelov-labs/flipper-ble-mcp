---
title: Infrared (IR)
domain: capabilities
type: reference
status: detailed
summary: Capture, store, and replay consumer IR; protocols, .ir format, universal remotes, and the Flipper-IRDB library.
hardware: [flipper-internal]
use_cases: [UC-01, UC-02, UC-03]
related: [capabilities/badusb.md, hardware/gpio-addons-current.md, resources/best-github-repos.md, legal-and-safety.md]
tags: [infrared, ir, nec, sirc, ir-format, universal-remote, irdb]
last_verified: 2026-06-19
---

# Infrared (IR)

> **TL;DR —** The Flipper captures, stores, and re-emits consumer IR remote signals (TVs, ACs, projectors, soundbars) via learn-one-button mode or a brute-force Universal Remote. Covers the IR hardware, the 13 parsed protocols vs RAW, the `.ir` file format, building a personal remote from Flipper-IRDB, and IR-blaster range.
> See [badusb.md](./badusb.md), [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md), [../resources/best-github-repos.md](../resources/best-github-repos.md). Part of the [KB](../README.md).

## What it is

The Flipper's IR module captures, stores, and re-emits consumer infrared remote signals (TVs, ACs, projectors, soundbars, LED strips, cameras). It is the safest, most universally-legal capability on the device: IR is line-of-sight, short-range, unlicensed, and identical to any learning remote you can buy. Two modes matter — **learn one button at a time** from an existing remote, and **Universal Remote** which brute-forces bundled code dictionaries to power off / change volume on unknown gear (the "TV-B-Gone" pattern, but multi-function).

## Hardware

| Part | Detail |
|---|---|
| **TX** | **3 transmitting IR LEDs** behind the top IR window; fired together for the carrier burst. Wide-ish beam, modest output (see Range). |
| **RX** | An **integrated IR receiver/demodulator** tuned for the standard **~38 kHz** carrier (typical consumer band). It outputs the *demodulated envelope*, so the Flipper sees mark/space timings, not the raw carrier — this is why learn mode reconstructs timings rather than sampling the LED directly. |
| **Carrier band** | 38 kHz is the sweet spot; many remotes use 36–40 kHz and still decode. Far-off carriers (e.g. 56 kHz Sky/B&O) may capture poorly via the demodulator (verify per device). |
| **GPIO out** | The IR signal and **5 V** can be routed to **GPIO** to drive an external high-output IR transmitter ("IR backpack" / blaster) — works with stock firmware, no special app. |

> Demodulating RX = great for *learning* normal remotes, but it cannot see the carrier frequency itself. The Flipper assumes 38 kHz when saving learned signals unless you know better and edit the `.ir`.

## Protocols Flipper decodes (parsed)

Recognized signals are stored compactly as **protocol + address + command**. Anything not recognized falls back to **RAW** timings. The current firmware decoder set (per the firmware `InfraredFileFormats.md` and the `ir` CLI command):

| Family | Protocols | Notes |
|---|---|---|
| **NEC** | `NEC`, `NECext`, `NEC42`, `NEC42ext` | Most common consumer family (TVs, audio, generic). `ext`/`42` are longer-address variants. |
| **Sony SIRC** | `SIRC` (12-bit), `SIRC15` (15-bit), `SIRC20` (20-bit) | Sony's 3 bit-length variants. |
| **Philips RC** | `RC5`, `RC5X`, `RC6` | Bi-phase (Manchester) toggle-bit protocols. |
| **Samsung** | `Samsung32` | Samsung TVs/AV. |
| **Panasonic/Kaseikyo** | `Kaseikyo` | Panasonic and the broader Kaseikyo/Japan AV alliance. |
| **RCA** | `RCA` | Legacy RCA AV gear. |

That's **13 named protocols**. AC remotes are the notable gap: many air-conditioners send long stateful frames (temp + mode + fan in one burst) that aren't in the parsed set — these are usually captured/stored as **RAW**, and full IRDB AC files exist precisely because each button is a distinct long frame. Flag any "my AC didn't decode" as expected, not broken `(verify exact AC coverage per unit)`.

## The `.ir` file format

Plain-text, human-editable, lives in `/ext/infrared/` on the SD. One file = one "remote" (many buttons). Buttons are separated by `#` comment lines.

**Header (every file):**
```
Filetype: IR signals file
Version: 1
```

**Parsed entry** (recognized protocol — compact, portable):

| Field | Example | Meaning |
|---|---|---|
| `name` | `Power` | Button label shown in the UI |
| `type` | `parsed` | Stored as decoded protocol |
| `protocol` | `NECext` | One of the 13 names above |
| `address` | `EE 87 00 00` | **4 bytes**, hex, space-separated, LSB-first padding |
| `command` | `5D A0 00 00` | **4 bytes**, hex (only the protocol's used bits matter) |

**RAW entry** (unrecognized — verbatim timing capture):

| Field | Example | Meaning |
|---|---|---|
| `name` | `Power` | Button label |
| `type` | `raw` | Stored as raw timings |
| `frequency` | `38000` | Carrier in Hz (uint32; almost always 38000) |
| `duty_cycle` | `0.330000` | Carrier duty (float; typically 0.33) |
| `data` | `9000 4500 560 560 …` | Mark/space durations in **microseconds**, space-separated. First value is always a **HIGH** (mark). **Max 1024 timings.** |

Because parsed entries are tiny and device-agnostic, prefer them; RAW is faithful but bulky and locked to the captured carrier. You can freely **mix parsed and RAW buttons** in one file, rename buttons, and merge files by concatenating button blocks under one header — this is exactly how you assemble a personal universal remote.

## Universal Remote feature

Stock firmware ships bundled universal databases (`tv.ir`, `audio.ir`, `ac.ir`, `projector.ir` under the app's assets). Selecting e.g. **Power** makes the Flipper **iterate the whole dictionary**, transmitting that function's code for hundreds of known models back-to-back — a brute-force sweep until something in the room responds. CFW (Unleashed/Xtreme) typically expands these dictionaries and adds extra categories. It's the right tool when you don't know the brand; it is slower and noisier than a single learned button.

## Building a personal universal remote from Flipper-IRDB

[Flipper-IRDB](https://github.com/logickworkshop/Flipper-IRDB) (CC0-licensed) is the canonical community `.ir` library, organized **Device Type → Brand → Series**, with 50+ device-type folders (`TVs`, `ACs`, `Audio_and_Video_Receivers`, `Streaming_Devices`, `DVD_Players`, `Projectors`, `LED_Lighting`, …) and a `Brand_Model.ir` naming convention plus standardized button names (`Power`, `Vol_up`, `Vol_dn`, `Mute`, `Ch_next`, navigation).

Workflow:
1. Pull the relevant `Brand_Model.ir` files from IRDB onto the SD (`/ext/infrared/`) via qFlipper, the mobile app, or direct card copy.
2. Test each button against your gear; keep the ones that work.
3. **Merge** the good buttons into one curated `home.ir` (copy button blocks under a single header), renaming for clarity.
4. Prefer **parsed** entries; only keep RAW where the device needs it (e.g. AC state frames).
5. Optionally seed missing buttons via **learn mode** and contribute corrections back to IRDB.

See [../resources/best-github-repos.md](../resources/best-github-repos.md) for the wider IR/firmware repo set.

## Range limits + when an IR backpack helps

| Setup | Practical range | When to use |
|---|---|---|
| **Stock 3-LED** | ~3–5 m, needs reasonable aim | Same-room use, replacing a lost remote, AV automation |
| **External IR blaster** (Rabbit-Labs IR Blaster, 7 LEDs) | "up to ~100 m" line-of-sight claim, much wider cone `(vendor figure, verify)` | Big rooms, ceiling projectors, signage, bouncing off walls |
| **Masta-Blasta** (12 LEDs) | Even higher output/cone `(vendor figure)` | Max range / awkward angles |

A backpack helps because stock output is intentionally low-power; it draws **5 V from GPIO** (enable via GPIO → 5 V → ON) and is driven by the same IR signal — no firmware change. It does **not** improve *receiving*/learning, only transmit reach. See [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md).

## Legitimate uses

- Replace a lost/broken remote; consolidate many remotes into one curated file.
- Home-theatre and meeting-room automation (power sequences, input switching).
- Bench/repair work and reverse-engineering your **own** AV gear's protocol.
- Authorized facilities testing (e.g. confirming a projector/TV isn't trivially power-cycled by a stranger) — IR is inherently low-risk but still: only point it at equipment you own or are authorized to control. See [../legal-and-safety.md](../legal-and-safety.md).

## Open questions / to research

- Exact AC remote coverage: which (if any) AC protocols ever decode as *parsed* vs always RAW; behaviour of CFW AC universal DB `(verify)`.
- Real-world capture reliability for non-38 kHz carriers (36 kHz RC5, 40 kHz, 56 kHz B&O) through the demodulating RX `(verify)`.
- Whether CFW exposes a true raw (non-demodulated) capture mode or carrier-frequency detection.
- Measured stock-LED range vs the 7-LED / 12-LED blasters under identical conditions (vendor numbers are optimistic).
- Best tooling to bulk-convert RAW captures to parsed (and to dedupe/merge large IRDB pulls).

## Sources

- Flipper docs — Infrared: https://docs.flipper.net/zero/infrared
- Firmware `.ir` file format spec: https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/InfraredFileFormats.md
- Developer docs (file format): https://developer.flipper.net/flipperzero/doxygen/infrared_file_format.html
- Flipper-IRDB community DB: https://github.com/logickworkshop/Flipper-IRDB
- Jamison Derek IR tutorial wiki: https://github.com/jamisonderek/flipper-zero-tutorials/wiki/Infrared
- Rabbit-Labs IR Blaster (7-LED) / Masta-Blasta (12-LED): https://rabbit-labs.com/product/the-original-ir-blaster-compatible-with-flipper-zero-by-rabbit-labs-3/
