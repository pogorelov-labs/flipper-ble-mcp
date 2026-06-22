---
title: HID iCLASS / Picopass
domain: cards
type: reference
status: detailed
summary: iCLASS legacy vs SE/SEOS; the PicoPass app
hardware: [flipper-internal]
use_cases: []
related: [cards/mifare.md, cards/cloning-matrix.md, cards/nfc-theory.md, cards/README.md, capabilities/nfc-rfid.md]
tags: [iclass, picopass, seos, iso-15693, loclass, hid-downgrade, pacs]
last_verified: 2026-06-19
---

# HID iCLASS / Picopass

> **TL;DR —** HID's 13.56 MHz iCLASS family spans three security generations: legacy/standard-keyed Picopass is broken and cloneable with the Flipper PicoPass app, while SE and SEOS use AES and are not — don't assume any "HID 13.56 card" is clonable.
> 13.56 MHz neighbor of [mifare.md](mifare.md) · practical cloning in [cloning-matrix.md](cloning-matrix.md) · physics in [nfc-theory.md](nfc-theory.md). Part of the [Cards hub](README.md) · [KB](../README.md).

**iCLASS** is HID Global's 13.56 MHz access-control family. It is the HF answer to weak 125 kHz prox — but "iCLASS" spans **three very different security generations**, and conflating them is the single biggest mistake people make. **Legacy iCLASS is broken; iCLASS SEOS is not.** This page draws that line precisely. Educational/defensive use only — work on **your own** credentials ([legal-and-safety](../legal-and-safety.md)).

> **Headline:** legacy iCLASS (and standard-keyed Picopass) is cloneable with a Flipper because its keys were derived and leaked. **iCLASS SE and especially SEOS use AES and are *not* broken** — do not assume a "HID 13.56 card" is clonable.

---

## 1. The technology stack

