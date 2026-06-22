---
title: Installed Apps — BadUSB/HID, Automotive & Misc Security
domain: resources
type: reference
status: detailed
summary: Runbook for the BadUSB/HID, CAN/automotive, physical-access, crypto and misc security FAPs on my Momentum rig.
hardware: [flipper-internal, gpio, devboard]
use_cases: [UC-25, UC-26, UC-27, UC-28, UC-47, UC-48, UC-50, UC-53]
related: [my-setup.md, my-use-cases.md, capabilities/badusb.md, capabilities/nfc-rfid.md, topics/tinkering.md, topics/security-pentest.md, resources/cool-projects.md, resources/notable-apps-and-data.md, legal-and-safety.md]
tags: [badusb, hid, can-bus, obd, magspoof, sentry-safe, totp, encryption, barcode]
last_verified: 2026-06-22
---

# Installed Apps — BadUSB/HID, Automotive & Misc Security

> **TL;DR —** Per-app runbook for the BadUSB/HID, automotive (CAN/OBD-II), physical-access, and crypto/misc security FAPs installed on my Flipper (Momentum, maxed app set). For each: what it does, key options, use-cases, and what it *needs* — many require a **USB-attached host** (HID/BadUSB), a **CAN transceiver module** (automotive), or **coil/GPIO wiring** (MagSpoof, Sentry Safe). All for my own/authorized targets only.
> Companions: [my-setup](../my-setup.md) · [BadUSB deep-dive](../capabilities/badusb.md) · [NFC/RFID](../capabilities/nfc-rfid.md) · [tinkering/GPIO](../topics/tinkering.md) · [pentest framing](../topics/security-pentest.md) · [legal](../legal-and-safety.md). Part of the [KB](../README.md).

> **Authorized use only.** Most of these are dual-use. HID/BadUSB = unauthorized access if run against a machine you don't own/lack written permission for; CAN injection can disable a moving vehicle; safe/lock tools are for your own property. See [legal-and-safety](../legal-and-safety.md) and the per-app gotchas. This doc documents *what each app is and needs* — no working attack payloads.

## How to read the "needs" column

| Tag | Meaning |
|---|---|
| **host** | Needs a **USB-attached target** (PC/phone) — the app is useless without something on the other end of the cable/BLE. |
| **BLE** | Can also run wirelessly over Bluetooth LE (no cable). |
| **internal** | Runs on the bare Flipper — no extra hardware. |
| **module** | Needs an **external GPIO board** (CAN transceiver, MagSpoof coil, safe wiring). |

