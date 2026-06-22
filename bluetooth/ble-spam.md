---
title: BLE Spam (UC-29)
domain: bluetooth
type: reference
status: detailed
summary: Advertising-flood pairing popups (Sour Apple/Fast Pair/Swift Pair); the iOS 17.2 story; nuisance, not a hack.
hardware: [flipper-internal]
use_cases: [UC-29]
related: [bluetooth/README.md, bluetooth/interception.md, bluetooth/airtag-tracker-detection.md, firmware/momentum.md]
tags: [ble, ble-spam, advertising, sour-apple, fast-pair, swift-pair, ios-17-2, notification-dos]
last_verified: 2026-06-19
---

# BLE Spam (UC-29)

> **TL;DR —** BLE Spam floods crafted advertising packets so nearby phones pop up pairing prompts — an advertising-layer nuisance/notification-DoS with no connection or data theft. Since iOS 17.2 rate-limiting it's largely a party trick on patched devices.
> Built on the same broadcast layer as [interception.md](interception.md) recon · contrast with [airtag-tracker-detection.md](airtag-tracker-detection.md) (detecting real beacons). Part of the [Bluetooth hub](README.md) · [KB](../README.md).

## TL;DR (the honest version)
BLE Spam **floods crafted Bluetooth advertising packets** so nearby phones/PCs pop up pairing or "device nearby" prompts. It abuses the **advertising layer** — the *same* unencrypted broadcast layer that [interception.md](interception.md) §2 uses for scanning — so there is **no connection, no pairing, no data theft**. It's a **notification denial-of-service / nuisance**, nothing more. The Flipper acts as an **advertiser**, not a sniffer. Since vendors added rate-limiting (notably **iOS 17.2**, Dec 2023), it's largely a **party trick** against patched devices.

## 1. What it actually is (mechanics)
- BLE devices announce themselves with **advertising (ADV) packets** on channels **37/38/39** — unencrypted by design (see [interception.md](interception.md) §2). OSes parse certain manufacturer-/service-specific ADV payloads to show "helpful" pairing UI (AirPods popup, "device nearby", Swift Pair card).
- BLE Spam **forges those payloads** and broadcasts them rapidly (intervals down to ~**1 s** or faster, often cycling fake MACs/names). Each forged packet = one popup on every phone in range that trusts that payload type.
- **No handshake happens.** The attacker never connects, never completes pairing, never sees any of the target's data. The "attack surface" is purely the OS's *eager parsing of broadcasts*.
- This is why it's the mirror image of recon: scanning **reads** advertising; spam **writes** advertising. Same layer, opposite direction.

## 2. Variants (what each popup is, and who shows it)
| Variant | OS that pops up | Forged ADV payload | What the user sees |
|---|---|---|---|
| **Apple "Sour Apple"** | iOS / iPadOS | Apple **Continuity** proximity-pairing beacons | AirPods pairing sheet, **Apple TV** pairing, "Setup new device", **"AirTag found moving with you"**, etc. |
| **Android Fast Pair** | Android | Service data UUID **`FE2C`** + device model IDs (e.g. Bose NC 700, Pixel Buds) | "**device nearby**" pairing notification |
| **Microsoft Swift Pair** | Windows 10/11 | Manufacturer data prefix `0006` + `030008…` (+ custom name in hex) | bottom-right **"new Bluetooth device found"** card |
| **Samsung EasySetup** | Samsung (One UI) | Samsung Buds/Watch EasySetup payloads | Galaxy **Buds / Watch** pairing popup |
| **NameFlood** | Android / Windows | many fake *connectable* advertisements | floods the **Bluetooth device list** with junk entries |

"Kitchen Sink" mode cycles all of these at once to hit a mixed crowd. Defaults matter: Fast Pair needs "**scan for nearby devices**" on (default on); Swift Pair needs its notification toggle on (default on Win10+).

