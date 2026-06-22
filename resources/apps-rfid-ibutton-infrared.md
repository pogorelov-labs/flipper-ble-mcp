---
title: Installed Apps — LF RFID, iButton & Infrared
domain: resources
type: reference
status: detailed
summary: Per-app runbook for the LF RFID (125 kHz), iButton/1-Wire, and Infrared apps on the owner's maxed Momentum rig.
hardware: [flipper-internal]
use_cases: [UC-01, UC-02, UC-03, UC-15, UC-24]
related: [cards/lf-125khz.md, capabilities/ibutton.md, capabilities/infrared.md, capabilities/nfc-rfid.md, cards/cloning-matrix.md, my-setup.md, resources/notable-apps-and-data.md]
tags: [lfrfid, t5577, ibutton, infrared, rfid-fuzzer, uhf-rfid, xremote, momentum]
last_verified: 2026-06-22
---

# Installed Apps — LF RFID, iButton & Infrared

> **TL;DR —** Runbook for the three "contact + short-range" app families on the owner's maxed Momentum app set: **LF RFID 125 kHz** (core `lfrfid` + fuzzer, T5577 writers, EM4100 generator, UHF readers), **iButton/1-Wire** (core + fuzzer + format converter), and **Infrared** (core + XRemote/Cross-Remote, custom layouts, IR scope, intervalometer). Each entry: what it does, key options, use-cases, gotchas/required chips-or-hardware, source.
> Theory & protocols live in [cards/lf-125khz.md](../cards/lf-125khz.md), [capabilities/ibutton.md](../capabilities/ibutton.md), [capabilities/infrared.md](../capabilities/infrared.md). The rig: [my-setup.md](../my-setup.md). Part of the [KB](../README.md).

## Scope & conventions

This is an **app catalogue** for the owner's own device — what each installed `.fap` (or built-in app) *is*, not a re-teaching of the radios (that's in the linked capability docs). All three families use **internal Flipper hardware only** — except the two **UHF RFID** apps, which need an external **860–960 MHz module** (YRM100/M6E-Nano-class) and are flagged accordingly. Authorized-use rules from [legal-and-safety.md](../legal-and-safety.md) apply throughout: clone/emulate/fuzz **only credentials and readers you own or are authorized to test**.

