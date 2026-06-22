---
title: Stage 1 Setup — Claude Code + busse MCP over USB (read-only, gated)
domain: resources
type: guide
status: detailed
summary: Install busse MCP, add to Claude Code over USB, scope it read-only with gating — first safe AI↔device milestone.
hardware: [flipper-internal]
use_cases: []
related: [resources/flipper-mcp-and-ai.md, frontier-roadmap.md, topics/ai-flipper-possibilities.md, firmware/migration-xtreme-to-momentum.md, legal-and-safety.md]
tags: [mcp, claude-code, usb, read-only, permission-gating, stage-1, busse]
last_verified: 2026-06-19
---

# Stage 1 Setup — Claude Code + busse MCP over USB (read-only, gated)

> **TL;DR —** Install **busse/flipperzero-mcp**, add it to **Claude Code** over USB, scope it **read-only** with permission gating, and hit the first safe "AI ↔ device" milestone. **No transmit/inject until later stages.**
> Concepts: [flipper-mcp-and-ai](flipper-mcp-and-ai.md) · plan: [frontier-roadmap Stage 1](../frontier-roadmap.md) · risk: [ai-flipper-possibilities](../topics/ai-flipper-possibilities.md) · [legal](../legal-and-safety.md). Part of the [KB](../README.md).

**Stage 1** of the [frontier-roadmap](../frontier-roadmap.md): Claude Code talks to the Flipper over USB **read-only**, with a human-approval gate on every tool call — proving the loop safely before any write/TX.

