---
title: The Human Layer — Where Crypto Doesn't Apply
domain: theory
type: theory
status: detailed
summary: The gap no patch closes — phishing, BadUSB social-eng, NFC/QR baiting; passkeys as the fix
hardware: []
use_cases: [UC-19, UC-25, UC-26, UC-27, UC-36]
related: [topics/remaining-gaps.md, theory/relay-attacks.md, wifi/evil-portal.md, capabilities/badusb.md, bluetooth/ble-spam.md, capabilities/nfc-rfid.md]
tags: [social-engineering, phishing, badusb, quishing, nfc-baiting, passkeys, fido2, evil-twin]
last_verified: 2026-06-19
---

# The Human Layer — Where Crypto Doesn't Apply

> **TL;DR —** Attacks on people and trust that beat fully-patched, modern-crypto targets — Evil-Twin phishing, BadUSB social engineering, NFC/QR baiting, cloned-badge pretexting — and why phishing-resistant auth (FIDO2/passkeys) is the one real fix.
> [remaining-gaps](../topics/remaining-gaps.md) Bucket B · sibling of [relay-attacks](relay-attacks.md) · vectors: [evil-portal](../wifi/evil-portal.md), [badusb](../capabilities/badusb.md), [ble-spam](../bluetooth/ble-spam.md). Part of the [KB](../README.md).

## The core idea
Every other attack class in this KB targets a **protocol**. The human layer targets the **person operating
it** — and there is **no patch for that**. It works on a fully-patched device with WPA3, AES, UWB, and a
hardware secure element, because it never touches the crypto: it convinces a human to **type a secret, plug
in a device, tap a tag, or hold a door.** It's the most universal member of [remaining-gaps](../topics/remaining-gaps.md) Bucket B.

> The Flipper's role here is a **prop / credibility multiplier** — a real cloned badge, a planted NFC tag,
> a "firmware-update" USB make a pretext *physical and believable*. The device wins by going **around** the
> human, not through the crypto.

## The vectors (consolidated)

### 1. Evil-Twin / captive-portal phishing (Wi-Fi)
Rogue AP + fake "Sign in to Wi-Fi" / login page → harvest credentials (mechanics: [wifi/evil-portal](../wifi/evil-portal.md)).
**Why it beats modern crypto:** the captive-portal UX *trains* users to sign in, SSID names are trusted, and
the rogue AP is **open** — there's no cipher to break. WPA3 doesn't stop a rogue open AP. Rig: ✅ (Marauder).

### 2. BadUSB / BadBT social engineering (HID)
Technically HID injection ([capabilities/badusb](../capabilities/badusb.md)); the **delivery is human** — the dropped USB,
"plug in to print/charge," "here's the deck," or simply an **unlocked unattended machine**.
**The data:** a UIUC/Michigan/Google study dropped **297** USB drives on a campus — **98% were picked up,
files opened on 45%**, first one plugged in **< 6 minutes**; **68% did it "to return the drive,"** 18% out of
curiosity. (CompTIA: ~20% plugged in.) It's altruism + curiosity, not stupidity — which is why it keeps working.
Rig: ✅ (USB/BLE HID) — but it depends on a human plugging it in or leaving a session open.

### 3. NFC / QR tag baiting ("quishing")
A planted or overlaid tag/QR opens a phishing URL, joins a rogue Wi-Fi, or triggers a payment prompt.
**Quishing rose ~25% in 2025; ~12% of phishing now includes a QR.** Tactics: stickers over legit codes, fake
parking-meter QRs, "scan to confirm delivery"; nested/split QRs evade scanners; QR is often **paired with an
NFC prompt** to join a fake network or authorize a payment. Rig: ✅ partial — the Flipper **writes NDEF tags**
([nfc-rfid](../capabilities/nfc-rfid.md), UC-19), so a planted NTAG that auto-opens a URL / Wi-Fi-join is a real human-layer vector.

