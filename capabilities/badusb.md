---
title: BadUSB / BadBT (HID Injection)
domain: capabilities
type: reference
status: detailed
summary: HID keystroke injection over USB (and BLE on CFW) — Ducky Script, layouts, OS targets, and blue-team defenses.
hardware: [flipper-internal]
use_cases: [UC-25, UC-26, UC-27, UC-28, UC-50]
related: [topics/security-pentest.md, resources/best-github-repos.md, legal-and-safety.md]
tags: [badusb, badbt, hid, ducky-script, keystroke-injection, ble-hid, defenses]
last_verified: 2026-06-19
---

# BadUSB / BadBT (HID Injection)

> **TL;DR —** The Flipper enumerates as a trusted HID keyboard (USB, or BLE on CFW) to "type" scripted payloads at machine speed with the logged-in user's privileges — the Rubber Ducky model. Covers why HID trust bypasses software controls, the Flipper Ducky Script dialect, `.kl` keyboard layouts, BadBT over BLE, OS-target concepts, and blue-team defenses. No working payloads.
> See [../topics/security-pentest.md](../topics/security-pentest.md), [../legal-and-safety.md](../legal-and-safety.md), [../resources/best-github-repos.md](../resources/best-github-repos.md). Part of the [KB](../README.md).

> **Authorized use only.** This page explains mechanics and **defenses** so you can test machines you own or have **written permission** to assess. Unauthorized keystroke injection is unauthorized access (CFAA / Computer Misuse Act / local equivalents). No working attack payloads here — see [../legal-and-safety.md](../legal-and-safety.md).

## Why a "keyboard" bypasses software controls

When plugged in, the Flipper **enumerates over USB as a HID keyboard** (it can also present mouse/consumer-control interfaces). The OS trusts HID by design — there is no "is this really a human?" check, and a keyboard needs no driver install, no admin prompt, and is exempt from USB *mass-storage* blocking. So the Flipper "types" a scripted payload at machine speed into whatever window has focus, with the **privileges of the logged-in user**. This is the classic **Rubber Ducky** model.

Key consequences for defenders to internalize:
- It **does not exploit a vuln** — it abuses legitimate HID trust. AV/EDR may not flag the *device*; detection has to come from *behavior* (impossible typing speed) or *device policy*.
- It runs as the **current user**, not root/SYSTEM — so it inherits that user's rights (and limits). UAC/sudo still gate elevation unless the user is already privileged or is socially engineered.
- A **locked screen** stops most payloads cold (keystrokes go nowhere useful) — screen-lock discipline is the cheapest defense.
- Mass-storage allow-listing alone is insufficient: a device can expose a **hidden HID interface** alongside (or instead of) storage. Control must be at the **interface** level.

## Ducky Script on the Flipper

Payloads are plain `.txt` files in `/ext/badusb/`, written in **Ducky Script**, executed by the **Bad USB** app. The Flipper runs an **extended dialect**: compatible with classic **USB Rubber Ducky 1.0**, plus Flipper-specific additions (custom USB ID, ALT+Numpad, SYSRQ, more function keys, mouse). Both `\n` and `\r\n` line endings work; blank lines and leading whitespace are fine.

### Command set (per current firmware `BadUsbScriptFormat.md`)

