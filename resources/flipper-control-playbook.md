---
title: Flipper Control Playbook (AI operating manual)
domain: resources
type: guide
status: detailed
summary: How an AI agent should drive the Flipper via the MCP toolkit — data-first algorithm, menu maps, app-entry recipes, conventions.
hardware: [flipper-internal]
use_cases: []
related: [resources/flipper-ble-control.md, resources/flipper-control-mcp-server.md, resources/flipper-read-mcp-server.md, topics/subghz-region-lock.md, frontier-roadmap.md]
tags: [mcp, ble, device-control, automation, menu-map, playbook, rpc]
last_verified: 2026-06-22
---

# Flipper Control Playbook (AI operating manual)

> **TL;DR —** The Flipper exposes **structured data** over RPC (files, device/power info, app flags) but **no UI tree** — the screen is just a 1024-byte framebuffer. So drive it **data-first, screenshot-last**: climb to the highest rung that reaches the goal — (1) pure data, (2) direct app/file entry, (3) semantic action, (4) batched blind navigation, (5) screenshot loop (only for unknown/dynamic UI). Each BLE call ≈ 6–10 s, so **optimize round-trips, not presses**: batch with `press_sequence`, screenshot only to verify the landing. This doc has the verified **menu maps + recipes** so navigation stays on rungs 1–4. Also served live by the `playbook` MCP tool. Toolkit: [flipper-ble-control](flipper-ble-control.md) · [control server](flipper-control-mcp-server.md) · [read server](flipper-read-mcp-server.md). Part of the [KB](../README.md).

## The one constraint
RPC gives **no structured access to the UI** — no widget list, no "current menu items," just pixels. Whenever a goal is reachable through **data** or a **direct entry point**, you skip slow, ambiguous pixel-reading entirely. The framebuffer (screenshot + vision) is the *only* UI introspection, so treat it as the fallback, not the default.

## Cost model
One tool call = one BLE **connect → act → disconnect ≈ 6–10 s** (+ an auto-retry if the phone holds the radio). The scarce resource is **round-trips**, not button presses → batch presses; screenshot rarely.

## The algorithm — climb to the highest rung that works
1. **Pure data** — `storage_read/list/stat/info/md5`, `device_info`, `power_info`. Read/write/inspect directly. (Read a `.sub`? `storage_read` — never navigate Sub-GHz → Saved → file.)
2. **Direct app/file entry** — `app_launch(name)`, `app_launch(name, args=<file>)`, `app_load_file`. Jump into an app, or straight to a file's screen (Tesla send screen in **one call** vs ~5 hops).
3. **Semantic action** — `app_button(name)`, `transmit_subghz/infrared`. Named action, no pixel navigation.
4. **Batched blind navigation** — `press_sequence("down down ok")` + a single trailing `+shot`. Known path → all moves in one connection, verify the landing once.
5. **Screenshot loop** — unknown/dynamic UI only (variable lists, confirm dialogs, errors): `screenshot → read → press(+shot)`, re-screenshotting only at unpredictable decision points.

**Verify cheaply:** a trailing `+shot` on the *last* press of a sequence, or a state query (`app_lock_status`, `desktop_is_locked`) — not a screenshot after every press.

## Verified menu maps `(verify per firmware version)`
*(observed on `the device`, Momentum `mntm-dev` build 8ed809fb — layouts can shift across firmware/versions; re-confirm with a screenshot if a step lands wrong.)*

- **Desktop → main menu:** `press ok` opens the horizontal **carousel**. `Start` (dolphin) is leftmost; apps in the middle; **`MNTM` (Momentum) and `Settings` are at the far right**. `press left` from `Start` **wraps to the end** (Settings, then MNTM) — faster than scrolling right. `back` returns to desktop.
- **Momentum settings:** main menu → `left left` (lands on `MNTM`) → `ok` → submenus **`Interface` / `Protocols` / `Misc`** (vertical list; `up/down` + `ok`).
- **Protocols submenu:** `SubGHz Freqs` / **`SubGHz Bypass Region Lock`** (inline toggle) / `SubGHz Extend Freq Bands` (🔒 locked until bypass is ON) / `GPIO Pins`.
- **Region-bypass recipe (one path):** from desktop →
  `press_sequence("ok left left ok down ok down right")` → lands on the **"Are you sure?"** confirm dialog → read it → `press right` (= **Yes**). Backing fully out of settings saves it. (See [subghz-region-lock](../topics/subghz-region-lock.md) for *why*.)

