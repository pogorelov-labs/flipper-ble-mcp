---
title: Sub-GHz / RF Apps — Installed-App Runbook
domain: resources
type: reference
status: detailed
summary: Per-app reference for the Sub-GHz/RF .faps on this Momentum rig — what each does, key options, use-cases, gotchas, sources.
hardware: [flipper-internal, cc1101-ext]
use_cases: [UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10, UC-11, UC-12, UC-13, UC-14]
related: [capabilities/sub-ghz.md, theory/rolling-codes.md, topics/subghz-region-lock.md, resources/subghz-device-repos.md, my-setup.md, legal-and-safety.md]
tags: [sub-ghz, apps, fap, brute-force, rolling-code, tpms, pocsag, pagers, momentum]
last_verified: 2026-06-22
---

# Sub-GHz / RF Apps — Installed-App Runbook

> **TL;DR —** One-stop reference for every Sub-GHz/RF `.fap` installed on this rig (Momentum, maxed catalog): what it does, its key settings, concrete use-cases, and the gotcha that bites first. The radio theory lives in [capabilities/sub-ghz.md](../capabilities/sub-ghz.md); why rolling-code apps can't "just open" a modern gate is [theory/rolling-codes.md](../theory/rolling-codes.md); the `.sub` libraries these apps consume are in [subghz-device-repos.md](subghz-device-repos.md).
> Region/TX limits: [topics/subghz-region-lock.md](../topics/subghz-region-lock.md). My radio (433-only external CC1101): [my-setup.md](../my-setup.md). Legality: [legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md).

This is an **app catalog**, not a capability primer — read [capabilities/sub-ghz.md](../capabilities/sub-ghz.md) first for bands, presets, the Read/Read-RAW/Frequency-Analyzer/Add-Manually workflows, and the `.sub` format; everything here builds on it. **Authorized targets only.** Most of these transmit on regulated ISM/SRD bands; the legal duty to only TX what/where you're permitted is entirely on the operator regardless of what the firmware allows ([legal-and-safety.md](../legal-and-safety.md)).

## How to read this doc
- **Hardware tags per app:** `[internal]` = the Flipper's built-in CC1101; `[+ext-CC1101]` = benefits from / may need an external module. My external board is **433-only** (E07-400MM10S, ~410–450 MHz) — for **315 / 868 / 915 MHz** switch `Sub-GHz → Radio Settings → Module → Internal` ([my-setup.md](../my-setup.md)).
- **RX-only vs TX:** receive/decode-only apps (analyzers, sensor decoders, POCSAG) carry no TX-legality risk beyond listening restrictions; **TX apps** (brute-force, remotes, replay, pagers, chat, share) do.
- `(verify)` = volatile or not pinned to a primary source on this pass — re-check before relying.

---

## Core Sub-GHz (built-in app) — `subghz`
**[internal] [+ext-CC1101] · RX + TX · UC-04, UC-05, UC-06, UC-11, UC-13, UC-14**

