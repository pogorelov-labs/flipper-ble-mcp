---
title: NFC & RFID — Theory
domain: cards
type: reference
status: detailed
summary: RFID/NFC physics + ISO 14443/15693/18092 protocols
hardware: [flipper-internal]
use_cases: []
related: [cards/README.md, cards/mifare.md, cards/lf-125khz.md, cards/iclass-picopass.md, capabilities/nfc-rfid.md]
tags: [nfc, rfid, iso-14443, iso-15693, iso-18092, inductive-coupling, security-tiers]
last_verified: 2026-06-19
---

# NFC & RFID — Theory

> **TL;DR —** Foundational theory for the cards folder: near-field physics, the ISO 14443/15693/18092 HF standards, LF signaling, UID/anticollision, the Flipper HF/LF stack, and the security-tier model.
> Part of the [Cards hub](README.md) · [KB](../README.md). See also [MIFARE](./mifare.md) · [LF 125 kHz](./lf-125khz.md) · [iCLASS/PicoPass](./iclass-picopass.md) · [Cloning matrix](./cloning-matrix.md) · capability page [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md) · hardware [../hardware/README.md](../hardware/README.md).

This is the **foundational theory doc** for everything in `cards/`. It explains *how the radio works* and *what the standards specify*, so the per-family docs ([mifare](./mifare.md), [lf-125khz](./lf-125khz.md), [iclass-picopass](./iclass-picopass.md)) can focus on the specifics of each chip. Educational/defensive framing — understand these systems to assess and secure them, not to abuse them ([legal & safety](../legal-and-safety.md)).

---

## 1. Terminology & frequency bands

**RFID** (Radio-Frequency Identification) is the umbrella term: any system where a *reader* powers and queries a *transponder* (tag) over a radio link. **NFC** (Near-Field Communication) is a *subset* of HF RFID — a family of 13.56 MHz standards (ISO/IEC 14443, 15693, 18092) curated by the NFC Forum, with the extra ability for two active devices to talk **peer-to-peer**. Put simply: **all NFC is RFID, but most RFID is not NFC.** LF 125 kHz "RFID" and HF 13.56 MHz "NFC" are different physical layers and the Flipper drives them with **separate hardware paths** (see §6).

| Band | Freq | Typical range | Coupling | Examples | Flipper? |
|------|------|---------------|----------|----------|----------|
| **LF** | 125 kHz (also 134.2 kHz for animal ISO FDX-B/HDX) | ~1–10 cm (up to ~1 m industrial) | Inductive (near-field) | EM4100, HID Prox, Indala, T5577, animal chips | ✅ read/emulate/write |
| **HF** | 13.56 MHz | ~1–10 cm | Inductive (near-field) | MIFARE, NTAG, DESFire, iCLASS, FeliCa, ICODE, EMV, e-passports | ✅ (varies by tier) |
| **UHF** | 860–960 MHz | 1–12 m | **Far-field** (backscatter) | EPC Gen2 inventory tags, retail, logistics | ❌ out of scope |

UHF is a fundamentally different physics regime (radiative far-field backscatter, not magnetic coupling) and the Flipper has no UHF radio — ignore it for this KB.

---

## 2. Physics — near-field inductive coupling

LF and HF RFID both rely on **inductive (transformer-like) coupling** in the radio **near field**. The reader drives an AC current through an antenna coil, producing an oscillating *magnetic* field. A passive tag's coil sits inside that field and, by Faraday's law, has a voltage induced across it.

