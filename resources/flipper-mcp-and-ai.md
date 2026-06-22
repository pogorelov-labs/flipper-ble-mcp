---
title: Flipper + MCP + AI (drive it from Claude on a Mac)
domain: resources
type: resource-list
status: detailed
summary: Drive the Flipper from Claude — MCP servers, AgentFlipper, Mac/USB setup, AI-control risks
hardware: []
use_cases: []
related: [resources/notable-apps-and-data.md, topics/tinkering.md, legal-and-safety.md]
tags: [mcp, ai, claude, agent, automation, rpc, usb]
last_verified: 2026-06-19
---

# Flipper + MCP + AI (drive it from Claude on a Mac)

> **TL;DR —** MCP servers and AI tooling that let an agent (Claude Desktop/Code, Cursor) control the Flipper over its protobuf RPC — the projects (busse, roostercoopllc, AgentFlipper), Mac/USB setup, what you can do, and the risks of an AI driving a dual-use RF tool. Builds on the PC-tooling doc.
> Builds on the PC-tooling in [notable-apps-and-data](notable-apps-and-data.md) · dev in [../topics/tinkering.md](../topics/tinkering.md) · safety [../legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md).

## What this is
**MCP** (Model Context Protocol) is the open standard for connecting AI assistants to tools. A
**Flipper MCP server** wraps the Flipper's **protobuf RPC** (the same serial/RPC interface
[pyFlipper](https://github.com/wh00hw/pyFlipper) uses) as MCP tools — so **Claude Desktop / Claude Code /
Cursor / any MCP client** can read NFC, send a saved `.sub`, toggle GPIO, generate+deploy a BadUSB
script, manage files, etc., from natural language. *(This KB was itself built by an AI agent — same idea, pointed at your Flipper.)*

## The projects (as of late-2025 / early-2026 — early/unofficial, `(verify)` maturity)
| Project | Lang | Runs where | Transport | Notes |
|---|---|---|---|---|
| **[busse/flipperzero-mcp](https://github.com/busse/flipperzero-mcp)** | Python | **host (Mac)** | **USB** / WiFi / BLE | Most general; works with Claude Desktop/Cursor; modules incl. BadUSB-gen + music; ships a custom **ESP32-S2 TCP↔UART** bridge fw for WiFi |
| **[roostercoopllc/flipper-mcp](https://github.com/roostercoopllc/flipper-mcp)** | Rust | **on the ESP32-S2 DevBoard** | WiFi | Makes the Flipper a **network MCP endpoint**; exposes SubGHz/NFC/RFID/IR/BLE/GPIO. *Needs the official Wi-Fi DevBoard (ESP32-**S2**)* |
| **[mattyspangler/AgentFlipper](https://github.com/mattyspangler/AgentFlipper)** | Python | host | USB (pyFlipper) | Not MCP — uses **LiteLLM** + **RAG over Flipper docs**; works with **local Ollama** too |
| flipper-mcp-bridge (dudebot) | — | host | USB | Another bridge variant `(verify)` |

> ⚠️ **Name collision:** `flippercloud/flipper-mcp` is the **Ruby feature-flag** library "Flipper" — **unrelated** to the device.

## How it works
```
Claude (Desktop / Code / Cursor)  ──MCP──►  Flipper MCP server  ──protobuf RPC──►  Flipper Zero
                                            (Python on your Mac)   USB-CDC serial / WiFi(ESP32) / BLE
```
The agent calls tools (e.g. `nfc_read`, `subghz_send`, `gpio_set`, `badusb_run`); the server translates to RPC over the chosen transport.

## Setup on a Mac (busse, USB — the path for *my* rig)
1. Plug the Flipper in via USB-C (it enumerates as `/dev/tty.usbmodemflip_*`).
2. Install the server (Python; `uv`/`pipx` per its README).
3. Add it to your MCP client config (Claude Desktop `claude_desktop_config.json`, or `claude mcp add` for **Claude Code**) under `mcpServers`, with env like `FLIPPER_TRANSPORT=usb` (it also supports `auto`/`wifi`/`ble` + `FLIPPER_WIFI_HOST`).
4. Restart the client → ask: *"read the NFC card on my Flipper"*, *"list my saved Sub-GHz files and send `garage.sub`"*, *"write a BadUSB script that opens Notepad and types hello, deploy and run it."*

## What you can do
- **Natural-language control:** read/emulate NFC/RFID, send saved Sub-GHz/IR, GPIO, file ops, screen capture.
- **Generate → validate → deploy → run** payloads (BadUSB Ducky scripts) end-to-end.
- **Agentic app dev:** a viral demo has **Claude Code** remotely *write a FAP, compile it, install it, read the screen to check it works, fix bugs, and repeat* — autonomous Flipper development ([tinkering](../topics/tinkering.md), [ufbt]).
- **RAG help** (AgentFlipper): an LLM that "knows" the Flipper docs and your files.

## On MY rig
- **USB + busse/flipperzero-mcp** is the directly-usable path: any Flipper + Mac + Claude Desktop/**Claude Code**. No extra hardware.
- **WiFi**: busse's WiFi transport wants an **ESP32-S2** bridge, and **roostercoopllc** needs the official **ESP32-S2 Wi-Fi DevBoard** — I have an **ESP32-WROOM Marauder** board, not an S2, so WiFi-MCP may not fit my board without reflashing/another ESP `(verify WROOM compatibility)`. **Stick with USB.**
- Nice synergy: point Claude at this KB **and** the live Flipper at once.

## ⚠️ Risks & cautions (an AI driving a dual-use RF tool)
- **Real-world actions, real-world law.** An agent that transmits Sub-GHz, emulates a card, or injects HID is doing the *actual* thing — the [legal-and-safety](../legal-and-safety.md) rules apply, and **you** are responsible. Keep **human approval** on any TX / emulate / BadUSB step; don't let an agent transmit autonomously.
- **Prompt-injection → hardware.** If the agent ingests untrusted data (a captured payload, a web page, a file) and *also* holds device-control tools, a crafted input could try to make it act. Scope the tools; review tool calls; run in a controlled setting.
- **Maturity:** these are **unofficial / early / WIP** — expect serial flakiness, breaking changes, and partial RPC coverage `(verify current state before relying)`.
- **Least privilege:** prefer read-only/scoped configs for experimentation; back up the SD first.

## Open questions / to research
- Does busse's WiFi/ESP32 firmware run on my **WROOM** Marauder board, or is it S2-only? `(verify)`
- Exact tool/module coverage of busse's server today (which RPC commands are exposed).
- Best **approval/guardrail** setup so an agent can't TX/inject without my confirmation.
- Try AgentFlipper with **local Ollama** (offline, private) vs the MCP route.

## Sources
- busse/flipperzero-mcp: https://github.com/busse/flipperzero-mcp · Show HN: https://news.ycombinator.com/item?id=46434612
- roostercoopllc/flipper-mcp: https://github.com/roostercoopllc/flipper-mcp
- AgentFlipper: https://github.com/mattyspangler/AgentFlipper
- pyFlipper (underlying RPC): https://github.com/wh00hw/pyFlipper · MCP: https://modelcontextprotocol.io
