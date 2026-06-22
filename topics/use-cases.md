---
title: Use Cases & Project Ideas
domain: topics
type: topic
status: detailed
summary: Legitimate uses & project ideas organized by capability, with a starter-projects table.
hardware: []
use_cases: []
related: [topics/security-pentest.md, legal-and-safety.md, firmware/README.md, capabilities/sub-ghz.md, capabilities/nfc-rfid.md, theory/rolling-codes.md]
tags: [use-cases, projects, starter-projects, education, maker, authorized-testing]
last_verified: 2026-06-19
---

# Use Cases & Project Ideas

> **TL;DR —** A catalog of legitimate, authorized-only things to do with the Flipper, organized by capability and cross-linked to prerequisite docs, opening with a starter-projects table to build skill fast.
> Authorized targets only — [legal-and-safety](../legal-and-safety.md). See [security-pentest](security-pentest.md), [firmware/README](../firmware/README.md). Part of the [KB](../README.md).

A catalog of **legitimate** things to actually do, organized by capability, each cross-linked to its
prerequisite capability/firmware/add-on file. The Flipper is a dual-use tool: every RF/NFC/HID idea
below assumes **you own the target or have explicit written authorization**. "Test your own" is the
default mode; if it isn't yours, get permission first. See [legal-and-safety](../legal-and-safety.md).

---

## Starter projects (do these first)

A shortlist to build skill fast. Difficulty = how fiddly, not how "dangerous" — all are on-your-own-stuff.

| # | Project | Difficulty | Capability | What it teaches |
|---|---------|-----------|------------|-----------------|
| 1 | Rebuild a lost TV/AC remote with the **Universal IR** app | easy | [infrared](../capabilities/infrared.md) | IR is just timed pulses; brute-force vs learned codes |
| 2 | Read → save → emulate **your own** office/gym 125 kHz fob | easy | [nfc-rfid](../capabilities/nfc-rfid.md), [ibutton](../capabilities/ibutton.md) | LF fixed-ID has no auth; why UID-only readers are weak |
| 3 | Capture **your own** garage/gate remote and identify **fixed vs rolling** code | easy | [sub-ghz](../capabilities/sub-ghz.md), [rolling-codes](../theory/rolling-codes.md) | ASK/OOK, replay, why rolling codes don't replay |
| 4 | Write an **NDEF NFC tag**: Wi-Fi-join card, URL, or contact | easy | [nfc-rfid](../capabilities/nfc-rfid.md) | NDEF records; NFC as convenience, not security |
| 5 | **BadUSB** "Hello World" + auto-lock script on **your own** laptop | medium | [badusb](../capabilities/badusb.md) | HID trust model; why USB ports are an attack surface |
| 6 | Read **your own** car's **TPMS** tyre-pressure sensors | medium | [sub-ghz](../capabilities/sub-ghz.md) | Real-world 315/433 MHz telemetry decoding |
| 7 | **GPIO** I²C sensor (e.g. BME280) read-out or UART logic sniff | medium | [gpio-addons-current](../hardware/gpio-addons-current.md), [tinkering](tinkering.md) | Serial buses, 3.3 V logic, the Flipper as a bench tool |
| 8 | **Clone your own** Amiibo / NTAG215 to a writable tag for play | medium | [nfc-rfid](../capabilities/nfc-rfid.md) | NTAG memory layout; password-protected pages |

After these you'll understand modulation, the read→save→emulate loop, the HID trust model, and where
security actually lives (auth/crypto, not the air gap).

---

## Everyday / household

| Use | Notes | Links |
|-----|-------|-------|
| Universal IR remote | One device for TVs, ACs, projectors, soundbars; rebuild a lost remote via learned or brute-force codes | [infrared](../capabilities/infrared.md) |
| Carry one access credential | Clone **your own** LF fob to a blank **T5577**, or your iButton to a writable key, so you carry one Flipper instead of a keyring | [nfc-rfid](../capabilities/nfc-rfid.md), [ibutton](../capabilities/ibutton.md) |
| Test your own remotes | Range-test garage/gate/doorbell; confirm fixed-code (replayable) vs rolling-code; spot a dying battery from weak TX | [sub-ghz](../capabilities/sub-ghz.md) |
| Program NFC tags (NDEF) | Wi-Fi-join cards, URL/launch shortcuts, contact share, home-automation triggers | [nfc-rfid](../capabilities/nfc-rfid.md) |
| Amiibo for your own games | Emulate or write NTAG215 figures you own | [nfc-rfid](../capabilities/nfc-rfid.md) |
| Read your own sensors | Weather stations, **TPMS**, some doorbells/thermometers on 315/433/868 MHz | [sub-ghz](../capabilities/sub-ghz.md) |
| Bad-remote diagnosis | Confirm whether a remote still transmits at all before buying a replacement | [infrared](../capabilities/infrared.md), [sub-ghz](../capabilities/sub-ghz.md) |

> Reality check: encrypted car key fobs (rolling code), AES transit/access cards, and EMV payment
> cards **cannot** be cloned. If a "clone your own car key" idea fails, the security is working as
> designed — see [rolling-codes](../theory/rolling-codes.md) and [legal-and-safety](../legal-and-safety.md).

---

## Learning / RF & security education

