---
title: Marauder AP Scan over MCP — the BLE-Driven Recipe
domain: wifi
type: guide
status: detailed
summary: Agent-driven AP scan — launch Marauder over the BLE MCP, run scanap, read the full network list from the SD log.
hardware: [esp32-marauder]
use_cases: [UC-31]
related: [wifi/recon-and-attacks.md, wifi/README.md, hardware/esp32-marauder-module.md, resources/flipper-ble-control.md, resources/flipper-control-playbook.md]
tags: [marauder, scanap, ble, mcp, agent-control, sd-log, recon]
last_verified: 2026-06-22
---

# Marauder AP Scan over MCP — the BLE-Driven Recipe

> **TL;DR —** To list nearby Wi-Fi from an agent: the WiFi Marauder app **seizes the USB serial**, so the USB MCP servers (`flipper`, `flipper-control`) go dead while it runs — you **must drive it over BLE** (`flipper-ble`). Recipe: pre-flight reachability → `app_launch` the `.fap` **by full path** over BLE → drive the variable-list menu (`Scan → ap → OK`) → let it sweep ~20 s (2.4 GHz, channel-hopping) → **`press back` to stop+flush** → `storage_read` the auto-saved log at `/ext/apps_data/marauder/logs/scanap_N.log` for the **full** result list (the 128×64 console only shows ~5 lines). This is the verified agent path to **scanap** (UC-31) and the reusable template for *any* USB-takeover app.
> Capability reference: [recon-and-attacks.md](recon-and-attacks.md) · board [../hardware/esp32-marauder-module.md](../hardware/esp32-marauder-module.md) · BLE method [../resources/flipper-ble-control.md](../resources/flipper-ble-control.md) · driving algorithm [../resources/flipper-control-playbook.md](../resources/flipper-control-playbook.md). Part of the [Wi-Fi hub](README.md) · [KB](../README.md).