iCLASS is built on the **Picopass** chip (originally Inside Secure / HID's Iate; the silicon is "Picopass") and the **ISO/IEC 15693** vicinity-card air interface (the same NFC-V layer covered in [nfc-theory.md](nfc-theory.md)). It is **not** ISO 14443 / MIFARE — different anticollision, different framing, longer nominal range.

| Layer | iCLASS |
|---|---|
| Frequency | 13.56 MHz |
| Air interface | **ISO 15693** (vicinity, NFC-V) — *not* 14443A |
| Chip | **Picopass** (2KS / 16KS variants) |
| Memory model | Blocks of 8 bytes; app areas; **PACS** payload in the credential's secured area |
| Identity | 8-byte **CSN** (Card Serial Number) + protected application data |
| Crypto (legacy) | **2DES/3DES**-based mutual auth with a **diversified key** per card |
| Crypto (SE/SEOS) | **AES-128** inside a **Secure Identity Object (SIO)** |

The thing a reader actually cares about is the **PACS** (Physical Access Control System) payload — essentially the same Wiegand-style facility-code + card-number bits as prox, but stored *inside* the card's protected memory rather than broadcast in the clear.

---

## 2. iCLASS legacy — why it's broken

"iCLASS legacy" (a.k.a. iCLASS Classic) was HID's first-gen smartcard access. Its security rests on a **master key** and a **key-diversification function (KDF)** that turns the master key + the card's CSN into a per-card key. Two keyset flavors exist:

- **Standard / "default" keyset** — the *same master key across HID's entire standard product line worldwide*. Most legacy deployments use it.
- **Elite / High-Security (HID Custom) keyset** — a customer-specific master key (the "Elite" or "MOB" key) meant to isolate a site.

### What went wrong
- The **standard legacy master key was recovered/leaked** (notably via the Garcia/Verdult *"Dismantling iClass and iClass Elite"* research, 2012). Once you have the master key + the card's CSN, you compute the card's diversified key and read its protected blocks. ([Dismantling iClass & iClass Elite](https://www.researchgate.net/publication/235916470_Dismantling_iClass_and_iClass_Elite))
- The **KDF and the Elite scheme were also broken** — the **loclass** attack derives a reader's Elite/custom key by having a tool emulate a sequence of chosen CSNs and collecting the reader's authentication responses (an "online" capture step + an "offline" key-computation step). ([Elite iClass hacking](https://swende.se/blog/Elite-Hacking.html))
- Large dictionaries of **~700+ leaked/known legacy keys** circulate (e.g. from iCopy-X), making most legacy cards openable by dictionary alone.

**Crucial nuance:** you can often **copy the protected blocks (6–9) verbatim between cards without even decrypting them** — the PACS data lives in blocks 7/8/9, and a like-for-like Picopass clone reproduces the credential. ([iClass notes gist](https://gist.github.com/bettse/36f25f9a2fcca74d773587cc8e780766))

> **Net:** legacy iCLASS provides *obfuscation*, not security. With public keys + a Flipper/Proxmark, a legacy card is readable and cloneable.

---

## 3. iCLASS SE / SEOS — why these are *not* broken

HID's modern generations fix the root problem (shared/derivable keys, weak proprietary crypto) by moving to **AES** inside a portable **Secure Identity Object (SIO)**.

### iCLASS SE
- Stores the PACS inside an **SIO protected with AES** cryptography rather than the legacy 2DES/diversified scheme.
- Part of HID's **Seos/SE "Trusted Identity Platform" (TIP)** key-management model — keys are managed, not a single global secret.
- **Caveat — the downgrade problem:** an **SE card is frequently dual-technology**, also carrying a *legacy* iCLASS application for backward compatibility, and **most readers ship with legacy mode enabled by default**. The "**HID downgrade**" attack extracts the PACS via that legacy side and re-encodes it to a Picopass/T5577. **This attacks the legacy fallback, not the AES SIO.** Disable legacy on the reader and the SE AES path stands. ([PM3 hid_downgrade](https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/hid_downgrade.md))

### iCLASS SEOS
- HID's flagship: **open-standard AES-128 (and 256)**, secure messaging, **strong mutual authentication**, SIO-based, designed for mobile/NFC and future threats.
- **No public break.** There is no known key leak or practical clone of a properly deployed SEOS credential. The Flipper/Proxmark can see the CSN and that it's SEOS, but **cannot read the protected SIO or clone it**.
- For very high assurance, the comparable peer is **MIFARE DESFire EV3** (EAL5+ Common Criteria certified). SEOS and SE are strong but not certified to that exact level `(verify)`. ([HID iCLASS comparison](https://groovebadges.com/a/blog/hid-iclass-comparison-iclass-sr-se-and-seos) · [Seos whitepaper](https://www.emacs.es/downloads/WP/20140723_iCLASS_Seos_Card_Whitepaper_EXTERNAL_v1.0.pdf))

> **Restate, because it matters:** **SEOS is not broken.** If your badge is SEOS (and the reader has legacy disabled), a Flipper cannot clone it. Cloning success on "iCLASS" almost always means the card or reader still exposes the **legacy** path.

---

## 4. Legacy vs SE vs SEOS — comparison

| | **iCLASS legacy** | **iCLASS SE** | **iCLASS SEOS** |
|---|---|---|---|
| Generation | 1st (2002-era) | 2nd | 3rd / current |
| Air interface | ISO 15693 | ISO 15693 (+ SIO) | ISO 15693 / NFC (mobile) |
| Crypto | 2DES + diversified key (proprietary KDF) | **AES** SIO | **AES-128/256** SIO, secure messaging |
| Key model | Global **standard** key *or* per-site **Elite** | Managed (TIP) | Managed (TIP), mutual auth |
| Public break? | **Yes** — std key leaked; KDF/Elite broken (loclass); ~700-key dicts | SIO itself: no. **But legacy-downgrade fallback often exploitable** | **No known practical break** |
| Flipper can clone? | ✅ legacy (PicoPass app, std keys / dict / loclass) | ⚠️ only via **legacy/downgrade** side, not the AES SIO | ❌ read CSN only; cannot clone |
| Security tier | 🟠 broken | 🟡→🟢 strong if legacy disabled | 🟢 strong |
| Defensive action | **Replace** | Disable legacy on readers; plan migration | Keep; preferred target |

---

## 5. The Flipper PicoPass app

The Flipper handles iCLASS/Picopass through a **separate PicoPass app** (by @bettse; on Flipper Lab / catalog) — it lives apart from the main NFC app because iCLASS is ISO 15693, not 14443A.

### What it can do
- **Read / save / emulate** legacy iCLASS / Picopass cards and fobs.
- Defaults target **iCLASS Legacy with standard keys / 3DES**; the **CSN is pre-filled** with a typical HID value.
- **Write** the credential to a writable Picopass blank **or** export to the Flipper LFRFID format / write to a **T5577** (for legacy→prox downgrade scenarios).
- **Change keys** on a card; run a **dictionary attack** (the ~700-key legacy dictionaries).
- Perform the **"online" part of the loclass attack** — emulate the CSN sequence and collect reader responses; you then compute the Elite/custom key **off-device** (e.g. `loclass.ericbetts.dev`) and drop the result into `iclass_elite_dict_user.txt` under `apps_data/picopass/assets/`.

([PicoPass on Flipper Lab](https://lab.flipper.net/apps/picopass) · [catalog](https://catalog.flipperzero.one/application/64d2039313043e71ea76645f/page) · [Flipper iClass wiki](https://flipper.wiki/hidiclass/))

### What it can't do
The offline loclass / standard-key path **fails** on:
- **iCLASS SE** and **SEOS** (AES SIO — out of scope).
- **Non-iCLASS Picopass** deployments (e.g. Circuit Laundry and similar closed apps).
- Readers using **Standard-2 keyset**, or **custom-keyed readers using a Standard KDF / SE KDF**.

So the honest boundary is: **PicoPass app = legacy iCLASS toolkit.** It is excellent at legacy and standard-keyed cards; it does not break modern AES iCLASS.

---

## 6. Cloning legacy iCLASS to writable cards

For **your own** legacy credential:
1. **Read** with the PicoPass app. If standard-keyed, it dumps directly; if Elite/custom, you need the key (dictionary, or loclass against *your* reader).
2. **Save** the dump (CSN + blocks, including the PACS in blocks 7–9).
3. **Write** to a **writable Picopass** blank (a like-for-like clone, the cleanest result) — or, for a **downgrade**, write the extracted PACS to a **T5577** so a legacy-enabled prox reader accepts it. See [cloning-matrix.md](cloning-matrix.md) for blanks and gotchas.

### Where Proxmark3 is needed instead
The Flipper PicoPass app covers most *legacy* needs, but **Proxmark3 (RRG/Iceman)** remains the deeper iCLASS tool for:
- Full **`hf iclass`** suite — granular dumps (`--ki`), block-level read/write, config/AA1–AA2 application handling.
- More robust **loclass** capture and key management, MOB-key handling, edge readers.
- Working with **non-standard keysets**, partial credentials, and diagnosing *why* a card won't read.
- Anything beyond legacy that's research-grade (and even PM3 does **not** break SEOS).

([PM3 RRG/Iceman](https://github.com/RfidResearchGroup/proxmark3) · [hid_downgrade](https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/hid_downgrade.md))

---

## 7. Security takeaways & migration advice

**Why legacy is weak:** shared/derivable keys (the standard master key is public; Elite/KDF are broken), and the PACS can be lifted or block-copied. It is a 2002-era design with 2012-era public attacks — assume any legacy or standard-keyed iCLASS card is clonable.

**Why SEOS is strong:** AES-128/256, managed keys (no global secret), secure messaging, mutual authentication, no public break. Treated correctly (legacy disabled on readers), a SEOS credential is **not** clone-on-read.

**Migration checklist (defensive):**
- **Inventory:** identify legacy vs SE vs SEOS in your fleet (the PicoPass app / PM3 reveal the type; SE/SEOS won't dump).
- **Disable legacy mode** on SE-capable readers to kill the **downgrade** path — this is the highest-leverage, lowest-cost fix.
- **Migrate** legacy and standard-keyed cards to **SEOS** (or DESFire EV3 if you want EAL5+ certification).
- **Custom keys:** if staying on iCLASS, use **Elite/custom** keysets (not the global standard) — necessary but *not sufficient* given loclass.
- **Defense-in-depth:** pair badges with PIN/biometric on sensitive doors; static-credential cloning is mitigated, not solved, by format choice.

> Do **not** report "iCLASS is broken" to stakeholders without qualifying the generation. **Legacy: yes. SE: conditionally (legacy fallback). SEOS: no.**

---

## Open questions / to research
- Exact Flipper-vs-Proxmark3 boundary for **SE downgrade** capture on stock firmware — what the PicoPass app exposes today.
- Whether current PicoPass app builds bundle updated legacy/Elite dictionaries, and dictionary-attack speed on-device.
- Practical loclass capture reliability on the Flipper (CSN count, reader cooperation) vs Proxmark3.
- Writable **Picopass** blank availability/quality vs T5577 downgrade for legacy clones (cross-ref [cloning-matrix.md](cloning-matrix.md)).
- Independent certification status of SEOS/SE vs DESFire EV3 EAL5+ — confirm the precise claims `(verify)`.
- Detection: do modern HID readers flag emulated CSNs / loclass capture attempts?

## Sources
- Flipper NFC docs: https://docs.flipper.net/zero/nfc
- Flipper PicoPass app (Lab): https://lab.flipper.net/apps/picopass · catalog: https://catalog.flipperzero.one/application/64d2039313043e71ea76645f/page
- Flipper Community Wiki — HID iClass: https://flipper.wiki/hidiclass/
- Proxmark3 (RRG/Iceman): https://github.com/RfidResearchGroup/proxmark3
- Proxmark3 HID downgrade / SIO guide: https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/hid_downgrade.md
- Garcia & Verdult, "Dismantling iClass and iClass Elite" (2012): https://www.researchgate.net/publication/235916470_Dismantling_iClass_and_iClass_Elite
- M. Swende — Elite iClass hacking (loclass): https://swende.se/blog/Elite-Hacking.html
- iClass legacy block/key notes (gist): https://gist.github.com/bettse/36f25f9a2fcca74d773587cc8e780766
- HID iCLASS / SR / SE / Seos comparison: https://groovebadges.com/a/blog/hid-iclass-comparison-iclass-sr-se-and-seos
- HID iCLASS Seos whitepaper: https://www.emacs.es/downloads/WP/20140723_iCLASS_Seos_Card_Whitepaper_EXTERNAL_v1.0.pdf
