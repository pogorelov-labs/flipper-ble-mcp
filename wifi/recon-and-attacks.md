---
title: Wi-Fi Recon & the Rest of the Marauder Toolset
domain: wifi
type: reference
status: detailed
summary: Scan, sniff to PCAP, beacon spam, analyzer, wardrive, detect-deauth.
hardware: [esp32-marauder]
use_cases: [UC-31, UC-32, UC-35, UC-37, UC-38, UC-54]
related: [wifi/marauder-mcp-scan.md, wifi/wpa-handshake-pmkid.md, wifi/deauth.md, wifi/evil-portal.md, hardware/gpio-addons-current.md, topics/security-pentest.md]
tags: [recon, scanap, sniffing, pcap, beacon-spam, channel-analyzer, wardrive, deauth-detect]
last_verified: 2026-06-19
---

# Wi-Fi Recon & the Rest of the Marauder Toolset

> **TL;DR —** The Marauder Wi-Fi tools without their own deep-dive: scan/recon (scanap/scansta), sniff to PCAP, the beacon/probe/SSID spam family, channel/signal analyzer, wardrive (GPS-gated), and the defensive deauth/Pwnagotchi detectors.
> Pairs with [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md), [deauth.md](deauth.md), [evil-portal.md](evil-portal.md) · board [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md). Part of the [Wi-Fi hub](README.md) · [KB](../README.md).

## What this covers
The [Wi-Fi hub](README.md) maps every use-case to a doc. **The deep three live elsewhere:** WPA capture → [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md) (UC-33), deauth → [deauth.md](deauth.md) (UC-34), Evil Portal → [evil-portal.md](evil-portal.md) (UC-36). This page is everything else the **WiFi Marauder** app exposes — recon, sniffing-to-PCAP, the spam family, signal analysis, wardriving, and the defensive detectors. All on the **ESP32-WROOM Marauder** backpack: **2.4 GHz only**, onboard microSD for captures, driven over UART. **Authorized networks only** ([../legal-and-safety.md](../legal-and-safety.md)).

| § | Tool group | UC | Marauder items |
|---|---|---|---|
| 1 | Scan / recon | **UC-31** | `scanap`, `scansta`, Scan All, Select, List |
| 2 | Sniff → PCAP | **UC-32** | Packet Monitor, Raw/Beacon/Probe/Deauth/EAPOL sniff |
| 3 | Beacon / probe / SSID spam | **UC-35** | Beacon Spam (Random / List / Rick Roll / AP-clone), Probe Flood |
| 4 | Channel / signal analyzer | **UC-37** | Channel Analyzer, Signal Monitor, Packet Count |
| 5 | Wardrive | **UC-38** | Wardrive *(GPS-gated — see warning)* |
| 6 | Detect / defensive | **UC-54** | Deauth Sniff, Detect Pwnagotchi |

---

## 1. Scan / recon — `scanap` / `scansta` (UC-31)
The foundation. Everything targeted (deauth, AP-clone, targeted PMKID sniff) needs a target list built here first. Driving this **from an agent over MCP** (BLE — because Marauder seizes the USB serial) is its own verified recipe → **[marauder-mcp-scan.md](marauder-mcp-scan.md)**.

| Command | What it does | Builds |
|---|---|---|
| **`scanap`** (Scan APs) | Harvests beacons from nearby APs; adds each **unique BSSID** to the AP list | **AP list** |
| **`scansta`** (Scan Stations) | Finds **client/station** MACs — but **only** for stations associated with APs already in the AP list. **Run `scanap` first.** | **Station list** |
| **Scan All** | Combined AP + station discovery | both lists |
| **Select** (APs / Stations) | Traverse the list, click to mark targets **"active"** (shown in red). Active entries are what attacks target. | selection |
| **List** | Scrollable display of everything scanned this session | — |

**What each AP entry gives you:** BSSID, SSID, **channel**, **RSSI** (signal), encryption hint, and associated clients (after `scansta`).

- **Passive vs active:** scanning here is **passive** (just listening to beacons/probes the air already carries) — no frames injected, low legal risk on its own. The *active* steps are deauth/spam in §3 and [deauth.md](deauth.md).
- **SSID lists:** a separate user-editable list of SSID *strings* (not scanned APs) feeds **Beacon Spam List** and probe behaviour (§3).
- Lists live in RAM for the session; saving/clearing is per-build. The scan **output** is separate: on Momentum it **auto-logs** to `/ext/apps_data/marauder/logs/scanap_N.log` — read it back for the full list ([marauder-mcp-scan.md](marauder-mcp-scan.md)). *(In-RAM target-list persistence across sessions still varies by build — verify.)*

