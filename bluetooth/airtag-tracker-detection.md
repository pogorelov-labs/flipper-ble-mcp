---
title: AirTag / Tracker Detection (UC-40) + FindMy Flipper (UC-30)
domain: bluetooth
type: reference
status: detailed
summary: How Find My works, anti-stalking tracker detection, rig limits, and FindMy Flipper as the inverse emulator.
hardware: [flipper-internal, esp32-marauder]
use_cases: [UC-40, UC-30]
related: [bluetooth/README.md, bluetooth/interception.md, bluetooth/ble-spam.md, bluetooth/ble-sniffer-addon.md, topics/security-pentest.md]
tags: [ble, airtag, find-my, tracker-detection, anti-stalking, dult, findmy-flipper]
last_verified: 2026-06-19
---

# AirTag / Tracker Detection (UC-40) + FindMy Flipper (UC-30)

> **TL;DR —** Detecting unwanted trackers (AirTag/SmartTag/Tile) is advertising-layer recon turned defensive — the rig can see beacons but OS-native DULT detectors win on "is it following me." FindMy Flipper (UC-30) is the inverse: broadcast the Flipper as a Find My tag.
> Builds on [interception.md](interception.md) §5 (advertising scan); rig [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md) · CFW apps [../firmware/momentum.md](../firmware/momentum.md) · [legal](../legal-and-safety.md). Part of the [Bluetooth hub](README.md) · [KB](../README.md).

## TL;DR
Tracker detection is **advertising-layer recon turned defensive**: every tracker (AirTag, SmartTag, Tile, Chipolo) gives itself away by **broadcasting BLE advertisements**, so any BLE radio — Flipper + [Marauder](../hardware/gpio-addons-current.md) — can *see* them. The hard part isn't seeing one; it's deciding a tracker is **following you** despite **MAC/key rotation** designed to stop exactly that linkage. **The OS-native detectors (iOS/Android, built on the Apple-Google DULT spec) are better at this than my rig** — they have motion, time, and the manufacturer crypto. Treat the Flipper/Marauder as a **supplementary, educational scanner**, not your primary anti-stalking tool. **FindMy Flipper (UC-30)** is the inverse: make the Flipper *advertise as* a Find My tag so I can locate it if lost.

## 1. How Find My / crowdsourced trackers work
**Apple Find My** is an offline-finding network: the ~billion+ Apple devices in the wild act as anonymous "finders."

1. An AirTag (or any Find My accessory) broadcasts **BLE advertisements** carrying a **rotating public key** — no GPS, no cellular, no connection. It's a dumb beacon.
2. Any nearby iPhone/iPad/Mac hears it, grabs **its own** location, **encrypts that location with the tag's public key**, and uploads the encrypted report + a hash of the key to Apple.
3. Apple stores **encrypted blobs it cannot read**. The finder never learns it helped.
4. The **owner** — who alone holds the matching **private key** — queries Apple by key-hash and **decrypts** the location locally.

The privacy model is genuinely strong **for the owner and the finder**: rotating keys mean Apple can't link reports to an identity, and only the owner's private key decrypts. The flip side is the stalking problem (§2) — the same silent beacon works whether it's in *your* bag or a victim's. Google's **Find Hub** (formerly Find My Device, re-launched 2024 with a crowdsourced network) mirrors the architecture on Android.

| Ecosystem | Network | Crowdsource device base | Key rotation model |
|---|---|---|---|
| **Apple AirTag / Find My** | Find My offline-finding | iPhone/iPad/Mac (huge) | rotating P-224 public key; **24 h** when separated |
| **Samsung SmartTag / Galaxy Find** | Galaxy Find Network | Samsung Galaxy phones (regional) | randomized MAC + optional location encryption (verify cadence) |
| **Tile** | Tile network | Tile-app phones (smaller) | **largely static** identifiers — see §3 |
| **Chipolo / Pebblebee / Eufy** | ride on **Apple Find My and/or Google Find Hub** | host network's device base | inherit host-network rotation |

## 2. The stalking problem and the industry response
A $30 coin-sized beacon with months of battery, slipped into a bag or car, turns a *find-my-keys* product into a covert tracker. This drove a rare **Apple + Google joint effort**:

