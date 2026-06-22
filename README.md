<!-- mcp-name: io.github.pogorelov-labs/flipper-ble-mcp -->

# flipper-ble-mcp 🐬📡

> Drive a **Flipper Zero** wirelessly over **Bluetooth LE** from Claude — no USB cable — backed by
> a **self-evolving knowledge base** that makes every session faster than the last.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![MCP](https://img.shields.io/badge/Model_Context_Protocol-server-purple.svg)

**flipper-ble-mcp** is three layers that form a loop:

1. **An MCP server** (`src/`) — 38 tools that control a Flipper Zero over BLE: read device info & files, screenshot the screen, inject button presses, launch apps, app-driven Sub-GHz/IR transmit, GPIO, BadUSB, and a scheduled read-only **health-watch**.
2. **A skill** (`.claude/skills/flipper/`) — the operating *brain*: an `ORIENT → EXECUTE → CAPTURE` loop, a routine index (task → KB doc → tools), verified menu maps, and safety gates.
3. **A knowledge base** (the docs in this repo) — ships prebuilt with deep Flipper + toolkit knowledge the agent **reads before acting** and **writes back to after** (`/flipper-learn`).

```
read the KB  →  act via MCP  →  capture what you learned  →  KB grows  →  next session is faster
```

That last arrow is the point: instead of re-deriving how the device behaves each time, the agent
**accumulates expertise** — and it ships with a big head start.

> ⚠️ **macOS only (today).** The Bluetooth work runs inside a small ad-hoc-signed `.app` that carries the
> macOS Bluetooth entitlement; the MCP process itself never touches BT. See [Architecture](#architecture).
>
> ⚠️ **Dual-use tool.** It can transmit RF/IR and inject USB keystrokes (BadUSB). **Your own devices,
> authorized targets, and legal frequencies only.** Every real action is human-approved per call.
> See [SECURITY.md](SECURITY.md).

## Why
LLM agents are great at reasoning and terrible at remembering what they learned last time. This project
pairs real hardware control (an MCP server) with a **knowledge base the agent both consumes and grows** —
so operating a Flipper gets faster and more reliable with use, and the knowledge is *portable* (it ships
in the repo, not trapped in one chat).

## Demo
<!-- TODO: 30–60s GIF — "ask Claude to screenshot the Flipper / press a button → it happens" -->
_Demo GIF coming soon._

## Architecture
```
Claude (Desktop / Code)
      │  MCP (stdio)
      ▼
flipper-ble MCP server  ──────────────┐   (never touches Bluetooth directly)
      │  token-authed Unix socket      │
      ▼                                │
resident daemon  (holds ONE BLE link)  │  runs inside FlipperBLE.app —
      │  Bluetooth LE                   │  the ad-hoc-signed bundle that carries
      ▼                                ┘  the macOS Bluetooth (TCC) entitlement
   Flipper Zero
```
A persistent daemon keeps a single BLE connection open (status/reads ~0.1–0.3 s, screenshot/press
~1.5 s; idle-disconnects to free the radio for your phone). The socket is `0600` + shared-token authed.

## Install
> Prerequisites: **macOS**, a **Flipper Zero** (Momentum / Unleashed / official firmware), **Claude
> Code** or **Claude Desktop**, Python 3.11+, and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/pogorelov-labs/flipper-ble-mcp && cd flipper-ble-mcp
./app/build_app.sh            # builds + ad-hoc-signs FlipperBLE.app (one-time; no Apple Dev account)
```
Add the MCP server to Claude — `claude mcp add flipper-ble -- uvx flipper-ble-mcp`, or in your Claude Desktop config:

```json
{
  "mcpServers": {
    "flipper-ble": { "command": "uvx", "args": ["flipper-ble-mcp"] }
  }
}
```

Then **run Claude Code in this repo**: the `flipper` skill + the KB are auto-discovered, so just ask —
*"what's my Flipper's battery?"* / *"screenshot my Flipper."* (To use the skill outside the repo, copy
`.claude/skills/flipper/` and `.claude/commands/flipper-learn.md` into your `~/.claude/`.)

## The self-evolving knowledge base
- **Seed** (this repo) — curated, general Flipper + toolkit knowledge. Indexed by [`llms.txt`](llms.txt).
- **Local overlay** (`kb-local/`, git-ignored) — where each install's new learnings land via
  **`/flipper-learn`**. The skill reads it alongside the seed; local entries win on conflict.
- **PR-back** — broadly-useful learnings get promoted into the seed via pull request, so the
  community's collective experience compounds. Classification rule: [`.claude/skills/flipper/references/kb-map.md`](.claude/skills/flipper/references/kb-map.md).

## Tools
38 tools — full table + RPC mapping in [`resources/flipper-ble-control.md`](resources/flipper-ble-control.md). Highlights: `device_info`, `power_info`, `screenshot`, `press` / `press_sequence`, `storage_*`, `app_launch`, `transmit_subghz` / `transmit_infrared` (gated), `gpio_*`, `run_badusb` (gated), `healthwatch`.

## Safety & responsible use
See [SECURITY.md](SECURITY.md): every action is human-approved per call; RF/IR/BadUSB is for your own
authorized targets on legal bands; the health-watch is read-only and default-off; the agent is
instructed never to autonomously transmit.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) — including how to PR a learned-KB entry back into the seed.
House style for KB docs: [`CLAUDE.md`](CLAUDE.md).

## License
[MIT](LICENSE) © 2026 Ruslan Pogorelov.

---

**State:** 70 content docs, ~102k words. The knowledge base below is generated from per-doc frontmatter —
run `python3 build-kb-index.py` to rebuild; never hand-edit the block.

<!-- BEGIN GENERATED INDEX (do not hand-edit — run: python3 build-kb-index.py) -->
## Index

### Start here / Core
| File | Status | What's in it |
|---|---|---|
| [use-cases-model.md](use-cases-model.md) | ✅ | Scored data model — schema + 1–10 real-use rubric + 63 use-cases in ranked score bands. |
| [01-architecture.md](01-architecture.md) | ✅ | Hardware block map, STM32WB MCU, radios, software stack, SD layout, and full capability map. |
| [legal-and-safety.md](legal-and-safety.md) | ✅ | Dual-use ground rules — RF-transmit, cloning, HID, EMV reality, and a responsible-use checklist. |
| [glossary.md](glossary.md) | ✅ | One-line definitions of every term used across the KB, each linking to its deep-dive. |

> **Dataset:** [use-cases.csv](use-cases.csv) / [use-cases.json](use-cases.json) — regenerate the JSON with `python3 build-use-cases-json.py`. UC-ID → docs map: [uc-index.json](uc-index.json).

### Firmware
| File | Status | What's in it |
|---|---|---|
| [firmware/README.md](firmware/README.md) | ✅ | Firmware comparison matrix, Xtreme to Momentum history, flashing/recovery, and legal/stability risks. |
| [firmware/migration-xtreme-to-momentum.md](firmware/migration-xtreme-to-momentum.md) | ✅ | Step-by-step — back up SD, flash Momentum, restore, re-enable add-ons, verify (frontier Stage 0). |
| [firmware/momentum.md](firmware/momentum.md) | ✅ | Feature-rich Xtreme successor — capabilities by domain plus an honest is-it-the-best verdict. |
| [firmware/official.md](firmware/official.md) | ✅ | Stock OFW from Flipper Devices — abilities, deliberate limits, and the sanctioned app catalog. |
| [firmware/roguemaster.md](firmware/roguemaster.md) | ✅ | Kitchen-sink, bleeding-edge custom firmware with the largest bundled app/game set and most crashes. |
| [firmware/unleashed.md](firmware/unleashed.md) | ✅ | Unlocked, stable, RF-focused custom firmware — the oldest OFW fork, favored for serious Sub-GHz work. |

### Hardware & GPIO
| File | Status | What's in it |
|---|---|---|
| [hardware/README.md](hardware/README.md) | ✅ | GPIO pinout, ADC/PWM/buses, power limits, and the Flipper's internal-radio front-end hardware. |
| [hardware/esp32-firmware-comparison.md](hardware/esp32-firmware-comparison.md) | ✅ | Bruce vs Ghost ESP vs Marauder — which firmware to flash on an ESP32 Flipper backpack. |
| [hardware/esp32-marauder-module.md](hardware/esp32-marauder-module.md) | ✅ | The ESP32-WROOM Marauder backpack hardware — GPIO 9-18 mount (3V3), the freeze fix, BOOT/RST buttons, dual-SD, flashing. |
| [hardware/gpio-addons-current.md](hardware/gpio-addons-current.md) | ✅ | Current GPIO add-ons — DevBoard, VGM, Marauder/Ghost ESP, Mayhem, NRF24, CC1101, GPS, protoboards. |
| [hardware/buying-guide.md](hardware/buying-guide.md) | ✅ | Which GPIO add-on(s) to buy, by goal/persona, with a board-vs-persona comparison table. |
| [hardware/addons-explained.md](hardware/addons-explained.md) | ✅ | Plain-words use-cases + pros/cons for each Flipper GPIO add-on — GPS, NRF24, CC1101, BLE sniffer, thermal, geiger. |
| [hardware/gpio-addons-potential.md](hardware/gpio-addons-potential.md) | ✅ | DIY GPIO add-ons — I²C/SPI/UART sensors, displays, LoRa, BLE sniffer, logic analyzer, and design limits. |

### Capabilities (built-in feature deep-dives)
| File | Status | What's in it |
|---|---|---|
| [capabilities/badusb.md](capabilities/badusb.md) | ✅ | HID keystroke injection over USB (and BLE on CFW) — Ducky Script, layouts, OS targets, and blue-team defenses. |
| [capabilities/ibutton.md](capabilities/ibutton.md) | ✅ | Dallas / Cyfral / Metakom contact "touch" keys over 1-Wire — read, emulate, and clone to writable blanks. |
| [capabilities/infrared.md](capabilities/infrared.md) | ✅ | Capture, store, and replay consumer IR; protocols, .ir format, universal remotes, and the Flipper-IRDB library. |
| [capabilities/nfc-rfid.md](capabilities/nfc-rfid.md) | ✅ | Overview of the two card radios — LF 125 kHz RFID and HF 13.56 MHz NFC; deep dives live in cards/. |
| [capabilities/sub-ghz.md](capabilities/sub-ghz.md) | ✅ | CC1101 sub-1-GHz radio — bands, modulation/presets, on-device workflows, .sub format, protocol decoders. |

### Cards, NFC & RFID (deep-research sub-domain)
| File | Status | What's in it |
|---|---|---|
| [cards/README.md](cards/README.md) | ✅ | Hub: card taxonomy, security tiers, and the cards doc index |
| [cards/cloning-matrix.md](cards/cloning-matrix.md) | ✅ | What's cloneable + how, magic cards, and a blanks list |
| [cards/iclass-picopass.md](cards/iclass-picopass.md) | ✅ | iCLASS legacy vs SE/SEOS; the PicoPass app |
| [cards/lf-125khz.md](cards/lf-125khz.md) | ✅ | EM4100/HID Prox/Indala/AWID + T5577 cloning |
| [cards/mifare.md](cards/mifare.md) | ✅ | MIFARE Classic/Ultralight/NTAG/DESFire + Crypto1 attacks |
| [cards/nfc-theory.md](cards/nfc-theory.md) | ✅ | RFID/NFC physics + ISO 14443/15693/18092 protocols |

### Wi-Fi (ESP32 Marauder add-on)
| File | Status | What's in it |
|---|---|---|
| [wifi/README.md](wifi/README.md) | ✅ | Hub: Wi-Fi capability map — which use-case lives in which doc. |
| [wifi/evil-portal.md](wifi/evil-portal.md) | ✅ | Rogue-AP captive-portal credential harvesting. |
| [wifi/marauder-mcp-scan.md](wifi/marauder-mcp-scan.md) | ✅ | Agent-driven AP scan — launch Marauder over the BLE MCP, run scanap, read the full network list from the SD log. |
| [wifi/own-network-audit.md](wifi/own-network-audit.md) | ✅ | Runnable: audit your own PSK (capture, hcxtools, hashcat). |
| [wifi/deauth.md](wifi/deauth.md) | ✅ | Deauthentication: the 802.11 flaw and the PMF/802.11w defense. |
| [wifi/recon-and-attacks.md](wifi/recon-and-attacks.md) | ✅ | Scan, sniff to PCAP, beacon spam, analyzer, wardrive, detect-deauth. |
| [wifi/wpa-handshake-pmkid.md](wifi/wpa-handshake-pmkid.md) | ✅ | Capture the WPA 4-way handshake / PMKID and crack it offline with hashcat. |

### Bluetooth / BLE
| File | Status | What's in it |
|---|---|---|
| [bluetooth/README.md](bluetooth/README.md) | ✅ | Hub for Bluetooth on this rig — Classic vs BLE, and the BLE use-case map across the sub-domain docs. |
| [bluetooth/airtag-tracker-detection.md](bluetooth/airtag-tracker-detection.md) | ✅ | How Find My works, anti-stalking tracker detection, rig limits, and FindMy Flipper as the inverse emulator. |
| [bluetooth/ble-sniffer-addon.md](bluetooth/ble-sniffer-addon.md) | ✅ | Real BLE connection capture via nRF52840/nRF Sniffer or Sniffle, plus crackle for LE Legacy pairings. |
| [bluetooth/ble-spam.md](bluetooth/ble-spam.md) | ✅ | Advertising-flood pairing popups (Sour Apple/Fast Pair/Swift Pair); the iOS 17.2 story; nuisance, not a hack. |
| [bluetooth/classic.md](bluetooth/classic.md) | ✅ | Bluetooth Classic (BR/EDR) attacks — KNOB, BIAS, BlueBorne — and why this rig can't touch them. |
| [bluetooth/interception.md](bluetooth/interception.md) | ✅ | Interception reality — advertising vs connection sniffing, pairing crypto, and what this rig can/can't do. |

### Theory
| File | Status | What's in it |
|---|---|---|
| [theory/relay-attacks.md](theory/relay-attacks.md) | ✅ | The attack class that beats correct crypto — PKES/BLE/NFC relay; UWB/distance-bounding defense |
| [theory/rolling-codes.md](theory/rolling-codes.md) | ✅ | KeeLoq internals, RollJam/RollBack, cryptanalysis, and defenses |
| [theory/human-layer.md](theory/human-layer.md) | ✅ | The gap no patch closes — phishing, BadUSB social-eng, NFC/QR baiting; passkeys as the fix |

### Topics
| File | Status | What's in it |
|---|---|---|
| [topics/ai-flipper-possibilities.md](topics/ai-flipper-possibilities.md) | ✅ | What an AI agent driving the Flipper unlocks, the hardware/crypto ceiling, and injection→hardware risk. |
| [topics/tinkering.md](topics/tinkering.md) | ✅ | Maker/electronics projects, FAP/ufbt app dev, on-device JavaScript, and asset packs. |
| [topics/security-pentest.md](topics/security-pentest.md) | ✅ | Honest red-team framing — capability-vs-tool matrix, methodology, ROE checklist, remediation. |
| [topics/subghz-region-lock.md](topics/subghz-region-lock.md) | ✅ | How Flipper's Sub-GHz region provisioning works, why "Missing region file" blocks TX, and the fix. |
| [topics/use-cases.md](topics/use-cases.md) | ✅ | Legitimate uses & project ideas organized by capability, with a starter-projects table. |
| [topics/remaining-gaps.md](topics/remaining-gaps.md) | ✅ | Where capability still beats modern defenses in 2026 — deployment inertia, relay attacks, IoT floor, FM11RF08S. |

### Resources
| File | Status | What's in it |
|---|---|---|
| [resources/best-github-repos.md](resources/best-github-repos.md) | ✅ | Curated GitHub repos by category, with maintenance flags |
| [resources/community-and-video.md](resources/community-and-video.md) | ✅ | Discord/Reddit/forums + vetted YouTube creators |
| [resources/flipper-ble-control.md](resources/flipper-ble-control.md) | ✅ | Wireless Flipper control SOLVED — read/see/drive/launch/file-read over BLE via the flipper-ble MCP server. |
| [resources/cool-projects.md](resources/cool-projects.md) | ✅ | Fun/novel projects — FlipperHTTP web apps, games, VGM DOOM, MagSpoof, Home Assistant |
| [resources/flipper-mcp-and-ai.md](resources/flipper-mcp-and-ai.md) | ✅ | Drive the Flipper from Claude — MCP servers, AgentFlipper, Mac/USB setup, AI-control risks |
| [resources/flipper-control-playbook.md](resources/flipper-control-playbook.md) | ✅ | How an AI agent should drive the Flipper via the MCP toolkit — data-first algorithm, menu maps, app-entry recipes, conventions. |
| [resources/flipper-control-mcp-server.md](resources/flipper-control-mcp-server.md) | ✅ | Gated control MCP server (Stage 3) — 14 tools (input/apps/LED/GPIO/IR+SubGHz-TX/writes + screenshot) over USB, each approved. |
| [resources/flipper-healthwatch.md](resources/flipper-healthwatch.md) | ✅ | Gated, default-off launchd job that polls the Flipper read-only 3×/day (battery/storage/clock/firmware) and notifies on anomalies. |
| [resources/flipper-read-mcp-server.md](resources/flipper-read-mcp-server.md) | ✅ | The read-only MCP server we built for this rig — 14 native mcp__flipper__* device-read tools over USB, one allowlist. |
| [resources/github-landscape.md](resources/github-landscape.md) | ✅ | Leaderboard + people — top repos by stars, devs/orgs to follow, the ESP32 scene |
| [resources/apps-badusb-automotive-misc.md](resources/apps-badusb-automotive-misc.md) | ✅ | Runbook for the BadUSB/HID, CAN/automotive, physical-access, crypto and misc security FAPs on my Momentum rig. |
| [resources/apps-rfid-ibutton-infrared.md](resources/apps-rfid-ibutton-infrared.md) | ✅ | Per-app runbook for the LF RFID (125 kHz), iButton/1-Wire, and Infrared apps on the owner's maxed Momentum rig. |
| [resources/apps-nfc.md](resources/apps-nfc.md) | ✅ | Per-app reference for every 13.56 MHz NFC .fap on my Momentum rig — what it does, options, gotchas, sources. |
| [resources/learning-and-docs.md](resources/learning-and-docs.md) | ✅ | Docs, cheat-sheets, and deep RF+NFC learning material by level |
| [resources/notable-apps-and-data.md](resources/notable-apps-and-data.md) | ✅ | Deeper cut — pyFlipper scripting, sensor/utility apps, data/dumps, asset packs, 3D |
| [resources/mcp-setup-claude-code.md](resources/mcp-setup-claude-code.md) | ✅ | Install busse MCP, add to Claude Code over USB, scope it read-only with gating — first safe AI↔device milestone. |
| [resources/apps-subghz.md](resources/apps-subghz.md) | ✅ | Per-app reference for the Sub-GHz/RF .faps on this Momentum rig — what each does, key options, use-cases, gotchas, sources. |
| [resources/subghz-device-repos.md](resources/subghz-device-repos.md) | ✅ | Device-specific Sub-GHz repos and .sub collections (TouchTunes, gates, Tesla, sensors) |
| [resources/tools-and-software.md](resources/tools-and-software.md) | ✅ | qFlipper, Flipper Lab, flashers, and an SD-backup checklist |
| [resources/apps-esp-ble-nrf24.md](resources/apps-esp-ble-nrf24.md) | ✅ | Per-app runbook for the ESP32 / BLE / NRF24 companion FAPs on my Momentum rig — what each does, settings, hardware, sources. |

<!-- END GENERATED INDEX -->