## 2. Sniff → PCAP (UC-32)
Capture raw 802.11 to the card, analyse in **Wireshark** on the Mac. **If a microSD is inserted, the sniffers auto-save a `.pcap`** — no extra step. WROOM = **2.4 GHz only**, so 5 GHz traffic is invisible.

| Sniff mode | Captures | Note |
|---|---|---|
| **Packet Monitor** | All mgmt frames, live graph + PCAP | best general-purpose capture |
| **Raw Sniff** | Everything across frame types | broadest, noisiest |
| **Beacon Sniff** | AP beacon frames | AP discovery / spoof detection |
| **Probe Request Sniff** | Client probe requests | shows what SSIDs devices seek |
| **Deauth Sniff** | Deauth/disassoc frames | doubles as a detector → §6 |
| **EAPOL / PMKID Scan** | EAPOL + PMKID frames | the WPA-capture path → [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md) |

**Packet Monitor display** (touchscreen): traffic-density line graph, colour-coded — **green = beacon**, **blue = probe request**, **red = deauth/disassoc**. (Text-feed builds: green beacon, cyan probe, magenta misc-mgmt, red deauth, white data.) Frames are matched on type bytes: `0x80` beacon, `0x40` probe req, `0xA0`/`0xC0` deauth/disassoc.

**Workflow:** pick channel (or hop) → run a sniff → pull the microSD → open the `.pcap` in Wireshark / `tshark`. EAPOL captures go to hcxtools → hashcat (see [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md)). Useful for blue-team baselining your own air — see [../topics/security-pentest.md](../topics/security-pentest.md).

## 3. Beacon / probe / SSID spam (UC-35)
Floods the air with fake management frames. **Nuisance / testing only** — disruptive to everyone in range and easy to trace. Treat like deauth: **own gear or authorized lab only** ([../legal-and-safety.md](../legal-and-safety.md)).

| Tool | What it sends | Effect |
|---|---|---|
| **Beacon Spam Random** | Beacons with **random SSIDs**, as fast as possible | floods nearby devices' network lists with junk |
| **Beacon Spam List** | One beacon per SSID in **your SSID list** | inject chosen fake network names |
| **Rick Roll Beacon** | Beacons whose SSIDs are the lyrics of *Never Gonna Give You Up* | the classic gag; lyrics show in nearby Wi-Fi lists |
| **Beacon Spam AP (clone)** | Beacons **copying APs you picked** via `scanap` → Select | spawns look-alike SSIDs of real APs |
| **Probe Request Flood** | Many probe requests with **random SSIDs** | confuses probe sniffers (Marauder, Pineapple, etc.) |

- AP-clone **requires a target list**: `scanap` → **Select** the APs to copy first (§1).
- Why it matters defensively: this is exactly the noise an **Evil Twin** / [evil-portal.md](evil-portal.md) setup leans on, and what a WIDS should flag.
- Honest limit: spam reveals **nothing** and breaks no crypto — it's pure clutter/DoS. Loud, obvious, and annoying to real users.

## 4. Channel / signal analyzer (UC-37)
The legitimate **site-survey** corner — find a clean channel, locate interference, eyeball signal. Passive; the most defensible day-to-day use of the board.

| Tool | Shows | Use |
|---|---|---|
| **Channel Analyzer** | Per-**channel** activity / congestion across the 2.4 GHz band | pick a quiet channel; spot interference |
| **Signal Monitor** | **Signal strength (RSSI)** of detected devices over time | walk down a signal; find a transmitter |
| **Packet Count** | Running tally of packets seen | quick "how busy is this channel" gauge |

- Exact on-screen rendering (graph axes, units, refresh) is thinly documented in the wiki — **(verify on your build)**.
- 2.4 GHz only, so this won't survey your 5 GHz APs. Pair with [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md) for board limits and [../my-use-cases.md](../my-use-cases.md) for where this fits.

## 5. Wardrive (UC-38) — ⚠️ no GPS on this board
Logs APs while you move, in **WiGLE.net** format (`wardrive_` filename prefix), uploadable to wigle.net for stats.

