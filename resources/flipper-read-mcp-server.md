---
title: Flipper Read — Read-Only MCP Server
domain: resources
type: guide
status: detailed
summary: The read-only MCP server we built for this rig — 14 native mcp__flipper__* device-read tools over USB, one allowlist.
hardware: [flipper-internal]
use_cases: []
related: [resources/flipper-control-mcp-server.md, resources/mcp-setup-claude-code.md, resources/flipper-mcp-and-ai.md, frontier-roadmap.md, topics/ai-flipper-possibilities.md, my-setup.md]
tags: [mcp, claude-code, read-only, usb, fastmcp, stage-1, ai-agent]
last_verified: 2026-06-21
---

# Flipper Read — Read-Only MCP Server

> **TL;DR —** The Stage-1 "best-fit" outcome for this rig: a small **read-only MCP server** ([`~/flipper-ai/flipper_mcp_server.py`](file://~/flipper-ai/flipper_mcp_server.py), FastMCP) exposing **14 native `mcp__flipper__*` device-read tools** to Claude Code over USB, with read-only enforced by one shared allowlist — every write/TX/emulate/launch/clock-set is refused before a byte reaches the device. Built (2026-06-21) instead of installing busse (BadUSB-centric, reads less) or roostercoopllc (needs an ESP32-S2 board this rig lacks).
> Setup + path comparison: [mcp-setup-claude-code](mcp-setup-claude-code.md) · concepts/landscape: [flipper-mcp-and-ai](flipper-mcp-and-ai.md) · plan: [frontier-roadmap](../frontier-roadmap.md) · rig: [my-setup](../my-setup.md). Part of the [KB](../README.md).

This is **"Path C"** of [mcp-setup-claude-code](mcp-setup-claude-code.md) and the realized **M1** of the [frontier-roadmap](../frontier-roadmap.md): a native, gated AI↔device read loop on the owner's `the device` (Momentum `mntm-dev`, API 87.1).

## Why build it instead of installing one (June 2026 landscape)
| Server | Tools | Transport | Fit for this rig |
|---|---|---|---|
| [busse/flipperzero-mcp](https://github.com/busse/flipperzero-mcp) | ~15: systeminfo + **BadUSB** + music; no NFC/SubGHz/RFID read | USB | works, but **reads less** than our toolkit |
| [roostercoopllc/flipper-mcp](https://github.com/roostercoopllc/flipper-mcp) | ~30: SubGHz/NFC/RFID/IR/GPIO/BadUSB/BLE/storage | runs **on an ESP32-S2 WiFi Dev Board** | ❌ needs the **S2 board** (rig has a WROOM Marauder) |
| [dudebot/flipper-mcp-bridge](https://github.com/dudebot/flipper-mcp-bridge) | 9, IR-only | USB | too narrow |
| **flipper-read (ours)** | **14 device-read tools**, read-only enforced | USB | ✅ broadest reads for this hardware, no purchase |

Decision: the comprehensive server needs hardware we don't have, and the best USB alternative (busse) reads less than the RPC we already drive — so we wrapped our proven read core as a real MCP server.

## The 14 tools
| Tool | Runs | Returns |
|---|---|---|
| `device_info` | `device_info` | fw version/commit/branch/API, hw model/UID/region, radio |
| `status` | `neofetch` | **one-shot:** fw, **battery %**, disk used/free, RAM, uptime, CPU |
| `free_memory` | `free` | heap free/total/min, largest block |
| `uptime` | `uptime` | time since boot |
| `device_date` | `date` | current clock (read; never sets) |
| `app_list` | `loader list` | built-in app registry |
| `storage_list` | `storage list PATH` | dir listing ([D]/[F]+size); default `/ext` |
| `storage_tree` | `storage tree PATH` | recursive tree |
| `storage_info` | `storage info PATH` | total/free bytes |
| `storage_stat` | `storage stat PATH` | type + size of one entry |
| `storage_read` | `storage read PATH` | file contents (e.g. a `.sub`/`.nfc` header) |
| `storage_md5` | `storage md5 PATH` | file checksum |
| `read_raw` | any command **through the allowlist** | arbitrary read; refuses non-reads |
| `readonly_policy` | (none) | prints the allowlist (no device needed) |

## Read-only by design
Read-only is enforced in [`flipper_core.py`](file://~/flipper-ai/flipper_core.py) (`check_readonly`), the single allowlist shared by the server **and** the CLI so they can't drift:

- **Allowed:** `device_info`, `neofetch`, `free`, `free_blocks`, `uptime`, `date` (bare), `storage {info,list,tree,stat,read,md5}`, `loader {list,info}`.
- **Refused (not on the allowlist):** `power` (off/reboot/5v), `update`, `factory_reset`, `crypto`, `sysctl`, `top`, every `subghz/nfc/rfid/ikey/gpio/buzzer/vibro/led/js` verb, plus `storage {remove,write,mkdir,rename,copy,format}` and `loader {open,run}`.

**Two gating layers:** (1) the allowlist refuses non-reads before opening the port; (2) Claude Code still prompts to approve each tool call. Writes/TX will be a **separate, explicitly-gated** server (Stage 3 / M3) — never folded into this one.

## Files (operational tooling — lives in `~/flipper-ai/`, outside this KB)
- [`flipper_core.py`](file://~/flipper-ai/flipper_core.py) — shared allowlist + serial plumbing (`check_readonly`, `run_read`).
- [`flipper_mcp_server.py`](file://~/flipper-ai/flipper_mcp_server.py) — the FastMCP server (the 14 tools above).
- [`flipper-read.py`](file://~/flipper-ai/flipper-read.py) — a CLI over the same core (handy outside an MCP client).
- `venv/` (pyserial + mcp) and `README.md` — operational notes.

## Install / registration (this machine)
There's **no `claude` CLI** here (Claude desktop app), so the server is registered directly in `~/.claude.json` → `mcpServers.flipper`:
```json
"flipper": { "command": "~/flipper-ai/venv/bin/python",
             "args": ["~/flipper-ai/flipper_mcp_server.py"],
             "env": {"PYTHONUNBUFFERED": "1"} }
```
**Restart Claude Code to load it** (a backup of the prior config is at `~/.claude.json.bak-2026-06-21`). Verified working via an MCP `initialize` handshake (`serverInfo.name: flipper`). Only one host app can hold the serial port — close qFlipper / browser WebUSB tabs.

## Using it
After restart, plain-language asks route to native tools, e.g.:
- *"Use the flipper status tool"* → `status` (battery/fw/disk).
- *"List the saved NFC on my Flipper"* → `storage_list /ext/nfc`.
- *"Read this capture: /ext/subghz/Tesla/Tesla_EU_AM650.sub"* → `storage_read`.

## mntm-dev specifics (verified live on `the device`)
- `power` has **no read subcommand** on this firmware (only off/reboot/5v) → `status`/`neofetch` is the battery+disk read instead.
- `ps` doesn't exist (it's `top`, which **streams**) → `top` is excluded to keep one-shot calls clean.
- Live RX (`nfc`/`subghz` scans) is **intentionally excluded** — it energizes hardware, so it belongs behind the Stage 3 gate, not the passive read set.

## Open questions / to research
- A **Stage 3 companion** write/TX server with per-action approval (file ops first, then device clones) — kept separate from this read-only one.
- Whether the desktop app also honors a project `.mcp.json` (would make the server version-able with a repo) `(verify)`.
- Packaging the absolute venv path more portably (e.g. a launcher script) so the registration survives a venv move.
- Adding `free_blocks` and a safe `storage_read`-with-line-limit helper as first-class tools.

## Sources
- Our tooling: `~/flipper-ai/` (`flipper_core.py`, `flipper_mcp_server.py`, `flipper-read.py`).
- MCP Python SDK / FastMCP: https://github.com/modelcontextprotocol/python-sdk
- Servers compared: https://github.com/busse/flipperzero-mcp · https://github.com/roostercoopllc/flipper-mcp · https://github.com/dudebot/flipper-mcp-bridge
- Concepts + setup: [flipper-mcp-and-ai](flipper-mcp-and-ai.md) · [mcp-setup-claude-code](mcp-setup-claude-code.md)