| Command | Type | Purpose |
|---|---|---|
| `REM <text>` | classic | Comment; ignored by interpreter |
| `DELAY <ms>` | classic | Pause N milliseconds (lets the target keep up) |
| `DEFAULT_DELAY <ms>` / `DEFAULTDELAY <ms>` | classic | Auto-pause inserted **before every command** |
| `STRING <text>` | classic | Type the literal text (case handled automatically) |
| `STRINGLN <text>` | classic | Type text **then press Enter** `(supported in current FW; older builds lacked it — verify on your CFW)` |
| `ENTER`, `TAB`, `ESC`/`ESCAPE`, `SPACE`, `DELETE`, `BACKSPACE`, `HOME`, `END`, `INSERT`, `PAGEUP`, `PAGEDOWN`, `UP`/`DOWN`/`LEFT`/`RIGHT` (+`…ARROW`) | classic | Named non-printing keys |
| `CAPSLOCK`, `NUMLOCK`, `SCROLLLOCK`, `PRINTSCREEN`, `PAUSE`, `BREAK`, `MENU`/`APP` | classic | Lock/system keys |
| `F1`–`F12` | classic | Function keys |
| **Modifiers:** `CTRL`/`CONTROL`, `ALT`, `SHIFT`, `GUI`/`WINDOWS` | classic | Combine with `-` or space, e.g. `GUI r`, `CTRL ALT DELETE`; **up to 5 keys** held at once |
| `ID <vid:pid>` (+ optional manufacturer/product string) | **Flipper ext** | Spoof the USB descriptor so the device *looks like* a specific keyboard |
| `ALTCHAR <code>` | **Flipper ext** | Type one char via ALT+Numpad code point |
| `ALTSTRING <text>` / `ALTCODE <text>` | **Flipper ext** | Whole string via ALT+Numpad (layout-independent entry trick) |
| `SYSRQ <key>` | **Flipper ext** | Linux Magic SysRq (kernel-level, works even on a frozen host) |
| `REPEAT <n>` | classic | Re-run the **previous line** n times (loops/retries) |
| `MEDIA <key>` | **Flipper ext** | Consumer-control keys (PLAY, VOLUP, MUTE, …) `(verify keyset on CFW)` |
| `GLOBE` | **Flipper ext** | macOS/iPad Fn/Globe key `(verify)` |
| `HOLD`/`RELEASE`, mouse (`LEFTCLICK`, `MOUSEMOVE`, `MOUSESCROLL`), `WAIT_FOR_BUTTON_PRESS` | **Flipper ext** | Documented in some CFW/build notes; **availability varies by firmware** — `(verify on your exact Unleashed/Xtreme build)` |
| `DUCKY_LANG <x>` | compat no-op | Accepted for cross-tool compatibility; ignored |

> Source conflict: the older methanoliver gist lists `STRINGLN` as *unsupported* and omits `HOLD`/`RELEASE`/`WAIT_FOR_BUTTON_PRESS`, while the current firmware doc and CFW builds include them. Treat the firmware-doc list as authoritative for up-to-date Unleashed/Xtreme, and `(verify)` the edge commands before relying on them.

### Keyboard-layout handling (`.kl` files)

Ducky Script types **HID scancodes**, not characters — the host maps scancode→character using *its* active layout. If the target is on AZERTY/QWERTZ/Cyrillic and your payload assumes US-QWERTY, symbols and letters land wrong (the classic `STRING` garbling). The Flipper fixes this with **keyboard-layout files (`.kl`)**: binary maps in `/ext/badusb/assets/layouts/` selected in the Bad USB app (e.g. `en-US`, `de-DE`, `fr-FR`). Pick the layout that matches the **target's** OS layout, not yours. `ALTSTRING`/ALT+Numpad is a layout-independent fallback on Windows when the target layout is unknown. (Custom `.kl` files can be generated with community tools — see repos below.)

## BadBT / BadKB over BLE HID (CFW)

On Unleashed/Xtreme, the **BadBT / BadKB** app runs the *same Ducky Script payloads* over **Bluetooth LE HID** — the Flipper advertises as a **BLE keyboard**, so **no cable** is needed. It can also clone an existing BT keyboard's name/MAC to blend in.

| Aspect | Detail |
|---|---|
| **Transport** | BLE HID (HID-over-GATT); Flipper acts as a wireless keyboard peripheral |
| **Pairing flow** | Enable BT, the Flipper broadcasts as a keyboard; target must **pair/accept** the device, then payload runs. Some OSes show a pairing/confirmation prompt — a real consent gate, unlike plug-in USB |
| **OS support** | Broad — Windows, macOS, Linux, Android all accept BLE keyboards; behavior/prompts differ per OS `(verify per target/CFW version)` |
| **vs USB** | Pros: no physical port, works at BT range, can run from a pocket. Cons: needs a (sometimes interactive) pairing step, less reliable than wired, BLE can be jammed/out of range |
| **Defensive note** | The pairing prompt + Bluetooth allow-listing/disable-when-locked are the BLE-side equivalents of USB device control |

Pairing is the friction that makes BLE injection *louder* than USB: an unexpected "keyboard wants to pair" prompt is itself an alert worth training users to refuse.

## OS-target considerations (conceptual)

Payloads differ by OS only in **which keys open a run/terminal surface and how text is invoked** — not in anything secret. At a conceptual level:

| OS | Concept (no payloads) |
|---|---|
| **Windows** | Run dialog / terminal launch + scripted commands; ALT+Numpad available; UAC still gates elevation |
| **macOS** | Spotlight/terminal launch; needs the right `.kl` and sometimes the Globe/Fn key; Gatekeeper/TCC prompts still apply |
| **Linux** | Terminal launch varies by DE; Magic **SYSRQ** is uniquely reachable; sudo still required for root |

