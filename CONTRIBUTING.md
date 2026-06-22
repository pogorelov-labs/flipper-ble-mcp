# Contributing

Thanks for helping improve **flipper-ble-mcp**!

## Ground rules
- This is a **dual-use** project — contributions must support legitimate, authorized use. No
  features whose primary purpose is detection-evasion, mass/abusive targeting, or attacking systems
  you don't own. See [SECURITY.md](SECURITY.md).
- Be kind; assume good faith.

## Code
- Python ≥ 3.11, `src/` layout, managed with [`uv`](https://docs.astral.sh/uv/).
- Lint/format with **`ruff`** (`ruff check` / `ruff format`) — keep it green.
- The daemon's verified protobuf builders/parsers are the **single source of truth**; reuse them.
- **Never commit secrets or device-identifying data.** The control token, sockets, screen captures,
  and health-watch logs are all in `.gitignore` — keep it that way.

## Contributing knowledge (the self-evolving KB)
The knowledge base at the repo root is the project's memory. Two ways to improve it:

1. **Direct edits** to seed docs — follow the **house style**: YAML frontmatter in the documented
   key order, a `> **TL;DR —**` blockquote right after the H1, ending with
   `## Open questions / to research` then `## Sources`. After editing, regenerate the index:
   `python3 build-kb-index.py`. **Never hand-edit** the generated artifacts
   (`llms.txt`, `llms-full.txt`, the README index block).

2. **PR-back a learned entry.** Sessions accumulate learnings in the per-install local overlay
   (`kb-local/`, flagged `pr_back_candidate: true`). If one is broadly useful,
   move it into the right domain folder, **strip any rig-specific detail** (device name, BLE
   MAC, personal paths), conform it to the house style, regenerate the index, and open a PR. This is
   how collective session experience compounds into the shipped seed.

## Pull requests
- One focused change per PR; say what and why.
- Run `ruff` and `python3 build-kb-index.py` before pushing if you touched code or KB docs.
