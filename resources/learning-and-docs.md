---
title: Learning & Documentation
domain: resources
type: resource-list
status: detailed
summary: Docs, cheat-sheets, and deep RF+NFC learning material by level
hardware: []
use_cases: []
related: [resources/community-and-video.md, capabilities/sub-ghz.md, capabilities/nfc-rfid.md, theory/rolling-codes.md]
tags: [learning, docs, cheat-sheets, rf, nfc, mifare, modulation]
last_verified: 2026-06-19
---

# Learning & Documentation

> **TL;DR —** Where to learn the Flipper by level — official docs and beginner cheat-sheets, developer/reference material, and deep RF-modulation and MIFARE/NFC-security papers behind cloning. Pairs with the capability primers in this KB.
> See [sub-ghz](../capabilities/sub-ghz.md) · [nfc-rfid](../capabilities/nfc-rfid.md) · [community & video](./community-and-video.md). Part of the [KB](../README.md).

## Beginner — start here
- **Official user docs** — https://docs.flipper.net/zero — per-feature reference; also the best free per-radio "what is this" primer; active.
- **StationX Flipper Zero tutorial** — https://www.stationx.net/flipper-zero-tutorial/ — broad, beginner-friendly walkthrough of every mode.
- **InfoSec Writeups cheat-sheet** — https://infosecwriteups.com/the-ultimate-guide-cheatsheet-to-flipper-zero-d4c42d79d32c — dense one-page quick reference.
- **Flipper Zero Hacking 101** (pingywon) — https://flipper.pingywon.com — approachable hands-on intro site.
- **Per-capability primers (this KB)** — [sub-ghz](../capabilities/sub-ghz.md) · [nfc-rfid](../capabilities/nfc-rfid.md) · [infrared](../capabilities/infrared.md) · [ibutton](../capabilities/ibutton.md) · [badusb](../capabilities/badusb.md) · [rolling-codes](../theory/rolling-codes.md) — read alongside the official docs.

## Reference — when you need specifics
- **Developer docs** — https://developer.flipper.net — firmware/app/JS dev, hardware, **file formats** (`.sub`/`.nfc`/`.ir` structure); active.
- **Blog** — https://blog.flipper.net — official deep-dive explainers (Sub-GHz, NFC, VGM, releases).
- **Tech specs / schematics** — https://docs.flipper.net/zero/development/hardware/tech-specs · https://docs.flipper.net/zero/development/hardware/schematic — radios, MCU, pinout.
- **Recovering MIFARE Classic keys (mfkey32)** — https://docs.flipper.net/zero/nfc/mfkey32 — official how-to for the nonce→key attack the Flipper runs.
- **UberGuidoZ Playground** — https://github.com/UberGuidoZ/Flipper — sprawling reference dumps, notes, and links; active.
- **jamisonderek tutorials** — https://github.com/jamisonderek/flipper-zero-tutorials — code-along protocol/app walkthroughs; active.

## Deep-dive — RF & NFC fundamentals
### RF / modulation / encoding
- **AllAboutCircuits — Digital Modulation (ASK/FSK)** — https://www.allaboutcircuits.com/textbook/radio-frequency-analysis-design/radio-frequency-modulation/digital-modulation-amplitude-and-frequency/ — clean primer on the OOK/ASK/FSK the Sub-GHz chip uses.
- **GeeksforGeeks — ASK/FSK/PSK** — https://www.geeksforgeeks.org/electronics-engineering/digital-modulation-techniques/ — quick comparison of the keying schemes; good for "which modulation is this capture?".
- **EDN — Modulation basics (AM/FM)** — https://www.edn.com/modulation-basics-part-1-amplitude-and-frequency-modulation/ — concepts behind what the Flipper demodulates.
- Manchester / line coding: covered in the above; pairs with this KB's [rolling-codes](../theory/rolling-codes.md) for why captures look the way they do.

### NFC / MIFARE security (the real theory behind cloning)
- **Garcia et al., "A Practical Attack on the MIFARE Classic" (2008)** — https://link.springer.com/content/pdf/10.1007/978-3-540-85893-5_20.pdf — foundational CRYPTO1 weakness; basis of nested/mfkey attacks.
- **Garcia et al., "Wirelessly Pickpocketing a MIFARE Classic Card"** — https://www.researchgate.net/publication/220713937_Wirelessly_Pickpocketing_a_Mifare_Classic_Card — card-only key recovery, the attack class the Flipper automates.
- **Meijer & Verdult, "Ciphertext-only Cryptanalysis on Hardened MIFARE Classic" (CCS 2015)** — http://cs.ru.nl/~rverdult/Ciphertext-only_Cryptanalysis_on_Hardened_Mifare_Classic_Cards-CCS_2015.pdf — why "hardened" cards still fall (hardnested).
- **"Exploring the Real Capabilities of the Flipper Zero" (MDPI 2025)** — https://www.mdpi.com/2673-4591/123/1/6 — peer-reviewed scope of what the device can/can't actually do; good myth-check.

## Open questions / to research
- Find one authoritative KeeLoq / Security+ rolling-code write-up to anchor the Sub-GHz theory page.
- Confirm a current, non-paywalled NFC/FeliCa/DESFire primer for transit work (pairs with Metroflip).
- Locate a recorded conference talk (DEF CON / Hackaday) specifically on Flipper RF/NFC and verify the link before adding.
- Add a concise `.sub` and `.nfc` file-format cheat-sheet (or link the dev-docs section) for capture editing.
- Vet whether StationX / InfoSec Writeups pages are still current vs OFW UI changes.

## Sources
- https://docs.flipper.net/zero · https://developer.flipper.net · https://blog.flipper.net
- https://docs.flipper.net/zero/nfc/mfkey32
- https://link.springer.com/content/pdf/10.1007/978-3-540-85893-5_20.pdf · https://www.mdpi.com/2673-4591/123/1/6
- https://www.allaboutcircuits.com/textbook/radio-frequency-analysis-design/radio-frequency-modulation/digital-modulation-amplitude-and-frequency/
