---
title: Installed NFC Apps (13.56 MHz) — Runbook
domain: resources
type: reference
status: detailed
summary: Per-app reference for every 13.56 MHz NFC .fap on my Momentum rig — what it does, options, gotchas, sources.
hardware: [flipper-internal]
use_cases: [UC-16, UC-17, UC-18, UC-19, UC-20, UC-21, UC-22, UC-23]
related: [capabilities/nfc-rfid.md, cards/mifare.md, cards/iclass-picopass.md, cards/cloning-matrix.md, theory/relay-attacks.md, my-setup.md, legal-and-safety.md]
tags: [nfc, apps, momentum, mifare, picopass, seader, amiibo, metroflip, ultralight-c]
last_verified: 2026-06-22
---

# Installed NFC Apps (13.56 MHz) — Runbook

> **TL;DR —** A per-app field reference for every HF (13.56 MHz) NFC `.fap` on my Momentum rig: what each does, its key options, concrete use-cases, the gotchas (card type / magic generation / extra hardware), and a source. The card-technology *why* lives in [cards/](../cards/README.md); this is the *which-app-for-what* lookup. **Own cards / authorized targets only** ([legal-and-safety](../legal-and-safety.md)).
> Builds on [capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md) · [cards/mifare.md](../cards/mifare.md) · [cards/iclass-picopass.md](../cards/iclass-picopass.md) · [cards/cloning-matrix.md](../cards/cloning-matrix.md) · [theory/relay-attacks.md](../theory/relay-attacks.md). Part of the [KB](../README.md).

This documents the **13.56 MHz HF** app set installed on my [Flipper](../my-setup.md) (Momentum, maxed app catalog). It is a companion to the capability/theory docs: the [NFC capability overview](../capabilities/nfc-rfid.md) and the [cards/](../cards/README.md) folder explain *how the card technologies work and what is cloneable*; **this doc answers "which installed app do I open, and what are its knobs and traps?"** Everything here is for **cards and credentials I own or am explicitly authorized to test** — the line is in [legal-and-safety.md](../legal-and-safety.md).

> **Scope note.** This is the **HF/NFC** set only — the 125 kHz LF RFID app and its world live in [cards/lf-125khz.md](../cards/lf-125khz.md). All apps below use the **Flipper's internal ST25R3916 NFC front-end** unless an app's row explicitly calls out extra hardware (only **Seader** and the optional **seos** BLE path do). No app here needs the [CC1101](../my-setup.md) or [Marauder](../my-setup.md) backpacks.
>
> **Version/availability flags.** App version numbers are App-Catalog snapshots — treat them as `(verify)`. Catalog availability moves; several of these are GitHub/firmware-distributed rather than first-party.

## The 30-second map

