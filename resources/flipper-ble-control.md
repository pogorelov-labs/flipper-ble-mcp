---
title: Controlling the Flipper over BLE — Wireless RPC (Solved)
domain: resources
type: reference
status: detailed
summary: Wireless Flipper control SOLVED — read/see/drive/launch/file-read over BLE via the flipper-ble MCP server.
hardware: [flipper-internal]
use_cases: []
related: [resources/flipper-control-mcp-server.md, resources/flipper-read-mcp-server.md, resources/mcp-setup-claude-code.md, bluetooth/README.md, frontier-roadmap.md]
tags: [ble, bluetooth, rpc, bleak, wireless-control, input-injection, mcp, macos-tcc]
last_verified: 2026-06-21
---

# Controlling the Flipper over BLE — Wireless RPC (Solved)

> **TL;DR — ✅ SOLVED (2026-06-21/22):** the Flipper speaks the **same protobuf RPC over BLE** as over USB, and we got it working from the Mac — `device_info` read **wirelessly** (60 fields) **and the screen captured live** (1024-byte framebuffer → PNG, fully decoded). We then added **button/input injection** (drive the whole UI over BLE) and wrapped it all as the **`flipper-ble` MCP server** — a fully wireless `flipper-control` equivalent (read + see + drive, no cable). Two non-obvious keys: (1) run the Python inside a **signed app-bundle** launched via `open` (so macOS lets it touch Bluetooth — Claude.app itself lacks the BT entitlement), and (2) **do NOT send `start_rpc_session`** over BLE — the BLE serial service is *already* in RPC mode, so the text command corrupts the stream; send the protobuf request directly. Recipe below; full debugging journey (TCC, arch, notification delivery, dead ends) further down.
> Control over USB: [flipper-control-mcp-server](flipper-control-mcp-server.md) · reads: [flipper-read-mcp-server](flipper-read-mcp-server.md) · BLE hub: [bluetooth](../bluetooth/README.md). Part of the [KB](../README.md).

