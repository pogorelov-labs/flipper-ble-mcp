---
title: What Still Works — Real Remaining Gaps (2026)
domain: topics
type: topic
status: detailed
summary: Where capability still beats modern defenses in 2026 — deployment inertia, relay attacks, IoT floor, FM11RF08S.
hardware: []
use_cases: []
related: [capabilities/sub-ghz.md, cards/mifare.md, wifi/wpa-handshake-pmkid.md, bluetooth/interception.md, theory/rolling-codes.md, theory/relay-attacks.md]
tags: [remaining-gaps, deployment-inertia, relay-attacks, iot-security, fm11rf08s, legacy]
last_verified: 2026-06-19
---

# What Still Works — Real Remaining Gaps (2026)

> **TL;DR —** An honest accounting of where the Flipper still beats modern defenses: not fresh crypto breaks but four buckets — legacy deployment inertia, structural gaps (relay/human layer), the cheap-IoT quality floor, and newly-found holes like the FM11RF08S backdoor.
> Ties together [sub-ghz](../capabilities/sub-ghz.md) · [cards/mifare](../cards/mifare.md) · [wifi](../wifi/wpa-handshake-pmkid.md) · [bluetooth](../bluetooth/interception.md) · [rolling-codes](../theory/rolling-codes.md). Part of the [KB](../README.md).

## The thesis
Across this KB you'll see the refrain *"yes, the capability exists, BUT modern X resists it."* That's
**true for a fully up-to-date, correctly-configured target** — and **false for the world most systems
actually live in.** The gaps didn't close; they **moved**. They now sit in four buckets, and only one
of them is "new crypto breaks." "Modern X resists it" is a statement about a *target's configuration*,
not about reality — almost nothing is deployed to the modern standard end-to-end.

---

## Bucket A — Deployment inertia (the biggest gap by far)
The secure fix exists; the installed base hasn't adopted it. Hardware lifecycles are 10–20 years; cost
and compatibility win over security. **This is where the Flipper is genuinely powerful** — it's a
*deployment-inertia exploiter*.

| Gap (fix exists, not deployed) | Still everywhere because | My rig exploits it? |
|---|---|---|
| **Fixed-code Sub-GHz** (EV1527/PT2262) — gates, garages, RF outlets, 433 alarm sensors | cheap, "it still works" | ✅ capture/replay ([sub-ghz](../capabilities/sub-ghz.md)) |
| **125 kHz prox** (EM4100/HID Prox) — "among the easiest physical bypasses" | huge installed base | ✅ clone to T5577 ([lf-125khz](../cards/lf-125khz.md)) |
| **MIFARE Classic** (Crypto1, broken 2008) — hotels/transit/offices/gyms | "many orgs still use it despite published breaks" | ✅ crack+clone ([mifare](../cards/mifare.md)) |
| **iCLASS legacy** (keys leaked) | partial migration to SE/SEOS | ✅ PicoPass ([iclass-picopass](../cards/iclass-picopass.md)) |
| **WPA2-PSK weak password** | WPA3 adoption slow; transition mode is the 2026 norm | ✅ capture+offline crack ([wpa](../wifi/wpa-handshake-pmkid.md)) |
| **WPS on / PMF off** | default on older routers | ✅ deauth works (PMF off); WPS partial |
| **UID-only readers** | reader trusts just the UID, even on good cards | ✅ spoof the UID |

Why it persists: replacing readers/cars/locks is expensive, and "secure enough until it isn't" is the
default posture. The modern fixes (DESFire EV3 + diversified keys + reader-side checks, WPA3+PMF) exist
and *work* — they're just not everywhere.

## Bucket B — Structural gaps crypto can't close
- **Relay attacks (the standout).** Proximity-based auth — car **PKES**, **BLE phone-as-key**, some
  smart locks. The crypto is perfect; you **relay** the legitimate exchange between key and lock. NCC
  Group (2022) defeated a **Tesla + LE Secure Connections + latency-bounding + anti-amplification
  localization**, unlocking from **25 m**. The only real fix is **UWB / time-of-flight distance
  bounding** or a user-confirm tap — adoption still **partial** in 2026. This is the cleanest proof that
  *"modern crypto" ≠ safe.* **Not a Flipper-rig capability** (needs a paired low-latency relay), but the
  most important gap to understand — full deep-dive: **[relay-attacks](../theory/relay-attacks.md)**. ([bluetooth/interception](../bluetooth/interception.md))
- **The human layer.** **Evil-Twin/captive-portal phishing** and **BadUSB on an unlocked machine** work
  on fully-patched targets — they attack people and trust, not ciphers. ✅ my rig — full deep-dive: **[human-layer](../theory/human-layer.md)** ([evil-portal](../wifi/evil-portal.md), [badusb](../capabilities/badusb.md)).
