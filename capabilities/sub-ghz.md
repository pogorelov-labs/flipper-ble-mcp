---
title: Sub-GHz — Detailed Reference
domain: capabilities
type: reference
status: detailed
summary: CC1101 sub-1-GHz radio — bands, modulation/presets, on-device workflows, .sub format, protocol decoders.
hardware: [flipper-internal, cc1101-ext]
use_cases: [UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10, UC-11, UC-12]
related: [theory/rolling-codes.md, capabilities/nfc-rfid.md, hardware/gpio-addons-current.md, hardware/README.md, legal-and-safety.md]
tags: [sub-ghz, cc1101, ook, fsk, rolling-code, sub-format, frequency-analyzer]
last_verified: 2026-06-19
---

# Sub-GHz — Detailed Reference

> **TL;DR —** The Flipper's CC1101 sub-1-GHz radio for receiving, decoding, storing, and re-transmitting short-burst signals from gate/garage remotes, RF sensors, TPMS, and pagers. Covers bands, modulation presets, on-device workflows (Read/Read RAW/Frequency Analyzer/brute-force), the `.sub` file format, the decoder roster, and the fixed-vs-rolling-code distinction.
> Rolling-code security lives in [theory/rolling-codes.md](../theory/rolling-codes.md). Hardware: [hardware/README.md](../hardware/README.md), [hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md). Legality: [legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md).

The Sub-GHz subsystem is the Flipper's general-purpose **sub-1-GHz digital radio**: receive, decode, store, generate, and re-transmit the short-burst signals used by gate/garage remotes, RF sensors, barriers, doorbells, TPMS, weather stations, and pagers. Everything below is for transmitters **you own or are authorized to test**; TX on licensed/ISM bands is regulated — see [legal-and-safety.md](../legal-and-safety.md).

## The radio: TI CC1101
The Flipper uses a **Texas Instruments CC1101** transceiver on the main board, wired to a 433-MHz-tuned PCB/whip antenna. The CC1101 is a flexible OOK/FSK chip; the Flipper firmware drives it through `furi_hal_subghz` and exposes a curated subset of its register space as **presets**.

| CC1101 parameter | Hardware range (datasheet) | What it does | Flipper exposure |
|---|---|---|---|
| **Carrier frequency** | 300–348 / 387–464 / 779–928 MHz (3 tuned bands) | Center of TX/RX | Chosen per signal; OFW enforces a regional allow-list |
| **Modulation** | ASK/OOK, 2-FSK, 4-FSK, GFSK, MSK | How bits map to RF | Picked via **preset** (OOK or 2-FSK) |
| **Deviation** | ~1.5–381 kHz | For FSK: how far the two tones sit above/below carrier | Fixed by preset (238 kHz / 476 kHz presets) |
| **RX bandwidth** | ~58–812 kHz | Width of the RX filter (±BW/2 around carrier) | Fixed by preset (270 kHz / 650 kHz) |
| **Data rate** | 0.6–500 kBaud | Symbol rate the demodulator expects | Fixed by preset; custom presets can override |