| App (`.fap`) | One-liner | Tier |
|---|---|---|
| **nfc** | Core read / save / emulate / write; the hub every other app feeds | first-party |
| **nfc_magic** | Write UID + block 0 to magic cards (Gen1/Gen2/Gen4) → real clones | first-party |
| **mfkey** | On-device Crypto1 key recovery (mfkey32 + nested) from collected nonces | first-party-ish |
| **mfc_editor** | On-device editor for saved MIFARE Classic `.nfc` dumps | community |
| **mifare_fuzzer** | Emulate cycling/fuzzed UIDs to test a reader | community |
| **nfc_tools** | wakdev read/**write** utility (clean write UX for consumer tags) | community |
| **nfc_apdu_runner** | Run scripts of raw APDUs against ISO-DEP smartcards | community |
| **metroflip** | Read & **parse** transit cards (balance/history), multi-region | community |
| **picopass** | Legacy HID iCLASS / Picopass read/write/emulate + loclass | community (@bettse) |
| **seader** | Read iCLASS **SE / SEOS / DESFire** — **needs external HID SAM** | community (@bettse) |
| **seos** | Experimental no-SAM SEOS-compatible read/emulate (zero-key default) | community (@bettse) |
| **passy** | e-passport / ICAO eMRTD reader (BAC, needs the MRZ) | community (@bettse) |
| **weebo** | Amiibo (NTAG215) emulate / write / remix | community (@bettse) |
| **ami_tool** | Alternate amiibo toolkit (generate/encrypt/decrypt; separate format) | community |
| **iso15693_nfc_writer** | Write ISO15693 (NFC-V) tags — fills a stock-FW gap | community |
| **nfc_maker** | Build NDEF records (URL / Wi-Fi / BT / vCard…) into a `.nfc` | first-party (Momentum) |
| **nfc_eink** | Push images to NFC e-ink price-tag / shelf-label displays | community |
| **ulc_brute** · **ulcfkey** · **ulc_relay** | Ultralight-C (3DES) attack PoCs from one 2026 paper | research PoC |
| **nfc_login** | NFC-gated BadUSB password typer (PC auto-login over HID) | community |
| **saflip** | (unidentified) — likely Saflok/"Unsaflok" hotel-lock related; flagged | **unverified** |

**The backbone chain:** `nfc` (Read → if locked, **Extract MF Keys**) → `mfkey` (crack nonces → keys land in the user dictionary) → `nfc` (re-Read now fully decrypts) → optionally `mfc_editor` (tweak the dump) → `nfc_magic` (write a working clone). Everything else is a specialist branch off that spine.

---

## Core read/clone toolkit

### `nfc` — core NFC app
- **What it does.** The stock 13.56 MHz app: **Read → Save → Emulate → Write**, with automatic card-type detection and community **parsers** that decode contents (e.g. transit balances). Saved dumps are `.nfc` files on the SD that every other app here consumes or produces. This is the hub; deep treatment of the stack and the Crypto1 attack chain is in [capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md) and [cards/mifare.md](../cards/mifare.md).
- **Reads / identifies.** MIFARE Classic (Mini 0.3K / 1K / 4K), MIFARE Ultralight & NTAG21x, MIFARE DESFire (**metadata only** — AES not broken), ISO15693 / NFC-V (e.g. ICODE SLIX), FeliCa (Lite-S), ST25TB (NFC-B), and UID-only "unknown" cards. EMV bank-card public-data parsing (PAN/expiry) is widely reported on current firmware but is not listed among the named families in the read docs `(verify)`.
- **Key options.**
  - **Read** — auto-runs the bundled key **dictionary** (~1200+ common Classic keys `(verify exact count)`).
  - **Extra Actions → Read Specific Card Type** — force a protocol on a hybrid/multi-tech card.
  - **Extra Actions → MIFARE Classic Keys / Ultralight-C Keys** — view/add user keys.
  - **Extract MF Keys** (a.k.a. **Detect Reader**) — emulate the saved card at a *real reader* and harvest its Crypto1 **nonce pairs** (tap several times, ~10 nonces); this is the **mfkey32 collection step**, cracked later in `mfkey`.
  - **Add Manually** — build a virtual card by entering type + UID/data, no physical card.
- **Use-cases.** UC-16 (Classic read/crack/clone), UC-17 (NTAG/Ultralight read & emulate), UC-23 (DESFire/EMV metadata read), back up your own access fob.
- **Gotchas.** Emulation **data-editing** is limited to saved **NTAG/Ultralight** (Crypto1 emulation quirks); DESFire is read-only metadata; mfkey32 needs access to the card's real reader. Many readers reject Flipper **emulation** on timing/UID grounds → a **magic-card clone** ([nfc_magic](#nfc_magic--nfc-magic)) is the reliable duplicate. See [cards/cloning-matrix.md §2](../cards/cloning-matrix.md).
- **Source:** https://docs.flipper.net/zero/nfc/read

### `nfc_magic` — NFC Magic
- **What it does.** Detects whether a card is "magic," then writes a saved `.nfc` (UID + full contents) onto a compatible **magic** card to produce a true clone; also **wipes/restores** magic cards. This is the only sanctioned path to a duplicate that survives a **UID/block-0 check**. Generations and the buying guide are in [cards/cloning-matrix.md §3](../cards/cloning-matrix.md).
- **Supported generations.**
  - **Gen1A / Gen1B** (incl. OTP) — MIFARE Classic 1K/4K via the backdoor wakeup.
  - **Gen2 (DirectWrite / CUID / FUID / UFUID)** — Classic 1K/4K; block 0 written by a normal authenticated write.
  - **Gen4 "Ultimate" (GTU)** — shapeshifter: per Flipper docs emulates **any MIFARE Classic, MIFARE Ultralight EV1/EV2, and NTAG 203/213/215/216**; password-protectable.
- **Key options.** **Check Magic Tag** (identify generation) · **Write** (pick saved original → hold magic card to back) · **Wipe** (reset UID to default, clear data) · **Gen4 Actions** (Auth with Password, config/shadow-mode, direct block-0 write).
- **Use-cases.** UC-18 (magic-card full clone). Pairs with the §3 buying table in cloning-matrix.
- **Gotchas.** **Not** supported: Gen3 (APDU), Gen4 **GDM**, "supercards," and the plain (non-magic) UL/NTAG/DESFire/NFC-V tags. **Fully read every sector/page first** in the core app or the clone is partial. Some Gen2/CUID/UFUID variants have reported per-firmware block-0-write quirks (`(verify)`; Check Magic Tag, then re-read the clone).
- **Source:** https://docs.flipper.net/zero/nfc/magic-cards

### `mfkey` — MIFARE Classic key recovery
- **What it does.** Recovers Crypto1 keys **on the Flipper itself** from nonces the core app collected. Implements **mfkey32** (reader-nonce attack) and the **Nested** family; v3.0 (2024) added **Static Encrypted Nested** `(verify)`. By @noproto.
- **In / out.** **Input:** the nonce files from `nfc` → **Extract MF Keys** (mfkey32), or card-derived nonces (nested). **Output:** recovered keys are written **straight into the user key dictionary**, so the next `nfc` Read of that card decrypts and can be cloned. The same recovery is also reachable in the Flipper mobile app / Flipper Lab.
- **Use-cases.** UC-16 — the "crack" middle step of the read→clone chain in [cards/mifare.md](../cards/mifare.md).
- **Gotchas.** On-device cracking is **slow** (minutes; can exceed ~10 min — limited compute). mfkey32 requires you to have collected reader nonces first; nested needs ≥1 known key on the card. Which nested variants run on-device vs offloaded to phone/web varies `(verify)`.
- **Source:** https://docs.flipper.net/zero/nfc/mfkey32

### `mfc_editor` — MIFARE Classic dump editor
- **What it does.** Views and **edits a saved Classic `.nfc` dump directly on the Flipper** — no PC / MifareClassicTool needed — before you emulate it or write it to a magic card. By TollyH.
- **Edits.** Organized **sector → block**; edit raw block bytes; dedicated editors for the **UID** and the sector-trailer **keys (A/B)**; a per-block **access-bits decoder/editor** that flags and corrects invalid bits; **BCC** validity check + one-tap fix (4-byte-UID cards only). Supports Classic Mini/1K/4K, 4- and 7-byte UID. A value-block-specific arithmetic editor is not documented — value blocks edit as raw bytes `(unverified)`.
- **Use-cases.** Fix a malformed dump, change a UID before writing to a magic card, study access-condition encoding. Pairs with [cards/mifare.md](../cards/mifare.md).
- **Gotchas.** **Shadow files:** a card modified during emulation gets a `.shd`; while it exists the core NFC app reads *that*, not the base `.nfc` — the editor lets you choose. The per-block access view doesn't fully reflect that invalid bits disable the **whole sector**, nor the "Key B readable ⇒ can't auth" rule. Editor only — never touches a physical card.
- **Source:** https://github.com/TollyH/flipper-apps/tree/main/mfc-editor

### `mifare_fuzzer` — Mifare Fuzzer
- **What it does.** Rapidly emulates MIFARE cards with **varying UIDs** to watch how a reader/access controller reacts — emulates **only the UID** (enough for UID-only systems), not full contents.
- **Card types / modes.** Selectable **Classic 1K, Classic 4K, Ultralight**; 4- and 7-byte UIDs. **Load UIDs from a file** (ships `example_uids04/07.txt`) and iterate. An explicit "incrementing-byte" / "TTF" mode is named by some mirrors but **not in the upstream README** `(unverified)`; the naz50 fork adds whole-card emulation from storage.
- **Use-cases.** UC-56-style **defensive**: stress-test your own reader's robustness to malformed/sequential UIDs; QA reader firmware. (Legitimate-use framing in [topics/security-pentest.md](../topics/security-pentest.md).)
- **Gotchas.** UID-only — useless against readers that check sector data/crypto. Community `.fap`, not first-party. WTFPL, minimal docs.
- **Source:** https://github.com/spheeere98/mifare_fuzzer · catalog: https://lab.flipper.net/apps/mifare_fuzzer

### `nfc_tools` — NFC Tools (wakdev)
- **What it does.** A polished **read/write** utility from wakdev (the "NFC Tools" mobile-app maker) with a cleaner **writing** UX than the core app for consumer tags — preserves the input buffer on a failed/cancelled write, auto-retries on failure. **It is a tag read/writer, not a cracking multi-tool.**
- **Supported chips.** NTAG210/212/213/213TT/215/216, Ultralight / Ultralight-C, ICODE SLI/SLIX/SLIX2, MIFARE Classic 1K/4K.
- **Use-cases.** UC-19 (NDEF/tag writing) when you want a smoother write flow than the stock app.
- **Gotchas / disambiguation.** Runs on **official firmware** (not CFW-only). Distinct from `flipperdevices/flipperzero-nfc-tools`, which is a **host/companion** repo, not an on-device app. There is **no evidence** of a separate Momentum-bundled `nfc_tools` multi-tool — the parser/mfkey/Ultralight-C-key features people associate with that name are built into the **core NFC app** in CFW, so "bundled multi-tool" is a likely misattribution `(unverified)`.
- **Source:** https://www.wakdev.com/en/apps/nfc-tools-flipper-zero.html

### `nfc_apdu_runner` — NFC APDU Runner
- **What it does.** Runs **scripts of raw APDU commands** against ISO14443-4 / ISO7816 (ISO-DEP) smartcards: sends each APDU, logs the response. By SpenserCai.
- **Script format.** Plain text, extension **`.apduscr`** (not `.apdu`): a `CardType:` (`iso14443_4a` / `iso14443_4b` support APDU; `iso14443_3a/3b` are recognized but **have no ISO-DEP layer** so APDU won't run) plus a `Data:` array of hex command strings. Responses are written next to it as **`.apdures`** (`In:`/`Out:` pairs, e.g. `Out: 9000`).
- **Use-cases.** Select EMV applications and read banking-card records, probe custom JavaCard/applet AIDs, query travel cards, automate repeatable APDU sequences. A companion **NARD** decoder + web frontend parse the `.apdures` (TLV).
- **Gotchas.** Card **must** support ISO-DEP (ISO14443-4) — plain Classic won't APDU. You supply correct APDUs yourself; the app sends raw bytes and doesn't interpret them.
- **Source:** https://github.com/SpenserCai/nfc_apdu_runner

---

## Transit, toys & makers

### `metroflip` — Metroflip
- **What it does.** A multi-protocol transit-card **reader and parser** (inspired by Metrodroid): reads a card, decodes the proprietary layout, shows **balance and trip/transaction history**. Explicitly a **parser / proof-of-concept — it does not write, top up, or clone**.
- **Coverage (per repo; roster grows — `(verify)`).** Bip! (Santiago), Charliecard (Boston), Clipper (SF), Intertic (FR, 21 cities), ITSO (UK), Metromoney (Tbilisi), myki (Melbourne), Navigo (Paris), Opal (Sydney), Opus (Montreal), Rav-Kav (IL), RENFE (ES), SmartRider (Perth), Suica (JP), Troika (Moscow), Trt (Tianjin), Octopus (HK), nol (Dubai). Underlying tech spans **MIFARE Classic, DESFire, Calypso (unified parser), FeliCa (Suica/Octopus), ST25TB, Ultralight**.
- **Use-cases.** UC-21 (transit card read) — check your own card's balance/journeys, study transit data formats.
- **Gotchas.** **Read-only.** Per-system parsing depends on card region/revision; newer revisions may not parse. Internal NFC only.
- **Source:** https://github.com/luu176/Metroflip · catalog: https://lab.flipper.net/apps/metroflip

### `weebo` — Weebo (amiibo)
- **What it does.** An NTAG215-focused amiibo tool by @bettse: **parse / write / emulate / remix / duplicate**. Emulates an amiibo over NFC straight to a console/Joy-Con (no physical tag), writes a dump to a real NTAG215, and "**remixes**" (re-signs with a fresh valid UID). Built on the amiitool crypto approach.
- **Use-cases.** UC-22 (NFC toys emulate) — emulate amiibo to a Switch, back up your amiibo, generate re-signed copies for UID-gated loot. Cloning context: [cards/cloning-matrix.md §1](../cards/cloning-matrix.md).
- **Gotchas.** **Requires `key_retail.bin`** (Nintendo keys) in `apps_data/weebo/` — not distributed; you supply it. Emulation is live-only (nothing permanent); writing needs a blank/UID-writable NTAG215 (amiibo signature is **UID-bound**). Console enforces a one-scan-per-amiibo-per-day cooldown. Its stored format is **incompatible** with `ami_tool`'s — pick one toolchain.
- **Source:** https://github.com/bettse/weebo

### `ami_tool` — Amiibo toolkit (alternate)
- **What it does.** A separate, independent amiibo toolkit (NTAG215): reads tags, shows character metadata (AmiiboAPI), **generates / encrypts / decrypts** amiibo data, emulates to consoles, writes to blanks, randomizes UIDs, emulates a blank NTAG215. By Firefox2100.
- **Use-cases.** UC-22 — full decrypt → regenerate-UID → re-encrypt → emulate/write workflow plus character ID.
- **Gotchas.** Also needs the proprietary `key_retail.bin`. Its data format is **not interchangeable** with Weebo's. Repo is `ami-tool` ("AmiiboTool"); a renamed successor `flipper-amiibo-toolkit` is likely the same project `(verify which is current)`. Functionally overlaps Weebo — having both installed is redundant; choose per file format.
- **Source:** https://github.com/Firefox2100/ami-tool

### `iso15693_nfc_writer` — ISO15693 NFC Writer
- **What it does.** A community app (Unleashed/RogueMaster lineage) that **writes ISO15693 / NFC-V tags** — a capability the stock firmware lacks (stock reads/saves/emulates NFC-V but doesn't write). Writes saved NfcV `.nfc` data blocks back onto compatible tags. By ch4istO.
- **Use-cases.** UC-19-adjacent — duplicate/restore an ISO15693 tag (e.g. ICODE SLIX family), write NFC-V content to blanks. Background tech: [cards/iclass-picopass.md](../cards/iclass-picopass.md) (iCLASS is the ISO15693 access-control cousin), [cards/nfc-theory.md](../cards/nfc-theory.md).
- **Gotchas.** **Not on the official catalog** (CFW-distributed → not installable from Flipper Lab). Whether it sets **AFI / DSFID / lock bits** is **not documented** — block-write only `(unverified)`. UID changes need a **magic/changeable-UID** ISO15693 blank (the sibling `Julienbxl/SLI-Writer` targets exactly those Gen2 SLIX2/SLIX-L blanks); ICODE OTP/lock bits block rewriting some blocks. No canonical standalone repo URL confirmed `(unverified)`.
- **Source:** https://github.com/Julienbxl/SLI-Writer (closest documented primary source; references `iso15693_nfc_writer`)

### `nfc_maker` — NFC Maker
- **What it does.** An on-Flipper **NDEF record builder** (by @Willy-JL; ships in Momentum / official catalog). Pick a record type, enter data, and it writes a `.nfc` file containing the NDEF payload — then go to **NFC → Saved** to emulate it or write it to a tag.
- **Record types (catalog v2.1).** Plain URL, HTTPS link, **Wi-Fi login (WPA SSID+password)**, **Bluetooth MAC (handover)**, text note, **contact vCard**, mail address, empty. (Phone/SMS and app-store-link types are **not** in the builds I found — `(unverified)/likely absent`.) Targets NTAG 203/213/215/216, plus Classic and SLIX variants; custom UID supported.
- **Use-cases.** UC-19 (NDEF tag writing) — a tap-to-join Wi-Fi tag, URL/business-card tag, BT-pairing tag, all without a PC. Social-engineering framing (NFC baiting) in [theory/human-layer.md](../theory/human-layer.md).
- **Gotchas.** The app builds the file but **doesn't write the tag itself** — emulate/write separately via the core app. **iOS limitation:** Contact vCard and Wi-Fi-login records don't work on iPhones (Android only). Distinct from the unrelated `jaylikesbunda/Flipper-NFC-Maker` web tool.
- **Source:** https://lab.flipper.net/apps/nfc_maker

### `nfc_eink` — NFC E-Ink
- **What it does.** Drives **NFC-powered passive e-ink / e-paper** price-tag and shelf-label displays: pushes a bitmap over NFC to the tag's controller (and can emulate such a tag, or transfer images Flipper→Flipper). By RebornedBrain.
- **Supported displays.** **Waveshare** NFC e-paper 2.13" / 2.7" / 2.9" / 4.2" / 7.5"; **Goodisplay** GDEY0154D67 / GDEY0213B74 / GDEY029T94 / GDEY037T03.
- **Key options.** **Emulate** (act like the e-ink tag toward the vendor app / Proxmark `hf waveshare`) and **Write** (push image to a physical tag or another Flipper). **Write-restriction modes:** Strict (exact screen) / Size (matching res) / Vendor (same maker) / Free. Auto-scales: smaller centered + black fill, larger cropped.
- **Use-cases.** Repurpose a Waveshare/Goodisplay NFC e-paper as a static custom display — name badge, room sign, signage — pushing your own image from the Flipper. Project-idea cousin of [resources/cool-projects.md](cool-projects.md).
- **Gotchas.** Pick the right model/size (mismatches get scaled/cropped per the chosen mode); hold to the tag until the push completes. Different project from the earlier `mogenson/flipperzero-waveshare-nfc` and `bettse/wink` PoCs.
- **Source:** https://github.com/RebornedBrain/nfc_eink · catalog: https://lab.flipper.net/apps/nfc_eink

---

## HID iCLASS / SEOS family

> Read [cards/iclass-picopass.md](../cards/iclass-picopass.md) first — it draws the **legacy (broken) vs SE/SEOS (AES, not broken)** line these three apps live on. The crucial split: **picopass** handles *legacy* on the Flipper alone; **seader** reaches *SE/SEOS/DESFire* but **only with an external HID SAM**; **seos** is an *experimental no-SAM* attempt.

### `picopass` — PicoPass
- **What it does.** Reads / writes / saves / **emulates legacy HID iCLASS / Picopass** (the Picopass chip on the **ISO15693** air interface, *not* 14443A), decodes the Wiegand/**PACS** payload, can change keys, export to LF format, and run two offensive flows: a **dictionary attack** and the **online portion of the loclass attack**. By @bettse. Full theory in [cards/iclass-picopass.md §5](../cards/iclass-picopass.md).
- **Key options.** Read (auto-tries dictionaries) · Write · Save · Emulate · **Loclass (online)** — emulate a CSN sequence and collect the reader's MAC responses · **Elite dict. attack** · **NR-MAC** (capture a reader response to read partial data without the key). Defaults to **iCLASS Legacy, standard key, 3DES**, with a typical HID **CSN** pre-filled.
- **Use-cases.** UC-20 (PicoPass / HID iCLASS) — clone/emulate your own **legacy** fob; audit a reader you own (recover its Elite key); legacy→prox **downgrade** onto a T5577.
- **Gotchas.** Internal NFC only. The **loclass key is computed OFF-device** — the Flipper does the online capture (emulate CSNs, collect MACs until the bar fills); you derive the Elite/custom key on a host (e.g. `loclass.ericbetts.dev`) and drop it into `iclass_elite_dict_user.txt`. The built-in dict is small — community users add the **~700-key iCopy-X leak**. **Cannot** touch **iCLASS SE / SEOS (AES)** → that's Seader. Also fails on non-iCLASS Picopass (e.g. Circuit Laundry), Standard-2 keyset, and Standard-KDF/SE-KDF custom readers.
- **Source:** https://lab.flipper.net/apps/picopass

### `seader` — Seader  ·  ⚠️ needs external SAM hardware
- **What it does.** Reads credentials from **HID iCLASS, iCLASS SE, MIFARE DESFire EV1/EV2, MFC SE, and SEOS** by **delegating the AES/secure crypto to an external HID SAM (Secure Access Module)** wired to the Flipper over UART. The SAM does the authentication + SIO decryption on-chip (exactly as a HID wall reader does internally); the Flipper just shuttles APDUs and never sees the keys. This is what lets a Flipper read the **AES** formats PicoPass alone cannot. By @bettse.
- **Key options.** Read → save (an agnostic format, or a per-type Flipper format — Prox / MFC / iClass / iClass SR); designed to hand off to **picopass** for the write/downgrade step. Granular in-app menus beyond read/save are `(unverified)`.
- **Use-cases.** UC-20 — read an SE/SEOS/DESFire credential you're authorized to test, extract the PACS, then **downgrade** it onto a supported legacy card for a portable test token.
- **Gotchas (the hardware is the whole story).** **Useless without a HID SAM + a UART/mini-SIM adapter.** Sourcing options: the **NARD** add-on (DIY or assembled), **SAMadams** / **Flippermeister** (Red Team Tools), or a **MikroE Smart Card 2 Click** + your own SAM (5V→pin1, GND→8/11/18, TX→pin16, RX→pin15). The HID SAM itself is a **procurement gate** (not freely sold) `(unverified — availability varies)`. You **read + downgrade only** — no re-encoding SEOS/SE. Because it needs a backpack, **note it in [my-setup.md](../my-setup.md)** if I ever buy the SAM — I do **not** own this hardware today.
- **Source:** https://github.com/bettse/seader · test writeup: https://ipvm.com/reports/seader-test

### `seos` — SEOS (experimental, no-SAM)
- **What it does.** A **separate, explicitly experimental** @bettse app (repo `seos_compatible`) attempting to **read/emulate SEOS-compatible** credentials **on the Flipper without a SAM** — a from-scratch software implementation of the SEOS crypto rather than delegating to a HID SAM. Distinct from Seader.
- **Key options.** Defaults to **all-zero AES keys**; supports **custom AES keys via text files** and a customizable **ADF OID**; an experimental **BLE** path needs **nRF52840** hardware.
- **Use-cases.** UC-20 — research against SEOS-**compatible** cards where *you hold the keys* (your own provisioned test cards); emulating such a credential.
- **Gotchas — heavily flagged.** **Incomplete and experimental** — the README's own TODO lists unfinished core pieces (ISO14443-4 framing, ASN.1, message wrapping); author disclaims compatibility/functionality. Because it defaults to **zero keys**, it does **not** break real HID-keyed SEOS deployments — real-world success is `(unverified)`. Relationship: **Seader = SAM-based, works today; seos = no-SAM software attempt, experimental; picopass = can't do SEOS at all.** Catalog-name "seos" vs repo "seos_compatible" appear to be the same project `(unverified)`.
- **Source:** https://github.com/bettse/seos_compatible

---

## Passports & smartcards

### `passy` — Passy (e-passport reader)
- **What it does.** An **ICAO eMRTD reader**: reads and decodes the NFC chip in a biometric passport over **ISO 14443-4**, implementing **ICAO 9303**. Uses the **MRZ** (machine-readable zone) to derive the access keys. By @bettse.
- **Key options.** Enter the three MRZ-derived secrets on the Flipper — **passport number, date of birth, expiry date** — which seed the **BAC** key derivation. An **Advanced** menu (needs Debug mode) exposes additional/raw data groups.
- **Use-cases.** Read **your own** passport's chip to inspect what it stores; verify the chip works; learn ICAO 9303 / BAC. (No clean existing UC-ID — closest is the UC-23 "read public metadata" spirit; left out of frontmatter to avoid misattribution.)
- **Gotchas.** **BAC only — no PACE** (PACE is roadmap), so newer **PACE-only** chips (increasingly common in EU issuance) may not read `(verify by issuer)`. Wrong MRZ ⇒ keys won't derive ⇒ no access. **DG1 (personal data)** reading is consistent with BAC; full **DG2 (facial image)** extraction/parsing is `(unverified)` — several data groups are explicitly not fully parsed. ~33 countries tested; software-only, internal NFC.
- **Source:** https://github.com/bettse/passy

---

## Ultralight-C (3DES) attack PoCs — one 2026 research project

> **All three (`ulc_brute`, `ulcfkey`, `ulc_relay`) come from a single paper:** *"BREAKMEIFYOUCAN!": Exploiting Keyspace Reduction and Relay Attacks in 3DES and AES-protected NFC Technologies* — **IACR ePrint 2026/100** (2026-01-20), presented at **Hardwear.io USA 2026**. Code: **`github.com/zc-public/breakme-resources`** (`flipper_apps/`). These are **recent (2026) research proof-of-concepts, not App-Catalog apps** — treat per-app specifics as `(unverified)`; the load-bearing detail lives in the paper body. Disclosure with NXP ran from mid-2025. Strictly own-card / authorized research; this doc deliberately gives **no attack recipe** — see [theory/relay-attacks.md](../theory/relay-attacks.md) for the relay attack class and [cards/mifare.md](../cards/mifare.md) for the Ultralight-C 3DES background.
>
> Context worth keeping: the NXP **factory-default Ultralight-C 3DES key is the ASCII string `BREAKMEIFYOUCAN!`** (`425245414b4d454946594f5543414e21`) — a deliberate 2008 NXP nod, and literally the paper's title. **Checking that default is a stock-NFC-app / dictionary function**, not what `ulcfkey` does (a common misconception — corrected below).

### `ulc_brute` (+ `ulc_brute_optimized`)
- **What it does.** Implements the paper's **§7 "Keyspace Reduction via 75% Key Overwrite Relay"** brute force: Ultralight-C's 16-byte (112-bit) 2-key 3DES is far too large to brute head-on, so the attack first **reduces the unknown keyspace** (via a relay/overwrite primitive) until the remainder is brute-forceable. `ulc_brute_optimized` implements **§10.1 "Online Enhancements"** (faster on-card search).
- **Gotchas.** Depends on the keyspace-reduction precondition (the relay/overwrite step) — **raw 112-bit 3DES is not brute-forceable on a Flipper**. Runtimes are in the paper, not the README `(unverified)`. Internal NFC.
- **Source:** https://github.com/zc-public/breakme-resources/blob/main/flipper_apps/README.md

### `ulcfkey` (repo `ulcf_key`, + `ulcf_key_next`)
- **What it does.** **Not** a default-key checker. Implements **§11.5 "Comprehensive Recovery Process for ULCG, FJ8010, and USCUID-UL"** — recovers the 3DES key from **counterfeit / magic Ultralight-C clone chips** (ULCG, FJ8010, USCUID-UL) by exploiting weaknesses in *those clones*, **not** genuine NXP silicon. `ulcf_key_next` adds **tearing** (power-glitch) support; a host-side `ulcfkey_pc` companion is referenced but its exact role is `(unverified)`. A "recovers in under a minute" claim circulates but I could not confirm it in the README `(unverified)`.
- **Relationship.** Complementary to `ulc_brute`: brute defeats the *crypto* on genuine cards via keyspace reduction; `ulcfkey` defeats *flawed clone implementations*. Different card populations.
- **Source:** https://github.com/zc-public/breakme-resources/blob/main/flipper_apps/README.md

### `ulc_relay`
- **What it does.** Implements **§4 "Relay Attack Against Ultralight C"** — relays the 3DES challenge/response between a genuine card and a reader (and is the enabling primitive for the §7 key-overwrite step feeding `ulc_brute`). Topology (two Flippers? Flipper+host? transport?) is `(unverified)` for this specific app.
- **Disambiguation.** A separate, older, generic **`leommxj/nfc_relay`** relays NFC-A APDUs between **two Flippers over UART** (pins C1/C0, 38400 baud; optional internet relay via ESP32 + `socat`). If the installed file is plain `nfc_relay` it's most likely **leommxj's**; `ulc_relay` is the BREAKMEIFYOUCAN one. Relay attack class: [theory/relay-attacks.md](../theory/relay-attacks.md).
- **Source:** https://github.com/zc-public/breakme-resources/blob/main/flipper_apps/README.md · generic: https://github.com/leommxj/nfc_relay

---

## Login & flagged

### `nfc_login` — NFC PC Login
- **What it does.** "NFC PC Login" by **Play2BReal** (on the official catalog): essentially a **BadUSB password-typer gated by NFC** — the Flipper acts as a **USB HID keyboard** and types your PC login password, but the action is **triggered/secured by an NFC tag** rather than firing blindly.
- **How it works.** HID into the PC (same channel as [BadUSB](../capabilities/badusb.md)), so it works at the OS login prompt by *typing* — **no host-side agent/PAM module required**. The NFC element gates which credential is sent / requires tag presence (exact tag-binding UX `(unverified)`).
- **Use-cases.** Convenience auto-login to a personal PC; demoing why unattended USB ports are risky ([theory/human-layer.md](../theory/human-layer.md)).
- **Gotchas.** Because it *types* a password over HID it's OS-agnostic in principle, but it's **no stronger than a typed password** — not cryptographic 2FA (contrast a real FIDO/U2F second factor, [01-architecture.md UC-53](../01-architecture.md)). Needs USB at login. Distinct from the `linux_pam_nfc` (ACR122 + Android) project, which has no Flipper involvement.
- **Source:** https://lab.flipper.net/apps/nfc_login

### `saflip` — (unidentified; likely Saflok / "Unsaflok" related) ⚠️
- **Status — flagged.** **Could not confirm any publicly released Flipper app named `saflip` (or `unsaflok`) online.** Best hypothesis from the name: a private/reverse-engineered tool related to the **Saflok / "Unsaflok"** hotel-lock vulnerabilities. Treat as **(unidentified/unverified)**.
- **What "Unsaflok" is (high level only).** A 2024 set of vulnerabilities in **dormakaba Saflok** (MIFARE Classic-based, 13.56 MHz) RFID hotel locks — combining the flaws lets a forged keycard, derived from data on any card for a property, open other doors. Affects ~**3M+ locks in 131 countries**; disclosed March 2024 (Lennert Wouters, Ian Carroll, et al.); reported to dormakaba in 2022. The researchers **deliberately did not release a PoC**.
- **Legality / handling.** **Strongly sensitive.** Forging hotel keycards to enter rooms you aren't authorized to is **illegal** essentially everywhere ([legal-and-safety.md](../legal-and-safety.md)), independent of the tech. Documented here as a *disclosed vulnerability*, **not a how-to** — and only a property owner/operator can authorize testing their own locks. If this `.fap` is on the device, **identify what it actually is before running it**.
- **Source:** https://unsaflok.com/

---

## Open questions / to research
- Confirm `saflip`'s real identity by reading the on-device `.fap`/its manifest (not done here — research-only task). It may be benign or a renamed app.
- Whether the core `nfc` app on my exact Momentum build parses **EMV** public fields, and how deep (PAN/expiry/tx-log).
- `mfkey`: which **nested** variants run fully on-device vs. require phone/web offload on the current build.
- `seos_compatible`: any real-world SEOS-compatible card it works against beyond zero-key test cards, and the **nRF52840 BLE** path status.
- `passy`: PACE support arrival, and whether **DG2 (photo)** parsing works on current builds; which issuers are PACE-only.
- BREAKMEIFYOUCAN: pull **eprint 2026/100** PDF for exact runtimes, the relay topology of `ulc_relay`, and `ulcf_key_pc`'s precise role; verify whether any of these are packaged for Momentum vs. build-from-source only.
- `iso15693_nfc_writer`: confirm AFI/DSFID/lock-bit support and pin the canonical repo; verify whether Momentum bundles it or it's Unleashed-only.
- `nfc_magic`: re-confirm Gen2/CUID/UFUID block-0-write reliability on the current Momentum build (per-revision quirks — cross-ref [cards/cloning-matrix.md](../cards/cloning-matrix.md)).
- `ami_tool` vs `weebo`: which to keep (file formats are incompatible); confirm the current `ami-tool` vs `flipper-amiibo-toolkit` repo.

## Sources
- Core NFC / mfkey32 / magic: https://docs.flipper.net/zero/nfc/read · https://docs.flipper.net/zero/nfc/mfkey32 · https://docs.flipper.net/zero/nfc/magic-cards
- mfc_editor: https://github.com/TollyH/flipper-apps/tree/main/mfc-editor · mifare_fuzzer: https://github.com/spheeere98/mifare_fuzzer
- nfc_tools (wakdev): https://www.wakdev.com/en/apps/nfc-tools-flipper-zero.html · APDU runner: https://github.com/SpenserCai/nfc_apdu_runner
- Metroflip: https://github.com/luu176/Metroflip · catalog: https://lab.flipper.net/apps/metroflip
- weebo: https://github.com/bettse/weebo · ami_tool: https://github.com/Firefox2100/ami-tool
- iso15693 writer (closest primary): https://github.com/Julienbxl/SLI-Writer · nfc_maker: https://lab.flipper.net/apps/nfc_maker · nfc_eink: https://github.com/RebornedBrain/nfc_eink
- picopass: https://lab.flipper.net/apps/picopass · seader: https://github.com/bettse/seader · seader test: https://ipvm.com/reports/seader-test · seos: https://github.com/bettse/seos_compatible · passy: https://github.com/bettse/passy
- BREAKMEIFYOUCAN (ulc_brute/ulcfkey/ulc_relay): https://breakmeifyoucan.com/ · paper: https://eprint.iacr.org/2026/100 · repo: https://github.com/zc-public/breakme-resources · generic relay: https://github.com/leommxj/nfc_relay
- Ultralight-C default 3DES key: https://www.nxp.com/docs/en/data-sheet/MF0ICU2.pdf
- nfc_login: https://lab.flipper.net/apps/nfc_login · saflip/Unsaflok (vuln, not a recipe): https://unsaflok.com/