## Three paths (this rig now runs Path C — a native MCP server)
- **Path A — busse MCP** (Steps 1-4 below): the Flipper becomes `mcp__flipper-zero__*` tools *inside* Claude Code — the cleanest "agent tool" integration. But busse today exposes only **connection + systeminfo + BadUSB + music**, needs a Claude Code restart to load, and reads *less* of the device than the raw RPC.
- **Path B — direct read-only RPC toolkit** ✅ *built, in use, and live-verified on this rig (`the device`, mntm-dev API 87.1, 2026-06-21)*: a small Python CLI, [`~/flipper-ai/flipper-read.py`](file://~/flipper-ai/flipper-read.py), that drives the Flipper's text console over USB behind a **hard-coded read-only allowlist** — `device_info`, `neofetch` (fw+battery+disk in one shot), `free`/`free_blocks`/`uptime`/`date`, `storage {info,list,tree,stat,read,md5}`, `loader {list,info}`. Anything that writes/transmits/emulates/launches/sets-the-clock is **refused before a byte reaches the device**, so an agent calling it literally cannot make the Flipper act. Reads more than busse; no restart needed.

### Path B — quickstart
```bash
python3 -m venv ~/flipper-ai/venv && ~/flipper-ai/venv/bin/pip install pyserial   # one-time
PY=~/flipper-ai/venv/bin/python; S=~/flipper-ai/flipper-read.py

$PY $S policy                  # print the read-only allowlist (no device)
$PY $S --dry-run cat /ext/x    # show the gated command it WOULD send (no port opened)
$PY $S info                    # device_info  (live: Flipper in, qFlipper/browser closed)
$PY $S neofetch                # one-shot status: firmware, battery, disk, uptime
$PY $S assets                  # storage list /ext/asset_packs  (did the asset pack survive?)
$PY $S ls /ext/nfc             # saved NFC dumps · `apps` · `tree /ext`
```
> **mntm-dev gotcha (verified live):** `power` has no read subcommand (only off/reboot/5v) — `neofetch` is the one-shot status (firmware, **battery %**, disk, uptime). `ps`→ use `top` (but `top` streams, so it's excluded from the read set). Live RX (`nfc`/`subghz` scans) is **deliberately not** in the read set — it energizes hardware, so it belongs behind the Stage 3 gate, not the passive read path.
**Two gating layers, same as Path A:** (1) the tool's own allowlist refuses non-reads; (2) Claude Code's Bash-permission prompt still gates each invocation. Writes/TX remain impossible at the tool layer until a later stage adds them behind an explicit per-action gate. Full operational notes: `~/flipper-ai/README.md`.

### Path C — native MCP server ✅ (the chosen "best-fit", built 2026-06-21)
Rather than install **busse** (BadUSB-centric, reads less than our toolkit) or **roostercoopllc** (~30 tools but runs on an **ESP32-S2 WiFi Dev Board** this rig lacks), we wrapped the read core as a real MCP server: [`~/flipper-ai/flipper_mcp_server.py`](file://~/flipper-ai/flipper_mcp_server.py) (FastMCP) exposing **14 native read-only `mcp__flipper__*` tools** (`device_info`, `status`/neofetch, `storage_list/tree/info/stat/read/md5`, `app_list`, `free_memory`, `uptime`, `device_date`, `read_raw`, `readonly_policy`) on the shared [`flipper_core.py`](file://~/flipper-ai/flipper_core.py) allowlist. **Registration:** there's no `claude` CLI on this machine (desktop app), so it's added directly to `~/.claude.json` → `mcpServers.flipper` (`command` = venv python, `args` = [server.py]); **restart Claude Code to load it**. Writes/TX will be a *separate, explicitly-gated* server (Stage 3).

## Prereqs
- **Stage 0 done** — on Momentum ([migration](../firmware/migration-xtreme-to-momentum.md)); USB serial works (`/dev/tty.usbmodemflip_*`).
- **Python 3.10+**, **Claude Code**, Flipper on USB-C.
- ⚠️ **Only one host app can hold the serial port** — **quit qFlipper / close Flipper Lab tabs** first.

## Step 1 — Install the server
```bash
git clone https://github.com/busse/flipperzero-mcp.git
cd flipperzero-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e .            # needs Python 3.10+
```
(Sanity-check with no hardware: `FLIPPER_MCP_ALLOW_STUB_MODE=1`.)

## Step 2 — Add it to Claude Code (USB transport)
Use the **venv's** python (absolute path) so no working-dir is needed:
```bash
claude mcp add flipper-zero \
  --env FLIPPER_TRANSPORT=usb --env PYTHONUNBUFFERED=1 \
  -- /ABS/PATH/flipperzero-mcp/.venv/bin/python -m flipper_mcp.cli.main
```
- Verify: `claude mcp list` → `flipper-zero` connected.
- If auto-detect misses the port: add `--env FLIPPER_PORT=/dev/tty.usbmodemflip_XXXX`.

## Step 3 — Scope it READ-ONLY (the approval gate)
busse's tools are named `mcp__flipper-zero__<tool>`:

| Safe / read-only (allow) | Writes or acts (**deny for now**) |
|---|---|
| `flipper_connection_health`, `flipper_connection_reconnect` | `badusb_write`, `badusb_delete`, `badusb_rename` |
| `systeminfo_get` (device + SD status) | **`badusb_execute`** ← **runs a payload** (needs `confirm=true`) |
| `badusb_list`, `badusb_read`, `badusb_generate`, `badusb_validate` (create/validate scripts; don't run them) | `music_play` |
| `music_get_format` | |

Two gating layers — use **both**:
1. **Default = ask.** Claude Code prompts before every MCP tool call. Approve **only reads**; never pick "always allow" on a write/execute tool.
2. **Explicit allow/deny** in `.claude/settings.json` (or `/permissions`):
```json
{ "permissions": {
    "allow": [
      "mcp__flipper-zero__systeminfo_get",
      "mcp__flipper-zero__flipper_connection_health",
      "mcp__flipper-zero__badusb_list",
      "mcp__flipper-zero__badusb_read"
    ],
    "deny": [
      "mcp__flipper-zero__badusb_execute",
      "mcp__flipper-zero__badusb_write",
      "mcp__flipper-zero__badusb_delete",
      "mcp__flipper-zero__music_play"
    ] } }
```

## Step 4 — First commands (the milestone)
In Claude Code:
- *"Use the flipper-zero tools to show my device + SD-card status."* (`systeminfo_get`)
- *"Check the Flipper connection health."* (`flipper_connection_health`)
- *"List the BadUSB scripts on my Flipper."* (`badusb_list`)
- ✅ **M1 (this rig's first milestone):** Claude reads your device state over USB, and you've confirmed every write/execute tool is gated/denied.

## Honest scope note (current busse build)
busse today exposes **connection + systeminfo + BadUSB + music** — it does **not** yet ship NFC/Sub-GHz *read* tools, so the literal *"AI reads my NFC card"* needs a newer build or a **[pyFlipper](https://github.com/wh00hw/pyFlipper)/[AgentFlipper](https://github.com/mattyspangler/AgentFlipper)** path that wraps the broader RPC `(verify current tools)`. The milestone that matters now — a **gated, read-only AI↔device loop** — is fully real via `systeminfo_get`. (When NFC-read tools land, the same gating pattern extends to them.)

## Safety (carries into Stage 3+)
- **Never** approve `badusb_execute` / writes until Stage 3 — and only per-action.
- **Prompt-injection → hardware:** don't let the agent ingest untrusted files/pages in a session where it holds device tools ([ai-flipper-possibilities §risk](../topics/ai-flipper-possibilities.md)).
- **Privacy:** prefer AgentFlipper + local **Ollama** if device data shouldn't leave the Mac.
- Authorized/own devices only; SD backed up.

## Troubleshooting
- *No device / "port busy"* → quit qFlipper, close Flipper Lab; replug; set `FLIPPER_PORT`.
- *Server won't start* → Python 3.10+, `pip install -e .` succeeded, venv python path correct.
- *Tool not found* → `claude mcp list`; restart Claude Code after adding/editing.

## Open questions / to research
- Confirm busse's exact current tool list (does a newer build add NFC/Sub-GHz read?) `(verify)`.
- Best per-tool **approval prompt** UX in Claude Code for a device that does physical things.
- Whether `claude mcp add` needs a cwd/wrapper for this server, or the absolute venv-python path suffices.

## Sources
- busse/flipperzero-mcp: https://github.com/busse/flipperzero-mcp
- pyFlipper: https://github.com/wh00hw/pyFlipper · AgentFlipper: https://github.com/mattyspangler/AgentFlipper
- Concepts + risk: [flipper-mcp-and-ai](flipper-mcp-and-ai.md) · [ai-flipper-possibilities](../topics/ai-flipper-possibilities.md)
