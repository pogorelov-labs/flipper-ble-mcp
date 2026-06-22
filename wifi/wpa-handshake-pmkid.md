---
title: WPA Handshake & PMKID Capture (UC-33)
domain: wifi
type: reference
status: detailed
summary: Capture the WPA 4-way handshake / PMKID and crack it offline with hashcat.
hardware: [esp32-marauder]
use_cases: [UC-33, UC-54]
related: [wifi/own-network-audit.md, wifi/deauth.md, wifi/recon-and-attacks.md, topics/security-pentest.md, legal-and-safety.md]
tags: [wpa, pmkid, eapol, hashcat, offline-cracking, wpa3, pmf]
last_verified: 2026-06-19
---

# WPA Handshake & PMKID Capture (UC-33)

> **TL;DR —** How WPA-PSK capture plus offline cracking actually works: grab the 4-way handshake or clientless PMKID, convert with hcxtools, then crack with hashcat -m 22000 — a strong PSK or WPA3-SAE makes it fail.
> Rig: ESP32 Marauder ([../hardware/gpio-addons-current.md](../hardware/gpio-addons-current.md)) · use-case UC-33 ([../my-use-cases.md](../my-use-cases.md)) · framing [../topics/security-pentest.md](../topics/security-pentest.md). Part of the [Wi-Fi hub](README.md) · [KB](../README.md).

## The one-sentence truth
This does **not** "hack Wi-Fi." It captures a small cryptographic proof the network emits, then **guesses the password offline on a PC**. A strong password or WPA3 makes it fail. In practice it's a **password-strength test for your own network** — and capturing/cracking anyone else's is illegal ([../legal-and-safety.md](../legal-and-safety.md)).

The Flipper/ESP32 only **captures**. The actual cracking happens later on a computer with a GPU.

---

## 1. The WPA2-PSK key hierarchy
The whole attack exists because, in **WPA/WPA2-Personal**, the network's master key is derived **only** from the passphrase + network name:

| Key | Derived from | Notes |
|---|---|---|
| **PMK** (Pairwise Master Key) | `PBKDF2-HMAC-SHA1(passphrase, SSID, 4096 iters, 256 bits)` | Fixed per network. *This is what cracking recovers.* |
| **PTK** (Pairwise Transient Key) | `PRF(PMK, ANonce ‖ SNonce ‖ AP_MAC ‖ STA_MAC)` | Per-session; split into KCK / KEK / TK |
| **MIC** (Message Integrity Code) | `HMAC(KCK, EAPOL frame)` | Proves both sides hold the same PMK (= know the password) |

The 4096-iteration PBKDF2 is deliberately **slow** — that's what makes a strong PSK expensive to guess.

## 2. The 4-way handshake (what's exchanged, what's useful)
When a client joins, AP and client prove they share the PMK **without sending it**, via four EAPOL-Key frames:

| Msg | Dir | Contains | Why it matters to a cracker |
|---|---|---|---|
| **M1** | AP→client | **ANonce** (random), no MIC | gives ANonce |
| **M2** | client→AP | **SNonce** + **MIC** | gives SNonce + a MIC to test guesses against |
| **M3** | AP→client | GTK + MIC (install keys) | confirms; alt MIC source |
| **M4** | client→AP | ACK + MIC | completes |

**To crack, you need:** SSID, AP_MAC, STA_MAC, ANonce, SNonce, and one MIC. With those an attacker loops offline: *guess passphrase → PMK → PTK → recompute MIC → compare.* A match reveals the password. Capturing **M1+M2** is enough.

## 3. Two ways to capture

### A) Handshake capture — needs a connected client
1. Sniff on the AP's channel.
2. Wait for a device to (re)connect → grab the EAPOL frames.
3. **Speed it up with a deauth:** forge a "deauthenticate" management frame to kick a client off; it auto-reconnects → fresh handshake. (Deauth works on open management frames; **blocked by PMF/802.11w** — see §6.)

