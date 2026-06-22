---
title: BLE Sniffer Add-On (connection capture upgrade)
domain: bluetooth
type: reference
status: detailed
summary: Real BLE connection capture via nRF52840/nRF Sniffer or Sniffle, plus crackle for LE Legacy pairings.
hardware: [nrf52840]
use_cases: [UC-64]
related: [bluetooth/README.md, bluetooth/interception.md, bluetooth/ble-spam.md, bluetooth/airtag-tracker-detection.md, hardware/buying-guide.md]
tags: [ble, sniffer, nrf52840, sniffle, wireshark, crackle, connection-capture, pcap]
last_verified: 2026-06-19
---

# BLE Sniffer Add-On (connection capture upgrade)

> **TL;DR —** To actually capture/follow a BLE connection (not just adverts) you need a dedicated sniffer chip — cheapest is an nRF52840 dongle + nRF Sniffer + Wireshark, best is Sniffle on a TI CC1352. None defeat LE Secure Connections crypto.
> Builds on [interception.md](interception.md) (advertising vs connection layer) · related [ble-spam.md](ble-spam.md) · [airtag-tracker-detection.md](airtag-tracker-detection.md) · hardware [../hardware/buying-guide.md](../hardware/buying-guide.md) · [../hardware/gpio-addons-potential.md](../hardware/gpio-addons-potential.md). Part of the [Bluetooth hub](README.md) · [KB](../README.md).

## TL;DR
My Flipper + ESP32 Marauder do **advertising-layer recon only** ([interception.md §5](interception.md)). To actually **capture/follow a BLE connection** — i.e. ride the 37-data-channel hop sequence after `CONNECT_IND` — I need a **dedicated sniffer chip**. Cheapest real entry: **nRF52840 dongle + Nordic nRF Sniffer + Wireshark** (~$10–20, works on macOS). Best open sniffer: **Sniffle** on a TI CC1352/CC26x2. Want it **standalone on the Flipper** (PCAP to SD, no PC): the community **Flipper-Zero-BLE-Sniffer** add-on driving a Seeed nRF52840 over UART. None of these defeat **LE Secure Connections** crypto — that limit is physics, not hardware ([interception.md §3](interception.md)).

## 1. Why a dedicated add-on is needed
Following a connection means tracking the **Access Address + hop increment/channel-map** agreed in `CONNECT_IND` and re-tuning the radio every connection event across the 37 data channels (see [interception.md §2](interception.md)). The Flipper's STM32WB and the Marauder's ESP32 are **scanners** — slow scan intervals, advertising channels only, no link-layer follow. A purpose-built sniffer firmware (Nordic / Sniffle / Ubertooth) does the hop-following in radio firmware. That's the whole upgrade.

## 2. Hardware options