## What this is
A **worked, end-to-end recipe** for getting "what Wi-Fi networks are around me" out of the ESP32 Marauder **when an AI agent is driving the Flipper over MCP** — not a human tapping the buttons. The *what scanap does* lives in [recon-and-attacks.md §1](recon-and-attacks.md) (UC-31); this doc is the *how to actually run it through the toolkit and get the data back out*, including the non-obvious traps that cost time the first time. **Authorized networks only** — though a passive AP scan is the most benign thing the board does (see [Legitimate uses](#legitimate-uses)).

## The one constraint that dictates everything
**The Marauder app takes over the Flipper's USB serial.** While it's open, every USB-path MCP tool stops responding:

| Server | Transport | While Marauder runs |
|---|---|---|
| `flipper` (read-only) | USB CDC | ❌ dead (Marauder owns the port) |
| `flipper-control` (gated control) | USB CDC | ❌ dead — `screenshot`/`press` explicitly refuse |
| **`flipper-ble`** (wireless RPC) | **BLE** | ✅ **works** — this is your only live channel |

So the whole workflow runs over **BLE**: launch, navigate, screenshot, *and* the final log read all go through `flipper-ble`. (USB, if connected, is still useful **before** launch and **after** exit — e.g. a robust large-file `storage_read` — but not during.) The BLE method, daemon, and tool list are documented in [flipper-ble-control.md](../resources/flipper-ble-control.md).

## Discovery & planning (how this was figured out)
The reusable *method*, not just the result:

1. **Surface the tools.** The `mcp__flipper*__*` tools arrive **deferred** — only names are listed until you fetch schemas. Pull them with **ToolSearch** (`"flipper wifi marauder scan"`, then `select:…` for the specific ones). Three servers appear: `flipper` (USB read), `flipper-control` (USB control), `flipper-ble` (wireless).
2. **Read the tool descriptions first** — the USB-takeover warning is written **right in** the `flipper-control__screenshot`/`press` descriptions. That single line is what forces the BLE plan; reading it up front avoids a dead end.
3. **Pre-flight the transports** (reachability *ladder*, cheap → telling): `mcp__flipper__status` (USB up?) and `mcp__flipper-ble__ping` / `scan` (BLE up?). BLE has **one central at a time** — if the user's *phone* holds the Flipper, BLE says *not found*; they must free the phone's app.
4. **Call `playbook` once.** `mcp__flipper-ble__playbook` returns the data-first driving algorithm + menu conventions — orient before pressing buttons.
5. **Data-first, screenshot-last.** Prefer structured reads (`storage_list`, `storage_read`) over driving pixels. The screen is just a framebuffer; the *real* scan output is a file on SD. That realization is what makes the result usable.

## The recipe (verified 2026-06-22, Momentum + Marauder)

### 0. Pre-flight
```
mcp__flipper-ble__ping              → PING_OK
mcp__flipper-ble__desktop_is_locked → DESKTOP UNLOCKED
mcp__flipper-ble__app_lock_status   → APP_LOCK free      # nothing else running
```
If `app_lock_status` shows an app, close it first (`app_exit`, or `press back` for a file-launched app).

### 1. Locate the `.fap`
```
mcp__flipper-ble__storage_list  /ext/apps/GPIO
  → … esp32_wifi_marauder.fap (117036) …
```
On this rig the Marauder companion app is `/ext/apps/GPIO/esp32_wifi_marauder.fap`.

### 2. Launch it over BLE — by full path
```
mcp__flipper-ble__app_launch  name="/ext/apps/GPIO/esp32_wifi_marauder.fap"  then_screenshot=true
```
Passing the **full `.fap` path** as `name` makes the loader resolve the external app directly (no registry-name guessing, same trick as the JS-runtime launch in the [playbook](../resources/flipper-control-playbook.md)). It **fails if an app is already running** (step 0) — and because it's *file-launched*, you later exit with **`press back`**, not `app_exit` (which returns `ERROR_APP_NOT_RUNNING` 21 for loader-owned apps).

### 3. Drive the menu — it's a VariableItemList
The main screen is a **variable-item list**: each row has a label and a **right-side value you cycle with ◀/▶**, and **OK runs that row's command**. On this build the rows are `View Log from [start]`, **`Scan [all]`**, `SSID [add rand]`, `List [ap]`, … Set Scan to **ap** and run it:
```
press down            # move to the "Scan" row
press right           # cycle value: "all" → "ap"   (◀ is a no-op at the left end; "all" is first)
press ok              # runs `scanap` → switches to the live console
```
Use `then_screenshot=true` on each press to verify (this UI is dynamic → screenshot-loop territory). A correct start shows:
```
#scanap
Starting AP scan. Stop with stopscan
Clearing APs...0
>
```
`#scanap` echoing back also **confirms the ESP32 is attached and responding** (no "waiting for ESP32").

### 4. Let it sweep
`scanap` **channel-hops** the 2.4 GHz band, adding each unique BSSID to the ESP32's in-RAM AP list and streaming beacon lines to the console. **~15–25 s** gives good coverage of channels 1–11+; strong/near APs appear in the first few seconds. Beacons are passive — nothing is transmitted.

### 5. Stop — `press back` (this flushes the log)
```
press back  then_screenshot=true   # returns to the menu
```
Leaving the scan scene **sends `stopscan` automatically** (verified: `#stopscan` is appended to the log) **and flushes the log file** to disk.

### 6. Read the full result list from SD
Logging is on when `/ext/apps_data/marauder/save_logs_here.setting` exists. Each `scanap` session writes a **numbered** log:
```
mcp__flipper-ble__storage_list  /ext/apps_data/marauder/logs
  → scanap_0.log (1512)   scanap_1.log (0)   …        # newest = highest N
mcp__flipper-ble__storage_stat  /ext/apps_data/marauder/logs/scanap_1.log
  → FILE 1525 bytes                                    # >0 ⇒ flushed (was 0 mid-scan)
mcp__flipper-ble__storage_read  /ext/apps_data/marauder/logs/scanap_1.log
```
> ⚠️ **Buffering gotcha:** mid-scan the active log reads **0 bytes** — the output is buffered in RAM and only sized/flushed when the scan scene closes (step 5). Always **stop first, then read.** This resolves the "does my build persist lists to SD?" `(verify)` in [recon-and-attacks.md §1](recon-and-attacks.md) — on Momentum it **auto-saves** to `scanap_N.log`, no manual save needed. (BLE `storage_read` caps ~8 KB and can time out on large files — for a very long scan, pull it over the USB `flipper` server after exiting Marauder.)

## Parsing the `scanap` log
Two line types: **AP records** and **`Beacon:` counter lines** (ignore the latter). Example (BSSIDs anonymized):
```
> RSSI: -56 Ch: 8 BSSID: aa:bb:cc:11:22:33 ESSID: Keenetic-home
Beacon: 11 18 11 100596
RSSI: -90 Ch: 7 BSSID: 92:32:e5:17:7e:1d ESSID: ␀␀␀…              # null SSID = hidden
RSSI: -86 Ch: 4 BSSID: 7e:20:51:33:f4:0a ESSID:  7e:20:51:33:f4:0a # ESSID==BSSID = not broadcasting
#stopscan
```
Field map: `RSSI:` dBm · `Ch:` 2.4 GHz channel · `BSSID:` radio MAC · `ESSID:` network name.

**Reading it:**
- **Signal (RSSI):** −30→−60 = 🟢 strong/near · −60→−80 = 🟡 usable · −80→−95 = 🔴 weak/distant. Most neighbor APs land −85 or weaker.
- **Hidden / non-broadcast:** `ESSID` printed as **null bytes** or **equal to the BSSID** ⇒ the AP isn't advertising a name.
- **Virtual / guest / mesh radios:** a **locally-administered** BSSID — 2nd hex digit of the first octet ∈ `{2,6,A,E}` (e.g. `7e:`, `92:`, `52:`) — is a software-derived BSSID, typically a guest SSID or mesh backhaul paired with a "real" (universally-administered) AP that differs by a bit or two. Group these under their parent.
- **De-dup by SSID:** one network often appears as several BSSIDs (multi-band, mesh nodes, guest). Collapse same-ESSID rows; note the count of radios.

## Caveats & gotchas (all verified this session)
- **2.4 GHz only.** The ESP32-WROOM radio **cannot see 5 GHz / 6 GHz** APs at all — a `…- 2,4 GHz`-suffixed SSID hints at a 5 GHz twin you won't capture.
- **No encryption field.** `scanap`'s output is RSSI/Ch/BSSID/ESSID — **no WPA2/WPA3/open** hint. Security type needs a different view/capture.
- **Console ≠ data.** The 128×64 screen shows ~5 scrolling lines; never try to read the full list from screenshots — use the SD log.
- **Log flush** only on scene exit (see step 5/6).
- **One BLE central.** Phone connected ⇒ Mac can't; free the phone's Flipper app.
- **Exit** a file-launched app with `press back`, not `app_exit`.

## Why this is reusable
The shape generalizes to **any Flipper app that monopolizes the USB serial** (other ESP32 apps — Ghost ESP, Bruce; UART-terminal apps): **drive it over BLE, and read its results from the app's `apps_data` log/PCAP on SD rather than off the screen.** The template:
> pre-flight BLE → `app_launch` by full `.fap` path → drive the menu (screenshot-verify) → let it run → `press back` to stop+flush → `storage_read` the SD artifact → parse.
Pairs with [flipper-control-playbook.md](../resources/flipper-control-playbook.md) (the generic driving algorithm) and [flipper-ble-control.md](../resources/flipper-ble-control.md) (the BLE server internals).

## Legitimate uses
A passive AP scan only **listens to beacon frames every AP already broadcasts** — the same thing a phone's Wi-Fi list does. No frames are injected; legal risk on its own is low. Genuine uses: **site survey** (find a clean channel, see what's congesting the band), **inventory your own APs/mesh nodes**, locate a rogue/unknown SSID, or build the target list a self-audit needs ([own-network-audit.md](own-network-audit.md)). Active steps (deauth, spam, evil portal) are *not* this — see [recon-and-attacks.md](recon-and-attacks.md) and [../legal-and-safety.md](../legal-and-safety.md).

## Open questions / to research
- Full **Scan value cycle order** beyond `all → ap` (does `station`/`all` follow? wraps?) — and the complete main-menu row list for this build.
- Does the **`List → ap`** menu item re-dump the in-RAM list to the *same* `scanap_N.log`, or a new file? (Could give a clean enumerated list without re-scanning.)
- Marauder **channel-hop dwell/period** on this firmware — to pick an optimal scan duration.
- Whether a longer scan's log reliably exceeds the **BLE ~8 KB** read cap (→ force USB read) and where the practical limit sits.
- Confirm the `save_pcaps_here.setting` / `pcaps/` path for the **sniff→PCAP** flow ([recon-and-attacks.md §2](recon-and-attacks.md)) under the same BLE-driven model.

## Sources
- This session (2026-06-22): live `app_launch` → `Scan ap` → `scanap` → `press back` → `storage_read /ext/apps_data/marauder/logs/scanap_1.log` over `flipper-ble`, on the owner's Momentum + ESP32 Marauder rig.
- Marauder `scan-aps` wiki: https://github.com/justcallmekoko/ESP32Marauder/wiki/scan-aps
- BLE MCP method + tool list: [../resources/flipper-ble-control.md](../resources/flipper-ble-control.md) · driving algorithm: [../resources/flipper-control-playbook.md](../resources/flipper-control-playbook.md)
- Board: [../hardware/esp32-marauder-module.md](../hardware/esp32-marauder-module.md) · capability reference: [recon-and-attacks.md](recon-and-attacks.md)