- **Apple "Item Found Moving With You" / unknown-tracker alerts** — iOS surfaces an unknown Find My accessory that has been **separated from its owner and traveling with you**, with map, sound-trigger, and serial/disable instructions. (Standalone **Tracker Detect** app exists for Android, but it's manual-scan only.)
- **Google "unknown tracker alerts" (2024)** — built into Android (6.0+), now **cross-brand**: alerts on AirTag, SmartTag, Tile, Chipolo, Eufy, Pebblebee, not just Google's own.
- **DULT — Detecting Unwanted Location Trackers** — the Apple+Google spec (authors Ledvina et al., June/Oct 2024) submitted to the **IETF DULT working group**. It standardizes (a) how a *separated* accessory advertises so any phone can recognize it as a tracker, and (b) the **interaction protocol** (sound, identify-owner, disable guidance) a phone offers once it flags one. The goal: **interoperable detection regardless of brand**, so an Android user is warned about an AirTag and vice-versa.

Caveat worth knowing: **anti-theft / hidden modes** undercut this — Tile's "Anti-Theft Mode" deliberately makes a tracker **invisible to scan-based detection** (Tile gates it behind ID verification + a stalking penalty, but the capability exists). A determined stalker also picks the tracker whose host network is *least* common on the victim's phone OS.

## 3. How detection works (the BLE side)
You're scanning **advertising** (channels 37/38/39, unencrypted — see [interception.md](interception.md) §2) for tracker **signatures**, then reasoning over **time + movement**.

**Apple AirTag advertisement (registered, separated)** — the signal a detector keys on:

| Field | Value | Meaning |
|---|---|---|
| AD type | `0xFF` | Manufacturer Specific Data |
| Company ID | `0x004C` | **Apple** |
| Payload type | `0x12` | **Find My** network packet (unregistered/setup uses `0x07`) |
| Status byte | `0x10` etc. | flags incl. **maintained vs separated** state |
| Public key | ~23 bytes | rotating **P-224** ECC key (changes daily) |
| Counter | last byte | increments ~every **15 min** |

Key behaviours that make detection *possible*:
- **Near owner:** an AirTag is essentially **silent** (it lets the owner's device hold it); it only advertises loudly when **separated**, at ~**2 s** intervals (`ADV_IND`, random-static address).
- **Separated → the tell:** the very state that triggers crowdsourcing is the state a detector can *see*. A tag that's **separated AND persists AND moves with you** over time = candidate stalker.
- **Unregistered/setup** tags advertise far faster (~33 ms) with type `0x07` — easy to spot but not yet a Find My tracker.

Key behaviours that make detection **imperfect** (the limiter):
- **MAC + key rotation.** A separated AirTag rotates **both its BLE address and public key once per day (≈04:00 local)** — so a naive "same MAC seen for hours" heuristic **breaks across the daily boundary**, and you can't trivially prove yesterday's tag is today's. (Within a day it's stable, which is the privacy trade-off researchers flag.)
- **Sound is slow.** Apple's separated-tag **sound alert is delayed (≈ up to 24 h, and in current firmware only after motion, in short bursts every several hours)** — so "wait for it to chirp" is unreliable.
- **No crypto for you.** You see the *public* key and state flags; you **cannot** identify the owner or decrypt anything. Only Apple's/Google's first-party flow can offer "play sound / show owner / disable."
- **Tile is the asymmetric case:** Tile advertises **largely static identifiers** and historically did **not** randomize its MAC in lost/connected states — *easier* to track persistently, but its anti-stalking relies on an **app-based scan** (opt-in), so passive detection of a Tile is on you.

## 4. On the rig — what the Marauder/Flipper actually do
| Tool / feature | Where | What it shows | Limit |
|---|---|---|---|
| **Marauder "AirTag Monitor"** | `Bluetooth > Sniffers > Airtag Monitor` | lists detected Find My / AirTag-type advertisers (MAC, RSSI, payload) | snapshot list; scan cadence too slow for burst capture; no time-series "is it following me" logic |
| **Marauder BLE scan** | Sniffers | all BLE advertisers (MAC/name/RSSI/UUID/mfr-data) — filter for `0x004C` + type `0x12` manually | passive discovery only ([interception.md](interception.md) §4) |
| **Flipper BLE (STM32WB)** | built-in | **broadcast detection only** | can't follow/decrypt; community detector apps are thin |
| **Community Flipper apps** | CFW catalog | various "AirTag scanner" GPIO/BLE apps | quality varies; mostly re-surface advertising data |

**Honest verdict:** the rig is great for *seeing* the BLE layer and learning the packet format, and fine for a one-off **sweep** of a space (rental car, hotel room). But for "is a tracker stalking *me* over a day," the **OS-native detectors win** — they fuse the manufacturer crypto, persistent motion, and the daily-rotation handling that a passive scanner can't replicate. Use the rig to *understand* and *augment*, not to replace the phone alert. (More attack/defense framing in [../topics/security-pentest.md](../topics/security-pentest.md).)

## 5. FindMy Flipper (UC-30) — the inverse
**Goal:** make the Flipper **broadcast as a Find My tag** so I can locate a lost Flipper via Apple's (or Samsung/Tile's) network — OpenHaystack-style.

