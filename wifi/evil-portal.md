---
title: Evil Portal / Evil Twin (UC-36)
domain: wifi
type: reference
status: detailed
summary: Rogue-AP captive-portal credential harvesting.
hardware: [esp32-marauder]
use_cases: [UC-36, UC-34]
related: [wifi/deauth.md, wifi/wpa-handshake-pmkid.md, wifi/recon-and-attacks.md, topics/security-pentest.md, legal-and-safety.md]
tags: [evil-portal, evil-twin, rogue-ap, captive-portal, phishing, dns-hijack, defenses]
last_verified: 2026-06-19
---

# Evil Portal / Evil Twin (UC-36)

> **TL;DR —** How rogue-AP captive-portal credential harvesting works (DNS hijack pops a fake Wi-Fi sign-in page that logs whatever the victim types) and the defenses (HTTPS/HSTS, OS captive sandboxes, 802.1X, user awareness).
> Pairs with [deauth.md](deauth.md), [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md) · framing [../topics/security-pentest.md](../topics/security-pentest.md). Part of the [Wi-Fi hub](README.md) · [KB](../README.md).

## What it is
The Marauder stands up a **rogue access point** plus a **captive portal**: any device that joins gets funneled to a fake login page (a router "re-enter your Wi-Fi password", or a fake social/email login). Whatever the victim types is **captured**. When the rogue AP **clones a real SSID**, it's an **"Evil Twin."**

Critically, this attacks **human trust + the captive-portal UX — not cryptography.** It breaks no encryption; it tricks a person into typing a secret.

## How it works (the chain)
1. **Rogue AP:** the ESP32 broadcasts an SSID (often cloning a real one) and runs a tiny **web server + DNS server**. The rogue AP is usually **open** (no password) so anyone can join.
2. **(Optional) Deauth** the real AP ([UC-34](deauth.md)) so clients drop and reconnect — ideally to the twin.
3. **Captive-portal trigger:** every OS probes a known URL to detect captive portals (Apple `captive.apple.com`, Android `connectivitycheck.gstatic.com`, Microsoft `msftconnecttest.com`). The ESP's **DNS hijack** answers *every* lookup with its own IP → the probe "fails" → the OS auto-pops the **"Sign in to Wi-Fi"** page = your fake portal.
4. **Harvest:** the victim submits the form → credentials are logged to ESP **flash** and to the SD card (e.g. `/sdcard/lab/portals.txt`) _(path varies by build — verify)_, persistent until cleared.

## On the Marauder
- **Evil Portal** tool: load a custom **HTML** page from the SD card, set the SSID, start the AP; then **view / clear** captured logs and export them from SD.
- The HTML is fully customizable to the scenario (the realism is what makes it work).

## Why it's effective — and its real limits
- Exploits **trust + convenience**, so no crypto needs breaking; an **open** twin needs no password to stand up.
- **Limits / what stops it:**
  - **HTTPS + HSTS:** it can't present a valid certificate for a real site → browsers show **cert warnings**; modern sites/apps won't auto-submit.
  - OS **captive-portal sandboxes** isolate that mini-browser and warn users.
  - **User awareness:** never type real passwords into a Wi-Fi "sign-in" page.
  - WPA3/PMF doesn't stop a rogue *open* AP, but it makes the **deauth-assisted herding** step fail ([deauth.md](deauth.md)).

## Defenses (blue-team + personal)
- **Don't enter credentials** into Wi-Fi sign-in pages; verify SSIDs; prefer cellular when unsure; watch for cert warnings.
- **Enterprise:** **802.1X / EAP-TLS** (certificate-based, nothing phishable), rogue-AP detection (**WIPS**), client isolation, and "known network" hygiene on devices.

## Legality (rated High)
Standing up a rogue AP to harvest others' credentials is **unauthorized access / fraud** — illegal. Run it only in an **isolated lab** (your own devices) or an **authorized engagement with written consent** ([../legal-and-safety.md](../legal-and-safety.md)).

## Open questions / to research
- My Marauder build's exact Evil Portal HTML format + log path on SD.
- A safe lab setup (throwaway SSID + my own test phone) to see the capture end-to-end.
- How current iOS/Android captive-portal handling blunts this in 2026 _(verify)_.

## Sources
- Marauder Evil Portal: https://deepwiki.com/justcallmekoko/ESP32Marauder/2.5-evil-portal
- Captive-portal mechanics / evil twin background: https://en.wikipedia.org/wiki/Evil_twin_(wireless_networks)
