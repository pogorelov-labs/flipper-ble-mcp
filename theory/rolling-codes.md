---
title: Rolling-Code Security — Theory Note
domain: theory
type: theory
status: detailed
summary: KeeLoq internals, RollJam/RollBack, cryptanalysis, and defenses
hardware: []
use_cases: []
related: [capabilities/sub-ghz.md, theory/relay-attacks.md, 01-architecture.md, legal-and-safety.md]
tags: [rolling-code, keeloq, rolljam, rollback, cryptanalysis, sub-ghz, replay]
last_verified: 2026-06-19
---

# Rolling-Code Security — Theory Note

> **TL;DR —** How rolling (hopping) codes work, why they resist Flipper replay, and the real attack classes against them — KeeLoq internals, RollJam/RollBack, side-channel key recovery, and defender mitigations.
> Practical radio side: [capabilities/sub-ghz.md](../capabilities/sub-ghz.md). Architecture: [01-architecture.md](../01-architecture.md). Legality: [legal-and-safety.md](../legal-and-safety.md). Part of the [KB](../README.md).

Educational / defensive framing. The point of this note is to explain **why a modern gate or car resists a Flipper replay**, what would actually break it (mostly research-grade attacks, often illegal), and how a defender reasons about it. Mechanics are at a conceptual level — not a build guide.

## Fixed vs rolling — the core idea
- **Fixed code:** the transmitter sends the **same codeword every press**; the receiver accepts any match. → **Capture + replay works**, and small code spaces (8–12-bit dip switches) are brute-forceable. Common in cheap/old gates, doorbells, RF sockets, and most sensors. On a Flipper these are the **"unlocked"** vendors that Read can save and emulate ([sub-ghz.md](../capabilities/sub-ghz.md)).
- **Rolling (hopping) code:** each press sends a **different, non-repeating codeword** derived from a **secret key + an incrementing counter**, so a captured code is immediately "used up." Designed specifically to defeat replay. On a Flipper these are the **"locked"** vendors: decode-only, Save/Emulate disabled.

## KeeLoq internals (the canonical example)
KeeLoq is the most widespread code-hopping scheme (Microchip; used by countless garage/gate/car systems). It's a **block cipher**: 32-bit block, 64-bit key, built from an **NLFSR** with a nonlinear 5-input feedback function, iterated **528 rounds** ([Bogdanov 2007](https://eprint.iacr.org/2007/055.pdf)).

A transmitted KeeLoq packet has two parts:

| Part | Width | Contents | Role |
|---|---|---|---|
| **Fixed portion** | ~34 bits | **28-bit device serial** + button/status bits | Identifies the remote; tells receiver *whose* counter to check |
| **Hopping portion** | **32 bits** | KeeLoq-**encrypted** block of {counter + button + discrimination bits} | The "rolling" value; different every press |

The lifecycle:
1. **Provisioning.** The manufacturer holds a **64-bit manufacturer key**. Each remote's **device key** is *derived* from its 28-bit serial under that manufacturer key (common schemes: XOR/concatenate the serial into two halves and decrypt, or a "secure learning" **seed** exchanged once at pairing). The receiver, knowing the manufacturer key (or the seed), can recompute the same device key.
2. **Each press.** Remote increments its **sync counter**, encrypts {counter, button, disc} with its device key → the 32-bit hopping code, and sends `serial || button || hopping`.
3. **Receive.** Receiver looks up the serial, recomputes the device key, **decrypts** the hopping code, recovers the counter, and accepts only if the counter is **ahead** of the last accepted value.

### Receiver windows (why replay and desync behave as they do)
- **Forward / "open" window** (typ. ~16 counts ahead): counter values just beyond the last seen are accepted immediately. Absorbs presses made out of range.
- **Resync / "double-operation" window** (a much larger span, e.g. up to ~32k): if the counter is far ahead — but you provide **two consecutive valid presses** — the receiver resynchronizes. This is what saves a remote that fell far behind.
- **Below the last counter → rejected.** This is exactly why a replayed capture fails: the real remote has since advanced the counter, so the stale packet's counter is now "behind."

> Because the **whole 32-bit hopping field is encrypted under a key the Flipper doesn't have**, a stock Flipper cannot compute the *next* valid code — even though it can perfectly decode and display the *structure*.

## Other schemes (comparative)
All share the **counter + secret** principle; they differ in cipher, encoding, and key management.

