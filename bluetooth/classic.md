---
title: Bluetooth Classic (BR/EDR) — KNOB, BIAS & rig limits
domain: bluetooth
type: reference
status: detailed
summary: Bluetooth Classic (BR/EDR) attacks — KNOB, BIAS, BlueBorne — and why this rig can't touch them.
hardware: [esp32-marauder]
use_cases: []
related: [bluetooth/README.md, bluetooth/interception.md, bluetooth/ble-spam.md, bluetooth/ble-sniffer-addon.md, theory/relay-attacks.md]
tags: [bluetooth-classic, br-edr, knob, bias, blueborne, ubertooth, threat-model]
last_verified: 2026-06-19
---

# Bluetooth Classic (BR/EDR) — KNOB, BIAS & rig limits

> **TL;DR —** Bluetooth Classic (BR/EDR) attacks KNOB, BIAS, and BlueBorne are real and spec-level, but out of reach for this rig — the Flipper has no Classic radio and the Marauder can only scan/list Classic devices. A "know the threat" doc, not a capability.
> BLE side: [interception.md](interception.md) · spam [ble-spam.md](ble-spam.md) · relay [../theory/relay-attacks.md](../theory/relay-attacks.md). Part of the [Bluetooth hub](README.md) · [KB](../README.md).

## TL;DR (the honest version)
Bluetooth **Classic** (BR/EDR) is the audio/file-transfer side of Bluetooth, and the famous attacks against it — **KNOB** and **BIAS** — are real, spec-level, and devastating *on paper*. But two things make this a **"know the threat" doc, not a capability** for me:
1. **The Flipper's radio is BLE-only** (STM32WB) — it has **no Classic/BR/EDR radio at all**. It cannot scan, sniff, or attack Classic.
2. The **ESP32 Marauder can SCAN and list Classic devices** (name / MAC / class / RSSI) but **cannot follow, sniff, or attack a Classic connection.** It's a discovery tool, not a baseband sniffer.
3. KNOB/BIAS attacks need a device that can **inject/impersonate at the baseband (LMP) layer** during connection setup — that's **Ubertooth-class custom firmware territory**, not Marauder, not Flipper.

So Classic attacks are **out of reach for this rig**. This doc is for understanding the threat model (and defending my own devices), not for doing it.

## 1. Classic (BR/EDR) vs BLE — quick recap
| | Bluetooth Classic (BR/EDR) | Bluetooth LE |
|---|---|---|
| Used for | audio (A2DP/HFP), file transfer, keyboards/mice, legacy serial | sensors, wearables, beacons, trackers, locks |
| Channels (2.4 GHz) | **79** × 1 MHz | 40 × 2 MHz (3 adv + 37 data) |
| Hopping | **~1600 hops/s**, adaptive (AFH) — fast, hard to follow | per-connection-event hop |
| Pairing | **SSP** (Secure Simple Pairing, BT 2.1+); older **legacy PIN** pairing; **Secure Connections** added BT 4.1/4.2 | LE Legacy vs LE Secure Connections (see [interception.md](interception.md) §3) |
| Sniffing difficulty | **very hard** — fast adaptive hop + 79 channels needs dedicated HW (Ubertooth) | hard, but cheap nRF52840/Sniffle do it |

Why Classic is harder to sniff than BLE: **1600 hops/s across 79 adaptive channels**, no fixed advertising channels to lock onto, and the hop sequence is derived from the master's clock+address. A passive listener has to reconstruct that — which is why Classic sniffing is **Ubertooth-class hardware**, not a USB BLE dongle. (BLE, by contrast, advertises openly on 3 fixed channels — that's the whole reason advertising recon is trivial there.)

## 2. KNOB — Key Negotiation Of Bluetooth (CVE-2019-9506)
**Antonioli, Tippenhauer & Rasmussen, USENIX Security 2019.** A flaw in the **spec itself**, not one vendor.

| Aspect | Detail |
|---|---|
| Core idea | During link setup, BR/EDR devices **negotiate encryption-key entropy** (1–16 bytes). The negotiation is **not integrity-protected** and happens *before* encryption. |
| The attack | A MITM in radio range silently **forces the negotiated entropy down to 1 byte (8 bits)** — neither victim is told. |
| Payoff | A 1-byte key is **brute-forceable in real time** → attacker decrypts the eavesdropped ciphertext and can **inject valid encrypted messages**. |
| Scope | Affects spec versions **1.0 → 5.1**; the team tested **14+ chips** (Broadcom, Qualcomm, Apple, Intel…) — **all vulnerable**. |
| Stealth | Victims get **no notification** of the reduced key size. |
| Fix | Bluetooth SIG **Erratum 11838**: enforce **minimum encryption key length ≥ 7 octets** for BR/EDR; controllers must implement *Read Encryption Key Size*. Patched OSes/stacks reject short keys. |

