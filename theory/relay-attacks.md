---
title: Relay Attacks — Beating Crypto Without Breaking It
domain: theory
type: theory
status: detailed
summary: The attack class that beats correct crypto — PKES/BLE/NFC relay; UWB/distance-bounding defense
hardware: []
use_cases: []
related: [theory/rolling-codes.md, bluetooth/interception.md, topics/remaining-gaps.md, cards/cloning-matrix.md]
tags: [relay-attack, pkes, ble, nfc, uwb, distance-bounding, keyless-entry]
last_verified: 2026-06-19
---

# Relay Attacks — Beating Crypto Without Breaking It

> **TL;DR —** The attack class that defeats correct crypto by extending the range of a live authentication exchange — PKES car keys, BLE phone-as-key, and NFC/EMV relay — and why only UWB ranging / distance-bounding stops it.
> The standout of [remaining-gaps](../topics/remaining-gaps.md) Bucket B · cousin of [rolling-codes](rolling-codes.md) · BLE case in [bluetooth/interception](../bluetooth/interception.md). Part of the [KB](../README.md).

## The core idea
You don't break the crypto — you become a **transparent wire** that *extends the range* of a legitimate
authentication exchange. Two relay devices: a **leech** held near the token (key fob / phone / card) and
a **ghost** held near the verifier (car / lock / reader). They forward the messages back and forth in
real time, so the verifier concludes the token is present when it's actually far away. Because the **real
token performs the real crypto**, strong authentication, encryption, and rolling codes **don't help** —
the relay forges nothing.

> Defining property: relays are *"completely independent of the modulation, protocol, or presence of
> strong authentication and encryption."* That's why this is the cleanest example of "modern crypto ≠ safe."

## Relay vs replay vs amplification (don't conflate)
| Technique | What it does | Beaten by |
|---|---|---|
| **Replay** | record now, transmit later | nonces / rolling codes / freshness ([rolling-codes](rolling-codes.md)) |
| **Relay** | forward the *live* exchange in real time | **NOT** beaten by freshness/crypto — it's the genuine exchange |
| **Amplification** | a "dumb" relay — just boost the RF so the token hears the verifier from farther | distance/time bounding |
| **Link-layer relay** | decode → re-transmit the *messages* (low added latency) | tight distance bounding only (beats loose latency checks) |

## Where it works (by domain)

### 1. Car keyless entry (PKES) — the canonical case
- **How:** the fob has an **LF (125 kHz) receiver + UHF transmitter**; the car has an **LF transmitter + UHF receiver**. LF is deliberately **short-range (1–2 m)** so the car can sense the key is *right there*; the key answers on **UHF (~100 m)**. The attack **relays the car's LF wake-up** to the distant key (e.g. on a hook inside the house) → the key answers on UHF (already long-range) → the car unlocks and starts. Relaying **one direction (car→key)** is enough.
- **Origin:** Francillon, Danev & Čapkun (ETH Zürich, **2011**) — 10 models / 8 makers, worked to **50 m non-line-of-sight**.
- **2026 status:** still works on **most of the fleet** — >90% of 2019–2023 keyless models failed to block a relay. Some makers fixed it (Thatcham "Superior": BMW 7-Series, Porsche 911, Audi e-tron, Ford Puma). Cheap user fix: **Faraday pouch / kitchen foil**.

### 2. BLE phone-as-key / smart locks
- NCC Group (**2022**) built the first **link-layer** BLE relay: it forwards GATT at the link layer with only ~tens of ms added latency — under the threshold — defeating a **Tesla + LE Secure Connections + latency bounding + RSSI localization**, unlocking from **25 m**. Affects cars (phone-as-key) and residential smart locks. Detail: [bluetooth/interception](../bluetooth/interception.md).

### 3. NFC / contactless EMV
- **"Ghost & leech":** a **ghost** near the reader (up to ~50 m from it) and a **leech** near the victim card (~50 cm) relay the **APDU** exchange — even **over the internet** via two NFC phones.
- EMV contactless relay has been demonstrated repeatedly; the payoff is limited by **transaction caps**, **relay-resistance protocols** (below), and **device-bound tokenization** (Apple/Google Pay). Card cloning context: [cards/cloning-matrix](../cards/cloning-matrix.md).

