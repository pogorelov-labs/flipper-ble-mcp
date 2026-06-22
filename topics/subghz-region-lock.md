---
title: Sub-GHz Region Lock & "Missing region file"
domain: topics
type: reference
status: detailed
summary: How Flipper's Sub-GHz region provisioning works, why "Missing region file" blocks TX, and the fix.
hardware: [flipper-internal, cc1101-ext]
use_cases: [UC-04, UC-05, UC-06, UC-07, UC-08, UC-09, UC-10, UC-11, UC-12]
related: [capabilities/sub-ghz.md, theory/rolling-codes.md, my-setup.md, resources/flipper-ble-control.md, legal-and-safety.md, firmware/official.md, firmware/momentum.md, firmware/migration-xtreme-to-momentum.md]
tags: [sub-ghz, region-lock, region-provisioning, furi-hal-region, region-data, firmware, compliance]
last_verified: 2026-06-22
---

# Sub-GHz Region Lock & "Missing region file"

> **TL;DR —** Before it transmits, the Flipper checks the target frequency against a **region allow-list** loaded from a small provisioning file at **`/int/.region_data`** (verify). That file is written **only by an online firmware install** (Web Updater / Flipper Lab / mobile app), where a Flipper server stamps your region from your **IP geolocation**. If the file is absent — offline/archive install, internal-storage wipe, or a custom-firmware flash that never re-provisioned — TX is blocked with **"Missing region file"**. That is the message we hit driving `the device` (Momentum `mntm-dev`) to send a 315 MHz Tesla `.sub`. It is **distinct** from "frequency not allowed in your region": the data is *missing*, not *forbidding*. **Fix:** reinstall/update Momentum once via its **Web Updater** (or qFlipper/app) to recreate `/int/.region_data` — or set **`Momentum → Protocols → SubGHz Bypass Region Lock`** to ignore the check entirely (legal duty then sits entirely on you — [legal-and-safety.md](../legal-and-safety.md)).
> Radio mechanics: [capabilities/sub-ghz.md](../capabilities/sub-ghz.md) · rolling codes: [theory/rolling-codes.md](../theory/rolling-codes.md) · the rig & how we drove it: [my-setup.md](../my-setup.md), [resources/flipper-ble-control.md](../resources/flipper-ble-control.md). Part of the [KB](../README.md).

## The concrete trigger
While driving the owner's physical Flipper (`the device`, Momentum `mntm-dev`, model FZ.1, migrated off EOL Xtreme — [my-setup.md](../my-setup.md)) **wirelessly over BLE** ([resources/flipper-ble-control.md](../resources/flipper-ble-control.md)), we opened a saved **315 MHz** Sub-GHz capture (a Tesla charge-port `.sub`, `Preset FuriHalSubGhzPresetOok650Async`) and pressed Send. The screen showed, verbatim:

```
Transmission is blocked
Missing region file. Reinstall firmware with Web/App or bypass region.
```

The wording is the giveaway: **"Missing region file"** ≠ "this frequency is restricted in your region." The first means the regional allow-list **isn't present at all**; the second means it *is* present and *forbids* this frequency. Knowing which you're looking at picks the fix (reinstall vs bypass). This doc explains the whole subsystem behind that one screen.