Everything here is in the **Momentum** app set / Flipper catalog unless flagged. Install/update via [Flipper Lab](https://lab.flipper.net/apps) or the Momentum app loader; mirror pages on [Awesome Flipper](https://awesome-flipper.com) render better than the JS catalog when you just want the README. `(verify)` = real but the exact version/behavior wasn't pinned on *this* build.

---

## BadUSB / HID / USB gadget

These all make the Flipper enumerate as some **USB (or BLE) device** to a host. Background, Ducky Script command set, `.kl` layout handling, and blue-team defenses live in **[capabilities/badusb.md](../capabilities/badusb.md)** — this section is just the installed-app inventory.

### `bad_kb` — Bad KB (BadUSB/BadBLE)
- **What:** The CFW evolution of stock **Bad USB**. Runs Ducky Script payloads as an HID keyboard **over USB *and* over Bluetooth LE** ("BadBLE"); the OFW app is USB-only. Renamed from "Bad USB" → "Bad KB" when BLE support landed (XFW v41 lineage). Authors: Willy-JL, ClaraCrazy + XFW/Momentum contributors.
- **Key options:** USB vs BT transport toggle; in **BT mode**, spoof the advertised **device name and BLE MAC**; full **keyboard-layout (`.kl`)** picker (match the *target's* layout, not yours); custom **USB VID/PID** + manufacturer/product strings (`ID` command); the extended Flipper Ducky dialect (ALT+Numpad/`ALTSTRING`, `SYSRQ`, mouse, `HOLD`/`RELEASE`, `STRINGLN`) — see the [command matrix](../capabilities/badusb.md#command-set-per-current-firmware-badusbscriptformatmd).
- **Use-cases:** UC-25 (attack payloads), UC-26 (automation/keep-awake), UC-27 (BadBT/BadKB BLE keystrokes), UC-28 (kbd/mouse remote). Payloads are plain `.txt` in `/ext/badusb/`.
- **Gotchas:** Needs a **host** to type into. A **locked screen** neuters most payloads. **BLE mode requires the target to accept pairing** — a real consent gate (and an alert worth refusing). Layout mismatch garbles `STRING`. Authorized targets only.
- **Source:** https://lab.flipper.net/apps/bad_kb · https://docs.flipper.net/zero/bad-usb · BadBT origin: https://github.com/AGO061/BadBT

### `hid_usb` — USB/BT HID Remote ("Remote" / controllers)
- **What:** The stock **HID controller** app — turns the Flipper into a **keyboard/mouse/media remote** for a connected PC or phone, over USB or Bluetooth. Interactive (you drive it with the D-pad), not scripted like Bad KB. Modes include Keynote/presentation clicker, mouse, mouse-jiggler, media/volume, and a numpad.
- **Key options:** mode select (Keynote, Mouse, Media, Keyboard, TikTok/Camera, etc.); USB vs BT; mouse-jiggler sub-mode.
- **Use-cases:** UC-28 (BLE clicker / kbd-mouse remote), overlaps UC-50 (mouse jiggler). Genuinely useful as a presentation remote or for nudging a screensaver.
- **Gotchas:** Needs a **host**; BT mode needs pairing. Benign by itself (it's a remote), but it *is* an HID input device — the same screen-lock caveats apply.
- **Source:** https://docs.flipper.net/zero/apps/controllers

### `mass_storage` — USB Mass Storage emulator
- **What:** Presents the Flipper as a **USB flash drive**. You create a disk image (**up to 64 MB**), format/mount it on the host, and read/write files over USB. Images live in `/ext/mass_storage/` on the SD, so you can keep several and switch.
- **Key options:** create image (size), select existing image, mount/eject. Official app by nminaylov/kevinwallace.
- **Use-cases:** carry files, present a known-good test image, autorun/USB-handling research on hosts you own. No dedicated UC-ID (utility — cf. UC-51 utilities).
- **Gotchas:** Needs a **host**. It's a **very slow** device (Flipper SD is on a ~600 KiB/s SPI bus — see [my-setup §3](../my-setup.md)). Not a security exploit on its own, but pairs with BadUSB-style "drop a file then run it" research — keep it to authorized machines.
- **Source:** https://lab.flipper.net/apps/mass_storage · https://awesome-flipper.com/application/lab.flipper.net/usb/mass_storage/

### `mouse_click_recorder` — Mouse click recorder/replayer
- **What:** Records a sequence of mouse clicks/movement and **replays** them as a USB/BT HID mouse — with replay, randomize, and click-spam modes. No host-side software needed (it's HID).
- **Key options:** record / replay / loop; randomize timing or position; click-spam (autofire) rate; USB vs BT.
- **Use-cases:** automate repetitive clicking, anti-idle, autofire — overlaps UC-50 (mouse jiggler) and UC-26 (HID automation).
- **Gotchas:** Needs a **host**. The app's own README warns: don't drive a system you don't own/lack permission for.
- **Source:** Flipper catalog (USB category) — https://lab.flipper.net/apps/category/usb · related autofire: https://github.com/pbek/usb_hid_autofire

### `xinput_controller` — XInput (Xbox 360) gamepad emulator
- **What:** Makes the Flipper enumerate as an **XInput game controller** over USB; connects automatically when opened. Drive buttons/axes from the Flipper. (Identified: `expected-ingot/flipper-xinput`.)
- **Use-cases:** test XInput handling on a PC, novelty gamepad. No KB UC-ID. Likely **won't work on an Xbox console** (MS auth) — PC/emulator only `(verify)`.
- **Gotchas:** Needs a **host** that speaks XInput. Trivial/novelty.
- **Source:** https://github.com/expected-ingot/flipper-xinput

### `usb_ccb` — USB Consumer Control
- **What:** Sends **USB HID Consumer-Control** button presses (play/pause, volume, brightness, launch-browser, sleep, etc.) as a USB device — a different HID report than keyboard. By piraija. Used to research how kiosks/devices handle consumer-control codes (kiosk-breakout research).
- **Use-cases:** media control, kiosk/lockdown HID research on your own gear. No KB UC-ID (HID-adjacent).
- **Gotchas:** Needs a **host**. Authorized-targets caveat applies (kiosk breakout = the same legal line as BadUSB).
- **Source:** https://awesome-flipper.com/application/lab.flipper.net/usb/usb_ccb/ · context: https://labs.reversec.com/tools/usb-consumer-control

---

## Automotive — CAN bus / OBD-II

> **Needs a CAN transceiver module.** The Flipper has **no CAN hardware**. These apps drive an **MCP2515 (SPI CAN-controller + TJA1050-class transceiver) GPIO add-on** — the Electronic Cats "CAN Bus Add-On" or any MCP2515 board wired to the Flipper's SPI pins. Without that module, neither app does anything. ⚠️ Writing/injecting onto a live vehicle bus can disable controls or brick modules — **bench/own-vehicle, engine-off, authorized only**.

### `can_commander` + `can_tools` — MCP2515 CAN Bus suite
- **What:** The two FAPs from **ElectronicCats/flipper-MCP2515-CANBUS** — a pocket CAN-bus Swiss-army knife. `can_tools`/`can_commander` cover **sniffing** the bus (hex or decoded output), **logging** frames to the SD, and **injection** (craft/replay frames, store recent frames to modify + re-send). Newer releases add **OBD-II PID** reads and a **UDS** layer (request **VIN**, **read/clear DTCs**, ECU reset) `(verify on this build — base README documents sniff/inject/log; OBD-II/UDS appear in v2.x releases/forks)`.
- **Key options:** bitrate select (125k/250k/500k…); sniff vs inject mode; hex/normal formatting; SD logging on/off; frame editor for re-injection; OBD-II PID picker / UDS functions `(verify)`.
- **Use-cases:** read live OBD-II PIDs on your own car, pull VIN/DTCs, reverse-engineer body-control frames, learn CAN. No KB UC-ID yet → **candidate new UC** (e.g. "CAN/OBD-II read", "CAN injection"). See also the **Tesla mods** that ride the same module ([hypery11/flipper-tesla-fsd](https://github.com/hypery11/flipper-tesla-fsd)) and the WIP [iomonad/flipper-canutils](https://github.com/iomonad/flipper-canutils).
- **Gotchas:** **MCP2515 module mandatory** (SPI on pins 1–8 region; CAN-H/CAN-L to the bus, e.g. white/black on the Electronic Cats board). Plugging into the **OBD-II port** = the powertrain/body bus — **injection is genuinely dangerous on a moving car**; sniff first, inject only bench/engine-off on a vehicle you own. Region/bitrate must match the target bus.
- **Source:** https://github.com/ElectronicCats/flipper-MCP2515-CANBUS · module: https://awesome-flipper.com/extra/module/can-bus/

---

## Physical / access security

### `magspoof` — MagSpoof (magnetic-stripe emulator)
- **What:** Port of **Samy Kamkar's MagSpoof** — pulses an **electromagnet coil** to wirelessly emulate a **magnetic-stripe swipe** (it does **not read** stripes, only emulates). Stores `.mag` files in `/apps_data/magspoof/`. Iconic hack; also noted in [cool-projects](cool-projects.md).
- **Key options:** select/emulate `.mag` track data (Track 1/2); GPIO pins for the coil driver default to **A7/A6/A4** (configurable); experimental **internal-coil TX** behind a debug flag; an untested UART-reader dev mode.
- **Use-cases:** emulate **your own** loyalty/hotel/gift magstripe cards, demonstrate magstripe insecurity. No KB UC-ID (physical-card spoofing) → **candidate new UC**.
- **Gotchas:** **Needs a coil + H-bridge + capacitor on GPIO** (DIY, or a Rabbit-Labs/Electronic Cats board) — the bare Flipper can't do it well; **internal TX rarely produces a strong enough field** for real readers. Positioning is finicky. Your-own-cards only; emulating someone else's card data is fraud.
- **Source:** https://github.com/zacharyweiss/magspoof_flipper

### `gpio_sentry_safe` — [GPIO] Sentry Safe opener
- **What:** Exploits the keypad-comms weakness in **SentrySafe / Master Lock electronic safes** to **open them with no PIN**, by driving the keypad's serial line over a GPIO wire (H4ckd4ddy plugin).
- **Key options:** send default or a chosen **5-digit** code (a fork adds arbitrary-code set); press OK → safe beeps and unlocks.
- **Use-cases:** open **your own** safe when you've lost the code; demonstrate the e-lock flaw. Maps to **UC-47** (Sentry Safe / e-safe opener).
- **Gotchas:** **Requires wiring into the safe's keypad**: Flipper **GND → safe black (GND)** wire and **GPIO C1 (pin 16) → safe green (data)** wire (open the keypad/battery housing to reach them). Only models with the vulnerable solenoid/keypad comms; your own safe only.
- **Source:** https://github.com/H4ckd4ddy/flipperzero-sentry-safe-plugin · https://lab.flipper.net/apps/gpio_sentry_safe

### `combo_cracker` — Combo Cracker (combination-lock aid)
- **What:** On-device implementation of **Samy Kamkar's Master Lock dial-padlock** technique. You feed it the **resistance/sticking positions** you feel while turning the dial; it computes the math and outputs a **short candidate list** of combinations to try (it doesn't physically open anything).
- **Key options:** enter observed resistance position(s) / first-digit hints → get the reduced combination set.
- **Use-cases:** recover the combo of **your own** Master Lock dial padlock; teaching the attack. No KB UC-ID → minor (physical-lock aid).
- **Gotchas:** **Internal** (no hardware) but **manual** — you still measure the lock by hand and try the candidates. Works on the specific vulnerable Master Lock dial design, not arbitrary locks. Your own lock only.
- **Source:** https://github.com/CharlesTheGreat77/ComboCracker-FZ · https://lab.flipper.net/apps/combo_cracker

### `key_copier` — Key Copier (physical-key bitting)
- **What:** Turns the Flipper screen into a **key-bitting gauge** (zinongli/KeyCopier). Lay a physical key flat on the display, drag each on-screen cut depth to match the real cuts, and read off the **bitting code** — the numbers a locksmith/duplicator needs to cut a copy. Supports common keyways/depth specs.
- **Key options:** keyway/manufacturer depth profile; per-cut depth sliders; save bitting.
- **Use-cases:** decode/record the bitting of **keys you own** (spare-key planning, lock hobby). No KB UC-ID → minor (physical-key decode).
- **Gotchas:** **Internal** (no hardware); it only *measures/decodes* — cutting still needs a machine or a 3D-printed-blank workflow. Decoding keys you aren't authorized to duplicate is the legal line.
- **Source:** https://github.com/zinongli/KeyCopier

### `nfc_rfid_detector` — NFC & LF-RFID Field Detector
- **What:** Official app that uses the Flipper's antennas as a **passive RF field detector** — hold it near a reader/surface and it reports whether an **HF (13.56 MHz NFC/iCLASS/PicoPass)** and/or **LF (125 kHz RFID)** field is present, with signal strength. Read-only sensing; it doesn't read card data.
- **Use-cases:** **find hidden card readers / skimmers**, locate the antenna in a reader, confirm a reader's frequency before choosing a [cards](../cards/README.md) workflow. Defensive — cf. UC-41 (skimmer detection) family; closest existing doc is [capabilities/nfc-rfid](../capabilities/nfc-rfid.md).
- **Gotchas:** **Internal** (no hardware). Detects an *active field*; it won't find a powered-off/passive tag. Purely defensive/diagnostic — no legal concern.
- **Source:** https://lab.flipper.net/apps/nfc_rfid_detector · context: https://github.com/djsime1/awesome-flipperzero/blob/main/FAQ.md

---

## Crypto / secrets

### `totp` — Authenticator (TOTP/HOTP 2FA)
- **What:** Software **TOTP (RFC 6238) / HOTP (RFC 4226)** authenticator on the Flipper (akopachov). Generates the same 6/8-digit 2FA codes as Google Authenticator/Authy. Token secrets are stored **encrypted** (PBKDF2-derived key tied to the device); a desktop **companion app** helps bulk-import.
- **Key options:** add token (Base32 secret, SHA1/256/512, 6/8 digits, 30/60 s); PIN/auto-lock; optional **BadUSB-style auto-type** of the current code into a host; notification/haptics.
- **Use-cases:** **UC-48** (TOTP 2FA authenticator) — one of the highest real-use scores in the KB. Pairs with U2F/FIDO (**UC-53**, [01-architecture](../01-architecture.md)).
- **Gotchas:** **Internal.** A Flipper holding your 2FA seeds is a **second factor you can lose/seize** — keep recovery codes elsewhere; the encryption is only as strong as the device PIN. Back up the `/ext/authenticator` config.
- **Source:** https://github.com/akopachov/flipper-zero_authenticator · https://lab.flipper.net/apps/totp

### `flipbip` — FlipBIP (BIP32/39/44 crypto wallet)
- **What:** Experimental **offline hierarchical-deterministic crypto wallet** (xtruan/FlipBIP). Generates/derives **BIP39 mnemonics**, **BIP32** keys and **BIP44** accounts (BTC/ETH and more), shown as addresses/QR. A "how much wallet fits on a Flipper" project.
- **Key options:** generate/import seed (12/24-word); **BIP39 passphrase** ("25th word"); coin/account selection; view xpub/address/QR; wipe.
- **Use-cases:** learn HD-wallet mechanics, an air-gapped scratch wallet. No KB UC-ID (crypto-wallet) → minor.
- **Gotchas:** **Internal**, but **treat as experimental, not a hardware wallet** — no secure element, the seed lives on a general-purpose MCU/SD. The README itself says use a BIP39 passphrase kept off-device. **Do not store real funds** beyond experiment amounts.
- **Source:** https://github.com/xtruan/FlipBIP · https://lab.flipper.net/apps/flipbip

### `flip_crypt` — FlipCrypt (text crypto/hashing toolbox)
- **What:** A **text** encrypt/decrypt/hash/encode toolbox (Tyl3rA/FlipCrypt) — **not** a file encryptor. ~14 ciphers (AES-128, RC4, Vigenère, Caesar, Playfair, Beaufort, Atbash, Baconian, Polybius, Porta, Rail-Fence, ROT13, Scytale, Affine), ~12 hashes (MD2/5, SHA-1/224/256/384/512, BLAKE-2s, SipHash, FNV-1a, Murmur3, XXHash64), and Base32/58/64 encoding.
- **Key options:** pick algorithm → enter text → output; export result to `.txt`, **emulate as NFC (NTAG215)**, or render a **QR code**.
- **Use-cases:** CTF/puzzle helper, quick hashes/encodings on the go, classic-cipher learning. No KB UC-ID → minor (utility).
- **Gotchas:** **Internal.** Author's own warning: *"don't use for anything important"* — accuracy not guaranteed, and the classical ciphers are toys, not security. **Text only** (despite the name — not whole-file encryption). QR gen may crash when qFlipper is attached.
- **Source:** https://github.com/Tyl3rA/FlipCrypt · https://lab.flipper.net/apps/flip_crypt

### `ck42x_passvault` — CK42X PassVault (password vault)
- **What:** A **PIN-gated, encrypted on-device password vault** (lordbuffcloud/flipper-ck42x-passvault) with a **memorable-password generator (RNG)** and **opt-in HID typing** — it can act as a USB keyboard to type a stored password into a host so you don't retype it.
- **Key options:** master-PIN unlock; add/view entries; generate memorable/random password; **HID auto-type** toggle (USB).
- **Use-cases:** a pocket password store + auto-typer. No KB UC-ID (secrets-manager) → minor; HID-typing feature overlaps the BadUSB/HID family.
- **Gotchas:** **Internal**, but **HID-type mode needs a host**. As with `totp`, the Flipper becomes a **secrets-bearing device** — losing it/PIN strength matters; verify the encryption claims yourself `(verify implementation)` before trusting it with real credentials. Smaller/less-audited than mainstream password managers.
- **Source:** https://github.com/lordbuffcloud/flipper-ck42x-passvault (per catalog listing) `(verify exact repo)`

---

## Misc

### `barcode_app` — Barcode Generator (1D)
- **What:** Generates and **displays 1D/linear barcodes on the Flipper screen** (Kingal1337/flipper-barcode-generator): **UPC-A, EAN-8, EAN-13, Code-39, Codabar, Code-128**. **No 2D/QR** (use FlipCrypt's QR or a dedicated QR app for that). Saves barcodes in `/apps_data/barcodes/`.
- **Key options:** pick type → filename → data → save/view; create/edit/delete from a menu.
- **Use-cases:** show a **loyalty/membership barcode** to a scanner, test a barcode reader, label lookups. No KB UC-ID → minor (utility, cf. UC-51); the KB already noted a "UPC-A Barcode Generator" in [notable-apps](notable-apps-and-data.md).
- **Gotchas:** **Internal** — but **screen-only**: success depends on the scanner reading the Flipper's small monochrome LCD (works for many laser/CCD scanners; some camera scanners struggle). **Code-128** is Set B/C only; **Codabar** needs manual start/stop chars.
- **Source:** https://github.com/Kingal1337/flipper-barcode-generator

---

## Quick reference

| App (`.fap`) | Group | Needs | KB UC |
|---|---|---|---|
| `bad_kb` | BadUSB/HID | host (USB **or** BLE) | UC-25/26/27/28 |
| `hid_usb` | BadUSB/HID | host (USB/BT) | UC-28 |
| `mass_storage` | USB gadget | host | — (UC-51) |
| `mouse_click_recorder` | BadUSB/HID | host | UC-50/26 |
| `xinput_controller` | USB gadget | host (XInput/PC) | — |
| `usb_ccb` | USB gadget | host | — |
| `can_commander` / `can_tools` | Automotive | **MCP2515 module** + bus | — (new UC?) |
| `magspoof` | Physical | **coil/H-bridge on GPIO** | — (new UC?) |
| `gpio_sentry_safe` | Physical | **wire into safe keypad** | UC-47 |
| `combo_cracker` | Physical | internal (manual) | — |
| `key_copier` | Physical | internal | — |
| `nfc_rfid_detector` | Physical (defensive) | internal | UC-41-adjacent |
| `totp` | Crypto | internal | UC-48 |
| `flipbip` | Crypto | internal | — |
| `flip_crypt` | Crypto | internal (text) | — |
| `ck42x_passvault` | Crypto | internal (+host for HID-type) | — |
| `barcode_app` | Misc | internal (screen) | — (UC-51) |

## Open questions / to research
- **CAN suite:** confirm on *this* build whether `can_commander`/`can_tools` expose the **OBD-II PID / UDS / VIN / DTC** layer or just sniff+inject; pin the exact firmware-fork/version `(verify)`. Decide whether to mint new UC-IDs ("CAN/OBD-II read", "CAN injection") and run `build-kb-index.py`.
- **MagSpoof:** sanity-check the default coil GPIO pins (A7/A6/A4) and whether a prebuilt board (Rabbit-Labs/Electronic Cats) is worth it vs DIY; test internal-TX field strength `(verify)`.
- **`ck42x_passvault`:** confirm the canonical repo/author and **audit its crypto** before trusting real credentials `(verify implementation + exact repo)`.
- **`gpio_sentry_safe`:** re-confirm the **C1 = GPIO pin 16** mapping and green/black keypad wiring against the current plugin README before wiring my own safe `(verify)`.
- Whether any of these clash on a maxed Momentum app set (API/version mismatches after the 2026-03 build — cf. [my-setup §2](../my-setup.md)).
- Mint candidate UC-IDs for MagSpoof (magstripe spoofing), CAN read/inject, and physical key/lock decode if I want them tracked in [use-cases-model](../use-cases-model.md).

## Sources
- BadUSB/HID: https://lab.flipper.net/apps/bad_kb · https://docs.flipper.net/zero/bad-usb · https://docs.flipper.net/zero/apps/controllers · https://lab.flipper.net/apps/mass_storage · https://lab.flipper.net/apps/category/usb · https://github.com/expected-ingot/flipper-xinput · https://awesome-flipper.com/application/lab.flipper.net/usb/usb_ccb/
- Automotive: https://github.com/ElectronicCats/flipper-MCP2515-CANBUS · https://awesome-flipper.com/extra/module/can-bus/ · https://github.com/iomonad/flipper-canutils · https://github.com/hypery11/flipper-tesla-fsd
- Physical: https://github.com/zacharyweiss/magspoof_flipper · https://github.com/H4ckd4ddy/flipperzero-sentry-safe-plugin · https://github.com/CharlesTheGreat77/ComboCracker-FZ · https://github.com/zinongli/KeyCopier · https://lab.flipper.net/apps/nfc_rfid_detector
- Crypto/misc: https://github.com/akopachov/flipper-zero_authenticator · https://github.com/xtruan/FlipBIP · https://github.com/Tyl3rA/FlipCrypt · https://github.com/Kingal1337/flipper-barcode-generator
- Internal cross-refs: [capabilities/badusb.md](../capabilities/badusb.md) · [capabilities/nfc-rfid.md](../capabilities/nfc-rfid.md) · [topics/security-pentest.md](../topics/security-pentest.md) · [legal-and-safety.md](../legal-and-safety.md)
