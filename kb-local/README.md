# kb-local/ — the local overlay (private, not published)

This is where **owner/rig-specific** Flipper knowledge grows without touching the publishable **SEED** tree.
Everything in here except this README is **gitignored** — it never ships in the public repo.

## What lands here
- Captures the `/flipper-learn` loop classifies as **LOCAL**: your exact device specifics, private app inventory,
  personal targets/notes, anything that would only help *you*.
- The owner-specific docs that currently live in the seed tree but conceptually belong here — see the LOCAL table
  in [`.claude/skills/flipper/references/kb-map.md`](../.claude/skills/flipper/references/kb-map.md)
  (`my-setup.md`, `my-use-cases.md`, `resources/apps-inventory.md`, `roadmap.md`, `frontier-roadmap.md`,
  `resources/publishing-plan.md`). They stay put until the publishable layout is finalized; this dir is their home.

## What does NOT land here
General, reusable knowledge (a gotcha/format/method anyone with the kit would hit) → the **SEED** tree, committed.
When unsure: *"would this help anyone, or only me?"*

## Promote "gold" → SEED → PR upstream
When a LOCAL note turns out to be general: **generalize** it (strip private specifics), **move** it into the
right SEED directory, cross-link + `python3 build-kb-index.py`, and open a **PR** to the upstream repo. That's how
the published seed compounds.

## Index hygiene
`build-kb-index.py` **excludes `kb-local/` from the generated maps** (`llms.txt` / `llms-full.txt` /
`uc-index.json`), so overlay notes never leak into the published index — capture freely here. Navigate this
overlay directly (it's small and personal); if you ever want it in a *private* index, build a separate local map
rather than committing one.