## What the "region" system is
The Flipper's Sub-GHz radio (TI **CC1101**, [capabilities/sub-ghz.md](../capabilities/sub-ghz.md)) can physically tune roughly **300–348 / 387–464 / 779–928 MHz**, but radio law lets you *transmit* on only a subset of that, and the subset **differs by country**. Flipper Devices ships a **region-aware TX allow-list** so the stock device only transmits where it's legally permitted to ([docs.flipper.net/zero/sub-ghz/frequencies](https://docs.flipper.net/zero/sub-ghz/frequencies)).

Three ideas stack up, and conflating them causes most confusion:

| Layer | What it bounds | Set by | Bypass on Momentum |
|---|---|---|---|
| **Hardware range** | What the CC1101 can tune at all (~300–348 / 386–464 / 778–928 MHz) | Silicon | None — "outside supported range" is final |
| **Default/firmware band list** | Frequencies the firmware will even *consider* (a safety/QA envelope inside the hardware range) | Firmware build | `SubGHz Extend Freq Bands` |
| **Region allow-list** | Of the default bands, which you may **transmit** on in *your country* | `/int/.region_data` (provisioned) | `SubGHz Bypass Region Lock` |

> **RX is never blocked.** The region system gates **transmit only**. You can always *receive/decode* on any frequency; only Send/Emulate is checked. On Momentum specifically: "the SubGHz app does not restrict receiving in any way, only transmit" ([Momentum FAQ](https://momentum-fw.dev/wiki/FAQ/)).

### The per-region allowed-frequency model
The official allocations (Flipper's published tables — [docs.flipper.net/zero/sub-ghz/frequencies](https://docs.flipper.net/zero/sub-ghz/frequencies); exact edges `(verify)`):

| Region group | TX-allowed bands | Examples |
|---|---|---|
| **Americas** (incl. US, CA, BR, MX, AU, NZ, …) | **304.10–321.95**, **433.05–434.79**, **915.00–928.00 MHz** | US 315 fobs/garages, 433.92 remotes, 915 ISM |
| **Europe / Africa / ME / much of Asia** (EU, UK, …) | **433.05–434.79**, **868.15–868.55 MHz** | 433.92 workhorse, 868 SRD |
| **UAE** | 420.00–440.00 MHz | — |
| **Taiwan** | 304.50–321.95, 433.075–434.775, 915.00–927.95 MHz | — |
| **Rest of World** (fallback) | 314.00–316.00, 430.00–432.00, 433.05–434.79 MHz | narrow safe set |

(Singapore, Israel, Philippines, India, China etc. have their own rows.) Internally these map to a small set of **hardware region codes** (e.g. `0/1/2…`) plus a provisioned country string — the device exposes both as `hardware_region` and `hardware_region_provisioned` in *Full Info* / `device_info` ([forum: Region Provisioning](https://forum.flipper.net/t/region-provisioning/5789)).

> **Note the 315 MHz subtlety relevant to our trigger:** 315 MHz (the Tesla `.sub`) is **only TX-legal in the Americas region**, not in the EU set. So even after we *provision* a region, whether that 315 MHz send is permitted depends on which region the device gets stamped with — see [How to fix](#how-to-fix-the-missing-region-file-our-case) and [Legal](#legal-regulatory--terms).

**Duty-cycle / ERP limits.** The published Flipper region tables list **frequency edges only** — they do **not** encode the EU's duty-cycle ceilings (often ≤1% or ≤0.1%) or per-sub-band ERP/power caps (e.g. ≤25–500 mW e.r.p.). Those legal limits are real (ETSI EN 300 220, CEPT/ERC REC 70-03) but live in the regulations, **not** in the Flipper's enforcement — the firmware gates *which frequency*, not *how long* or *how hard* you transmit. Full regulatory framing: [legal-and-safety.md](../legal-and-safety.md). `(verify: whether any build encodes duty/ERP — none observed.)`

## Provisioning: the region file, where it lives, how it's set
**The file.** The allow-list is loaded from a small hidden file on **internal flash**: **`/int/.region_data`** — it "contains information on allowed frequencies for [the] country you are located in" ([Momentum `SubGHzBypass&Extend.md`](https://github.com/Next-Flip/Momentum-Firmware/blob/dev/documentation/SubGHzBypass%26Extend.md)). `/int` is the ~1 MB internal LittleFS partition (separate from the SD card). Exact on-flash format is not publicly documented — treat as an opaque provisioning blob `(verify)`.

**When it's written — online install only.** Region is **(re)provisioned during a firmware install/update performed online**: the **Web Updater** (lab.flipper.net / momentum-fw.dev/update in Chrome), **Flipper Lab**, the **mobile app**, or **qFlipper**. During that flow a Flipper server determines your region from your **IP geolocation** (no VPN) and the installer writes the matching `.region_data` ([forum: Region Provisioning](https://forum.flipper.net/t/region-provisioning/5789); [docs: firmware update](https://docs.flipper.net/zero/basics/firmware-update)). It re-provisions **on each such update**, so the documented trick to *change* region is: travel, then update to RC and back to Release once on-location ([forum 5789](https://forum.flipper.net/t/region-provisioning/5789)).

**When it's absent.** `/int/.region_data` can be missing because:
- **Offline / archive install** — flashing a `.tgz`/`.dfu`/`.zip` directly (or any fully-offline method) **does not include the region step**, so no file is written ([Momentum `SubGHzBypass&Extend.md`](https://github.com/Next-Flip/Momentum-Firmware/blob/dev/documentation/SubGHzBypass%26Extend.md)). This is the most common cause.
- **Internal-storage wipe / repair** — wiping `/int` (storage repair, factory-reset-style operations) deletes it.
- **A custom-firmware flash that never re-provisioned online** — likely what happened to `the device` (see below).

**Out-of-the-box state.** Brand-new units (and any un-provisioned device) report region **`--`** and have **TX disabled** until the first online update: Flipper "has the send function disabled out of the box" and unlocks region-allowed frequencies only "during updates" ([docs: frequencies](https://docs.flipper.net/zero/sub-ghz/frequencies)). Users with region `--` repeatedly report that updating via **lab.flipper.net in Chrome** fixes it, whereas some mobile-app update paths left it blank ([forum: New Flipper, no region?](https://forum.flipper.net/t/new-flipper-zero-no-region/16299)).

> **OTA detail (why a reinstall is safe for your data):** before flashing, the updater backs up `/int` to a plain **tar archive on the SD card**, then restores it after reboot ([developer.flipper.net OTA](https://developer.flipper.net/flipperzero/doxygen/ota_updates.html)). So the region file rides along with the normal `/int` backup/restore — but only an **online** install actually (re)creates it in the first place. `(verify: whether .region_data is captured in that /int tar or pushed separately during provisioning.)`

## Enforcement: who/how/when
**Component.** Region logic lives in the firmware HAL as **`furi_hal_region`** (`furi_hal_region.h/.c`), exposing a `FuriHalRegion` structure of allowed **bands** and accessors such as `furi_hal_region_get_band()` / `furi_hal_region_is_frequency_allowed()` ([developer.flipper.net furi_hal](https://developer.flipper.net/flipperzero/doxygen/furi__hal_8h.html)). The Sub-GHz subsystem (`furi_hal_subghz` + the SubGHz app/`SubGhzEnvironment`) consults it. The whole thing — "FuriHal,SubGhz: complete region provisioning" — landed in one batch ([0.64.3 changelog](https://github.com/flipperdevices/flipperzero-firmware/releases/tag/0.64.3)).

**When.** The check fires at the **TX attempt** (pressing Send/Emulate, or a programmatic `subghz tx`), **not** when you open the Sub-GHz app or load a `.sub`. That's why the file loaded fine and only **Send** failed in our case. Receiving is never gated.

**How "blocked" is decided.** On a TX request the firmware resolves the frequency and walks the precedence: is it within the **hardware range**? within the **default/firmware band list**? present in the **region allow-list** read from `/int/.region_data`? Each "no" maps to a distinct message ([Momentum `SubGHzBypass&Extend.md`](https://github.com/Next-Flip/Momentum-Firmware/blob/dev/documentation/SubGHzBypass%26Extend.md)):

| Screen says (≈) | Meaning | Fix |
|---|---|---|
| **"Missing region file"** / *region not provisioned* | `/int/.region_data` not found | **Reinstall/update online** (Web/App/qFlipper) — *our case* |
| **"Outside region range"** / restricted in your region | File present; freq **not** allowed in your country | `SubGHz Bypass Region Lock` (if legal for you) |
| **"Outside default range"** | Freq not in the firmware's default band list | `SubGHz Extend Freq Bands` (⚠ hardware-damage risk) |
| **"Outside supported range"** | Beyond CC1101 hardware | **None** — physically impossible |

> Stock OFW shows a shorter "Transmission is blocked" + a one-line reason; Momentum rewords/expands these (its build is what printed *"Missing region file. Reinstall firmware with Web/App or bypass region."*). Exact verbatim strings differ per firmware and version `(verify)`.

## Official vs custom firmware
- **Official (OFW)** — ships the region lock on by design; **"Region-locks Sub-GHz TX and blocks transmit on restricted bands"** ([firmware/official.md](../firmware/official.md)). No in-UI bypass; the sanctioned way to change region is to update on-location.
- **Unleashed** — "removes regional Sub-GHz TX restrictions; expands frequency ranges" ([firmware/unleashed.md](../firmware/unleashed.md)). Generally ignores the region gate.
- **RogueMaster** — kitchen-sink; unlocks/ignores region like the other RF-forward forks.
- **Momentum** — region-unlocked **ranges** (~**281–361 / 378–481 / 749–962 MHz** extended) ([firmware/momentum.md](../firmware/momentum.md)) **but deliberately re-adds the region lock plus a manual bypass toggle**. Per its own docs the bypass is **off by default**, and you must "update via qFlipper/Mobile App/Momentum WebUpdater once to set up the region file" ([Momentum FAQ](https://momentum-fw.dev/wiki/FAQ/), [SubGHzBypass&Extend.md](https://github.com/Next-Flip/Momentum-Firmware/blob/dev/documentation/SubGHzBypass%26Extend.md)).

### Why did *Momentum* block us? (the puzzle resolved)
The common belief "custom firmware unlocks everything, so it can't region-block" is **only half true** — it holds for Unleashed/RogueMaster, but **Momentum keeps a real region check** (with an opt-in bypass). Two things combined on `the device`:
1. **`/int/.region_data` was absent.** The migration onto Momentum ([firmware/migration-xtreme-to-momentum.md](../firmware/migration-xtreme-to-momentum.md)) evidently didn't leave a provisioned region — the file was never written (the install path didn't run online provisioning, or `/int` came over from the old state without it). Hence **"Missing region file"**, not "outside region range." Consistent with `hardware_region_provisioned: --` that un-provisioned units report ([issue #2704](https://github.com/flipperdevices/flipperzero-firmware/issues/2704)).
2. **Bypass was off** (Momentum's default), so the missing file wasn't ignored — it became a hard block.

So Momentum behaved *exactly as designed*: region enforcement is present, our provisioning data was missing, and the safe default refused to transmit. The fix is therefore **provision** (reinstall online) **or** **bypass** (flip the toggle) — not "the firmware is broken."

## How to fix the "Missing region file" (our case)
Pick one. Order = most-correct first.

1. **Re-provision (recommended): update Momentum once via its Web Updater.** Open **momentum-fw.dev/update in Chrome**, connect `the device` over USB, install (Release channel for stability — [my-setup.md](../my-setup.md) §2). The online flow stamps your region from your IP and writes `/int/.region_data`. **No VPN.** lab.flipper.net (Chrome) is the most reliable path per community reports ([forum 16299](https://forum.flipper.net/t/new-flipper-zero-no-region/16299)). qFlipper or the mobile app also work. After it reboots, *Full Info* should show a real `hardware_region_provisioned` (e.g. `EU`/`US`) instead of `--`. `(verify menu: Settings → System → About / Full Info.)`
   - ⚠ **Wireless caveat:** provisioning needs a **USB** install — it can't be done over the BLE control link we were using ([resources/flipper-ble-control.md](../resources/flipper-ble-control.md)). Plug in for this step.
   - ⚠ **315 MHz reality:** if the server stamps an **EU** region (likely, by IP), **315 MHz still won't TX** — it's Americas-only. You'd then *also* need the bypass below (and a legal basis) for that specific Tesla `.sub`. Provisioning fixes the *"missing file"*; it does **not** by itself make 315 legal in Europe.
2. **Bypass the check (Momentum):** `Momentum → Protocols → SubGHz Bypass Region Lock` → **ON** ([Momentum FAQ](https://momentum-fw.dev/wiki/FAQ/)). This makes the firmware ignore both "missing file" and "outside region range," so the 315 MHz send proceeds. **Only do this where that transmission is legal for you** — the firmware will let you; the law still won't bend ([legal-and-safety.md](../legal-and-safety.md)).
3. **Extend bands (rarely needed here):** `Momentum → Protocols → SubGHz Extend Freq Bands` is for **"outside default range"**, not our error, and is **locked until you bypass region first**. It carries an explicit **"at your own risk of potential hardware damage"** warning (transmitting where the CC1101/antenna front-end isn't tuned). 315/433 are inside the default bands, so you don't need this for the Tesla `.sub`.

> **Bottom line for `the device`:** run a one-time **USB Web-Updater reinstall** of Momentum to clear "Missing region file." For the **315 MHz** Tesla capture specifically, if your provisioned region is EU you must additionally enable **Bypass Region Lock** *and* be on legal ground (e.g. authorized testing) before it will — and should — transmit.

## Legal, regulatory & Terms
**Why the lock exists.** Short-range devices are licence-exempt only inside specific bands/power/duty envelopes that **differ by jurisdiction**: **FCC Part 15** (US, e.g. 315/915 MHz device rules), **CE / RED 2014/53/EU + ETSI EN 300 220 + CEPT/ERC REC 70-03** (EU SRD: 433.05–434.79 and 863–870 MHz with duty-cycle ≤1%/≤0.1% and ERP caps). Transmitting on a band your country doesn't permit — even with a remote you own — can be an offence. The region lock is Flipper Devices' good-faith **radio-compliance** mechanism so the stock device is shippable/CE-FCC-defensible worldwide ([firmware/official.md](../firmware/official.md), [legal-and-safety.md](../legal-and-safety.md)).

**Responsibility model.** The firmware *permits* a bypass; it does **not** confer legal permission. "Region-unlocked firmware does NOT make transmitting legal … the responsibility shifts entirely to you" ([legal-and-safety.md](../legal-and-safety.md)). Once you flip **Bypass Region Lock**, every transmission is on you to keep within your regulator's bands/power/duty rules. Flipper's own docs and the CFWs all repeat the "at your own risk / only if you're sure it's permitted" framing.

## Legitimate uses
This is the owner's **own** device and (in the trigger) the owner's **own** Tesla charge-port signal — squarely legitimate research/personal use. Knowing the region system matters for honest, lawful operation:
- **Diagnose your own block:** read the exact wording to tell *missing file* (reinstall) from *restricted frequency* (bypass + check legality) from *unsupported* (give up) — no guesswork, no needless bypassing.
- **Travel correctly:** re-provision on-location so your device's allow-list matches where you actually are, rather than blanket-bypassing.
- **Stay compliant by default:** keep the lock on for everyday use; bypass only deliberately, for a frequency you've confirmed is legal for you (authorized testing, your own gear on a permitted band).
- **Blue-team / teaching:** demonstrate *why* RF is region-gated and how compliance is enforced in a real consumer device.

## Open questions / to research
- Exact **verbatim** OFW vs Momentum strings for each variant, and which firmware/version introduced the precise "Missing region file. Reinstall firmware with Web/App or bypass region." wording `(verify)`.
- The **on-flash format** of `/int/.region_data` and whether the allow-list also derives from **OTP** region bytes set at factory (the changelog's "add new region to OTP generator" hints OTP carries a region code too) — i.e. OTP code vs provisioned file interplay `(verify)`.
- Whether `.region_data` is included in the pre-update **`/int` tar backup** on SD, or pushed only by the online provisioning step (determines if an SD restore alone can re-create it) `(verify)`.
- The exact source symbol/path that emits the block today (e.g. `furi_hal_subghz_is_tx_allowed` / SubGHz app TX guard) on current `dev` `(verify)`.
- Confirm `the device`'s current `hardware_region` / `hardware_region_provisioned` over `device_info` (was it really `--`?), then re-test after a USB Web-Updater reinstall.
- Precise date of 0.64.3 (GitHub renders "3 years ago"; community notes say **Aug 16 2022**) `(verify)`.

## Sources
- Flipper Sub-GHz frequencies & regional allocations: https://docs.flipper.net/zero/sub-ghz/frequencies
- Firmware update (provisioning during update): https://docs.flipper.net/zero/basics/firmware-update
- OTA update process (`/int` tar backup/restore): https://developer.flipper.net/flipperzero/doxygen/ota_updates.html
- furi_hal API reference (region HAL): https://developer.flipper.net/flipperzero/doxygen/furi__hal_8h.html
- furi_hal_subghz reference: https://developer.flipper.net/flipperzero/doxygen/furi__hal__subghz_8h.html
- 0.64.3 release notes ("complete region provisioning"): https://github.com/flipperdevices/flipperzero-firmware/releases/tag/0.64.3
- Issue #2704 — region lost after update (`hardware_region_provisioned: --`): https://github.com/flipperdevices/flipperzero-firmware/issues/2704
- Forum — Region Provisioning (re-provision on update; Full Info fields): https://forum.flipper.net/t/region-provisioning/5789
- Forum — New Flipper Zero, no region? (`--`; Chrome Web Updater fixes it): https://forum.flipper.net/t/new-flipper-zero-no-region/16299
- Momentum FAQ (RX never blocked; bypass; provision once): https://momentum-fw.dev/wiki/FAQ/
- Momentum `SubGHzBypass&Extend.md` (`/int/.region_data`; 4 error variants; menu paths; band ranges): https://github.com/Next-Flip/Momentum-Firmware/blob/dev/documentation/SubGHzBypass%26Extend.md
- Momentum Protocols / SubGHz wiki: https://momentum-fw.dev/wiki/Protocols/
- Otaku Bear — compiling FW to remove the TX region restriction (background): https://www.otakubear.com/2022/11/23/flipper-zero-transmission-is-blocked-unlock-sub-ghz-region-restriction-by-compile-your-own-firmware/
- FCC Part 15: https://www.fcc.gov/general/part-15-radio-frequency-devices
- ETSI EN 300 220 (EU SRD bands, duty cycle/power): https://www.etsi.org/deliver/etsi_en/300200_300299/30022002/03.02.01_60/en_30022002v030201p.pdf