> ⚠️ **The catch on my rig: the Wardrive tool requires the GPS Modification.** The wiki states network info is **"only saved to the log file as long as the GPS has a valid fix."** With **no GPS attached**, the display shows **"No Fix"** and GPS data reads **all zeroes** — so you get **no usable geo-logged output**. Geo-mapping needs a **GPS add-on** wired to the Marauder's spare UART.

| Aspect | Detail |
|---|---|
| Output | WiGLE-format CSV, `wardrive_*` on the onboard microSD (or Flipper SD with serial firmware) |
| GPS | **Mandatory** for coordinates; uses an external module on UART (firmware ≥ 0.11.0) |
| No-GPS reality | "No Fix" / zeroed lat-lon → effectively no log written |
| Related | **GPS Tracker** logs a `.gpx` track (also needs the module) |

**Bottom line:** until I add a GPS module, UC-38 is **not usable for mapping** on this board. For plain "what APs are around me" without location, use **`scanap`** (§1) instead. Hardware path: [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md).

## 6. Detect deauth / defensive (UC-54)
The blue-team value of the same hardware — turn the offensive tools around to **spot** attacks.

| Tool | Detects | How |
|---|---|---|
| **Deauth Sniff** | **Deauth-flood / disassoc** attacks in range | filters for `0xA0`/`0xC0` frames; shows **source + dest MAC**; saves PCAP |
| **Detect Pwnagotchi** | A nearby **Pwnagotchi** (its distinctive beacon) | flags the device's advertisement |

- **Deauth Sniff as a WIDS-lite:** a sudden burst of deauth/disassoc frames is the signature of the attack in [deauth.md](deauth.md). Watching this on your own network tells you someone's trying to knock clients off (or force a handshake). It's the practical counterpart to UC-34.
- **Defensive takeaway:** if you see floods, the fix is **PMF / 802.11w** (mandatory in WPA3) — it makes forged deauths fail outright (see [deauth.md](deauth.md) §"Why modern Wi-Fi resists it").
- **Related detectors (pointers):** BLE-side AirTag / tracker and skimmer detection are Bluetooth tools, not Wi-Fi — they likely belong in a sibling `ble.md` (flagged in [README.md](README.md)). Pwnagotchi detection bridges the two. Blue-team framing: [../topics/security-pentest.md](../topics/security-pentest.md).

---

## Open questions / to research
- Confirm exact menu labels + ordering on **my** Marauder build/version (wiki spans many firmware revs).
- Channel Analyzer / Signal Monitor: what exactly is graphed (axes, units, RSSI scale)? **(verify)**
- Does my build persist AP/SSID **lists to SD** between sessions, or RAM-only?
- Which **GPS module** to wire for UC-38 wardriving (chipset, UART pins, antenna) — see [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md).
- Should AirTag/skimmer/BLE detectors get their own `ble.md` rather than living under Wi-Fi UC-54?
- Probe Request Flood: does it pull from the SSID list or only random strings on my firmware?

## Sources
- Marauder wiki home / tool list: https://github.com/justcallmekoko/ESP32Marauder/wiki
- Scan / select: https://github.com/justcallmekoko/ESP32Marauder/wiki/scan-aps · https://github.com/justcallmekoko/ESP32Marauder/wiki/scansta · https://github.com/justcallmekoko/ESP32Marauder/wiki/select-aps
- Sniffers / PCAP: https://github.com/justcallmekoko/ESP32Marauder/wiki/wifi-sniffers · https://github.com/justcallmekoko/ESP32Marauder/wiki/Packet-Monitor · https://github.com/justcallmekoko/ESP32Marauder/wiki/deauth-sniff
- Spam family: https://github.com/justcallmekoko/ESP32Marauder/wiki/Beacon-Spam-Random · https://github.com/justcallmekoko/ESP32Marauder/wiki/Beacon-Spam-List · https://github.com/justcallmekoko/ESP32Marauder/wiki/rick-roll-beacon · https://github.com/justcallmekoko/ESP32Marauder/wiki/attack
- Wardrive / GPS: https://github.com/justcallmekoko/ESP32Marauder/wiki/wardrive · https://github.com/justcallmekoko/ESP32Marauder/wiki/gps-modification · https://github.com/justcallmekoko/ESP32Marauder/wiki/gps-data