## ✅ The working recipe (macOS, agent-launched)
Every layer that had to be right:
1. **TCC:** run the BLE code inside an **app-bundle** ([`~/flipper-ai/FlipperBLE.app`](file://~/flipper-ai/FlipperBLE.app)) whose Info.plist has `NSBluetoothAlwaysUsageDescription`, **launched via `open`** so it's its own TCC principal (Claude.app can't carry the BT entitlement). An MCP tool can `open -W FlipperBLE.app` — Bluetooth happens *inside* the app.
2. **Arch:** the bundle launcher uses **`arch -arm64`** (`open` ran Python x86_64 under Rosetta; numpy/PIL/protobuf are arm64).
3. **Connect:** **scan-then-connect** — discover first with a `BleakScanner` **detection-callback that early-exits** on an address-or-name match, then `BleakClient(dev)` (a cold `BleakClient(addr)` raises *device-not-found* on macOS; `find_device_by_address` works but is flaky/intermittent on CoreBluetooth, and plain `discover()` always waits the full timeout).
4. **Notifications:** subscribe RX (`…61fe`, indicate) with `cb={"notification_discriminator": lambda d: True}` **on the main-thread asyncio loop** (background-thread loop = silent; macOS CoreBluetooth shares one callback for read+notify, so the discriminator is mandatory for read+notify chars).
5. **RPC init:** **send nothing** — *no* `start_rpc_session`. The BLE channel is already in RPC mode; the text command desyncs the parser (the single bug that cost the most time).
6. **Request / parse:** write the protobuf request **write-without-response** to TX (`…62fe`); each RX notification is one length-delimited `PB_Main`; parse until `has_next=0`. (`device_info` request bytes = `050801820200`.)
7. **Screenshot (✅ working):** same path with the **GUI screen-stream request** (`050801a20100`). The frame arrives as a `PB_Main` whose `ScreenFrame.data` field is marked **`0a 80 08`** (field 1, wire-type 2, varint length **1024**) followed by the **1024-byte framebuffer** (128×64, 8-page column-major). Reassemble RX notifications, find the marker, slice 1024 bytes, decode pages→bits→PNG. Confirmed wirelessly: the Momentum desktop rendered cleanly.
8. **Input injection (✅ working):** send `gui_send_input_event_request` (PB_Main **field 22**). Emulate a tap as the event triple **PRESS → SHORT → RELEASE** (swap SHORT→**LONG** for a long-press); keys `UP/DOWN/LEFT/RIGHT/OK/BACK`. Build with the protobuf lib — e.g. OK-short = `070801ba01020804` (press) · `090801ba010408041002` (short) · `090801ba010408041001` (release). With **input + screenshot** you can drive *anything* the UI exposes = a fully wireless control loop. Verified live: OK→main menu, BACK→desktop, `ok right`→menu scrolled to SubGHz.

Tool: [`ble_worker.py`](file://~/flipper-ai/ble_worker.py) — `scan` / `info` / `screenshot` / `press` **all working**, wrapped by the **`flipper-ble` MCP server** (see below). Driven via `open -W FlipperBLE.app --args <cmd>`, output → `~/flipper-ai/ble_result.txt` (screenshot → `~/flipper-ai/ble_screen.png`). macOS finder detail: scan with a **detection-callback + early-exit, matching by address OR name** (`find_device_by_address` is flaky on CoreBluetooth; plain `discover()` always waits the full timeout).

## The wireless MCP server (`flipper-ble`)
[`flipper_ble_server.py`](file://~/flipper-ai/flipper_ble_server.py) (FastMCP; registered in `~/.claude.json` → `mcpServers.flipper-ble`, loads on Desktop restart). It talks to a **resident BLE daemon** ([`flipper_bled.py`](file://~/flipper-ai/flipper_bled.py)) over a Unix socket; the daemon runs inside `FlipperBLE.app` (`open FlipperBLE.app --args daemon`) holding **one persistent BleakClient**, so the server process itself **never touches Bluetooth** (BT lives in the `.app`, its own TCC principal) and per-call latency drops from ~6–10 s to **~0.1–1.5 s** (only the first connect costs ~6–25 s). The MCP server auto-spawns the daemon on cold start. See [the daemon section](#the-persistent-daemon-phase-2--speed-layer) below. Tools:

**38 tools** — 37 spanning the full BLE-reachable RPC surface (system / storage / gui / app / desktop / **gpio**) plus the M5 `healthwatch` scheduler switch. Only **LED and vibro** are truly CLI-only — **GPIO IS in the RPC schema** (`gpio_read`/`gpio_write`/`gpio_set_mode`; verified live: `gpio_read PC0` → `ERR 58 ERROR_GPIO_MODE_INCORRECT`, correcting an earlier note). *Raw* IR/Sub-GHz TX are CLI-only, but **RF transmit IS reachable via the app-driven path** (`transmit_subghz` / `transmit_infrared`, below); `find_my_flipper` (beep+flash) is the one built-in output RPC fires directly. Tools are tagged `readOnlyHint`/`destructiveHint` for the approval UI; data tools carry the full `CommandStatus`→message map.

**Read-only / diagnostics (safe):**
| Tool | RPC |
|---|---|
| `scan` | BLE discovery — is it advertising? |
| `device_info` | `system_device_info` — 60+ fields |
| `power_info` | `system_power_info` — battery V / mA / °C / % / health |
| `ping` | `system_ping` — liveness + echo |
| `get_datetime` | `system_get_datetime` — RTC |
| `desktop_is_locked` | `desktop_is_locked` — PIN-lock state |
| `app_lock_status` | `app_lock_status` — is an app running? |
| `screenshot` | `gui_start_screen_stream` → PNG (the eyes) |
| `storage_list` | `storage_list` — dir listing (dirs tagged, files sized) |
| `storage_read` | `storage_read` — file → text/binary (multi-msg reassembly) |
| `storage_stat` | `storage_stat` — type + size |
| `storage_info` | `storage_info` — free / total space |
| `storage_md5` | `storage_md5sum` — file hash |
| `app_get_error` | `app_get_error` — the running app's last error, as text |
| `gpio_read` | `gpio_read_pin` — read a GPIO pin (PC0/PC1/PC3/PB2/PB3/PA4/PA6/PA7) |
| `selftest` | daemon + BLE health, ping RTT, cached-device/idle state (diagnostics; no forced connect) |
| `read_latest` | read the newest saved file in a folder by `storage_timestamp` — pull a just-saved capture |

**Control / gated (real actions — approve per call):**
| Tool | RPC |
|---|---|
| `press` / `press_sequence` | `gui_send_input_event` — UI button / macro (opt `+shot`) |
| `app_launch` | `app_start` (field 16) — open an app by name (opt `args` = a file path to open directly) |
| `transmit_subghz` | ⚠️ launch Sub-GHz **with a .sub** → drives straight into transmit (RF; region-gated) |
| `transmit_infrared` | ⚠️ launch Infrared **with a .ir** → button list; `press ok` fires the selected button |
| `app_exit` | `app_exit` — close a *plainly* RPC-launched app (file-launched apps: use `press back`) |
| `app_load_file` | `app_load_file` — load a file into an already-running app |
| `app_button` | `app_button_press`/`release` — named in-app button |
| `set_datetime` | `system_set_datetime` — set RTC (sync to Mac) |
| `find_my_flipper` | `system_play_audiovisual_alert` — beep + flash |
| `storage_write` | `storage_write` (chunked) — upload text or a local file |
| `storage_mkdir` / `storage_delete` / `storage_rename` | dir create / delete (recursive opt) / move |
| `desktop_unlock` | `desktop_unlock` — clear the desktop lock (swipe-lock) |
| `reboot` | ⚠️ `system_reboot` — OS / DFU / UPDATE (recovery when wedged) |
| `gpio_write` / `gpio_set_mode` | `gpio_write_pin` / `gpio_set_pin_mode` — drive / configure a pin |
| `run_badusb` | ⚠️ upload+launch a DuckyScript payload and run it (HID keystrokes into the USB-attached host) |
| `healthwatch` | M5 — manage the scheduled **read-only** health-watch: `status` / `on` / `off` / `run` (default-off; 3×/day when on) → [flipper-healthwatch](flipper-healthwatch.md) |

Verified live over BLE: **write round-trip** (mkdir→write 82 B→read-back→delete→confirm-gone); `storage_md5` matched a **local** hash of the read bytes exactly; `power_info` (12 fields); `desktop_is_locked` (status 1 = unlocked); `find_my_flipper` beeped; `app_exit` correctly reported "no app". **Caveats:** `storage_read`/`write` reassemble across messages but **large files may time out over BLE → use USB**; `app_load_file`/`app_button` need the matching app already running; `press`/`app_launch` default to `+shot` (drive *then see*). This is the wireless twin of the USB [`flipper-control`](flipper-control-mcp-server.md). Only **LED/vibro** lack a BLE path (CLI-only); **GPIO** is reachable (`gpio_*` RPC) and **RF transmit** via the app-driven path (below), not raw CLI TX. **One BLE central at a time** — if the **phone** holds the Flipper, calls say *device not found*; free the phone's app. Transient not-advertising is auto-retried once.

## App-driven RF transmit (the only TX path over BLE)
There is **no direct IR/Sub-GHz TX RPC** — transmit happens by driving the app (via `app_start` with the file as its launch `args`):
- **Sub-GHz:** `transmit_subghz(path)` launches Sub-GHz with the `.sub` as its arg → goes **straight into transmit**. ⚠️ On *this* device it hits **"Transmission is blocked — missing region file"** (a Momentum region lock; fixable on-device, not in tooling — so RF doesn't actually leave until that's resolved).
- **Infrared:** `transmit_infrared(path)` launches Infrared with the `.ir` → the remote's **button list** (verified: Samsung remote, POWER/Up/Down/…); fire a button with a follow-up `press ok` (navigate with `press right` first).
- **Key behavior (verified):** RPC-launched apps **persist across BLE disconnects** — opened a remote, reconnected 3× over separate calls, still there — so *open-then-press across separate tool calls works*. And **`app_exit` returns `ERROR_APP_NOT_RUNNING` (21) for file-launched apps** (they're loader-owned, not RPC-owned) → exit them with `press back`, not `app_exit`.
- ⚠️ Real RF — **your own targets, legal bands only.**

## The persistent daemon (Phase 2 — speed layer)
The original model shelled `open -W FlipperBLE.app --args <cmd>` **per call** — a full scan→connect→work→disconnect each time (~6–10 s). A deep-research pass found the real win: the firmware's `StartScreenStream` **pushes a frame on every redraw** (`rpc_gui.c`), i.e. the per-call reconnect is architectural, not inherent. So we built a **resident daemon** ([`flipper_bled.py`](file://~/flipper-ai/flipper_bled.py)):
- Runs inside `FlipperBLE.app` (`open FlipperBLE.app --args daemon`, routed via `ble_worker.DISPATCH["daemon"]`), holds **one** `BleakClient`, serves a **Unix socket** (`~/flipper-ai/bled.sock`, newline-JSON `{cmd,args}`). The MCP server's `_run_worker` now talks to that socket (same `(text, png)` contract → all 34 tools unchanged), **auto-spawning** the daemon on cold start.
- **Latency:** status/list/read **~0.1–0.3 s**, screenshot/press **~1.5 s** (was ~6–10 s/call); first connect ~6–25 s one-time; **idle-disconnect after 180 s** frees the radio for the phone (auto-reconnect on next call).
- **Correctness machinery (hard-won):** (1) **command-ID demux** — each command is tagged a unique `command_id` (2–121) and responses are filtered to it, so stragglers from a prior command can't corrupt the next; (2) **screen-frame demux** — `gui_screen_frame` pushes are filtered out of command parsing; (3) **post-screenshot quiesce** — after grabbing a frame, send `gui_stop_screen_stream_request` and wait for the channel to go quiet before the next command (the stream floods otherwise); (4) **command serialization** (`_cmd_lock`). `ble_worker.py` was made importable (dispatch → `DISPATCH` dict + `__main__` guard) so the daemon reuses its verified builders/parsers — single source of truth.
- **One central still applies:** while the daemon holds the link, the phone can't; the idle-disconnect is the release valve.
- **Round-2 research hardening (2026-06-22):** cached-`BLEDevice` reconnect (skips the re-scan after an idle-disconnect — only the *first* connect pays the ~6–25 s scan floor; macOS gives no shortcut there); **flock singleton** (racing cold-start spawns lose the lock and exit); the idle-watcher takes `_cmd_lock` so it never disconnects mid-command; a mid-command link drop returns "connection lost" and auto-retries once; `command_id=0` push frames are demuxed out of command parsing; and a **<0.4 s screenshot cache** makes repeat screenshots instant. `device_info` / `power_info` now return typed `{field: value}` maps (FastMCP structured output). Deferred: a permanently-on cached stream (low marginal value — `press` already `+shot`s; permanent stream would flood), push-events (needs a protobuf regen + a command_id=0 consumer), and deleting the now-dead per-call `do_*` functions in `ble_worker.py` (harmless/unreachable; pure hygiene).
- **Round-4 additions (2026-06-22):** `selftest` (daemon/BLE diagnostics + ping RTT — verified ~42 ms warm) and `read_latest(folder)` (newest file by `storage_timestamp` — pull a just-saved capture; pairs with the guided read-and-save flow: launch the reader → user taps + Saves on-device → `read_latest`). The full **protobuf regen** (push events / `include_md5` / `app_button` index) was deliberately **not done** — modest value vs real breakage risk to the working bindings, and the fast polls (`desktop_is_locked`/`app_lock_status` ~0.1 s) already cover the equivalents. Now **37 tools**.
- **`storage_write` fix (2026-06-22):** this firmware **rejects the multi-message write continuation** (an empty-path continuation chunk → `ERROR_STORAGE_INVALID_NAME`, file truncates at 512 B). Fix: the single-message chunk was bumped to **2048 B** (+ reliable write-with-response), so small files (scripts/configs/small captures) upload in one `storage_write_request`; files >~2 KB still need USB.
- **M4 (autonomous app), JS half done (2026-06-22):** Claude wrote → uploaded → ran a JS (mJS) app over BLE and verified by screenshot. Recipe: `app_launch("/ext/apps/assets/js_app.fap", args="<script>.js")` (launch the JS runtime by **full .fap path** + script arg — the appid is rejected). See [flipper-control-playbook](flipper-control-playbook.md#deploy--run-a-js-app-mjs--autonomous-build--install--run).
- **Security hardening (2026-06-22):** the daemon's Unix socket is now **`0600` (owner-only)** plus a **shared-token check** — the daemon reads-or-creates `~/flipper-ai/bled.token` (0600) and rejects any request whose `token` doesn't match (verified: raw no-token / bad-token probes → `unauthorized`; the MCP server reads the token and includes it on every call). Blocks other local users (0600 socket) and opportunistic same-user processes (token). Threat model is **local-only** (Unix socket, not network). ⚠️ This is a server change → **a Desktop restart is REQUIRED**: the old in-memory server sends no token, which the new token-daemon will reject.
- **M5 health-watch (2026-06-22):** added `healthwatch` — the on/off switch for a **gated, default-off, scheduled read-only monitor** (`flipper_healthwatch.py` + a launchd LaunchAgent, 3×/day) that snapshots battery/storage/clock/firmware/reachability and notifies on anomalies. It's a *pure-stdlib* client of this same daemon socket+token, and **structurally incapable of TX/write** (hardcoded read-only command allowlist; verified — `press`/`write`/`reboot` raise). → **38 tools**. Full writeup: [flipper-healthwatch](flipper-healthwatch.md). (Server change → Desktop restart needed to expose the tool.)

## It's the same RPC, just a different pipe
The Flipper exposes its RPC over a BLE **"Serial" GATT service** — the same length-delimited protobuf (`device_info`, `storage`, `Gui.ScreenFrame`, `input`…) we drive over USB; the official **mobile app** uses exactly this. **The key difference from USB:** the BLE channel is *already* in RPC mode — you do **not** send `start_rpc_session` (that's USB-only; over BLE it corrupts the stream).

## BLE serial GATT service (the concrete knowledge)
| Role | UUID |
|---|---|
| Serial service | `8fe5b3d5-2e7f-4a98-2a48-7acc60fe0000` |
| **TX** (write, host→Flipper) | `19ed82ae-ed21-4c9d-4145-228e62fe0000` |
| **RX** (notify, Flipper→host) | `19ed82ae-ed21-4c9d-4145-228e61fe0000` |
| RPC state | `19ed82ae-ed21-4c9d-4145-228e64fe0000` |

(+ a flow-control characteristic referenced in firmware logs.) **Flow:** connect → subscribe to RX notifications → write delimited protobuf `Main` messages to TX → read responses on RX. Identical protobuf to the USB path — **but NO `start_rpc_session`** (that's USB-only; over BLE it corrupts the stream — see recipe above).

---
> **⚠️ Everything below is the historical debugging journey (2026-06-21), kept for the record.** It contains dead ends and interim *"didn't work"* conclusions that were **later solved** — the working truth is the recipe at the top.

## Transport design (the shape we used)
Use **[`bleak`](https://github.com/hbldh/bleak)** (cross-platform BLE; CoreBluetooth on macOS) with a small **sync-over-async adapter** exposing a pyserial-like `read/write/flush/in_waiting`, so the existing [`flipperzero_protobuf`](https://github.com/flipperdevices/flipperzero_protobuf_py) `FlipperProto` runs **unchanged** over BLE. Only the transport swaps; the protobuf layer + our tools (incl. `screenshot`) reuse as-is.

## ⛔ The macOS wall (what we hit, definitively)
- Installed `bleak`; the **first `BleakScanner.discover()` → SIGABRT (exit 134)**.
- Crash report (`~/Library/Logs/DiagnosticReports/Python-2026-06-21-184314.ips`):
  - `responsibleProc : "claude"`
  - `termination` namespace **`TCC`**: *"…the app's Info.plist must contain an `NSBluetoothAlwaysUsageDescription` key…"*
- **Meaning:** the launching app (**Claude Desktop**) hasn't *declared* Bluetooth usage, so macOS kills any process it spawns that touches BT — **before** even checking permissions. **Adding Claude to System Settings → Privacy & Security → Bluetooth (and restarting) does NOT help** — it's a missing-plist-key abort, not a permission toggle.
- The only "fixes" are bad: edit `Claude.app/Contents/Info.plist` (breaks the app's code signature — don't), or run BLE from a *different* app that declares BT.

## Update — the app-bundle wrapper BREACHES the BT wall (2026-06-21)
Re-attempted with an **app-bundle wrapper** ([`~/flipper-ai/FlipperBLE.app`](file://~/flipper-ai/FlipperBLE.app), Info.plist with `NSBluetoothAlwaysUsageDescription`, **launched via `open`** so it's its own TCC principal, not Claude). Results:
- ✅ **Bluetooth access works** — no SIGABRT; the bundle is the TCC principal (one-time user "Allow"). Big correction to the earlier "impossible."
- ✅ **BLE scan** finds `the device`; ✅ **connect** succeeds (already bonded — no pairing prompt).
- ⚠️ Needed **`arch -arm64`** in the bundle launcher — `open` ran Python as **x86_64** (Claude.app is Intel/Rosetta) while numpy/PIL/protobuf are arm64.
- ✅ RPC **session init** (`start_rpc_session`) sends over BLE ("rpc up").
- ❌ **But RPC responses never return** — neither `device_info` (small) nor `screenshot` (1024 B) gets a reply; the worker hangs reading the response. **Write-with-response didn't help.** Almost certainly the Flipper's BLE RPC needs the **flow-control / RPC-status characteristic** handshake (the chars seen in firmware logs) and/or a non-USB session init — real protocol work, not a quick fix.

**Net:** the TCC wall is **breachable** (app-bundle, not the localhost daemon), and BLE access/connect work — but **reliable RPC-over-BLE still needs flow-control handling**. Tooling left in place: `FlipperBLE.app` + [`ble_worker.py`](file://~/flipper-ai/ble_worker.py) (scan/info/screenshot). **USB remains the full control path.**
> ↳ **Superseded:** RPC-over-BLE did *not* need flow-control handling — the bug was sending `start_rpc_session` over BLE. Dropping it made RPC work (see recipe at top).

**Deeper attempt (RPC data path) — got close, didn't close:** (1) macOS notifications **only** fire with `start_notify(..., cb={"notification_discriminator": fn})` **and** the bleak loop on the **main thread** (background-thread loop = silent — that was the first red herring). (2) Correct architecture = bleak loop on the main thread + `FlipperProto` (sync) in a **worker thread** (its `write()` marshalled back to the loop via `run_coroutine_threadsafe`). (3) **But the Flipper returns empty/zero RPC data** — `rpc_device_info` reads only zeros and spins, and notification delivery is **flaky/inconsistent** between runs. After **~7 approaches** (both threading models · write-with-response · all-char subscribe · discriminator · poll-read · main-loop+worker-thread · skip-handshake) the RPC **response** never came through. Conclusion: deep undocumented BLE-RPC framing + flaky macOS CoreBluetooth indications. **Best future path: Web Bluetooth in Chrome** (the PoC's approach — Chrome handles BLE indications natively/robustly), as a separate project. **USB stays the working control channel.**
> ↳ **Superseded:** solved natively in `bleak` (pure-async, main-thread loop, discriminator) once `start_rpc_session` was dropped — no Web Bluetooth needed. The "empty/zero data" was the corrupted stream, not framing.

## Workarounds (ranked)
1. **USB** — full agent control already (drive + screenshot). Nothing to do. ✅
2. **localhost BLE-bridge daemon** — the *only* agent-side BLE route: run a small BLE daemon from **Terminal.app** (which *can* get BT permission), expose a `localhost` API; the MCP tool talks to localhost (no BT on Claude's side). Heavier — you keep a daemon running.
3. **User-run Terminal script** — *you* drive BLE directly from Terminal (not the agent).
4. **Mobile app** — wireless control today, zero build.

## Caveats (even where BLE works)
- BLE RPC **times out on large transfers** ([firmware #3174](https://github.com/flipperdevices/flipperzero-firmware/issues/3174)) — fine for control + occasional screenshots, unreliable for big file pulls. USB is the full/robust transport.
- **One BLE connection at a time** (phone vs. Mac).
- **Pairing/bonding** uses a PIN shown on the Flipper; flakiness fixes: `Settings → Bluetooth → Forget All Paired Devices`, Release firmware, reboot (LEFT+BACK 5s).
- Slower than USB, but the mobile app screen-mirrors over BLE, so `screenshot` is feasible.

## Verdict
✅ **Done — full wireless agent control works.** Over BLE, from the Mac with **no cable**, the agent reads `device_info`, captures the screen, **and injects UI input** (drives any menu) — all via the **`flipper-ble` MCP server**. The earlier *"not worth it / banked"* call was **wrong**: the blocker was self-inflicted (`start_rpc_session` sent over BLE) plus macOS notification quirks (need `notification_discriminator` + main-thread loop), all now solved (recipe at top). USB stays the *robust* path for large file transfers; **BLE is now a fully working wireless control + screenshot channel — the wireless twin of `flipper-control`.**

## Open questions / to research
- Whether a future **Claude Desktop** ships the Bluetooth entitlement (would unblock agent BLE directly) `(verify)`.
- The **localhost BLE-bridge daemon** as a clean optional module, if wireless ever matters.
- Exact **flow-control characteristic** behavior + MTU for reliable BLE RPC framing.
- Usable **BLE screen-stream FPS** for `screenshot` over the bridge.

## Sources
- BLE serial UUIDs (PoC): https://github.com/EstebanFuentealba/flipper-zero-bluetooth-serial-poc
- bleak macOS TCC crash: https://github.com/hbldh/bleak/issues/761 · troubleshooting: https://bleak.readthedocs.io/en/latest/troubleshooting.html
- BLE RPC timeout: https://github.com/flipperdevices/flipperzero-firmware/issues/3174
- Pairing troubleshooting: https://support.flipper.net/hc/en-us/articles/17915842087709
- RPC protobuf bindings: https://github.com/flipperdevices/flipperzero_protobuf_py
- Our attempt: `~/flipper-ai/` (bleak installed; crash report `Python-2026-06-21-184314.ips`)