| Device | Chip | Follows connection? | BLE5 (2M/Coded/ext-adv)? | Relay / MITM? | Classic (BR/EDR)? | ~Cost | Notes |
|---|---|---|---|---|---|---|---|
| **nRF52840 dongle** (Nordic PCA10059 / clone) | nRF52840 | ✅ one connection | Partial — 1M/2M; ext-adv limited _(verify per fw rev)_ | ❌ | ❌ | **~$10–20** | Cheapest real entry. UF2 or nRF Connect Programmer flash. Cheap clones may be **LDO-only** → need the firmware patcher (§3a). |
| **Seeed XIAO nRF52840** | nRF52840 | ✅ one connection | Partial (as above) | ❌ | ❌ | ~$10–15 | Same fw as the dongle; also the board the **Flipper add-on** (§3c) drives over UART. |
| **TI CC2652 / CC1352** (Sonoff CC2652P dongle, TI LAUNCHXL) + **Sniffle** | CC1352P / CC26x2 | ✅ + can **follow without seeing CONNECT_IND** | ✅ full (1M/2M/Coded, CSA#1/#2, ext-adv) | ✅ link-layer **relay** (2 boards) | ❌ | **~$10–50** | **Best open sniffer.** Sonoff dongle = cheapest/no-solder; LAUNCHXL has onboard debugger. |
| **Ubertooth One** | CC2400 + LPC175x | Partial (BLE follow; weaker on BT5) | ❌ (pre-BT5) | ❌ | Some **Classic** monitoring | **~$120** | Older; the classic **crackle** companion. Only board here that touches Classic at all. |

Quick read: **nRF52840 dongle** for cheapest "does it work," **Sniffle/CC1352** for serious BLE5 + relay, **Ubertooth** only if I specifically want Classic or the crackle workflow.

## 3. Setup paths

### (a) nRF52840 dongle + nRF Sniffer for Bluetooth LE + Wireshark (recommended first)
Nordic's free **nRF Sniffer** firmware turns a $10 dongle into a Wireshark capture interface via the **extcap** mechanism. Works on **macOS**.
1. **Flash the firmware** — the dongle does **not** ship with it. Either drag the `.uf2` (hold the button while plugging in → mass-storage bootloader → drop the file) or use **nRF Connect for Desktop → Programmer** to flash the `.hex`.
2. **LDO-only clones:** many cheap clones disable the DC/DC regulator the stock Sniffer fw expects → no packets. Fix with **`danielstuart14/nrfsniffer_patcher`** (patches the fw for LDO-only boards), then flash the patched build _(verify your board needs it before patching)_.
3. **Install the extcap plugin:** `pip3 install -r requirements.txt` in `Sniffer_Software/extcap/`, then copy that folder's contents into Wireshark's **Extcap path** (`Help → About Wireshark → Folders`). Also drop the `Profile_nRF_Sniffer_Bluetooth_LE` folder into the Wireshark profiles dir.
4. **macOS perms:** `chmod +x nrf_sniffer_ble.sh`; verify with `./nrf_sniffer_ble.sh --extcap-interfaces`.
5. Restart Wireshark → the **nRF Sniffer** interface appears. Pick the target from the device dropdown to follow its connection.

### (b) Sniffle on a TI CC1352 / CC26x2
NCC Group's **Sniffle** — the strongest open BLE5 sniffer; can even **sync to a live connection without catching `CONNECT_IND`**, and do a 2-board **link-layer relay**.
1. **Flash firmware:** Sonoff CC2652P dongle → patched **`sultanqasim/cc2538-bsl`** (the stock one has a post-flash reset bug on the Sonoff):
   `python3 cc2538-bsl.py -p /dev/tty.usbserial-XXXX --bootloader-sonoff-usb -ewv sniffle_cc1352p1_cc2652p1.hex`
   LAUNCHXL boards → `make load` in `fw/` (DSLite) or the UniFlash GUI with `sniffle.hex`.
2. **Host (Python 3.9+, PySerial):** capture with `python3 sniff_receiver.py -o capture.pcap`, or wire it to Wireshark via the **`sniffle_extcap.py`** extcap plugin (symlink into `~/.local/lib/wireshark/extcap` on macOS).
3. **Relay (own devices only):** `relay_slave.py` + `relay_master.py` on two boards (the master can request faster connection intervals to cut latency).

### (c) Flipper-Zero-BLE-Sniffer (EvanDebruyne) — standalone, PCAP to SD
A **separate community add-on, NOT the Marauder**: the Flipper drives a **Seeed nRF52840** (flashed with nRF Sniffer fw) over its **UART**, and the `.fap` writes **`ble_capture_*.pcap` straight to the Flipper SD card** — no PC needed to capture.
- **Wiring (115200 baud):** nRF `GND→`Flipper GND, `3.3V→`3.3V, `P0.06→`Flipper **A14 (RX)**, `P0.08→`Flipper **A13 (TX)**.
- **App:** build with `ufbt`/`make`, copy the `.fap` to `/ext/apps/Tools/`, launch from Apps. Controls: **OK** start/stop, **Right** new file, **Left** pause, **Back** exit.
- **Status:** early/in-progress — treat as experimental; pull the PCAP off SD and analyze on the Mac _(verify current state of the repo before relying on it)_.

## 4. Capture → analyze workflow
1. **Identify the target** — scan first (Marauder / nRF Sniffer device list): MAC, name, service UUIDs ([interception.md §5](interception.md)).
2. **Follow the connection** — point the sniffer at that MAC. **Ideally catch the `CONNECT_IND`** (be sniffing *before* the devices connect) so you have the Access Address + hop params from the start; Sniffle can also latch onto an already-running connection.
3. **Open the PCAP in Wireshark** — `btle` dissector decodes the link layer, ATT/GATT, and SMP pairing frames.
4. **Decrypt (only if weak):**
   - **LE Legacy** pairing → if you captured the **pairing exchange**, **crackle** brute-forces the **TK** (range 0–999,999; `Just Works` = TK 0), derives STK/LTK, and decrypts the rest: `crackle -i capture.pcap -o decrypted.pcap` (or `-l <LTK>` if you already know the key).
   - **LE Secure Connections** → ECDH (P-256); a passive sniffer **cannot** derive the key → traffic stays encrypted, full stop ([interception.md §3](interception.md)). This is the modern default, so most real targets won't decrypt.

## 5. macOS (darwin) notes
- **Wireshark:** install the app (`brew install --cask wireshark`); extcap plugins live under `Help → About Wireshark → Folders → Extcap path`.
- **Python/PySerial:** `brew install python`; `pip3 install pyserial`. Sniffle wants **Python 3.9+**.
- **Gotcha:** Wireshark on macOS may invoke **Xcode's Python** instead of your shell's. If PySerial "isn't found," edit the **shebang** in `sniffle_extcap.py` (or `nrf_sniffer_ble.sh`) to point at Homebrew Python, e.g. `/opt/homebrew/bin/python3`.
- **Serial ports** show as `/dev/tty.usbserial-*` or `/dev/tty.usbmodem*`; CP210x/CH340 USB-UART bridges may need a kext/driver on older macOS _(verify on current macOS)_.

## 6. What you gain vs limits — and my recommendation
**Gain:** real **connection following** + PCAP; read **unencrypted GATT** (lots of cheap IoT skips link encryption); decrypt **LE Legacy** pairings with crackle; with Sniffle, BLE5 + relay/MITM on **my own** devices.
**Limits:** still **one connection at a time** (nRF); **LESC traffic stays encrypted**; **Classic** needs Ubertooth and is weak; timing/`CONNECT_IND` capture takes practice; the Flipper standalone add-on (§3c) is experimental.

**Recommendation:**
- **Cheapest first step → nRF52840 dongle** on the Mac (path **a**). ~$10–20, proves the whole pipeline.
- **Want it on the Flipper, no laptop → Flipper-Zero-BLE-Sniffer** add-on (path **c**), accepting it's early-stage.
- **Serious BLE5 / relay later → Sniffle on a CC1352** (path **b**).
- See [../hardware/buying-guide.md](../hardware/buying-guide.md) / [../hardware/gpio-addons-potential.md](../hardware/gpio-addons-potential.md) to slot this next to my current [Marauder](../hardware/gpio-addons-current.md); use-case fit in [../my-use-cases.md](../my-use-cases.md).

## 7. Legality
Capturing/decrypting a connection you aren't a party to can fall under **wiretap/interception** law even when passive — far higher risk than reading public advertising broadcasts. **Own devices or a written-authorization engagement only** ([../legal-and-safety.md](../legal-and-safety.md), [interception.md §8](interception.md)).

## Open questions / to research
- Does the cheap nRF52840 dongle I'd buy use the **DC/DC** path or is it **LDO-only** (i.e. do I need the `nrfsniffer_patcher`)? _(verify per listing)_
- Current state of the **Flipper-Zero-BLE-Sniffer** repo in 2026 — does UART PCAP capture work reliably end-to-end yet? _(verify)_
- Which of my own BLE devices pair **LE Legacy vs LESC** — i.e. what's even theoretically decryptable with crackle.
- Practical hit-rate of catching `CONNECT_IND` vs Sniffle's mid-connection sync on my devices.
- Does any current macOS driver hassle apply to the CP2102/CH340 bridge on the Sonoff dongle? _(verify on this macOS rev)_
- Is a CC1352 relay worth it for me, or overkill vs just the nRF dongle?

## Sources
- Nordic nRF Sniffer for Bluetooth LE (setup/extcap): https://academy.nordicsemi.com/courses/bluetooth-low-energy-fundamentals/lessons/lesson-6-bluetooth-le-sniffer/topic/nrf-sniffer-for-bluetooth-le/ · guide: https://novelbits.io/nordic-ble-sniffer-guide-using-nrf52840-wireshark/
- LDO-only nRF52840 Sniffer fw patcher: https://github.com/danielstuart14/nrfsniffer_patcher
- NCC Group Sniffle (boards, host, relay, macOS shebang, flashing): https://github.com/nccgroup/Sniffle · write-up: https://www.nccgroup.com/research/sniffle-a-sniffer-for-bluetooth-5/
- Patched Sonoff flasher: https://github.com/sultanqasim/cc2538-bsl
- crackle (LE Legacy TK brute-force; LESC limitation): https://github.com/mikeryan/crackle
- Flipper-Zero-BLE-Sniffer (UART wiring, PCAP-to-SD): https://github.com/EvanDebruyne/Flipper-Zero-BLE-Sniffer
- BLE pairing security (Legacy vs LESC): https://academy.nordicsemi.com/courses/bluetooth-low-energy-fundamentals/lessons/lesson-5-bluetooth-le-security-fundamentals/topic/legacy-pairing-vs-le-secure-connections/
