---
title: Use-Case Data Model
domain: core
type: dataset
status: detailed
summary: Scored data model — schema + 1–10 real-use rubric + 63 use-cases in ranked score bands.
hardware: []
use_cases: []
related: [my-use-cases.md, use-cases.csv, use-cases.json, hardware/buying-guide.md]
tags: [data-model, scoring, rubric, use-cases, ranking]
last_verified: 2026-06-19
---

# Use-Case Data Model

> **TL;DR —** The structured, scored model behind the catalog: a schema plus a 1–10 real-use rubric, with all 63 use-cases ranked into score bands. The CSV is the source of truth; the tables here are a ranked view.
> Canonical data: **[use-cases.csv](use-cases.csv)** (63 rows) · machine export **[use-cases.json](use-cases.json)** (regenerate: `python3 build-use-cases-json.py`). Prose: [my-use-cases.md](my-use-cases.md). Part of the [KB](README.md).

This is the **data model** behind [my-use-cases.md](my-use-cases.md): one row per use-case, with a
defined schema and a scoring rubric so the numbers are consistent. The CSV is the source of
truth (sort/filter it); the tables below are a **ranked view** grouped by real-use score.

## Schema

| Field | Type / enum | Meaning |
|---|---|---|
| `id` | UC-NN | Stable reference id |
| `category` | IR · SubGHz · RFID-LF · NFC-HF · iButton · HID · BLE · WiFi · GPIO · Software · Defensive | Domain |
| `name` | text | Short use-case name |
| `purpose` | text | One-line goal |
| `description` | text | 1-sentence detail |
| `target` | **Hardware** · **Software** · **Hybrid** | Acts on external hardware/RF/cards, runs on the Flipper, or both |
| `needs_accessory` | None · CC1101-433 · ESP32-Marauder(+SD) · GPIO-wiring · consumable blank · `(need: …)` | What it requires beyond the Flipper |
| `firmware` | OFW · CFW · n/a(ESP) | Minimum Flipper firmware (or n/a when the ESP runs its own) |
| `real_use_score` | 1–10 | Genuine legitimate value (see rubric) |
| `difficulty` | Easy · Medium · Hard | Skill/effort to do it |
| `legality` | Low · Medium · High | Authorization sensitivity (dual-use risk) |
| `status` | Ready · NeedAccessory · ByDesign-No | Feasibility with my current kit |
| `prereq_consumable` | None · T5577 · NTAG21x · NTAG215 · Magic card · RW1990 | Cheap blank needed beyond the kit |
| `time_to_value` | Instant · Quick · Setup · Project · n/a | Effort/time to first useful result (incl. first-time setup) |
| `kb_ref` | path | How-to file in this KB |

