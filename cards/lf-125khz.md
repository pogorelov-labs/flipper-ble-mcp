---
title: LF 125 kHz Cards
domain: cards
type: reference
status: detailed
summary: EM4100/HID Prox/Indala/AWID + T5577 cloning
hardware: [flipper-internal]
use_cases: []
related: [cards/nfc-theory.md, cards/cloning-matrix.md, cards/iclass-picopass.md, cards/mifare.md, capabilities/nfc-rfid.md]
tags: [lf-125khz, em4100, hid-prox, indala, awid, t5577, em4305, fdx-b]
last_verified: 2026-06-19
---

# LF 125 kHz Cards

> **TL;DR —** The 125 kHz LF families (EM4100, HID Prox, Indala, AWID and more) are static, unencrypted serial numbers — clone-on-read onto a T5577 blank; covers their encodings, the T5577/EM4305 chips, and why LF access control is weak.
> Physics in [nfc-theory.md](nfc-theory.md) · practical cloning in [cloning-matrix.md](cloning-matrix.md) · feature view in [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md). Part of the [Cards hub](README.md) · [KB](../README.md).

The 125 kHz low-frequency band is the *old* world of access control: cards that are **just a number**, transmitted in the clear, with **no cryptography and no authentication**. The whole family is trivially cloneable, which is exactly why it is the safest place to learn — and why it should be *retired* from any door that matters. Educational/defensive use only: clone **your own** credentials ([legal-and-safety](../legal-and-safety.md)).

> **One-line security verdict:** an LF 125 kHz access card is a *broadcast serial number*. Anyone who can stand near it for ~1 second owns a copy. Treat LF as a convenience token, not a security control.

---

## 1. How LF signaling works

LF tags are **passive**: the reader's 125 kHz field powers the chip, which replies by **load-modulating** that same field (it switches a load on/off, the reader sees the amplitude/phase wobble). There is no battery and no transmitter — just a tuned coil. Data is layered in two steps: a **bit encoding** (how a 0/1 maps to field changes) on top of a **line code** (how raw bits are framed).

### Modulation types
| Modulation | What varies | Used by | Flipper |
|---|---|---|---|
| **ASK** (Amplitude Shift Keying) | field amplitude (load on/off) | EM4100, HID Prox*, AWID, Keri, most | ✅ read/write |
| **PSK** (Phase Shift Keying) | phase of the subcarrier | **Indala**, NexWatch/Honeywell | ✅ read/write |
| **FSK** (Frequency Shift Keying) | subcarrier frequency (two rates) | HID Prox, AWID, Paradox, ioProx | ✅ read; write support narrower `(verify per-firmware)` |

