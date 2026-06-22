---
title: iButton / 1-Wire Keys
domain: capabilities
type: reference
status: detailed
summary: Dallas / Cyfral / Metakom contact "touch" keys over 1-Wire — read, emulate, and clone to writable blanks.
hardware: [flipper-internal]
use_cases: [UC-24]
related: [capabilities/nfc-rfid.md, hardware/README.md, legal-and-safety.md, 01-architecture.md]
tags: [ibutton, 1-wire, dallas, cyfral, metakom, ds1990a, rw1990]
last_verified: 2026-06-19
---

# iButton / 1-Wire Keys

> **TL;DR —** Contact-based "touch" keys (Dallas DS1990A, Cyfral, Metakom) read over a 1-Wire bus — static IDs with no crypto, trivially cloneable, common on ex-USSR intercoms. Covers 1-Wire electrical basics, the ID layout, read/emulate/write workflows, writable RW1990-class blanks (and voltage limits), and contact-reliability tips.
> See [nfc-rfid.md](./nfc-rfid.md), [hardware/README.md](../hardware/README.md), [legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md) · [architecture](../01-architecture.md).

**iButton** = contact-based "touch" keys read over a 1-Wire-style bus. Think of the round metal fobs on apartment-building intercoms and old door controllers, especially across the ex-USSR / Eastern Europe. Unlike NFC/RFID, there's **no radio** — the key must physically touch the reader's two contacts. Functionally these are the contact-credential cousins of the LF prox tags in [nfc-rfid.md](./nfc-rfid.md): a **static ID, no crypto, trivially cloneable**.

Authorized-use note: clone/emulate **only keys you own or are authorized to duplicate** (your own flat, your own gate). Duplicating a building's keys without permission is the same legal/ethical line as cloning access cards — see [legal-and-safety.md](../legal-and-safety.md).

---

## 1-Wire electrical basics
1-Wire (and the Dallas/Maxim iButton family) carries **data and power on a single signaling line plus ground** — two conductors total. On the Flipper:

- The iButton contacts wire to **GPIO pin 17** (the 1-Wire data line) and **GND**.
- The reader (or the Flipper, as reader) holds the line **high through a pull-up**; either side communicates by **pulling the line low** in timed slots (the bus is open-drain). Bit timing — reset pulse, presence pulse, read/write time slots — is what distinguishes the protocols.
- **Parasitic power:** a genuine Dallas iButton has no battery; it **harvests power from the data line** while the line is idle-high, storing charge to run its logic and answer when the line is pulled low. This is why a tiny coin-shaped key with two contacts and no battery still "works."

Physically, the Flipper exposes **three spring-loaded pogo pins** plus a flat iButton pad. Two pins are the data line and ground; the geometry gives two usable contact zones:
- **Flat pad** (left data pin + ground) → **read / write** keys.
- **Protruding pad section** (right data pin + ground) → **emulate** (Flipper acts as the slave key that you touch to a reader).

Getting the right pins onto the right reader contacts is most of the battle (see reliability tips below).

---

## Dallas DS1990A — 64-bit ROM
The canonical iButton. Each DS1990A carries a **factory-burned 64-bit ROM** (no rewritable memory) laid out as:

| Field | Size | Meaning |
|---|---|---|
| **Family code** | 8 bits (LSB) | Device family. **`0x01`** = DS1990A / 1-Wire serial-number-only iButton. |
| **Serial number** | 48 bits | Unique-per-device serial (the meat of the ID). |
| **CRC-8** | 8 bits (MSB) | Dallas CRC-8 over the preceding 56 bits; lets a reader validate the read. |

So the whole "key" is just **8 + 48 + 8 = 64 bits** of read-only ID. The Flipper reads it, detects the type, and saves the unique number. Related Dallas parts with actual memory exist (DS1992/DS1996 = NVRAM, DS1971 = EEPROM); the Flipper can copy memory **between two keys of the same type** for those, but the common access fob is the ID-only DS1990A.

---

## Cyfral and Metakom (intercom keys)
Two non-Dallas contact protocols common on **ex-USSR intercom systems**. They mimic the iButton form factor and contact interface but use their own (simpler, non-1-Wire-standard) signaling and shorter IDs:

| Protocol | Context | Notes |
|---|---|---|
| **Cyfral** | Older Russian/CIS intercoms (Cyfral brand panels). | Short ID, simple modulation. Read/emulate supported; **writing Cyfral to blanks is limited / not fully supported** (verify). |
| **Metakom** | Common on Metakom intercom panels (CIS). | Short ID; read/emulate supported. Like Cyfral, no real authentication. |

For the owner on CFW: these are exactly the keys you'll meet on a typical Eastern-European apartment-block door. The Flipper auto-detects which of Dallas / Cyfral / Metakom a touched key is.

