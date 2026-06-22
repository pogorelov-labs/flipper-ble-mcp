---
description: Distill the current Flipper session's learnings into the KB (the CAPTURE loop)
argument-hint: "[optional: title/topic hint, e.g. 'nrf24 mousejack range']"
---

You are running the **CAPTURE** step of the Flipper operating loop — turning what just happened in this
session into durable, re-discoverable KB knowledge so the next run is faster. Work in this repo's KB and
follow its house style ([`CLAUDE.md`](CLAUDE.md)). Optional focus hint from the user: **$ARGUMENTS**

Do this in order; think before writing:

1. **Decide if there's anything worth capturing.** Scan what this session actually did/learned: a verified
   workflow, a menu path, a file/log format, a transport quirk, a non-obvious gotcha, a `(verify)` you
   confirmed or newly doubt. **If nothing is durable** (pure chatter, or all already in the KB), say so and
   stop — don't manufacture filler. **Never capture secrets** (card UIDs/keys, EMV PANs, handshakes,
   credentials) — redact or omit.

2. **Find the home.** Search first: `grep -rl "^domain: <d>" .`, [`uc-index.json`](uc-index.json) for the
   use case, and the relevant `*/README.md` hub. **Prefer updating the closest existing doc** over creating a
   near-duplicate. Only create a new doc when the learning is genuinely its own topic.

3. **Write it KB-style.** New or updated doc must have: full **ordered frontmatter** (title, domain, type,
   status, summary ≤120 chars, hardware, use_cases, related, tags, last_verified — never omit a key, `[]` for
   empty) → a `> **TL;DR —**` blockquote → free-form `##` body → `## Open questions / to research` → `## Sources`.
   Use the skeleton in [`.claude/skills/flipper/references/capture-template.md`](.claude/skills/flipper/references/capture-template.md).
   Set `last_verified` to today. Append `(verify)` to volatile facts (firmware versions, prices, availability);
   **resolve** any `(verify)` flag this session actually confirmed (and link the doc that confirmed it).

4. **Cross-link both ways.** Add `related:` entries in the new doc *and* in the docs it relates to; add it to
   the domain **hub/README map** so it's reachable by browsing, not just by search. An orphan doc is a lost doc.

5. **Classify SEED vs LOCAL** ([`.claude/skills/flipper/references/kb-map.md`](.claude/skills/flipper/references/kb-map.md)):
   - **General / reusable** (capability, method, gotcha, format anyone with the kit would hit) → commit into the
     **SEED** tree in place.
   - **Owner/rig-specific** (your exact app inventory, personal setup, private targets) → put under **`kb-local/`**
     (the gitignored overlay), not the seed tree.
   - If a `kb-local/` learning later proves general, **promote** it: generalize, move into SEED, and flag it for a
     PR back upstream ("gold").

6. **Rebuild the generated maps.** Run `python3 build-kb-index.py`. Verify the new/updated doc appears in
   `llms.txt`, in `uc-index.json` under its UC(s), and in the README index. **Never hand-edit** those generated files.

7. **Report.** Summarize: what was captured, where it lives (path + SEED/LOCAL), which `(verify)` flags moved,
   what cross-links/hub entries were added, and any "gold" worth a PR. Note follow-ups in the doc's
   `## Open questions` so the next session has a head start.