The Flipper's best long-term value is as a teaching tool. Use **your own** cards/remotes as the lab.

| Topic | Hands-on idea | Links |
|-------|---------------|-------|
| RF modulation & encoding | Capture raw, watch ASK/OOK waveforms, decode protocols (Princeton, CAME, NICE, Holtek) | [sub-ghz](../capabilities/sub-ghz.md) |
| Rolling-code theory | Capture a rolling remote twice; prove the code changes every press; understand counters/sync windows | [rolling-codes](../theory/rolling-codes.md) |
| Card-security lab | Compare MIFARE Classic (Crypto1, broken) vs DESFire/AES (resists) on cards you own | [nfc-rfid](../capabilities/nfc-rfid.md) |
| HID trust model | Demonstrate why a "keyboard" is trusted instantly (BadUSB), on your own machine | [badusb](../capabilities/badusb.md) |
| IR protocol study | Reverse-engineer an unknown remote's protocol from captures | [infrared](../capabilities/infrared.md) |
| CTF / wargames | RF/NFC/hardware challenges; Flipper is a great portable CTF companion | [security-pentest](security-pentest.md) |
| Defensive awareness | Show colleagues (with permission) why Faraday pouches, EMV, and AES badges matter | [legal-and-safety](../legal-and-safety.md) |

---

## Hardware / maker

| Project | Notes | Links |
|---------|-------|-------|
| GPIO sensors | I²C/SPI/UART read-out; build a portable data logger | [gpio-addons-current](../hardware/gpio-addons-current.md), [tinkering](tinkering.md) |
| Logic analyzer / UART sniff | Debug serial devices; the Flipper doubles as a cheap bench tool | [gpio-addons-current](../hardware/gpio-addons-current.md) |
| SWD debugging | Flash/debug other STM32/MCU targets via the Wi-Fi DevBoard | [gpio-addons-current](../hardware/gpio-addons-current.md) |
| Custom backpack | Solder a proto-board module to the GPIO header for a project enclosure | [hardware/README](../hardware/README.md), [buying-guide](../hardware/buying-guide.md) |
| Video Game Module (RP2040) | DVI/HDMI video-out, IMU motion apps, extra compute via the official VGM | [gpio-addons-current](../hardware/gpio-addons-current.md) |
| App development | Write your own `.fap` apps in C; learn the Flipper SDK | [firmware/README](../firmware/README.md) |
| 3D-printed cases/jigs | Antenna mounts, fob holders, test rigs | [buying-guide](../hardware/buying-guide.md) |

---

## Authorized security testing (with written scope)

Only with a signed statement of work / rules of engagement. See **[security-pentest](security-pentest.md)**
for methodology, the capability-vs-tool matrix, and the authorization checklist.

| Activity | Notes | Links |
|----------|-------|-------|
| Physical-access audits | Clone **issued test credentials** to show UID-only / LF fixed-ID readers are spoofable | [nfc-rfid](../capabilities/nfc-rfid.md), [security-pentest](security-pentest.md) |
| RF hygiene survey | Identify fixed-code remotes/gates that are replayable; document; recommend rolling/AES | [sub-ghz](../capabilities/sub-ghz.md), [rolling-codes](../theory/rolling-codes.md) |
| USB-control testing | BadUSB keystroke-injection demos for awareness training and endpoint/USB-policy testing | [badusb](../capabilities/badusb.md) |
| Wi-Fi / BLE assessment | With an **ESP32 backpack** (Marauder / Ghost ESP): deauth, handshake capture, evil-portal, BLE recon — in a lab/engagement | [gpio-addons-current](../hardware/gpio-addons-current.md), [security-pentest](security-pentest.md) |
| Hardware assessment | UART/SWD/I²C poking and logic analysis of a device you're authorized to assess | [gpio-addons-current](../hardware/gpio-addons-current.md) |

> The Flipper is a **demonstration and discovery** tool in a real engagement, not a one-box red-team
> kit. For deep RFID work reach for a Proxmark3; for wideband RF a HackRF/RTL-SDR; for HID implants
> an O.MG cable. Matrix in [security-pentest](security-pentest.md).

---

## Open questions / to research
- Pick 3 starter projects matched to my specific goals and write detailed step-by-steps with screenshots.
- Which Unleashed/Xtreme apps (`.fap`) are worth installing for each use case above (curate a shortlist).
- Best beginner GPIO sensor kit + wiring for the I²C/UART logger project (parts list under €30).
- A reproducible "fixed vs rolling code" teaching demo I can run for non-technical colleagues.
- Which CTF events / wargames best exercise the Flipper's RF+NFC+HID skillset.

## Sources
- Flipper docs hub: https://docs.flipper.net/zero
- Sub-GHz frequencies & regional limits: https://docs.flipper.net/zero/sub-ghz/frequencies
- Tutorials (jamisonderek): https://github.com/jamisonderek/flipper-zero-tutorials
- awesome-flipperzero (apps, FAQ, capabilities): https://github.com/djsime1/awesome-flipperzero
- Capabilities & limits overview: https://lifetips.alibaba.com/tech-efficiency/everything-flipper-zero-can-and-cant-do
- Card-cloning ethics & reality (2026): https://www.cyberseclabs.org/can-you-clone-cards-with-flipper-zero/
