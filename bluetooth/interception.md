---
title: Bluetooth Interception — Reality vs Hype (UC-39)
domain: bluetooth
type: reference
status: detailed
summary: Interception reality — advertising vs connection sniffing, pairing crypto, and what this rig can/can't do.
hardware: [esp32-marauder]
use_cases: [UC-39, UC-40, UC-41, UC-29, UC-30]
related: [bluetooth/README.md, bluetooth/ble-sniffer-addon.md, bluetooth/ble-spam.md, bluetooth/airtag-tracker-detection.md, bluetooth/classic.md]
tags: [ble, interception, sniffing, advertising, pairing, crackle, le-secure-connections]
last_verified: 2026-06-19
---

# Bluetooth Interception — Reality vs Hype (UC-39)

> **TL;DR —** What "intercepting Bluetooth" actually requires (sniff adverts vs follow a connection vs decrypt it) and what this rig can and can't do. Flipper + ESP32 Marauder are advertising-layer recon + spam, not connection interception.
> Rig BLE: Flipper built-in + [Marauder](../hardware/gpio-addons-current.md) · use-cases [../my-use-cases.md](../my-use-cases.md) · [legal](../legal-and-safety.md). Part of the [Bluetooth hub](README.md) · [KB](../README.md).

## TL;DR (the honest version)
"Intercepting Bluetooth" is three different problems stacked on top of each other:
1. **Sniff advertising** (broadcasts) — **trivial**; my rig does this.
2. **Follow a connection** (the actual data) — **hard**; needs a dedicated sniffer, *not* my rig.
3. **Decrypt it** — only feasible against **old/weak pairing**; **modern (LE Secure Connections) traffic can't be passively decrypted at all.**

**My Flipper + ESP32 Marauder = advertising-layer recon + spam, NOT connection interception.** Anything implying "spy on any Bluetooth device" is wrong for this rig — and mostly wrong for modern devices regardless of hardware.

## 1. BLE vs Bluetooth Classic
| | Bluetooth Classic (BR/EDR) | Bluetooth LE |
|---|---|---|
| Use | audio, file transfer, legacy | sensors, wearables, beacons, AirTags, locks |
| Channels (2.4 GHz) | 79 (1 MHz) | **40** (2 MHz): 3 advertising + 37 data |
| Hopping | 1600 hops/s (hard to follow) | per-connection-event hop |
| Interception | very hard (Ubertooth; KNOB/BIAS downgrade attacks) | the focus below |

Most "Bluetooth interception" interest is **BLE**, so that's the focus.

