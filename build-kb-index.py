#!/usr/bin/env python3
"""
build-kb-index.py — regenerate the KB's machine-facing maps from per-doc frontmatter.

Outputs (all are GENERATED — do not hand-edit):
  - llms.txt            one-line map of every doc (llms.txt standard; token-lean)
  - llms-full.txt       every doc concatenated (single-file context dump)
  - uc-index.json       UC-ID -> docs resolver (+ name/score joined from use-cases.json)
  - README.md           the index tables between the BEGIN/END GENERATED INDEX markers

Source of truth = the YAML frontmatter block at the top of each .md doc
(see CLAUDE.md for the schema). No third-party deps (tolerant inline parser).

Usage:
  python3 build-kb-index.py            # write all artifacts
  python3 build-kb-index.py --dry-run  # report only; write nothing
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Files that are entry points / generated / meta — never listed as content docs.
EXCLUDE = {"README.md", "CLAUDE.md", "CONTRIBUTING.md", "SECURITY.md"}

DOMAIN_ORDER = ["core", "firmware", "hardware", "capabilities", "cards",
                "wifi", "bluetooth", "theory", "topics", "resources"]
DOMAIN_TITLE = {
    "core": "Start here / Core",
    "firmware": "Firmware",
    "hardware": "Hardware & GPIO",
    "capabilities": "Capabilities (built-in feature deep-dives)",
    "cards": "Cards, NFC & RFID (deep-research sub-domain)",
    "wifi": "Wi-Fi (ESP32 Marauder add-on)",
    "bluetooth": "Bluetooth / BLE",
    "theory": "Theory",
    "topics": "Topics",
    "resources": "Resources",
}
# Preferred ordering inside the core domain (others appended alphabetically).
CORE_ORDER = ["my-setup.md", "my-use-cases.md", "use-cases-model.md",
              "01-architecture.md", "legal-and-safety.md", "glossary.md",
              "roadmap.md", "frontier-roadmap.md"]
STATUS_BADGE = {"detailed": "✅", "seeded": "🌱", "stub": "🧩"}

BEGIN = "<!-- BEGIN GENERATED INDEX"          # prefix (line carries a hint comment)
END = "<!-- END GENERATED INDEX -->"


# ---------- frontmatter parsing (tolerant; no PyYAML) ----------
def split_frontmatter(text: str):
    """Return (meta_dict_or_None, body_without_frontmatter)."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    block = text[3:end].strip("\n")
    rest = text[end + 4:]
    if rest.startswith("\n"):
        rest = rest[1:]
    meta = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",")]
            meta[key] = [x for x in items if x]
        else:
            meta[key] = val.strip('"').strip("'")
    return meta, rest