- **Powering the tag.** The tag has no battery. Induced AC is rectified on-chip into DC to run its logic — the reader's field *is* the tag's power supply. Cut the field and the tag dies instantly. The tag's resonant tank (coil L + capacitor C) is tuned to the carrier so it harvests maximum energy at resonance.
- **Tag → reader reply = load modulation.** The tag cannot transmit its own carrier (no power budget for that). Instead it **modulates the load** on its coil — switching a transistor across the coil to change how much energy it draws. Because the two coils are coupled, that load change is reflected back as a tiny amplitude/phase perturbation on the reader's own carrier, which the reader detects. This is **load modulation** (a.k.a. backscatter-by-loading), the defining trick of passive near-field RFID.
- **Carrier + subcarrier.** To lift the weak reply out of the reader's huge carrier, the tag usually switches its load at a **subcarrier** frequency = carrier ÷ 16. At 13.56 MHz that subcarrier is **847.5 kHz** (13.56 MHz / 16); the actual data then modulates this subcarrier. ISO 15693 uses subcarrier(s) at **423.75 kHz** (fc/32) and optionally **484.28 kHz**.
- **Antenna, Q, coupling distance.** Range is governed by mutual inductance, which falls off steeply (~1/d³ for the field strength a small loop sees). A high **Q** (quality factor) antenna couples more energy and reads further but has narrower bandwidth (it rings); designers trade Q against data bandwidth. The reader must deliver enough field at the tag *and* be sensitive enough to see the load-modulation echo — both degrade fast with distance and misalignment.
- **Why LF range is short** despite low frequency: a 125 kHz wavelength is ~2.4 km, so you are *always* deep in the near field, and coupling depends on coil geometry/overlap rather than radiated power. Small coils + low induced power + simple analog detection ⇒ a few centimetres in practice. HF (13.56 MHz, λ ≈ 22 m) is similar in range but supports far higher data rates and on-tag compute.

---

## 3. LF signaling (125 kHz)

LF tags are deliberately **simple**. Most are "dumb": when energized they **clock out a fixed bit pattern** (their ID) over and over, with no challenge/response, no state, often no write protection. The reader recovers the ID purely by demodulating the load-modulation pattern.

- **Modulations:** **ASK** (Amplitude-Shift Keying — the common case, e.g. EM4100), **FSK** (Frequency-Shift Keying — e.g. HID Prox swaps between two field divisors), and **PSK** (Phase-Shift Keying — e.g. Indala, some T5577 configs). Flipper documents the HF/LF analog front-end as **AM / OOK** with **ASK / PSK** coding; while reading it *cycles reader protocols/modulations in a loop* to auto-detect the card.
- **Line coding:** bits are usually carried as **Manchester** or **biphase (differential Manchester)** transitions, which are self-clocking (a guaranteed mid-bit edge lets the reader recover bit timing from the load-modulation envelope without a separate clock).
- **Why "dumb" matters for security:** a static, freely-readable ID with no crypto means *whoever reads it can replay it*. This is why LF access cards are trivially cloneable to a writable **T5577** — the whole "secret" is a number the card shouts to anyone who asks. Detail in [lf-125khz.md](./lf-125khz.md); cross-tech comparison in [cloning-matrix.md](./cloning-matrix.md).

---

## 4. HF standards (13.56 MHz) in depth

### 4.1 ISO/IEC 14443 — proximity cards (NFC-A / NFC-B)

The dominant HF access/payment standard, range ~10 cm ("proximity"). Two incompatible physical layers share the band:

| | **Type A** | **Type B** |
|---|---|---|
| Reader→card modulation | **100% ASK** (carrier fully gated off in pauses) | **10% ASK** (shallow amplitude dips) |
| Reader→card bit coding | **Modified Miller** (pulse-position pauses) | **NRZ** |
| Card→reader | OOK on **847.5 kHz** subcarrier, **Manchester** | BPSK on subcarrier, **NRZ-L** |
| Anticollision | Bitwise, deterministic (binary search on UID) | Slotted-ALOHA (probabilistic, slot markers) |
| Famous users | MIFARE family, NTAG, most access cards | German eID, some passports/banking |

Bit rates start at **fc/128 = 106 kbit/s** and scale to **212, 424, 848 kbit/s** (fc/64, /32, /16). Both types share the higher-layer **ISO 14443-4** (T=CL) transport for smartcards (APDUs), used by DESFire, EMV, passports.

**Important framing distinction:** **MIFARE Classic** is NXP-proprietary and rides only on ISO 14443-**A** layer 3 — it does **not** implement the 14443-4 transport; instead it bolts a proprietary security/command layer (Crypto1) onto the anticollision layer. So "ISO 14443-A compliant" ≠ "MIFARE". See [mifare.md](./mifare.md).

### 4.2 UID, anticollision & cascade levels (Type A)

When a card enters the field the reader runs **REQA → ATQA → anticollision → SELECT → SAK**:

- **ATQA** (Answer To Request, type A): 2 bytes hinting UID size and that bitwise anticollision is supported.
- **Anticollision:** if multiple cards answer, the reader walks the UID bit-by-bit (deterministic binary tree) until one full UID is isolated — then `SELECT`s it. Collisions are resolved by which bit position differs.
- **SAK** (Select AcKnowledge): 1 byte telling the reader the card's type/capabilities (e.g. "UID complete", "ISO 14443-4 compliant", "MIFARE Classic 1K").
- **BCC:** a Block Check Character = XOR of the 4 UID bytes of that cascade level, for integrity.

**UID sizes use cascade levels (CL):**

| UID size | Cascade levels | SELECT commands | Notes |
|----------|----------------|-----------------|-------|
| **4 bytes** ("single") | CL1 | `0x93` | Classic 1K/4K, many legacy tags. First byte (UID0) **must not be `0x88`** |
| **7 bytes** ("double") | CL1 + CL2 | `0x93`, `0x95` | NTAG, Ultralight, DESFire, modern cards |
| **10 bytes** ("triple") | CL1+CL2+CL3 | `0x93`,`0x95`,`0x97` | Rare |

The byte **`0x88` is the "cascade tag"**: in any non-final cascade level the first transmitted byte is `0x88`, signalling "more UID bytes follow in the next level." That is why a real 4-byte UID can never *start* with `0x88` (it would be mistaken for a cascade indicator).

**Random / non-unique UIDs:** privacy-oriented cards (some DESFire, phones in card-emulation mode, modern transit) emit a **random UID** beginning with **`0x08`** each tap, so the static UID can't be used to track you. This breaks any clone-by-UID scheme — the "identity" is established later by cryptographic application data, not the UID. **"Magic" cards** invert this: they expose a *writable* UID (including block 0 on gen1a/gen2 magic Classic), which is what makes UID cloning possible — see [cloning-matrix.md](./cloning-matrix.md).

### 4.3 ISO/IEC 15693 — vicinity cards (NFC-V)

"Vicinity" tags: lower coupling requirements ⇒ **longer range** (tens of cm, up to ~1 m with a big reader antenna) at the cost of **lower data rate**. Subcarrier at **423.75 kHz** (single) or dual 423.75/484.28 kHz; data rates roughly **~6.6 kbit/s (low)** and **~26 kbit/s (high)**. Examples: NXP **ICODE**, ST **ST25TV**, many library/laundry/ski-pass tags. Mapped to **NFC Forum Type 5**. Flipper reads ISO 15693 UID (and ICODE-class tags with firmware support); see capability page.

### 4.4 ISO/IEC 18092 — NFC-F / FeliCa

Sony **FeliCa**, dominant in Japan (Suica transit, Edy, many e-money). 13.56 MHz, **Manchester** coding, **no subcarrier** (symmetric reader/tag signalling), data rates **212 and 424 kbit/s**. Identified by an **IDm/PMm** rather than an ISO-14443 UID. Mapped to **NFC Forum Type 3**. Flipper can read a FeliCa UID/IDm; full ticketing crypto is out of reach (see security tiers, §7).

### 4.5 NDEF and NFC Forum tag types

**NDEF** (NFC Data Exchange Format) is the NFC Forum's *application-layer* data container — a TLV/record format for "this tag holds a URL / text / Wi-Fi config / contact." It is **orthogonal to the physical layer**: the same NDEF message can live on any of the five tag types, so phones treat them interchangeably.

| NFC Forum type | Underlying tech | Representative chip |
|----------------|-----------------|---------------------|
| **Type 1** | ISO 14443-A (Topaz) | Innovision/Broadcom Topaz 512 |
| **Type 2** | ISO 14443-A | NXP **NTAG** 21x, MIFARE **Ultralight** |
| **Type 3** | ISO 18092 / JIS X 6319-4 (FeliCa) | Sony **FeliCa Lite-S** |
| **Type 4** | ISO 14443-A **or** B + ISO 7816 APDUs | DESFire, smartcard ICs |
| **Type 5** | ISO 15693 | NXP **ICODE**, ST **ST25TV** |

Key insight: a tag's **physical standard** (how it talks) is separate from whether it carries **NDEF** (what data convention it uses). Access/transit cards usually do *not* use NDEF — they use proprietary or 7816 application data with crypto.

---

## 5. Operating modes — reader vs card vs peer

NFC/RFID roles, with the standards' terminology:

- **Reader / PCD** (Proximity Coupling Device): generates the field and initiates. *Flipper acting as a reader* powers the tag and runs the protocol to read/identify it.
- **Card / PICC** (Proximity *Card*): the passive transponder that answers via load modulation. *Flipper acting as an emulated card* uses its front-end in **listen/target mode** to *be* a card to an external reader.
- **Peer-to-peer:** two powered devices alternate roles (ISO 18092 active mode / NFC-DEP). Phones do this; it's largely irrelevant to access-card workflows and the Flipper does not focus on it.

**Limits of emulation — the crucial caveat.** Flipper can faithfully emulate **what it knows**:
- For a *plain-ID* card it can present the saved **UID/SAK/ATQA** and any stored static data — enough to fool readers that only check the UID.
- For a *cryptographic* card it can only replay the **state it has captured**. If you never recovered the sector keys / application keys, the Flipper holds an incomplete card and **cannot answer a fresh cryptographic challenge** — it has the UID but not the live secret. This is why "I read the card" ≠ "I cloned the card" for MIFARE Classic (needs keys via MFKey32/nested), DESFire (AES — generally infeasible), iCLASS, FeliCa, and EMV. The per-family docs spell out exactly what is and isn't recoverable.

Per Flipper's own docs, **bank cards (EMV)** are read **UID/SAK/ATQA only, not saved**; **unknown Type A** cards can be read (UID/SAK/ATQA) **and emulated by UID**; **Type B/F/V** are **UID-read only**. That maps directly onto the tier model in §7.

---

## 6. The Flipper NFC/RFID stack (hardware vs firmware)

Two distinct front-ends share one dual-band antenna; understanding the split explains *why* some things are hardware-impossible and others are just firmware features. Hardware detail in [../hardware/README.md](../hardware/README.md).

| Path | Front-end | Driven by | Consequence |
|------|-----------|-----------|-------------|
| **HF 13.56 MHz** | **ST25R3916** dedicated NFC transceiver | Hardware does framing/anticollision/modulation; firmware does protocol logic | Handles ISO 14443-A/B, 15693, FeliCa, in **reader and card-emulation** modes natively |
| **LF 125 kHz** | **No dedicated LF chip** — passive analog path + comparator | **STM32WB55 MCU** bit-bangs/samples the field directly | Modulation/decoding is *software-defined*; flexible but CPU-bound |

- **MCU:** STM32WB55RG — Cortex-M4 @ 64 MHz (apps) + Cortex-M0+ @ 32 MHz (radio), 1 MB flash / 256 KB SRAM (shared).
- **HF (ST25R3916):** the chip natively supports the popular NFC protocols (ISO 14443A/B, ISO 15693, FeliCa) in both read and emulate modes. Per Flipper's tech specs the supported card families include **ISO 14443A/B, NXP MIFARE Classic/Ultralight/DESFire, FeliCa, HID iCLASS (PicoPass)** plus NFC Forum types. What's *hardware-limited*: the chip defines the achievable modulations/timing. What's *firmware-limited*: which higher-layer protocols and attacks are implemented (e.g. Crypto1 key recovery, DESFire commands).
- **LF (MCU-driven):** because there is **no LF ASIC**, the 125 kHz reader/emulator is entirely firmware — the MCU generates the 125 kHz carrier and samples load-modulation, switching reader protocols in a loop to identify EM4100 / HID / Indala / etc. This is *why* the LF protocol list grows via firmware updates and why exotic LF cards can sometimes be added in software. Listed LF families: EM4100, HID H10301, Indala 26, IoProx, AWID, ISO FDX-B / FDX-A animal, Paradox, Keri, Gallagher, Nexwatch, and others.
- **Emulation limits are mostly firmware + secrets, not radio:** the ST25R3916 *can* be a card; whether emulation is *useful* depends on whether firmware implements the protocol and whether you captured the crypto state (§5).

---

## 7. Security-tier overview (the lens for every per-family doc)

Read each card family by *where it sits on this ladder*. This is the single most useful mental model in the KB.

