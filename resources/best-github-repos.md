---
title: Best GitHub Repos (Curated)
domain: resources
type: resource-list
status: detailed
summary: Curated GitHub repos by category, with maintenance flags
hardware: []
use_cases: []
related: [resources/tools-and-software.md, resources/learning-and-docs.md, resources/github-landscape.md, resources/cool-projects.md, firmware/README.md]
tags: [github, repos, curated, firmware, apps, sub-ghz, nfc, esp32]
last_verified: 2026-06-19
---

# Best GitHub Repos (Curated)

> **TL;DR —** The utilitarian "best by category" list of canonical Flipper repos (firmware, apps, Sub-GHz, NFC, IR, BadUSB, ESP32, dev tooling), each flagged active/(verify)/archived. Sort GitHub by recently-updated — this list ages.
> See [tools & software](./tools-and-software.md) · [learning & docs](./learning-and-docs.md) · [firmware](../firmware/README.md). Part of the [KB](../README.md).

> **How to read flags:** *active* = commits within the last few months; *(verify)* = couldn't confirm recency, re-check before relying; *(archived)* = read-only/superseded. Always sort GitHub by "recently updated" — this list ages.

## Meta-lists (start here)
- **djsime1/awesome-flipperzero** — https://github.com/djsime1/awesome-flipperzero — the master list everything links back to; active.
- **UberGuidoZ/Flipper** — https://github.com/UberGuidoZ/Flipper — huge "everything" playground (dumps, refs, scripts); active.
- **RogueMaster/awesome-flipperzero-withModules** — https://github.com/RogueMaster/awesome-flipperzero-withModules — module-focused variant tuned for RogueMaster CFW; active.
- **Awesome-Flipper (web)** — https://awesome-flipper.com — browsable knowledgebase / FAQ; active.
- **123fzero/flipper-zero-awesome** — https://github.com/123fzero/flipper-zero-awesome — curated app/plugin/game catalog; (verify).

## Firmware
- **Official** — https://github.com/flipperdevices/flipperzero-firmware — upstream OFW; active.
- **Unleashed** — https://github.com/DarkFlippers/unleashed-firmware — your CFW; relaxed regional TX, extra apps; active.
- **Momentum** — https://github.com/Next-Flip/Momentum-Firmware — Xtreme successor, most customizable UX; ~8k★, active (Mar 2026 builds).
- **RogueMaster** — https://github.com/RogueMaster/flipperzero-firmware-wPlugins — kitchen-sink build (animations, every plugin); active but heavy.

## Apps / plugin packs
- **xMasterX/all-the-plugins** — https://github.com/xMasterX/all-the-plugins — the big external-app megapack (Unleashed-aligned); active.
- **Next-Flip/Momentum-Apps** — https://github.com/Next-Flip/Momentum-Apps — apps tweaked for Momentum; active.
- **flipperdevices/flipperzero-good-faps** — https://github.com/flipperdevices/flipperzero-good-faps — official first-party apps bundled in OFW; active.

## Sub-GHz
- **tobiabocchi/flipperzero-bruteforce** — https://github.com/tobiabocchi/flipperzero-bruteforce — generates `.sub` brute-force playlists (gates/barriers, fixed-code); (verify).
- **jimilinuxguy/flipperzero-touchtunes** — https://github.com/jimilinuxguy/flipperzero-touchtunes — TouchTunes jukebox remote `.sub` set; (verify).
- **Sub-GHz captures** live mostly inside the firmware repos and UberGuidoZ/Flipper — search those before standalone repos.

## NFC / RFID
- **noproto/FlipperMfkey** — https://github.com/noproto/FlipperMfkey — on-device MIFARE Classic 1K/4K key recovery (mfkey32) FAP; ships in App Hub; active.
- **equipter/mfkey32v2** — https://github.com/equipter/mfkey32v2 — desktop helper: pulls `.mfkey32.log`, computes keys, pushes back to user dict; (verify).
- **luu176/Metroflip** — https://github.com/luu176/Metroflip — multi-protocol transit-card reader/parser (Metrodroid-inspired; Suica/Octopus/DESFire/FeliCa); active.
- **Gioman101/FlipperAmiibo** — https://github.com/Gioman101/FlipperAmiibo — Amiibo dumps in Flipper NFC format; (verify).
- **nortakales/flipper-zero-tonies** — https://github.com/nortakales/flipper-zero-tonies — Toniebox (Tonie) NFC tags; (verify).

## Infrared (IRDB)
- **logickworkshop/Flipper-IRDB** — https://github.com/logickworkshop/Flipper-IRDB — the maintained IR database fork (~2.5k files, CC0); active (Apr 2026).
- **Lucaslhm/Flipper-IRDB** — https://github.com/Lucaslhm/Flipper-IRDB — original upstream; logickworkshop is the live fork now.