**KNOB also has a BLE variant** (the BLE key-length negotiation is similarly downgradeable) — but on BLE the modern **LE Secure Connections / app-layer crypto** blunts it, and again my rig can't perform the MITM regardless.

## 3. BIAS — Bluetooth Impersonation AttackS (2020)
**Antonioli, Tippenhauer & Rasmussen, IEEE S&P 2020.** Tracked as **VU#647177 / CVE-2020-10135**.

| Aspect | Detail |
|---|---|
| Core idea | Abuse the **reconnection / re-authentication** of an already-paired pair. The attacker **impersonates a previously-paired device** without knowing the long-term key. |
| Levers | (a) **No mandatory mutual authentication** in legacy auth — only one side need prove the key; (b) **overly permissive master/slave role switch** lets the attacker pick the role that *isn't* challenged; (c) **authentication-procedure downgrade** (Secure Connections → legacy). |
| Result | Attacker completes connection setup posing as the trusted peer — e.g. impersonate your headset to your phone, or vice-versa. |
| Chaining | Frequently **chained with KNOB**: BIAS gets you authenticated-as-the-peer, KNOB drops the key to 1 byte → full break of a "secured" link. |
| Scope | **Standard-compliant** → any compliant device, any version, any vendor; tested on **31 devices / 28 chips** (Apple, Qualcomm, Intel, Cypress, Broadcom, Samsung, CSR). |
| Fix | SIG updates: **require mutual authentication in legacy auth**, constrain when **role switches** are allowed, and check encryption type to block the **SC→legacy downgrade**. **Secure Connections (Only) mode blocks the legacy-auth path entirely.** |

## 4. BlueBorne (Armis, 2017) — historical
**8 vulnerabilities** across Windows, Linux/BlueZ, Android, iOS — an *implementation* attack set (memory corruption / logic flaws in stacks), **not** a spec/crypto flaw like KNOB/BIAS. Notable because it needed **no pairing and no discoverable mode** — airborne RCE/info-leak just from BT being on.

| CVE | Platform | Type |
|---|---|---|
| CVE-2017-1000251 | Linux kernel (BlueZ) | RCE |
| CVE-2017-1000250 | Linux (BlueZ) | Info leak |
| CVE-2017-0781 / -0782 | Android | RCE |
| CVE-2017-0785 | Android | Info leak |
| CVE-2017-0783 | Android | MITM ("Bluetooth Pineapple") |
| CVE-2017-8628 | Windows | MITM ("Bluetooth Pineapple") |
| CVE-2017-14315 | iOS (LEAP audio) | RCE |

**Status: historical / mostly patched** since 2017 (Google AOSP, Microsoft, Apple, Linux all shipped fixes). Listed here for completeness — relevant only against **long-unpatched** devices, and **not something this rig can launch** anyway (no Classic radio + no exploit framework).

## 5. Sniffing / MITM of Classic — the hardware reality
| Tool | Classic capability | Notes |
|---|---|---|
| **Ubertooth One** | partial BR/EDR **monitoring**; basis for **crackle** | the de-facto cheap Classic-ish sniffer; still not turnkey full-traffic capture |
| Dedicated baseband sniffers (Ellisys, Frontline/Teledyne) | full BR/EDR capture | lab gear, $$$$ |
| SDR (HackRF + custom DSP) | research-grade; very involved | not practical for casual use |
| **nRF52840 / Sniffle** | **BLE only** | great for BLE (see [interception.md](interception.md) §4/§6), **no Classic** |
| **Flipper built-in BLE** | **none** — BLE-only radio | cannot touch Classic at all |
| **ESP32 Marauder** | **scan/list only** (name, MAC, class, RSSI) | passive **discovery**; cannot follow/sniff/attack a Classic connection |

Bottom line: Classic interception/MITM is **not turnkey on any cheap device** — and KNOB/BIAS specifically require **active LMP-layer injection during connection setup**, which is custom-baseband-firmware work, well beyond Marauder or Flipper.

## 6. On the rig (honest) — what I can and can't do
**CAN:**
- **ESP32 Marauder:** *scan and list* nearby **Classic** devices — **name, MAC, device class, RSSI** (same scanner that does Card-Skimmer detection). Pure passive discovery.