The stock firmware app and the foundation everything else extends. Modes: **Read** (listen + run protocol decoders → editable Key file), **Read RAW** (record the on/off timing waveform → RAW file), **Saved** (browse/emulate/send stored `.sub`), **Add Manually** (synthesize a known static protocol from typed parameters), and **Frequency Analyzer** (sweep for the strongest RSSI while you hold the target's button). Radio Settings selects **Module: Internal/External** and the **frequency + modulation preset** (AM270/AM650/FM238/FM476).

- **Key options:** Frequency, Modulation (preset), Hopping (RSSI), Bin RAW (capture non-decoding signals too), Repeater (re-TX received signals!), Remove duplicates, Autosave, the Ignore-protocol filters. Full settings table: [capabilities/sub-ghz.md → Read-app settings](../capabilities/sub-ghz.md).
- **Use-cases:** read/replay your own fixed-code garage/gate/doorbell/RF-socket; range-test your own 433 gear (UC-13/UC-14); survey what's on a band; synthesize a fixed-code signal you own.
- **Gotchas:** **rolling-code vendors are decode-only** (Save/Emulate disabled by design — see [rolling-codes.md](../theory/rolling-codes.md)); on the external board **set Module → External and enable 5V on GPIO**, and switch back to Internal for 315/868/915; "it didn't work" on a fixed-code target is almost always wrong **frequency/preset/deviation**, not a Flipper fault.
- **Source:** https://docs.flipper.net/zero/sub-ghz

## Sub-GHz Bruteforcer — `subghz_bruteforcer`
**[internal] [+ext-CC1101] · TX · UC-07**

On-device brute-forcer for **small fixed-code** systems (gates/garages/barriers). Pick a **protocol** (CAME 12-bit 433 is the default; also NICE 12-bit, Chamberlain/Linear, Holtek/Princeton-family, etc.) and a **frequency**, and it walks the entire code space, sending each candidate. Distinct from the *PC-side* `.sub` generators in [subghz-device-repos.md](subghz-device-repos.md) — this is the interactive app (Ganapati & xMasterX; maintained by derskythe/xMasterX in the DarkFlippers `flipperzero-subbrute` tree, bundled in Unleashed/Momentum).

- **Key options:** protocol, frequency, **repeats per code** (default ~3; raise with ←/→ for stubborn receivers), pause/resume, resume-from-index.
- **Use-cases:** open a fixed-code gate/barrier **you own** whose remote is lost; demonstrate the replay-risk of legacy dip-switch hardware (UC-07).
- **Gotchas:** **useless against rolling codes** (the keyspace *is* the cipher); only tiny fixed spaces (≈8–12-bit, hundreds–few-thousand codes) are practical; sweeping someone else's receiver is unauthorized access in many jurisdictions. de Bruijn mechanics + which spaces are worth it: [capabilities/sub-ghz.md → Brute-force reality](../capabilities/sub-ghz.md).
- **Source:** https://github.com/DarkFlippers/flipperzero-subbrute

## SubRem (Sub-GHz Remote) — `subghz_remote_ofw` + `subghz_remote`
**[internal] [+ext-CC1101] · TX · UC-04**

Turns the Flipper into a **multi-button universal remote**: map up to **5 saved `.sub` files** to the D-pad (Up/Down/Left/Right/OK) and fire each with one keypress. Config is a plain `.txt` map (per direction: a `…U=/D=/L=/R=/OK=` file path plus a `ULABEL/DLABEL/…` on-screen label). `subghz_remote_ofw` is the catalog build (gid9798 & xMasterX, OFW-flavoured); `subghz_remote` is the same SubRem concept bundled in CFW firmware (Unleashed/Momentum/RogueMaster) — keep one to avoid confusion `(verify which the rig launches)`.

- **Key options:** the 5 file slots + 5 labels in the map file; file paths must avoid spaces/special chars (only `-` and `_`).
- **Use-cases:** a single "home RF remote" — e.g. Up = fan on, Down = fan off, Left = doorbell, Right = garage open, OK = garage close (all devices **you own**, fixed-code or your own synthesized signals).
- **Gotchas:** still bound by the fixed-vs-rolling rule — a rolling-code capture mapped to a button won't work; build the map file on the SD with a text editor or via the app's editor; each slot just replays one `.sub`.
- **Source:** https://lab.flipper.net/apps/subghz_remote_ofw · docs: https://github.com/DarkFlippers/unleashed-firmware/blob/dev/documentation/SubGHzRemotePlugin.md

## ProtoView — `protoview`
**[internal] [+ext-CC1101] · RX + TX (resend/edit) · UC-05, UC-06**

antirez's **digital RF signal viewer/analyzer** — the go-to "what is this signal?" tool. Shows the high/low pulse train the CC1101 is receiving in real time (so you can tell signal from noise), decodes a growing set of protocols (incl. several **TPMS** families and car/sensor OOK), and for supported protocols can **edit decoded fields, re-detect, and re-transmit** — including resending on a *different* frequency/modulation than captured.

- **Key options:** frequency, modulation/preset, pause/freeze the view, field editor (for protocols implementing message creation), TX of the (edited or raw) signal.
- **Use-cases:** reverse-engineer an unknown OOK signal's structure; inspect/diagnose your own TPMS or sensor; learn encodings hands-on (UC-05/UC-06). Complements stock **Read RAW**.
- **Gotchas:** editing only works for protocols with creation methods implemented; TX is real RF (authorized targets only); cross-links to the receive-only sensor section of [subghz-device-repos.md](subghz-device-repos.md).
- **Source:** https://github.com/antirez/protoview

## ProtoPirate — `proto_pirate`
**[internal] [+ext-CC1101] · RX (decode-only by default) · UC-05**

Experimental **rolling-code analysis / interception** toolkit (RocketGod). Captures and **decodes automotive key-fob families** (Kia, Ford, Subaru, Suzuki, VW, and more) with a live "radar" capture UI and frequency hopping; can also load and analyze existing `.sub` captures from `/ext/subghz/`. Ships with **TX disabled by default** so you can't accidentally desync a fob.

- **Key options:** frequency / hopping set, live capture vs load-from-SD, per-family decoder selection `(verify exact menu)`.
- **Use-cases:** study how modern RKE frames are structured (counter/serial/button fields); confirm a target is rolling-code (and therefore replay-proof) during an authorized assessment (UC-05). Educational counterpart to [theory/rolling-codes.md](../theory/rolling-codes.md).
- **Gotchas:** **decode ≠ clone** — it cannot mint a valid next code (no manufacturer/device key); WIP and firmware-sensitive; "analysis," not entry.
- **Source:** https://github.com/RocketGod-git/ProtoPirate

## Rolling Flaws — `rolling_flaws`
**[internal] · RX + TX (against its own simulated receiver) · UC-05**

Derek Jamison's **educational rolling-code lab**: the Flipper **simulates a KeeLoq receiver** (DoorHan, Subaru/KGB, and unknown-manufacturer profiles) so you can practice ~12 attack scenarios — **replay, pairing/cloning, future-code, RollBack-style rollback, and the ENC00 weak-key attack** — safely, against the simulator rather than real hardware.

- **Key options:** receiver manufacturer/profile, attack-scenario selector, manufacturer-key source (DoorHan key vs a universal key DB) `(verify menu labels)`.
- **Use-cases:** *understand* RollBack and KeeLoq counter-window behaviour on something you control; classroom/CTF demonstrations (UC-05). Theory: [rolling-codes.md → RollJam/RollBack](../theory/rolling-codes.md).
- **Gotchas:** explicitly **education-only** — the author warns that practising against real remotes/receivers can permanently **desync** them (requiring a service visit); the value is a safe sandbox, not a field exploit. The "DarkWeb firmware bypasses rolling codes" headlines this app is associated with overstate what's possible on real, correctly-implemented systems.
- **Source:** https://github.com/jamisonderek/flipper-zero-tutorials/tree/main/subghz/apps/rolling-flaws

## Weather Station — `weather_station`
**[internal] [+ext-CC1101] · RX-only · UC-08**

Skorpionm's **433/868/315 MHz weather-sensor receiver** (also bundled in CFW). Same UI as core Sub-GHz but with a **weather-sensor decoder set** instead of access-control protocols: reads temp/humidity/wind/rain/ID from a wide range of outdoor sensors (LaCrosse, TFA/Dostmann, Nexus, Acurite, Oregon, etc. `(verify exact roster per build)`).

- **Key options:** frequency (most EU/global sensors on **433.92**; some on 868), modulation, history/dedupe.
- **Use-cases:** read **your own** outdoor sensor telemetry for diagnostics or a home dashboard; identify which protocol a sensor uses (UC-08).
- **Gotchas:** RX-only (no spoofing here); a sensor only transmits periodically, so be patient; 868 MHz sensors need **Module → Internal** on this rig.
- **Source:** https://lab.flipper.net/apps/weather_station

## TPMS — `tpms`
**[internal] [+ext-CC1101] · RX-only · UC-09**

wosk's **tire-pressure-sensor receiver**: decodes pressure/temperature/sensor-ID from TPMS modules over 315/433 MHz. Includes a **125 kHz "relearn" trigger** to wake a sensor that's stationary/unmounted.

- **Key options:** frequency (315 US / 433 EU), the LF relearn trigger, sensor history.
- **Use-cases:** diagnose **your own** vehicle's TPMS, match a sensor to a wheel position, verify a replacement sensor (UC-09).
- **Gotchas:** sensor coverage is limited — **Schrader GG4** confirmed, more in progress (last release v0.2, Apr 2024 `(verify)`); sensors usually transmit only when the car is moving (hence relearn); ProtoView decodes some TPMS too. Cross-ref [subghz-device-repos.md → Sensors](subghz-device-repos.md).
- **Source:** https://github.com/wosk/flipperzero-tpms

## POCSAG Pager — `pocsag_pager`
**[internal] [+ext-CC1101] · RX-only · UC-10**

xMasterX & Shmuma's **POCSAG pager decoder** — captures and displays **POCSAG 512 / 1200 / 2400** messages on any CC1101 frequency (defaults aimed at the amateur **DAPNET 439.9875 MHz**; add custom presets/frequencies via an SD settings file). Same plugin tree as the `flipper-pager` repo in [subghz-device-repos.md](subghz-device-repos.md).

- **Key options:** frequency + (often **Custom 2-FSK**) preset, baud rate (512/1200/2400), custom-frequency list on SD.
- **Use-cases:** receive your own amateur/DAPNET pager traffic; learn the POCSAG protocol (UC-10).
- **Gotchas:** **listening to pager traffic is legally restricted in many countries** regardless of technical feasibility ([legal-and-safety.md](../legal-and-safety.md)); usually needs the right **Custom preset + data rate** to lock (see [capabilities/sub-ghz.md → presets](../capabilities/sub-ghz.md)).
- **Source:** https://lab.flipper.net/apps/pocsag_pager · https://github.com/xMasterX/flipper-pager

## Meal Pager — `meal_pager`
**[internal] [+ext-CC1101] · TX · (no KB UC — closest: UC-07 fixed-code)**

leedave's **restaurant coaster-pager trigger/spoofer**. Brute-forces the call space of common **Retekess** systems — **T119, TD157, TD165, TD174** — to make pagers buzz; modes target a **station-ID range** and a **pager-number range** (typically 0–31) with adjustable repeats. Built on Moeker's `pagger` protocol work + xb8's T119 research.

- **Key options:** **pager type** (T119/TD157/TD165/TD174), **station-ID range**, **pager-number range** (0–31), **repeat count** (1–10), frequency (≈433.92 EU; 315/467.75 elsewhere). LED: yellow = generating, purple = transmitting.
- **Use-cases:** functionally test **pagers you operate** (a venue's own kit); protocol study (closest KB tag UC-07).
- **Gotchas:** **ethically loaded** — these target *commercial* equipment in venues you don't own; treat venue hardware as off-limits unless you run it. Fixed-code (replays by design). Overlaps `chief_cooker` below (different author/feature set).
- **Source:** https://github.com/leedave/flipper-zero-meal-pager

## Chief Cooker — `chief_cooker`
**[internal] [+ext-CC1101] · RX + TX · (no KB UC — closest: UC-07 fixed-code)**

denr01's **fuller restaurant-pager tool** (Momentum-oriented): **receive, decode, edit, save, and resend** pager signals. Auto-detects encoding on capture (with manual override and live decoded-value preview), can resend to a **specific pager or all at once**, and saves captures with custom station names into categories.

- **Key options:** scan frequency (EU/RU default **433.92**; **315.00 / 467.75** for US/other), encoding (auto/manual), target pager vs broadcast-all, save-with-station-name.
- **Use-cases:** richer counterpart to `meal_pager` for **pager systems you operate** — capture-then-replay rather than blind brute-force; protocol analysis of coaster pagers.
- **Gotchas:** same venue-equipment ethics as `meal_pager`; the capture/edit/resend flow makes intent clearer but the authorization rule is identical.
- **Source:** https://github.com/denr01/FZ-ChiefCooker

## Spectrum Analyzer — `spectrum_analyzer`
**[internal] [+ext-CC1101] · RX-only · UC-05**

jolcese's classic (maintained by xMasterX/theY4Kman/ALEEF02): renders a **spectrogram** of RF energy across a band so you can *see* which frequencies are active. Turns the CC1101 into a coarse band-scope.

- **Key options:** band/center selection, span/range, refresh `(verify exact controls per build)`.
- **Use-cases:** find which sub-band a remote/sensor lives in before a precise Frequency-Analyzer pass; spot interference; general RF survey (UC-05).
- **Gotchas:** the CC1101 is a narrowband transceiver, not a real SDR — resolution/sensitivity are coarse; **RX-only**; for protocol decoding use Read/ProtoView instead.
- **Source:** https://awesome-flipper.com/application/lab.flipper.net/sub-ghz/spectrum_analyzer/

## Sub Analyzer — `sub_analyzer`
**[internal] · RX / file-analysis · UC-06 · (unverified specifics)**

A catalog **Sub-GHz analyzer** distinct from `spectrum_analyzer`. Best evidence is that it inspects/decodes **signal structure / RAW pulse timing** (frame boundaries, bit-field stability) rather than drawing a spectrogram — i.e. a protocol/RAW analyzer in the ProtoView family. **(unverified)** — note that web results frequently conflate this on-device app with jsammarco's *desktop* `flipper-subghz-analyzer` GUI, which is a different thing; confirm the on-device app's exact author/feature set from its catalog page before relying.

- **Likely use-cases:** examine an unknown RAW `.sub`'s timing/encoding on-device (UC-06).
- **Gotchas:** identity/author **not pinned** this pass; don't conflate with the desktop analyzer; verify on the rig.
- **Source:** https://lab.flipper.net/apps/sub_analyzer

## Radio Scanner — `radio_scanner`
**[internal] [+ext-CC1101] · RX-only · UC-05**

RocketGod's **frequency scanner with audio**: sweeps CC1101-reachable frequencies, locks to active ones, and pipes the demodulated audio to the **internal speaker** so you can *hear* activity (it is **not** an FM broadcast radio — those frequencies aren't reachable).

- **Key options:** start/stop frequency + step, RSSI/lock threshold, scan direction `(verify exact controls)`.
- **Use-cases:** quickly find a transmitting device on a band by ear; survey ISM activity (UC-05).
- **Gotchas:** RX-only; AM/OOK audio is rough; CC1101 band limits apply (315/868/915 need Module → Internal here).
- **Source:** https://github.com/RocketGod-git/Flipper-Zero-Radio-Scanner

## Enhanced Sub-GHz Chat — `esubghz_chat`
**[internal] [+ext-CC1101] · RX + TX · UC-05**

twisted-pear's **encrypted text chat over Sub-GHz** — a hardened reimplementation of the firmware's CLI Sub-GHz chat. Messages are **AES-256-GCM encrypted** with a per-message random IV; the GCM tag is verified on receive (bad tags dropped) and a basic **replay-prevention** mechanism is included. Keys come from a **password** (SHA-256 of the passphrase → key), a **raw hex key**, or by **reading a key from another Flipper over NFC**.

- **Key options:** frequency + modulation (both Flippers must match), encryption mode (password / hex key / NFC key-exchange / plaintext), name.
- **Use-cases:** short-range off-grid encrypted messaging between two Flippers you control; a hands-on demo of authenticated encryption + key exchange over RF (UC-05).
- **Gotchas:** security is **only as strong as the password** (single SHA-256, no KDF stretching — use a long passphrase or hex key); both ends need matching freq/preset; it's **transmitting** on ISM bands (region/TX rules apply); plaintext mode is unencrypted.
- **Source:** https://github.com/twisted-pear/esubghz_chat

## TX automation — Scheduler, Playlist, Playlist Creator
**`subghz_scheduler` · `subghz_playlist` · `subghz_playlist_creator` — [internal] [+ext-CC1101] · TX · UC-04**

A small family for **automated/sequenced transmission** of saved `.sub` files (authorized targets only):
- **`subghz_scheduler`** (gid9798 & xMasterX) — sends a single `.sub` *or* a playlist `.txt` at a **timed interval**. Interval modes: **Relative** (gap = end-of-one → start-of-next) vs **Precise** (start → start); trigger modes: **Normal / Immediate / One-Shot**. Use: repeat a signal you own on a schedule; timed lab tests.
- **`subghz_playlist`** — plays a list of `.sub` files **back-to-back in sequence** (the Unleashed/RogueMaster/Xtreme "Sub-GHz Playlist" consumed by playlist `.txt` collections). Use: fire a sequence of your own signals in order.
- **`subghz_playlist_creator`** — builds those playlist files **on-device** (pick `.sub`s → write the `.txt`), so you don't have to hand-edit on a PC.
- **Gotchas:** convenient for fixed-code signals you own; the same rolling-code limits apply; long unattended TX is exactly where **TX-legality + authorized-targets** rules matter most ([legal-and-safety.md](../legal-and-safety.md)). Related `.sub`/playlist collections: [subghz-device-repos.md](subghz-device-repos.md).
- **Sources:** https://github.com/shalebridge/flipper-subghz-scheduler · https://github.com/darmiel/flipper-playlist

## Utility & conversion apps (one-liners)
**[internal] except where noted**

- **`subghz_raw_edit`** — tiny **on-device RAW `.sub` editor**: trim a RAW capture down to just the burst you care about (drop leading/trailing noise/dead air) before replaying. RX-derived editing; output is a cleaner RAW `.sub`. (For heavier inspection/decoding use a desktop tool.) `(verify exact repo/author)`.
- **`flipper_share`** — **direct file transfer between two Flippers over Sub-GHz** (internal TX), no cables/phone/PC/internet. Both devices run the app; sends arbitrary files device-to-device. **TX** — region/TX rules apply; speed is modest (it's an OOK radio link). Catalog: https://lab.flipper.net/apps/flipper_share `(verify author + size limits)`.
- **`hc11_modem`** — **HC-11 serial-radio emulator** (Giraut): makes the Flipper behave like an **HC-11 433 MHz UART module** — relay USB serial data to/from a real HC-11, or chat **Flipper-to-Flipper** with no HC-11 at all. Supports 20 channels / 16 addresses; **FU3** full RX/TX, **FU1** reliable RX-only (FU2/FU4 unsupported); protocol partly reverse-engineered (WIP). **TX**. Source: https://github.com/Giraut/flipper_zero_hc11_wireless_modem
- **`fmf_to_sub`** ("Music to Sub-GHz Radio", CodeAllNight) — **format converter**: turns Flipper music files (**.fmf / .txt**, RTTTL-style) into a **RAW `.sub`** you can transmit; a second Flipper running it can receive and play the "music." Pick frequency + modulation (AM650 default). Novelty/demo of RAW synthesis. **TX**. Source: https://lab.flipper.net/apps/fmf_to_sub
- **`chief_cooker`** / **`meal_pager`** — see their full entries above (restaurant pagers).

> **Naming note:** several of these ship under more than one name/build (e.g. `subghz_remote_ofw` vs `subghz_remote`; the bundled-vs-catalog brute-forcer; scheduler vs playlist) because Momentum bundles some and the catalog offers others. If two do the same thing, keep one to avoid menu clutter — confirm which the rig actually launches.

## Quick map — app → KB use-case
| App(s) | What you'd reach for it | KB UC |
|---|---|---|
| `subghz` (core) | read/replay/synthesize, freq-analyzer, RAW | UC-04/05/06/11/13/14 |
| `subghz_bruteforcer` | fixed-code gate brute-force (own) | UC-07 |
| `subghz_remote(_ofw)` | 5-button universal remote (own signals) | UC-04 |
| `protoview`, `sub_analyzer` | reverse/inspect unknown signal | UC-05/06 |
| `proto_pirate`, `rolling_flaws` | study rolling-code structure / RollBack (lab) | UC-05 |
| `weather_station` | own outdoor sensors | UC-08 |
| `tpms` | own vehicle tire sensors | UC-09 |
| `pocsag_pager` | own/amateur pager RX | UC-10 |
| `spectrum_analyzer`, `radio_scanner` | band survey (visual / audio) | UC-05 |
| `esubghz_chat` | encrypted Flipper-to-Flipper chat | UC-05 |
| `subghz_scheduler/playlist/_creator` | automated/sequenced own-signal TX | UC-04 |
| `meal_pager`, `chief_cooker` | restaurant pagers (operate-only) | — (≈UC-07) |
| `flipper_share`, `hc11_modem`, `fmf_to_sub`, `subghz_raw_edit` | transfer / serial-radio / convert / edit | — |

## Open questions / to research
- Pin **`sub_analyzer`**'s on-device author/repo and confirm it's a protocol/RAW analyzer (not the jsammarco desktop GUI) `(verify)`.
- Confirm whether the rig launches **`subghz_remote_ofw`** or the CFW-bundled **`subghz_remote`** (SubRem) — and dedupe.
- Pin **`subghz_raw_edit`** and **`flipper_share`** repos/authors + `flipper_share` size limits and throughput `(verify)`.
- Snapshot the **`weather_station` / `tpms`** decoder rosters on *this* Momentum build (they drift per release) `(verify)`.
- Which of these are **Momentum-bundled** vs catalog-installed on the rig (cross-check against an `app_list` once the device is in scope) — and whether any old FAPs failed to load post-migration (API 87.1).
- Best **Custom-preset register dumps** for POCSAG / odd TPMS data rates (shared open question with [capabilities/sub-ghz.md](../capabilities/sub-ghz.md)).

## Sources
- Core Sub-GHz: https://docs.flipper.net/zero/sub-ghz · supported vendors: https://docs.flipper.net/zero/sub-ghz/supported-vendors
- Sub-GHz Bruteforcer: https://github.com/DarkFlippers/flipperzero-subbrute
- SubRem / Sub-GHz Remote: https://lab.flipper.net/apps/subghz_remote_ofw · https://github.com/DarkFlippers/unleashed-firmware/blob/dev/documentation/SubGHzRemotePlugin.md
- ProtoView: https://github.com/antirez/protoview
- ProtoPirate: https://github.com/RocketGod-git/ProtoPirate
- Rolling Flaws: https://github.com/jamisonderek/flipper-zero-tutorials/tree/main/subghz/apps/rolling-flaws
- Weather Station: https://lab.flipper.net/apps/weather_station
- TPMS: https://github.com/wosk/flipperzero-tpms
- POCSAG Pager: https://lab.flipper.net/apps/pocsag_pager · https://github.com/xMasterX/flipper-pager
- Meal Pager: https://github.com/leedave/flipper-zero-meal-pager
- Chief Cooker: https://github.com/denr01/FZ-ChiefCooker
- Spectrum Analyzer: https://awesome-flipper.com/application/lab.flipper.net/sub-ghz/spectrum_analyzer/
- Sub Analyzer: https://lab.flipper.net/apps/sub_analyzer
- Radio Scanner: https://github.com/RocketGod-git/Flipper-Zero-Radio-Scanner
- Enhanced Sub-GHz Chat: https://github.com/twisted-pear/esubghz_chat
- Scheduler: https://github.com/shalebridge/flipper-subghz-scheduler · Playlist: https://github.com/darmiel/flipper-playlist
- HC-11 modem: https://github.com/Giraut/flipper_zero_hc11_wireless_modem
- Music to Sub-GHz (fmf_to_sub): https://lab.flipper.net/apps/fmf_to_sub
- Awesome-Flipper Sub-GHz app index: https://awesome-flipper.com/application/lab.flipper.net/sub-ghz/