## BadUSB payloads
- **I-Am-Jakoby/Flipper-Zero-BadUSB** — https://github.com/I-Am-Jakoby/Flipper-Zero-BadUSB — near plug-and-play DuckyScript payloads + helper tooling; active. *(lab use only)*
- **FalsePhilosopher/badusb** — https://github.com/FalsePhilosopher/badusb — payload library sorted by exfil/phishing/recon/remote-access; (verify).
- **MarkCyber/BadUSB** — https://github.com/MarkCyber/BadUSB — teaching-oriented payload collection; (verify).

## ESP32 / Wi-Fi backpacks
- **justcallmekoko/ESP32Marauder** — https://github.com/justcallmekoko/ESP32Marauder — the WiFi/BLE pentest firmware (deauth, beacon, sniff); active (v1.12.x, May 2026).
- **GhostESP-Revival/GhostESP** — https://github.com/GhostESP-Revival/GhostESP — actively-maintained Ghost ESP firmware (2.4/5 GHz, evil portal, PCAP); active.
- **jaylikesbunda/ghost_esp_app** — https://github.com/jaylikesbunda/ghost_esp_app — Flipper companion app for GhostESP Revival; active.
- **C5Lab/projectZero** — https://github.com/C5Lab/projectZero — ESP32-C5 evil-twin/deauth/WPA3-SAE overflow w/ Flipper CLI; (verify, newer).
- **eried/flipperzero-mayhem** — https://github.com/eried/flipperzero-mayhem — "Mayhem Fin" ESP-based add-on board project; (verify).

## GPS / wardriving
- **Sil333033/flipperzero-wardriver** — https://github.com/Sil333033/flipperzero-wardriver — ESP32+GPS wardriving, writes CSV (Wigle-style) to SD; (verify).
- **Sil333033/flipperzero-gps-lpuart** / **ezod/flipperzero-gps** — https://github.com/Sil333033/flipperzero-gps-lpuart · https://github.com/ezod/flipperzero-gps — NMEA-0183 serial GPS display apps; (verify).

## Hardware / boards
- **Chrismettal/flipper-zero-backpacks** — https://github.com/Chrismettal/flipper-zero-backpacks — open-hardware GPIO "backpack" PCB designs; (verify).
- **lomalkin/flipperzero-protoboards-kicad** — https://github.com/lomalkin/flipperzero-protoboards-kicad — KiCad proto-board templates for the GPIO header; (verify).

## Animation / asset packs
- **skizzophrenic/Talking-Sasquach** — https://github.com/skizzophrenic/Talking-Sasquach — Talking Sasquach's animation pack + creations; (verify).
- **iakat/awesome-flipperzero-pack** — https://github.com/iakat/awesome-flipperzero-pack — packaged asset/app bundle releases; (verify).
- Largest animation sets ship inside **RogueMaster** (ALL / anime / themed builds) — see Firmware above.

## Dev tooling
- **flipperdevices/flipperzero-ufbt** — https://github.com/flipperdevices/flipperzero-ufbt — micro Flipper Build Tool: scaffold/build/deploy a single FAP without the full SDK; active.
- **jamisonderek/flipper-zero-tutorials** — https://github.com/jamisonderek/flipper-zero-tutorials — code-along app/protocol tutorials (links his Discord + YouTube); active.

## Browse by topic (catch new tools)
- https://github.com/topics/flipperzero · https://github.com/topics/flipper-zero · https://github.com/topics/flipper-app — sort by **recently-updated** to surface fresh repos this list misses.

## Open questions / to research
- Re-run maintenance checks on the *(verify)*-flagged repos (last-commit dates) and promote/demote.
- Confirm which Sub-GHz brute-force repos still match current OFW/Unleashed `.sub` format (codes evolve).
- Find a maintained payment-EMV (contactless bank card) parser, if any exists beyond transit (Metroflip is transit-only).
- Track whether GhostESP-Revival vs trevjohnand/Ghost_ESP_revival forks diverge — pick the canonical one.
- Add a vetted Sub-GHz/NFC sample-dump archive (legal regions) for testing.

## Sources
- https://github.com/djsime1/awesome-flipperzero
- https://github.com/Next-Flip/Momentum-Firmware/releases
- https://github.com/noproto/FlipperMfkey · https://github.com/luu176/Metroflip
- https://github.com/logickworkshop/Flipper-IRDB
- https://github.com/justcallmekoko/ESP32Marauder/releases · https://github.com/GhostESP-Revival/GhostESP · https://github.com/jaylikesbunda/ghost_esp_app
- https://github.com/Sil333033/flipperzero-wardriver · https://github.com/flipperdevices/flipperzero-ufbt