---

## Workflows
| Action | How | Notes |
|---|---|---|
| **Read** | `iButton → Read` → touch key to the **flat pad** | Detects type (Dallas/Cyfral/Metakom), reads + shows the ID. |
| **Save** | save after read, name it | Stored as a `.ibtn` file on the SD card. |
| **Emulate** | `iButton → Saved → (key) → Emulate` → touch the **protruding pad** to the reader | Flipper becomes the slave key. Reliable for ID-only keys since there's no crypto handshake to fake. |
| **Add manually** | enter type + ID by hand | No physical key needed to create an emulator. |
| **Write** | `iButton → Saved → (key) → Write` → touch a **blank** to the flat pad | Burns the ID into a writable blank (below). |

---

## Writable blank keys
Dallas iButtons are factory-locked (read-only ROM), so cloning targets are **aftermarket rewritable "RW" blanks** that expose a command to rewrite the ID. Per Flipper docs, the Flipper currently **writes the UID/ID** to these (it does **not yet rewrite a blank's data memory** — ID only):

| Blank | Emulates / writes | Notes |
|---|---|---|
| **RW1990 / RW1990.2 (TM-08 family)** | Dallas DS1990 ID | The standard cheap clone blank for DS1990A fobs. |
| **TM1990 / TM08v2 / TM08vi-2** | Dallas ID | Common TM-series rewritable blanks. |
| **RW2004 / TM2004** | Dallas ID (EEPROM types) | Larger blanks; Flipper writes the ID. |
| **TM01** | (partial / disabled) | Incomplete support noted in firmware — verify. |
| **Cyfral / Metakom blanks** | their respective ID | Writing support is **limited** vs Dallas — verify per firmware/CFW. |

**Voltage caveat:** some blanks require a higher programming voltage than the Flipper's 1-Wire line provides. E.g. **RW2000-class blanks need ~8 V** to program, which the Flipper can't supply — so certain high-voltage blanks **can't be written** by the Flipper at all. Stick to RW1990-class blanks for reliable DS1990A cloning. (Exact list shifts with firmware — verify against your installed OFW/CFW.)

---

## Security reality
iButton ID keys are **static identifiers with no authentication**:
- The ID is sent in the clear on contact; **read once = clone-ready**.
- No challenge-response, no rolling code, no crypto. Emulation always "wins" because there's nothing to forge beyond the bits.
- The Dallas CRC-8 is **integrity, not security** — it stops misreads, not copying.

Mitigation is the same story as LF prox (see [nfc-rfid.md](./nfc-rfid.md)): treat ID-only contact keys as **non-secret**. Where it matters, move to authenticated credentials. For a hobbyist owner the upside is the legitimate one — instantly back up or duplicate **your own** intercom/gate keys.

---

## Contact / orientation reliability tips
Most "it won't read/emulate" problems are mechanical contact, not the protocol:

- **Match the contact zones:** read/write uses the **flat pad** (left data pin + GND); emulate uses the **protruding pad** (right data pin + GND). Using the wrong zone is the #1 failure.
- **Seat firmly and hold still** — the pogo pins need solid pressure; a glancing touch drops the bit timing.
- **Polarity matters for the reader:** the key's center vs ring must land on the reader's data vs ground correctly; if a real key works in one orientation, the Flipper emulation needs the same orientation against the reader.
- **Clean contacts** — oxidized fob/reader pads cause flaky reads.
- **For stubborn blanks**, re-try the write a couple of times; contact bounce can corrupt a single-shot program.
- If a key reads but won't emulate to a specific door, suspect a **non-standard reader** (or a system that does more than ID) rather than the Flipper — cross-check whether it's actually a contact ID system at all.

---

## Open questions / to research
- Definitive current list of writable blanks (incl. RW1990.2, TM2004, TM01 status) on latest OFW vs Unleashed/Momentum.
- Cyfral/Metakom **write-to-blank** support state — which blanks, which firmware.
- Whether any firmware adds Flipper-side **high-voltage** programming (RW2000-class) via external circuitry.
- Memory-copy support beyond ID for DS1992/DS1996/DS1971 — current limits.
- Reliability differences between OFW and CFW iButton stacks (timing tolerance).

## Sources
- iButton docs: https://docs.flipper.net/zero/ibutton · Read: https://docs.flipper.net/zero/ibutton/read · Write: https://docs.flipper.net/zero/ibutton/write
- Blog (Taming iButton): https://blog.flipper.net/taming-ibutton/
- Writable blanks discussion: https://forum.flipper.net/t/what-blank-key-models-can-be-written-with-flipper/16934
- Maxim/Dallas 1-Wire & DS1990A ROM background: https://www.analog.com/en/technical-articles/guide-to-1wire-communication.html
