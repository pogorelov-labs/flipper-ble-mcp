# KB map — SEED vs LOCAL vs GENERATED

The classification that keeps the published repo **general** while the owner's private/rig-specific notes
grow in a gitignored overlay. The CAPTURE step uses this to decide where a new doc lands; the publisher uses
it to decide what ships.

## The rule (so you don't have to memorize the list)
- **`type: personal`** in frontmatter → **LOCAL**.
- A doc that is literally **the owner's own inventory, setup, backlog, or internal project plan** → **LOCAL**.
- **Everything else** — capabilities, cards, wifi, bluetooth, hardware, firmware, theory, topics, the MCP-method
  guides, curated resource lists, conventions, and the toolchain — is general knowledge → **SEED**.
- The doc-map files (`llms.txt`, `llms-full.txt`, `uc-index.json`, the README index block) are **GENERATED** —
  reproducible from frontmatter, never hand-authored, never the source of truth.

When in doubt, ask: *"would this help anyone with a Flipper + this add-on, or only **this** owner?"* General → SEED.

## SEED — ships in the published repo (commit in place)
- **Conventions & toolchain:** `CLAUDE.md`, `build-kb-index.py`, `build-use-cases-json.py`, `use-cases.json`, `use-cases.csv`, `README.md`.
- **Core knowledge:** `01-architecture.md`, `glossary.md`, `legal-and-safety.md`, `use-cases-model.md`.
- **All of** `capabilities/`, `cards/`, `wifi/`, `bluetooth/`, `hardware/`, `firmware/`, `theory/`, `topics/` (references, hubs, guides, theory, topic docs — general by nature).
- **`resources/` — method & blueprint docs:** `flipper-control-playbook.md`, `flipper-ble-control.md`, `flipper-control-mcp-server.md`, `flipper-read-mcp-server.md`, `mcp-setup-claude-code.md`, `flipper-healthwatch.md` (the *pattern* is reusable; it documents owner tooling — generalize wording when promoting).
- **`resources/` — curated lists:** `best-github-repos.md`, `community-and-video.md`, `cool-projects.md`, `github-landscape.md`, `learning-and-docs.md`, `notable-apps-and-data.md`, `subghz-device-repos.md`, `tools-and-software.md`, `flipper-mcp-and-ai.md`.
- **`resources/` — app runbooks** (⚠️ *rig-flavored* — written "on my Momentum rig" but the per-app knowledge is reusable; keep in SEED, generalize specifics when you touch them): `apps-subghz.md`, `apps-nfc.md`, `apps-rfid-ibutton-infrared.md`, `apps-badusb-automotive-misc.md`, `apps-esp-ble-nrf24.md`.

## LOCAL — owner/rig-specific (lives in `kb-local/`, gitignored, not published as-is)
| Doc | Why LOCAL |
|---|---|
| `my-setup.md` | `type: personal` — the owner's exact rig (FZ.1, SD, modules, wiring) |
| `my-use-cases.md` | `type: personal` — what the owner's exact kit can do |
| `resources/apps-inventory.md` | The owner's literal ~240-fap install list |
| `roadmap.md` | The owner's open-work backlog (regenerable from docs' Open-questions) |
| `frontier-roadmap.md` | The owner's private staged plan toward an AI-driven rig |
| `resources/publishing-plan.md` | Internal meta about publishing *this* repo — not Flipper knowledge |

> These six are currently committed in the repo's root/`resources/`. When the parallel repo-structure session
> finalizes the publishable layout, they either move under `kb-local/` or ship as `*.example.md` templates with
> the owner's specifics scrubbed. Until then they stay put — this table is the **intent**, the source of truth
> for what counts as "private."

## GENERATED — never hand-edit, rebuilt by `build-kb-index.py`
`llms.txt` · `llms-full.txt` · `uc-index.json` · the `README.md` index block (between the BEGIN/END markers) ·
the doc/word counts in the README State line.

## Overlay + PR-back mechanics
- **`kb-local/` is the overlay**: gitignored (except its own `README.md`). New **owner/rig-specific** captures land
  here; the SEED tree stays clean and publishable.
- **Promote "gold":** when a `kb-local/` learning turns out to be general (a gotcha/format/method anyone would
  hit), *generalize* it (strip private specifics), **move it into the SEED tree**, cross-link + reindex, and open a
  **PR upstream**. That's how the published seed compounds over time.
- **The index build excludes the overlay.** `build-kb-index.py` skips `kb-local/` (along with `.claude/` and
  `memory/`), so the generated maps are **always seed-only** — overlay notes never leak, no clean-checkout dance.
  The only residual publish concern is the six in-tree LOCAL docs below, until they're moved or scrubbed.

## Open questions (for task #7 / the parallel repo session)
- The six in-tree LOCAL docs are still indexed (they live in the seed tree, not under `kb-local/`): move them to
  `kb-local/` or ship scrubbed `*.example.md` so the published index is fully seed-only.
- Do the six LOCAL docs move to `kb-local/` or ship as scrubbed `*.example.md`? (Affects relative links + hub maps.)
- Where do the MCP server sources (`~/flipper-ai/*`) sit in the published repo vs. referenced as a sibling project?
