---
title: NFC (HF) & RFID (LF) — Card Radios
domain: capabilities
type: reference
status: detailed
summary: Overview of the two card radios — LF 125 kHz RFID and HF 13.56 MHz NFC; deep dives live in cards/.
hardware: [flipper-internal]
use_cases: [UC-15, UC-16, UC-17, UC-18, UC-19, UC-20, UC-21, UC-22, UC-23, UC-61, UC-63]
related: [cards/nfc-theory.md, cards/mifare.md, cards/lf-125khz.md, cards/cloning-matrix.md, topics/security-pentest.md, capabilities/ibutton.md]
tags: [nfc, rfid, mifare, crypto1, lf-125khz, hf-13.56mhz, magic-cards, emv]
last_verified: 2026-06-19
---

# NFC (HF) & RFID (LF) — Card Radios

> **TL;DR —** The Flipper has two separate card radios sharing one antenna: LF 125 kHz RFID (EM4100/HID Prox/Indala, MCU-bit-banged, no auth) and HF 13.56 MHz NFC (ST25R3916, MIFARE/DESFire/NTAG/EMV). Overview of both stacks, the Crypto1 attack chain, magic-card clones, and when to reach for a Proxmark3; per-card deep dives live in cards/.
> See [hardware/README.md](../hardware/README.md), [ibutton.md](./ibutton.md), [security-pentest.md](../topics/security-pentest.md), [legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md).
> **🔬 Deep dive:** the [cards/](../cards/README.md) research folder — [NFC theory](../cards/nfc-theory.md) · [MIFARE](../cards/mifare.md) · [LF 125 kHz](../cards/lf-125khz.md) · [iCLASS/Picopass](../cards/iclass-picopass.md) · [cloning matrix](../cards/cloning-matrix.md).

The Flipper has **two completely separate card radios** sharing one antenna board. They run at different frequencies, use different silicon, and have nothing in common but the menu structure. Do not conflate "RFID" (LF) with "NFC" (HF).

| | **LF — 125 kHz RFID** | **HF — 13.56 MHz NFC** |
|---|---|---|
| App name | `125 kHz RFID` | `NFC` |
| Front-end | custom analog front-end, **MCU bit-bangs** the protocol (no dedicated reader chip) | dedicated **ST25R3916** NFC IC |
| Standards | proprietary per-vendor (no ISO umbrella) | ISO/IEC 14443A & 14443B, ISO/IEC 15693 (NFC-V), FeliCa (JIS X 6319-4) |
| Typical tags | EM4100/EM4102, HID Prox, Indala, AWID; T5577/EM4305 (writable) | MIFARE Classic/Ultralight/DESFire, NTAG21x, ISO15693, FeliCa, EMV bank cards |
| Range | a few cm (low-Q coil) | ~1–5 cm |
| Security floor | usually **none** — fixed ID, no auth | none → broken (Crypto1) → strong (DESFire AES) |
| Data | a short static ID | UID + memory blocks + (sometimes) crypto-protected sectors |
| Clone reality | trivial if reader trusts ID only | depends on card; UID-only readers trivial, crypto readers hard/impossible |
| Common uses | legacy building fobs, animal chips, hotel LF, gym tags | transit, modern access, payment (read-only), amiibo, NDEF tags |

Authorized-use framing: everything below is for **cards you own or are explicitly authorized to test** — backing up your own access fob, auditing your own building's credentials, learning protocol/crypto internals. Cloning or emulating credentials you don't control is covered in [legal-and-safety.md](../legal-and-safety.md); treat it as off-limits.

---

## LF — 125 kHz RFID

### How LF works on the Flipper (no chip)
There is **no dedicated 125 kHz reader IC**. The STM32WB55 MCU drives the LF coil and runs an analog front-end; the firmware *bit-bangs* the modulation in software. Consequences:

- **New LF protocols can be added by firmware update** (the demodulation is code, not silicon). CFW (Unleashed/Xtreme/Momentum) ships extra LF decoders the OFW lacks.
- **Read:** the coil energizes the tag; the tag load-modulates its ID back; the MCU samples and decodes (Manchester/biphase/PSK depending on protocol).
- **Emulate:** the MCU modulates the field to replay a saved ID — the Flipper *becomes the tag* to a reader.
- **Write:** for writable blanks (T5577/EM4305) the MCU sends the protocol's write/program command sequence over the field to burn config + data pages.