Conventions in the tables below:
- **Chip/HW** = the writable blank or extra hardware the app needs (e.g. `T5577`, `RW1990`, `UHF module`).
- `(verify)` / `(unverified)` = volatile or not-confirmed-from-primary-source this pass.
- "Catalog" = listed on [lab.flipper.net/apps](https://lab.flipper.net/apps); "bundled" = ships inside Momentum/Unleashed app sets; "community" = GitHub-only.

---

# Family 1 — LF RFID (125 kHz)

> Deep theory (EM4100 frame, HID Wiegand, T5577 config block, why LF is clone-on-read): [cards/lf-125khz.md](../cards/lf-125khz.md). Feature view: [capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md).

## `lfrfid` — 125 kHz RFID (core, built-in)

**What it does.** The stock low-frequency RFID app: **read, save, emulate, write** 125 kHz cards/fobs (building-access tags, etc.). LF credentials are static unencrypted serial numbers, so most are clone-on-read onto a writable blank.

**Menu structure (as actually laid out — a common point of confusion).** Top level is **Read · Saved · Add Manually · Extra Actions**:
- **Read** — auto-cycles modulations/codings, switching ~every 3 s; an unknown card can take up to ~10 s to settle. Try this first.
- **Saved** — open a stored card → **Emulate**, **Write** (to a T5577 blank), **Edit**, rename/delete.
- **Add Manually** — create a virtual card without scanning: pick protocol, type the data in hex, save.
- **Extra Actions → Read ASK** (forces Amplitude-Shift-Keying demod: EM4100, HID, AWID, IoProx) / **Read PSK** (forces Phase-Shift-Keying demod: Indala and other PSK formats). This is the manual codec escape-hatch when auto **Read** fails. (So "Read ASK/PSK" are *under Extra Actions*, and "Write" is a *Saved-card action* — not top-level items.)

**Protocols.** ~24 LF protocols compiled in the firmware registry: EM4100 (+ EM4100/32, EM4100/16 variants), Electra, HID H10301, Generic HID Prox/Extended, IDTeck, Indala-26, IoProx (Kantech XSF), AWID, FDX-A, FDX-B (ISO animal chips), Pyramid (Farpointe), Viking, Jablotron, Paradox, PAC/Stanley, Keri, Gallagher/GProx, Nexwatch, Securakey, Guardall G-Prox II, Noralsy. (Docs say "26 protocols" in Add-Manually vs 24 in source — a counting/variant difference, not a real gap `(verify)`.)

**T5577 clone workflow.** (1) **Read** the original (use Extra Actions if it won't auto-detect), save it. (2) **Saved → card → Write**, hold the Flipper's back antenna to the **T5577 blank** until "Successfully written." See [cards/cloning-matrix.md](../cards/cloning-matrix.md) for the blanks list.

| | |
|---|---|
| **Chip/HW** | Internal 125 kHz antenna; writable target = **T5577** (EM4305 is writable too but isn't the named target). Plain EM4100 tags are **read-only** → clone onto T5577. |
| **Use-cases** | UC-15 (LF fob read/emulate/clone). Back up your own gym/office/apartment fob; emulate it from the Flipper; cut a spare onto a T5577. |
| **Gotchas** | Emulation works because there's no crypto to forge; FSK formats (ioProx/Paradox) may write narrower than they read `(verify per-firmware)`. FDX-B animal chips are 134.2 kHz → best-effort, off-band (see [cards/lf-125khz.md](../cards/lf-125khz.md) §6). |
| **Source** | https://docs.flipper.net/zero/rfid (sub-pages /read, /write-data, /add-manually) |

## `fuzzer_rfid` — RFID Fuzzer

**What it does.** A 125 kHz **reader-fuzzer**: rapidly *emulates* a sequence of card UIDs at an access reader to test which it will accept — common/default UIDs, a brute-forced customer-ID byte, or IDs iterated from a loaded card/dictionary. Emulate-only — **it does not write physical cards**.

**Modes (exact UI labels).** **Default Values** (built-in dictionary of common/default UIDs) · **BF Customer ID** (iterates a selected byte, rest held at zero — the "increment" behaviour) · **Load File** (load a saved `.rfid` as the base UID, edit it, iterate a byte) · **Load UIDs from file** (play a custom SD dictionary). There is *no* separate "+1/−1", "BadUSB" or "Dictionary" mode in the catalog build.

**Settings.** **Time Delay (TD)** = idle gap between UID transmissions; **Emulation Time (EmT)** = how long each UID is sent. Exact numeric defaults/ranges `(unverified)`.

| | |
|---|---|
| **Chip/HW** | Internal 125 kHz antenna; **no external hardware**, no blanks (emulate-only). |
| **Use-cases** | Test a reader *you own* for default-UID acceptance; map the accepted customer-ID range; confirm a captured card and probe adjacent IDs; DoS stress-test. Pair the generated dictionaries with `em4100_generator` (below). |
| **Protocols** | Catalog v1.4: EM4100, HIDProx, PAC/Stanley, H10301, IoProxXSF, Paradox, Indala26, Viking, Pyramid, Keri, Jablotron (11). The maintained **DarkFlippers/Multi_Fuzzer** fork adds Electra, IDTeck, Gallagher, Nexwatch (15). |
| **Source** | https://lab.flipper.net/apps/fuzzer_rfid · fork: https://github.com/DarkFlippers/Multi_Fuzzer |

## `t5577_writer` — T5577 Raw Writer

**What it does.** Writes **raw block data** directly to T5577 blanks. You configure the chip's blocks by hand (or load a saved `.t5577`) and burn them — a low-level alternative to the stock writer when block order / modulation / clock matter.

**Options (Config).** Modulation (e.g. ASK/Manchester), RF Clock (e.g. 64), number of user blocks (~7–8), per-block hex editing **including block 0 (the config block)**, load `.t5577` (config auto-parsed from block 0), save back to `.t5577`.

| | |
|---|---|
| **Chip/HW** | Internal 125 kHz antenna; target = **T5577** only. |
| **Use-cases** | Clone with exact raw-block control; **fix a card the stock writer mis-formats** (wrong modulation/clock/block-order); recreate from a saved config; experiment with block layouts. |
| **Gotchas** | Only **block 0 hex** is processed — the human-readable strings in a `.t5577` file are derived and editing them does nothing. Per README: **no** page-1 writes, **no** password-protected writes, **no** Proxmark3 `.json` parsing, **no** emulation. |
| **Source** | https://github.com/zinongli/T5577_Raw_Writer · https://lab.flipper.net/apps/t5577_writer |

## `t5577_multiwriter` — T5577 Multi Writer

**What it does.** Writes **several different keys onto ONE T5577 card** (author Leptopt1los) — i.e. **many records → one card**, *not* batch-writing one record to many cards. It multiplexes ~2–3 distinct **EM41xx/EM4100** IDs onto a single chip so one card can present multiple EM4100 IDs. Proof-of-concept.

| | |
|---|---|
| **Chip/HW** | Internal 125 kHz antenna; target = **T5577**; **EM41xx/EM4100 only** (the trick is format-specific). |
| **Use-cases** | Consolidate several 125 kHz EM4100 fobs you own (gym + office + apartment) onto one card; research demo of T5577 block multiplexing. |
| **Gotchas** | Early PoC — sparse docs, no tagged releases; read-back reliability depends on the target reader `(verify)`. Reportedly bundled into RogueMaster `(verify)`. Distinct from `t5577_writer` (single-record raw writer). |
| **Source** | https://github.com/Leptopt1los/t5577_multiwriter · https://lab.flipper.net/apps/t5577_multiwriter |

## `em4100_generator` — EM4100 Key generator

**What it does.** Generates EM4100 key/ID values — "universal keys" derived from an EM4100 key. On the owner's device the `.fap` is named `em4100_generator`; this is the firmware-bundled name for **Milk-Cool's "EM4100 Key generator"**, which appears in the official catalog under the slug **`key_generator`** (the slug/`.fap`-name mismatch is just packaging) `(verify the exact build)`.

**Note — two similarly-named tools, only one is on-device:**
- **Milk-Cool/fz-em4100-generator** — the on-device `.fap` (catalog `key_generator`). Produces EM4100 IDs; **no documented direct T5577 write** (random-vs-sequential mode `(unverified)`). This is the one installed.
- **evillero/F0_EM4100_generator** — a **desktop Python script** (not a `.fap`) that emits *random* IDs for EM4100/HIDProx/PAC-Stanley/H10301 into a `dictionary.txt` for the RFID Fuzzer.

| | |
|---|---|
| **Chip/HW** | Internal 125 kHz antenna; generator only — **does not itself write to T5577** (write the chosen ID via `lfrfid` or `t5577_writer`). |
| **Use-cases** | Generate candidate / "universal" EM4100 IDs; build an ID dictionary to feed `fuzzer_rfid`; produce a known ID to then write onto a T5577. |
| **Gotchas** | Generates IDs, doesn't clone — the write step is a separate app. Since EM4100 tags are read-only, "cloning" always means writing the EM4100 data onto a writable **T5577**. |
| **Source** | https://lab.flipper.net/apps/key_generator · https://github.com/Milk-Cool/fz-em4100-generator |

## `uhf_rfid` — [YRM100] UHF RFID

**What it does.** Reads, writes, and saves **a single UHF (860–960 MHz) RFID tag** at a time via an external **YRM100** module — EPC **Gen2 / ISO 18000-6C**. The leaner, original of the two UHF apps (author frux-c). This is a *different band entirely* from the 125 kHz LF apps above — UHF RAIN RFID (warehouse/retail/asset tags), not access fobs.

**Options/modes.** Read single tag (**EPC/TID/User**); read-multiple list view; write single tag (**EPC + User**; TID write unsupported when locked); view saved tags; settings for **baud rate, RF power, region**; Set/Reset Access Password ("in progress"); Kill Tag ("planned").

| | |
|---|---|
| **Chip/HW** | ⚠️ **Requires the external YRM100 / M100 UHF module** (M6E-Nano-class, 860–960 MHz), via **GPIO UART**. **Power:** the YRM100 wants **VCC 3.7–5 V with 3.3 V TTL logic** and draws real TX current — feed VCC from the Flipper **5 V pin** (or external/USB), not bare 3.3 V GPIO `(partially unverified — neither README mandates external power, but the datasheet voltage is documented)`. |
| **Use-cases** | Read a single UHF asset/inventory EPC tag; inspect TID (chip serial) + User memory; write/encode an EPC; basic access-password setting. |
| **Gotchas** | Not a 125 kHz app — needs the UHF module to do anything. Upstream of `simultaneous_rfid_reader` (below). |
| **Source** | https://github.com/frux-c/uhf_rfid · https://lab.flipper.net/apps/uhf_rfid |

## `simultaneous_rfid_reader` — Simultaneous UHF RFID Reader

**What it does.** The **extended** UHF app (author Riley Haffner), derived from frux-c's `uhf_rfid`. Headline feature is **bulk/"simultaneous" inventory** — reading and listing many EPC Gen2 tags in one pass (up to ~150 tags/sec on M6E/M7E hardware), then cycling the results. Read/write/view/save across all four banks.

**Options/modes.** Read single + read multiple (list, cycle); write **EPC / TID / User / Reserved** (TID blocked if locked); save/rename/delete/view; settings for **RF power, UHF module selection, baud rate, region, access password, save-on-write**; plus tag **lock/kill**. The EPC/TID/User/Reserved bank model is the EPC **Gen2 / ISO 18000-6C** air interface.

| | |
|---|---|
| **Chip/HW** | ⚠️ Needs an external **860–960 MHz module**, one of: **YRM100 (M100)** — connects **directly** to Flipper GPIO UART; or **ThingMagic M6E-Nano / M7E Hecto** — these require a **Raspberry Pi Zero running a ThingMagic Mercury-API bridge** (wiring in README). Same VCC/TTL power note as `uhf_rfid`. |
| **Use-cases** | Bulk UHF inventory (warehouse/retail stock-take, asset tracking); cataloguing/writing EPC Gen2 tags; RAIN RFID lab work. |
| **Gotchas** | YRM100 path = simple; M6E/M7E path = extra Raspberry Pi bridge. Relationship: this **forked/extended** frux-c's app — most YRM100 read/write code came from `uhf_rfid`, with M6E/M7E + bulk-read + Reserved-bank + save/rename added here. Not a "Momentum version" — an independent catalog app. |
| **Source** | https://github.com/haffnerriley/Simultaneous-UHF-RFID-FlipperZero · https://lab.flipper.net/apps/simultaneous_rfid_reader |

---

# Family 2 — iButton / 1-Wire

> Theory (1-Wire electrical basics, DS1990A 64-bit ROM, Cyfral/Metakom, writable blanks, contact-pad zones): [capabilities/ibutton.md](../capabilities/ibutton.md).

## `ibutton` — iButton (core, built-in)

**What it does.** The stock 1-Wire app: **read, save, emulate, write** contact "touch" keys. Auto-detects the key type on read across three families — **Dallas** (DS199x), **Cyfral**, **Metakom** (the latter two common on ex-USSR intercoms).

**Workflow & key types.** **Read** (touch key to pad → auto-detect type, read UID) → then **Emulate**, **Save** (`.ibtn` on SD), or **Write** to a blank. **Add Manually** lets you pick a protocol and type a UID in hex; documented manual types include Dallas **DS1990(A), DS1992, DS1996, DS1971**, plus **Cyfral** and **Metakom**. A Dallas key is an 8-byte / 64-bit ROM (1 family byte + 6 ID bytes + 1 CRC). Cyfral/Metakom are shorter codes (exact bit-lengths `(unverified)` this pass).

**Contact-pad orientation (the #1 failure point — from official docs).** The module is three spring-loaded pogo pins:
- **Read / Write** → **left data pin + middle ground pin**.
- **Emulate** → **right data pin + middle ground pin**.

| | |
|---|---|
| **Chip/HW** | Internal 1-Wire (GPIO pin 17 + GND). Rewritable blanks: **RW1990, TM1990, TM08V2** (UID only) and **RW2004** (DS1990/DS1992-compatible, still UID-only). Community lists also cite **TM2004 / TM01C** `(verify)`. |
| **Use-cases** | UC-24 (iButton read/emulate/write). Back up / duplicate your own intercom or gate key onto an RW1990. |
| **Gotchas** | **Flipper writes the UID only — it cannot rewrite a blank's data memory yet.** Some high-voltage blanks (RW2000-class, ~8 V) can't be programmed at all. `.ibtn` is a FlipperFormat text file (`Filetype: Flipper iButton key`, version, protocol/key-type, hex `Data:` — exact field names `(unverified)`). |
| **Source** | https://docs.flipper.net/zero/ibutton (write: https://docs.flipper.net/zero/ibutton/write) |

## `fuzzer_ibtn` — iButton Fuzzer

**What it does.** The iButton sibling of the RFID Fuzzer — tests/attacks 1-Wire **readers** by rapidly emulating a sequence of UIDs. It is **dictionary/list-based** (cycles built-in lists of default & frequently-used UIDs per protocol, plus optional user dictionaries / imported key files), not pure incremental brute-force. Supports **DS1990 (Dallas), Metakom, Cyfral**.

**Options.** Attack source = **Default Values** (built-in dictionaries) / custom UID lists from SD / a FlipperFormat key file with byte-level editing. **Time Delay (TD)** = gap between UID submissions (the RFID-Fuzzer sibling lets you hold a button to step ±10; default ms `(unverified)`). **Emulation Time (EmT)** = per-UID transmit time. Mid-run you can switch UID, emulate the current one, or save it.

| | |
|---|---|
| **Chip/HW** | Internal 1-Wire; **no external hardware**, emulate-only (no blanks). |
| **Use-cases** | Audit your own intercom/access reader for acceptance of default or common keys; DoS-type weakness check via invalid/repeated UIDs. |
| **Gotchas** | Emulate-only — doesn't write keys. Original repo **xMasterX/ibutton-fuzzer** (built for Unleashed, also works on stock; standalone v0.1.1, Dec 2022); now **bundled** in Unleashed/Xtreme/Momentum app sets (catalog shows v1.4, author placeholder "Check repo"). From-scratch successor: **DarkFlippers/Multi_Fuzzer**. |
| **Source** | https://github.com/xMasterX/ibutton-fuzzer · catalog: https://lab.flipper.net/apps/category/ibutton |

## `ibutton_converter` — iButton Converter

**What it does.** Converts **Metakom or Cyfral key dumps into Dallas format** so the result can be written to a common Dallas-compatible blank (RW1990 etc.) and emulated where the original protocol isn't directly writable. One-directional: **Cyfral/Metakom → Dallas**.

**Conversion modes (verbatim).** **Metakom:** Direct, Reversed. **Cyfral:** standard **C1, C2, C3, C4**; extended **C5, C6, C7**. (Different intercom brands use different Cyfral→Dallas recoding tables, hence the modes.)

**Usage.** Read the source key first with the stock `ibutton` app → open Converter → select the saved Metakom/Cyfral file → pick a mode → enter an output filename → save as a Dallas `.ibtn`.

| | |
|---|---|
| **Chip/HW** | None for the conversion itself; the resulting Dallas key writes to the usual **RW1990/TM1990** blanks (UID-only). |
| **Use-cases** | Make a Cyfral/Metakom intercom key (which the Flipper can't write to a blank directly) cloneable by recoding it to Dallas first. |
| **Gotchas** | Choosing the **wrong Cyfral mode (C1–C7)** yields a Dallas code the target reader rejects — the right mode depends on the specific intercom model. Output is UID-level Dallas (all stock-app blank caveats apply). |
| **Source** | https://github.com/Leptopt1los/ibutton_converter |

---

# Family 3 — Infrared

> Theory (IR hardware, 38 kHz demod RX vs 3 TX LEDs, 13 parsed protocols vs RAW, `.ir` format, Universal Remote, IRDB, external blasters): [capabilities/infrared.md](../capabilities/infrared.md).

## `infrared` — Infrared (core, built-in)

**What it does.** The stock IR app: capture, store, and replay consumer IR (TVs, ACs, soundbars, projectors). Three modes — learn one button, replay saved `.ir` remotes, and **Universal Remote** brute-force dictionaries.

**Modes.** **Learn New Remote** (point a remote at the front RX, capture, name, save into a `.ir`) · **Saved remotes** (`.ir` files under `/ext/infrared/`; scroll the button list and tap to TX) · **Universal Remote** (ships four bundled dictionaries — **TV, Audio, Projector, Air Conditioner** — that iterate hundreds of known codes until the device responds; the AC DB covers power/mode/temperature). CFW expands these. **13 parsed protocols** (`NEC`, `NECext`, `NEC42`, `NEC42ext`, `Samsung32`, `RC5`, `RC5X`, `RC6`, `SIRC`, `SIRC15`, `SIRC20`, `Kaseikyo`, `RCA`); unknown signals fall back to **RAW** mark/space timings.

| | |
|---|---|
| **Chip/HW** | Internal IR: **3 TX LEDs** + a **38 kHz demodulating RX**. Optional external **IR blaster** for range (powered from GPIO **5 V**, same IR signal, no firmware change). |
| **Use-cases** | UC-01 (universal IR remote), UC-02 (learn & save a remote), UC-03 (TV-B-Gone-style power-off). Consolidate household remotes; rebuild a lost one; AV-room automation. |
| **Gotchas** | RX is *demodulating* → it can't see the carrier frequency (assumes 38 kHz on save); 56 kHz B&O / some 36–40 kHz remotes capture poorly. AC remotes encode full state per burst, so a single learned button may misbehave → IRDB AC files exist for this reason. |
| **Source** | https://docs.flipper.net/zero/infrared |

## `flipper_xremote` — XRemote (kala13x)

> ⚠️ **Name caveat:** the catalog **slug `xremote` is NOT this app** — it's leedave's *Cross Remote* (next entry). kala13x's **XRemote** has the slug **`flipper_xremote`**. The owner has both `.fap`s; keep them straight.

**What it does.** An advanced IR remote that maps the Flipper's **physical buttons** straight to IR commands, so it behaves like a real handheld remote (press the D-pad) instead of a scroll-and-fire menu. Adds a guided learn mode and editable custom layouts on top of standard `.ir` files.

**Options/modes.** Interface pages — General / Control / Navigation / Player / Custom / All buttons. **Guided "Learn new remote"** (tells you which button it's recording, no manual naming). **Custom Layout editor** (assign an IR command to each physical button's *press* or *hold*). **Alternative button names** fallback (e.g. "Power" also matches off/on/standby), editable at `apps_data/flipper_xremote/alt_names.txt`. Vertical/horizontal view; ~25 predefined button types.

| | |
|---|---|
| **Chip/HW** | Internal IR (3 TX LEDs, 38 kHz RX) + standard `.ir` files. **No documented external-IR/GPIO support** `(unverified)`. |
| **Use-cases** | Use the Flipper as a genuine tactile TV/AV remote; quick guided cloning; reuse `.ir` dumps whose labels don't match via alt-names. |
| **Gotchas** | Don't confuse with Cross Remote (`xremote`). Active; ~v1.4.1 / ~240★ `(verify)`. |
| **Source** | https://github.com/kala13x/flipper-xremote · https://lab.flipper.net/apps/flipper_xremote |

## `xremote` — Cross Remote (leedave)

**What it does.** Despite the `xremote` slug, this is **Cross Remote**: it merges **IR *and* Sub-GHz** commands into a single executable **chain/playlist** — one press fires a whole sequence (e.g. TV + Blu-ray + receiver + AC). An automation/macro tool, not a one-signal remote.

**Options/modes.** Build chains mixing IR + Sub-GHz; insert pauses; loop transmissions; LED effects; **"External IR & 5V on GPIO"** toggle; saves chains as `.xr` files.

| | |
|---|---|
| **Chip/HW** | Internal IR + internal Sub-GHz (CC1101); **explicitly supports an external IR board via 5 V on GPIO** (unlike XRemote). |
| **Use-cases** | "Movie night" multi-device macro; home-automation sequences combining a Sub-GHz gate/switch with IR AV gear. |
| **Gotchas** | Transmits Sub-GHz too → regional Sub-GHz TX caveats apply ([topics/subghz-region-lock.md](../topics/subghz-region-lock.md)). ~v2.7 `(verify)`. |
| **Source** | https://github.com/leedave/flipper-zero-cross-remote · https://lab.flipper.net/apps/xremote |

## `ir_remote` — Alternative Infrared Remote (Hong5489)

**What it does.** Maps the Flipper's physical buttons (Up/Down/Left/Right/OK/Back + a hold action each) to named signals pulled from existing `.ir` files, via a small `.txt` config — so you drive a device from the D-pad instead of scrolling. Its trick vs the others: it can **fan one button press out to up to 11 `.ir` files at once** (e.g. power on TV + soundbar + set-top box together).

**Config (`.txt`, `KEY: value`).** `REMOTE:` → path to the `.ir`; `UP/DOWN/LEFT/RIGHT/OK/BACK:` → signal name (must match a name inside the `.ir`) on short press; `UPHOLD/...OKHOLD:` → signal on hold; `REPEATSIGNAL: false` (optional); `EXTERNAL: true|false` (optional — selects external IR + 5 V on GPIO; prompts at startup if omitted; auto-off on exit).

| | |
|---|---|
| **Chip/HW** | Internal IR; **supports external IR + 5 V on GPIO** via the `EXTERNAL:` flag. Consumes existing `.ir` only — **doesn't learn/capture**. |
| **Use-cases** | A clean D-pad remote for one device; or multi-device "all-on" via the multi-file fan-out. |
| **Gotchas** | Signal-name matching is **exact**. With >1 remote configured only the first remote's button names show and repeat-on-hold is disabled (max 11). RAW-signal support `(unverified)`. **Community/GitHub + Unleashed-bundled — not in the official catalog** `(verify)`. README tested on `unlshd-072` (older). |
| **Source** | https://github.com/Hong5489/ir_remote |

## `ir_scope` — IR oscilloscope / analyzer (@kallanreed)

**What it does.** A live IR **oscilloscope**: continuously receives raw IR and draws the captured pulse train as a logical waveform (high = mark/IR-on, baseline = space/off) on the 128×64 screen. A real-time visualizer/diagnostic for reverse-engineering an unknown remote's timing — **not** a decoder or saver.

**Controls (from source).** **OK** = toggle **Autoscale** (fit whole capture) · **Up/Down** = manual horizontal zoom (`us_per_sample` ±25, clamped **25–1000 µs/sample**, turns autoscale off) · **Back** = exit. No save/replay.

| | |
|---|---|
| **Chip/HW** | Internal **front 38 kHz demod RX** (uses `infrared_worker` with protocol decoding disabled). **No external hardware.** |
| **Use-cases** | Eyeball an unknown remote's timing structure; compare bursts; spot headers/repeats before deciding parsed-vs-RAW. |
| **Gotchas** | Shows the **demodulated envelope, not the 38 kHz carrier** → can't reveal carrier frequency. View-only (can't save/replay). Says "Infrared is busy" if the IR HW is in use elsewhere. Ships inside plugin packs (no standalone repo). |
| **Source** | https://lab.flipper.net/apps/ir_scope · https://github.com/xMasterX/all-the-plugins/tree/dev/base_pack/ir_scope |

## `ir_intervalometer` — Intervalometer (@Nitepone)

**What it does.** Turns the Flipper into a camera **intervalometer / remote shutter**: fires a camera's IR shutter code on a schedule for time-lapse and burst photography, with a live countdown UI.

**Camera brands (from source — README is stale/Sony-only).** Selectable via **Trigger Type**: **Sony** (SIRC), **Canon** (raw 38 kHz), **Nikon** (raw, the ML-L3 sequence), **Pentax** (raw). **Olympus not supported** (planned `(unverified)`).

**Timing settings (6).** Initial Delay · Interval Delay · Shot Count (**0 = infinite**) · Burst Count (triggers per shot) · Burst Delay · Trigger Type (brand). Main scene shows live countdown + elapsed + shot counter with Config / **Snap** (one shot now) / Start-Stop.

| | |
|---|---|
| **Chip/HW** | Internal **IR TX LEDs**; needs direct line-of-sight to the camera's IR sensor. **No external hardware.** |
| **Use-cases** | IR-triggered time-lapse / interval / burst shooting on a supported body. |
| **Gotchas** | The **camera must support an IR remote shutter** and often needs a "remote"/IR drive mode enabled first (older Canon EOS w/ RC-6, Nikon w/ ML-L3, many Sony Alpha/NEX, Pentax IR). Per-body compatibility `(unverified)`. Trust the source over the README. |
| **Source** | https://github.com/Nitepone/flipper-intervalometer · https://lab.flipper.net/apps/ir_intervalometer |

---

## Cross-app notes

- **Two IR apps drive opposite halves of the internal IR hardware:** `ir_scope` uses the **front 38 kHz demod RX** (decoding off, raw-timing mode); `ir_intervalometer` uses the **3 TX LEDs**. Neither needs external hardware.
- **Which apps support an external IR blaster (5 V on GPIO):** **Cross Remote** (`xremote`) and **`ir_remote`** do explicitly; **XRemote** (`flipper_xremote`) does not (`(unverified)`); the stock `infrared` app routes to a blaster with no firmware change.
- **The two UHF apps are the only non-internal-hardware apps here** — they need an 860–960 MHz module and are a *different band* from everything else in the LF section. `uhf_rfid` (frux-c) is upstream/single-tag; `simultaneous_rfid_reader` (Haffner) is the extended/bulk fork.
- **Fuzzer pairing:** `em4100_generator` → builds an ID dictionary → `fuzzer_rfid` plays it at a reader. The iButton equivalent (`fuzzer_ibtn`) uses built-in dictionaries.

---

## Open questions / to research

- Confirm the **owner's actual installed slugs/versions** over USB/BLE (e.g. is `em4100_generator.fap` literally Milk-Cool's `key_generator`? is `ir_remote` present given it's not in the official catalog?). The MCP read tools could enumerate `/ext/apps/**` to settle the `.fap` names.
- `fuzzer_rfid` / `fuzzer_ibtn` **TD/EmT default values and ranges** (ms) — not in primary sources `(unverified)`.
- `lfrfid` "26 vs 24 protocols" discrepancy (docs vs firmware registry) — which variants are the extra two.
- Whether `lfrfid` / the writers can program **EM4305** directly (not just T5577) on current Momentum.
- `t5577_multiwriter` real-world **read-back reliability** and max records per card; whether it's truly EM4100-only.
- UHF apps: confirm the **power path** (does the YRM100 run off the Flipper 5 V pin alone, or need external power?) and whether either app is ever firmware-bundled vs catalog-only.
- `flipper_xremote` external-IR support; `ir_remote` RAW-signal support; `ir_intervalometer` per-camera-body compatibility + Olympus status.
- `.ibtn` exact field layout (read from firmware `applications/main/ibutton`).

## Sources

- LF RFID core: https://docs.flipper.net/zero/rfid · firmware protocol registry: https://github.com/flipperdevices/flipperzero-firmware/tree/dev/lib/lfrfid/protocols
- RFID Fuzzer: https://lab.flipper.net/apps/fuzzer_rfid · fork https://github.com/DarkFlippers/Multi_Fuzzer
- T5577 Raw Writer: https://github.com/zinongli/T5577_Raw_Writer · Multi Writer: https://github.com/Leptopt1los/t5577_multiwriter
- EM4100 generator: https://lab.flipper.net/apps/key_generator · https://github.com/Milk-Cool/fz-em4100-generator · desktop variant https://github.com/evillero/F0_EM4100_generator
- UHF RFID: https://github.com/frux-c/uhf_rfid · https://github.com/haffnerriley/Simultaneous-UHF-RFID-FlipperZero
- iButton core: https://docs.flipper.net/zero/ibutton · write https://docs.flipper.net/zero/ibutton/write
- iButton Fuzzer: https://github.com/xMasterX/ibutton-fuzzer · iButton Converter: https://github.com/Leptopt1los/ibutton_converter
- Infrared core: https://docs.flipper.net/zero/infrared · `.ir` format https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/InfraredFileFormats.md
- XRemote (kala13x): https://github.com/kala13x/flipper-xremote · Cross Remote (leedave): https://github.com/leedave/flipper-zero-cross-remote
- ir_remote: https://github.com/Hong5489/ir_remote · ir_scope: https://github.com/xMasterX/all-the-plugins/tree/dev/base_pack/ir_scope · ir_intervalometer: https://github.com/Nitepone/flipper-intervalometer