### 4. Cloned-credential pretexting (physical)
Bucket A clones the badge ([cards/](../cards/README.md)); but **obtaining** the card to clone (bump/proximity read,
"I forgot my badge") and **using** it on-site (tailgating, confident walk-in) is social engineering. The clone
just makes the pretext credible.

### 5. BLE spam / rogue-pairing as a lure
[bluetooth/ble-spam](../bluetooth/ble-spam.md) popups can seed a "fix your Bluetooth by…" pretext or soften/distract a target —
a nuisance turned social opening.

## Why it beats modern defenses
Crypto, UWB ranging, and secure elements all **assume the legitimate human behaves correctly.** The human is
the **un-patchable endpoint**: a flawless WPA3 network is moot if the user types the PSK into a fake portal;
a hardware-keyed laptop is moot if it's unlocked and someone plugs in a "keyboard." No firmware update fixes
**trust + convenience + curiosity.**

## Defenses — you can't patch the human, so shrink what a fooled human can do
| Control | Stops / blunts | Note |
|---|---|---|
| **Phishing-resistant auth — FIDO2 / passkeys** | credential phishing **+ Evil-Twin harvesting** | origin-bound public key → won't release a secret to a fake site (**verifier-impersonation resistant**). *Caveat: AitM downgrade to a weaker fallback.* The single best technical control. |
| **802.1X / EAP-TLS** (Wi-Fi) | Evil-Twin PSK phishing | certificate-based; nothing phishable |
| **HTTPS + HSTS, OS captive-portal sandbox** | fake login pages | cert warnings; isolates the portal |
| **USB device-control / allow-listing; disable HID-on-lock** | BadUSB | only approved devices act as input |
| **Screen-lock discipline + short timeout** | walk-up BadUSB / session hijack | physical hygiene |
| **Disable NFC auto-actions; confirm before acting** | NFC/QR baiting | don't auto-open tag URLs |
| **Anti-tailgating (mantraps), badge-on-display** | physical pretexting | process, not tech |
| **Awareness training + phishing/USB-drop sims** | all of the above | the **primary** control — the only one aimed at the actual gap |

## On MY rig
- **This is where the Flipper is genuinely potent against *modern* targets** — it doesn't fight the crypto, it
  equips a human attack: Evil Portal (UC-36), BadUSB/BadBT (UC-25/26/27), a planted **NDEF tag** (UC-19), a
  cloned badge as a prop, BLE-spam as a lure.
- **The rig is the prop, not the exploit.** Every one of these needs a person to sign in, plug in, tap, or hold
  a door — remove the human mistake and the rig does nothing here.
- **Legality: uniformly High.** These target people. Authorized social-engineering needs explicit written
  **ROE + consent** (named targets, approved pretext, data handling); phishing/USB-drop sims are HR/legal-
  sensitive even internally; doing any of it to the public is fraud / unauthorized access. See
  [legal-and-safety](../legal-and-safety.md) and [security-pentest](../topics/security-pentest.md).

## Open questions / to research
- Passkey/FIDO2 adoption + AitM-downgrade defenses in 2026 — how much of the phishing gap is actually closing.
- A safe **own-environment** drill: a planted NDEF tag + an Evil-Portal awareness test on my own devices.
- Build a **phishing-resistant-auth checklist** for my own accounts (the personal fix).

## Sources
- USB-drop study: https://zakird.com/papers/usb.pdf · https://blog.knowbe4.com/users-really-do-plug-in-usb-drives-they-find
- Phishing-resistant auth / passkeys: https://fidoalliance.org/passkeys/ · https://www.ncsc.gov.uk/paper/traditional-user-and-fido2-credentials-personal-use
- Quishing / NFC-QR: https://keepnetlabs.com/blog/qr-code-phishing-trends-in-depth-analysis-of-rising-quishing-statistics · https://abnormal.ai/glossary/qr-code-phishing-attacks