### LF protocols
| Protocol | Structure | Notes |
|---|---|---|
| **EM-Marin EM4100/EM4102** | 40-bit (5-byte) ID, Manchester | Most common in CIS/EU. No copy protection. Often only 3 bytes printed on the fob. |
| **HID Prox II (H10301 / "HID 26")** | 26-bit format: 8-bit **facility code** + 16-bit **card number** + 2 parity bits | The classic prox format. Flipper stores the raw bits; facility code + card number are derivable. Many other HID formats exist (35-bit Corporate 1000, etc.) with partial support. |
| **Indala (e.g. I40134)** | ~26–34 bit, PSK-modulated, proprietary | Motorola/HID legacy. Byte ordering varies by integrator — fields aren't always cleanly parseable. |
| **AWID** | 26-bit-style FSK | Supported on current firmware; another legacy access format. |
| **Others** | Pyramid, Keri, Jablotron, Paradox, Nexwatch, etc. | Varying support, broader on CFW. |

Because the ID is just bits, **a card's ID can be typed in manually** (RFID → Add Manually → pick protocol → enter ID) — no physical card needed to create an emulator.

### Writable clone targets
| Blank | Role |
|---|---|
| **T5577** | The universal LF clone target. Configurable to **emulate EM4100, HID Prox, or Indala** by programming its config block + data. This is what "RFID write" almost always targets. |
| **EM4305** | Rewritable EM-family chip (unlike read-only EM4100). Writable by Flipper. |
| **EM4100** | **Read-only** — cannot be (re)written; only cloned *to* a T5577/EM4305. |

Write flow: `125 kHz RFID → Saved → (pick card) → Write` → hold a blank T5577 to the back coil → firmware programs the config + ID.

### LF security reality
LF prox is **security theater**: a fixed ID transmitted with **no authentication, no encryption, no challenge-response**. Anyone who reads the field once has everything needed to clone. The "security" lives entirely in whether the building's reader/controller checks anything beyond the raw ID (it usually doesn't). Facility codes are *namespacing*, not secrets. Defensively, LF prox should be treated as a deprecated credential — migrate to HF DESFire/SEOS or seos-class smartcards.

---

## HF — 13.56 MHz NFC (ST25R3916)

The **ST25R3916** is a real NFC front-end IC supporting reader and card-emulation modes across ISO14443A/B, ISO15693 (NFC-V), and FeliCa. The Flipper rewrote its entire NFC stack around firmware **0.94+**, which is the dividing line for "modern" MIFARE Classic handling, parsers, and emulation quality. (Card-type *classification*, parsers, and attacks have expanded steadily since.)

### What the NFC app does
- **Read** → captures UID, SAK, ATQA, and (where keys/access allow) memory. Saved cards can be **renamed and emulated**.
- **Detect Reader / Extract MF Keys** → the Flipper emulates a card to a real reader and harvests Crypto1 nonces (mfkey32 path).
- **Add Manually** → build a virtual card by entering parameters.
- **NFC Magic** (separate app) → write UID / block 0 to "magic" cards for full clones.

### Card-type support overview
| Family | Standard | Flipper support today |
|---|---|---|
| **MIFARE Classic 1K/4K** | ISO14443A + Crypto1 | Full: read (with key recovery), dump, emulate, clone to magic. See attacks below. |
| **MIFARE Ultralight / NTAG21x** | ISO14443A | Read/write/emulate. NDEF read/write. Amiibo via **NTAG215**. Little/no auth (some have password/PWD pages). |
| **MIFARE DESFire EV1/EV2/EV3 / DESFire Light** | ISO14443A, AES/3DES | **Read metadata / app & file structure only.** AES keys not broken — no clone. |
| **NTAG / NFC Forum Type 2/5** | ISO14443A / ISO15693 | NDEF tags: read/write/emulate (URLs, Wi-Fi, vCard). |
| **ISO15693 (NFC-V)** | ISO15693 | Read; **emulation added** (NFC-V emulation landed in the modern stack / CFW). Vicinity tags, some ski-pass/library tags. |
| **FeliCa** | JIS X 6319-4 | Standard/Lite detection & read; emulation limited. Japanese transit/e-money are typically **read-only curiosities** (locked/online). |
| **EMV bank cards** | ISO14443-4A | Read **some public data only** (see below). **Cannot clone, cannot pay.** |

