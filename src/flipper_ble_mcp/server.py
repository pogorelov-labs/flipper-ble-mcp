#!/usr/bin/env python3
"""
flipper-ble — WIRELESS control MCP server for the Flipper Zero (no USB cable).

Drives the Flipper over Bluetooth LE by shelling out to FlipperBLE.app — the signed
app-bundle that carries the macOS Bluetooth usage entitlement (see
resources/flipper-ble-control.md). The MCP server process NEVER touches Bluetooth
directly: all BT happens *inside* the .app, which is its own TCC principal. That's why
this works even though Claude Desktop itself lacks the Bluetooth entitlement.

Capabilities (all over BLE — same protobuf RPC as USB, but NO start_rpc_session):
  - device_info     : read 60+ device fields
  - screenshot      : capture the 128x64 screen as PNG (the agent's eyes)
  - press           : inject one UI button (up/down/left/right/ok/back; short/long/press/release)
  - press_sequence  : a macro of presses in ONE connection (efficient navigation)
  - scan            : diagnostic — is the Flipper advertising right now?

Closed loop: press / press_sequence default to grabbing a screenshot in the SAME BLE
connection, so the agent SEES the result of what it pressed.

SAFETY: every press is a real action; Claude Desktop prompts per call = the human gate.
This is the wireless counterpart to the USB `flipper-control` server.

REQUIRES: the Flipper's BLE must be FREE — not connected to your phone (only one BLE
central at a time). If a call returns "device not found", disconnect the phone's Flipper
app (or toggle the Flipper's Bluetooth) and retry. Transient not-advertising is
auto-retried once.
"""
import os
import subprocess
import time

from mcp.server.fastmcp import FastMCP, Image

HOME = os.environ.get("FLIPPER_AI_HOME") or os.path.expanduser("~/.flipper-ble-mcp"); os.makedirs(HOME, exist_ok=True)
APP = f"{HOME}/FlipperBLE.app"
RESULT = f"{HOME}/ble_result.txt"
PNG = f"{HOME}/ble_screen.png"
FILEBIN = f"{HOME}/ble_file.bin"
UPLOAD = f"{HOME}/ble_upload.bin"
HEALTHWATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flipper_healthwatch.py")
PY = "/usr/bin/python3"                          # stdlib-only watcher → system python, PATH-independent

mcp = FastMCP("flipper-ble")

BUTTONS = {"up", "down", "left", "right", "ok", "back"}
KINDS = {"short", "long", "press", "release"}


import base64  # noqa: E402
import json  # noqa: E402
import socket  # noqa: E402

SOCK = f"{HOME}/bled.sock"
TOKEN_FILE = f"{HOME}/bled.token"


def _read_token():
    try:
        with open(TOKEN_FILE) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def _daemon_send(cmd, args, timeout, token=None):
    """Send one request to the resident BLE daemon; return the response dict, or None if unreachable."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect(SOCK)
        s.sendall((json.dumps({"cmd": cmd, "args": list(args), "token": token}) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        s.close()
        return json.loads(buf.decode())
    except (OSError, ValueError):
        return None


def _ensure_daemon():
    """Ensure the resident BLE daemon is up + return its auth token (cold-starting via the app bundle,
    one-time TCC, if needed). Returns the token string, or None on failure."""
    tok = _read_token()
    if tok and _daemon_send("health", [], 3, tok) is not None:
        return tok
    subprocess.Popen(["open", APP, "--args", "daemon"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(25):  # ~25s for app launch + socket bind + token file
        time.sleep(1)
        tok = _read_token()
        if tok and _daemon_send("health", [], 3, tok) is not None:
            return tok
    return None


def _run_worker(args, want_png=False, timeout=90, _retry=True):
    """Route a command through the resident daemon (held BLE connection). Returns (text, png|None).
    Same contract as the old per-call worker, so the tool wrappers are unchanged."""
    cmd, rest = args[0], list(args[1:])
    tok = _ensure_daemon()
    if not tok:
        return ("BLE daemon unavailable — couldn't launch FlipperBLE.app (check Bluetooth/TCC).", None)
    resp = _daemon_send(cmd, rest, timeout, tok)
    if resp is None:
        return ("BLE daemon stopped responding — retry.", None)
    text = resp.get("text") or ("OK" if resp.get("ok") else "(no output)")
    if _retry and ("device not found" in text or "connection lost" in text):
        time.sleep(3)
        return _run_worker(args, want_png=want_png, timeout=timeout, _retry=False)
    png = base64.b64decode(resp["png_b64"]) if resp.get("png_b64") else None
    return (text, png)


def _not_found_hint(text: str) -> str:
    return (f"{text}\n\n↳ Flipper not reachable over BLE. It's likely connected to your "
            f"phone (one BLE central at a time) or asleep. Disconnect the phone's Flipper "
            f"app (or toggle the Flipper's Bluetooth) and retry. Use `scan` to check.")


def _text_call(args, timeout=45) -> str:
    """Run a worker command that returns a text result; map not-found to the hint."""
    text, _ = _run_worker(args, timeout=timeout)
    if "device not found" in text:
        return _not_found_hint(text)
    return text or "(no output)"


PLAYBOOK_TEXT = """\
FLIPPER BLE CONTROL — OPERATING MANUAL (data-first, screenshot-last)

