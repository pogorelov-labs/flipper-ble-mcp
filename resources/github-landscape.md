---
title: GitHub Landscape — Leaderboard, People & Tracking
domain: resources
type: resource-list
status: detailed
summary: Leaderboard + people — top repos by stars, devs/orgs to follow, the ESP32 scene
hardware: []
use_cases: []
related: [resources/best-github-repos.md, resources/cool-projects.md, resources/notable-apps-and-data.md, hardware/gpio-addons-current.md]
tags: [github, leaderboard, stars, developers, esp32, tracking]
last_verified: 2026-06-19
---

# GitHub Landscape — Leaderboard, People & Tracking

> **TL;DR —** The Flipper GitHub ecosystem by popularity and people — top repos by stars, the developers/orgs who drive it, the adjacent ESP32 firmware scene (relevant to a Marauder board), and how to track what's new. Complements the by-category and fun lists.
> Complements [best-github-repos](best-github-repos.md) (by category) and [cool-projects](cool-projects.md) (fun/novel). Part of the [KB](../README.md).

Three lenses the category lists don't give: **what's biggest**, **who drives it**, and **how to track new stuff**.

## Top repos by stars (snapshot ~mid-2026; counts drift)
| # | Repo | ~★ | What |
|---|---|---|---|
| 1 | [djsime1/awesome-flipperzero](https://github.com/djsime1/awesome-flipperzero) | 23.6k | The master resource list |
| 2 | [DarkFlippers/unleashed-firmware](https://github.com/DarkFlippers/unleashed-firmware) | 21.7k | Unleashed CFW |
| 3 | [flipperdevices/flipperzero-firmware](https://github.com/flipperdevices/flipperzero-firmware) | 16.2k | Official firmware |
| 4 | [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) | 11.2k | Wi-Fi/BLE toolkit (ESP32) — *your backpack* |
| 5 | [Flipper-XFW/Xtreme-Firmware](https://github.com/Flipper-XFW/Xtreme-Firmware) | 9.9k | Xtreme CFW — **archived → Momentum** |
| 6 | [Next-Flip/Momentum-Firmware](https://github.com/Next-Flip/Momentum-Firmware) | 8.7k | Momentum CFW (Xtreme successor) |
| 7 | [I-Am-Jakoby/Flipper-Zero-BadUSB](https://github.com/I-Am-Jakoby/Flipper-Zero-BadUSB) | 6.9k | BadUSB payloads |
| 8 | [RogueMaster/flipperzero-firmware-wPlugins](https://github.com/RogueMaster/flipperzero-firmware-wPlugins) | 6.3k | RogueMaster CFW |
| 9 | [BruceDevices/firmware](https://github.com/BruceDevices/firmware) | 5.9k | **Bruce** — ESP32 multitool fw (sibling scene) |
| 10 | [geo-tp/ESP32-Bit-Pirate](https://github.com/geo-tp/ESP32-Bit-Pirate) | 3.9k | Bus-Pirate-style ESP32 tool |
| 11 | [cifertech/ESP32-DIV](https://github.com/cifertech/ESP32-DIV) | 3.2k | All-in-one ESP32 wireless toolkit |
| 12 | [flipperdevices/Flipper-Android-App](https://github.com/flipperdevices/Flipper-Android-App) | 2.2k | Official Android app |
| 13 | [RogueMaster/awesome-flipperzero-withModules](https://github.com/RogueMaster/awesome-flipperzero-withModules) | 2.0k | Module-focused awesome list |
| 14 | [aleff-github/my-flipper-shits](https://github.com/aleff-github/my-flipper-shits) | 1.8k | BadUSB payloads |
| 15 | [I-Am-Jakoby/PowerShell-for-Hackers](https://github.com/I-Am-Jakoby/PowerShell-for-Hackers) | 1.5k | PowerShell payload helpers |
| 16 | [xMasterX/all-the-plugins](https://github.com/xMasterX/all-the-plugins) | 1.5k | Huge plugin pack |
| 17 | [Spooks4576/Ghost_ESP](https://github.com/Spooks4576/Ghost_ESP) | 1.2k | Ghost ESP firmware (ESP32) |
| 18 | [flipperdevices/flipper-application-catalog](https://github.com/flipperdevices/flipper-application-catalog) | 1.1k | The official app catalog source |
| 19 | [flipperdevices/flipperzero-ufbt](https://github.com/flipperdevices/flipperzero-ufbt) | 1.0k | App build tool (ufbt) |
| 20 | [DarkFlippers/flipperzero-subbrute](https://github.com/DarkFlippers/flipperzero-subbrute) | 0.9k | Sub-GHz brute/key tool |

> Note: ~5 of the top 20 are **ESP32 firmwares** (Marauder, Bruce, Bit-Pirate, ESP32-DIV, Ghost ESP), not Flipper apps — see the sibling-scene note below.

## Developers & orgs to follow (navigate by author)
| Handle | Known for |
|---|---|
| **DarkFlippers / @xMasterX** | Unleashed FW + [all-the-plugins](https://github.com/xMasterX/all-the-plugins); Sub-GHz protocol research |
| **Next-Flip** | Momentum FW (Xtreme successor) |
| **RogueMaster** | RogueMaster kitchen-sink FW |
| **flipperdevices** (official) | Firmware, ufbt, app catalog, Android/iOS apps, game engine, VGM |
| **djsime1** | The awesome-flipperzero master list |
| **jamisonderek (CodeAllNight)** | Tutorials + YouTube; Sub-GHz decoders, Wiegand reader, app-dev |
| **jblanked** | [FlipperHTTP](https://github.com/jblanked/FlipperHTTP) + web apps (FlipSocial, FlipTrader, FlipWeather, FlipWifi, FlipMap, Web Crawler) |
| **bettse** | [Seader](https://github.com/bettse/seader) — read HID iCLASS/SE/SEOS, DESFire EV1/2 via an external SAM |
| **noproto** | FlipperMfkey / NFC tooling |
| **luu176** | Metroflip (transit cards) |
| **kbembedded** | [Game Boy Pokémon trading](https://github.com/kbembedded/Flipper-Zero-Game-Boy-Pokemon-Trading) + [flipper-gblink](https://github.com/kbembedded/flipper-gblink) |
| **zacharyweiss** | [magspoof_flipper](https://github.com/zacharyweiss/magspoof_flipper) |
| **eried** | [Mayhem fin](https://github.com/eried/flipperzero-mayhem) + project collection |
| **UberGuidoZ** | The "everything" playground/dumps |
| **EstebanFuentealba** | VGM DIY, Pokémon, apps |
| **justcallmekoko / Spooks4576 / cifertech / BruceDevices** | ESP32 firmwares (Marauder / Ghost ESP / ESP32-DIV / Bruce) |
| **logickworkshop** | [Flipper-IRDB](https://github.com/logickworkshop/Flipper-IRDB) (IR database) |

## Notable repos we hadn't pinned (by niche)
- **Dev SDKs:** [ufbt](https://github.com/flipperdevices/flipperzero-ufbt) (build tool) · **Rust:** [flipperzero-rs/flipperzero-rs](https://github.com/flipperzero-rs/flipperzero-rs), [boozook/flipper0](https://github.com/boozook/flipper0) (FW bindings), [elijah629/flipper-rpc](https://github.com/elijah629/flipper-rpc) (host-side RPC) · [game engine](https://github.com/flipperdevices/flipperzero-game-engine).
- **NFC "read the secure stuff":** **[bettse/Seader](https://github.com/bettse/seader)** (iCLASS SE / SEOS / DESFire via SAM — the legit route to "secure" credentials), [MFKey](https://lab.flipper.net/apps/mfkey) (mfkey32/nested on-device), Metroflip (transit). See [cards/](../cards/cloning-matrix.md).
- **Now-pinned cool ones:** [magspoof_flipper](https://github.com/zacharyweiss/magspoof_flipper), [Pokémon trading](https://github.com/kbembedded/Flipper-Zero-Game-Boy-Pokemon-Trading), [doom-flipper-zero](https://github.com/p4nic4ttack/doom-flipper-zero).
- **BadUSB libs:** [I-Am-Jakoby](https://github.com/I-Am-Jakoby/Flipper-Zero-BadUSB), [aleff-github/my-flipper-shits](https://github.com/aleff-github/my-flipper-shits).
- **Official companions:** [Android app](https://github.com/flipperdevices/Flipper-Android-App), [app catalog](https://github.com/flipperdevices/flipper-application-catalog).

## The "ESP32 sibling scene" (relevant to your Marauder)
Several top repos are **ESP32 firmwares**, not Flipper apps — the adjacent "cheap wireless multitool" world: **Marauder**, **Ghost ESP**, **ESP32-DIV**, **Bruce**, **Bit-Pirate**. They matter to you because your **Marauder backpack is an ESP32** that can be **reflashed** to several of them (Ghost ESP, Bruce, FlipperHTTP) — your board is a gateway to that whole scene, not just Marauder. See [hardware/gpio-addons-current](../hardware/gpio-addons-current.md).

## How to track what's new / trending
- GitHub topics, sorted **Recently updated** or **Most stars**: https://github.com/topics/flipperzero · https://github.com/topics/flipper-zero
- **Watch/star** [awesome-flipperzero](https://github.com/djsime1/awesome-flipperzero) — PRs add new tools constantly.
- Firmware **release feeds** (Unleashed/Momentum/RogueMaster) surface newly-bundled apps.
- [Hackaday's Flipper tag](https://hackaday.com/tag/flipper-zero/) for write-ups.

## Open questions / to research
- Re-snapshot the star leaderboard periodically (counts drift; new entrants appear).
- Try reflashing my Marauder ESP32 to **Bruce** or **Ghost ESP** and compare to Marauder.
- Add `bettse/Seader` to my NFC workflow notes (the way to read iCLASS SE/SEOS).

## Sources
- Leaderboard: https://github.com/topics/flipperzero?o=desc&s=stars
- Verified repos: https://github.com/zacharyweiss/magspoof_flipper · https://github.com/kbembedded/Flipper-Zero-Game-Boy-Pokemon-Trading · https://github.com/cifertech/ESP32-DIV · https://github.com/flipperzero-rs/flipperzero-rs · https://github.com/bettse/seader
