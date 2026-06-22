---
title: Sub-GHz Device-Specific Repos & .sub Collections
domain: resources
type: resource-list
status: detailed
summary: Device-specific Sub-GHz repos and .sub collections (TouchTunes, gates, Tesla, sensors)
hardware: []
use_cases: []
related: [capabilities/sub-ghz.md, theory/rolling-codes.md, resources/best-github-repos.md, resources/notable-apps-and-data.md, legal-and-safety.md]
tags: [sub-ghz, sub-files, brute-force, tesla, gates, tpms, fixed-code]
last_verified: 2026-06-19
---

# Sub-GHz Device-Specific Repos & .sub Collections

> **TL;DR —** The device-targeted Sub-GHz companion — repos shipping `.sub` files or generators tuned to one brand/model (TouchTunes, restaurant pagers, gates/barriers, the Tesla charge-port, TPMS/POCSAG decoders) plus the big mega-DBs. Authorized use only; most are fixed-code and modern vehicles/gates are rolling-code and won't replay.
> See [sub-ghz capability](../capabilities/sub-ghz.md) · [rolling codes](../theory/rolling-codes.md) · [best repos](./best-github-repos.md) · [notable apps & data](./notable-apps-and-data.md). Part of the [KB](../README.md).

This is the *device-targeted* companion to [best-github-repos.md](./best-github-repos.md): repos that ship `.sub` files (or generators) tuned to **one brand/model** — a specific jukebox, pager, gate vendor, car, sensor — rather than general firmware or app packs. "Device-specific" matters because a `.sub` is frequency + preset + protocol + payload baked together; a CAME 12-bit file is useless against a NICE remote, a 433.92 capture won't fire a 315-MHz receiver, and a fixed-code dump is only a working clone if the *target* is fixed-code.

**Authorized use only.** Everything here transmits on regulated ISM/SRD bands and is for hardware **you own or are explicitly authorized to test**. Two hard limits to internalize before downloading anything below: (1) **most are fixed-code** — they replay because the device has *no* rolling security, which is exactly why firing them at someone else's receiver can be unauthorized access; (2) **modern vehicles/gates are rolling-code** (KeeLoq/Security+/RTS/FAAC SLH) — a captured/library `.sub` **will not work by design** ([rolling-codes.md](../theory/rolling-codes.md)). Region also matters: stock OFW enforces a TX allow-list; CFW unlocks the hardware range but the legal duty stays on you ([legal-and-safety.md](../legal-and-safety.md)). Sort every repo below by "recently updated" before relying on it — `.sub` format and decoder rosters drift across firmware.

> **Flags:** *active* = recent commits; *(verify)* = recency/exact contents unconfirmed, re-check; *(archived)* = read-only. ★ counts are approximate snapshots.

