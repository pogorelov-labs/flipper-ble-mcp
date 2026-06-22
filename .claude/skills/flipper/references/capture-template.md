# CAPTURE template + checklist

Copy the skeleton, fill it, then run the checklist. House style authority: [`CLAUDE.md`](CLAUDE.md). This mirrors
it so you don't have to re-read the whole guide mid-capture.

## Doc skeleton (new doc)
````markdown
---
title: <H1 text, verbatim>
domain: <core|firmware|hardware|capabilities|cards|wifi|bluetooth|theory|topics|resources>
type: <reference|guide|theory|hub|index|dataset|personal|resource-list|meta>
status: <detailed|seeded|stub>
summary: <one line ≤120 chars — feeds llms.txt + README index; tight & specific>
hardware: [<flipper-internal|cc1101-ext|esp32-marauder|nrf24|nrf52840|gps|vgm|devboard>]   # [] if pure theory/meta
use_cases: [<UC-NN, …>]    # [] if none
related: [<dir/doc.md, …>] # repo-root-relative; the cross-link graph
tags: [<3–8 kebab-case>]
last_verified: <YYYY-MM-DD>   # today
---

# <Title>

> **TL;DR —** <1–2 sentences: what this is + when to use it, enough to judge relevance without the body.>
> <Cross-links to the key related docs.> Part of the [<hub>](README.md) · [KB](../README.md).

<body — free-form ## sections. For a capability/attack doc: intro → how it works → workflow → defenses →
## Legitimate uses. Append `(verify)` to volatile facts.>

## Open questions / to research
- <what this session did NOT pin down — the next run's head start>

## Sources
- <this session (date) + commands run> · <external refs as full URLs>
````

> **Updating an existing doc instead?** Don't bolt on a near-duplicate — fold the new fact into the right `##`
> section, bump `last_verified`, flip any `(verify)` you confirmed, and add `related:` if you linked something new.

## Post-capture checklist (don't skip — half-captured = lost)
- [ ] **Home is right** — updated the closest existing doc, or a new doc only because it's genuinely its own topic.
- [ ] **Frontmatter complete & ordered** — all 10 keys, `[]` for empty, `summary` ≤120 chars, `last_verified` = today.
- [ ] **TL;DR present** right under the H1; ends with the `Part of the [KB]` line.
- [ ] **Ends with** `## Open questions / to research` then `## Sources` (in that order).
- [ ] **`(verify)` hygiene** — resolved what you confirmed (link the confirming doc), flagged what's still volatile.
- [ ] **Cross-linked both ways** — `related:` in the new doc *and* the docs it references; added to the domain hub/README map.
- [ ] **Classified** SEED vs LOCAL per [`kb-map.md`](.claude/skills/flipper/references/kb-map.md); LOCAL → `kb-local/`.
- [ ] **No secrets** — no card UIDs/keys, EMV PANs, handshakes, credentials, or private targets.
- [ ] **Reindexed** — ran `python3 build-kb-index.py`; confirmed the doc shows in `llms.txt`, `uc-index.json` (under its UC), and the README index. Did **not** hand-edit generated files.
- [ ] **"Gold" flagged** — if a LOCAL learning is actually general, noted it for promotion + PR upstream.

## Worked example
The cleanest reference for "what good looks like" is [`wifi/marauder-mcp-scan.md`](wifi/marauder-mcp-scan.md) —
written from a live session: full frontmatter, TL;DR, a runnable recipe, it **resolved a `(verify)`** in a sibling
doc, cross-linked both ways, and was followed by a `build-kb-index.py` rebuild.
