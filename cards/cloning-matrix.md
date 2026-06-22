---
title: Card Cloning — Practical Matrix
domain: cards
type: reference
status: detailed
summary: What's cloneable + how, magic cards, and a blanks list
hardware: [flipper-internal]
use_cases: []
related: [cards/mifare.md, cards/lf-125khz.md, cards/iclass-picopass.md, cards/nfc-theory.md, capabilities/nfc-rfid.md, capabilities/ibutton.md]
tags: [cloning, magic-cards, t5577, gen1a, gen4, blanks, uid-cloning]
last_verified: 2026-06-19
---

# Card Cloning — Practical Matrix

> **TL;DR —** The payoff lookup for the cards folder: given a card in hand, what the Flipper can duplicate, by what method and onto which blank — the cloneability matrix, the magic-card generations, and a blanks shopping list (modern crypto cards can't be cloned at all).
> Builds on [./mifare.md](./mifare.md), [./lf-125khz.md](./lf-125khz.md), [./iclass-picopass.md](./iclass-picopass.md), [./nfc-theory.md](./nfc-theory.md). Part of the [Cards hub](README.md) · [KB](../README.md).

This is the payoff doc for the cards folder: **given a card in hand, can the Flipper duplicate it, by what method, and onto what blank?** The per-family docs hold the *why*; this one is the lookup table plus the magic-card buying guide and the end-to-end workflow.

> **Authorized use only.** Everything here is for **cards and credentials you own or are explicitly authorized to duplicate** — backing up your own apartment fob, re-keying your own gym tag, restoring your own amiibo, auditing your own building. Cloning a credential you don't control is the line in [../legal-and-safety.md](../legal-and-safety.md); treat it as off-limits. This doc deliberately does **not** give recipes for defeating access systems you don't own — the hard part of any real clone (recovering someone else's keys) is exactly what stays out. The honest headline is that **modern crypto cards can't be cloned at all** (§5), and the only things that clone trivially are the ones that were never really secured.

---

## 1. Cloneability matrix

Read "Cloneable on Flipper?" as: **Yes** = a working duplicate of *your* card is realistic with stock/CFW tooling; **Partial** = UID or partial data only, or needs key recovery / luck / add-on hardware; **No** = the cryptography defeats duplication, full stop.

| Card / chip | Cloneable? | Method (Flipper) | Blank / magic needed | Notes & limits |
|---|---|---|---|---|
| **EM4100 / EM4102** (LF) | ✅ Yes | `125 kHz RFID → Read → Save → Write` | **T5577** (or EM4305) | Static 40-bit ID, no auth. Source EM4100 is read-only; you clone *onto* a T5577. Trivial. |
| **HID Prox** (H10301 etc., LF) | ✅ Yes | Read → Save → Write | **T5577** | T5577 emulates the HID waveform. Facility code + card # are just bits. Some exotic HID formats only partially parsed → [lf-125khz.md](./lf-125khz.md). |
| **Indala** (LF) | ✅ Yes | Read → Save → Write | **T5577** | PSK format; T5577 reproduces it. Field byte-order varies by integrator (verify the copy reads back). |
| **AWID** (LF) | ✅ Yes | Read → Save → Write | **T5577** | FSK legacy format; supported on current FW. |
| **T5577** (LF) | ✅ Yes (it *is* the target) | Write any LF profile to it | — (it's the blank) | The universal LF clone target; configured to *be* EM/HID/Indala/etc. Not a credential itself. |
| **MIFARE Classic 1K/4K** (HF) | ⚠️ Partial → Yes | Read + recover keys → dump → write to magic | **Gen1a / Gen2-CUID** magic Classic | Cloneable **only once all sector keys are recovered** (dictionary/mfkey32/nested/hardnested — [mifare.md](./mifare.md)). Crypto1 is broken, so for *your* card this usually works; hardened cards can stall. Block 0/UID needs a magic card. |
| **MIFARE Ultralight / NTAG21x** (HF) | ✅ Yes (mostly) | Read → write to blank/emulate | Blank UL/NTAG; **magic UL/NTAG** if UID must match | Little/no auth. NDEF copies freely. If a reader checks the **locked UID** or a PWD page, you need a UID-writable magic NTAG (§3) and the password. |
| **MIFARE DESFire EV1/EV2/EV3** (HF) | ❌ No | Read app/file *metadata* only | — | **AES/3DES, not broken.** No key recovery, no dump, no clone. Flipper reads structure, never secrets. §5. |
| **iCLASS legacy / Picopass** (HF) | ⚠️ Partial | PicoPass app: read (if default/known keys) → write | **Picopass 2k** blank or **T5577** (LF downgrade) | Weak legacy crypto; works **only if the card still uses default/known keys** (often re-keyed on personalization). Your own legacy card may clone; a personalized one may not. → [iclass-picopass.md](./iclass-picopass.md). |
| **iCLASS SE / SEOS** (HF) | ❌ No (stock) | Read CSN/metadata only | — | **AES + Secure Identity Object.** No card-only attack. "Downgrade" paths exist but need extra hardware (NARD/SAM) and a reader left in a permissive config — out of scope here. §5. |
| **EMV bank card** (HF) | ❌ No | Read some public data (PAN, expiry) | — | Per-transaction cryptogram (CDA/DDA) defeats replay. No CVV, no keys, **cannot pay**. Privacy demo only. §5. |
| **amiibo (NTAG215)** (HF) | ⚠️ Partial | Write `.nfc`/converted `.bin` to blank, or emulate | **Blank NTAG215** (or magic NTAG215 for UID match) | You can write/emulate amiibo data. **But Nintendo's signature is bound to the tag UID** — a plain blank has a different fixed UID, so a byte-for-byte "clone" of *one specific* amiibo needs a **UID-writable** NTAG215. Emulation + community dumps are the usual path. |
| **iButton** (DS1990A etc., contact) | ✅ Yes (cross-ref) | iButton app: Read → Save → Write | **RW1990** (rewritable blank) | Not RFID — 1-Wire contact key. Static 64-bit ROM, no crypto. See [../capabilities/ibutton.md](../capabilities/ibutton.md). |

**One-line read of the table:** LF prox, iButton, and most UL/NTAG = trivially cloneable (no real security). MIFARE Classic = cloneable once you've cracked Crypto1 (feasible for your own card). DESFire EV1+, iCLASS SEOS, EMV = **not cloneable** because the crypto actually works.

---

## 2. UID-only vs full-content cloning

The single most useful question before cloning an HF card: **does the reader check just the UID, or the encrypted contents too?** This decides whether you need a 5-minute job or a full key-recovery campaign.

| | **UID-only clone** | **Full-content clone** |
|---|---|---|
| What the reader trusts | Just the 4/7-byte UID (anticollision serial) | UID **+** sector/file data **+** live crypto handshake |
| Typical systems | Cheap access controllers, hobby projects, some time-clocks, lots of "tap = my number" setups | Proper MIFARE Classic deployments, transit, anything using DESFire/SEOS |
| What you need | The UID (emulate it) **or** a magic card with block 0 written | All keys recovered + every block dumped + a card that does live crypto |
| Flipper effort | Minimal — emulate, or one magic-card write | Read + dictionary + mfkey32/nested/hardnested + magic clone, **or impossible** (AES) |
| Fails when | Reader also validates a sector/MAC | A single key won't crack, or the cipher is AES |

**Emulation vs a physical clone** is a second axis. Flipper **emulation** (it pretends to *be* the card) is great for UID-only readers and for testing, but many real readers reject it on **timing/UID quirks** — which is exactly why a **magic-card physical clone** is the reliable way to make a duplicate that behaves like a genuine card. Rule of thumb: *emulate to test, clone to a magic card to keep.*

---

## 3. Magic cards deep dive

A normal MIFARE Classic has a **factory-locked block 0** (the UID and manufacturer bytes are read-only). "Magic" cards are aftermarket Classic clones that expose a way to rewrite block 0, so you can make the UID match your original. They differ in *how* block 0 is unlocked and *how many times* you can write it. The Flipper's **NFC Magic** app drives the common ones; the Proxmark3 RRG/Iceman `magic_cards_notes.md` is the canonical catalogue (and the source for the mechanics below).

### How each generation works

| Gen | Unlock mechanism | Block-0 writes | UID len | Identify (`hf mf info`) | Notes |
|---|---|---|---|---|---|
| **Gen1a** ("UID", classic Chinese magic) | **Backdoor "magic wakeup"** commands (`40`/`43`, then `A0` write) — outside the normal protocol, **no key needed** | Repeatable | 4-byte | "Gen 1a"; tell-tale static PRNG `01200145` | The original magic card. Flipper writes it directly via the backdoor. Cheap, ubiquitous, well supported. |
| **Gen1b** | Same backdoor family as Gen1a (read/write after wakeup) | Repeatable (some OTP variants) | 4-byte | "Gen 1b" | A filter-bypass variant of Gen1a; behaves the same for cloning. |
| **Gen2 / CUID** ("DirectWrite") | **No backdoor** — block 0 accepts a *normal* authenticated write like any other block | Repeatable | 4-byte **and** 7-byte | "Gen 2 / CUID" | More reader-/Android-compatible (no weird wakeup). Needs a key to auth to block 0. Several sub-flavours differ in ATQA/SAK/ATS. |
| **FUID** ("write-once") | DirectWrite while UID is at default `AA55C396` (backdoor exists on older revs) | **One-time** — block 0 locks after first write | 4-byte | "Write Once / FUID" | Writes once, then looks/behaves like a *genuine* fixed-UID card. Good when you want an un-rewritable, convincing duplicate. |
| **UFUID** ("sealable") | Gen1a-style backdoor; can be **sealed** to stop further writes | Repeatable **until sealed** | 4-byte | reports as "Gen 1a" (+ USCUID) | The "best of both": rewrite freely while testing, then seal to make it permanent. |
| **Gen3 / APDU** | Special **APDU** commands (`90 F0…` block 0; `90 FB…` UID-only) | Repeatable | 4-byte **and** 7-byte | "Gen 3 / APDU" | Writing block 0 auto-fixes BCC and ATQA/SAK. Android-friendly. Less common in stock Flipper flows. |
| **Gen4 / GTU** ("Ultimate Magic" / USCUID / GDM) | **Magic-auth** (`8000`) + config registers; a configurable shapeshifter | Repeatable (shadow mode persists) | 4-byte **and** 7-byte | "Gen 4 GDM / USCUID" | The premium chip. Emulates **many** card types, password-protectable, "shadow mode" auto-restores block 0. Can impersonate **Ultralight/NTAG** as well as Classic (see UL magic below). |

### UID-writable Ultralight / NTAG ("magic NTAG")

Cloning a card that checks an **Ultralight/NTAG UID** (e.g. a specific amiibo, or a UL-based access tag) needs a UID-writable UL chip, not a Classic magic card. The notes catalogue several: **NTAG21x "magic"/DirectWrite** (uses `A0` to write normally-locked pages, repeatable, 4-byte UID), **UL Gen2/EV1 DirectWrite**, and **Gen4/UMC** parts that *emulate* Ultralight while exposing magic features. On Flipper the practical route is a **Gen4 Ultimate configured as NTAG215**, which the NFC Magic app explicitly supports.

### How the Flipper writes each (NFC Magic app)

Per Flipper's own docs, the NFC Magic app supports three buckets:

| In NFC Magic | Covers | Can emulate |
|---|---|---|
| **Gen1** | Gen1a/Gen1b (incl. OTP) | MIFARE Classic 1K |
| **Gen2** | Gen2 / CUID / FUID / UFUID (DirectWrite) | MIFARE Classic 1K **or** 4K |
| **Gen4 (Ultimate)** | USCUID/GTU | **any** MIFARE Classic, **MIFARE Ultralight EV1/EV2, NTAG 203/213/215/216** |

Workflow in the app: **Read & Save the original in the NFC app first → NFC Magic → "Check Magic Tag"** (confirms the blank's generation) → for password-protected Gen4, **Gen4 Actions → Auth with Password** → **Write → pick the saved original → hold the magic card to the back**. There's also a **Wipe** to reset a magic card's UID to default and clear it.

### Which magic card to buy for which clone

| You want to clone… | Buy this | Why |
|---|---|---|
| Your MIFARE Classic 1K, rewrite freely while learning | **Gen1a** (or **Gen2-CUID**) 1K | Cheapest, best supported; Gen2 if you need better reader/Android compatibility |
| Your Classic **4K** | **Gen2-CUID 4K** | Gen1a is typically 1K-only; Gen2 comes in 4K |
| A **7-byte UID** Classic | **Gen2** or **Gen4** | Gen1a is 4-byte only; Gen2/Gen4 do 7-byte |
| A permanent, convincing duplicate (no further writes) | **FUID** (write-once) or **UFUID** then seal | Locks to look like a genuine fixed-UID card |
| One card that can *become* many cards (incl. UL/NTAG, amiibo) | **Gen4 "Ultimate" (GTU)** | Shapeshifter; Classic + Ultralight/NTAG, password-protectable |
| A specific **amiibo** byte-for-byte (UID-matched) | **Gen4 as NTAG215**, or a **UID-writable NTAG215** | Amiibo signature is UID-bound (§1) |

> **Caveat (verify):** specific Gen2/CUID/UFUID variants have reported block-0-write quirks on some Flipper firmware revisions; "Check Magic Tag" first, and re-read the clone to confirm. Cross-ref the magic notes in [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md).

---

## 4. General workflow (identify → clone → verify)

The same five steps apply to almost every clone; the middle steps collapse for trivial (LF / UID-only) cards and balloon for MIFARE Classic.

1. **Identify the card.** Read it (`NFC → Read` or `125 kHz RFID → Read`). Note **band** (LF vs HF), **type/SAK/ATQA**, UID length, and which **security tier** it's in ([nfc-theory.md](./nfc-theory.md) for the protocol cues). This decides everything downstream.
2. **Read / recover keys (HF Classic only).** Run the on-device dictionary; if sectors stay locked, escalate: **mfkey32** (harvest the reader's keys via *Extract MF Keys*), then **nested / hardnested** for the rest — full chain in [mifare.md](./mifare.md). LF and UID-only cards skip this entirely.
3. **Dump.** With keys in hand (or no keys needed), save the full card. Confirm every sector/page actually read — a partial dump makes a partial clone.
4. **Pick the right blank / magic.** LF → **T5577**. UID-only HF → a **magic card** (any gen that matches UID length). Full Classic → **Gen1a/Gen2** (4K → Gen2-4K; 7-byte → Gen2/Gen4). UL/NTAG/amiibo → **blank or magic NTAG / Gen4-as-NTAG**. Use §3's buying table.
5. **Write or emulate, then verify against the reader.** Write the dump to the blank (RFID `Write`, or NFC Magic `Write`), **re-read the clone** to confirm UID + data match the original, then **test it on the actual reader you own**. If emulation is flaky on that reader, fall back to a magic-card physical clone (§2). A clone that reads back correctly but the reader rejects = UID-only-vs-full-content mismatch, missing keys, or emulation timing.

---

## 5. What you CAN'T clone (and why)

This is the important half. The cards that matter for security are designed so that **holding the card and a Flipper gives you nothing cloneable**. The dividing line is **modern symmetric crypto with a per-transaction challenge** — there is no card-only attack, so "read it and copy it" simply doesn't exist. Maps to the **security tiers** in [../capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md) (⚪ plain ID → 🟠 broken crypto → 🟢 modern crypto).

| Can't clone | Why (mechanism) | What Flipper *can* do |
|---|---|---|
| **Rolling-code / challenge-response** credentials | Reader sends a fresh **challenge**; card returns a response from a secret key. A captured exchange is **single-use** — replay fails. (Same principle as Sub-GHz rolling codes — [../legal-and-safety.md](../legal-and-safety.md).) | Observe, sometimes read a serial; never reproduce a valid response |
| **MIFARE DESFire EV1/EV2/EV3, DESFire Light** | **AES-128 / 3DES** mutual authentication, diversified keys. Crypto1's breaks don't apply; **not broken**. | Read **app/file structure metadata** only — never the keys or contents |
| **iCLASS SE / SEOS** | **AES** + **Secure Identity Object (SIO)**; no card-only attack vector. Downgrade tricks need extra hardware (NARD/SAM) **and** a permissively-configured reader — not a card clone, and out of scope here. | Read CSN/metadata; legacy iCLASS only if it still has default keys (§1) |
| **EMV bank cards (Visa/Mastercard contactless)** | Each tap produces a unique **cryptogram (CDA/DDA)** signed by a key that never leaves the chip. Replaying a tap is worthless; the PAN/expiry that *are* readable can't authorize a payment. | Read **some public data** (PAN, expiry, sometimes a tx log). **No CVV, no keys, no payment.** |
| **A specific signed NTAG (e.g. one real amiibo) onto a plain blank** | Nintendo's signature is bound to the **tag's hard-coded UID**; a normal blank has a different, locked UID, so the signature won't match. | Emulate, or write to a **UID-writable** NTAG215 so the UID (and thus signature) lines up (§1) |

> **The honest summary:** if a card uses **AES** (DESFire EV1+, SEOS) or a **per-transaction cryptogram** (EMV, rolling codes), the Flipper **cannot duplicate it** — not "slowly," not "with the right plugin," *not at all* from the card alone. The only things that clone easily are the credentials that never had real security (LF prox, plain UID checks, iButton). That asymmetry is the whole point of the matrix.

---

## 6. Blanks shopping list

Keep these on hand to cover authorized cloning of your own credentials. (Pricing/availability move; buy from listings that match the exact part.)

| Blank | For | Notes |
|---|---|---|
| **T5577** (cards / fobs / stickers) | The **universal LF clone target** — EM4100, HID Prox, Indala, AWID, Pyramid, etc. | What "RFID Write" almost always targets. **Buy listings that say _only_ T5577** — "T5577/EM4305" combo listings may ship EM4305, which the **Flipper can't write the same way**. |
| **EM4305** | Rewritable EM-family; ISO11784/85 **animal microchip** (FDX-B) format | Niche vs T5577; useful for EM/animal-ID work. Don't buy it expecting a universal LF blank. |
| **Magic MIFARE Classic 1K — Gen1a** | Cheap, best-supported Classic clones; rewrite freely | 4-byte UID; backdoor write. The default magic Classic. |
| **Magic MIFARE Classic — Gen2 / CUID** | **4K** clones, **7-byte** UID, better reader/Android compatibility | DirectWrite (needs a key to write block 0). Get the **4K** version for 4K cards. |
| **FUID / UFUID** (optional) | A **permanent**, genuine-looking duplicate (write-once, or write-then-seal) | Use when you don't want the clone to stay rewritable. |
| **Magic NTAG215 / Gen4 "Ultimate"** | **amiibo** (UID-matched), UL/NTAG clones, one-card-many-types | Gen4 also covers Classic + UL/NTAG and is password-protectable; pricier. |
| **RW1990** (iButton blank) | **iButton / Dallas** contact-key clones | Not RFID — 1-Wire. Pairs with [../capabilities/ibutton.md](../capabilities/ibutton.md). |

A minimal personal kit: **a few T5577**, **a couple of Gen1a Classic 1K**, **one Gen2-CUID (4K)**, **one Gen4 / magic NTAG215**, and **a couple of RW1990** — covers nearly all authorized clones across both bands and the contact keys. See [../my-use-cases.md](../my-use-cases.md) for how these map onto the owner's actual cards.

---

## Open questions / to research
- Which Gen2 **CUID / UFUID** variants reliably accept block-0 writes on the **latest** Flipper firmware (reported per-revision quirks) — needs hands-on verification.
- Exact NFC Magic behaviour for **Gen4 Ultimate emulating NTAG216** vs 215 (page count / signature handling).
- Whether current Flipper firmware exposes any **iCLASS legacy write-to-Picopass** flow natively, or if that stays Proxmark3-only (NARD/SAM add-on status).
- Practical hit-rate of **default-key iCLASS legacy** clones on real-world personalized cards (how often keys are actually changed).
- amiibo: cleanest current path for a **UID-matched** physical clone on Flipper (magic NTAG215 sourcing + write flow).
- LF: full list of formats T5577 can be made to emulate via Flipper beyond EM/HID/Indala/AWID (Pyramid, Keri, Paradox…).

## Sources
- Proxmark3 RRG/Iceman — magic card notes (authoritative): https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/magic_cards_notes.md
- Proxmark3 RRG/Iceman — cheatsheet (iCLASS/MIFARE commands): https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/cheatsheet.md
- Flipper NFC — writing to magic cards: https://docs.flipper.net/zero/nfc/magic-cards
- Flipper NFC docs: https://docs.flipper.net/zero/nfc · RFID 125 kHz write: https://docs.flipper.net/zero/rfid/write-data
- Flipper RFID deep dive (blog): https://blog.flipper.net/rfid/
- Flipper Community Wiki — 125 kHz overview: https://flipper.wiki/125khz-rfid-overview/ · MIFARE Classic: https://flipper.wiki/mifareclassic/
- HID iCLASS/SEOS downgrade background (context, not a recipe): https://github.com/RfidResearchGroup/proxmark3/blob/master/doc/hid_downgrade.md
- amiibo / NTAG215 on Flipper: https://deepwiki.com/UberGuidoZ/Flipper/6.1-amiibo-emulation · https://kevinbrewster.github.io/Amiibo-Reverse-Engineering/
- EM4100 vs EM4305 vs T5577 chip comparison: https://securityidsystems.com/guides/em4100-em4305-t5577/
