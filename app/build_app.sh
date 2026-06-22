#!/bin/zsh
# Build + ad-hoc-sign FlipperBLE.app — the small helper bundle that carries the macOS
# Bluetooth entitlement (its Info.plist has NSBluetoothAlwaysUsageDescription) and runs the
# BLE worker. Because it is BUILT LOCALLY it is not Gatekeeper-quarantined; macOS will prompt
# once for Bluetooth access on first use. No Apple Developer account required for personal use.
#
# Usage:  ./app/build_app.sh [PYTHON]
#   PYTHON  interpreter that can import the package + its deps (bleak, protobuf, flipper_ble_mcp).
#           Typically: make a venv, install the package, and pass its python:
#             python3 -m venv .venv && .venv/bin/pip install -e . && ./app/build_app.sh .venv/bin/python
set -e

HERE=${0:A:h}
PYTHON=${1:-$(command -v python3)}
HOME_DIR=${FLIPPER_AI_HOME:-$HOME/.flipper-ble-mcp}
mkdir -p "$HOME_DIR"

# Locate the installed ble_worker.py (prefer the installed package; fall back to the repo src tree).
WORKER=$("$PYTHON" -c 'import os, flipper_ble_mcp as m; print(os.path.join(os.path.dirname(m.__file__), "ble_worker.py"))' 2>/dev/null) \
  || WORKER="$HERE/../src/flipper_ble_mcp/ble_worker.py"
WORKER=${WORKER:A}
if [[ ! -f "$WORKER" ]]; then
  echo "✗ could not locate ble_worker.py (install the package, or run from the repo)"; exit 1
fi
SRCROOT=${WORKER:h:h}   # dir that contains the flipper_ble_mcp package (repo src/ or site-packages)

# Pre-flight: the daemon's python must have bleak + protobuf AND be able to import the package.
if ! PYTHONPATH="$SRCROOT" "$PYTHON" -c "import bleak, google.protobuf, flipper_ble_mcp" 2>/dev/null; then
  echo "✗ $PYTHON can't import the runtime (needs: bleak, protobuf, flipper_ble_mcp)."
  echo "  Install into a venv and pass its python, e.g.:"
  echo "    python3 -m venv .venv && .venv/bin/pip install -e . && ./app/build_app.sh .venv/bin/python"
  exit 1
fi

APP="$HOME_DIR/FlipperBLE.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"
cp "$HERE/Info.plist" "$APP/Contents/Info.plist"

cat > "$APP/Contents/MacOS/flipperble" <<EOF
#!/bin/zsh
# Launched via \`open\` so this .app is its own TCC principal (its Info.plist carries
# NSBluetoothAlwaysUsageDescription). Runs the BLE worker; stdout/stderr -> result file.
exec env PYTHONPATH="$SRCROOT" "$PYTHON" "$WORKER" "\$@" >"$HOME_DIR/ble_result.txt" 2>&1
EOF
chmod +x "$APP/Contents/MacOS/flipperble"

codesign -s - --force --deep "$APP"

echo "✅ Built + ad-hoc-signed:  $APP"
echo "   python:  $PYTHON"
echo "   worker:  $WORKER"
echo "   home:    $HOME_DIR"
echo "First BLE command will prompt macOS for Bluetooth access — grant it once."
