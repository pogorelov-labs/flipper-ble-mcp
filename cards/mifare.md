---
title: MIFARE Family — Deep Dive
domain: cards
type: reference
status: detailed
summary: MIFARE Classic/Ultralight/NTAG/DESFire + Crypto1 attacks
hardware: [flipper-internal]
use_cases: []
related: [cards/nfc-theory.md, cards/cloning-matrix.md, cards/README.md, capabilities/nfc-rfid.md, cards/iclass-picopass.md]
tags: [mifare, crypto1, classic, ultralight, ntag, desfire, mfkey32, nested]
last_verified: 2026-06-19
---

# MIFARE Family — Deep Dive

> **TL;DR —** NXP MIFARE deep dive: Classic memory map and the broken Crypto1 cipher + key-recovery attacks (dictionary/mfkey32/nested/hardnested), Ultralight/NTAG, and the AES wall of DESFire/Plus — with what the Flipper can and can't do per type.
> Theory: [./nfc-theory.md](nfc-theory.md) · clone targets: [./cloning-matrix.md](cloning-matrix.md) · feature summary: [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md). Part of the [Cards hub](README.md) · [KB](../README.md).

**MIFARE** is NXP's brand for 13.56 MHz contactless ICs built on **ISO/IEC 14443 Type A**. It is the single most deployed access/transit/ticketing card family on Earth (billions of units), which is exactly why it matters here: the legacy **Classic** line uses the broken **Crypto1** cipher, so a card you own can be read, key-recovered, dumped, and emulated/cloned on a Flipper. The modern line (**DESFire EV1+**, **Plus SL3**) uses **AES-128** and is **not broken** — the Flipper can enumerate its structure but cannot defeat its crypto. The whole skill is telling those two worlds apart. Defensive/own-card framing throughout; see [../legal-and-safety.md](../legal-and-safety.md).

---

## 1. Family overview

| Sub-family | Representative ICs | ISO 14443A layer | User memory | Crypto | Typical use | Flipper support |
|---|---|---|---|---|---|---|
| **Classic Mini** | MF1ICS20 | -3 (T=CL not used) | 320 B (5 sectors) | Crypto1 48-bit | legacy access | full read→recover→emulate/clone |
| **Classic 1K** | MF1S50 / EV1 | -3 | 1 KB (16 sectors) | Crypto1 | access, hotel, old transit | full |
| **Classic 4K** | MF1S70 / EV1 | -3 | 4 KB (40 sectors) | Crypto1 | access, transit | full |
| **Ultralight** | MF0ICU1 | -3 | 48 B (16 pages) | **none** (plain) | disposable tickets | read + emulate + clone |
| **Ultralight C** | MF0ICU2 | -3 | 144 B | **3DES** auth | tickets w/ auth | read structure; 3DES not broken |
| **Ultralight EV1** | MF0UL11/21 | -3 | 48 B / 128 B | 32-bit **PWD/PACK**, ECC sig | transit, events | read + emulate (sig not forgeable) |
| **NTAG213/215/216** | NT2H13/15/16 | -3 (NFC Forum T2T) | 144 / 504 / 888 B | 32-bit PWD/PACK, ECC sig | NFC tags, **amiibo (215)** | read + emulate + clone-to-magic |
| **DESFire EV1** | MF3ICD41 | **-4 (T=CL)** | 2/4/8 KB | **AES-128 / 3DES / 3K3DES** | transit, gov ID, enterprise | read metadata only; **not broken** |
| **DESFire EV2** | MF3D(H)x2 | -4 | 2/4/8 KB | AES-128 (+ proximity check) | secure access/transit | read metadata only |
| **DESFire EV3** | MF3D(H)x3 | -4 | 2/4/8 KB | AES-128, EAL5+ | latest enterprise/transit | read metadata only |
| **Plus (S/X/SE/EV1/EV2)** | MF1P(H)x2 etc. | -3 (SL1) / -4 (SL3) | 2/4 KB | Crypto1 (SL1) → **AES** (SL3) | Classic→AES migration | depends on SL (see §7) |
| **SmartMX / JCOP** | P5/P6, NTAG-on-SmartMX | -4 | varies | full SE (AES/RSA/ECC, JavaCard) | EMV, eID, DESFire-as-applet | read public metadata only |

> "Flipper support" = OFW (Official Firmware, 1.x NFC stack) and **Momentum** CFW, which adds extra dictionaries, plugins, and the on-device mfkey/nested apps. `(verify)` exact app availability against your installed firmware — these move fast.

---

## 2. MIFARE Classic architecture