Mature payloads include an **OS-detect / layout preamble** and timing `DELAY`s. We deliberately do **not** publish working chains — see repositories below for *authorized lab* study.

## Payload repositories

Curated in [../resources/best-github-repos.md](../resources/best-github-repos.md) (I-Am-Jakoby, MarkCyber, FalsePhilosopher, et al.). Use only against your **own** hardware or an in-scope, authorized engagement, ideally on disposable/lab VMs.

## Blue-team defenses

The throughline: **HID trust is the weakness**, so defend with device-policy + behavior detection + lock discipline, not AV signatures.

### 1. USB device control / interface-level allow-listing (strongest)
- Allow-list at the **interface** level, not device level — a "flash drive" can hide a HID keyboard interface; block the hidden interface while permitting storage.
- **Linux:** `USBGuard` — userspace daemon authorizing devices against an allowlist *before* the kernel binds them; generate a baseline policy from your known-good devices, default-deny new ones, and optionally **block all new devices while the screen is locked**.
- **Windows:** **Group Policy → Device Installation Restrictions** (allow/deny by device class/ID) and **Microsoft Defender for Endpoint device control** (policy + audit + optional serial-based allow-lists, cross-platform) for high-assurance fleets.
- **macOS:** MDM (Jamf/Intune) USB/removable-media restrictions and approved-device profiles.

### 2. Disable / restrict HID at lock
- Refuse **new** HID devices that enumerate while the workstation is **locked** (USBGuard policy switch; some EDR/endpoint suites offer the same). Defeats the "plug in while user is away" play.

### 3. Screen-lock discipline (cheapest, highest ROI)
- Auto-lock on short idle; lock-on-walk-away culture. A locked screen neuters nearly all keyboard payloads. Pair with strong, non-typed credentials so a injected unlock isn't trivial.

### 4. Endpoint/behavioral controls
- EDR/UEBA rules for **superhuman typing cadence**, sudden Run-dialog→PowerShell/terminal bursts, or a brand-new HID device immediately followed by command execution.
- App-allowlisting (WDAC/AppLocker) and constrained-language PowerShell blunt what an injected command can actually run.

### 5. BadUSB-blocker tooling
- Host agents that **fingerprint new keyboards and require confirmation** before accepting input (community tools historically: *DuckHunt*, *Beamgun*, *USBKill*-style monitors `(verify current maintenance status)`), and BLE: keep Bluetooth off when unused and **never accept unexpected pairing prompts**.

### 6. Physical / BLE
- Port blockers / data-blocking on kiosks; disable unused ports in firmware; for BLE, allow-list bonded devices and disable HID-over-GATT acceptance where the OS allows.

See [../topics/security-pentest.md](../topics/security-pentest.md) for where HID injection fits in an authorized engagement.

## Open questions / to research

- Exact, current command matrix for **Unleashed vs Xtreme/Momentum** BadUSB/BadKB (especially `HOLD`/`RELEASE`, `WAIT_FOR_BUTTON_PRESS`, `MEDIA`, mouse, `STRINGLN`) — confirm on installed firmware `(verify)`.
- Full list of shipped `.kl` layouts and the supported tool to build custom ones.
- BLE pairing UX per OS in 2026 (does macOS/Windows 11 force a confirmation? bondless injection still possible?) `(verify)`.
- Whether Defender for Endpoint / USBGuard reliably catch a device that presents **only** a HID interface (no storage) in current builds.
- Maintenance/efficacy status of DuckHunt / Beamgun-class blockers vs modern fast-typing payloads.
- Detection efficacy of "impossible typing speed" UEBA rules and false-positive rate with legitimate macro keyboards.

## Sources

- Flipper docs — Bad USB: https://docs.flipper.net/zero/bad-usb
- Firmware Ducky Script command reference: https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/BadUsbScriptFormat.md
- Developer docs (BadUSB file format): https://developer.flipper.net/flipperzero/doxygen/badusb_file_format.html
- DuckyScript-on-Flipper community reference (methanoliver gist): https://gist.github.com/methanoliver/efebfe8f4008e167417d4ab96e5e3cac
- Hak5 USB Rubber Ducky / Ducky Script: https://docs.hak5.org/hak5-usb-rubber-ducky
- BadBT (BLE) app: https://github.com/AGO061/BadBT · Xtreme wiki (BadKB): https://github.com/Flipper-XFW/Xtreme-Firmware/wiki/Generic-Guides
- USBGuard: https://wiki.archlinux.org/title/USBGuard · Windows Defender device control: https://learn.microsoft.com/en-us/defender-endpoint/device-control-overview
