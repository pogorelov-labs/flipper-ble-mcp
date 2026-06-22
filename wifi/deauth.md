---
title: Wi-Fi Deauthentication (UC-34)
domain: wifi
type: reference
status: detailed
summary: Deauthentication: the 802.11 flaw and the PMF/802.11w defense.
hardware: [esp32-marauder]
use_cases: [UC-34, UC-33, UC-36, UC-54]
related: [wifi/wpa-handshake-pmkid.md, wifi/evil-portal.md, wifi/recon-and-attacks.md, legal-and-safety.md]
tags: [deauth, 802-11, management-frames, pmf, 802-11w, dos, wpa3]
last_verified: 2026-06-19
---

# Wi-Fi Deauthentication (UC-34)

> **TL;DR —** How deauth works (forged 802.11 management frames kick clients off an AP), how to run it on the Marauder, and why PMF/802.11w — mandatory in WPA3 — stops it cold.
> Pairs with [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md), [evil-portal.md](evil-portal.md) · board [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md). Part of the [Wi-Fi hub](README.md) · [KB](../README.md).

## What it is
A **deauthentication attack** forges 802.11 **deauth** management frames to kick clients off an access point. It's a **denial-of-service** by itself — and, more usefully, a way to **force a reconnect** so you can capture a handshake or herd a client onto a rogue AP. It does **not** reveal or break any secret on its own.

## Why it works — the 802.11 design flaw
- Wi-Fi **management frames** (beacons, probes, auth/assoc, **deauth/disassoc**) are sent **unencrypted and unauthenticated** in WPA2 and earlier.
- So anyone can **spoof** a deauth frame using the AP's BSSID and a client's MAC — the client believes the AP told it to leave and disconnects.
- **No password or crypto break needed** — it's a protocol-level weakness.

## Frame anatomy (brief)
| Field | Value |
|---|---|
| Frame type | Management (type 0), **subtype 12 = deauth** (10 = disassoc) |
| Source addr | spoofed = **AP BSSID** |
| Dest addr | a **client MAC** (targeted) or **FF:FF:FF:FF:FF:FF** (broadcast = whole AP) |
| Reason code | e.g. 7 "class-3 frame from nonassociated STA" _(verify code use varies)_ |

## What it's used for
- **Disruption / DoS** — knock devices offline (noisy, obvious).
- **Force a handshake** → combine with **PMKID/EAPOL capture** ([UC-33](wpa-handshake-pmkid.md)).
- **Herd clients onto an Evil Twin** → kick them off the real AP so they reconnect to your rogue one ([evil-portal.md](evil-portal.md)).

## On the Marauder
- **Deauth Flood** tool: pick target AP(s) from `scanap`, then flood deauths (targeted client or broadcast). 2.4 GHz only.
- It's the provoke-step inside the "targeted active PMKID sniff" and Evil-Portal workflows.

## Why modern Wi-Fi resists it
- **PMF / 802.11w (Protected Management Frames):** authenticates unicast mgmt frames and integrity-checks broadcast ones → **forged deauths are rejected**.
- PMF is **mandatory in WPA3**, optional in WPA2. So on a WPA3 (or PMF-on WPA2) network, deauth simply **fails**.
- Detect deauth floods with a WIDS / monitor ([UC-54](../my-use-cases.md)).

## Honest limits
- Pure deauth = **disruption only**; it exposes nothing secret.
- Useless against PMF/WPA3.
- It's jamming-adjacent and disruptive to real users.

## Legality (rated High)
Disconnecting clients or networks you don't own is a **denial-of-service** — illegal in most jurisdictions. Only on your own gear, in an isolated lab, or an authorized engagement ([../legal-and-safety.md](../legal-and-safety.md)).

## Open questions / to research
- Exact Marauder deauth options/reason-codes on my build.
- Whether my own AP has PMF available (test that deauth fails when enabled).

## Sources
- Deauth (Wikipedia): https://en.wikipedia.org/wiki/Wi-Fi_deauthentication_attack
- Marauder Deauth Flood: https://github.com/justcallmekoko/ESP32Marauder/wiki/deauth-flood
- PMF/802.11w: https://docs.espressif.com/projects/esp-idf/en/v5.0.3/esp32/api-guides/wifi-security.html · https://lab401.com/blogs/academy/deauth