### Memory layout
- **1K** = 16 sectors × 4 blocks × 16 bytes = 1024 B. Sectors 0–15, each with **3 data blocks + 1 sector trailer**.
- **4K** = 32 sectors of 4 blocks (like 1K) **+ 8 sectors of 16 blocks** (15 data + 1 trailer). 40 sectors total, 3072 + 1024 = 4096 B.
- **Mini** = 5 sectors (same 4-block layout).
- Addressing is **block-linear**; the last block of every sector is its trailer.

```
MIFARE Classic 1K — memory map
┌────────┬───────┬─────────────────────────────────────────────┐
│ Sector │ Block │ Contents                                     │
├────────┼───────┼─────────────────────────────────────────────┤
│   0    │   0   │ MANUFACTURER: UID(4) BCC(1) SAK(1) ATQA(2)…  │  ← read-only on stock cards
│   0    │  1–2  │ data                                         │
│   0    │   3   │ TRAILER: KeyA(6) | AccessBits(3)+GPB(1) | KeyB(6) │
├────────┼───────┼─────────────────────────────────────────────┤
│  1–14  │  0–2  │ data (3 blocks × 16 B each)                  │
│  1–14  │   3   │ TRAILER (KeyA | access | KeyB)               │
├────────┼───────┼─────────────────────────────────────────────┤
│   15   │  0–2  │ data                                         │
│   15   │   3   │ TRAILER                                      │
└────────┴───────┴─────────────────────────────────────────────┘
  4K adds sectors 16–31 (same shape) + 32–39 (16 blocks each, trailer = block 15).
```

### Sector trailer (block 3 of each sector) — 16 bytes
| Bytes | 0–5 | 6–8 | 9 | 10–15 |
|---|---|---|---|---|
| **Field** | **Key A** | **Access bits** (C1 C2 C3, stored non-inverted + inverted) | GPB (general-purpose / user byte) | **Key B** (or 6 data bytes) |