CORE CONSTRAINT: RPC exposes structured DATA (files, device/power info, app flags) but NO UI tree —
the screen is just a 1024-byte framebuffer. The only UI introspection is screenshot + vision, so it's
the FALLBACK, not the default. A resident daemon holds ONE BLE connection, so calls are fast now:
status/list/read ~0.1-0.3s, screenshot/press ~1.5s; only the FIRST connect (or a post-idle reconnect)
costs ~6-25s. Batching still helps a little; screenshot to verify.

ALGORITHM - use the highest rung that reaches the goal:
 1. PURE DATA: storage_read/list/stat/info/md5, device_info, power_info. (Read a .sub? storage_read -
    don't navigate to it.)
 2. DIRECT ENTRY: app_launch(name) / app_launch(name, args=<file>) / app_load_file - jump into an app
    or straight to a file's screen (one call, no menu hops).
 3. SEMANTIC: app_button(name), transmit_subghz/infrared - named action, no pixels.
 4. BATCHED BLIND NAV: press_sequence("down down ok") + ONE trailing +shot - known path, verify once.
 5. SCREENSHOT LOOP: only for unknown/dynamic UI (variable lists, confirm dialogs, errors):
    screenshot -> read -> press(+shot), re-shooting only at unpredictable decision points.
VERIFY CHEAPLY: +shot on the LAST press, or app_lock_status / desktop_is_locked - not every press.

MENU MAPS (Momentum mntm-dev; re-verify after firmware updates):
 - Desktop -> press ok -> main menu CAROUSEL. "Start" (dolphin) leftmost; MNTM + Settings at far RIGHT.
   press left from Start WRAPS to the end (Settings, then MNTM). back -> desktop.
 - Momentum settings: main menu -> left left (-> MNTM) -> ok -> Interface / Protocols / Misc.
 - Protocols: SubGHz Freqs / SubGHz Bypass Region Lock (toggle) / SubGHz Extend Freq Bands (locked
   until bypass ON) / GPIO Pins.
 - REGION-BYPASS (from desktop): press_sequence("ok left left ok down ok down right") -> "Are you
   sure?" dialog -> press right (= Yes). Back fully out to save.

APP-ENTRY RECIPES (exact names from the USB read server's app_list / `loader list`):
 - app_launch("Sub-GHz", args="/ext/subghz/.../X.sub") -> transmitter/send screen (freq preset + Send;
   region permitting). press ok = transmit (gated).
 - app_launch("Infrared", args="/ext/infrared/X.ir") -> remote button list; press right to select,
   press ok to fire (gated).
 - app_launch("NFC" / "125 kHz RFID" / "GPIO" / "U2F" / "Bad USB" ...) -> that app's main screen.

INPUT / WIDGET CONVENTIONS:
 - Carousel: left/right move, ok enter, back -> desktop.
 - Vertical list: up/down move, ok enter, back up one level.
 - Inline toggle ("X ... OFF"): right/left changes value; may raise a confirm dialog.
 - DialogEx ("< No ... Yes >"): press left = left button, press right = right button (acts immediately).
 - Settings persist when you exit the settings app (back all the way out).

KEY BEHAVIORS:
 - Apps launched via RPC PERSIST across BLE disconnects -> open in one call, press in the next.
 - app_exit only closes a plainly-launched RPC app; a FILE-launched app returns status 21
   (ERROR_APP_NOT_RUNNING) -> exit it with press back.
 - ONE BLE central at a time - if the phone holds the Flipper, calls say "device not found"; free the
   phone's Flipper app (action tools auto-retry once).
 - scan = reachability probe, NOT a routine first step.
 - On an app error (bare status), call app_get_error -> the app's own readable text. The full
   CommandStatus map is in the error strings. GPIO is RPC-reachable (gpio_read/write/set_mode);
   desktop_unlock clears the swipe-lock; reboot(OS) recovers a wedged device.
 - selftest = daemon/BLE health + ping RTT (debug "is it working?"). read_latest(folder) = pull the
   NEWEST saved file by timestamp. GUIDED capture (NFC/RFID/SubGHz can't read+save headless over BLE):
   app_launch the reader -> have the USER physically tap + Save on the device -> read_latest('/ext/nfc').
 - Screen may dim between calls; a press may just wake it - screenshot to confirm if unsure.

GATES: every press/launch/transmit is a real action (approve per call); RF = your own targets, legal
bands only. Full doc: resources/flipper-control-playbook.md.
"""


# ---- the operating manual (call this first) ---------------------------------
@mcp.tool()
def playbook() -> str:
    """The operating manual for driving this Flipper efficiently over BLE. CALL THIS FIRST in a fresh
    session before navigating the device: returns the data-first control algorithm, verified menu maps
    (main menu, Momentum settings, region-bypass path), app-entry recipes, input/widget conventions,
    and key device behaviors. Read-only, no device action."""
    return PLAYBOOK_TEXT


# ---- diagnostics ------------------------------------------------------------
@mcp.tool()
def scan() -> str:
    """Diagnostic: is the Flipper advertising over BLE right now? If not, it's most likely
    connected to your phone (only one BLE central at a time) or asleep. No device action."""
    text, _ = _run_worker(["scan"], timeout=45)
    for line in text.splitlines():
        if "FLIPPER_FOUND" in line:
            return f"✅ Flipper is advertising and reachable over BLE:\n{line}"
    return ("❌ Flipper not found advertising over BLE. It may be connected to your phone "
            "(disconnect the Flipper app there) or asleep. Then retry.")


# ---- read / observe ---------------------------------------------------------
@mcp.tool()
def device_info() -> dict:
    """Read the Flipper's device_info (60+ fields: firmware, hardware revision, radio stack,
    battery, etc.) WIRELESSLY over BLE, as a {field: value} map. Read-only."""
    text, _ = _run_worker(["info"], timeout=60)
    if "device not found" in text:
        return {"error": _not_found_hint(text)}
    d = {k.strip(): v.strip() for k, v in
         (ln.split(" = ", 1) for ln in text.splitlines() if " = " in ln)}
    return d or {"error": text or "(no output)"}


@mcp.tool()
def screenshot():
    """📷 Capture the Flipper's 128x64 screen as a PNG over BLE — the agent's eyes, wireless.
    Read-only/observational (safe to auto-allow)."""
    text, png = _run_worker(["screenshot"], want_png=True, timeout=70)
    if png:
        return Image(data=png, format="png")
    if "device not found" in text:
        return _not_found_hint(text)
    return f"screenshot failed: {text}"


# ---- control (input injection) ---------------------------------------------
@mcp.tool()
def press(button: str, kind: str = "short", then_screenshot: bool = True):
    """Inject a UI button over BLE to drive the Flipper wirelessly.
    button: up|down|left|right|ok|back. kind: short|long|press|release (default short).
    then_screenshot (default True): capture the resulting screen in the SAME BLE connection
    so you SEE what changed. Real action — Claude Desktop prompts per call (the gate)."""
    button, kind = button.lower(), kind.lower()
    if button not in BUTTONS:
        return f"bad button {button!r}; use {sorted(BUTTONS)}"
    if kind not in KINDS:
        return f"bad kind {kind!r}; use {sorted(KINDS)}"
    args = [f"{button}:{kind}"]
    if then_screenshot:
        args.append("+shot")
    text, png = _run_worker(["press", *args], want_png=then_screenshot, timeout=70)
    if then_screenshot and png:
        return Image(data=png, format="png")
    if "device not found" in text:
        return _not_found_hint(text)
    return text or "(no output)"


@mcp.tool()
def press_sequence(buttons: str, then_screenshot: bool = True):
    """Inject a SEQUENCE of buttons in ONE BLE connection — efficient multi-step navigation
    (one connect instead of one per press). buttons: space-separated btn[:kind], e.g.
    'down down ok' or 'right right ok:long'. then_screenshot (default True): capture the
    final screen in the same connection. Real actions — approve per call."""
    toks = buttons.split()
    if not toks:
        return "no buttons given"
    bad = [t for t in toks if t.partition(":")[0].lower() not in BUTTONS]
    if bad:
        return f"bad button(s) {bad}; use {sorted(BUTTONS)}"
    args = list(toks)
    if then_screenshot:
        args.append("+shot")
    text, png = _run_worker(["press", *args], want_png=then_screenshot, timeout=90)
    if then_screenshot and png:
        return Image(data=png, format="png")
    if "device not found" in text:
        return _not_found_hint(text)
    return text or "(no output)"


@mcp.tool()
def storage_list(path: str = "/ext") -> str:
    """List a directory on the Flipper's SD/internal storage over BLE (storage_list_request).
    path: e.g. '/ext' (SD root), '/ext/subghz', '/ext/nfc', '/ext/infrared', '/int'. Dirs are
    tagged [DIR], files show their byte size. Read-only."""
    text, _ = _run_worker(["list", *path.split(" ")], timeout=60)
    if "device not found" in text:
        return _not_found_hint(text)
    return text or "(no output)"


@mcp.tool()
def storage_read(path: str) -> str:
    """Read a file from the Flipper's storage over BLE (storage_read_request). Returns decoded text
    for text files (.sub / .nfc / .ir / configs, capped ~8 KB), or a binary summary + local path
    otherwise. path: e.g. '/ext/subghz/Tesla/foo.sub'. ⚠️ BLE times out on LARGE files (firmware
    #3174) — for big ones use the USB `flipper` server's storage_read. Read-only."""
    return _text_call(["read", *path.split(" ")], timeout=50)


# ---- read-only: storage metadata + diagnostics -----------------------------
@mcp.tool()
def storage_info(path: str = "/ext") -> str:
    """Free/total space on a Flipper filesystem over BLE (storage_info_request). path: '/ext' (SD)
    or '/int' (internal). Read-only."""
    return _text_call(["diskinfo", *path.split(" ")])


@mcp.tool()
def storage_stat(path: str) -> str:
    """Stat a file/dir on the Flipper over BLE (storage_stat_request) — type (FILE/DIR) + size.
    Read-only."""
    return _text_call(["stat", *path.split(" ")])


@mcp.tool()
def storage_md5(path: str) -> str:
    """MD5 hash of a file on the Flipper over BLE (storage_md5sum_request) — integrity check.
    Read-only."""
    return _text_call(["md5", *path.split(" ")], timeout=55)


@mcp.tool()
def power_info() -> dict:
    """Detailed battery/power info over BLE (system_power_info) as a {field: value} map: voltage,
    current, charge %, temperature, charging state. Read-only."""
    text, _ = _run_worker(["power"])
    if "device not found" in text:
        return {"error": _not_found_hint(text)}
    d = {k.strip(): v.strip() for k, v in
         (ln.split(" = ", 1) for ln in text.splitlines() if " = " in ln)}
    return d or {"error": text or "(no output)"}


@mcp.tool()
def ping() -> str:
    """Ping the Flipper over BLE (system_ping) — liveness + round-trip echo check. Read-only."""
    return _text_call(["ping"], timeout=30)


@mcp.tool()
def get_datetime() -> str:
    """Read the Flipper's real-time clock over BLE (system_get_datetime). Read-only."""
    return _text_call(["getdt"], timeout=30)


@mcp.tool()
def desktop_is_locked() -> str:
    """Is the Flipper's desktop PIN-locked? over BLE (desktop_is_locked). Read-only."""
    return _text_call(["locked"], timeout=30)


@mcp.tool()
def app_lock_status() -> str:
    """Is an app currently running/locking the Flipper? over BLE (app_lock_status) — a good
    pre-check before app_launch. Read-only."""
    return _text_call(["applock"], timeout=30)


# ---- gated control ----------------------------------------------------------
@mcp.tool()
def app_exit() -> str:
    """Cleanly EXIT the app currently running on the Flipper over BLE (app_exit_request) — back to
    the desktop/menu. Use before app_launch if an app is already running. Real action — approve per call."""
    return _text_call(["appexit"], timeout=30)


@mcp.tool()
def app_load_file(path: str) -> str:
    """Open a specific saved file in its app over BLE (app_load_file_request) — e.g. load a .sub into
    Sub-GHz. ⚠️ The matching app must already be running (app_launch it first). Real action."""
    return _text_call(["appload", *path.split(" ")], timeout=40)


@mcp.tool()
def app_button(args: str) -> str:
    """Press a NAMED in-app button over BLE (app_button_press + release). App-specific: in the
    universal IR / Sub-GHz / etc. apps this triggers actions (including transmit). args = the button
    name/index the running app expects. ⚠️ Advanced + app-specific; YOUR OWN TARGETS ONLY. Real action."""
    return _text_call(["appbutton", *args.split(" ")], timeout=40)


@mcp.tool()
def set_datetime(when: str = "now") -> str:
    """Set the Flipper's clock over BLE (system_set_datetime). when='now' syncs to this Mac's time,
    or pass 'YYYY-MM-DD HH:MM:SS'. Real action."""
    toks = ["now"] if when.strip() == "now" else when.replace("-", " ").replace(":", " ").split()
    return _text_call(["setdt", *toks], timeout=30)


@mcp.tool()
def find_my_flipper() -> str:
    """Make the Flipper beep + flash to locate it over BLE (system_play_audiovisual_alert) — the one
    'output' reachable over BLE RPC (LED/vibro proper are CLI-only). Real action (noise + light)."""
    return _text_call(["alert"], timeout=30)


@mcp.tool()
def storage_mkdir(path: str) -> str:
    """Create a directory on the Flipper over BLE (storage_mkdir_request). Real action."""
    return _text_call(["mkdir", *path.split(" ")], timeout=40)


@mcp.tool()
def storage_delete(path: str, recursive: bool = False) -> str:
    """⚠️ DELETE a file/dir on the Flipper over BLE (storage_delete_request). recursive=True for a
    non-empty dir. Real action — irreversible."""
    args = ["delete", *path.split(" ")]
    if recursive:
        args.append("-r")
    return _text_call(args, timeout=40)


@mcp.tool()
def storage_rename(old: str, new: str) -> str:
    """Rename/move a file or dir on the Flipper over BLE (storage_rename_request). Real action."""
    return _text_call(["rename", *old.split(" "), "->", *new.split(" ")], timeout=40)


@mcp.tool()
def storage_write(dest: str, content: str = "", local_path: str = "") -> str:
    """⚠️ WRITE/UPLOAD a file to the Flipper over BLE (chunked storage_write_request). Provide EITHER
    content (text, written as UTF-8) OR local_path (a file on this Mac to upload). dest = full Flipper
    path, e.g. '/ext/subghz/foo.sub'. Overwrites. ⚠️ BLE is slow for large files — use USB for big
    ones. Real action."""
    if local_path:
        try:
            with open(local_path, "rb") as fh:
                payload = fh.read()
        except OSError as e:
            return f"cannot read local_path: {e}"
    else:
        payload = content.encode("utf-8")
    try:
        with open(UPLOAD, "wb") as fh:
            fh.write(payload)
    except OSError as e:
        return f"cannot stage upload: {e}"
    return _text_call(["write", *dest.split(" ")], timeout=90)


@mcp.tool()
def app_launch(name: str, args: str = "", then_screenshot: bool = True):
    """Launch a Flipper app BY NAME over BLE (app_start_request) — skips UI navigation.
    name: exact app name, e.g. 'NFC', 'Sub-GHz', '125 kHz RFID', 'Infrared', 'GPIO', 'U2F',
    'iButton', 'Bad USB' (get exact names from the USB read server's app_list).
    args (optional): a launch argument — typically a FILE PATH to open directly (a .sub/.nfc/.ir);
    many apps jump straight to that file. then_screenshot (default True): capture the first screen.
    FAILS if an app is already running (app_exit first) or the name is unknown. Real action."""
    name = name.strip()
    if not name:
        return "no app name given"
    wargs = ["app", *name.split(" ")]
    if args.strip():
        wargs += ["--args", *args.split(" ")]
    if then_screenshot:
        wargs.append("+shot")
    text, png = _run_worker(wargs, want_png=then_screenshot, timeout=70)
    if "device not found" in text:
        return _not_found_hint(text)
    if then_screenshot and png:
        return Image(data=png, format="png")
    return text or "(no output)"


# ---- app-driven RF transmit (gated; no direct TX RPC exists over BLE) -------
@mcp.tool()
def transmit_subghz(path: str, then_screenshot: bool = True):
    """⚠️ TRANSMIT a saved Sub-GHz capture over BLE — the app-driven TX path (there is NO direct
    Sub-GHz TX RPC). Launches the Sub-GHz app with the file as its launch arg, which drives straight
    into the transmit flow. path: e.g. '/ext/subghz/Tesla/Tesla_US_AM650.sub'. The firmware's region
    check applies — a 'Transmission is blocked / missing region file' screen = the device's region
    lock (fix in Momentum settings, not here). ⚠️ Real RF — YOUR OWN TARGETS, LEGAL BANDS ONLY.
    Approve per call."""
    wargs = ["app", "Sub-GHz", "--args", *path.split(" ")]
    if then_screenshot:
        wargs.append("+shot")
    text, png = _run_worker(wargs, want_png=then_screenshot, timeout=70)
    if "device not found" in text:
        return _not_found_hint(text)
    if then_screenshot and png:
        return Image(data=png, format="png")
    return text or "(no output)"


@mcp.tool()
def transmit_infrared(path: str, then_screenshot: bool = True):
    """⚠️ Open a saved Infrared remote over BLE — the app-driven IR path. Launches the Infrared app
    with the .ir file as its launch arg, showing the remote's BUTTON LIST. path: e.g.
    '/ext/infrared/TV.ir'. IR is one-command-per-button, so this opens the remote; then use `press`
    (+ `screenshot`) to select a button and fire it. ⚠️ Real IR — your own devices. Approve per call."""
    wargs = ["app", "Infrared", "--args", *path.split(" ")]
    if then_screenshot:
        wargs.append("+shot")
    text, png = _run_worker(wargs, want_png=then_screenshot, timeout=70)
    if "device not found" in text:
        return _not_found_hint(text)
    if then_screenshot and png:
        return Image(data=png, format="png")
    return text or "(no output)"


# ---- app error / desktop unlock / reboot / GPIO -----------------------------
@mcp.tool()
def app_get_error() -> str:
    """Read the running app's last error as a HUMAN-READABLE string over BLE (app_get_error). Call this
    when an app_launch / app_button / transmit returns a bare status code, to get the app's own error
    text. Read-only."""
    return _text_call(["apperror"], timeout=30)


@mcp.tool()
def desktop_unlock() -> str:
    """Clear the Flipper's desktop lock over BLE (desktop_unlock_request). Note: likely clears the
    swipe-lock only, not a numeric PIN. Real action."""
    return _text_call(["unlock"], timeout=30)


@mcp.tool()
def reboot(mode: str = "OS") -> str:
    """⚠️ Reboot the Flipper over BLE (system_reboot). mode: OS (normal, default) | DFU (bootloader) |
    UPDATE. Use OS as a recovery action when the device is wedged; the BLE link drops as it restarts.
    Real action — do NOT use DFU/UPDATE unless you mean it."""
    mode = (mode or "OS").upper().strip()
    if mode not in ("OS", "DFU", "UPDATE"):
        return f"bad mode {mode!r}; use OS|DFU|UPDATE"
    return _text_call(["reboot", mode], timeout=40)


@mcp.tool()
def gpio_read(pin: str) -> str:
    """Read a GPIO pin over BLE (gpio_read_pin). pin: PC0|PC1|PC3|PB2|PB3|PA4|PA6|PA7. Read-only.
    (Corrects the earlier 'GPIO is CLI-only' note — GPIO IS in the RPC schema.)"""
    return _text_call(["gpioread", pin], timeout=30)


@mcp.tool()
def gpio_write(pin: str, value: int) -> str:
    """Set a GPIO OUTPUT pin over BLE (gpio_write_pin). pin: PC0|PC1|PC3|PB2|PB3|PA4|PA6|PA7; value 0/1.
    Set the pin to OUTPUT first via gpio_set_mode. Real action."""
    return _text_call(["gpiowrite", pin, str(1 if value else 0)], timeout=30)


@mcp.tool()
def gpio_set_mode(pin: str, mode: str = "output") -> str:
    """Set a GPIO pin mode over BLE (gpio_set_pin_mode). pin: PC0|PC1|PC3|PB2|PB3|PA4|PA6|PA7;
    mode: output|input. Real action."""
    return _text_call(["gpiomode", pin, mode], timeout=30)


@mcp.tool()
def run_badusb(path: str, content: str = ""):
    """⚠️ Run a BadUSB (DuckyScript) payload over BLE: if `content` is given it's uploaded to `path`
    (storage_write) first, then the Bad USB app is launched on that file and started (press OK).
    path e.g. '/ext/badusb/demo.txt'. ⚠️ This injects keystrokes into whatever the Flipper is
    USB-plugged into — YOUR OWN machine / authorized targets ONLY. Returns the run screen.
    Real action — approve per call."""
    path = path.strip()
    if not path:
        return "no path given"
    if content:
        wr = storage_write(path, content=content)
        if "OK" not in wr:
            return f"upload failed: {wr}"
    launch = app_launch("Bad USB", args=path, then_screenshot=False)
    if isinstance(launch, str) and "device not found" in launch:
        return launch
    if isinstance(launch, str) and "OK" not in launch:
        return f"launch failed (app name 'Bad USB'? file at {path}?): {launch}"
    return press("ok", then_screenshot=True)   # start the payload + capture the screen


@mcp.tool()
def selftest() -> str:
    """Daemon self-test / diagnostics: is the daemon up, is the BLE link connected, cached-device
    status, ping round-trip time, idle timer. Does NOT force a connect (reports current state).
    Read-only — call this to debug 'is the wireless toolkit healthy?'."""
    return _text_call(["selftest"], timeout=20)


@mcp.tool()
def read_latest(folder: str = "/ext/nfc") -> str:
    """Read the MOST-RECENTLY-SAVED file in a Flipper folder over BLE (newest by timestamp) — e.g. pull
    the NFC card / Sub-GHz capture / RFID dump you just saved on the device. folder: e.g. '/ext/nfc',
    '/ext/subghz', '/ext/lfrfid', '/ext/infrared'. Returns decoded text or a binary summary. Read-only."""
    return _text_call(["readlatest", *folder.split(" ")], timeout=70)


# ---- M5: gated, scheduled, read-only health-watch ---------------------------
@mcp.tool()
def healthwatch(action: str = "status") -> str:
    """Manage the M5 unattended HEALTH-WATCH — a scheduled, READ-ONLY job that polls the Flipper
    (battery / storage / clock / firmware / reachability) and fires a macOS notification on anomalies
    (low/aging/hot battery, full SD, clock drift, firmware change). DEFAULT-OFF; this tool is the
    on/off switch. When enabled it runs 3×/day (09:00 / 15:00 / 21:00 local) via a launchd LaunchAgent.
    action:
      'status' (default) — enabled? + the last snapshot summary (read-only, no device poll).
      'on'   — enable the 3×/day schedule (load the LaunchAgent).
      'off'  — disable it (back to default-off).
      'run'  — run ONE read-only health check right now and return the summary.
    The job is structurally incapable of transmit/write (hardcoded read-only command allowlist)."""
    sub = {"status": "status", "on": "enable", "enable": "enable", "off": "disable",
           "disable": "disable", "run": "run", "check": "run"}.get((action or "status").lower().strip())
    if not sub:
        return f"bad action {action!r}; use status | on | off | run"
    try:
        r = subprocess.run([PY, HEALTHWATCH, sub], capture_output=True, text=True, timeout=150)
        return (r.stdout + r.stderr).strip() or "(no output)"
    except Exception as e:
        return f"healthwatch {sub} failed: {e}"


# ---- annotate tools (read-only vs destructive) for the client approval UI ---
from mcp.types import ToolAnnotations as _TA  # noqa: E402

_RO = {"scan", "playbook", "device_info", "power_info", "ping", "get_datetime", "desktop_is_locked",
       "app_lock_status", "screenshot", "storage_list", "storage_read", "storage_stat",
       "storage_info", "storage_md5", "app_get_error", "gpio_read", "selftest", "read_latest"}
_DESTRUCTIVE = {"storage_delete", "transmit_subghz", "transmit_infrared", "reboot", "run_badusb"}
for _n, _t in mcp._tool_manager._tools.items():
    if _n in _RO:
        _t.annotations = _TA(readOnlyHint=True)
    elif _n in _DESTRUCTIVE:
        _t.annotations = _TA(readOnlyHint=False, destructiveHint=True)


if __name__ == "__main__":
    mcp.run()


def main():
    mcp.run()