## 3. History: the 2023 "Flipper crashes iPhones" story
- **What happened (Oct 2023):** Flipper custom firmware (Xtreme) shipped Apple proximity-pairing spam. On **iOS < 17.2** the relentless ADV flood didn't just annoy — it could **freeze the UI and force-reboot** iPhones/iPads, because iOS parsed the popups with **no rate limit / timeout**.
- **The crash got a CVE:** **CVE-2023-42941** (Apple's tracking of the BLE-pairing DoS).
- **Apple's fix:** **iOS 17.2** (Dec 2023) added safeguards — widely understood as a **rate-limit / ADV-request timeout** on pairing prompts — neutralizing the crash loop. A few popups may still flicker briefly before it clamps down *(exact mechanism never published — verify)*.
- **The honest framing:** this was **advertising spam**, **not** a hack. Nothing was paired, accessed, or exfiltrated; iOS simply mishandled a flood of broadcasts. Headlines saying Flipper "hacks iPhones" were wrong — it was a notification-DoS bug. (Same distinction this KB draws in [interception.md](interception.md): broadcasts ≠ connections.)

## 4. On the rig
| Path | What runs | Notes |
|---|---|---|
| **Flipper built-in BLE** | CFW **BLE Spam** app | ships on **Momentum** (the [target firmware](../firmware/momentum.md)) / ex-Xtreme; Apple/Android/Windows/Samsung + NameFlood |
| **ESP32 Marauder** | BLE spam module | 2.4 GHz; same advertising-flood idea on the [ESP32 add-on](../hardware/gpio-addons-current.md) |
| **ESP32 Bruce / standalone** | "Sour Apple" / AppleJuice forks | community PoCs (ECTO-1A AppleJuice, RapierXbox Sour Apple) |

- All of this is **2.4 GHz BLE**, *not* the **433 MHz CC1101** (that's Sub-GHz — different radio entirely).
- The Flipper here is purely an **advertiser**. It does **not** sniff, follow, or decrypt anything — consistent with [interception.md](interception.md) §5 ("recon + nuisance, not interception").
- Maps to **UC-29** in [../my-use-cases.md](../my-use-cases.md); see [../firmware/momentum.md](../firmware/momentum.md) for the app entry.

## 5. What it IS vs ISN'T
| It IS | It ISN'T |
|---|---|
| an **annoyance / notification-DoS** | a pairing or connection |
| forged **public broadcasts** | data theft / account compromise |
| capable of disrupting/annoying nearby users | capable of "taking over" or installing anything |
| (pre-patch) able to **crash unpatched iOS** | a remote exploit on patched OSes — popups don't auto-connect or run code |

The popups are **inert prompts**: dismiss them and nothing happened. The only real harm was the *legacy* iOS crash bug, now patched.

## 6. Defenses (blue-team)
- **Update the OS.** iOS ≥ 17.2 and current Android/Windows builds **rate-limit** pairing prompts — the crash and most of the spam volume are gone.
- **Disable "nearby device" suggestions:** Android → turn off **"Scan for nearby devices" / Fast Pair**; Windows → off **"Show notifications to connect using Swift Pair"**; iOS → these prompts are throttled OS-side.
- **In a crowd / con, just turn Bluetooth off** (or use Airplane mode) — zero ADV parsing = zero popups.
- Detection: Android apps (e.g. "Wall of Flippers" / BLE-spam detectors) flag the burst of spoofed pairing ADVs; conceptually the inverse of [airtag-tracker-detection.md](airtag-tracker-detection.md), which watches for *real* trackers in the same advertising stream.

## 7. Legality (rated High)
Blasting pairing popups at **other people's** phones is **harassment / interference with their devices** — a nuisance you are deliberately inflicting, and (pre-patch) one that could crash them. That can run afoul of computer-misuse / harassment statutes regardless of "it's just a popup." Run it **only against your own devices or in an RF-isolated lab** ([../legal-and-safety.md](../legal-and-safety.md)). This doc explains **mechanics and defenses**, not how to grief a room.

## Open questions / to research
- Does **Momentum**'s current BLE Spam build still meaningfully affect any **patched** mainstream OS, or is it now purely NameFlood/legacy-device noise? *(verify on my own devices)*
- Exact iOS 17.2 mitigation internals — confirmed rate-limit vs ADV-timeout vs payload validation *(Apple never published — verify)*.
- Marauder vs Flipper built-in: which advertises **faster / more payload types** on my rig?
- Can my Android phone *detect* a spam burst (Wall of Flippers-style), tying this back to [airtag-tracker-detection.md](airtag-tracker-detection.md)?
- Any 2024–2026 follow-up CVEs for Fast Pair / Swift Pair flooding? *(verify)*

## Sources
- CVE-2023-42941 writeup (mechanism, AirDrop/Handoff/Watch ADV spoof, iOS 17.2 timeout): https://ecto-1a.github.io/AppleJuice_CVE/
- 9to5Mac — iOS 17.2 stops the crash (Dec 15 2023; popups still flicker): https://9to5mac.com/2023/12/15/the-jig-is-up-flipper-zero-devices-can-no-longer-crash-iphones-running-ios-17-2/
- Mobile Hacker — variant payloads (Apple/Fast Pair FE2C/Swift Pair 0006/Samsung, intervals, advertising-only): https://www.mobile-hacker.com/2023/10/17/spam-ios-android-and-windows-with-bluetooth-pairing-messages-using-flipper-zero-or-android-smartphone/
- WillyJL — "The controversy behind Apple BLE Spam" (app history, Continuity/FastPair/SwiftPair/EasySetup/NameFlood, firmwares, "not data theft"): https://willyjl.dev/blog/the-controversy-behind-apple-ble-spam
- BleepingComputer — spam ported to Android/Windows: https://www.bleepingcomputer.com/news/security/flipper-zero-can-now-spam-android-windows-users-with-bluetooth-alerts/
- Momentum Firmware (ships BLE Spam): https://github.com/Next-Flip/Momentum-Firmware · AppleJuice PoC: https://github.com/ECTO-1A/AppleJuice
- Detection (Wall of Flippers / BLE-spam detect): https://www.mobile-hacker.com/2024/01/09/how-to-detect-flipper-zero-and-bluetooth-advertisement-attacks/