| Scheme | Crypto / encoding | Notes |
|---|---|---|
| **KeeLoq** | 64-bit NLFSR block cipher, 32-bit hop | Industry baseline; many vendors (DoorHan, AN-Motors, Nice Flor-S, FAAC, etc.) ride on it |
| **FAAC SLH / Genius SLH** | KeeLoq-based, **"Self-Learning Hopping"** | Device key derived from a **random seed** exchanged **once at pairing**; ~32-press out-of-range window, then double-press resync within 5 s ([FAAC/PandwaRF](https://pandwarf.com/news/kaiju-support-for-faac-genius-slh-protocol-master-slave-remotes-gate-openers/)) |
| **BFT Mitto** | KeeLoq-family rolling | Common EU gate remote; rolling counter + secret |
| **Nice FloR-S / Smilo** | KeeLoq-based, 52-bit class | Rolling variants of Nice's FLO family (FLO itself is fixed-code) |
| **Somfy RTS** | **AES** used to encrypt a rolling **counter**, XORed into the frame | 80-bit-ish frame with a rolling code field + checksum; blinds/awnings/shutters. (Somfy io-homecontrol is a separate, stronger 2-way AES stack) |
| **Chamberlain/LiftMaster Security+ 1.0** | rolling code, **trinary** symbols (0/1/2); counter **+3** per press | Older but still common; not AES |
| **Chamberlain Security+ 2.0** | **AES-128**-based, rolling, ~bidirectional handshake | Released ~2011, **incompatible** with 1.0; one code from ~10^11 space per press ([Chamberlain](https://www.chamberlaindiy.com.au/news/behind-the-tech-how-security-2-0-keeps-your-garage-safe-and-secure/)) |

Reverse-engineered references exist for several (e.g. argilo's [secplus](https://github.com/argilo/secplus) for Security+, [PushStack](https://pushstack.wordpress.com/somfy-rts-protocol/) for Somfy RTS) — useful for understanding, but possessing a spec ≠ possessing a device's secret/counter.

## Attack classes — conceptual + defensive
| Attack | Idea (conceptual) | Works against | Mitigation |
|---|---|---|---|
| **Capture-and-replay** | Record one transmission, send it back later | **Fixed-code only** | Use rolling codes |
| **Brute-force** | Walk a small code space (de Bruijn sweep) | Small **fixed-code** spaces | Larger keyspace; rolling codes; rate-limit/lockout |
| **RollJam / capture-replay-with-jamming** | See below | Naive rolling codes w/o expiry | Time-expiry, challenge-response, AES, jam detection |
| **RollBack (2022)** | Replay a *captured sequence* of consecutive codes to roll the counter back into an accepted state — **time-agnostic** | Some automotive RKE | Counters that never rewind; session/time binding ([RollBack](https://dl.acm.org/doi/full/10.1145/3627827)) |
| **Cryptanalysis / key recovery** | Recover device or **manufacturer** key, then *predict* codes | KeeLoq (research) | Per-device keys, side-channel-hardened tokens, AES |
| **Counter desync (DoS)** | Spam presses out of range to push the counter past the window | Rolling codes (annoyance) | Wide resync window + double-press resync; this is **not** entry |

### RollJam (Samy Kamkar, DEF CON 2015)
A landmark demonstration that **naive rolling codes are defeatable without breaking crypto** ([rtl-sdr writeup](https://www.rtl-sdr.com/replicating-a-rolljam-wireless-vehicle-entry-attack-with-a-yardstick-one-and-rtl-sdr/)). The trick converts a safety feature (out-of-range presses still being valid later) into the exploit:
1. **Jam** the receiver's band while **capturing** the victim's first press — the receiver never hears it, so that code stays **unused**.
2. The owner presses again (it "didn't work"); the attacker **captures the second** and simultaneously **replays the first**, which opens the gate/car — looking normal to the owner.
3. The attacker is left holding the **still-unused second code** to replay at will.

Why a **stock Flipper can't do this:** it requires **simultaneous jam + capture on adjacent channels** (effectively two radios) and tight timing — the Flipper has one CC1101 and no jam-while-receive mode; jamming is also illegal in most jurisdictions. **Mitigations:** code **time-expiry** (a captured code dies after seconds), **challenge-response / bidirectional** handshakes (Security+ 2.0, io-homecontrol, modern RKE), **AES** instead of bespoke ciphers, and **jam/interference detection** at the receiver. RollBack (2022) is a related, time-agnostic variant against systems where the counter can be rolled back via a replayed sequence.

### KeeLoq cryptanalysis / manufacturer-key recovery (conceptual)
Two research threads matter:
- **Cipher-level cryptanalysis** (Bogdanov 2007; slide/guess-and-determine attacks) recovered a device key in ~2^52 work — academically significant, not a field tool ([Bogdanov 2007](https://eprint.iacr.org/2007/055.pdf)).
- **Side-channel "complete break"** (Eisenbarth, Kasper, Paar et al., CRYPTO 2008): **power analysis** of a real KeeLoq receiver recovers the **manufacturer key**. Because that key is **shared across an entire product series**, recovering it once lets an attacker compute the device key for *any* remote of that line from **one or two intercepted messages**, then clone or predict future codes ([CRYPTO 2008](https://informatik.rub.de/wp-content/uploads/2022/01/crypto2008_keeloq.pdf)).

The defensive lesson is about **key management**, not just the cipher: a manufacturer key that is **identical across a series** is a single point of catastrophic failure. Schemes that derive **per-device keys from a random seed** (FAAC/Genius SLH) or move to **AES with proper key separation** raise the bar. None of this is a one-click Flipper feature; a stock Flipper has **no key-recovery, no side-channel rig, and no predict-next-code** capability.

## Why a stock Flipper usually can't "just open" a rolling-code gate
- It can **decode and display** the locked protocol, but **Save/Emulate is disabled by firmware** for rolling-code vendors, and even a raw capture is **stale** once the real remote advances the counter.
- It does **not** hold the manufacturer/device key, so it **cannot mint a valid next code**.
- It is a **single-radio** device with no jam-while-capture mode, so RollJam-class attacks are out of reach.
- **"It didn't work" is the expected result** and almost always means the security is functioning — not that the Flipper is broken or mis-tuned. (Genuine failures are usually wrong **frequency/preset/deviation** on a *fixed-code* target — see [sub-ghz.md](../capabilities/sub-ghz.md).)
- CFW (Unleashed/Xtreme/Momentum) adds protocol labelling and sometimes owned-device helpers, but does **not** hand you anyone's secret key; the cryptographic barrier is identical.

## Blue-team takeaways
- Treat **any fixed-code** remote/sensor as **publicly cloneable** — assume an attacker can capture and replay it. Upgrade legacy gates.
- Prefer rolling-code systems with **time-expiry + challenge-response + AES** (e.g., Security+ 2.0, io-homecontrol, modern RKE) over bespoke single-direction ciphers.
- Favor products with **per-device keys / seed-based learning**, not a single manufacturer key reused across the line.
- Deploy **jam/interference detection** and don't rely on RF obscurity; assume the protocol is public.
- For high-value access, add an **independent factor** (PIN pad, app with server-side nonce, physical lock) so a single RF break isn't game-over.
- In assessments, demonstrating a **fixed-code replay** on owned hardware is a clean, lawful way to justify upgrades; rolling-code attacks (jamming, key recovery) are research-grade and often unlawful — keep them conceptual.

## Open questions / to research
- Exact **forward vs resync window** sizes per major brand (KeeLoq defaults are configurable; FAAC SLH ≈ 32-press out-of-range) `(verify)`.
- Current status of published analysis on **Security+ 2.0 / FAAC SLH2** and whether any practical (lawful, owned-device) tooling exists `(verify)`.
- Which rolling-code vendors current **CFW labels/partially parses** (serial + counter) vs only RAW-captures, and whether any expose save for owned devices `(verify)`.
- Practical reach of **RollBack-style** time-agnostic replays across modern RKE families.
- A clean, lawful **lab setup** (own seed/key, own receiver) to study KeeLoq counter behavior on hardware you own.

## Sources
- Flipper Sub-GHz docs / supported vendors: https://docs.flipper.net/zero/sub-ghz · https://docs.flipper.net/zero/sub-ghz/supported-vendors
- KeeLoq overview: https://en.wikipedia.org/wiki/KeeLoq
- Bogdanov, "Cryptanalysis of the KeeLoq block cipher" (2007): https://eprint.iacr.org/2007/055.pdf
- Eisenbarth/Kasper/Paar et al., "A Complete Break of the KeeLoq Code Hopping Scheme" (CRYPTO 2008): https://informatik.rub.de/wp-content/uploads/2022/01/crypto2008_keeloq.pdf
- RollJam (Samy Kamkar, DEF CON 2015) writeup: https://www.rtl-sdr.com/replicating-a-rolljam-wireless-vehicle-entry-attack-with-a-yardstick-one-and-rtl-sdr/
- RollBack time-agnostic replay (2022): https://dl.acm.org/doi/full/10.1145/3627827
- Chamberlain Security+ 2.0 overview: https://www.chamberlaindiy.com.au/news/behind-the-tech-how-security-2-0-keeps-your-garage-safe-and-secure/
- Security+ reverse engineering (argilo/secplus): https://github.com/argilo/secplus
- Somfy RTS protocol (PushStack): https://pushstack.wordpress.com/somfy-rts-protocol/
- FAAC/Genius SLH (PandwaRF): https://pandwarf.com/news/kaiju-support-for-faac-genius-slh-protocol-master-slave-remotes-gate-openers/
