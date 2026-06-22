---
title: Hardware / Electronics Tinkering & App Dev
domain: topics
type: topic
status: detailed
summary: Maker/electronics projects, FAP/ufbt app dev, on-device JavaScript, and asset packs.
hardware: [flipper-internal]
use_cases: []
related: [hardware/README.md, hardware/gpio-addons-potential.md, resources/learning-and-docs.md, resources/best-github-repos.md, 01-architecture.md]
tags: [tinkering, gpio, fap, ufbt, javascript, asset-packs, app-dev]
last_verified: 2026-06-19
---

# Hardware / Electronics Tinkering & App Dev

> **TL;DR —** The hands-on maker side of the Flipper: GPIO electronics starter builds (I²C/UART/logic-analyzer/SWD), writing your own FAP apps with ufbt/fbt, on-device JavaScript scripting, and building asset packs.
> Hardware: [hardware/README.md](../hardware/README.md), [gpio-addons-potential.md](../hardware/gpio-addons-potential.md). Docs: [learning-and-docs](../resources/learning-and-docs.md), [best-github-repos](../resources/best-github-repos.md). Part of the [KB](../README.md).

The Flipper makes a surprisingly capable bench tool: it speaks **UART/SPI/I²C/1-Wire/SWD** on an
18-pin header, runs **C apps (FAPs)** and **on-device JavaScript**, and can act as a logic analyzer
or ARM debugger. This page is the hands-on counterpart to the [architecture map](../01-architecture.md).

> ⚠️ **Electrical limits first.** GPIO is **3.3 V logic — not 5 V tolerant**. Pin 1 (5V) and the
> 3V3 pin can source only limited current (budget ≲100–200 mA total for add-ons; the 5V rail is
> gated and off by default — enable it in GPIO settings). Level-shift any 5 V device. Full pinout,
> current ceilings, and the per-pin function table live in [hardware/README.md](../hardware/README.md).

---

## 1) Electronics projects (first builds)

Concrete starter projects that validate your toolchain, roughly in order of difficulty:

| Project | What you wire | How | Notes |
|---|---|---|---|
| **Read an I²C sensor** (BME280 / SHT3x) | SDA→pin 15 (C1), SCL→pin 16 (C0), 3V3→pin 9, GND→pin 18 | Use an **I²C scanner** FAP to confirm the address, then read via a sensor FAP or a JS script (Momentum's `i2c` module). | Many breakouts are 3.3 V-native — check before connecting. Pull-ups usually on the breakout. |
| **UART bridge / serial console** | TX/RX on pins 13 (TX) / 14 (RX), GND | Stock **GPIO → USB-UART Bridge** app turns the Flipper into a USB-serial adapter; talk to a router/IoT console. Or read in-app via the JS **Serial** module. | Default 3.3 V levels; pick the baud to match the target. |
| **Basic logic analyzer** | Up to 8 channels on GPIO | Flash a **logic-analyzer FAP** that speaks the **SUMP** protocol → capture in **PulseView/sigrok** over USB serial. (e.g. `andr0423/flipper-logic-analyzer`, or the older "Saleae-style"/sigrok ports.) | Good for slow buses (UART/I²C/SPI reverse-engineering, e.g. SentrySafe). For fast/long captures use an RP2040/dedicated LA — the M4 is the bottleneck. |
| **SWD-debug another ARM MCU** | SWD pins 10 (SWC/SWCLK) / 12 (SIO/SWDIO) + GND, 3V3 reference | Two routes: (a) **DAP Link / DAPLink FAP** → CMSIS-DAP target for OpenOCD/pyOCD on a PC; (b) **Wi-Fi DevBoard** running **Black Magic** firmware → wireless GDB server. **SWD Probe FAP** (`g3gg0/flipper-swd_probe`) even enumerates SWD pinouts on-device, no PC. | The DevBoard ships with Black Magic preinstalled and exposes BMP/DAPLink modes; the same SWD pins also let the board debug the Flipper itself. |

Most of these need only Dupont jumpers and a breadboard. Start with the I²C scanner — if it finds
the address, your power + wiring + level assumptions are all correct.

## 2) App development — FAPs

A **FAP (Flipper Application Package, `.fap`)** is a relocatable app the OS loads from the SD card
at runtime (no full reflash). Minimum project:

```
my_app/
├─ application.fam      # manifest: appid, name, entry_point, category, stack size, icon
├─ my_app.c            # entry point declared in the manifest
└─ icon.png            # 10x10 1-bit app icon
```

### ufbt — the micro build tool (recommended)
**ufbt** ("micro FBT") pulls a matching SDK and builds a single app without cloning the whole firmware.

```bash
python3 -m pip install --upgrade ufbt     # or: pipx install ufbt   (Win: py -m pip install --upgrade ufbt)
ufbt create APPID=my_app                  # scaffold manifest + source in the cwd
ufbt                                       # build → dist/my_app.fap
ufbt launch                                # upload over USB + run on the connected Flipper
ufbt cli                                    # drop into the device serial CLI
ufbt vscode_dist                            # generate VS Code build/debug config
ufbt update --channel=dev                   # pin a different SDK channel (release/rc/dev)
```

Requires Python 3.8+. On first run ufbt downloads the SDK for the selected channel. `ufbt vscode_dist`
gives full IntelliSense + F5 build/flash in VS Code (pair with the Flipper VS Code extension and a
DevBoard for source-level debugging).

### fbt — full firmware SDK (alternative)
For changes that touch firmware itself (new system apps, HAL, drivers), clone the firmware repo and
use **fbt** (the full Flipper Build Tool). Heavier checkout, but builds the whole image; `fbt launch
APPSRC=…` builds and runs one app against your tree.

### Where the examples live
- **Official examples:** `applications/examples/` in the firmware repo, plus the [SDK / API docs](https://developer.flipper.net).
- **Community tutorials:** **[jamisonderek/flipper-zero-tutorials](https://github.com/jamisonderek/flipper-zero-tutorials)** (C + JS, GUI patterns).
- More pointers: [best-github-repos](../resources/best-github-repos.md), [learning-and-docs](../resources/learning-and-docs.md).
- ufbt source/README: https://github.com/flipperdevices/flipperzero-ufbt

## 3) On-device JavaScript

The fastest way to script behavior — **no compile step**. A small JS engine (mJS-derived) runs `.js`
files straight from the SD card; launch via **Apps → Scripts** (or run/edit through `ufbt cli` / the
serial CLI). Each module is `require()`'d.

**Stock firmware modules** (per developer.flipper.net): `badusb`, `gpio`, `gui`, `notification`,
`serial`, `storage`, `math`, `flipper`, plus an **event loop** module for event-driven scripts.

**Momentum has the largest module set** (VERIFY against your installed version) — it adds, among
others: `subghz` (transmit `.sub` files, RSSI), `usbdisk` (virtual USB mass-storage), `i2c`, `spi`,
`blebeacon`, `widget`, `vgm`, plus richer `gui` views (`submenu`, on-screen `keyboard`/byte input) and
extras like `storage-virtual` and `usbdisk-createimage`.

```js
// concept: read a sensor over UART and notify, Momentum-style
let serial = require("serial");
let notify = require("notification");
serial.setup("usart", 115200);
serial.write("READ\n");
let line = serial.readln(1000);          // 1s timeout
if (line) { print("got:", line); notify.success(); }
else      { notify.error(); }
serial.end();
```

To run: copy `script.js` into `/ext/apps/Scripts` (or the Archive), open it on the device, "Run".
Module availability differs by firmware — guard with feature checks and keep stock-only scripts
portable. JS reference: https://developer.flipper.net/flipperzero/doxygen/js.html

## 4) Asset packs / animations

Asset packs reskin the dolphin idle animations, icons, and fonts.

**Format:** each animation is a folder of 1-bit frames `frame_0.bm … frame_N.bm` (raw 128×64 pixel
data) plus a **`meta.txt`** (Filetype `Flipper Animation`, Width/Height, Passive/Active frames,
Frames order, Frame rate, Duration, Active cycles/cooldown, Bubble slots). A pack-level
**`manifest.txt`** lists each animation with the **min/max dolphin level** and weight that gate when
it plays — bump the max level for Momentum's extended curve.

**Tools:** **FlipperAnimationManager** (GUI to build/preview packs and emit `meta.txt`/`manifest.txt`);
GIF/PNG → `.bm` converters in community repos. See [best-github-repos](../resources/best-github-repos.md).

**Install (firmware-specific paths):**

| Firmware | Drop pack at |
|---|---|
| **Momentum** | `/ext/asset_packs/<PackName>/` with `Anims/` (+ `Icons/`, `Fonts/`); select in **Settings → Desktop/Momentum → Asset Pack** |
| **Xtreme / Unleashed** | `/ext/dolphin_custom/<PackName>/` with `Anims/` and/or `Icons/` |
| **RogueMaster** | same custom-pack mechanism (RM bundles many packs); pick in settings, reboot |

Reboot after copying so the new pack is picked up. Packs are cross-compatible across Official/
Momentum/Xtreme/Unleashed/RogueMaster as long as `manifest.txt` levels match the firmware's cap.

## Open questions / to research
- Exact stock JS module list per firmware version, and which Momentum modules are stable on Unleashed/Xtreme `(verify)`.
- Best-maintained logic-analyzer FAP for fast captures (sample-rate ceiling on the WB55 M4).
- Whether DAPLink-over-DevBoard now supports SWO/trace, not just SWD GDB.
- Reliable BME280/SHT3x sensor FAP vs. doing it purely in JS `i2c` (Momentum).
- Current FlipperAnimationManager fork that handles Momentum's level-30 manifest and Bubble slots.

## Sources
- Apps & FAP build: https://docs.flipper.net/zero/apps · SDK/JS: https://developer.flipper.net
- ufbt: https://github.com/flipperdevices/flipperzero-ufbt
- JS reference: https://developer.flipper.net/flipperzero/doxygen/js.html
- DevBoard debug modes (BMP/DAPLink): https://developer.flipper.net/flipperzero/doxygen/dev_board_debug_modes.html
- jamisonderek tutorials (C + JS + debugging): https://github.com/jamisonderek/flipper-zero-tutorials/wiki
- Logic analyzer (SUMP/PulseView): https://github.com/andr0423/flipper-logic-analyzer
- SWD Probe FAP: https://github.com/g3gg0/flipper-swd_probe · Black Magic ESP32-S2: https://github.com/flipperdevices/blackmagic-esp32-s2
- Asset Packs format: https://github.com/Next-Flip/Momentum-Firmware/blob/dev/documentation/file_formats/AssetPacks.md
