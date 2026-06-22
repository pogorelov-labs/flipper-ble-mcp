---
title: Notable Apps, Data & PC Tooling (the deeper cut)
domain: resources
type: resource-list
status: detailed
summary: Deeper cut — pyFlipper scripting, sensor/utility apps, data/dumps, asset packs, 3D
hardware: []
use_cases: []
related: [resources/best-github-repos.md, resources/cool-projects.md, resources/github-landscape.md, topics/tinkering.md]
tags: [pc-tooling, pyflipper, sensors, dumps, asset-packs, 3d-printing, scripting]
last_verified: 2026-06-19
---

# Notable Apps, Data & PC Tooling (the deeper cut)

> **TL;DR —** The deeper-cut niches the other repo lists skip — PC/host scripting (pyFlipper, protobuf RPC), utility/sensor apps, data/dumps to load on the SD, asset packs to reskin the dolphin, and 3D prints. Companion to the category/fun/leaderboard lists.
> Companion to [best-github-repos](best-github-repos.md) · [cool-projects](cool-projects.md) · [github-landscape](github-landscape.md). Part of the [KB](../README.md).

The category/leaderboard/fun lists miss five practical niches. Here they are. `(verify)` = real but exact repo not pinned — find it via the [catalog](https://lab.flipper.net/apps) or [awesome list](https://github.com/djsime1/awesome-flipperzero).

## 1. PC / host tooling — script the Flipper from a computer
The Flipper exposes a **serial CLI + protobuf RPC** over USB — so you can automate it from a PC.
- **[wh00hw/pyFlipper](https://github.com/wh00hw/pyFlipper)** — Python CLI wrapper (serial / TCP / websocket): power, file ops, app launch, GPIO, Sub-GHz, etc. Best for scripting.
- **[flipperdevices/flipperzero_protobuf_py](https://github.com/flipperdevices/flipperzero_protobuf_py)** — official Python **protobuf** bindings + `flipperCmd` (file transfer + remote command).
- **[AndreMiras/flipper-fs.py](https://github.com/AndreMiras/flipper-fs.py)** — **FlipperFS**: clean filesystem access over serial (read/write/list/mkdir/copy).
- **[lomalkin/flipperzero-cli-tools](https://github.com/lomalkin/flipperzero-cli-tools)** — handy `clipper.py` CLI helpers.
- **[elijah629/flipper-rpc](https://github.com/elijah629/flipper-rpc)** — the same idea in **Rust**.
- *Use:* batch-load dumps, scripted backups, CI for your own apps, remote control. Pairs with [tinkering](../topics/tinkering.md).

## 2. Utility & sensor apps
- **[quen0n/unitemp-flipperzero](https://github.com/quen0n/unitemp-flipperzero)** — **Unitemp**: read DHT11/22, DS18B20, BMP280, HTU21x temp/humidity/pressure sensors over GPIO. The go-to for the [GPIO sensor use-case](../topics/tinkering.md) (UC-45).
- **Sub-GHz Spectrum Analyzer** — turns the CC1101 into a basic spectrum view `(verify repo; in catalog)`.
- **UPC-A Barcode Generator**, **Multi Converter** (unit/base conversions), **WAV Player** (+ sample/convert tools) — small but genuinely useful `(verify repos; in catalog)`.
- **GPS / wardriver** — [Sil333033/flipperzero-wardriver](https://github.com/Sil333033/flipperzero-wardriver) (+ the `[NMEA] GPS` app).
- *(2FA Authenticator, PicoPass, Seader, Metroflip already covered in [tinkering](../topics/tinkering.md) / [cards](../cards/README.md).)*

## 3. Data & dumps (load onto the SD)
- **[Zero-Sploit/FlipperZero-Subghz-DB](https://github.com/Zero-Sploit/FlipperZero-Subghz-DB)** — a massive **~13,700 `.sub` file** Sub-GHz archive.
- **[logickworkshop/Flipper-IRDB](https://github.com/logickworkshop/Flipper-IRDB)** — the big IR remote database.
- **[Gioman101/FlipperAmiibo](https://github.com/Gioman101/FlipperAmiibo)** — amiibo in Flipper format · **[nortakales/flipper-zero-tonies](https://github.com/nortakales/flipper-zero-tonies)** — Toniebox figures.
- **ClassicConverter / ClassicConverterWeb** — convert MIFARE Classic `.bin` ⇄ Flipper `.nfc` (handy with Proxmark dumps) `(verify owner)`. See [cards/cloning-matrix](../cards/cloning-matrix.md).
- **[J9ck/FlipperZeroCollection](https://github.com/J9ck/FlipperZeroCollection)** — "everything I'd want if I lost my SD" personal kit.
- **[UberGuidoZ/Flipper](https://github.com/UberGuidoZ/Flipper)** — the giant dumps/reference playground. (Awesome list has a dedicated "Databases & Dumps" section.)
- ⚠️ Big `.sub` libraries are **dual-use**: TX legality + authorized-targets rules still apply ([legal-and-safety](../legal-and-safety.md)).

## 4. Asset packs & animations (reskin the dolphin)
- **[ablaran/Graphics4FZ](https://github.com/ablaran/Graphics4FZ)** — animations/icons/asset packs, Momentum-optimized.
- **[Kuronons/FZ_graphics](https://github.com/Kuronons/FZ_graphics)** — themed anims (G-Shock, Dexter's Lab, GTA, Android…).
- **[Cian28-C28/Flipper-Asset-Packs](https://github.com/Cian28-C28/Flipper-Asset-Packs)** — lots of animation packs (request-driven).
- **[mnenkov/flipper-zero-animations](https://github.com/mnenkov/flipper-zero-animations)** — animations + tools (Hacking Cat, Beluga).
- **[cyberartemio/flipper-pirates-asset-pack](https://github.com/cyberartemio/flipper-pirates-asset-pack)** — themed pack.
- **Builders:** **[hooker01/Flipper-Zero-Asset-Pack-Generator](https://github.com/hooker01/Flipper-Zero-Asset-Pack-Generator)** (GIF → pack, GUI) and **[Ooggle/FlipperAnimationManager](https://github.com/Ooggle/FlipperAnimationManager)** (in [tools-and-software](tools-and-software.md)). Install paths: [topics/tinkering §4](../topics/tinkering.md).

## 5. 3D prints & hardware design
- **[lomalkin/flipperzero-protoboards-kicad](https://github.com/lomalkin/flipperzero-protoboards-kicad)** — KiCad protoboard designs.
- **[s0ko1ex/FlipperZero-Hardware](https://github.com/s0ko1ex/FlipperZero-Hardware)** — 3D-printable cases.
- **Printables / Thingiverse** — cases, antenna mounts, backpack shells (e.g., the "Ultimate Flipper Case"). The RogueMaster module list also bundles case models.
- More hardware context: [hardware/gpio-addons-current](../hardware/gpio-addons-current.md) · [gpio-addons-potential](../hardware/gpio-addons-potential.md).

## Open questions / to research
- Pin exact repos for Spectrum Analyzer, Barcode, Multi Converter, ClassicConverter (catalog/awesome).
- Try **pyFlipper** for a scripted full-SD backup (pairs with the migration checklist).
- Install **Unitemp** + a BME280 as the first GPIO sensor project ([tinkering](../topics/tinkering.md)).

## Sources
- PC tooling: https://github.com/wh00hw/pyFlipper · https://github.com/flipperdevices/flipperzero_protobuf_py · https://github.com/AndreMiras/flipper-fs.py
- Apps/data: https://github.com/quen0n/unitemp-flipperzero · https://github.com/Zero-Sploit/FlipperZero-Subghz-DB · https://github.com/J9ck/FlipperZeroCollection
- Asset packs: https://github.com/ablaran/Graphics4FZ · https://github.com/Kuronons/FZ_graphics · https://github.com/hooker01/Flipper-Zero-Asset-Pack-Generator
- Index of dumps: https://github.com/djsime1/awesome-flipperzero (Databases & Dumps section)
