---
title: Flipper Health-Watch (M5 scheduled read-only monitor)
domain: resources
type: guide
status: detailed
summary: Gated, default-off launchd job that polls the Flipper read-only 3×/day (battery/storage/clock/firmware) and notifies on anomalies.
hardware: [flipper-internal]
use_cases: []
related: [resources/flipper-ble-control.md, resources/flipper-control-playbook.md, frontier-roadmap.md]
tags: [m5, health-watch, scheduled, launchd, monitoring, read-only, guardrails]
last_verified: 2026-06-22
---

# Flipper Health-Watch (M5 scheduled read-only monitor)

> **TL;DR —** A gated, **default-off** macOS launchd job (`flipper_healthwatch.py`) that — when switched on via the `healthwatch` MCP tool — connects to the Flipper over BLE **3×/day** and snapshots battery / storage / clock / firmware / reachability, appends a JSONL log, and fires a macOS notification on anomalies. It is **structurally read-only** (a hardcoded command allowlist makes it incapable of transmit/write), which is exactly what makes unattended operation safe — the M5 guardrail. This is the *scheduled* half of [frontier M5](../frontier-roadmap.md); the *fleet* half (Flipper + ESP32) is still open. Toolkit: [flipper-ble-control](flipper-ble-control.md) · [playbook](flipper-control-playbook.md). Part of the [KB](../README.md).

## What it is — and why it's gated
M5 ("fleet / unattended") is the highest-blast-radius stage because it removes the human from the *kick-off* loop. The defining guardrail (roadmap spine): **never an unattended transmit or write.** The health-watch honors that two ways:
1. **Default-off + MCP-gated.** The launchd schedule is **not loaded** by default. It only runs after you switch it on with the `healthwatch` MCP tool (`on`). The agent can't make it run autonomously without that approved tool call.
2. **Structurally read-only.** The watcher can issue *only* the commands in `READONLY_CMDS` (`power`, `diskinfo`, `getdt`, `info`, `ping`, `health`). `send()` asserts membership, so the process is **incapable** of `press` / `write` / `app` / `reboot` / transmit — verified: those raise `AssertionError`.

## What it checks
Each run takes one snapshot and evaluates these (thresholds editable at the top of the script):

| Check | Trips when | Level |
|---|---|---|
| Battery low | `charge_level` ≤ 15% **and** discharging | **ALERT** |
| Battery health | `battery_health` ≤ 80% (cell aging) | WARN |
| Battery temp | `battery_temp` ≤ 0 °C or ≥ 45 °C | WARN |
| SD space | `/ext` free ≤ 10% | WARN |
| Clock drift | \|Flipper RTC − Mac clock\| > 120 s | WARN |
| Firmware change | `firmware_commit` differs from the last run | NOTICE |
| BLE-MAC change | `radio_ble_mac` differs (device swap?) | NOTICE |
| Unreachable | `ping` fails after one retry | WARN |

Smart by design: a low battery **while charging** does *not* alert (only discharging+low fires). A healthy device produces **zero** alerts (silent). Any non-INFO item → one summarized macOS notification.

## Architecture
The watcher is a **pure-stdlib** script — it does *not* touch Bluetooth itself. It speaks the same newline-JSON protocol to the resident daemon (`~/flipper-ai/bled.sock`, `0600`) that the MCP server uses, including the **shared token** (`~/flipper-ai/bled.token`). The daemon holds the one BLE link and does the radio work inside the signed `FlipperBLE.app` (its TCC principal). So:

```
launchd (3×/day) → flipper_healthwatch.py → [Unix socket + token] → flipper_bled daemon → BLE → Flipper
```

It cold-starts the daemon if needed (`open FlipperBLE.app --args daemon`) and **retries once** on the known cold-connect race (first lazy connect after idle can report "device not found"), exactly like the MCP server. After the run the daemon idle-disconnects (180 s), freeing the radio.

## Controlling it
**Via the MCP tool** (the normal path — each call is approval-gated in the client):

| Call | Effect |
|---|---|
| `healthwatch("status")` | (default) enabled? + last-snapshot summary. Read-only, no device poll. |
| `healthwatch("on")` | Enable the 3×/day schedule (loads the LaunchAgent). |
| `healthwatch("off")` | Disable it (back to default-off). |
| `healthwatch("run")` | Run ONE read-only check right now, return the summary. |

**Via CLI** (same logic; what the tool shells out to):
```
python3 ~/flipper-ai/flipper_healthwatch.py status      # enabled? + last snapshot
python3 ~/flipper-ai/flipper_healthwatch.py on|off       # enable / disable the schedule
python3 ~/flipper-ai/flipper_healthwatch.py run          # one read-only run now
python3 ~/flipper-ai/flipper_healthwatch.py run --test-alert  # fire a test notification
python3 ~/flipper-ai/flipper_healthwatch.py run --print  # print last snapshot, no device call
```
(`on`/`off` map to the script's `enable`/`disable` subcommands.)

## The schedule
A user LaunchAgent at `~/Library/LaunchAgents/com.flipper-ble-mcp.healthwatch.plist` with `StartCalendarInterval` at **09:00 / 15:00 / 21:00** local, `RunAtLoad=false`. It's a *LaunchAgent* (user GUI session), not a system daemon — required so BLE/TCC and `osascript` notifications work. The script writes the plist itself (`install`), so the plist content has a single source of truth.

## Constraints (inherent to local BLE)
- **Mac must be awake** at the scheduled time. launchd coalesces a missed run to the next wake — so you get a (possibly late) snapshot, not a silent gap, but timing isn't guaranteed.
- **Local only.** BLE is physically local, so this is launchd on *this* Mac — **not** a cloud routine. A cloud agent couldn't reach the daemon.
- **Radio contention.** Each run briefly grabs the one BLE central. If your phone holds the Flipper at that moment, the run logs `UNREACHABLE` (and the retry usually rides it out).

## Files
- `~/flipper-ai/flipper_healthwatch.py` — the watcher (stdlib only).
- `~/Library/LaunchAgents/com.flipper-ble-mcp.healthwatch.plist` — the schedule.
- `~/flipper-ai/healthwatch.log` — JSONL history (one snapshot/run).
- `~/flipper-ai/healthwatch-last.json` — last snapshot (the firmware/MAC diff basis).
- `~/flipper-ai/healthwatch.out` / `.err` — launchd stdio (debugging).

## Open questions / to research
- **Log rotation** — JSONL grows ~3 lines/day (tiny), but unbounded; add rotation if it ever matters.
- **Single-miss noise** — `UNREACHABLE` can be benign (phone holding the radio). Consider a "N consecutive misses" counter before alerting.
- **Alert persistence** — a macOS notification is transient. Consider also writing a `healthwatch-alerts` status file the agent can read, or a phone push.
- **`/int` storage** — `diskinfo /int` returns the same figures as `/ext` on this firmware `(verify)`, so only `/ext` is monitored.
- **The fleet half of M5** — multi-tool orchestration (Flipper + ESP32 Marauder/Ghost-ESP) is still unbuilt; needs a second control path. See [frontier-roadmap](../frontier-roadmap.md) Stage 5.

## Sources
- Empirical: built + tested live on `the device` (2026-06-22) — power/storage/datetime field names captured from the device; alert logic + the read-only guard unit-verified; plist installed and confirmed default-off.
- Toolkit + daemon + socket/token model: [flipper-ble-control](flipper-ble-control.md). Operating algorithm: [flipper-control-playbook](flipper-control-playbook.md). Stage definition: [frontier-roadmap](../frontier-roadmap.md) Stage 5.
