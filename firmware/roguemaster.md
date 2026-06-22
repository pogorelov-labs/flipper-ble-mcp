---
title: RogueMaster Firmware
domain: firmware
type: reference
status: detailed
summary: Kitchen-sink, bleeding-edge custom firmware with the largest bundled app/game set and most crashes.
hardware: []
use_cases: []
related: [firmware/README.md, firmware/unleashed.md, firmware/momentum.md]
tags: [firmware, roguemaster, custom-firmware, plugins, games, animation-packs, instability]
last_verified: 2026-06-19
---

# RogueMaster Firmware

> **TL;DR —** Kitchen-sink, bleeding-edge custom firmware merging Unleashed and ex-Xtreme features plus the largest bundle of community apps, games, and animation packs — the most crash-prone of the four, for experimental use.
> See the [firmware overview & matrix](README.md). Part of the [KB](../README.md).

- **Repo:** https://github.com/RogueMaster/flipperzero-firmware-wPlugins
- **Maintainer:** RogueMaster. Active — **monthly** stable releases; Patreon supporters get more frequent compiled builds.
- **Lineage:** Fork of OFW that **merges Unleashed + (ex-)Xtreme features plus a very large set of community plugins/games** — "a fork of all Flipper Zero community projects."

## What it adds vs Official
- Region-unlock + extended Sub-GHz protocols (inherited from Unleashed).
- The **largest bundled collection**: apps, games, NFC parsers (transit/amusement/payment cards), Sub-GHz decoders, external-hardware helpers (ESP32, NRF24…).
- Multiple themed **animation packs** switchable via CFW Settings.

## Stability (read this)
**Most crash-prone of the four** — "for experimental purposes only."
Practical caveats:
- Flash **stock OFW first**.
- **Delete `/ext/apps`** before updates to avoid app errors.
- Requires up-to-date OFW base and an installed microSD.
- If you need stability/reliability, prefer **Unleashed or Momentum**.

## Install / flash
Flipper Lab (select the RM channel), qFlipper "Install from file" (`.tgz`), or manual
extraction of `.tgz`/`.zip` to the SD `update` folder, run from the Archive app.

## Best for
Tinkerers who want the broadest pile of preloaded apps/games/animations and don't mind
occasional crashes or maintenance chores.

## Open questions / to research
- Whether any RM-exclusive app is compelling enough to justify the instability for my uses.

## Sources
- https://github.com/RogueMaster/flipperzero-firmware-wPlugins · https://awesome-flipper.com/firmware/ · https://hackmag.com/security/flipper-zero-firmwarez