### B) PMKID capture — clientless (the 2018 shortcut)
- The **PMKID** = `HMAC-SHA1(PMK, "PMK Name" ‖ AP_MAC ‖ STA_MAC)` is included in the **RSN element of the AP's first EAPOL frame** on APs that support roaming/PMK caching.
- You can solicit it **directly from the AP** — **no client, no deauth, no full handshake**. Then crack the PMKID offline the same way.
- Discovered by hashcat's **Jens "atom" Steube (Aug 2018)**; hashcat mode **16800** (now folded into unified mode **22000**).
- Only works if the AP emits a PMKID — many do, some don't.

## 4. Offline cracking (the real "attack," on a PC)
1. Convert the capture (PCAP) → a hashcat **22000** line with **hcxpcapngtool** (hcxtools).
2. Run **hashcat -m 22000** with a wordlist (e.g. rockyou) or mask, on a GPU; or aircrack-ng.
3. Outcome depends entirely on the PSK:
   - **Weak / dictionary / short** → cracked in seconds-to-hours.
   - **Random ≥12–16 chars** → effectively **uncrackable** (PBKDF2 cost × keyspace).
- **This is the point:** UC-33 measures *your* password's resistance. A failed crack is a passing grade.

## 5. On my rig — ESP32-WROOM Marauder (2.4 GHz)
- Menu items: **Sniff EAPOL** (handshakes), **Sniff PMKID**, and **targeted active PMKID sniff** (`scanap` → select AP → deauth + capture, so only your target is disrupted).
- Captures save as **PCAP to the board's onboard microSD** → pull the card, convert + crack on a PC.
- Driven by the **WiFi Marauder** companion app; **2.4 GHz only** (WROOM); run the Flipper on **USB power**.
- Typical flow: `scanap` (list APs) → pick **your** AP → Sniff PMKID *or* Sniff EAPOL (+ deauth to provoke) → export SD → `hcxpcapngtool` → `hashcat -m 22000`.

## 6. Why it often fails — and that's good
- **Strong PSK** → offline crack infeasible.
- **WPA3-SAE ("Dragonfly")** → captured handshake/PMKID is **useless**: SAE provides offline-dictionary **resistance** + forward secrecy, and the **PMKID attack doesn't apply**.
- **PMF / 802.11w** (mandatory in WPA3, optional in WPA2) → **deauth is blocked**, so you can't force a handshake.
- Caveats: **WPA3 *transition* mode** still accepts WPA2 clients (downgrade exposure); **WPS** is a separate weakness; *Dragonblood* (Vanhoef/Ronen 2019) found WPA3 side-channel/downgrade bugs — not offline dictionary cracking.

## 7. Defenses (blue-team)
- Use a **long random PSK** (≥12–16 chars) or **WPA3-SAE**.
- Enable **PMF (802.11w)**; **disable WPS**; avoid WPA3 transition mode where possible; isolate guest networks.
- Detect **deauth floods** ([UC-54](../my-use-cases.md)) and rogue sniffers.

## 8. Legality (rated High)
Capturing handshakes/PMKIDs and cracking them is lawful **only** on networks you **own or are explicitly authorized** to test. Against others' Wi-Fi it's unauthorized access/interception — illegal in most jurisdictions ([../legal-and-safety.md](../legal-and-safety.md)). Use it to audit your **own** PSK.

## Open questions / to research
- Exact Marauder build menu labels on my board (v8?) and whether it writes 22000 directly vs PCAP-only.
- hcxtools install + the precise convert→hashcat command line (a runnable mini-guide).
- WPA3 adoption on my own gear — is my router SAE-capable / PMF-on?

## Sources
- 4-way handshake: https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2 · https://mrncciew.com/2014/08/19/cwsp-4-way-handshake/
- PMKID attack (origin): https://hashcat.net/forum/thread-7717.html · https://www.hackingarticles.in/wireless-penetration-testing-pmkid-attack/
- Marauder PMKID/EAPOL: https://github.com/justcallmekoko/ESP32Marauder/wiki/sniffpmkid · https://github.com/justcallmekoko/ESP32Marauder/wiki/targeted-active-pmkid-sniff-workflow
- WPA3/SAE/PMF: https://papers.mathyvanhoef.com/dragonblood.pdf · https://svenvg.com/posts/wifi-explained-wpa3-sae-and-pmf/