### MIFARE Classic + Crypto1: the attacks
Crypto1 is a broken 48-bit stream cipher; its weaknesses (short key, biased PRNG/nonces, parity leakage, known-keystream recovery) enable a layered attack chain. The Flipper runs these in order, escalating only as needed:

| Attack | Needs | Where it runs | What it does |
|---|---|---|---|
| **Dictionary** | nothing | on-device | Tries bundled + user key dictionaries against each sector. CFW ships much larger dictionaries. First thing tried on every read. |
| **mfkey32 / mfkey32v2** | the original **reader** | collect on-device (Extract MF Keys), crack on phone/PC/Flipper Lab or on-device `mfkey` app | Harvests Crypto1 nonce pairs the reader leaks during auth (up to ~10 pairs per session) → recovers the **reader's** sector keys. |
| **Nested / static nested** | **≥1 known key** on the card | collect on-device; static nested crackable in-app, full nested via PC `FlipperNestedRecovery` | Uses one known key to derive others by exploiting nonce structure. "Static" = card uses a fixed/predictable nonce. |
| **Hardnested** | a known key on a "hard" (proper-PRNG) card | collect nonces on-device → upload `.nested.log` to PC/web cracker → import found keys | For cards immune to classic nested. Compute-heavy; offloaded to a computer. |
| **KDF / "darkside"-class** | brand-specific | on-device plugins | Some manufacturers derive keys from UID (KDF) → instant. ("Darkside" historically recovered a first key from a card with *no* known key; on Flipper this niche is largely covered by big dictionaries + nested/hardnested + KDF.) (verify exact darkside availability per firmware) |

> Verify against your installed firmware: current OFW needs roughly **firmware ≥1.1.x + mfkey app ≥3.0** for the full nested/hardnested flow; CFW bundles it. Capability moves fast — check the changelog.

**Read → emulate flow (MIFARE Classic):**
1. `NFC → Read` — dictionary runs automatically; nested/hardnested nonces auto-collected if a key is found.
2. If sectors remain locked, do **Extract MF Keys** at the reader (mfkey32) and/or upload nonce logs for hardnested, then re-read.
3. With all keys, the card dumps fully and can be **emulated** — *but* many readers reject Flipper emulation due to **timing/UID specifics**, which is why a **magic card clone is often the reliable path** for a genuine duplicate.

### Magic cards (full UID / block-0 clones)
Standard MIFARE Classic has a **locked block 0** (UID is read-only). "Magic" cards expose backdoors to rewrite it, enabling true UID clones. Use the **NFC Magic** app:

| Magic type | Capability |
|---|---|
| **Gen1a (Gen1B)** | Backdoor commands; write UID + all blocks. 4-byte UID. The classic "Chinese magic" card. OTP variants exist. |
| **Gen2 / CUID / FUID / UFUID** | **DirectWrite** to block 0 via normal write after auth (no backdoor command). CUID = rewritable repeatedly; (U)FUID can be locked to look like a genuine card. 4- and 7-byte UID variants. (Some Gen2 CUID report UID-write quirks on certain firmware — verify.) |
| **Gen4 / "Ultimate" (GTU)** | Highly configurable shapeshifter (emulates many types, 7-byte UID, etc.). Premium. |

NFC Magic supports MIFARE Classic 1K/4K Gen1A/Gen1B (incl. OTP) and Gen2 DirectWrite/CUID/FUID/UFUID. After cloning UID+data to a magic card, it behaves as a genuine card to UID-and-crypto readers (assuming keys were recovered).

