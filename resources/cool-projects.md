---
title: Cool Flipper Projects (the fun / novel side)
domain: resources
type: resource-list
status: detailed
summary: Fun/novel projects — FlipperHTTP web apps, games, VGM DOOM, MagSpoof, Home Assistant
hardware: []
use_cases: []
related: [resources/best-github-repos.md, resources/github-landscape.md, resources/notable-apps-and-data.md, hardware/gpio-addons-current.md]
tags: [projects, games, flipperhttp, vgm, doom, magspoof, home-assistant]
last_verified: 2026-06-19
---

# Cool Flipper Projects (the fun / novel side)

> **TL;DR —** The "oh, that's cool" list of notable, creative, impressive Flipper GitHub projects — FlipperHTTP web-connected apps, games and the game engine, VGM DOOM, MagSpoof and other clever hacks, and Home Assistant integration. The fun companion to best-github-repos.md.
> The fun companion to [best-github-repos.md](best-github-repos.md) (which is the utilitarian "best by category"). Part of the [KB](../README.md).

Where [best-github-repos](best-github-repos.md) is the toolbox, this is the *"oh, that's cool"* list — games,
web-connected apps, clever hacks, and VGM projects. The scene moves fast; **verify stars/activity** before
relying, and flagged `(verify)` items are real but I haven't pinned the exact repo URL.

## 🌐 Web-connected Flipper — the novel frontier (FlipperHTTP)
- **jblanked/FlipperHTTP** — https://github.com/jblanked/FlipperHTTP — a library that turns an **ESP32**
  (the Wi-Fi DevBoard, a BW16, or **your Marauder board reflashed**) into the Flipper's **internet bridge**.
  It unlocks a whole genre of *online* apps on a device with no native Wi-Fi:
  - **FlipSocial** — a social network *on your Flipper*.
  - **FlipTelegram** — a Telegram client.
  - **Free Roam** — an open-world **3D multiplayer** game.
  - **FlipMap** — find other Flipper users on a map.
  - (+ weather, web crawler, etc. — see the repo for the current roster) `(verify roster)`
  - Catch: needs **FlipperHTTP firmware** on an ESP32 → you'd reflash your Marauder board (or use a 2nd ESP32).

## 🎮 Games & the Game Engine
- **flipperdevices/flipperzero-game-engine** — https://github.com/flipperdevices/flipperzero-game-engine (+ [example](https://github.com/flipperdevices/flipperzero-game-engine-example)) — the official engine many games build on.
- **p4nic4ttack/doom-flipper-zero** — https://github.com/p4nic4ttack/doom-flipper-zero — a DOOM-style raycaster on the 128×64 screen.
- **doofy-dev/flipper_games** — https://github.com/doofy-dev/flipper_games — a games collection.
- Official/built-in: **T-Rex, 2048, Sokoban, Ultimate Tic-Tac-Toe, Flight Assault**, and **rock-paper-scissors multiplayer over Sub-GHz** (two Flippers play over the radio — genuinely clever).
- Toys: a **DVD-logo screensaver**, a **BPM tapper**, a **metronome**.

## 📺 Video Game Module (RP2040) — needs the VGM
- **kilograham/rp2040-doom** — https://github.com/kilograham/rp2040-doom — full DOOM on the RP2040; the basis for **DOOM on a real screen** via the VGM's DVI-D output.
- **EstebanFuentealba/Flipper-Zero-Video-Game-Module-DIY** — https://github.com/EstebanFuentealba/Flipper-Zero-Video-Game-Module-DIY — build your own VGM.
- The VGM = **DVI-D 640×480 out + 6-axis motion** → motion-controlled games on an external display ([hardware/gpio-addons-current](../hardware/gpio-addons-current.md)). *(You don't have the VGM.)*

## 🪄 Clever / novel hacks
- **[zacharyweiss/magspoof_flipper](https://github.com/zacharyweiss/magspoof_flipper)** — a port of Samy Kamkar's MagSpoof: a coil on the GPIO **emulates magstripe swipes** wirelessly. Iconic hack.
- **[kbembedded/Flipper-Zero-Game-Boy-Pokemon-Trading](https://github.com/kbembedded/Flipper-Zero-Game-Boy-Pokemon-Trading)** — emulate the **Game Boy link cable** to trade/edit/receive Pokémon (Gen I & II); built on [flipper-gblink](https://github.com/kbembedded/flipper-gblink).
- **ESP32-CAM viewer** — show an ESP32 camera feed on the Flipper screen (also on the Mayhem fin).
- **Metroflip** — parse transit cards · **Seader** — read iCLASS **SE** via an external SAM. ([cards/](../cards/cloning-matrix.md))
- **Sub-GHz spectrum analyzer** app — turn the CC1101 into a basic spectrum view.
- **[cifertech/ESP32-DIV](https://github.com/cifertech/ESP32-DIV)** — a popular all-in-one ESP32 wireless toolkit (~3.2k★; Wi-Fi/BLE/Sub-GHz/IR/RFID/GPS) from the sibling scene.

## 🏠 Integrations
- **ClusterM/flipper_rc** — https://github.com/ClusterM/flipper_rc — **Home Assistant** integration: use the Flipper as a universal **IR / Sub-GHz remote emulator** in HA (your Flipper becomes the smart-home RF/IR bridge).

## 🧰 Big collections / playgrounds
- **djsime1/awesome-flipperzero** — https://github.com/djsime1/awesome-flipperzero — the master list.
- **FroggMaster/FlipperZero** — https://github.com/FroggMaster/FlipperZero — scripts/apps/etc.
- **123fzero/flipper-zero-awesome** — https://github.com/123fzero/flipper-zero-awesome — app catalog.
- **UberGuidoZ/Flipper** — https://github.com/UberGuidoZ/Flipper — the "everything" playground.

## What MY rig can run
- **Bare Flipper:** all the games + DVD screensaver + music toys, MagSpoof (with a DIY coil), Sub-GHz spectrum analyzer, Metroflip/PicoPass, and the Home Assistant integration (Flipper = the remote).
- **With my ESP32 Marauder board (reflashed to FlipperHTTP):** the **web-connected apps** — FlipSocial, FlipTelegram, Free Roam, FlipMap. (Reflashing replaces Marauder; ESP32-DIV is likewise a reflash.)
- **Needs hardware I don't have:** VGM games on a big screen (the Video Game Module).

## How to find more (the scene moves fast)
- GitHub topics, sorted recently-updated / by stars: https://github.com/topics/flipperzero · https://github.com/topics/flipper-zero
- Hackaday's Flipper tag: https://hackaday.com/tag/flipper-zero/
- The Flipper Lab app catalog + the awesome lists above.

## Open questions / to research
- Repo URLs for MagSpoof / Pokémon / ESP32-DIV now pinned (see also [github-landscape](github-landscape.md)).
- Try a FlipperHTTP app on my Marauder ESP32 (reflash + back) and note the experience.
- Shortlist 3 games worth keeping installed; check current FlipperHTTP app roster.

## Sources
- FlipperHTTP: https://github.com/jblanked/FlipperHTTP · game engine: https://github.com/flipperdevices/flipperzero-game-engine
- DOOM: https://github.com/p4nic4ttack/doom-flipper-zero · rp2040-doom: https://github.com/kilograham/rp2040-doom
- Home Assistant: https://github.com/ClusterM/flipper_rc · VGM DIY: https://github.com/EstebanFuentealba/Flipper-Zero-Video-Game-Module-DIY
- Discovery: https://github.com/topics/flipperzero · https://hackaday.com/tag/flipper-zero/
