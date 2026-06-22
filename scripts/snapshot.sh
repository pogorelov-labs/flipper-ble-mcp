#!/bin/zsh
# Re-snapshot the curated PUBLIC seed from your PRIVATE living KB (flipper-zero).
#
# Two-repo model: flipper-zero is where you work + drive the device + accrue learnings (kb-local);
# THIS repo is the published package. Run this to refresh the package after the KB grows:
#   ./scripts/snapshot.sh [path-to-flipper-zero]
#
# It mirrors the KB (minus the 6 LOCAL docs) + the canonical skill, sanitizes rig/device/path
# identifiers, and regenerates the seed-only index. Package-specific files (src/, app/, pyproject,
# server.json, README.md, build-kb-index.py, LICENSE, scaffolding) are PRESERVED — not overwritten.
set -e

SRC=${1:-"$HOME/msc_1/flipper-zero"}      # the private living KB
DST=${0:A:h:h}                             # repo root (scripts/ is one level down)
LOCAL_DOCS=(my-setup.md my-use-cases.md roadmap.md frontier-roadmap.md \
            resources/apps-inventory.md resources/publishing-plan.md)

echo "snapshot:  $SRC  ->  $DST"
[[ -d "$SRC" ]] || { echo "✗ source KB not found: $SRC"; exit 1; }

# 1. refresh KB content (remove + copy → faithful mirror, incl. upstream deletions)
for d in bluetooth capabilities cards firmware hardware resources theory topics wifi; do
  rm -rf "$DST/$d"; cp -R "$SRC/$d" "$DST/"
done
cp "$SRC/01-architecture.md" "$SRC/CLAUDE.md" "$SRC/glossary.md" "$SRC/legal-and-safety.md" \
   "$SRC/use-cases-model.md" "$SRC/use-cases.json" "$SRC/build-use-cases-json.py" "$DST/"
[[ -f "$SRC/use-cases.csv" ]] && cp "$SRC/use-cases.csv" "$DST/"
rm -rf "$DST/.claude"; cp -R "$SRC/.claude" "$DST/"          # canonical skill + /flipper-learn
mkdir -p "$DST/kb-local"; cp "$SRC/kb-local/README.md" "$DST/kb-local/"

# 2. drop LOCAL / owner-private docs from the published seed
for f in $LOCAL_DOCS; do rm -f "$DST/$f"; done

# 3. sanitize rig/device/path identifiers (skips src/ — already clean; never touches the author name)
grep -rIl -e dflip -e "/Users/" -e "com.ruslan" "$DST" \
     --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=src 2>/dev/null | while IFS= read -r f; do
  sed -i '' \
    -e 's#com\.ruslan\.flipper-healthwatch#com.flipper-ble-mcp.healthwatch#g' \
    -e 's#com\.ruslan\.flipperble#com.flipper-ble-mcp.app#g' \
    -e 's#com\.ruslan#com.flipper-ble-mcp#g' \
    -e 's#/Users/[A-Za-z0-9_.-]*#~#g' \
    -e 's/dflip/the device/g' "$f"
done

# 4. regenerate the seed-only index (excludes README/CLAUDE/CONTRIBUTING/SECURITY; prunes kb-local)
python3 "$DST/build-kb-index.py"

# 5. report
echo "PII check:"
for p in dflip com.ruslan "/Users/ruslan"; do
  echo "  $p -> $(grep -rIil "$p" "$DST" --exclude-dir=.git 2>/dev/null | wc -l | tr -d ' ')"
done
echo "Review 'git diff', then commit + push the curated release."