def first_h1(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def derive_summary(body: str) -> str:
    """Fallback summary for docs lacking frontmatter: the TL;DR or first prose line."""
    for line in body.splitlines():
        s = line.strip()
        if "TL;DR" in s:
            s = s.split("—", 1)[-1].strip() if "—" in s else s
            return s.strip("> *").strip()[:120]
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith(("#", ">", "|", "-", "```", "<!--")):
            return s[:120]
    return ""


# ---------- collect docs ----------
def collect():
    docs = []
    missing = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # prune: hidden dirs (.git/.claude), the auto-memory dir, and the gitignored
        # local overlay — none are publishable KB content.
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("memory", "kb-local")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if rel in EXCLUDE:  # only the ROOT README.md / CLAUDE.md, not sub-domain hubs
                continue
            text = open(full, encoding="utf-8").read()
            meta, body = split_frontmatter(text)
            folder = os.path.dirname(rel)
            default_domain = "core" if folder == "" else folder.split("/")[0]
            if meta is None:
                missing.append(rel)
                meta = {}
            doc = {
                "path": rel.replace(os.sep, "/"),
                "fname": fn,
                "title": meta.get("title") or first_h1(text) or fn,
                "domain": meta.get("domain") or default_domain,
                "type": meta.get("type", ""),
                "status": meta.get("status", "stub"),
                "summary": meta.get("summary") or derive_summary(body),
                "use_cases": meta.get("use_cases", []) or [],
                "related": meta.get("related", []) or [],
                "tags": meta.get("tags", []) or [],
                "body": body,
                "has_meta": bool(meta) and "title" in meta,
            }
            docs.append(doc)
    docs.sort(key=lambda d: d["path"]); return docs, missing


def sort_key(doc):
    d = doc["domain"]
    di = DOMAIN_ORDER.index(d) if d in DOMAIN_ORDER else len(DOMAIN_ORDER)
    if d == "core":
        ci = CORE_ORDER.index(doc["fname"]) if doc["fname"] in CORE_ORDER else 99
        return (di, ci, doc["title"].lower())
    # hubs (folder README) first within a sub-domain
    hub = 0 if doc["fname"] == "README.md" else 1
    return (di, hub, doc["title"].lower())


def grouped(docs):
    out = {}
    for doc in sorted(docs, key=sort_key):
        out.setdefault(doc["domain"], []).append(doc)
    ordered = [(d, out[d]) for d in DOMAIN_ORDER if d in out]
    ordered += [(d, out[d]) for d in out if d not in DOMAIN_ORDER]
    return ordered


# ---------- renderers ----------
def render_llms_txt(groups, total):
    L = ["# Flipper Zero — Research Knowledge Base", ""]
    L.append("> Structured research KB on the Flipper Zero — architecture, firmware, "
             "hardware/GPIO, cards/NFC, Wi-Fi & BLE, RF & security theory, scored use "
             "cases, and curated resources.")
    L.append("")
    L.append(f"This file is generated from per-doc frontmatter ({total} docs). "
             "See CLAUDE.md for navigation conventions and the frontmatter schema.")
    L.append("")
    L.append("## Start here")
    L.append("- [CLAUDE.md](CLAUDE.md): agent guide — how to navigate, frontmatter schema, house style")
    L.append("- [README.md](README.md): human index + device context + conventions")
    L.append("")
    for domain, items in groups:
        L.append(f"## {DOMAIN_TITLE.get(domain, domain.title())}")
        for d in items:
            uc = f" ({', '.join(d['use_cases'])})" if d["use_cases"] else ""
            L.append(f"- [{d['path']}]({d['path']}): {d['summary']}{uc}")
        L.append("")
    return "\n".join(L).rstrip() + "\n"


def render_readme_index(groups):
    L = ["## Index", ""]
    for domain, items in groups:
        L.append(f"### {DOMAIN_TITLE.get(domain, domain.title())}")
        L.append("| File | Status | What's in it |")
        L.append("|---|---|---|")
        for d in items:
            badge = STATUS_BADGE.get(d["status"], "🧩")
            L.append(f"| [{d['path']}]({d['path']}) | {badge} | {d['summary']} |")
        L.append("")
        if domain == "core":
            L.append("> **Dataset:** [use-cases.csv](use-cases.csv) / "
                     "[use-cases.json](use-cases.json) — regenerate the JSON with "
                     "`python3 build-use-cases-json.py`. UC-ID → docs map: "
                     "[uc-index.json](uc-index.json).")
            L.append("")
    return "\n".join(L).rstrip() + "\n"


def render_llms_full(groups):
    L = ["# Flipper Zero KB — full text dump", "",
         "Generated by build-kb-index.py. Every content doc concatenated "
         "(frontmatter stripped). See llms.txt for the map.", ""]
    for domain, items in groups:
        for d in items:
            L.append(f"\n{'='*80}")
            L.append(f"# {d['title']}")
            L.append(f"Source: {d['path']}  |  domain: {d['domain']}  |  status: {d['status']}")
            L.append("="*80 + "\n")
            L.append(d["body"].strip())
            L.append("")
    return "\n".join(L).rstrip() + "\n"


def build_uc_index(docs):
    """UC-ID -> docs. Canonical home from the dataset's kb_ref column; the docs'
    own frontmatter use_cases add cross-references. The dataset makes the map
    complete even for UCs no doc tags in frontmatter."""
    rows_by_id = {}
    ucj = os.path.join(ROOT, "use-cases.json")
    if os.path.exists(ucj):
        try:
            data = json.load(open(ucj, encoding="utf-8"))
            rows = data if isinstance(data, list) else data.get("use_cases", data.get("rows", []))
            if isinstance(rows, dict):
                rows = list(rows.values())
            for r in rows or []:
                if isinstance(r, dict) and r.get("id"):
                    rows_by_id[r["id"]] = r
        except Exception as e:  # never let the dataset break the build
            print(f"  (note: could not read use-cases.json: {e})")

    index = {}

    def ensure(uc):
        return index.setdefault(uc, {"canonical_doc": "", "docs": []})

    # 1) canonical home + metadata from the dataset (kb_ref)
    for uc, r in rows_by_id.items():
        e = ensure(uc)
        e["name"] = r.get("name", "")
        e["category"] = r.get("category", "")
        e["real_use_score"] = r.get("real_use_score", "")
        e["status"] = r.get("status", "")
        kb = (r.get("kb_ref") or "").strip()
        if kb:
            e["canonical_doc"] = kb
            if kb not in e["docs"]:
                e["docs"].append(kb)

    # 2) cross-references from each doc's frontmatter use_cases
    for d in docs:
        for uc in d["use_cases"]:
            e = ensure(uc)
            if d["path"] not in e["docs"]:
                e["docs"].append(d["path"])

    return {
        "_generated_by": "build-kb-index.py",
        "_source": "use-cases.json kb_ref (canonical) + frontmatter use_cases (cross-refs)",
        "count": len(index),
        "use_cases": {k: index[k] for k in sorted(index)},
    }


def replace_between_markers(text: str, new_block: str) -> str | None:
    i = text.find(BEGIN)
    j = text.find(END)
    if i == -1 or j == -1:
        return None
    line_end = text.find("\n", i)
    head = text[:line_end + 1]            # keep the BEGIN marker line
    tail = text[j:]                       # keep END marker onward
    return head + new_block + "\n" + tail


def main():
    dry = "--dry-run" in sys.argv
    docs, missing = collect()
    groups = grouped(docs)
    total = len(docs)
    words_k = round(sum(len(d["body"].split()) for d in docs) / 1000)

    print(f"Scanned {total} content docs across {len(groups)} domains (~{words_k}k words).")
    if missing:
        print(f"⚠ {len(missing)} doc(s) missing/!complete frontmatter "
              f"(used fallbacks): {', '.join(missing)}")

    artifacts = {
        "llms.txt": render_llms_txt(groups, total),
        "llms-full.txt": render_llms_full(groups),
        "uc-index.json": json.dumps(build_uc_index(docs), indent=2, ensure_ascii=False) + "\n",
    }

    # README: normalize the State-line counts, then replace the index between markers
    readme_path = os.path.join(ROOT, "README.md")
    readme = open(readme_path, encoding="utf-8").read()
    readme = re.sub(r"\b\d+ content docs", f"{total} content docs", readme, count=1)
    readme = re.sub(r"~\s*\d+k words", f"~{words_k}k words", readme, count=1)
    new_readme = replace_between_markers(readme, render_readme_index(groups))
    if new_readme is None:
        print("⚠ README.md missing GENERATED INDEX markers — writing count-normalized README only.")
        artifacts["README.md"] = readme
    else:
        artifacts["README.md"] = new_readme

    if dry:
        print(f"\nState line would read: {total} content docs, ~{words_k}k words")
        print("--dry-run: would write " + ", ".join(artifacts))
        print("\n----- llms.txt preview (first 40 lines) -----")
        print("\n".join(artifacts["llms.txt"].splitlines()[:40]))
        return

    for name, content in artifacts.items():
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(content)
        print(f"  wrote {name}")
    uc_count = json.loads(artifacts["uc-index.json"])["count"]
    print(f"Done. {total} docs indexed (~{words_k}k words), {uc_count} UC-IDs mapped.")


if __name__ == "__main__":
    main()