- **App:** `FindMyFlipper` (MatthewKuKanich) runs on the Flipper's **built-in BLE** — no extra hardware. Supports emulating **AirTag, Samsung SmartTag, or Tile** by broadcasting the right beacon. Adjustable **beacon interval** and **transmit power** (range vs battery).
- **Two key-provisioning paths:**
  - **Clone** an existing tag's MAC + payload (scan with nRF Connect / an ESP32) — but the **original must stay powered off**, because it will eventually **rotate its keys** and orphan the clone.
  - **Generate fresh OpenHaystack keys** via a Docker server that produces the keypair (the classic OpenHaystack flow historically needed a macOS Mail plug-in / older macOS to *pull* reports — verify current tooling on my Mac).
- **CFW:** README states recent builds work across firmwares (incl. icons); fits Momentum's app catalog ([../firmware/momentum.md](../firmware/momentum.md)).
- It's an **emulator, not a detector** — UC-30 (be findable) is orthogonal to UC-40 (find others). Same BLE radio, opposite direction.

## 6. Defenses / legitimate use (blue-team)
- **Trust the OS first.** Keep iOS/Android updated; the built-in unknown-tracker alerts are the strongest layer and are now cross-brand via DULT.
- **Manual sweep when alerts can't help** (e.g., you have iOS but the tracker rides a network your phone scans poorly): Apple **Tracker Detect** (Android) / Android's built-in scan, **plus** the Flipper/Marauder as a *supplementary* RF check for any persistent `0x004C`/`0x12` advertiser or static Tile ID.
- **Physical check** of bags/car/jacket — many trackers are found by hand once an alert says "something's here."
- **Builder side** (if I ship a BLE accessory): follow DULT separated-advertising rules so my device is *detectable* by design — don't be the next stalking vector. (See also [ble-spam.md](ble-spam.md) for the offensive-advertising cousin and [ble-sniffer-addon.md](ble-sniffer-addon.md) if I add a real sniffer.)

## 7. Legality
**Detecting trackers is defensive and lawful** — you're scanning **public advertising broadcasts** in your own space to find out if *you* are being tracked (lowest-risk activity on the rig; same footing as the advertising scan in [interception.md](interception.md) §8). The illegal act is the **inverse**: planting a tracker to follow a person without consent — **stalking/harassment**, and in many places a specific crime. **FindMy Flipper is for finding *my own* lost Flipper**, not for tagging anyone or anything that isn't mine. Own devices / authorized sweeps only ([../legal-and-safety.md](../legal-and-safety.md), [../my-use-cases.md](../my-use-cases.md)).

## Open questions / to research
- Does my Marauder "AirTag Monitor" build expose enough (state byte, time-series) to *meaningfully* flag a moving-with-me tracker, or is it just a live list?
- Current OpenHaystack report-retrieval path on **macOS 15+** without the old Mail plug-in — is there a maintained alternative? _(verify)_
- Exact DULT "separated" advertising flags vs Apple's legacy `0x12`/status-byte scheme — has the IETF draft changed the on-air format manufacturers emit? _(verify)_
- Samsung SmartTag 2 rotation cadence + whether its anti-stalking is now OS-level or still app-gated _(verify)_.
- Can a CFW app correlate AirTag advertisements **across** the daily 04:00 key rotation (e.g., via RSSI/timing) the way research tools attempt?
- Whether **UWB** (AirTag/SmartTag 2 precision finding) is at all visible to my rig (almost certainly not — no UWB radio) _(verify)_.

## Sources
- Apple Find My crowdsourcing + rotating keys: https://airpinpoint.com/tech/how-find-my-network-works · https://cc-sw.com/find-my-and-find-hub-network-research/
- AirTag BLE payload / state / rotation (reverse-engineering): https://adamcatley.com/AirTag.html · https://thebinaryhick.blog/2026/03/22/old-dog-new-tricks-lost-apples-2-0/
- DULT spec / IETF WG: https://datatracker.ietf.org/doc/draft-ledvina-apple-google-unwanted-trackers/ · https://datatracker.ietf.org/doc/html/draft-ietf-dult-accessory-protocol-00 · https://datatracker.ietf.org/wg/dult/about/
- Unwanted-tracking alerts (cross-brand, May 2024): https://www.androidpolice.com/i-want-trust-google-find-hub-but-these-tracking-issues-must-be-fixed/
- Tracker comparison + Tile static-ID / anti-theft analysis: https://arxiv.org/html/2501.17452v1 · https://arxiv.org/html/2510.00350v1
- AirGuard (Android tracker-detection research): https://arxiv.org/pdf/2202.11813
- Marauder AirTag Monitor: https://github.com/justcallmekoko/ESP32Marauder/wiki/Airtag-Monitor
- FindMy Flipper (UC-30): https://github.com/MatthewKuKanich/FindMyFlipper · https://github.com/MatthewKuKanich/FindMyFlipper/blob/main/README.md