## App-entry recipes
- `app_launch("NFC")` → NFC menu (Read / Extract MFC Keys / Saved / Extra Actions).
- `app_launch("Sub-GHz")` → Sub-GHz menu (Read / Read RAW / Saved / Add Manually / …).
- `app_launch("Sub-GHz", args="/ext/subghz/…/X.sub")` → **transmitter/send screen** for that file (shows `freq preset R:Int RAW` + `🔘 Send`; region permitting). Pressing `ok` transmits — gated.
- `app_launch("Infrared", args="/ext/infrared/X.ir")` → the remote's **button list**; `press right` to select, `press ok` to fire that button — gated.
- Exact app **names** come from the USB read server's `app_list` (or `loader list`): e.g. `NFC`, `Sub-GHz`, `125 kHz RFID`, `Infrared`, `GPIO`, `iButton`, `Bad USB`, `U2F`.

## Deploy & run a JS app (mJS) — autonomous build → install → run
The `js_app` runtime runs `.js` (mJS) scripts — **no compile/SDK**. To deploy one wirelessly:
1. **Write** the script — modern event-loop mJS (`require("event_loop")`, `require("gui")`, `gui/dialog`, `storage`, `notification`, `gpio`…). Copy patterns from the on-device examples in `/ext/apps/Scripts/Examples/*`.
2. **Upload:** `storage_write("/ext/apps/Scripts/<name>.js", content=…)` (small files only — multi-message writes are rejected by this firmware, so keep under ~2 KB or use USB).
3. **Run:** `app_launch("/ext/apps/assets/js_app.fap", args="/ext/apps/Scripts/<name>.js")` — launch the JS runtime by its **full `.fap` path** with the script as the arg. (The appid `"js_app"` is rejected → `ERROR_INVALID_PARAMETERS`; the `.fap` path works. This is also the general pattern for launching any external FAP by path + arg.)
4. **Verify:** `screenshot`; exit with `press("ok")` / `press("back")`.

Proven 2026-06-22 (the "Hello from Claude" dialog — M4 JS milestone).

## Guided capture & diagnostics
- **Read-and-save a card/signal** — NFC/RFID/Sub-GHz *can't* read+save headless over BLE (no read RPC, and the on-device Save needs keyboard text-entry for the filename). So: `app_launch` the reader (e.g. `app_launch("NFC")` → Read), have the **user physically tap + Save** on the device, then **`read_latest("/ext/nfc")`** (or `/ext/lfrfid`, `/ext/subghz`, `/ext/infrared`) pulls the newest saved file by `storage_timestamp`.
- **`selftest`** — daemon up? BLE connected? ping RTT? cached-device + idle state. Call it to debug "is the wireless toolkit healthy?" (read-only, doesn't force a connect).

## Input / widget conventions
- **Carousel** (main menu): `left/right` move · `ok` enter · `back` → desktop.
- **Vertical list/menu**: `up/down` move · `ok` enter · `back` up one level.
- **Inline toggle** ("X … OFF"): `right` (or `left`) changes the value; may raise a confirm dialog.
- **DialogEx** (`◄ No` … `Yes ►`): `press left` = left button, `press right` = right button (acts immediately); a center `ok` = the middle button if present.
- **Settings persist** when you exit the settings app (back all the way out).

## Key device behaviors (verified this session)
- **Apps launched via RPC persist across BLE disconnects** → open in one call, press in the next; multi-call navigation works.
- **`app_exit` only closes a *plainly* RPC-launched app**; for a **file-launched** app it returns `ERROR_APP_NOT_RUNNING (21)` (it's loader-owned) → exit with `press back`.
- **One BLE central at a time** — if the **phone** holds the Flipper, calls report *device not found*; free the phone's Flipper app. The action tools **auto-retry once**.
- **`scan` is a reachability probe**, not a routine first step — use it only when calls fail.
- The screen may **dim/sleep** between calls; a press may just wake it — screenshot to confirm state if unsure.

## Legitimate uses
Operating **your own** Flipper efficiently from an AI agent: reading your own saved data, driving menus, launching apps, and (on your own targets, legal bands) transmitting your own captures. The gates (per-call approval, RF "own targets only") still apply — this playbook is about *efficiency*, not bypassing the safety model.

## Open questions / to research
- How stable are these menu indices across Momentum releases (does `Protocols` stay 2nd, `Bypass` stay 2nd)? Re-verify after each firmware update `(verify)`.
- Whether a compact, machine-readable menu map (JSON of paths) is worth maintaining for fully-blind navigation.
- Whether `app_button` arg names can be enumerated per app (would turn rung-3 into a lookup rather than a guess).

## Sources
- Empirical: this project's live BLE-control sessions on `the device` (2026-06-21/22) — menu maps, app-entry behavior, and the region-bypass path were screenshot-verified.
- Toolkit + recipes: [flipper-ble-control](flipper-ble-control.md), [flipper-control-mcp-server](flipper-control-mcp-server.md), [flipper-read-mcp-server](flipper-read-mcp-server.md).
- Region mechanics: [subghz-region-lock](../topics/subghz-region-lock.md).