## Jukebox / vending / restaurant pagers
Mostly **fixed-code** consumer gear — the classic "it just replays" category, and the most ethically loaded (these target commercial equipment in venues you don't own).

| Repo | URL | What it is | Code type |
|---|---|---|---|
| **jimilinuxguy/flipperzero-touchtunes** | https://github.com/jimilinuxguy/flipperzero-touchtunes | TouchTunes bar/restaurant jukebox remote `.sub` set, split by admin PIN folder (most venues leave the default `000`); credits notpike's YardStick/Portapack work | Fixed (OOK) |
| **xb8/t119bruteforcer** | https://github.com/xb8/t119bruteforcer | Retekess **T119** restaurant coaster-pager brute-forcer — single `.sub` (use `t119bruteforcerupdated.sub`) that walks the pager call space; ~470★ | Fixed, sweep |
| *(pagers in)* **tobiabocchi/flipperzero-bruteforce** | https://github.com/tobiabocchi/flipperzero-bruteforce | also generates "Spacca"/restaurant-pager sweeps alongside gate protocols (see below) | Fixed, sweep |

> No standalone "Bevview" vending repo confirmed — those `.sub` files live inside the big DB collections below `(verify)`. Vending/jukebox triggers are fixed-code; treat venue hardware as off-limits unless you operate it.

## Brute-force generators (fixed-code OOK)
These don't ship per-device captures — they **synthesize** the entire small code space of a fixed protocol as `.sub` playlists (often a **de Bruijn** sequence so adjacent codes overlap and the sweep is ~N× shorter). Only meaningful against tiny fixed spaces you own; **useless on rolling codes**. Mechanics: [sub-ghz.md → Brute-force reality](../capabilities/sub-ghz.md).

| Repo | URL | Covers | Notes |
|---|---|---|---|
| **tobiabocchi/flipperzero-bruteforce** | https://github.com/tobiabocchi/flipperzero-bruteforce | **CAME** 12-bit (433.92/868.35), **CAME-fast**, **NICE** 12-bit, **Chamberlain** 9-bit (300/315), **Linear** 10-bit (300/310), **PT-2240** 24-bit, **Ansonic**, **Holtek** 12-bit; Python script takes custom protocols | active, ~2.5k★. Pre-built folders per split-factor (1/2/4/8/16/32) + a deBruijn file for binary-search-style narrowing |
| **xb8/t119bruteforcer** | https://github.com/xb8/t119bruteforcer | Retekess T119 pager (above) | A worked single-device example of the same idea |

> The CAME/NICE/Princeton/Holtek 12-bit families are the canonical "brute-forceable" set (hundreds–few-thousand codes). Anything calling itself rolling (KeeLoq, FloR-S 52-bit, Security+) is **not** in scope here regardless of what a generator's issue tracker requests.

## Vehicles
Read this section as mostly a **negative result**. Modern car remotes/fobs and PKE are rolling-code or challenge-response → **library `.sub` files do not work** ([rolling-codes.md](../theory/rolling-codes.md)). The one durable exception is the **Tesla charge-port door**, which historically responds to a simple unauthenticated 315/433 OOK burst (no pairing) — hence its own mini-ecosystem. Use only on your own car; spamming charge ports in a lot is a nuisance, not a hack.

| Repo | URL | What it is | Code type |
|---|---|---|---|
| **MuddledBox/FlipperZeroSub-GHz** | https://github.com/MuddledBox/FlipperZeroSub-GHz | Curated `.sub` set incl. `Vehicles/Tesla/` charge-door files (AM270 + AM650 variants); ~1.4k★, "unlocked firmware required" | Fixed/unauth |
| **Robbbbbbbbb/tesla-chargeport** | https://github.com/Robbbbbbbbb/tesla-chargeport | Tesla charge-port captures for **Flipper + HackRF/Portapack**, aggregated from other repos (Flipper files trace to UberGuidoZ) | Fixed/unauth |
| *(Tesla folder in)* **UberGuidoZ/Flipper** | https://github.com/UberGuidoZ/Flipper/tree/main/Sub-GHz/Vehicles/Tesla | The de-facto origin of the "Better Tesla Charge Port Opener" `.sub`; the playground most others copy from | Fixed/unauth |

> Beyond Tesla charge doors, treat car Sub-GHz as decode-only telemetry (TPMS, below) — not access. "Why my captured fob doesn't work" is the whole point of [rolling-codes.md](../theory/rolling-codes.md).

## Gates / garages / barriers, doorbells, RF sockets, wristbands
Brand-specific **fixed-code** captures and "universal RF remote" sets. These work where the *deployed* hardware is genuinely fixed-code (older/cheap installs); the same brand may also ship rolling-code lines that won't replay.

| Repo | URL | What it is | Notes |
|---|---|---|---|
| **MuddledBox/FlipperZeroSub-GHz** | https://github.com/MuddledBox/FlipperZeroSub-GHz | General device set (gates, barriers, misc remotes) beyond the Tesla folder | active-ish, ~1.4k★ |
| **MakeTotalSense/Flipper-Concert-bracelets** | https://github.com/MakeTotalSense/Flipper-Concert-bracelets | 433.92 MHz frames to trigger LED concert wristbands (off/blink/colour/rainbow); author asks you not to disrupt real shows | Fixed (OOK) |
| **niltefa/Flipper-CrowdLED-Wristbands** | https://github.com/niltefa/Flipper-CrowdLED-Wristbands | `.sub` files for **CrowdLED** bracelets — set colour, gradient, multicolour | Fixed (OOK) `(verify)` |
| **jimilinuxguy/flipperzero-universal-rf-remote** | https://github.com/jimilinuxguy/flipperzero-universal-rf-remote | "Universal RF remote" app + RAW captures; **RAW-only** (so KeeLoq/Came won't work) | **(archived 2022)** — author points to the ESurge fork; listed for the captures, not the app |

> For owned gates/doorbells/RF sockets, your own **Read → save** capture is almost always better than a library file — a generic `.sub` only matches if the brand/encoding/dip-switches line up exactly. RF mains sockets (Etekcity/NEXA/Intertechno-style) are Princeton/Holtek OOK and are also covered by the brute-force generators above.

## Sensors — weather / TPMS / POCSAG (receive-only decoders)
These are **listen-and-display apps**, not `.sub` replay, and not access control. Useful for diagnosing **your own** sensors. (Listening to pager traffic may be legally restricted regardless of feasibility — [legal-and-safety.md](../legal-and-safety.md).)

| Repo | URL | What it decodes | Notes |
|---|---|---|---|
| **antirez/protoview** | https://github.com/antirez/protoview | Signal explorer + decoders: TPMS (Schrader, Toyota, Renault, Citroën, Ford), plus generic OOK visualization | active; great for "what is this signal?" RX work |
| **wosk/flipperzero-tpms** | https://github.com/wosk/flipperzero-tpms | TPMS read (Schrader GG4; more in progress) + 125 kHz relearn trigger | RX-only; last release v0.2 Apr 2024 `(verify)` |
| **xMasterX/flipper-pager** | https://github.com/xMasterX/flipper-pager | **POCSAG** 512/1200/2400 pager receiver (defaults to DAPNET 439.9875 MHz; custom freqs via SD config) | RX-only; maintained (rel. late 2023) `(verify)` |

> Weather-station and many TPMS protocols also ship as built-in/CFW Sub-GHz decoders — check the firmware's own sensor list before adding an app. POCSAG usually needs a Custom 2-FSK preset + correct data rate ([sub-ghz.md → presets](../capabilities/sub-ghz.md)).

## Big `.sub` mega-collections (everything, by device folder)
Bulk archives that fold many of the above into one tree. Convenient, but **unvetted and uneven** — files vary in quality, legality by region, and fixed-vs-rolling viability (a folder existing ≠ a working clone). Cross-ref [notable-apps-and-data.md](./notable-apps-and-data.md).

| Repo | URL | Size / scope | Notes |
|---|---|---|---|
| **Zero-Sploit/FlipperZero-Subghz-DB** | https://github.com/Zero-Sploit/FlipperZero-Subghz-DB | ~**13,717** `.sub` in ~721 folders, aggregated from public sources | The big one; "education/research only." Contains everything from TPMS relearn tools to novelty device folders |
| **magikh0e/FlipperZero_Stuff** | https://github.com/magikh0e/FlipperZero_Stuff | Mixed IR + Sub-GHz + remotes + links | Smaller personal grab-bag `(verify)` |
| **UberGuidoZ/Flipper** | https://github.com/UberGuidoZ/Flipper | The canonical "everything" playground; `Sub-GHz/` has Vehicles/TouchTunes/etc. | active; the upstream most device files originate from (also in [best-github-repos.md](./best-github-repos.md)) |

> Prefer the focused per-device repos above when you know the target; reach for these mega-DBs only to *discover* whether a device has ever been captured. Always confirm the file's frequency/preset/protocol against your actual hardware before TX.

## Open questions / to research
- Re-confirm last-commit dates on the *(verify)* repos (TPMS apps, CrowdLED, magikh0e) and whether `.sub` format still loads on current OFW/Unleashed/Momentum.
- Whether the Tesla charge-port burst still works on **2024+ vehicles** or has been firmware-hardened (anecdotal reports differ) `(verify)`.
- A confirmed standalone "Bevview"/vending repo vs. those files only existing inside the mega-DBs.
- Which brute-force protocol spaces are small enough to be practical vs. pointless (codes/sec at typical TE) — extend the table in [sub-ghz.md](../capabilities/sub-ghz.md).
- Best Custom-preset register dumps bundled with the POCSAG/TPMS apps for odd data rates.
- A vetted, region-legal **subset** of the 13.7k DB for safe lab testing (the "sample-dump archive" open question in [best-github-repos.md](./best-github-repos.md)).

## Sources
- https://github.com/jimilinuxguy/flipperzero-touchtunes
- https://github.com/xb8/t119bruteforcer
- https://github.com/tobiabocchi/flipperzero-bruteforce
- https://github.com/MuddledBox/FlipperZeroSub-GHz
- https://github.com/Robbbbbbbbb/tesla-chargeport
- https://github.com/UberGuidoZ/Flipper/tree/main/Sub-GHz/Vehicles/Tesla
- https://github.com/MakeTotalSense/Flipper-Concert-bracelets
- https://github.com/niltefa/Flipper-CrowdLED-Wristbands
- https://github.com/jimilinuxguy/flipperzero-universal-rf-remote
- https://github.com/antirez/protoview
- https://github.com/wosk/flipperzero-tpms
- https://github.com/xMasterX/flipper-pager
- https://github.com/Zero-Sploit/FlipperZero-Subghz-DB
- https://github.com/magikh0e/FlipperZero_Stuff
- https://docs.flipper.net/zero/sub-ghz/supported-vendors