## 2. The two layers of BLE traffic
- **Advertising** — broadcast on channels **37/38/39**, unencrypted, by design. Carries device discovery, beacons, AirTag/tracker data, manufacturer data. **Any BLE radio can read this** — this is "interception" at the *discovery* layer (and it's what AirTag/skimmer detection uses).
- **Connection data** — after the `CONNECT_IND`, the two devices **frequency-hop across the 37 data channels**, a new channel each connection event, using an **Access Address + hop parameters** agreed at connect time. To capture this you must **follow the hop sequence** — that's the hard part, and what separates a real sniffer from a scanner.

## 3. Even if you capture a connection — can you read it? (the crypto)
- **Unencrypted** (many cheap IoT skip link encryption): readable once you follow the hops.
- **Encrypted** — depends on how the devices *paired*:
  - **LE Legacy pairing** (BT 4.0/4.1): security rests on a **Temporary Key (TK)** — `Just Works` sets **TK = 0**; `Passkey` is a **6-digit** value (0–999,999). If you captured the **pairing exchange**, **crackle** (Mike Ryan) brute-forces the TK → derives the STK/LTK → **decrypts everything afterward**. Weak.
  - **LE Secure Connections** (BT **4.2+**): uses **ECDH (P-256)** key agreement — a passive eavesdropper **cannot** derive the key. **Not decryptable by sniffing.** This is the modern default.
- So passive decryption is realistic **only** against **LE Legacy** devices where you catch the **pairing** (or it's `Just Works`). Catch a **LESC** connection mid-stream → encrypted blobs you can't read.
- *Classic:* **KNOB** (force low key entropy) and **BIAS** (impersonation) are separate attack classes needing specific conditions/hardware _(verify applicability)_.

## 4. Hardware reality — what actually sniffs connections
| Tool | What it does | ~Cost |
|---|---|---|
| **nRF52840 dongle** + nRF Sniffer + Wireshark | best cheap **real** BLE sniffer; follows one connection | ~$10 |
| **Sniffle** on TI **CC1352/CC26x2** | excellent BLE5 sniffer + link-layer **relay** | ~$30–50 |
| **Ubertooth One** | older; BLE + some Classic monitoring; **crackle** built on it | ~$120 |
| **bluesniff** (HackRF) | can **sync to a live connection** without seeing CONNECT_IND | (SDR) |
| **Flipper built-in BLE** | **advertising scan only** — no connect/sniff/inject | — |
| **ESP32 Marauder** | Classic+BLE **device scan**, spam, Flipper-detect, AirTag-detect | (have it) |

## 5. What MY rig can and can't do
**CAN (advertising layer):**
- Scan BLE/Classic devices — MAC, name, RSSI, service UUIDs, manufacturer data ([UC-39](../my-use-cases.md)).
- Detect beacons, **AirTags/trackers** ([UC-40](../my-use-cases.md)), **Bluetooth card skimmers** ([UC-41](../my-use-cases.md)).
- **BLE Spam** ([UC-29](../firmware/momentum.md)), **FindMy Flipper** ([UC-30](../firmware/momentum.md)), detect other Flippers.

**CANNOT:**
- Follow/sniff an **established connection**, **decrypt** encrypted GATT, **MITM** a pairing, or **inject** into a connection.
- The Flipper BLE is *broadcast detection only*; the Marauder is "passive discovery + spam," **not** packet-level interception (its scan intervals are too slow for burst advertising capture, let alone hop-following).

**Verdict:** on Bluetooth my rig is a **recon + nuisance** tool, not an interception tool.

## 6. Upgrade path (if I actually want connection sniffing)
- Add an **nRF52840** (Seeed XIAO / dongle). There's a community **Flipper-Zero-BLE-Sniffer** (EvanDebruyne) that drives an nRF52840 from the Flipper and saves **PCAP to SD** — or just run the dongle on a PC with **Wireshark + nRF Sniffer**.
- For BLE5 / relay / long-lived connections → **Sniffle** on a CC26x2.
- Then: read unencrypted GATT, or **crackle** a captured LE-Legacy pairing. Modern LESC traffic stays unreadable.

## 7. Defenses (blue-team)
- Require **LE Secure Connections** + a MITM-resistant method (**Passkey / Numeric Comparison / OOB**); avoid `Just Works` for anything sensitive.
- Add **application-layer encryption** on top of BLE (don't trust link security alone).
- Use **Resolvable Private Addresses** (rotating MAC) to resist tracking — but don't leak static IDs in manufacturer data.
- Minimize sensitive data in **advertising**.

## 8. Legality (rated High)
Intercepting communications you aren't party to falls under **wiretap/interception** laws in many places — even passively. Scanning **public advertising broadcasts** is lower-risk; **decrypting someone's connection is not**. Your own devices or an authorized engagement only ([../legal-and-safety.md](../legal-and-safety.md)).

## Open questions / to research
- Does my Marauder build expose a usable raw BLE-advertising capture (PCAP) or only the device list?
- Cheapest practical real-sniffer add-on for me (nRF52840 dongle on the Mac vs a Flipper BLE-sniffer module).
- Which of my own BLE devices use LE Legacy vs LESC (test what's even theoretically sniffable).
- Current state of crackle vs modern stacks (LE Legacy is rarer in 2026) _(verify)_.

## Sources
- BLE sniffing fundamentals: https://academy.nordicsemi.com/courses/bluetooth-low-energy-fundamentals/lessons/lesson-6-bluetooth-le-sniffer/ · https://novelbits.io/bluetooth-low-energy-ble-sniffer-tutorial/
- Sniffle: https://github.com/nccgroup/Sniffle · bluesniff/HackRF: https://blog.lexfo.fr/sniffing-ble-sdr.html
- Pairing security (Legacy vs LESC): https://academy.nordicsemi.com/courses/bluetooth-low-energy-fundamentals/lessons/lesson-5-bluetooth-le-security-fundamentals/topic/legacy-pairing-vs-le-secure-connections/ · crackle: https://github.com/mikeryan/crackle
- Flipper BLE limits: https://www.serverman.co.uk/hardware/flipper-zero/flipper-zero-bluetooth/ · Marauder BT: https://github.com/justcallmekoko/ESP32Marauder/wiki/bluetooth-sniffer
- Flipper BLE sniffer (nRF52840): https://github.com/EvanDebruyne/Flipper-Zero-BLE-Sniffer
