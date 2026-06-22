---
title: Wireless Add-On Apps — ESP32 Wi-Fi, Bluetooth LE & NRF24
domain: resources
type: reference
status: detailed
summary: Per-app runbook for the ESP32 / BLE / NRF24 companion FAPs on my Momentum rig — what each does, settings, hardware, sources.
hardware: [esp32-marauder, nrf24, devboard, flipper-internal]
use_cases: [UC-29, UC-30, UC-31, UC-32, UC-33, UC-34, UC-35, UC-36, UC-37, UC-38, UC-39, UC-40, UC-57]
related: [my-setup.md, hardware/esp32-marauder-module.md, hardware/esp32-firmware-comparison.md, hardware/gpio-addons-current.md, wifi/README.md, bluetooth/README.md, bluetooth/ble-spam.md, bluetooth/airtag-tracker-detection.md, capabilities/badusb.md, legal-and-safety.md]
tags: [esp32, marauder, ghost-esp, flipperhttp, ble-spam, findmy, nrf24, mousejack, companion-apps]
last_verified: 2026-06-22
---

# Wireless Add-On Apps — ESP32 Wi-Fi, Bluetooth LE & NRF24

> **TL;DR —** App-by-app launcher reference for the wireless add-on FAPs installed on my Flipper (Momentum, maxed app set), grouped **ESP32 Wi-Fi / Bluetooth LE / NRF24**. For each: what it does, key settings, use-cases (mapped to UC-IDs), and the **hardware/firmware it actually needs**. The split that matters: **ESP32 apps are dumb terminals** — they do nothing without an ESP32 board flashed with the matching firmware (Marauder / Ghost ESP / FlipperHTTP); **BLE apps run on the Flipper's own radio** (no add-on); **NRF24 apps need an nRF24L01+ wired to the GPIO**. Deep mechanics live in the wifi/ and bluetooth/ sub-domains — this doc is the index over the installed `.fap`s.
> Rig: [my-setup §4](../my-setup.md) · Marauder HW: [esp32-marauder-module](../hardware/esp32-marauder-module.md) · which ESP32 fw: [esp32-firmware-comparison](../hardware/esp32-firmware-comparison.md) · Wi-Fi hub [../wifi/README.md](../wifi/README.md) · BLE hub [../bluetooth/README.md](../bluetooth/README.md) · [legal](../legal-and-safety.md). Part of the [KB](../README.md).

## The three hardware tiers (read this first)
Whether an app *does anything* depends on what's attached. My rig has the **ESP32-WROOM "WiFi Marauder" backpack** ([my-setup §4](../my-setup.md)) and can take a bare **nRF24L01+** on the SPI pins, but **not both at once** (one backpack occupies the header).