\*HID Prox is technically **FSK** at the RF layer; the Flipper's reader handles it. Flipper's official line is "ASK or PSK coding" because those are the two user-selectable read modes; it auto-loops protocols on read. ([docs](https://docs.flipper.net/zero/rfid))

### Line codes (framing the bits)
- **Manchester** — each bit = a *transition* in the middle of the bit cell (rising = 1, falling = 0, or vice-versa). Self-clocking, DC-balanced. EM4100 uses this.
- **Biphase / differential** — a transition every bit boundary, plus a mid-bit transition for one symbol. Used by several FSK formats.
- **RF clock / bit rate** — expressed as a divider of the 125 kHz carrier: **RF/64** (≈1953 bps, EM4100), RF/32, RF/40, RF/50. The clock is part of what identifies a protocol.

> **Mental model:** *modulation* = how the radio carries a symbol (ASK/FSK/PSK); *line code* = how symbols spell out bits (Manchester/biphase); *RF clock* = how fast. A "protocol" is a fixed combination of all three plus a frame layout.

---

## 2. EM4100 / EM4102 — the canonical read-only tag

The **EM4100** (a.k.a. EM4102, EM4200 is the higher-density successor) is the archetypal "dumb" LF tag: **read-only, 40-bit ID, ASK + Manchester, RF/64**. Burned at the factory, never changes. Billions exist as the white "125 kHz" gym/office cards and blue keyfobs.

### The 64-bit frame structure
The 40-bit ID is wrapped with parity into a **64-bit transmitted frame** that repeats continuously:

```
1 1 1 1 1 1 1 1 1   ← 9-bit header (nine 1s — never occurs in payload, marks frame start)
D00 D01 D02 D03 P0  ← 8-bit customer/version ID as 2 nibbles, each + row (even) parity
D08 D09 D10 D11 P1
... (10 data nibbles total: 2 ID + 8 data) each row = 4 data bits + 1 row-parity bit
PC0 PC1 PC2 PC3 S0  ← 4 column-parity bits (one per nibble column) + 1 stop bit (0)
```

Breakdown: **9** (header) + **50** (10 rows × 5) + **5** (4 column parity + stop) = **64 bits**.
- **8 bits** = customer/version ID (often a manufacturer/batch byte)
- **32 bits** = the actual ID data
- Parity is *row* (per nibble) and *column* (across nibbles) — a simple 2-D check, **not** security.

Decoding example from the Proxmark walkthrough: a frame demodulates to ID `0x010872E77C`. ([PM3 EM4102 walkthrough](https://github.com/proxmark/proxmark3/wiki/Walkthrough-of-a-EM4102-tag))

**Security reality:** there is *nothing* to attack — it's a number broadcast on a loop. Read once, you have it forever. The parity bits stop radio errors, not copying.

---

## 3. EM4305 / T5577 — the writable clone targets

To *write* an LF credential you need a re-programmable chip. Two dominate:

### T5577 — the universal LF clone chip
The **T5577** (Atmel/Microchip) is the single most important blank in LF cloning. It is **multi-protocol and reconfigurable**, so one physical card can *become* an EM4100, HID Prox, Indala, AWID, Pyramid, etc., by rewriting its config.

| T5577 property | Detail |
|---|---|
| Memory | **2 pages**, 8 blocks/page, **32 bits per block** |
| Page 0 | **Block 0 = config**; blocks 1–7 = user data (the emulated card payload) |
| Page 1 | Traceability/manufacturer data + extended config |
| Config block 0 fields | **modulation** (Manchester/biphase/PSK/FSK/direct), **bit-rate divider** (RF/8…RF/128, e.g. RF/64), **MaxBlock** (how many blocks to stream), **PWD-enable** (bit 28), sequence terminator, X-mode |
| Password | Optional 32-bit password lock (block 7 PWD) — can brick a card if forgotten |
| Example | EM4100 emulation ≈ config word `00148040` (ASK/Manchester, RF/64, 2 data blocks) `(verify against your tool)` |

Because the config block *is* the protocol selector, the T5577 emulates almost every open 125 kHz format. This is why the cloning workflow is always "read original → write T5577." ([PM3 T5577 guide](https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/T5577_Guide.md))

### EM4305 — the EM-family writable
The **EM4305** (EM Microelectronic) is the writable member of the EM family. It is read/write, can **present an EM4100-style output**, and is the standard chip for **ISO 11784/11785 FDX-B animal microchips** (see §6). It is less of a chameleon than the T5577 (EM-centric rather than all-format) but is common as a writable EM4100 blank and in implants.

> **What writes to a T5577?** The Flipper's *Write* action (in the 125 kHz app) takes a saved/scanned LF card and **programs it onto a T5577 blank** — choose the saved card → *Write* → hold the blank to the back antenna. EM4305 is writable too but the Flipper's writer targets T5577 by default for multi-format clones. See [cloning-matrix.md](cloning-matrix.md) for the blanks shopping list and per-format write notes.

---

## 4. HID Prox — formats, facility codes & parity

**HID Prox** (HID Global's classic 125 kHz line: ProxCard II, ISOProx, Prox keyfobs) is the dominant LF access-control format in North America. At the radio layer it's **FSK**; what matters operationally is the **Wiegand bit format** carried inside.

### H10301 — the 26-bit standard format
The open, ubiquitous **H10301 26-bit** layout:

```
[ P_even ][  8-bit Facility Code  ][   16-bit Card Number   ][ P_odd ]
   bit 1        bits 2–9                  bits 10–25            bit 26
```
- **Leading even-parity** bit covers the first 12 data bits; **trailing odd-parity** covers the last 12.
- **Facility code:** 8 bits → **0–255** (only 255 usable codes).
- **Card number:** 16 bits → **1–65 535** per facility code.
- Total non-duplicating space ≈ **16.7 M** cards.

**Why this is weak (beyond being cloneable):** H10301 is an *open, published* format with only **256 facility codes**. Facility codes are not secret and collide constantly across organizations; many sites never customize them. So even *without* cloning a specific card, the keyspace is tiny and guessable, and a cloned card just needs the right FC+CN pair — both of which the Flipper reads in the clear. ([HID card formats](https://www.idesco.com/files/articles/HID%20-%20Understanding%20card%20formats.pdf) · [Kisi facility-code calc](https://www.getkisi.com/blog/how-to-calculate-facility-code-using-card-bit-calculators))

### Longer / proprietary HID formats
| Format | Bits | Notes |
|---|---|---|
| **H10301** | 26 | Open standard; 8-bit FC + 16-bit CN + 2 parity. The default. |
| **H10302** | 37 | No facility code — 35-bit ID + parity (larger flat ID space). |
| **H10304** | 37 | 16-bit FC + 19-bit CN + parity. |
| **Corporate 1000** | 35 / 48 | HID-controlled, per-customer; **larger FC field**, harder to guess, but still LF/static. |

**Facility-code handling on the Flipper:** for the open 26-bit format the Flipper decodes/displays FC + CN and can write them to a T5577. **Custom/proprietary formats** (Corporate 1000, 48-bit) are still *static numbers* — if the Flipper reads the raw bits it can clone them verbatim, even without "understanding" the field layout. The credential's security never depended on the format being secret. Longer formats raise the *guessing* bar, not the *cloning* bar.

---

## 5. Other LF families (brief)

The Flipper auto-detects a broad set of 125 kHz protocols. ([flipper.net](https://flipper.net/products/flipper-zero) lists EM400x/410x/420x, HID, Indala, FDX-A/B, Pyramid, AWID, Viking, Jablotron, Paradox, PAC/Stanley, Keri, Gallagher, NexWatch.)

| Format | Modulation | One-liner |
|---|---|---|
| **Indala** | **PSK** | Motorola/HID legacy; 26/27-bit + longer proprietary; PSK is why it needs the PSK read mode. |
| **AWID** | FSK | Common US access format; facility-code + card-number Wiegand, static. |
| **Paradox** | FSK | Alarm-panel ecosystem prox; static ID. |
| **Keri** (KeriNXT/PYRAMID) | FSK | Keri Systems / Pyramid format; static. |
| **ioProx** (Kantech) | FSK | Kantech ioProx; XSF format (facility/card/version); static. |
| **Viking** | ASK | Simple 64-bit ASK format; static. |
| **NexWatch / Honeywell** | PSK | Quadrakey/Nexkey PSK; static. |

All share the same fatal property: **fixed serial, no challenge-response → clone-on-read.** Indala/NexWatch differ mainly in needing **PSK** demodulation (use the Flipper's "read with preselected PSK coding" extra action if auto-detect struggles).

---

## 6. FDX-B animal microchips (134.2 kHz)

Pet/livestock implants use **ISO 11784/11785 FDX-B** (15-digit ISO number) — and these run at **134.2 kHz**, *not* 125 kHz. (Older **FDX-A** = 10-digit, non-ISO; **HDX** = half-duplex, also 134.2 kHz.)

**Flipper reality:** the Flipper's antenna is tuned for **125 kHz**, so 134.2 kHz reading is a *best-effort add-on*:
- It can detect chips across roughly a **110–140 kHz** range but at a **much shorter read distance** (~10 mm) and with **lower reliability** than at 125 kHz.
- Reading FDX-B/FDX-A requires holding the Flipper **steady for ~3 seconds**; misses are common; rotating 90° or re-scanning helps.
- For clinical pet-chip scanning, a **dedicated 134.2 kHz veterinary reader** is the correct tool. ([docs: animal microchips](https://docs.flipper.net/zero/rfid))

> **Takeaway:** treat Flipper FDX-B reads as "sometimes works," not "reliable." It is **not** a substitute for a vet scanner, and these chips are write-protected ID transponders (EM4305-class) — read-only in practice for the Flipper.

---

## 7. Card-type quick table

| Family | Freq | Mod | Read-only? | Flipper read | Flipper write→T5577 | Security |
|---|---|---|---|---|---|---|
| **EM4100/4102** | 125 kHz | ASK/Manchester | ✅ RO | ✅ | ✅ | ⚪ none (static 40-bit) |
| **EM4305** | 125 kHz | ASK | R/W chip | ✅ | n/a (is a blank) | ⚪ none |
| **T5577** | 125 kHz | configurable | R/W chip | ✅ | n/a (is the blank) | ⚪ none |
| **HID Prox (H10301)** | 125 kHz | FSK | ✅ RO | ✅ | ✅ | ⚪ static, tiny FC space |
| **HID Corp 1000 / 48-bit** | 125 kHz | FSK | ✅ RO | ✅ (raw clone) | ✅ if read | ⚪ static (bigger ID space only) |
| **Indala** | 125 kHz | PSK | ✅ RO | ✅ | ✅ | ⚪ static |
| **AWID / Paradox / Keri / ioProx** | 125 kHz | FSK | ✅ RO | ✅ | mostly ✅ `(verify)` | ⚪ static |
| **Viking** | 125 kHz | ASK | ✅ RO | ✅ | ✅ | ⚪ static |
| **NexWatch/Honeywell** | 125 kHz | PSK | ✅ RO | ✅ | ✅ `(verify)` | ⚪ static |
| **FDX-B / FDX-A (animal)** | **134.2 kHz** | FSK | ✅ RO | ⚠️ best-effort | ❌ | ⚪ ID only (off-band) |

---

## 8. Why LF access control is weak (the summary)

1. **No secret.** The card holds a plaintext number; the reader trusts any card that presents a valid number.
2. **No challenge-response.** The reader never asks the card to *prove* it holds a key — there's no key. So a replayed/cloned number is indistinguishable from the original.
3. **Read-on-walk-by.** A few hundred ms of proximity is enough; long-range LF readers extend that.
4. **Tiny, public keyspaces.** Open formats (26-bit HID, EM4100) have small, non-secret facility/ID spaces.
5. **Trivial blanks.** $1 T5577 cards plus a Flipper = a working duplicate.

**Defensive upgrade path:** move doors to **13.56 MHz with real crypto** — MIFARE **DESFire EV2/EV3 (AES)** or HID **iCLASS SEOS (AES)**. Those are *not* clone-on-read. (See [iclass-picopass.md](iclass-picopass.md) and [mifare.md](mifare.md).) If you must keep LF, at least use **custom/long formats** and pair the badge with a PIN — but understand LF remains a convenience layer, never the security layer.

---

## Open questions / to research
- Exact set of LF formats the current Momentum/official firmware can **write** to T5577 vs only read (FSK formats like ioProx/Paradox) — `(verify per-firmware)`.
- T5577 config words the Flipper writes for each emulated format (compare to PM3's `lf t55xx` decodes).
- Whether the Flipper can program **EM4305** directly (not just T5577) from the stock 125 kHz app.
- Real-world FDX-B read-rate on the Flipper vs a vet scanner — distance and success-rate numbers.
- Indala/NexWatch PSK longer proprietary formats: which sub-variants decode cleanly.
- Detection of T5577-based "magic" LF cards by modern access readers (anti-clone heuristics).

## Sources
- Flipper 125 kHz RFID docs: https://docs.flipper.net/zero/rfid
- Flipper product LF format list: https://flipper.net/products/flipper-zero
- Proxmark3 (RRG/Iceman) T5577 guide: https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/T5577_Guide.md
- Proxmark3 EM4102 walkthrough: https://github.com/proxmark/proxmark3/wiki/Walkthrough-of-a-EM4102-tag
- HID "Understanding Card Formats" (H10301 26-bit, parity, FC/CN): https://www.idesco.com/files/articles/HID%20-%20Understanding%20card%20formats.pdf
- Facility-code / Wiegand bit calculator explainer (Kisi): https://www.getkisi.com/blog/how-to-calculate-facility-code-using-card-bit-calculators
- EM4100 vs EM4305 vs T5577 comparison: https://securityidsystems.com/guides/em4100-em4305-t5577/
- EM Microelectronic EM4100 / EM4305 datasheets: https://www.emmicroelectronic.com/product/lf-animal-identification/em4305 · https://www.emmicroelectronic.com/product/lf-read-only/em4100