**CANNOT (everything that matters for an attack):**
- **Flipper:** anything Classic — its radio is **BLE-only (STM32WB)**. No Classic scan, sniff, or attack.
- **Marauder:** follow a Classic hop sequence, sniff connection data, run **KNOB** (no LMP entropy injection), run **BIAS** (no impersonation/role-switch injection), or fire **BlueBorne** exploits.
- Neither device performs the **active baseband MITM** that KNOB/BIAS need.

**Verdict:** on Bluetooth Classic, this rig is at most a **device-list scanner**. The interesting attacks here are **threat-model knowledge**, not capabilities. (The BLE side — where my rig *does* do recon + spam — is [interception.md](interception.md); active **relay** concepts live in [../theory/relay-attacks.md](../theory/relay-attacks.md); see also [../my-use-cases.md](../my-use-cases.md).)

## 7. Defenses (blue-team, for my own devices)
- **Keep firmware/OS/BT stacks updated** — KNOB (Erratum 11838, min-key ≥ 7 octets) and BIAS (mutual-auth + role-switch + downgrade) mitigations ship via stack/OS patches. Old/abandoned BT gear is the real risk.
- **Prefer Secure Connections (Only) mode** where the device offers it — it blocks the BIAS **legacy-auth** path outright and resists SC→legacy downgrade.
- **Avoid legacy PIN pairing**; use SSP and, ideally, Numeric Comparison / OOB.
- **Disable discoverability** when not actively pairing; turn Bluetooth **off** when unused (kills BlueBorne-style airborne exposure on unpatched stacks).
- **Don't trust link-layer security alone** for sensitive data — add **application-layer crypto** (same advice as the BLE doc).

## 8. Legality (rated High)
KNOB/BIAS are **active interception/impersonation** of communications you aren't party to — squarely **wiretap / unauthorized-access** territory in most jurisdictions, and *worse* than passive sniffing. Even **scanning/listing** Classic devices is benign-ish (public inquiry responses) but logging others' identifiers can still cross privacy lines. **Own devices or a written-authorized engagement only** ([../legal-and-safety.md](../legal-and-safety.md)).

## Open questions / to research
- Does my Marauder build expose Classic **inquiry results** as a saveable log/PCAP, or only the on-screen list?
- Real-world prevalence in 2026 of devices still on **legacy auth / no Secure Connections** (who's actually KNOB/BIAS-exploitable now)? _(verify)_
- Is there *any* hobby-priced path to active BR/EDR LMP injection (modern Ubertooth firmware forks)? Suspect **no** for full KNOB/BIAS _(verify)_.
- Exact CVE/erratum status of BIAS fixes across the BT versions my own devices report _(verify per-device)_.
- Confirm whether the KNOB **BLE variant** is meaningfully exploitable against LE Secure Connections devices _(verify)_.

## Sources
- KNOB (paper + site): https://francozappa.github.io/publication/knob/ · https://knobattack.com/ · repo https://github.com/francozappa/knob
- KNOB CVE-2019-9506: https://westoahu.hawaii.edu/cyber/vulnerability-research/vulnerabilities-weekly-summaries/cve-2019-9506-bluetooth-devices-vulnerable-to-key-negotiation-of-bluetooth-knob-attacks/
- Bluetooth SIG KNOB statement + Erratum 11838 (min key ≥ 7 octets): https://www.bluetooth.com/learn-about-bluetooth/key-attributes/bluetooth-security/statement-key-negotiation-of-bluetooth/
- BIAS (paper + announce): https://francozappa.github.io/about-bias/publication/antonioli-20-bias/antonioli-20-bias.pdf · https://francozappa.github.io/post/bias-announce/
- BIAS advisory (CERT/CC VU#647177, mutual auth / SC-only mitigation): https://kb.cert.org/vuls/id/647177/
- BlueBorne (Armis 2017): https://www.armis.com/blog/blueborne-on-android-exploiting-an-rce-over-the-air/ · CVE list https://en.wikipedia.org/wiki/BlueBorne_(security_vulnerability)
- ESP32 Marauder Bluetooth scanner (Classic+BLE list, skimmer detection): https://github.com/justcallmekoko/ESP32Marauder/wiki/bluetooth-sniffer
- Ubertooth / crackle (Classic-ish monitoring): https://github.com/greatscottgadgets/ubertooth · https://github.com/mikeryan/crackle
