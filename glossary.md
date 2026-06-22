---
title: Glossary
domain: core
type: meta
status: detailed
summary: One-line definitions of every term used across the KB, each linking to its deep-dive.
hardware: []
use_cases: []
related: [README.md, capabilities/sub-ghz.md, cards/README.md]
tags: [glossary, definitions, terminology, reference]
last_verified: 2026-06-19
---

# Glossary

> **TL;DR —** One-line definitions of the jargon used across the KB — RF/Sub-GHz, NFC/RFID, Wi-Fi, BLE, security concepts, firmware, and the ESP32 scene — each linking to the doc that explains it.
> Terms link to the deep-dive that explains them. Part of the [KB](README.md).

## RF & Sub-GHz
| Term | Meaning |
|---|---|
| **Sub-GHz** | Radio below 1 GHz (the Flipper's 300–928 MHz CC1101 bands) — remotes, sensors, gates. [sub-ghz](capabilities/sub-ghz.md) |
| **CC1101** | The TI transceiver chip that does Sub-GHz (internal + external module) |
| **ASK / OOK** | Amplitude-Shift Keying / On-Off Keying — the modulation most cheap remotes use |
| **FSK / PSK** | Frequency- / Phase-Shift Keying — other modulations (e.g. Indala = PSK) |
| **Manchester / biphase** | Line codings that encode bits as transitions (common in LF + Sub-GHz) |
| **ISM band** | License-exempt radio bands (433/868/915 MHz, 2.4 GHz) |
| **Fixed code** | Same code every press → **replayable** ([rolling-codes](theory/rolling-codes.md)) |
| **Rolling / hopping code** | Code changes each press (counter + secret) → resists replay |
| **KeeLoq** | The classic rolling-code cipher/scheme used by many remotes |
| **RAW capture** (`.sub`) | Recording the waveform when the protocol is unknown |
| **de Bruijn sequence** | Compact bitstream used to brute-force small fixed-code spaces |
| **TPMS / POCSAG** | Tire-pressure sensors / pager protocol — Sub-GHz decoders |

## NFC / RFID / cards
| Term | Meaning |
|---|---|
| **LF / HF** | Low-Freq 125 kHz / High-Freq 13.56 MHz card radios [cards/](cards/README.md) |
| **RFID vs NFC** | RFID = the broad tech; NFC = the 13.56 MHz HF subset |
| **ISO 14443 / 15693** | HF standards — 14443 (MIFARE, ~10 cm) / 15693 (vicinity, iCLASS) |
| **UID** | Card's unique ID; many weak readers trust *only* this |
| **NDEF** | Standard data format on NFC tags (URL/Wi-Fi/vCard) |
| **MIFARE Classic** | Ubiquitous HF card using the broken **Crypto1** cipher [mifare](cards/mifare.md) |
| **Crypto1** | MIFARE Classic's 48-bit cipher, broken since 2008 |
| **nested / hardnested / darkside** | Crypto1 key-recovery attack families |
| **mfkey32** | Recover a reader's key from captured nonces |
| **magic card** (Gen1a/Gen2/CUID/UFUID/Gen4) | Cards whose UID/block-0 is writable → full clones [cloning-matrix](cards/cloning-matrix.md) |
| **NTAG / Ultralight** | Simple HF tags (amiibo = NTAG215) |
| **DESFire (EV1/2/3)** | Modern AES HF card — **not** broken |
| **iCLASS / Picopass / SEOS** | HID HF access cards — legacy weak, **SE/SEOS** strong [iclass-picopass](cards/iclass-picopass.md) |
| **EM4100 / HID Prox / Indala / AWID** | Common LF access formats (static ID) [lf-125khz](cards/lf-125khz.md) |
| **T5577 / EM4305** | Writable LF blanks (the clone target) |
| **EMV** | Bank-card contactless standard — read-only public data; **no** cloning |
| **FeliCa / FDX-B** | Sony HF (transit, JP) / 134.2 kHz animal chip (Flipper can't read) |

## Wi-Fi
| Term | Meaning |
|---|---|
| **WPA2 / WPA3** | Wi-Fi security; WPA3 uses **SAE** (offline-crack resistant) |
| **PSK** | Pre-Shared Key (the Wi-Fi password) |
| **SAE** | WPA3's "Dragonfly" handshake — resists offline cracking |
| **4-way handshake / EAPOL** | The WPA join exchange (EAPOL-Key frames) [wpa](wifi/wpa-handshake-pmkid.md) |
| **PMK / PTK / MIC** | Master key / session key / integrity check |
| **PMKID** | A value some APs leak that enables **clientless** capture |
| **handshake/PMKID capture** | Grab the proof, **crack offline** (hashcat `-m 22000`) |
| **deauth** | Forged "disconnect" frame [deauth](wifi/deauth.md) |
| **PMF / 802.11w** | Protected Management Frames — blocks deauth (mandatory in WPA3) |
| **evil twin / captive portal** | Rogue AP + fake login page [evil-portal](wifi/evil-portal.md) |
| **WPS** | Easy-pair feature with brute-forceable PIN |
| **hcxtools / hashcat** | PC tools to convert captures and crack them |

## Bluetooth / BLE
| Term | Meaning |
|---|---|
| **BLE vs BR/EDR** | Low-Energy (sensors/keys) vs Classic (audio) [bluetooth/](bluetooth/README.md) |
| **GATT** | BLE's data/service model |
| **advertising** | BLE broadcast on 3 channels (37/38/39) — what scanning reads [interception](bluetooth/interception.md) |
| **CONNECT_IND** | The packet that starts a BLE connection (hop params) |
| **LE Legacy vs LE Secure Connections** | Weak (crackle-able) vs ECDH-strong pairing |
| **Just Works** | Pairing with no MITM protection (TK = 0) |
| **crackle** | Tool that decrypts LE-Legacy captures |
| **KNOB / BIAS** | Bluetooth Classic key-entropy / impersonation attacks [classic](bluetooth/classic.md) |
| **FindMy / AirTag** | Apple crowd-sourced tracker network [airtag](bluetooth/airtag-tracker-detection.md) |

## Security concepts
| Term | Meaning |
|---|---|
| **Replay** | Record now, transmit later (beaten by rolling codes) |
| **Relay** | Forward the *live* exchange — beats correct crypto [relay-attacks](theory/relay-attacks.md) |
| **Distance bounding / UWB** | Time-of-flight ranging — the real relay defense |
| **BadUSB / BadBT** | Flipper acts as a keyboard and injects keystrokes [badusb](capabilities/badusb.md) |
| **Ducky Script** | The BadUSB payload language |
| **FIDO2 / passkey** | Phishing-resistant auth [human-layer](theory/human-layer.md) |
| **ROE** | Rules of Engagement — the authorization scope for testing [security-pentest](topics/security-pentest.md) |
| **dual-use** | Same capability is fine on your stuff, illegal on others' [legal](legal-and-safety.md) |

## Flipper & firmware
| Term | Meaning |
|---|---|
| **OFW / CFW** | Official Firmware / Custom Firmware |
| **Unleashed / Momentum / Xtreme / RogueMaster** | The four firmwares [firmware/](firmware/README.md) |
| **FAP** | Flipper Application Package (a `.fap` app) |
| **ufbt** | Micro build tool for FAPs [tinkering](topics/tinkering.md) |
| **Furi / FreeRTOS** | The Flipper OS core / its RTOS |
| **asset pack** | Swappable animations/icons/fonts |
| **GPIO** | The 18-pin header (UART/SPI/I²C/1-Wire/SWD) [hardware](hardware/README.md) |
| **iButton / 1-Wire** | Contact keys (Dallas/Cyfral/Metakom) [ibutton](capabilities/ibutton.md) |
| **VGM** | Video Game Module (RP2040 + DVI + IMU) |
| **qFlipper / Flipper Lab** | Desktop updater / web app |

## ESP32 & external-tool scene
| Term | Meaning |
|---|---|
| **Marauder / Ghost ESP / Bruce** | ESP32 Wi-Fi/BLE firmwares [github-landscape](resources/github-landscape.md) |
| **FlipperHTTP** | ESP32 bridge that gives the Flipper internet apps [cool-projects](resources/cool-projects.md) |
| **Sniffle / Ubertooth / nRF52840** | Real BLE/Classic sniffers (add-ons) [ble-sniffer-addon](bluetooth/ble-sniffer-addon.md) |
| **Proxmark3** | The deep RFID/NFC research tool (beyond Flipper) |
| **HackRF / RTL-SDR** | True software-defined radios (the Flipper is **not** an SDR) |

## Sources
- Definitions distilled from the linked deep-dive docs in this KB.
