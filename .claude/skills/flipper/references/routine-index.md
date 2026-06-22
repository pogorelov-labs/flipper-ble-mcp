# Routine index — task → KB doc → tools

Your **first stop in ORIENT**. Find the row matching the user's intent, read the linked doc's TL;DR + body,
then execute. Paths are relative to the repo root. **Legend:** 🟢 passive (fine to run) · 🔴 active (RF/emulate/
inject/spam — needs the user's own gear + confirmation, see [`legal-and-safety.md`](legal-and-safety.md)) ·
📡 **USB-takeover app → must drive over BLE and read results from SD** (not the screen).

## Wi-Fi — ESP32 Marauder backpack (2.4 GHz only) · 📡 BLE-driven
| Task | UC | KB doc | Tools / app |
|---|---|---|---|
| 🟢 Scan APs / nearby networks | UC-31 | [`wifi/marauder-mcp-scan.md`](wifi/marauder-mcp-scan.md) (recipe) · [`wifi/recon-and-attacks.md`](wifi/recon-and-attacks.md) | `app_launch /ext/apps/GPIO/esp32_wifi_marauder.fap` → `Scan ap` → `press back` → `storage_read …/logs/scanap_N.log` |
| 🟢 Sniff → PCAP / analyzer / detect-deauth | UC-32/37/54 | [`wifi/recon-and-attacks.md`](wifi/recon-and-attacks.md) | same launch; read `…/marauder/pcaps/` |
| 🟢 Audit my own WPA (handshake/PMKID) | UC-33 | [`wifi/wpa-handshake-pmkid.md`](wifi/wpa-handshake-pmkid.md) · [`wifi/own-network-audit.md`](wifi/own-network-audit.md) | sniff EAPOL/PMKID → hcxtools → hashcat (off-device) |
| 🔴 Deauth · beacon/probe spam · evil portal | UC-34/35/36 | [`wifi/deauth.md`](wifi/deauth.md) · [`wifi/recon-and-attacks.md`](wifi/recon-and-attacks.md) · [`wifi/evil-portal.md`](wifi/evil-portal.md) | active — confirm + authorize first |

> **Also open** [`hardware/esp32-marauder-module.md`](hardware/esp32-marauder-module.md) for board gotchas an agent
> otherwise misses: **2.4 GHz-only**, **dual-SD** (the Marauder has its *own* microSD), don't hot-mount (freeze),
> power-hungry. **PCAP destination is rig-dependent** — the companion app may save to the *Flipper* SD
> `/ext/apps_data/marauder/pcaps/` (gated by `save_pcaps_here.setting`, observed on this rig) *or* the ESP32's own
> card; `storage_list` to confirm, don't assume.

## Sub-GHz — CC1101 (internal + ext)
| Task | UC | KB doc | Tools / app |
|---|---|---|---|
| 🟢 Read / analyze / save a signal | UC-04…09 | [`capabilities/sub-ghz.md`](capabilities/sub-ghz.md) · [`resources/apps-subghz.md`](resources/apps-subghz.md) | `app_launch "Sub-GHz"`; `read_latest /ext/subghz` |
| 🔴 Transmit / replay a `.sub` | UC-10…12 | [`capabilities/sub-ghz.md`](capabilities/sub-ghz.md) · [`topics/subghz-region-lock.md`](topics/subghz-region-lock.md) | `transmit_subghz(path)` — region-gated; `.sub` libs in [`resources/subghz-device-repos.md`](resources/subghz-device-repos.md) |

## NFC (13.56 MHz) & 125 kHz RFID
| Task | UC | KB doc | Tools / app |
|---|---|---|---|
| 🟢 Read a card (guided) | UC-15…18 | [`capabilities/nfc-rfid.md`](capabilities/nfc-rfid.md) · [`cards/README.md`](cards/README.md) · [`resources/apps-nfc.md`](resources/apps-nfc.md) | `app_launch "NFC"` → user taps + Saves → `read_latest /ext/nfc` |
| 🟢 Card theory / cloneability | UC-19…23 | [`cards/mifare.md`](cards/mifare.md) · [`cards/nfc-theory.md`](cards/nfc-theory.md) · [`cards/cloning-matrix.md`](cards/cloning-matrix.md) · [`cards/iclass-picopass.md`](cards/iclass-picopass.md) | reference only |
| 🟢 Read LF tag (guided) | UC-15 | [`cards/lf-125khz.md`](cards/lf-125khz.md) · [`resources/apps-rfid-ibutton-infrared.md`](resources/apps-rfid-ibutton-infrared.md) | `app_launch "125 kHz RFID"` → `read_latest /ext/lfrfid` |
| 🔴 Emulate / clone / write a card | UC-20…23 | [`cards/cloning-matrix.md`](cards/cloning-matrix.md) | active — your own cards only; **never dump/store EMV PANs or keys** |

## iButton · Infrared
| Task | UC | KB doc | Tools / app |
|---|---|---|---|
| 🟢 Read iButton (guided) / 🔴 emulate | UC-24 | [`capabilities/ibutton.md`](capabilities/ibutton.md) | `app_launch "iButton"` → `read_latest /ext/ibutton` |
| 🟢 Learn IR / 🔴 transmit IR | UC-01…03 | [`capabilities/infrared.md`](capabilities/infrared.md) · [`resources/apps-rfid-ibutton-infrared.md`](resources/apps-rfid-ibutton-infrared.md) | `app_launch "Infrared"` or `transmit_infrared(path)` — your own devices |

## BadUSB · BLE · NRF24 · GPIO
| Task | UC | KB doc | Tools / app |
|---|---|---|---|
| 🔴 BadUSB / HID payload | UC-25…28/50 | [`capabilities/badusb.md`](capabilities/badusb.md) · [`resources/apps-badusb-automotive-misc.md`](resources/apps-badusb-automotive-misc.md) | `run_badusb` / `app_launch "Bad USB"` — injects keystrokes into the host; confirm |
| 🟢 BLE recon / detect tracker · 🔴 BLE spam | UC-29/30/39/40/41/64 | [`bluetooth/README.md`](bluetooth/README.md) + siblings · [`resources/apps-esp-ble-nrf24.md`](resources/apps-esp-ble-nrf24.md) | per-doc; spam is active |
| 🔴 NRF24 (mousejack etc.) | — | [`hardware/gpio-addons-current.md`](hardware/gpio-addons-current.md) · [`resources/apps-esp-ble-nrf24.md`](resources/apps-esp-ble-nrf24.md) | active — authorized only |
| 🟢 GPIO read / 🔴 drive | — | [`hardware/README.md`](hardware/README.md) · [`hardware/gpio-addons-potential.md`](hardware/gpio-addons-potential.md) | `gpio_read` / `gpio_write` / `gpio_set_mode` |

## Device status · files · firmware (always 🟢)
| Task | KB doc | Tools |
|---|---|---|
| Status / battery / info / uptime | [`resources/flipper-read-mcp-server.md`](resources/flipper-read-mcp-server.md) | `mcp__flipper__status` · `device_info` · `mcp__flipper-ble__power_info` |
| Browse / read SD files | — | `storage_list` · `storage_read` · `storage_tree` · `read_latest` |
| Scheduled health monitor | [`resources/flipper-healthwatch.md`](resources/flipper-healthwatch.md) | `mcp__flipper-ble__healthwatch` |
| Firmware / migration / setup | [`firmware/README.md`](firmware/README.md) · [`resources/mcp-setup-claude-code.md`](resources/mcp-setup-claude-code.md) | reference |

## Cross-cutting method (read once)
- **Driving algorithm + menu maps:** [`resources/flipper-control-playbook.md`](resources/flipper-control-playbook.md)
- **BLE method + full tool list + the USB-takeover→BLE rule:** [`resources/flipper-ble-control.md`](resources/flipper-ble-control.md)
- **Worked 📡 exemplar (USB-takeover app → BLE → SD log):** [`wifi/marauder-mcp-scan.md`](wifi/marauder-mcp-scan.md)

> If a request has **no row here**, that's a CAPTURE candidate — solve it, then run `/flipper-learn` so the next
> person finds a row.
