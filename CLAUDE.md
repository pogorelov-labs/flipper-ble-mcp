# Flipper Zero KB — agent guide

This directory is a **research knowledge base** (~55 markdown docs, ~70k words) about the
Flipper Zero — *not* a code project. There is nothing to build or test. Your job when working
here is to **read, navigate, answer from, and extend** the KB.

## Where to start
1. **[llms.txt](llms.txt)** — generated one-line map of every doc (token-lean). Read this first to locate things.
2. **[README.md](README.md)** — the human index (richer tables, conventions, device context).
3. **Grep the frontmatter** (see schema below) for structured lookups — far cheaper than reading bodies.
4. **[use-cases.json](use-cases.json)** + **[uc-index.json](uc-index.json)** — the 64-use-case dataset and the UC-ID → docs resolver.

## How to navigate efficiently
- **By topic:** `grep -rl "^domain: wifi" .` or `grep -rl "wpa" --include=*.md` then read only the hits.
- **By use case:** every doc tags its `use_cases:` (e.g. `UC-33`). To find where UC-33 lives: look it up in `uc-index.json`, or `grep -rl "UC-33" --include=*.md`.
- **By freshness:** facts that may be stale are flagged inline with `(verify)`. `grep -rn "(verify)" .` lists every volatile claim.
- **Follow `related:`** in frontmatter — it's the explicit cross-link graph between docs.
- Each sub-domain (`cards/ wifi/ bluetooth/ firmware/ hardware/ resources/`) has a `README.md` **hub**.

## Doc format (the house style — follow it when adding/editing)

Every `.md` content doc has this shape:

```markdown
---
title: WPA Handshake + PMKID Capture
domain: wifi
type: reference
status: detailed
summary: Capture the WPA 4-way handshake / PMKID and crack it offline with hashcat.
hardware: [esp32-marauder]
use_cases: [UC-33]
related: [wifi/own-network-audit.md, wifi/deauth.md, theory/human-layer.md]
tags: [wpa, pmkid, eapol, hashcat, offline-cracking]
last_verified: 2026-06-19
---

# WPA Handshake + PMKID Capture

> **TL;DR —** One or two sentences a reader/agent can use to judge relevance without reading the body.
> Cross-links to related docs. Part of the [KB](README.md).

<body…>

## Open questions / to research
- …

## Sources
- …
```

### Frontmatter schema (keys in this order; never omit a key — use `[]` for empty lists)
| Key | Meaning / controlled values |
|---|---|
| `title` | The doc's H1 text, verbatim. |
| `domain` | `core` (root docs) · `firmware` · `hardware` · `capabilities` · `cards` · `wifi` · `bluetooth` · `theory` · `topics` · `resources` |
| `type` | `index` (README) · `hub` (a folder README) · `reference` · `guide` (runnable / step-by-step) · `theory` · `personal` (`my-*`) · `dataset` · `resource-list` · `meta` (glossary/legal/roadmap) |
| `status` | `detailed` · `seeded` · `stub` (canonical machine source; the README badge mirrors it for humans) |
| `summary` | One line, ≤120 chars. Feeds `llms.txt` and the README index — keep it tight and specific. |
| `hardware` | What the doc needs. Vocab: `flipper-internal` · `cc1101-ext` · `esp32-marauder` · `nrf24` · `nrf52840` · `gps` · `vgm` · `devboard`. `[]` for pure theory/meta. |
| `use_cases` | UC-IDs covered, e.g. `[UC-33, UC-34]`. `[]` if none. |
| `related` | Relative paths to closely-related docs (the cross-link graph). |
| `tags` | 3–8 kebab-case topical tags. |
| `last_verified` | ISO date the content was last checked. |

### Body conventions
- **TL;DR-first:** the H1 is immediately followed by a `> **TL;DR —** …` blockquote. An agent should be able to decide relevance from frontmatter + TL;DR alone.
- **Heading skeleton:** free-form `##` sections per topic, but **every doc ends with `## Open questions / to research` then `## Sources`** (in that order). Capability/attack docs should, where relevant, include: intro → how it works → workflow/usage → defenses → `## Legitimate uses`.
- **`(verify)` flags:** append `(verify)` to any volatile fact (firmware versions, prices, product availability). Re-check before relying.
- **Cross-link** with relative links; mirror important ones into frontmatter `related:`.

## Extending the KB
1. Drop the new `.md` into the right sub-domain folder (or create one with a `README.md` hub).
2. Add complete frontmatter (schema above) + a TL;DR + `## Open questions` + `## Sources`.
3. Regenerate the maps: `python3 build-kb-index.py` (rebuilds `llms.txt`, the README index block, and `uc-index.json` from frontmatter — never hand-edit those).
4. Update the KB memory note if a convention changed.

## Generated artifacts (do not hand-edit)
- `llms.txt` — the doc map (from frontmatter `summary`).
- `llms-full.txt` — every doc concatenated (single-file context dump for models without file access).
- `uc-index.json` — UC-ID → docs resolver.
- The README index tables between the `<!-- BEGIN GENERATED INDEX -->` / `<!-- END GENERATED INDEX -->` markers.
- The doc-count and word-count in the README **State** line (normalized in place on each run).