### `real_use_score` rubric (legitimate value, not novelty)
- **9–10** — high, recurring real value (you'd actually use it often).
- **7–8** — solidly useful, periodic.
- **5–6** — situational / occasional.
- **3–4** — niche, demo, or mostly novelty.
- **1–2** — rarely practical / prank / impossible-by-design.

> Scores reflect value to *me* (a legitimate owner). "Attack" use-cases often score low for real life
> even when technically impressive, because authorized opportunities are rare. Honesty over hype.

---

## Ranked view (Ready-now use-cases, by score)

### ⭐ Tier A — real-use 8–10 (use these)
| ID | Use-case | Cat | Target | Needs | FW | Score | Diff | Legal |
|---|---|---|---|---|---|:--:|---|---|
| UC-01 | Universal IR remote | IR | HW | None | OFW | **9** | Easy | Low |
| UC-02 | Learn & save a remote | IR | HW | None | OFW | **8** | Easy | Low |
| UC-15 | LF fob read/emulate/clone | RFID-LF | HW | None¹ | OFW | **8** | Easy | Med |
| UC-48 | TOTP 2FA authenticator | Software | SW | None | OFW | **8** | Easy | Low |

### Tier B — real-use 6–7 (solid)
| ID | Use-case | Cat | Target | Needs | FW | Score | Diff | Legal |
|---|---|---|---|---|---|:--:|---|---|
| UC-04 | Capture/replay fixed-code remote | SubGHz | HW | None | OFW | 7 | Easy | Med |
| UC-16 | MIFARE Classic read/crack/clone | NFC-HF | HW | None | CFW | 7 | Med | Med |
| UC-19 | NDEF tag writing | NFC-HF | HW | None¹ | OFW | 7 | Easy | Low |
| UC-05 | Frequency analyzer / RF survey | SubGHz | HW | None | OFW | 6 | Easy | Low |
| UC-13 | Long-range 433 capture/replay | SubGHz | HW | **CC1101** | CFW | 6 | Med | Med |
| UC-14 | Range-test own 433 gear | SubGHz | HW | **CC1101** | CFW | 6 | Easy | Low |
| UC-17 | NTAG/Ultralight read & emulate | NFC-HF | HW | None | OFW | 6 | Easy | Low |
| UC-20 | PicoPass / HID iCLASS | NFC-HF | HW | None | OFW | 6 | Med | Med |
| UC-24 | iButton read/emulate/write | iButton | HW | None¹ | OFW | 6 | Easy | Med |
| UC-31 | Wi-Fi scan/recon | WiFi | HW | **Marauder** | ESP | 6 | Easy | Med |
| UC-32 | Sniff → PCAP | WiFi | HW | **Marauder+SD** | ESP | 6 | Med | Med |
| UC-33 | WPA handshake/PMKID capture | WiFi | HW | **Marauder** | ESP | 6 | Med | High |
| UC-40 | AirTag/tracker detection | Defensive | HW | **Marauder** | ESP | 6 | Easy | Low |
| UC-41 | Bluetooth skimmer detection | Defensive | HW | **Marauder** | ESP | 6 | Easy | Low |
| UC-42 | USB-UART/SPI/I2C bridge | GPIO | Hybrid | **GPIO** | OFW | 6 | Med | Low |
| UC-52 | Build own FAP/JS apps | Software | SW | None | CFW | 6 | Hard | Low |
| UC-53 | U2F/FIDO second factor | Software | Hybrid | None | OFW | 6 | Easy | Low |
| UC-56 | Audit own RF/cards | Defensive | HW | None | OFW | 6 | Med | Low |

### Tier C — real-use 4–5 (situational)
| ID | Use-case | Cat | Needs | Score | Legal |
|---|---|---|---|:--:|---|
| UC-06 | Read RAW unknown signal | SubGHz | None | 5 | Low |
| UC-18 | Magic-card full clone | NFC-HF | None¹ | 5 | Med |
| UC-22 | NFC toys emulate (amiibo/…) | NFC-HF | None | 5 | Low |
| UC-25 | BadUSB attack payloads | HID | None | 5 | High |
| UC-26 | BadUSB automation/keep-awake | HID | None | 5 | Low |
| UC-28 | BLE clicker / kbd-mouse remote | HID | None | 5 | Low |
| UC-30 | FindMy Flipper | BLE | None | 5 | Low |
| UC-34 | Deauth (authorized) | WiFi | Marauder | 5 | High |
| UC-37 | Channel/signal analyzer | WiFi | Marauder | 5 | Low |
| UC-39 | BLE scan/sniff (Marauder) | BLE | Marauder | 5 | Low |
| UC-43 | SWD debug another MCU | GPIO | GPIO | 5 | Low |
| UC-44 | Logic analyzer | GPIO | GPIO | 5 | Low |
| UC-45 | GPIO sensor reading | GPIO | GPIO | 5 | Low |
| UC-50 | Mouse Jiggler | Software | None | 5 | Low |
| UC-54 | Detect Wi-Fi deauth attacks | Defensive | Marauder | 5 | Low |
| UC-55 | PCAP → Wireshark analysis | Defensive | Marauder+SD | 5 | Low |
| UC-08 | Weather-station read | SubGHz | None | 4 | Low |
| UC-09 | TPMS read | SubGHz | None | 4 | Low |
| UC-11 | Tesla charge-port opener | SubGHz | None | 4 | Low |
| UC-12 | 433 alarm/PIR/door monitor | SubGHz | None | 4 | Med |
| UC-21 | Transit card read (Metroflip) | NFC-HF | None | 4 | Low |
| UC-27 | BadBT/BadKB BLE keystrokes | HID | None | 4 | High |
| UC-36 | Evil Portal | WiFi | Marauder | 4 | High |
| UC-46 | Relay/servo/LED control | GPIO | GPIO | 4 | Low |
| UC-47 | Sentry Safe / e-safe opener | GPIO | GPIO | 4 | Med |

### Tier D — real-use 1–3 (niche / novelty)
| ID | Use-case | Cat | Needs | Score | Note |
|---|---|---|---|:--:|---|
| UC-03 | TV-B-Gone power-off | IR | None | 3 | Prank |
| UC-07 | Fixed-code brute-force | SubGHz | None | 3 | Slow, old systems only |
| UC-10 | POCSAG pager decode | SubGHz | None | 3 | Privacy-sensitive |
| UC-23 | DESFire/EMV metadata read | NFC-HF | None | 3 | Read-only demo |
| UC-35 | Beacon/probe/SSID spam | WiFi | Marauder | 3 | Nuisance |
| UC-38 | Wardrive (no GPS) | WiFi | Marauder+SD | 3 | No coordinates |
| UC-49 | Games | Software | None | 3 | Fun |
| UC-51 | Utilities (calc/clock/…) | Software | None | 3 | Minor |
| UC-29 | BLE Spam | BLE | None | 2 | Nuisance/novelty |

¹ Needs a cheap consumable blank — see the `prereq_consumable` column (T5577 / NTAG / magic card / RW key); not a Flipper accessory.

---

## ⛔ Not available with this kit (needs accessory or impossible)
| ID | Use-case | Status | Blocker | Unlock with | Score |
|---|---|---|---|---|:--:|
| UC-58 | Geo-wardriving / mapping | NeedAccessory | no GPS | UART GPS module | 5 |
| UC-59 | 315/868/915 long-range | NeedAccessory | 433-only board | other-band CC1101 | 5 |
| UC-57 | 2.4GHz HID mousejacking | NeedAccessory | no NRF24 | NRF24 module | 4 |
| UC-60 | 5GHz Wi-Fi testing | NeedAccessory | WROOM is 2.4-only | ESP32-C5/C6 board | 4 |
| UC-61 | Pet/animal microchip read | ByDesign-No | 134.2kHz vs Flipper 125kHz | dedicated reader | 3 |
| UC-62 | Defeat rolling codes | ByDesign-No | crypto/counters | nothing — security working | 1 |
| UC-63 | Clone/pay with EMV card | ByDesign-No | EMV crypto | nothing | 1 |

---

## Summary stats
- **63** use-cases modeled · **56 Ready** with my current kit · **4** need another accessory · **3** impossible by design.
- **Ready by requirement:** ~28 Flipper-alone · 3 need the **CC1101** · ~13 need the **Marauder** · 6 need **GPIO wiring** (no backpack mounted).
- **By target:** mostly **Hardware**; Software = TOTP/games/jiggler/utilities/dev; Hybrid = HID + GPIO apps.
- **Highest real-use (≥8):** UC-01 IR remote, UC-02 IR learn, UC-15 LF fob clone, UC-48 TOTP authenticator → these are the everyday wins.
- **Best the backpacks add:** CC1101 → UC-13/14 (long-range 433); Marauder → UC-33 (handshake), UC-40/41 (tracker/skimmer detection).
- **Quick wins (Instant/Quick + score ≥7):** UC-01, UC-02, UC-04, UC-15, UC-19, UC-48 — high value, minimal setup.

## How to use this model
- **Plan daily use:** sort `use-cases.csv` by `real_use_score` desc.
- **Plan purchases:** filter `status = NeedAccessory` and read `needs_accessory` (see [buying-guide](hardware/buying-guide.md)).
- **Plan a session:** filter `needs_accessory` to one backpack (they're one-at-a-time).
- **Find quick wins:** filter `time_to_value` = Instant/Quick and `real_use_score` ≥ 6.
- **Stay safe:** check `legality` before anything Medium/High ([legal-and-safety](legal-and-safety.md)).

## Open questions / to research
- Re-score after real use — my actual scores will drift from these estimates.
- Add `time_to_value` / `prereq_consumable` columns if useful.
- Decide next accessory by best blocked-score-per-cost (GPS UC-58 vs NRF24 UC-57).

## Sources
- Derived from [my-use-cases.md](my-use-cases.md) and the capability files; see those for per-use-case citations.