## Why crypto can't stop it (the deep point)
Challenge–response, rolling codes, mutual auth, AES — **all run correctly, end-to-end, through the relay.**
The relay adds no forgery; it's a conduit. The verifier's *only* signal that something is wrong is that
**the prover isn't physically close**. So the only robust defense is to **measure distance or time** — and
you can't relay information **faster than light**.

## Defenses (what actually works)
| Defense | How it stops relay | Status (2026) |
|---|---|---|
| **UWB secure ranging** (time-of-flight) | cm-accurate distance "security bubble"; unlock only if the device is truly near | The real fix for car/phone keys — **CCC Digital Key 3.0 (2021) / 4.0 (2025)**, FiRa; in newer iPhones/Watch + some cars. **Adoption partial.** Even UWB has research attacks (clock manipulation) `(verify)` |
| **Distance bounding** (Brands-Chaum '93; Hancke-Kuhn) | cryptographic round-trip-time at the physical layer | the principle behind UWB ranging + EMV RRP |
| **EMV Relay Resistance** (Mastercard **PayPass-RRP**, **L1RP**) | reader times the card's response; bounds the link | deployed in contactless EMV |
| **User intent** (tap / PIN / app-confirm) | there's no *passive* exchange to relay | e.g. Tesla "PIN to drive" |
| **Motion-sensing fobs** (sleep when still) | a parked key sends no LF response | many newer fobs |
| **Faraday pouch / disable PKES** | blocks the LF entirely (user-side) | cheap, effective, manual |
| ~~Latency bounding / RSSI localization~~ | too loose / amplifiable | **defeated** (link-layer relay; amplification) |

## On MY rig — can the Flipper relay? (honest answer: no)
- **Car PKES relay — NO.** A single Flipper **can't process LF-in and UHF-out simultaneously**; a real relay needs **two synchronized radios** (often + amplification). Relay kits exist but are **separate purpose-built hardware**, not a Flipper.
- **BLE link-layer relay — NO** on this rig (needs two low-latency BLE devices; NCC used custom hardware; *Sniffle* can relay between two Sniffle boards — not the Marauder).
- **NFC relay — not practically.** The Flipper is **store-and-emulate**, not a live two-device relay, and modern HF cards add crypto it can't break. Phone-to-phone PoCs exist; it is **not a turnkey Flipper capability** `(verify)`.
- **What the rig *can* do** is the *replay* cousin (fixed-code Sub-GHz) and emulate **captured/cloned** cards — fundamentally different from a live relay.
- So relay sits in [remaining-gaps](../topics/remaining-gaps.md) **Bucket B (structural)** as a **threat to understand**, not a rig feature.

## Defending yourself (the useful takeaway)
- **Car:** Faraday pouch for the fob, enable **motion-sleep**, use **PIN-to-drive**, prefer a car with a **UWB** digital key; don't leave the fob near an exterior wall.
- **Contactless cards:** rely on **transaction limits + tokenized wallets** (relaying a tap nets little); RFID sleeves are low-value vs relay but harmless.
- **Smart locks:** prefer **UWB / user-confirm**; avoid pure BLE-proximity unlock for anything that matters.

## Open questions / to research
- Real 2026 **UWB digital-key** penetration across the car fleet + phones (how much is still relayable).
- Whether my own car/locks use PKES (relayable) vs UWB/user-confirm — the personal threat check.
- Status of UWB ranging attacks (clock/"Time for Change" line of research) `(verify)`.
- Any credible Flipper-based NFC-relay PoC, and why it's impractical vs phone-to-phone.

## Sources
- PKES relay (Francillon/Danev/Čapkun 2011): https://www.ndss-symposium.org/wp-content/uploads/2017/09/franc.pdf · 2025 status: https://keylessprotector.com/relay-attack-protection-2025-guide/
- BLE link-layer relay (NCC, 2022): https://www.nccgroup.com/research/technical-advisory-ble-proximity-authentication-vulnerable-to-relay-attacks/
- NFC/EMV relay + RRP: https://link.springer.com/chapter/10.1007/978-3-319-39814-3_8 · https://practical_emv.gitlab.io/ · https://dl.acm.org/doi/10.1145/3372297.3417235
- UWB / CCC Digital Key: https://www.firaconsortium.org/resource-hub/blog/uwb-secure-ranging-revolutionizing-security-technology · https://carconnectivity.org/digital-key-use-cases/
- Flipper relay limits: https://medium.com/@shahzaib01/youre-right-b2ab5a281e56