| Tier | Apps | Runs on | On my rig? |
|---|---|---|---|
| **ESP32 Wi-Fi** | Marauder, Ghost ESP, FlipperHTTP family, UART Terminal | external **ESP32** flashed with the matching firmware; UART over GPIO 13/14 @ **115200 8N1** | ✅ have the ESP32-WROOM backpack |
| **Bluetooth LE** | BLE Spam, FindMy, BTHome, BT Trigger, Bluetooth Remote (HID), PC Monitor | the Flipper's **internal BLE (STM32WB55)** — **no add-on needed** | ✅ always available |
| **NRF24 (2.4 GHz)** | NRF24 Tool / Sniffer / Mouse Jacker / Batch | external **nRF24L01+** on the SPI pins (1–8 side) | ➕ need to wire a module (don't own one yet `(verify)`) |

**Key gotcha (ESP32):** the WROOM backpack is **2.4 GHz only — no 5 GHz** ([esp32-marauder-module](../hardware/esp32-marauder-module.md)). 5 GHz is a *chip* capability (ESP32-C5/C6), so no firmware unlocks it on a WROOM. **Only one ESP32 firmware at a time** — Marauder *or* Ghost ESP *or* FlipperHTTP — reflashing is reversible ([esp32-firmware-comparison](../hardware/esp32-firmware-comparison.md)). Companion-app version must track the ESP32 firmware version.

---

## ESP32 Wi-Fi apps

### `esp32_wifi_marauder` — WiFi Marauder companion
**The default Wi-Fi tool on this rig.** A Flipper UI that drives an ESP32 running **ESP32 Marauder** firmware (justcallmekoko) over UART, surfacing Marauder's commands as menus. This is the app the whole [wifi sub-domain](../wifi/README.md) is built around.

- **What it does:** 2.4 GHz Wi-Fi (+ some BLE) recon and attacks — scan, sniff, deauth, beacon/probe spam, evil portal, **WPA handshake + PMKID capture → PCAP**.
- **Key menu items** (the app exposes Marauder command strings): `scanap` / `scansta` (scan APs / stations), `list -a` / `list -s`, `select` (target), `sniffraw` / `sniffbeacon` / `sniffpmkid` (→ EAPOL/PMKID for offline cracking), `attack -t deauth|beacon|probe|rickroll`, `evilportal`, `channel -s <n>`, `update`, `reboot`. Plus a **Save PCAP** toggle and a **scripts** runner (saved command lists).
- **Use-cases:** Wi-Fi scan/recon (**UC-31**), sniff → PCAP (**UC-32**), WPA handshake/PMKID capture (**UC-33** → crack offline, [own-network-audit](../wifi/own-network-audit.md)), deauth (**UC-34**, [deauth](../wifi/deauth.md)), beacon/probe spam (**UC-35**), evil portal (**UC-36**, [evil-portal](../wifi/evil-portal.md)), channel analyzer (**UC-37**), wardrive (**UC-38**). Some BLE recon overlaps [interception](../bluetooth/interception.md) / [airtag detection](../bluetooth/airtag-tracker-detection.md).
- **Hardware / gotchas:** needs an **ESP32** (my WROOM backpack, or the official S2 DevBoard) flashed with **ESP32 Marauder** — pick the **WROOM** target (`old_hardware.bin`), flash via [FZEasyMarauderFlash](https://github.com/SkeletonMan03/FZEasyMarauderFlash) or a web flasher; hold **BOOT** if it won't auto-enter download mode. PCAPs land on the **Marauder's own microSD** (the ~11 KB/s UART is too slow for packet capture — see [esp32-marauder-module](../hardware/esp32-marauder-module.md)). Run on USB power; Wi-Fi TX is hungry. Delete any stale `ESP32CAM_Marauder.fap` to avoid two conflicting apps. **Authorized networks only.**
- **Source:** app https://github.com/0xchocolate/flipperzero-wifi-marauder · catalog https://lab.flipper.net/apps/esp32_wifi_marauder · firmware + wiki https://github.com/justcallmekoko/ESP32Marauder/wiki/flipper-zero

### `ghost_esp` — Ghost ESP suite
The alternative ESP32 firmware + companion app. On my screenless WROOM it's a **software upgrade over Marauder** (same board), worth flashing to compare ([esp32-firmware-comparison](../hardware/esp32-firmware-comparison.md)).

- **What it does:** broad Wi-Fi **and** BLE suite. Over Marauder it adds: **Karma** rogue-AP, **WPA3/SAE** attacks, **live Wireshark-over-USB**, richer **BLE** (BLE spam, **AirTag scan + spoof**, BLE-skimmer detection, **"Flipper finder"** = detect other Flippers), and **GPS wardriving → WiGLE CSV**. On **C5/C6** boards it does **5 GHz** — *not* on a WROOM.
- **Key menu items:** *Wi-Fi* — Scan and List, Beacon Spam (Random/Rickroll/Custom), Deauth, Packet Capture (PMKID/Probe/WPS/EAPOL/Raw), Evil Portal, Network Connection. *Bluetooth* — Flipper Discovery, AirTag Scanning, Raw Packet Capture, BLE Spam Detection. *GPS* — GPS Info, Wardriving (WiGLE export). *Settings* — RGB LED, Channel Hopping, BLE MAC Randomization, Auto-Stop, ESP Reboot.
- **Use-cases:** same Wi-Fi UC-31…UC-38 as Marauder, plus defensive BLE (**UC-40** AirTag/tracker detection, [airtag-tracker-detection](../bluetooth/airtag-tracker-detection.md)) and **UC-39** BLE scan ([interception](../bluetooth/interception.md)). Wardriving pairs with a GPS module ([gpio-addons-current](../hardware/gpio-addons-current.md)).
- **Hardware / gotchas:** needs an **ESP32** flashed with **Ghost ESP** firmware (web flasher: flasher.ghostesp.net, Chrome/Edge — not Firefox; hold BOOT). **Freshness:** the original `Spooks4576/Ghost_ESP` was **archived 2025-04-22**; the live project is the **"GhostESP: Revival"** fork (firmware `GhostESP-Revival/GhostESP`, app `jaylikesbunda/ghost_esp_app`) `(verify which build I run)`. PCAP-to-SD / live-Wireshark are board-dependent (needs an SD on the ESP / USB-CDC) `(verify on WROOM)`. **Authorized targets only.**
- **Source:** firmware https://github.com/GhostESP-Revival/GhostESP · app https://github.com/jaylikesbunda/ghost_esp_app · site/flasher https://ghostesp.net · catalog https://lab.flipper.net/apps/ghost_esp

### `blackhat` — Flipper Blackhat controller `(not an ESP32 app)`
**Premise correction (research):** despite living next to the Wi-Fi apps, `blackhat` is **not** an ESP32/evil-portal FAP. It is the UART controller for the **Flipper Blackhat** — a separate **Linux SBC** (Allwinner A33, onboard 2.4 GHz Wi-Fi, USB-A ×2) by Rootkit Labs. The "Evil Portal"/"Evil Twin" menu items run on the **A33 Linux board**, not an ESP32.

- **What it does:** drives the Blackhat Linux board from the Flipper — Shell, Run Script, Connect WiFi, Deauth Broadcast, Enable AP, **Start Kismet**, **Start Evil Twin**, **Evil Portal**, SSH, Get IP, Reboot.
- **Hardware / gotchas:** requires the **Flipper Blackhat board** (Rootkit Labs) flashed with **flipper-blackhat-os** (Armbian-based) — *not* Marauder/ESP firmware, and **not** something my ESP32-WROOM backpack can run. UART **115200 8N1**. **I do not own this board**, so this app is inert on my rig — listed here only to dispel the "it's an ESP32 evil-portal app" assumption. Whether it's in the official catalog is `(unverified)`; distributed via GitHub releases.
- **Source:** app https://github.com/o7-machinehum/flipper-blackhat-app · hardware https://github.com/o7-machinehum/flipper-blackhat · shop https://shop.rootkitlabs.com/products/flipper-blackhat

### `flip_downloader` + the FlipperHTTP family — Wi-Fi networking (not attacks)
A **different category** from Marauder/Ghost ESP: these give the Flipper real **HTTP/Wi-Fi networking** via an ESP32 flashed with **FlipperHTTP** firmware (jblanked). The ESP32 acts as a Wi-Fi modem; the FAPs are thin serial clients. See also [cool-projects](cool-projects.md) (FlipperHTTP web apps).

- **What they do / the family:**
  - **`flip_downloader` (FlipDownloader)** — download and manage apps/files onto the Flipper over Wi-Fi.
  - **`flip_wifi` (FlipWiFi)** — scan/save Wi-Fi credentials shared by *all* FlipperHTTP apps; also bundles **Deauthentication** and a **Captive Portal** (custom HTML). Menu: Scan · Saved Access Points · Deauthentication · Captive Portal.
  - **`flip_store` (FlipStore)** — in-Flipper app marketplace/installer.
  - Plus the wider jblanked set: Web Crawler, FlipLibrary, FlipWeather (GPS+weather), FlipTrader, FlipSocial, FlipMap, FlipWorld/Free Roam (games).
- **Use-cases:** give the Flipper internet — fetch catalogs, download `.fap`s, weather/stock/dictionary lookups, captive-portal demos (**UC-36**), Wi-Fi scan/connect. Mostly utility/novelty, not red-team.
- **Hardware / gotchas:** needs an **ESP32 flashed with FlipperHTTP** (apps require **firmware v2.0+**) — *a different firmware than Marauder*, so it's a reflash-on-demand "second hat" for the same WROOM board ([esp32-firmware-comparison](../hardware/esp32-firmware-comparison.md)). UART pins **13/14 @ 115200**; supported boards incl. WROOM/S2/S3/C3/C6, Pico W. **SD-folder convention:** each app keeps state under **`/apps_data/<appid>/`** (e.g. `/apps_data/flip_wifi/data/wifi_list.txt` holds the shared Wi-Fi creds) — note the GPIO/FlipperHTTP firmware folders live in the repo per board. Firmware-version mismatch (<v2.0) breaks the apps.
- **Source:** library/firmware https://github.com/jblanked/FlipperHTTP · FlipWiFi https://github.com/jblanked/FlipWiFi · FlipDownloader https://github.com/jblanked/FlipDownloader · catalog https://lab.flipper.net/apps/flip_wifi

### `uart_terminal` — generic ESP32 / UART serial console
A raw **serial terminal** on the Flipper (cool4uma) — talk to *any* UART device directly, no PC. Much of its code derives from the WiFi Marauder app, hence the family resemblance.

- **What it does:** read a device's UART output in a text box; **send commands**; a dedicated **AT-command** keyboard layout; **user-selectable baud**; saved **Fast commands** presets.
- **Use-cases:** send **AT commands to ESP32/ESP8266**, poke router/IoT debug consoles, manually issue Marauder/Ghost ESP commands, general serial debugging — pairs with the GPIO/UART work in [tinkering](../topics/tinkering.md) (USB-UART bridge, UC-42).
- **Hardware / gotchas:** generic — works against whatever UART device you attach. **TX = pin 13, RX = pin 14, GND = pin 8/18**, cross to the device's RX/TX; set baud in-app. No specific firmware required on the far end.
- **Source:** https://github.com/cool4uma/UART_Terminal · catalog https://lab.flipper.net/apps/uart_terminal

---

## Bluetooth LE apps (all run on the Flipper's internal BLE — no add-on)

> Every app in this group uses the **STM32WB55** internal BLE radio — **no ESP32, no nRF24** needed. The Flipper does **BLE only** (no Bluetooth Classic). Deep mechanics: [bluetooth hub](../bluetooth/README.md).

### `ble_spam` — BLE advertising spam
Floods spoofed BLE advertising packets so nearby phones pop pairing prompts. Full mechanics, the iOS-17.2 story, and defenses are in **[bluetooth/ble-spam.md](../bluetooth/ble-spam.md)** — this is just the app entry.

- **What it does:** advertising-layer **nuisance / notification-DoS** — Apple "Sour Apple"/Continuity, Android Fast Pair, Windows Swift Pair, Samsung EasySetup, NameFlood, "Kitchen Sink" (all at once). **No connection, no data theft.**
- **Key options:** attack list (incl. **iOS 17 Lockup Crash** = CVE-2023-42941 payload, **Apple Device Popup**, **Android Device Connect**, **Samsung Buds/Watch**, **Windows Device Found**); **advertising interval** (20/50/100/200/500 ms); **Random MAC** toggle; payload mode (standard vs. bruteforce).
- **Use-cases:** **UC-29** (BLE spam) — research/awareness/prank only. Largely a **party trick on patched devices** (iOS ≥ 17.2 rate-limits).
- **Hardware / gotchas:** **internal BLE only — confirmed no external hardware** (the "ESP32 BLE spam" association is a confusion with the Marauder/Ghost ESP BLE module, which is unrelated). **Custom-firmware-only** — ships in **Momentum**/Unleashed, **never** official. Range ~5 m. Credits: app/randomization **WillyJL**, Apple+crash **ECTO-1A**, Android/Win **Spooks4576**. **Own devices / RF-isolated lab only** — blasting popups at others is harassment ([legal](../legal-and-safety.md)).
- **Source:** Momentum apps https://github.com/Next-Flip/Momentum-Apps (`ble_spam`) · AppleJuice/CVE https://github.com/ECTO-1A/AppleJuice · CVE https://nvd.nist.gov/vuln/detail/CVE-2023-42941

### `findmy` (FindMyFlipper) — broadcast as a Find My tag
The **inverse** of tracker detection: make the Flipper advertise as an Apple Find My / AirTag (also Samsung SmartTag, Tile) beacon so I can locate a lost Flipper. Detail in **[bluetooth/airtag-tracker-detection.md §5](../bluetooth/airtag-tracker-detection.md)**.

- **What it does:** broadcasts a Find-My-network beacon over internal BLE (OpenHaystack-style); the Flipper itself becomes locatable.
- **Key options:** **Beacon Interval**, **Transmit Power** (range vs. battery); **Register Tag** → Import from File (`.keys`/`.txt`) or enter MAC + Payload manually.
- **Provisioning (two paths):** (a) **clone** a real tag's MAC + payload — sniff with nRF Connect / an ESP32, then **kill the original's battery** so it stops rotating keys and orphaning the clone; (b) **generate fresh OpenHaystack keys** via the Anisette Docker server + `AirTagGeneration` scripts (location retrieval needs an Apple ID / macless-haystack). Files in `/apps_data/findmy/`.
- **Use-cases:** **UC-30** (FindMy Flipper) — find a lost/stolen *own* Flipper. It's an **emulator, not a detector** (that's UC-40, same radio, opposite direction).
- **Hardware / gotchas:** **internal BLE for broadcasting — no add-on** (the optional ESP32 is only for the *sniffing* step in path a). Apple is the mature target; **Samsung/Tile are experimental** `(unverified robustness)`. Apple's own unknown-tracker alerts may flag it. **Tag *my own* Flipper only**, never anyone/anything else ([legal](../legal-and-safety.md)).
- **Source:** https://github.com/MatthewKuKanich/FindMyFlipper · catalog https://lab.flipper.net/apps/findmy

### `bthome` — BTHome v2 sensor advertiser
Turns the Flipper into a **BTHome v2** BLE beacon (ghedo / flipper-playground) so **Home Assistant** auto-discovers it as a sensor device.

- **What it does:** broadcasts battery level + a button event in the open **BTHome v2** advertising format (no pairing; HA native auto-discovery via the BTHome integration).
- **Key options:** **effectively none** — minimal demo app; press **OK** to start the beacon. Broadcasts real battery %; BLE packet-size limits prevent adding more sensors. Treat as **unencrypted** (no bindkey UI) `(verify)`.
- **Use-cases:** zero-hardware Home Assistant integration; use the **OK button as a wireless trigger** for HA automations; reference for the BTHome format. (Home Assistant context: [cool-projects](cool-projects.md).) No UC-ID — utility.
- **Hardware / gotchas:** **internal BLE — no add-on.** Receiving side needs **Home Assistant + the BTHome integration** and a BLE adapter/proxy in range. Targets **BTHome v2** (v1 deprecated). Distinct from OFW's generic `example_ble_beacon` (which is not BTHome).
- **Source:** catalog https://lab.flipper.net/apps/bthome · source https://github.com/ghedo/flipper-playground/tree/master/bthome · standard https://bthome.io

### `bt_trigger` — BLE camera shutter / intervalometer
**Premise note (research):** `bt_trigger` is a **BLE camera remote**, *not* a "trigger actions on BLE events" app. The Flipper advertises as a BLE HID device ("Control") and fires a phone camera's shutter.

- **What it does:** wireless camera shutter + **intervalometer** (timelapse) over internal BLE HID.
- **Key controls:** **Right** = one photo · **OK** = repeated photos (intervalometer) · **Up/Down** = shot delay · **Left** = reset counter.
- **Use-cases:** hands-free/long-exposure shutter, **timelapses** (astro/sunset), group selfies. No KB UC-ID — adjacent to the HID-remote family ([badusb](../capabilities/badusb.md) UC-28).
- **Hardware / gotchas:** **internal BLE — no add-on.** Works as a BLE-HID **volume-button** emulator → phone must shoot on volume-up (native on iOS; some Android camera apps need it enabled `(verify)`). Pair the Flipper ("Control") **first**, then open the camera app; may conflict with the Flipper mobile-app BLE link.
- **Source:** https://github.com/Nem0oo/flipper-zero-bluetooth-trigger · catalog https://lab.flipper.net/apps/bt_trigger

### `hid_ble` — Bluetooth Remote (BLE HID keyboard/mouse/media)
The **stock-firmware** "Bluetooth Remote" — the Flipper as a BLE HID peripheral controlling a phone/PC. Reached via **Apps → Bluetooth → Remote** (also runs wired via Apps → USB → Remote). This is the built-in HID-over-BLE feature, not a third-party FAP.

- **What it does / sub-modes:** **Keynote** (slide clicker, + vertical), **Keyboard** (with Ctrl/Alt/Cmd), **Media** (play/pause, track, volume), **Mouse** (move + click), **Mouse Jiggler** (keep host awake), **Mouse Clicker** (auto-click), **TikTok/Shorts** controller.
- **Use-cases:** **UC-28** (BLE clicker / kbd-mouse remote) — presentation clicker, media control, mouse jiggler / keep-awake (overlaps **UC-50**, [badusb](../capabilities/badusb.md)), basic wireless mouse+keyboard, accessibility.
- **Hardware / gotchas:** **internal BLE (STM32WB55) — no add-on; BLE only, no Classic.** **Stock firmware** (no CFW needed). **One paired host at a time**; shows as "Control <FlipperName>"; iOS cursor/TikTok modes may need **AssistiveTouch**. Unpair via the app + forget on the host.
- **Source:** docs https://docs.flipper.net/zero/apps/controllers · firmware https://github.com/flipperdevices/flipperzero-firmware/tree/dev/applications/system/hid_app

### `pc_monitor` — PC stats over Bluetooth
Shows live **PC CPU / RAM / GPU / VRAM usage** on the Flipper screen, fed by a companion desktop agent. **Premise corrections (research):** the BLE app is by **TheSainEyereg (@Olejka)** (not "Z3BR0"), and it reports **usage only — no temperatures / no network**.

- **What it does:** ambient secondary display of CPU/RAM/GPU/VRAM load (bars + connection-state views); the desktop agent pushes the numbers over BLE serial.
- **Key options:** essentially **none** — display-only, not configurable (no refresh-rate / metric / port settings).
- **Use-cases:** glanceable load indicator for a gaming/render PC; "is my machine pegged?" desk widget. No UC-ID — utility.
- **Hardware / gotchas:** **internal BLE — no add-on** (the original uses the `btleplug` BLE crate). **Requires the desktop agent** (Rust, `sysinfo` crate) — Flipper shows nothing without it; **GPU stats are Nvidia-only**. A separate **USB fork (DonJulve)** exists if you want serial instead of BLE — use the TheSainEyereg app for BLE. Linux pairing needs manual `bluetoothctl`.
- **Source:** app https://github.com/TheSainEyereg/flipper-pc-monitor · backend https://github.com/TheSainEyereg/flipper-pc-monitor-backend · catalog https://lab.flipper.net/apps/pc_monitor

---

## NRF24 apps (need an external nRF24L01+ on the SPI pins)

> The Flipper has **no usable 2.4 GHz radio of its own** for this — nRF24 work needs a dedicated **nRF24L01+** wired to the GPIO over SPI. The apps live in **`/ext/apps/GPIO/NRF24`**. Capability context: [gpio-addons-current §NRF24](../hardware/gpio-addons-current.md), [addons-explained](../hardware/addons-explained.md).

### Wiring (canonical — identical across mothball187, vad7, RogueMaster docs)
| Flipper pin | → nRF24L01+ |
|---|---|
| 2 / PA7 | MOSI |
| 3 / PA6 | MISO |
| 4 / PA4 | CSN |
| 5 / PB3 | SCK |
| 6 / PB2 | CE |
| 8 / GND | GND |
| 9 / 3V3 | VCC |

IRQ is left unconnected. **Stability tip (all repos):** solder a **3.3–10 µF cap (+ optional 0.1 µF)** across the module's VCC/GND — the nRF24 draws current spikes on TX that the Flipper's 3V3 rail handles poorly, and a missing cap is the #1 "module not found / no captures" cause. The module sits on the **1–8 (SPI) side**, so it can't co-exist with the Marauder backpack (9–18) — but it *can* share with nothing else needing SPI.

### `nrf24tool` — the app that ships in Momentum's GPIO/NRF24 folder
The current Momentum unified NRF24 app (OuinOuin74), built on mothball187's sniffer/mousejack code + the Flipper **BadUSB** engine.

- **What it does:** one app for **TX / RX / Sniffer / Mouse Jacker** on an nRF24L01+.
- **Key settings (per mode):** *TX* — channel, data rate, address width, TX address, payload size, auto-ACK, TX power, ARC/ARD, hex/ASCII/file input. *RX* — channel, data rate, 6 pipes (size/ACK/address each), CRC, RPD, hex/ASCII out. *Sniffer* — min/max channel, scan-time per channel, data rate; **auto-detects Unifying-style receiver addresses**. *Mouse Jacker* — target address (from the sniffed list), keyboard layout, data rate, TX power, retry count, key delay; injects a Flipper **Ducky/BadUSB** payload.
- **Use-cases:** **UC-57** (2.4 GHz HID mousejacking) — Sniffer finds a wireless keyboard/mouse dongle's address → Mouse Jacker injects keystrokes; plus general nRF24 TX/RX for protocol RE.
- **Hardware / gotchas:** **needs the nRF24L01+ (wiring above).** Mouse Jacker only works against **vulnerable, unencrypted** Unifying-style receivers. Lists Flipper FW **1.1.2+** `(verify)`. **Audit your own devices only** ([legal](../legal-and-safety.md)).
- **Source:** https://github.com/OuinOuin74/nrf24tool

### `nrf24scan` / `nrf24mousejack` — the original mothball187 Sniffer + Mouse Jacker
The canonical Flipper port everything descends from (bundled historically in RogueMaster/Unleashed as **"NRF24: Sniffer"** / **"NRF24: Mouse Jacker"**).

- **What it does:** **Sniffer** sweeps 2.4 GHz channels to discover nRF24 device addresses; **Mouse Jacker** uses a discovered address + a Ducky payload (`.txt`) to inject keystrokes into vulnerable 2.4 GHz HID.
- **Use-cases:** **UC-57** — locate a dongle's address, then demo MouseJack against your own unencrypted keyboard/mouse.
- **Hardware / gotchas:** **nRF24L01+ required** (wiring above). "Educational / own equipment only." Attribution: sniffing technique **Travis Goodspeed**; MouseJack vuln **Marc Newlin / Bastille**; mousejack impl inspired by **JackIt**.
- **Source:** https://github.com/mothball187/flipperzero-nrf24 · RogueMaster doc https://github.com/RogueMaster/flipperzero-firmware-wPlugins/blob/420/documentation/NRF24.md

### Related NRF24 apps
- **`nrf24scan` (vad7)** — "scanner with resend": sniff any valid packets *or* watch specific MAC(s); logs to file, **replays captured packets**, ESB decode, bit-shift recovery. Channel 0–125, rate 0.25/1/2 Mbps, 6 address pipes. https://github.com/vad7/nrf24scan
- **`nRF24-Batch` (vad7)** — **not an attack tool**: sends batch read/write commands to *your own* nRF24-equipped microcontrollers (home-automation telemetry/config). Ships in Momentum per its changelog. https://github.com/vad7/nRF24-Batch
- **Channel scanner / monitor / jammer** (community, not necessarily in the default folder): `htotoo/NRF24ChannelScanner` (channel activity), `CyberDemon73/flipperzero-nrf24monitor` (SPI/wiring tester — handy for debugging the cap/wiring), nRF24 jammer forks (2.4 GHz noise — legally sensitive).

### MouseJack background (Bastille, confirmed)
Discovered by **Marc Newlin** (Bastille), disclosed **2016-02-23**; tracked as **CERT/CC VU#981271**. Affected vendors per Bastille: **Logitech (Unifying), Microsoft, Dell, Lenovo, HP, Gigabyte, AmazonBasics** and others using 2.4 GHz dongles. Root cause: mouse-movement packets are unencrypted and many dongles fail to enforce that injected packets are encrypted/authenticated, so crafted **keystroke** packets are forwarded to the OS as legitimate HID input (range up to ~100 m). Per-vendor CVE numbers exist but aren't in Bastille's primary page `(verify before citing specific CVEs)`.

---

## Quick reference — what's installed vs. what runs

| App | Group | Needs | UC | Runs on my rig now? |
|---|---|---|---|---|
| `esp32_wifi_marauder` | ESP32 Wi-Fi | ESP32 + Marauder fw | UC-31…38 | ✅ (WROOM backpack) |
| `ghost_esp` | ESP32 Wi-Fi/BLE | ESP32 + Ghost ESP fw | UC-31…40 | ✅ after reflash |
| `blackhat` | (Linux SBC) | Flipper Blackhat board | — | ❌ no board |
| `flip_downloader` / `flip_wifi` / `flip_store` | ESP32 Wi-Fi (net) | ESP32 + FlipperHTTP fw | UC-36 | ✅ after reflash |
| `uart_terminal` | UART | any UART device | UC-42-adj | ✅ |
| `ble_spam` | BLE | internal BLE | UC-29 | ✅ |
| `findmy` | BLE | internal BLE | UC-30 | ✅ |
| `bthome` | BLE | internal BLE + HA | — | ✅ |
| `bt_trigger` | BLE | internal BLE | — | ✅ |
| `hid_ble` (Bluetooth Remote) | BLE | internal BLE (stock) | UC-28 | ✅ |
| `pc_monitor` | BLE | internal BLE + PC agent | — | ✅ |
| `nrf24tool` / `nrf24scan` / mousejack | NRF24 | nRF24L01+ on SPI | UC-57 | ➕ need module |

---

## Open questions / to research
- **Which exact build runs on my ESP32 backpack** — Marauder vs. Ghost ESP (Revival), and version — confirm via each app's about/version screen `(verify)`.
- Does **Ghost ESP** on my *screenless WROOM* expose live-Wireshark / PCAP-to-SD, or are those board-gated to ones with an ESP-side SD `(verify)`.
- Confirm `blackhat` is **not** in the official catalog and is genuinely inert without the Rootkit Labs board (drop it from the rig if so).
- **FlipperHTTP folder layout** on the SD for `flip_store` / `flip_downloader` (is it `/apps_data/<appid>/` for all of them, like `flip_wifi`?) `(verify)`.
- Does my `ble_spam` build still meaningfully affect any **patched** mainstream OS, or is it now NameFlood/legacy noise (cross-ref [ble-spam open questions](../bluetooth/ble-spam.md)).
- `bthome` — does any current build expose a **bindkey** for encrypted BTHome v2, or is it plaintext-only `(verify)`.
- Acquire an **nRF24L01+** (+ decoupling cap) to actually exercise UC-57; confirm which NRF24 `.fap`s are in *my* Momentum build's `/ext/apps/GPIO/NRF24` `(verify)`.
- Whether to keep **UART Terminal** as the manual fallback for driving Marauder/Ghost ESP commands when the companion app misbehaves.

## Sources
- Rig + mounting/power: [my-setup §4](../my-setup.md) · [esp32-marauder-module](../hardware/esp32-marauder-module.md) · which ESP32 fw: [esp32-firmware-comparison](../hardware/esp32-firmware-comparison.md) · board specs: [gpio-addons-current](../hardware/gpio-addons-current.md)
- Marauder: https://github.com/0xchocolate/flipperzero-wifi-marauder · https://github.com/justcallmekoko/ESP32Marauder/wiki/flipper-zero · flasher https://github.com/SkeletonMan03/FZEasyMarauderFlash
- Ghost ESP (Revival): https://github.com/GhostESP-Revival/GhostESP · https://github.com/jaylikesbunda/ghost_esp_app · https://ghostesp.net
- FlipperHTTP: https://github.com/jblanked/FlipperHTTP · https://github.com/jblanked/FlipWiFi · https://github.com/jblanked/FlipDownloader
- UART Terminal: https://github.com/cool4uma/UART_Terminal
- Flipper Blackhat: https://github.com/o7-machinehum/flipper-blackhat-app · https://github.com/o7-machinehum/flipper-blackhat
- BLE Spam: https://github.com/Next-Flip/Momentum-Apps · https://github.com/ECTO-1A/AppleJuice · CVE-2023-42941 https://nvd.nist.gov/vuln/detail/CVE-2023-42941 — mechanics: [bluetooth/ble-spam.md](../bluetooth/ble-spam.md)
- FindMyFlipper: https://github.com/MatthewKuKanich/FindMyFlipper — mechanics: [bluetooth/airtag-tracker-detection.md](../bluetooth/airtag-tracker-detection.md)
- BTHome: https://github.com/ghedo/flipper-playground/tree/master/bthome · https://bthome.io
- BT Trigger: https://github.com/Nem0oo/flipper-zero-bluetooth-trigger
- Bluetooth Remote (HID): https://docs.flipper.net/zero/apps/controllers · https://github.com/flipperdevices/flipperzero-firmware/tree/dev/applications/system/hid_app
- PC Monitor: https://github.com/TheSainEyereg/flipper-pc-monitor
- NRF24: https://github.com/OuinOuin74/nrf24tool · https://github.com/mothball187/flipperzero-nrf24 · https://github.com/vad7/nrf24scan · https://github.com/vad7/nRF24-Batch · MouseJack https://www.bastille.net/research/vulnerabilities/mousejack/technical-details