- **Key A is mandatory; Key B optional.** Both default to `FF FF FF FF FF FF`; access bytes default to `FF 07 80` (transport configuration: read/write with Key A).
- **Key A is never readable** over the air regardless of access bits — only used for auth. Key B *can* be configured as readable data (then it can't authenticate). This asymmetry is why dictionary attacks target Key A first.
- The access bits are stored **twice** (true + complement) so a corrupt trailer bricks the sector; if the inverse check fails the sector becomes inaccessible.

### Access conditions
The 3 access bits per block (C1/C2/C3) form a 3-bit code selecting one row of NXP's access-condition table, separately for each data block and for the trailer. They gate: read / write / increment / decrement-transfer-restore, and **which key** (A, B, or never) is required for each. A "value block" config, for instance, allows decrement with Key A but increment only with Key B — the basis of stored-value tickets.

### Manufacturer block (sector 0, block 0)
Layout (typical 4-byte-UID card): `UID[4] · BCC · SAK · ATQA[2] · manufacturer data[…]`.
- **BCC** = UID0 ⊕ UID1 ⊕ UID2 ⊕ UID3 (anticollision checksum).
- **SAK/ATQA** advertise card type to the reader.
- On a genuine card this block is **locked at the factory**. Writing a new UID requires a **"magic" card** (gen1a backdoor or gen2 direct-write block 0) — that's the entire premise of UID cloning, detailed in [./cloning-matrix.md](cloning-matrix.md).

### Value blocks
A special block format for monetary/credit counters: `value · ~value · value · addr · ~addr · addr · ~addr`. Stored 3× (with one inverted copy) for integrity, plus a 1-byte address stored 4×. The reader uses **increment/decrement/transfer/restore** commands gated by access bits. Note this is integrity, **not** confidentiality — once Crypto1 is broken the value is plaintext to the attacker.

---

## 3. Crypto1 — why it is broken

Crypto1 is NXP's **proprietary 48-bit stream cipher**, reverse-engineered 2007–2008 and now thoroughly dead. Structure:

- **48-bit LFSR** holds the cipher state; a fixed feedback polynomial clocks it.
- A **two-layer, 20-to-1 nonlinear filter function `f`** taps 20 specific LFSR bits and outputs **one keystream bit per clock**. Keystream XORs the plaintext.
- During authentication a separate **16-bit LFSR** acts as the tag's PRNG, generating the tag nonce **nT**.

The breaks (cite the 2008–2009 work below):

1. **Weak 16-bit PRNG → predictable nonces.** The nonce generator is only a 16-bit LFSR, so it has just **65 535 states** and cycles roughly every **~0.6 s** of card operation. Because the tag resets the PRNG on each power-up and the timing is controllable, an attacker can make the tag emit the **same nT repeatedly** (or predict it). A 48-bit cipher keyed off a 16-bit-predictable nonce is the original sin.
2. **Parity leakage.** ISO 14443 parity bits are computed over the **plaintext**, but MIFARE sends them **encrypted with the same keystream bit** that encrypts the next data bit. This reuse leaks information: it both reduces the nonce search space and gives the attacker a keystream/plaintext oracle (the card's NACK behaviour on bad parity is itself a side channel).
3. **Nested-authentication leak.** After one successful sector auth, authenticating to a *second* sector ("nested" auth) is encrypted — but the new nT is sent under known keystream, and its statelessness/predictability lets the attacker recover ~32 bits of keystream per nested auth, enough to solve for the new sector key. One known key cascades to all of them.
4. **Low keyspace + structure.** 48 bits is brute-forceable on a GPU in hours/days, but the structural attacks above make it minutes-to-seconds without brute force on most cards.

The cipher's secrecy ("security by obscurity") collapsed the moment the silicon was imaged; the math never had margin.

---

## 4. Attack methods (educational — mechanics, not a break-in recipe)

These recover the **sector keys** of a card or system **you own / are authorized to test**. The goal here is understanding *why* each works and *what it needs* — not a step-by-step for someone else's door.

| Attack | Prerequisite | What it yields | Feasibility | Flipper today |
|---|---|---|---|---|
| **Dictionary** | none | keys that are in a wordlist (defaults, vendor keys) | instant if key is common | ✅ runs automatically on **Read** |
| **Nested** | **≥1 known key** on the card | all remaining keys (exploits nested-auth leak §3.3) | seconds–minutes; needs predictable PRNG | ✅ FlipperNested-class app / Momentum `(verify)` |
| **Hardnested** | ≥1 known key, **hardened** card (no PRNG/parity leak) | remaining keys via statistical keystream collection | minutes; **needs a computer** for the heavy solve | ⚠️ partial — capture on Flipper, solve off-device |
| **Darkside** (mfcuk) | **none** (no key known) | one Key A, via NACK/parity bug | only on **non-hardened** cards; slow | ⚠️ historically off-device; limited on Flipper |
| **mfkey32 / mfkey32v2** | a **reader** + you emulate the card | the key the *reader* uses for a sector | seconds once nonces captured | ✅ **Detect Reader** → mfkey app/app/web |
| **Static / static-encrypted nonce** | varies (FM11RF08S "hardened" clones) | keys despite fixed-nonce hardening | research-grade; some need Proxmark3 | ⚠️ partial / firmware-dependent `(verify)` |

### Two directions of attack
- **Card-side** (you have the card): Dictionary → Nested/Hardnested/Darkside recover the keys *stored on the card*.
- **Reader-side** (`mfkey32`): you don't even need the real card's keys — you **emulate** the card to the genuine **reader**, the reader authenticates using *its* key, and the captured nonce pairs (`{UID, nT, nR, aR}` per auth) let an offline solver recover that key. **mfkey32v2** improved this so the two captured auth attempts need not be consecutive/same-session — far more practical. This is the FlipperMfkey / **noproto** lineage; it recovers keys *without the original tag*.

### The practical Flipper flow (own card)
1. **NFC → Read** — tries the dictionary; reports e.g. `28/32` sectors found.
2. For unread sectors with a reader available: **NFC → Detect Reader**, hold to the reader, collect the **10 nonces**; on-screen progress.
3. **Recover keys** off the collected nonces via: **Flipper Mobile App → tools → mfkey32**, *or* **lab.flipper.net → NFC tools → "give me the keys"** (USB-C), *or* the on-device **MFKey app** (slower — limited compute, several minutes).
4. Recovered keys auto-append to the **user dictionary**; **Read again** to unlock the now-known sectors → full dump.
5. **Emulate** (NFC → Saved → Emulate) for testing, or write to a **magic card** to clone the UID + data ([./cloning-matrix.md](cloning-matrix.md)).

> **When it fails:** if the reader doesn't accept the Flipper's emulation (some do extra checks), no nonces are captured. And **none of this touches AES** — against DESFire/Plus-SL3 the whole chain is a no-op.

---

## 5. MIFARE Ultralight / NTAG21x

Page-organized **NFC Forum Type 2** tags (4 bytes per page). No Crypto1; security is OTP + lock + optional 32-bit password.

| Feature | Ultralight (ICU1) | Ultralight EV1 | NTAG213 / 215 / 216 |
|---|---|---|---|
| User memory | 48 B | 48 B / 128 B | 144 / **504** / 888 B |
| Page size | 4 B | 4 B | 4 B |
| **Lock bytes** | page 02h | 02h + dynamic lock | static (02h) + dynamic lock |
| **OTP** | page 03h (one-time, OR-write) | yes | — (NTAG uses capability container) |
| **PWD / PACK** | — | 32-bit PWD + 16-bit PACK | 32-bit PWD + 16-bit PACK |
| Counters | — | 3 × 24-bit one-way | 1 × 24-bit (NFC counter) |
| **Originality signature** | — | **ECC** (read-only, NXP-signed) | **ECC** (read-only) |

- **Lock/OTP mechanics:** writes to lock and OTP pages are **bit-wise OR'd** and **irreversible** — a set bit can never clear. This is how disposable transit tickets "burn" rides: an OTP/counter bit flips per use.
- **Password:** PWD gates read and/or write of a configurable page range; on success the tag returns **PACK** as a weak mutual check. It is **not** a real cipher — a sniffed PWD/PACK is replayable. Brute-force is throttled by an auth-attempt limit (AUTHLIM) if configured.
- **Originality signature:** a 32/48-byte **ECC signature over the UID**, programmable but verifiable only against NXP's public key. A cloned tag can copy the *bytes* but a reader that checks the signature against NXP's key (and binds it to the live UID) will reject a re-UID'd clone. This is the one thing that survives naive cloning.
- **amiibo = NTAG215** (504 B). The amiibo's figure data lives in the user pages; emulating/cloning requires the per-figure data **and** Nintendo's key material to produce valid encrypted/signed contents — copying raw pages to a blank NTAG215 only works where the originality signature isn't enforced. Treat as own-figure backup only.
- **Flipper:** reads all of the above; **emulates** Ultralight/NTAG; clones to blank NTAG215 or magic UL where the UID/signature isn't checked.

---

## 6. MIFARE DESFire (EV1 / EV2 / EV3) — the AES wall

DESFire is a different animal: a small **file system on a card**, operating at **ISO 14443-4 (T=CL)** with real crypto. **This is not broken — the Flipper can read structure/metadata but cannot recover keys or forge auth.**

- **Crypto:** **AES-128** (and legacy 3DES / 3K3DES for back-compat). EV3 is **Common Criteria EAL5+** certified.
- **Memory:** 2 / 4 / 8 KB EEPROM, organized as up to **28 applications** (EV1) — EV2/EV3 raise/remove that limit — each holding up to **32 files**.
- **File types:** Standard data, Backup data (transactional), **Value**, Linear Record, Cyclic Record. Backup/value/record files support **commit/abort transactions**; EV2+ adds a **Transaction MAC** for tamper-evidence.
- **Mutual authentication:** a **3-pass challenge–response** — reader and card each prove knowledge of the shared AES key by encrypting each other's random challenge; a session key is derived for the rest of the conversation. No key ever crosses the air; a sniffer sees only ciphertext. There is no Crypto1-style PRNG/parity leak to exploit.
- **Secure messaging:** after auth, commands/data are AES-enciphered and MAC'd (integrity + confidentiality + replay protection).
- **Key diversification:** the deployed per-card key = `KDF(master_key, UID, app_data)` (typically AES-CMAC). So **every card carries a different key**, derived in the reader's SAM/HSM. Even a (hypothetical) single-card key compromise doesn't generalize to the fleet — and the master key never leaves the secure module.

**Why the Flipper stops here:** it can select the card, read the **app/file directory and settings** (which AIDs exist, file sizes, key-count, comms mode) because that's queryable pre-auth, but any **read/write of file contents requires passing AES mutual auth**, for which it has neither the diversified key nor any cipher break. **Emulation** of a DESFire that a reader actually authenticates is therefore **not possible** — the Flipper can replay a captured UID/ATS to fool UID-only readers (bad reader design), but it cannot complete the AES handshake. *That gap is the security.*

---

## 7. MIFARE Plus (SL1–SL3) — the migration bridge

Plus exists to move a Classic install to AES without swapping everything at once. It runs at a **Security Level**:

| Level | Auth | Data crypto | Meaning |
|---|---|---|---|
| **SL0** | — | — | pre-personalization (blank, factory) |
| **SL1** | Crypto1 | Crypto1 | **byte-compatible with Classic** — same weaknesses, drop-in for old readers |
| **SL2** | **AES** | Crypto1 | transitional: AES gate, Crypto1 data (rare; deprecated) |
| **SL3** | **AES** | **AES** + integrity | full AES; behaves like a secure Classic-shaped card |

- Upgrade path: ship cards in **SL1** (works with legacy readers today) → upgrade readers → switch cards to **SL3**. One-way ratchet (you can't drop back down).
- **Security:** SL1 is **exactly as breakable as Classic** (it *is* Crypto1) — a Plus card left at SL1 buys nothing. **SL3 is AES and not broken.** Flipper handling mirrors that: SL1 → treat as Classic; SL3 → metadata only.

---

## 8. Defensive guidance

- **Migrate Classic / Plus-SL1 → DESFire EV2/EV3 or Plus SL3.** Crypto1 is unfixable; only AES closes it. Budget the reader fleet upgrade — that's the real cost.
- **Never trust the UID alone.** A UID is a plaintext serial number; magic cards forge it freely. Any "UID == authorized" reader is trivially defeated. Authenticate the *crypto*, not the number.
- **Use reader-side key diversification** (UID-bound `KDF`, keys in a SAM/HSM). Defeats fleet-wide compromise and makes a single captured card useless elsewhere.
- **Enable the originality signature check** (DESFire / NTAG ECC) and **bind it to the live UID** so copied signature bytes on a re-UID'd clone are rejected.
- **Detect cloned UIDs:** anti-passback (same UID in two places / impossible travel), velocity/usage anomalies, and flagging UIDs that appear on the wrong card type (SAK/ATQA mismatch) or with implausible BCC/manufacturer bytes.
- **Don't store value/authorization in plaintext blocks** on a Crypto1 card — once keys leak, those blocks are open. Server-side validation beats on-card secrets.

---

## Open questions / to research
- Exactly which nested/hardnested/static-encrypted variants the **current Momentum + OFW** NFC app exposes on-device vs. requiring lab.flipper.net or Proxmark3, and real timings on hardened FM11RF08S cards `(verify)`.
- Practical Flipper status of the **static-encrypted-nonce** recovery (the `fm11rf08s_recovery` class) — on-device yet, or still Proxmark3-only? `(verify)`
- amiibo NTAG215: current state of read/emulate vs. write given Nintendo key material and signature enforcement `(verify)`.
- DESFire EV2/EV3 **metadata** depth the Flipper actually surfaces (AIDs, file settings, free memory) vs. what needs auth.
- Whether any reader-side Flipper emulation quirks cause `mfkey32` nonce capture to silently fail on specific reader models.

## Sources
- NXP MIFARE Classic EV1 1K datasheet (MF1S50YYX_V1): https://www.nxp.com/docs/en/data-sheet/MF1S50YYX_V1.pdf
- NXP MIFARE Ultralight EV1 datasheet (MF0ULX1): https://www.nxp.com/docs/en/data-sheet/MF0ULX1.pdf · AN11340 features/hints: https://www.nxp.com/docs/en/application-note/AN11340.pdf
- NXP MIFARE DESFire EV3 datasheet (MF3D(H)x3): https://www.nxp.com/docs/en/data-sheet/MF3D_H_X3_SDS.pdf
- NXP MIFARE Plus EV2 datasheet (MF1P(H)x2): https://www.nxp.com/docs/en/data-sheet/MF1P(H)x2.pdf · MIFARE HF overview: https://www.nxp.com/products/rfid-nfc/mifare-hf
- Garcia, de Koning Gans, Muijrers, van Rossum, Verdult, Schreur, Jacobs, "Dismantling MIFARE Classic" (ESORICS 2008): https://flaviodgarcia.com/publications/Dismantling.Mifare.pdf
- Nohl & Plötz, Crypto1 reverse-engineering (2007–2008); Courtois, "The Dark Side of Security by Obscurity" / darkside attack (2009)
- Crypto-1 cipher overview: https://en.wikipedia.org/wiki/Crypto-1
- MIFARE Classic static encrypted nonce variant (CESAR 2024): https://2024.cesar-conference.org/program-media/CESAR-2024_keynote-MiFare.pdf
- Flipper Zero — recovering MIFARE Classic keys (mfkey32): https://docs.flipper.net/zero/nfc/mfkey32 · NFC docs: https://docs.flipper.net/zero/nfc
- FlipperMfkey / noproto MIFARE Classic guide: https://gist.github.com/noproto/63f5dea3f77cae4393a4aa90fc8ef427 · mfkey32v2: https://github.com/equipter/mfkey32v2
- Proxmark3 (RRG/Iceman): https://github.com/RfidResearchGroup/proxmark3
