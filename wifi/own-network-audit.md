---
title: Own-Network Wi-Fi Audit — Mini-Guide (UC-33)
domain: wifi
type: guide
status: detailed
summary: Runnable: audit your own PSK (capture, hcxtools, hashcat).
hardware: [esp32-marauder]
use_cases: [UC-33]
related: [wifi/wpa-handshake-pmkid.md, wifi/deauth.md, wifi/recon-and-attacks.md, legal-and-safety.md]
tags: [wpa, psk-audit, hcxtools, hashcat, rockyou, macos, runnable]
last_verified: 2026-06-19
---

# Own-Network Wi-Fi Audit — Mini-Guide (UC-33)

> **TL;DR —** Runnable mini-guide to test YOUR OWN WPA2 PSK strength: capture PMKID/EAPOL on the Marauder, convert with hcxtools, then run hashcat -m 22000 against a wordlist — a failed crack is a passing grade.
> Theory: [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md) · board: [../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md). Part of the [Wi-Fi hub](README.md) · [KB](../README.md).

> ⚠️ **Your own network only.** Confirm the SSID **and** BSSID belong to you before capturing. Auditing
> someone else's Wi-Fi is illegal ([../legal-and-safety.md](../legal-and-safety.md)). hcxtools' own stated
> purpose is "detect weak points within one's **own** WiFi network."

**Goal:** prove whether your home Wi-Fi password would survive an offline crack. A failed crack = a passing grade.

**You need:** the ESP32 Marauder (+ WiFi Marauder app + its microSD) · a computer with **hcxtools** and **hashcat ≥6.0** · a wordlist (`rockyou.txt`) · ~15–30 min.

---

## Step 1 — Capture (near your AP, seconds)
In the WiFi Marauder app:
1. **Scan AP** (`scanap`) → note **your** SSID, BSSID, channel.
2. Select **your** AP as the target.
3. **Sniff PMKID** (clientless, easiest) — *or* **Sniff EAPOL/RAW** and force a handshake: on a device you own, toggle its Wi-Fi off/on (or briefly **deauth your own client** → it reconnects).
4. Stop when it reports a PMKID/EAPOL captured. The capture is written as **`.pcap`** to the board's **microSD** (e.g. `/pcaps`).
- No PMKID? Some APs don't emit one → use the EAPOL/handshake method.

## Step 2 — Move the capture to your computer
Power off, pull the Marauder microSD, copy the `.pcap` to your PC (or export via the app, per your build).

## Step 3 — Convert to a hashcat hash (mode 22000)
```bash
# install: Debian/Ubuntu → sudo apt install hcxtools ; macOS → brew install hcxtools
hcxpcapngtool -o mynet.hc22000 capture.pcap
```
- Produces a **22000** hashline (PMKID and/or EAPOL).
- The output lists the **ESSID + AP MAC** — confirm it's **your** BSSID and delete any other lines.

## Step 4 — Try to crack it (fully offline — no network, no proximity)
```bash
# wordlist attack
hashcat -m 22000 mynet.hc22000 rockyou.txt

# realistic extras: rules, or a mask (e.g. 8 digits)
hashcat -m 22000 mynet.hc22000 rockyou.txt -r rules/best64.rule
hashcat -m 22000 mynet.hc22000 -a 3 ?d?d?d?d?d?d?d?d
hashcat -m 22000 mynet.hc22000 --show     # show a cracked result
```

## Step 5 — Read the verdict
| Result | Meaning | Action |
|---|---|---|
| **Cracked in seconds–minutes** | weak / dictionary / short PSK | **change it now** |
| Cracked only with big masks / hours | borderline | strengthen |
| **Exhausted / not found** | resisted your test | good — but only as strong as the wordlist/masks you tried |

Target state: a **random ≥12–16 char** PSK, or move to **WPA3-SAE** (then this whole attack is moot — see [wpa-handshake-pmkid.md](wpa-handshake-pmkid.md) §6).

## Step 6 — Clean up
Delete the `.pcap` and `.hc22000` (they encode your network's auth material) and wipe the captures off the Marauder SD.

## macOS notes (my machine is darwin)
- `brew install hashcat hcxtools`. hashcat runs on macOS (Metal/OpenCL), but Apple-silicon GPU cracking is modest — for big wordlists use a Linux box with an NVIDIA GPU or a cloud GPU. A quick `rockyou` pass is fine locally.

## Open questions / to research
- My Marauder build's exact capture filename/path on SD, and whether it can emit 22000 directly vs PCAP-only.
- Best compact "realistic" wordlist+rules combo to represent a motivated attacker.
- Confirm whether my router supports WPA3-SAE + PMF (then re-audit is unnecessary).

## Sources
- hcxtools / hcxpcapngtool: https://github.com/ZerBea/hcxtools · https://hashcat.net/cap2hashcat/
- hashcat 22000: https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2
- Marauder PMKID/EAPOL: https://github.com/justcallmekoko/ESP32Marauder/wiki/sniffpmkid