- **Availability (jamming).** Structurally unfixable by crypto; illegal and out of scope here ([legal](../legal-and-safety.md)).

## Bucket C — Implementation / quality-floor gaps
The standard is fine; the *product* isn't.
- **Cheap BLE IoT** (smart locks, toys, fitness, some medical) using **Just Works / no app-layer auth /
  replayable commands** → sniff, replay, spoof. My rig: **partial** — advertising yes; connection
  capture needs the [nRF52840 sniffer add-on](../bluetooth/ble-sniffer-addon.md).
- **Misconfigured DESFire** — default keys, readable AIDs: a secure card deployed insecurely.
- **Vendor rolling-code bugs.** **Rolling-PWN** (Honda 2012–2022, CVE-2021-46145 — *non-expiring code +
  counter-resync* replay) and **RollBack** (2022, *time-agnostic* replay) prove rolling code is only as
  good as its implementation. Mostly SDR/specialized, not turnkey-Flipper. ([rolling-codes](../theory/rolling-codes.md))

## Bucket D — Newly found / not-yet-patched (the "resistant" claim has a shelf life)
Research keeps breaking the *current* stuff:
- **FM11RF08S backdoor (Quarkslab, Aug 2024)** — the FM11RF08S was the **"hardened," resists-all-card-
  only-attacks MIFARE Classic variant**… and it shipped with a **hardware backdoor key** that recovers
  **all user keys (even fully diversified) in minutes**. Affects Fudan **FM11RF08S/FM11RF08/FM11RF32/
  FM1208-10** plus some **NXP MF1ICS5003/5004** and **Infineon SLE66R35**. Recovered via **Proxmark3**
  _(verify Flipper support)_. **This is your recurring point in one finding:** the "modern resistant"
  replacement was itself broken — in hardware, on cards already shipping worldwide.
- Plus BLE relay (Bucket B) and the steady drip of key-fob/vendor bugs. The frontier always moves.

---

## The honest meta-answer
**Are there truly remaining gaps? Yes — large ones — but they're mostly not fresh crypto breaks.** They are:
1. The **huge legacy install base** (A) — where the Flipper is devastating.
2. **Structural** problems crypto can't solve — **relay** (cars/locks) and the **human layer** (B).
3. The **quality floor** of cheap IoT (C).
4. A **steady drip** of new findings even in "hardened" tech (D).

A system *correctly* built to the 2026 standard — WPA3-SAE + PMF, DESFire EV3 with diversified keys and
reader-side validation, UWB-ranged keyless entry, BLE LE-Secure-Connections + app-layer crypto — really
does defeat this rig. The gap is that **almost nothing is deployed that way end-to-end.**

## What this means for MY rig
- **Powerful at:** auditing my own **legacy** exposure — fixed-code remotes, 125 kHz/MIFARE-Classic/
  iCLASS-legacy cards, WPA2 PSK strength, Evil-Twin awareness (Bucket A + human layer).
- **Stopped by:** correctly-deployed modern crypto (rolling-AES, DESFire EV3, WPA3-SAE, LESC).
- **Beyond this rig:** **relay** (paired hardware), **FM11RF08S** backdoor (Proxmark3), **BLE connection
  sniffing** ([nRF52840 add-on](../bluetooth/ble-sniffer-addon.md)), **car RKE bugs** (SDR).
- **Frame:** the Flipper is best understood as a **"is your stuff actually on the modern standard?"
  tester.** Most of the time the honest answer is *no* — and that's the gap.

## Open questions / to research
- Does any Flipper firmware/app support the **FM11RF08S backdoor** auth, or is it Proxmark-only? _(verify)_
- Real-world **UWB keyless-entry** adoption % by 2026 (how much of the car fleet still relays).
- Which of my **own** BLE devices use Just Works vs LESC (the Bucket-C test for my gear).
- A concrete **"audit my own legacy exposure"** checklist drawing on Bucket A.

## Sources
- FM11RF08S backdoor: https://blog.quarkslab.com/mifare-classic-static-encrypted-nonce-and-backdoors.html · https://thehackernews.com/2024/08/hardware-backdoor-discovered-in-rfid.html
- BLE relay (Tesla/locks): https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/
- Rolling-PWN: https://rollingpwn.github.io/rolling-pwn/ · RollBack: https://arxiv.org/pdf/2210.11923
- WPA3 adoption (2026): https://mrncciew.com/2026/02/20/why-is-wpa3-adoption-so-slow/
- Legacy access prevalence: https://www.blackhillsinfosec.com/rfid-proximity-cloning-attacks/ · https://www.hidglobal.com/products/350x