### UID-only vs full emulation
A critical distinction for what actually opens a door:
- **UID-only readers** (lots of cheap access systems) check just the 4/7-byte UID → trivially defeated by emulation **or** any magic-card UID clone.
- **Full-content / crypto readers** (proper MIFARE Classic, DESFire) require correct sector data and **live crypto** → need recovered keys (Classic) or are infeasible (DESFire AES).

### EMV bank cards
Flipper detects EMV (ISO14443-4A) and can read **some public data** (PAN, expiry, sometimes a transaction log) exposed by the contactless app. It **cannot**: read the CVV, extract private keys, generate valid cryptograms, clone the card, or make a payment. EMV's per-transaction cryptogram (CDA/DDA) defeats replay. Treat Flipper EMV reading as a **privacy demonstration**, not an attack. (EMV parser depth has varied across OFW/CFW versions — verify on yours.)

---

## Where Proxmark3 is the better tool
The Flipper is a brilliant **field** NFC/RFID tool; the **Proxmark3** is the **lab/research** tool. Reach for a Proxmark when you need:

| Need | Why Proxmark |
|---|---|
| Raw protocol / sniffing | Sniff full reader↔card exchanges, replay arbitrary frames, low-level timing control. |
| Exotic LF formats | Far broader LF decoder/encoder coverage and tuning (odd HID/Indala/Nexwatch variants). |
| Heavier Crypto1 / iClass / Hitag | Mature darkside/nested/hardnested + **HID iClass / SEOS** and Hitag tooling Flipper lacks. |
| Antenna tuning & autopwn | Adjustable antennas, `hf mf autopwn`, scripting. |
| New/obscure card research | Active research community, deepest tooling. |

Rule of thumb: **Flipper for read/clone/emulate of common credentials in the field; Proxmark3 when the card fights back or is exotic.** Cross-reference [security-pentest.md](../topics/security-pentest.md).

---

## Tools & ecosystem
- On-device **NFC** + **125 kHz RFID** apps; **NFC Magic** for clones; **mfkey** for on-device cracking.
- **Flipper Lab** (lab.flipper.net) and the mobile app for nonce cracking / key recovery off-device.
- Large MIFARE key **dictionaries** bundled in CFW.
- amiibo: [FlipperAmiibo](https://github.com/Gioman101/FlipperAmiibo); Tonies: [flipper-zero-tonies](https://github.com/nortakales/flipper-zero-tonies).
- Defensive auditing app: [flipper-access-audit](https://github.com/matthewkayne/flipper-access-audit).

## Open questions / to research
- Exact darkside availability and whether it's exposed in current Unleashed/Momentum vs subsumed by dictionaries+KDF.
- Current OFW vs CFW deltas for **ISO15693/FeliCa emulation** depth (which sub-types actually emulate).
- Which Gen2 **CUID/UFUID** variants reliably accept block-0 writes on the latest firmware (reported quirks).
- DESFire: how much app/file *metadata* the modern parser exposes without keys.
- EMV parser status on current OFW/CFW (what public fields are read now).
- Full list of LF formats CFW decodes beyond EM/HID/Indala/AWID (Keri, Nexwatch, Paradox, etc.).

## Sources
- NFC docs: https://docs.flipper.net/zero/nfc · Read: https://docs.flipper.net/zero/nfc/read
- mfkey32: https://docs.flipper.net/zero/nfc/mfkey32 · Magic cards: https://docs.flipper.net/zero/nfc/magic-cards
- RFID docs: https://docs.flipper.net/zero/rfid · Write T5577: https://docs.flipper.net/zero/rfid/write-data · Add manually: https://docs.flipper.net/zero/rfid/add-manually
- Blog (RFID deep dive): https://blog.flipper.net/rfid/
- Flipper Community Wiki — MIFARE Classic: https://flipper.wiki/mifareclassic/
- MIFARE Classic attack notes (noproto): https://gist.github.com/noproto/63f5dea3f77cae4393a4aa90fc8ef427
- FlipperNested: https://github.com/AloneLiberty/FlipperNested
- ISO15693/NFC-V support write-up: https://www.g3gg0.de/reversing/flipper-zero-got-iso15693-nfc-v-support/
- NFC file format (developer docs): https://developer.flipper.net/flipperzero/doxygen/nfc_file_format.html
