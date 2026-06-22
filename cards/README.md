---
title: Cards, NFC & RFID — Research Hub
domain: cards
type: hub
status: detailed
summary: Hub: card taxonomy, security tiers, and the cards doc index
hardware: [flipper-internal]
use_cases: [UC-15, UC-16, UC-17, UC-18, UC-19, UC-20, UC-21, UC-22, UC-23]
related: [capabilities/nfc-rfid.md, cards/nfc-theory.md, cards/mifare.md, cards/cloning-matrix.md, capabilities/ibutton.md]
tags: [nfc, rfid, cards, taxonomy, security-tiers, hub]
last_verified: 2026-06-19
---

# Cards, NFC & RFID — Research Hub

> **TL;DR —** The deep-research hub for the Flipper's two card radios: a card-technology taxonomy, the plain-ID→broken-crypto→AES security-tier model, and the index to the per-family and cloning docs.
> Feature/how-to summary lives in [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md); this folder is the **theory + per-family + cloning** depth. Part of the [KB](../README.md).

This folder is the deep dive behind the Flipper's two card radios. The capability file answers
*"what can the Flipper do with cards?"*; these docs answer *"how do these card technologies actually
work, and what's really cloneable?"* — authorized/own-card use only ([legal-and-safety](../legal-and-safety.md)).

## Card technology taxonomy

| Band | Standard | Examples | Security tier | Flipper support |
|---|---|---|---|---|
| **125 kHz LF** | EM/HID/Indala proprietary | EM4100, HID Prox, Indala, AWID; **T5577/EM4305** (blanks) | ⚪ static ID, **no auth** | read · emulate · **write/clone** |
| **13.56 MHz HF** ISO 14443A | NXP **MIFARE** | Classic, Ultralight/NTAG, DESFire, Plus | ⚪→🟠 **Crypto1 (broken)**→🟢 **AES** | varies by type |
| **13.56 MHz HF** ISO 15693 | HID **iCLASS** / Picopass, NFC-V | iCLASS legacy / **SE / SEOS** | 🟠 legacy weak → 🟢 SEOS strong | PicoPass app (legacy) |
| **13.56 MHz HF** ISO 18092 (NFC-F) | Sony **FeliCa** | transit (JP), Amiibo uses NTAG | proprietary | limited read |
| **13.56 MHz HF** | **EMV** (ISO 7816/14443) | Visa/Mastercard contactless | 🟢 strong | read public metadata only |
| **860–960 MHz UHF** | EPC Gen2 | retail/inventory tags | n/a | ❌ not supported |

**Security tiers:** ⚪ *plain ID* (just a number, trivially cloned) → 🟠 *broken crypto* (Crypto1 / iCLASS
legacy — recoverable) → 🟢 *modern crypto* (AES: DESFire EV1+, iCLASS SEOS, EMV — **not** broken).
The whole game is identifying which tier a card is in.

## Docs in this folder
| Doc | What's in it |
|---|---|
| [nfc-theory.md](nfc-theory.md) | RFID/NFC physics + protocols: LF vs HF coupling, ISO 14443/15693/18092, UID/anticollision, reader vs emulation |
| [mifare.md](mifare.md) | MIFARE family deep dive: Classic memory map + Crypto1 attacks, Ultralight/NTAG, DESFire, Plus |
| [lf-125khz.md](lf-125khz.md) | LF cards: EM4100/HID Prox/Indala/AWID + T5577 cloning |
| [iclass-picopass.md](iclass-picopass.md) | HID iCLASS / Picopass: legacy vs SE/SEOS, the PicoPass app |
| [cloning-matrix.md](cloning-matrix.md) | **Practical cloning reference**: what's cloneable + how + magic cards + blanks shopping list |

## Related
- Feature summary + Flipper workflow: [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md)
- Card use-cases on my rig: [../my-use-cases.md](../my-use-cases.md) (UC-15..23) · pentest framing: [../topics/security-pentest.md](../topics/security-pentest.md)
- Contact keys (not RFID): [../capabilities/ibutton.md](../capabilities/ibutton.md)

## Open questions / to research
- Which exact MIFARE Classic attacks the current Momentum NFC app exposes (and speed on hardened cards).
- iCLASS SE/SEOS practical boundary on Flipper vs Proxmark3.
- Per-region transit card support in Metroflip.

## Sources
- Flipper NFC: https://docs.flipper.net/zero/nfc · RFID 125 kHz: https://docs.flipper.net/zero/rfid
- Proxmark3 (RRG/Iceman) wiki: https://github.com/RfidResearchGroup/proxmark3
- NXP MIFARE: https://www.nxp.com/products/rfid-nfc/mifare-hf