Key intuitions (per the [TI CC1101 datasheet](https://www.ti.com/lit/ds/symlink/cc1101.pdf) and [community notes](https://github.com/jamisonderek/flipper-zero-tutorials/wiki/Sub-GHz)):
- **OOK/ASK** = "carrier on / carrier off." Used by the vast majority of garage/gate remotes and cheap sensors. The number after the preset (270/650) is the **RX bandwidth in kHz** — wider tolerates frequency drift and off-tune transmitters; narrower rejects more noise.
- **2-FSK** = data ride on two tones separated by the **deviation**. For FSK, getting deviation right matters almost as much as frequency: a receiver tuned to expect ±238 kHz won't lock if you re-transmit with the wrong deviation. Modulation index (2·deviation / data-rate) should stay **≥ 0.5**.
- The built-in standard UI does **not** expose arbitrary bandwidth/deviation/data-rate sliders; you change them by choosing a different preset or by authoring a **Custom preset** (`Custom_preset_module` + `Custom_preset_data` register dump) in the `.sub` file.

### Built-in presets (the "Modulation" menu)
A "preset" is a packaged CC1101 register configuration (modulation + deviation + bandwidth + data rate + AGC/decision-boundary). The four stock presets ([firmware file-format doc](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/SubGhzFileFormats.md)):

| Preset string | Modulation | RX bandwidth | Typical use |
|---|---|---|---|
| `FuriHalSubGhzPresetOok270Async` | ASK/OOK | 270 kHz | Narrow-band OOK; cleaner in noisy RF |
| `FuriHalSubGhzPresetOok650Async` | ASK/OOK | 650 kHz | **Default for most remotes**; tolerates drift |
| `FuriHalSubGhzPreset2FSKDev238Async` | 2-FSK | 238 kHz dev | Many car fobs / FSK telemetry |
| `FuriHalSubGhzPreset2FSKDev476Async` | 2-FSK | 476 kHz dev | Wider-deviation FSK devices |
| `FuriHalSubGhzPresetCustom` | per register dump | per dump | Hand-tuned (e.g., POCSAG, oddball data rates) |

## Frequency bands and common spot frequencies
| Band | Region / notes | Common spot frequencies |
|---|---|---|
| 300–348 MHz | Garage/gate remotes, some sensors | **315 MHz** (North America), 330/345 |
| 387–464 MHz | Europe/Asia remotes, sensors, TPMS | **433.92 MHz** (the global workhorse), 434.42, 418 |
| 779–928 MHz | Newer remotes, IoT, pagers, some TPMS | **868 MHz** (EU SRD), **915 MHz** (US ISM), 925 |

- **315 MHz** dominates North-American garage/car gear; **433.92 MHz** is the worldwide default for remotes and sensors; **868 MHz** (EU) and **915 MHz** (US) carry newer remotes and IoT.
- **Regional locks:** stock/Official FW ships a region-aware TX allow-list (e.g., it will refuse to *transmit* on 868 in a US region profile). Unleashed/Xtreme CFW typically **unlock the full hardware range and remove TX restrictions** — convenient for lab work, but the legal duty to only transmit where/what you're permitted is entirely on the operator ([legal-and-safety.md](../legal-and-safety.md)).

### Antenna, range, and external modules
- Internal range is roughly **10–50 m line-of-sight**, very dependent on the target's receiver sensitivity and environment. The internal antenna is optimized for ~433 MHz, so 315/868/915 perform worse internally.
- **External CC1101 backpacks** (e.g., NRF24+CC1101 boards, or commercial add-ons) connect over the GPIO/SPI header and can add a tuned antenna and an LNA/PA for materially better range and band-specific performance. See [hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md). Higher TX power raises the legal stakes.

## On-device workflows (precise)
| Workflow | What it actually does | When to use | Output |
|---|---|---|---|
| **Read** | Listens on the chosen freq/preset and runs **protocol decoders**; if a known protocol matches, shows vendor + decoded **Key/Bit/counter** | You expect a supported protocol and want a clean, editable capture | `Flipper SubGhz Key File` (`.sub`) |
| **Read RAW** | Records the **raw on/off timing waveform** (µs durations) with denoising; understands nothing about the protocol | Unknown/unsupported protocol, or decode fails | `Flipper SubGhz RAW File` (`.sub`) |
| **Frequency Analyzer** | Sweeps available frequencies and reports the one with the **highest RSSI** (typically > -90 dBm threshold) while you hold the target's button | You don't know the transmit frequency | A frequency to plug into Read/Read RAW (CFW adds protocol naming) |
| **Add Manually** | Generates a signal for a **known static protocol** by entering parameters — no capture needed | You know the protocol/key and want to synthesize it | `.sub` Key File |
| **Saved → Emulate/Send** | Re-transmits a stored `.sub` | Replay your own captured/synthesized signal | RF transmission |
| **Brute-force** (CFW/app, e.g. *SubGHz Bruteforcer*) | Plays a pre-generated `.sub` that walks an **entire small fixed-code space**, often via a **de Bruijn sequence** so adjacent codes overlap and the sweep is shorter | Only meaningful for **small fixed-code** systems you own | Sequential TX |

Notes:
- **Read vs Read RAW:** Read gives you a *semantic* capture (you can edit the counter/button, regenerate, brute a field) and is required for any "understanding." Read RAW is a dumb tape recorder — it replays the waveform but can't adapt it.
- **Frequency Analyzer** measures signal strength, not protocol; it's the first step when a remote's frequency is unmarked. CFW builds (Unleashed/Xtreme/Momentum) add live protocol labelling + RSSI bars.
- **Brute-force reality:** a **de Bruijn** sequence lets you emit every N-bit codeword in one continuous stream instead of replaying each independently, cutting time roughly N-fold. Even so it's only practical for tiny **fixed-code** spaces (e.g., 8–12-bit dip-switch remotes ≈ hundreds–thousands of codes). It is **useless against rolling codes** (the space is effectively the cipher), and many jurisdictions treat sweeping someone else's receiver as unauthorized access. Tooling: [flipperzero-bruteforce](https://github.com/tobiabocchi/flipperzero-bruteforce).

## Protocols the firmware actually decodes
Flipper splits vendors into two classes ([official supported-vendors list](https://docs.flipper.net/zero/sub-ghz/supported-vendors)):
- **Unlocked (static / not encrypted):** decode + **save** + replay.
- **Locked (dynamic / encrypted, i.e. rolling-code):** Flipper can **decode and display** the signal, but **Save/Emulate is deliberately disabled** so it can't be used as a working clone. This is a firmware policy choice, not a hardware limit.

| Class | Representative families Flipper decodes |
|---|---|
| **Unlocked / fixed-code (save+replay)** | **Princeton** (SC5262-style, and Princeton-based vendors: Bytec, GSN, Tantos Proteus), **CAME** (12/24-bit), **NICE FLO** (12/24-bit), **NICE One**, **Holtek** / **Holtek HT12X**, **Linear** / **Linear Delta-3** / **Linear MegaCode**, **Chamberlain/Liftmaster** (7/8/9-code dip variants), **Hörmann HSM**, **Marantec**, **Magellan**, **Honeywell WBD**, **Intertechno V3**, **SMC5326**, **Clemsa**, **Doitrand**, **Dooya**, **Prastel**, **Tedsen**, **Phoenix V2**, **Scher-Khan Magic Code (51-bit)**, Legrand, Roger, Nero Radio/Sketch, Gate-TX |
| **Locked / rolling-code (decode-only)** | **KeeLoq** variants and many KeeLoq-based gates (DoorHan, AN-Motors, NICE **Flor-S**/Smilo/MHouse, Alutech AT-4N, Beninca, Allmatic, Genius, Gibidi, etc.), **CAME Atomo/Twin/Space**, **FAAC SLH / FAAC RC / FAAC XT**, **Somfy Telis RTS** & **Somfy Keytis RTS**, **Chamberlain/Security+** (pre-/post-2004), **Stilmatic HCS101**, **Star-Line**, Sommer, Novoferm, Ecostar, Normstahl |

> The split, and *why* the locked ones don't yield a working clone, is the entire subject of [theory/rolling-codes.md](../theory/rolling-codes.md). Short version: rolling codes change every press, so a saved capture is stale — the security working as designed, not a Flipper defect.

### Sensor / one-way decoders (read-only telemetry, mostly via apps)
These are receive-and-display, not access-control. Stock has some; full coverage is via CFW apps:
- **TPMS** — tire-pressure sensors (Schrader, Toyota, Citroën/Renault, etc.); decode pressure/temperature/ID. Useful for diagnosing **your own** vehicle's sensors.
- **Weather stations** — many 433/868 outdoor sensor protocols (temp/humidity/wind/rain).
- **POCSAG** — pager protocol decoder (often needs a Custom 2-FSK/NRZ preset and the right data rate). Listening to pager traffic may be **legally restricted** in your country regardless of technical feasibility.

## The `.sub` file format
`.sub` files are flat key/value text. Two shapes ([firmware doc](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/SubGhzFileFormats.md)):

**RAW file** (waveform tape):
```
Filetype: Flipper SubGhz RAW File
Version: 1
Frequency: 433920000          # Hz
Preset: FuriHalSubGhzPresetOok650Async
Protocol: RAW                 # literally "RAW"
RAW_Data: 29262 361 -68 2635 -66 24113 ...   # µs timings
```
- **RAW_Data** = signed durations in **microseconds**: positive = carrier ON, negative = OFF; values must be non-zero, **start positive**, and **alternate sign**; up to **512 values per line** (multiple `RAW_Data:` lines continue the stream).

**Protocol / Key file** (decoded, editable):
```
Filetype: Flipper SubGhz Key File
Version: 1
Frequency: 433920000
Preset: FuriHalSubGhzPresetOok650Async
Protocol: Princeton
Bit: 24                       # payload length in bits
Key: 00 00 00 00 00 95 D5 D4  # payload (hex, MSB-padded to 8 bytes)
TE: 400                       # quantization interval (µs), protocol-specific
```
| Field | Meaning |
|---|---|
| `Filetype` | `... RAW File` vs `... Key File` selects the parser |
| `Frequency` | carrier in Hz |
| `Preset` | CC1101 config (see preset table); `...Custom` adds `Custom_preset_module` + `Custom_preset_data` |
| `Protocol` | `RAW`, or a decoder name (Princeton, CAME, NICE FLO, KeeLoq, …) |
| `Bit` | payload bit length (e.g., 12/24/64) |
| `Key` | the decoded payload as space-separated hex bytes |
| `TE` | base timing/quantization unit for OOK protocols (µs) |
| (rolling-code extras) | KeeLoq-class files may carry `Sn` (serial), `Cnt`/counter, and manufacturer-key references — but **locked vendors are decode-only**, so a fully usable next-code can't be minted from a stock capture |

Because Key files are plain text, you can **edit fields and regenerate** (e.g., change a dip-switch field on a fixed-code gate you own), then test via Saved → Send. RAW files can be hand-authored or scripted (the brute-force tooling generates RAW sweeps).

## Fixed vs rolling — the one distinction that explains most outcomes
- **Fixed-code** (older gates, cheap remotes, most sensors): **same code every press** → capture + replay works; small spaces are brute-forceable.
- **Rolling-code** (KeeLoq, modern fobs, FAAC SLH, BFT, Nice Smilo/Flor-S, Somfy RTS, Security+): **code changes each press** via counter + crypto → a naive replay **fails by design**. Full mechanics, attack classes, and why "it didn't work" usually means the security is fine: **[theory/rolling-codes.md](../theory/rolling-codes.md)**. RFID/NFC access control is a separate stack: [capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md).

## Read-app settings reference + what's on 433 (survey)
*The Sub-GHz **Read** settings menu (Momentum/Unleashed labels — `(verify)` exact wording per build), with values for a general "what's on the band" survey. Verified on the rig's external CC1101 (433) 2026-06-19.*

| Setting | What it does | General-survey value |
|---|---|---|
| **Frequency** | listen frequency | **433.92 MHz** (most populated; the external 433 board's band) |
| **Modulation** (preset) | demod scheme | **AM650**; try **AM270 / FM238** if a signal won't decode |
| **Hopping (RSSI)** | auto-cycle preset freqs, lock to strongest RSSI | **OFF** — an *internal-radio* convenience; with an external module **fix the frequency** |
| **Bin RAW** | also capture non-decoding signals as raw | **OFF** to decode known protocols; **ON** to grab unknown signals to replay |
| **Repeater** | **re-transmits** received signals (TX!) | **OFF** for passive listening |
| **Remove duplicates** | collapse repeated identical frames (held button) | **ON** (clean list) |
| **Delete old signals** | auto-trim the history | **ON** (tidy) — OFF for a full log |
| **Autosave** | save every received signal to SD | **OFF** casual · **ON** to log everything |
| **Ignore Starline / car-alarm (RB2)** | filter that (chatty) protocol out | OFF for a full survey; ON to de-clutter |
| **Ignore alarms** | filter car-alarm protocols | "" |
| **Ignore sensors** | filter weather/TPMS sensor chatter | "" |
| **Ignore Princeton** | filter PT2262 (very common/noisy) | **OFF** to see all; **ON** when hunting (cuts the most clutter) |
| **Ignore Nice Flor-S / Nice One** | filter Nice rolling remotes | OFF unless a nearby one spams the list |
| **Sound** | beep on each received signal | **ON** (audible feedback) — or OFF |

**Quick survey preset:** `433.92 · AM650 · Hopping OFF · Bin RAW OFF · Repeater OFF · Remove-dupes ON · Sound ON · all Ignore-filters OFF`. If a signal won't decode → flip **Bin RAW ON**, or try **AM270/FM**.

### What the external 433 board catches (vs the internal radio)
The rig's **E07-400MM10S is 433-band only (~410–450 MHz)** → on `Module: External` it catches **433/434 MHz** devices. For **315 MHz** (US fobs/garages/TPMS) or **868/915 MHz** (EU SRD / US ISM), switch `Module: Internal`.

| 433.92 MHz device | fixed / rolling |
|---|---|
| Gate/garage remotes (CAME, NICE, FAAC, BFT, Hörmann, Sommer) | mix — **rolling won't replay** ([rolling-codes](../theory/rolling-codes.md)) |
| Wireless doorbells · RF sockets/plugs · LED & fan controllers | mostly **fixed** (PT2262 / EV1527) — replayable |
| Alarm sensors (door/window contacts, PIR) | some fixed, some encoded |
| Weather-station sensors · TPMS (EU) | one-way telemetry (decode-only) |
| Car key fobs (EU/Asia 433) | **rolling → capture won't replay** |
| Blind/shade motors · garage tilt sensors · POCSAG coasters | varies |

*(315 MHz = US car fobs/garages/TPMS · 868 MHz EU / 915 MHz US = newer alarms, Somfy io, LoRa, weather — all **internal-radio-only** on this rig.)*

## Legitimate uses
- Read/replay **your own** garage, gate, barrier, or doorbell; range-test your own remotes; clone a spare for a system you own (fixed-code).
- Decode **your own** TPMS, weather, or sensor telemetry for diagnostics.
- Learn RF modulation/encoding hands-on; build CTF or classroom exercises; characterize a device you're authorized to assess.
- Blue-team: confirm whether a deployment uses fixed vs rolling codes and demonstrate the replay risk of legacy hardware to justify upgrades.

Legality and ethics (TX power, listening restrictions, "authorized targets only"): **[legal-and-safety.md](../legal-and-safety.md)**.

## Open questions / to research
- Exact current **decoder roster** drift between OFW and Unleashed/Xtreme/Momentum (CFW adds protocols and sometimes loosens the locked/decode-only policy) — snapshot per release `(verify)`.
- Which **rolling-code vendors** a current CFW will *label and partially parse* (serial/counter) vs only RAW-capture, and whether any expose save for owned-device workflows `(verify)`.
- Practical **brute-force timing** per fixed-code family (codes/sec at given TE) and which spaces are large enough to be pointless.
- Best **Custom preset** register dumps for POCSAG and odd TPMS data rates `(verify)`.
- External **CC1101 module** wiring + recommended antenna per band, and the resulting realistic range numbers.

## Sources
- Official Sub-GHz: https://docs.flipper.net/zero/sub-ghz
- Supported vendors (unlocked vs locked): https://docs.flipper.net/zero/sub-ghz/supported-vendors
- Reading signals (Read / RAW / Frequency Analyzer): https://docs.flipper.net/zero/sub-ghz/read
- `.sub` file format spec: https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/SubGhzFileFormats.md
- SubGhz file-format doxygen: https://developer.flipper.net/flipperzero/doxygen/subghz_file_format.html
- TI CC1101 datasheet (SWRS061): https://www.ti.com/lit/ds/symlink/cc1101.pdf
- CC1101 parameter explainer (modulation/deviation/bandwidth): https://github.com/jamisonderek/flipper-zero-tutorials/wiki/Sub-GHz
- Sub-GHz settings (presets/custom): https://deepwiki.com/UberGuidoZ/Flipper/4.1-sub-ghz-settings
- Brute-force tooling (de Bruijn): https://github.com/tobiabocchi/flipperzero-bruteforce
- How Sub-GHz works (blog): https://blog.flipper.net/sub-ghz/