| Tier | What protects it | Read? | Clone/emulate? | Examples | KB doc |
|------|------------------|-------|----------------|----------|--------|
| **0 — Plain ID** | Nothing; static number, freely read | ✅ trivial | ✅ trivial (replay / T5577 / magic UID) | LF EM4100, HID Prox, Indala; bare UID-only HF use | [lf-125khz](./lf-125khz.md), [cloning-matrix](./cloning-matrix.md) |
| **1 — Broken crypto** | Proprietary cipher, since defeated | ✅ with attack | ✅ once keys recovered | **MIFARE Classic (Crypto1, 48-bit LFSR — broken)**, legacy iCLASS | [mifare](./mifare.md), [iclass-picopass](./iclass-picopass.md) |
| **2 — Strong/standard crypto** | AES/3DES, proper key mgmt | ✅ UID only | ❌ generally infeasible | MIFARE DESFire (AES), Ultralight C (3DES), iCLASS SE/SR, FeliCa, EMV | per-family + capability page |

- **Tier 0** is pure replay: the secret is the ID itself. Defensive takeaway: never use bare-UID auth for anything that matters.
- **Tier 1 — why Crypto1 fell:** MIFARE Classic uses **Crypto1**, a 48-bit LFSR stream cipher with a weak nonlinear filter, kept secret ("security by obscurity"). After reverse-engineering, **nested** and **darkside** attacks dropped key recovery from 2⁴⁸ brute force to ~2³⁰ — minutes on a laptop, or seconds given one known key. The Flipper implements the practical capture side (e.g. **MFKey32** from sniffed reader auth, dictionary/nested key recovery). NXP itself now recommends migrating *off* MIFARE Classic. Full mechanics in [mifare.md](./mifare.md).
- **Tier 2** is where the Flipper stops at "read the UID": AES/3DES with live challenge-response means capturing a trace gives you nothing replayable; you'd need the key, which the scheme is *designed* to never expose. EMV adds dynamic per-transaction cryptograms on top.

The progression **plain ID → broken crypto → AES** is exactly the order in which a defender should *upgrade* their access control, and the order in which an auditor should *expect* each system to fail.

---

## Open questions / to research
- Confirm exact Flipper firmware behaviour for **ISO 15693 ICODE** read/emulate vs UID-only, and whether SLIX passwords are handled (verify).
- Does the official build expose any **FeliCa** beyond IDm/PMm read (service/block reads)? (verify)
- Precise **ST25R3916 vs ST25R3916B** revision used across hardware batches and any capability delta (verify).
- LF **134.2 kHz** animal-tag (FDX-B/HDX) read support details and whether emulation is supported, not just read (verify).
- Real-world **read-range** envelope (cm) for LF vs HF on stock Flipper antenna vs with add-on antennas — quantify for the hardware doc.
- Status of **"hardened" MIFARE Classic EV1** vs current Flipper attack tooling (which nonce-based attacks still work) (verify).

## Sources
- Flipper NFC docs — https://docs.flipper.net/zero/nfc
- Flipper 125 kHz RFID docs — https://docs.flipper.net/zero/rfid
- Flipper tech specs (MCU, ST25R3916, supported card lists) — https://docs.flipper.net/zero/development/hardware/tech-specs
- Flipper blog, "Diving into RFID Protocols" — https://blog.flipper.net/rfid/
- ISO/IEC 14443-3 anticollision (cascade levels, BCC, 0x88) — https://community.nxp.com/pwmxy87654/attachments/pwmxy87654/nfc/4928/1/ISO-IEC%2014443-3_anticollision.pdf
- NXP AN10927, "MIFARE product and handling of UIDs" — https://www.nxp.com/docs/en/application-note/AN10927.pdf
- ISO 14443 Type A vs B modulation overview — https://www.rfidcard.com/iso-iec-14443-type-a-vs-type-b-whats-the-difference-and-how-to-choose/
- HF RFID standards guide (14443/15693/18092/NFC) — https://syncotek.com/hf-rfid-standards/
- Sony FeliCa system overview (212/424 kbps, Manchester) — https://www.sony.net/Products/felica/about/scheme.html
- NFC Forum tag types 1–5 mapping — https://www.rfidcard.com/nfc-forum-tag-types/
- ISO 15693 / NFC-V overview — https://www.rfidcard.com/what-is-iso-15693-iso-15693-standard-for-nfc-tags/
- Crypto-1 cipher & attacks (Wikipedia summary) — https://en.wikipedia.org/wiki/Crypto-1
- Proxmark3 RRG/Iceman — MIFARE Classic — https://deepwiki.com/RfidResearchGroup/proxmark3/3.2-mifare-classic
