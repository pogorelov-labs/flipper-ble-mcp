---
title: Flipper Control — Write/TX MCP Server (Stage 3)
domain: resources
type: guide
status: detailed
summary: Gated control MCP server (Stage 3) — 14 tools (input/apps/LED/GPIO/IR+SubGHz-TX/writes + screenshot) over USB, each approved.
hardware: [flipper-internal]
use_cases: []
related: [resources/flipper-read-mcp-server.md, resources/mcp-setup-claude-code.md, frontier-roadmap.md, topics/ai-flipper-possibilities.md, legal-and-safety.md]
tags: [mcp, control, write, transmit, input-injection, stage-3, ai-agent]
last_verified: 2026-06-21
---

# Flipper Control — Write/TX MCP Server (Stage 3)

> **TL;DR —** The **action** counterpart to the read-only [`flipper`](flipper-read-mcp-server.md) server: a second MCP server ([`~/flipper-ai/flipper_control_server.py`](file://~/flipper-ai/flipper_control_server.py)) that **drives the device** over USB — inject button presses, launch apps, LED/vibro, GPIO, **IR & Sub-GHz transmit**, storage writes. **Every tool is a real action; Claude Desktop prompts before each call (the human-approval gate)**; a blocklist refuses factory_reset/update/power-off. This is **frontier-roadmap M3**, proven live 2026-06-21 (an injected `input send ok short` opened the main menu).
> Read counterpart: [flipper-read-mcp-server](flipper-read-mcp-server.md) · plan: [frontier-roadmap M3](../frontier-roadmap.md) · risk: [ai-flipper-possibilities](../topics/ai-flipper-possibilities.md) · [legal](../legal-and-safety.md). Part of the [KB](../README.md).

This realizes **Stage 3 / M3**: writes & transmits behind a per-action gate, kept **separate** from the read-only server (least privilege — you can disable control independently).

## The 13 tools
| Tool | Action |
|---|---|
| `press(button, kind)` | inject UI input — `input send` (up/down/left/right/ok/back × short/long/press/release) |
| `launch_app(name)` · `close_app()` | `loader open <name>` / `loader close` |
| `led(channel, value)` | `led r\|g\|b\|bl 0-255` |
| `vibrate(on)` | `vibro 1\|0` |
| `gpio_set(pin,value)` · `gpio_read(pin)` | GPIO out/in |
| `ir_tx(protocol, address, command)` | ⚠️ **transmit** an IR code |
| `subghz_tx(key, freq, te, repeat, device)` | ⚠️ **transmit** a Sub-GHz key |
| `storage_remove/mkdir/rename(path)` | ⚠️ SD writes/deletes |
| `screenshot()` | 📷 capture the screen as a PNG (read-only — *see* what you drive; auto-allowable) |
| `raw_control(command)` | arbitrary CLI on the control path (catastrophic cmds still blocked) |

## Safety model
- **Per-action gate:** Claude Desktop prompts before *every* `mcp__flipper-control__*` call — approve one at a time. Never blanket-allow the TX/delete tools.
- **Hard blocklist:** `factory_reset`, `update`, `power off|reboot` are refused no matter how they're invoked.
- **TX is real RF:** `ir_tx` / `subghz_tx` transmit — **authorized / own targets only, legal bands only** ([legal-and-safety](../legal-and-safety.md)). Full saved-`.sub` replay is still done in the Sub-GHz app, not here (the CLI `subghz tx` takes a raw 3-byte key).
- **Separation:** observation stays in the read-only [`flipper`](flipper-read-mcp-server.md) server; this server only acts. Both ride the same USB CLI via [`flipper_core.run_command`](file://~/flipper-ai/flipper_core.py) — the control server deliberately does **not** apply the read-only allowlist (that's the point).
- **Prompt-injection → hardware:** don't let the agent act on untrusted input while it holds these tools ([ai-flipper-possibilities §risk](../topics/ai-flipper-possibilities.md)).

## How control works (and the proof)
The Flipper's `input` CLI injects events: `input send <key> <type>`. The desktop opens its menu on a *short* OK, so `input send ok short` = tap OK. **Verified live on `the device` 2026-06-21:** that command opened the main menu; `led`/`vibro` confirmed output control. That's M3 — the agent drives the device, not just reads it.

## Closed loop — screen capture ✅ (done 2026-06-21)
The `screenshot` tool **closes the loop** — the agent can **drive *and* see**. It uses the Flipper's **protobuf RPC** (`Gui.ScreenFrame`) via the [`flipperzero-protobuf`](https://pypi.org/project/flipperzero-protobuf/) bindings (installed `--no-deps` so they run on current numpy 2.x / protobuf 7.x); the 1024-byte 8-page framebuffer is decoded to a 128×64 PNG ([`flipper_control_server._capture_screen_png`](file://~/flipper-ai/flipper_control_server.py)). **Verified live** — captured the desktop (dolphin + 100% battery) cleanly. **Exception:** while the **Marauder app holds the USB**, screenshot (like all RPC) goes quiet — that one screen stays human-read.

## Install / registration
There's no `claude` CLI on this machine (Claude Desktop), so it's registered directly in `~/.claude.json` → `mcpServers.flipper-control`:
```json
"flipper-control": { "command": "~/flipper-ai/venv/bin/python",
                     "args": ["~/flipper-ai/flipper_control_server.py"],
                     "env": {"PYTHONUNBUFFERED": "1"} }
```
**Restart Claude Desktop to load it** (backup at `~/.claude.json.bak-control-2026-06-21`). Only one host app can hold the serial port — and **the Marauder app hogs the USB**, so control (like reads) goes quiet while it's open.

## Files
- [`flipper_control_server.py`](file://~/flipper-ai/flipper_control_server.py) — the 13 tools above (FastMCP).
- [`flipper_core.py`](file://~/flipper-ai/flipper_core.py) — shared serial plumbing (`run_command` = raw; `run_read`/`check_readonly` = the read server's allowlist, unused here).

## Open questions / to research
- **Screenshot via protobuf RPC** — pyFlipper vs hand-rolled `Gui.ScreenFrame`; can it read the Marauder screen while that app holds the USB? `(verify)`
- Reliable **file *content* writes** (CLI `storage write` is interactive; the RPC `Storage.Write` is cleaner) — not yet a tool.
- Saved-`.sub` **replay** as a tool (currently app-only).
- Per-tool **approval UX** in Claude Desktop for a device that physically acts.

## Sources
- Our tooling: `~/flipper-ai/flipper_control_server.py`, `flipper_core.py`.
- Flipper CLI (input/loader/led/vibro/subghz/ir/gpio/storage): https://docs.flipper.net/development/cli
- Read counterpart + concepts: [flipper-read-mcp-server](flipper-read-mcp-server.md) · [ai-flipper-possibilities](../topics/ai-flipper-possibilities.md)
