#!/usr/bin/env python3
"""
flipper_healthwatch.py — M5 (Stage 5) read-only, GATED, scheduled health-watch for the Flipper.

A LaunchAgent job that connects to the Flipper over BLE on a timer, snapshots battery / storage /
clock / firmware / reachability, appends a JSONL log, and fires a macOS notification when something
crosses a threshold. It talks to the SAME resident daemon the MCP server uses (Unix socket + shared
token), reusing the held BLE link.

GATING (M5 design): the schedule is DEFAULT-OFF. It only runs if explicitly enabled — normally via the
MCP `healthwatch` tool (on/off/run/status), which shells out to the subcommands here. When enabled it
runs 3×/day (09:00, 15:00, 21:00 local).

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  SAFETY — this job is STRUCTURALLY READ-ONLY.                                           ║
║  It can ONLY issue commands in READONLY_CMDS (power/diskinfo/getdt/info/ping/health).   ║
║  send() asserts membership, so it is INCAPABLE of transmit / write / press / app-launch ║
║  / reboot. This is the M5 guardrail spine: NEVER an unattended transmit or write.       ║
║  (frontier-roadmap.md Stage 5; resources/flipper-healthwatch.md.)                       ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

CLI:
  python3 flipper_healthwatch.py            # one read-only run: snapshot -> log -> notify on anomaly
  python3 flipper_healthwatch.py run        #   (same; explicit)
  python3 flipper_healthwatch.py run --quiet     # log only, no notification
  python3 flipper_healthwatch.py run --test-alert# fire a test notification (verify the alert path)
  python3 flipper_healthwatch.py run --print     # print the last snapshot, no device call
  python3 flipper_healthwatch.py install    # (re)write the LaunchAgent plist (does NOT enable it)
  python3 flipper_healthwatch.py enable     # install + load the 3×/day schedule
  python3 flipper_healthwatch.py disable    # unload the schedule (back to default-off)
  python3 flipper_healthwatch.py status     # enabled? + last snapshot summary

Exit code is always 0 (so launchd never thinks it crashed and throttles/relaunches it).
"""
import datetime as dt
import json
import os
import re
import socket
import subprocess
import sys
import time

HOME = os.environ.get("FLIPPER_AI_HOME") or os.path.expanduser("~/.flipper-ble-mcp"); os.makedirs(HOME, exist_ok=True)
APP = f"{HOME}/FlipperBLE.app"
SOCK = f"{HOME}/bled.sock"
TOKEN_FILE = f"{HOME}/bled.token"
LOG = f"{HOME}/healthwatch.log"          # JSONL: one snapshot per line
LAST = f"{HOME}/healthwatch-last.json"   # most-recent snapshot (for diffing firmware/MAC)
SELF = os.path.abspath(__file__)

LABEL = "com.flipper-ble-mcp.healthwatch"
PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{LABEL}.plist")
SCHEDULE = [(9, 0), (15, 0), (21, 0)]    # 3×/day, local time
PY = "/usr/bin/python3"                   # stdlib-only script → system python is fine + PATH-independent

# ---- thresholds (edit here) -------------------------------------------------
BATTERY_LOW_PCT = 15        # alert when discharging AND charge_level <= this
BATTERY_HEALTH_LOW = 80     # warn when battery_health <= this (cell aging)
BATTERY_TEMP_HI = 45        # warn when battery_temp °C >= this
BATTERY_TEMP_LO = 0         # warn when battery_temp °C <= this
STORAGE_FREE_LOW_PCT = 10   # warn when /ext free% <= this
RTC_DRIFT_SEC = 120         # warn when |Flipper clock - Mac clock| > this

# ---- the read-only allowlist — the structural TX/write guard ---------------
READONLY_CMDS = {"power", "diskinfo", "getdt", "info", "ping", "health", "selftest"}


# ---- daemon socket client (faithful copy of flipper_ble_server's helpers) ---
def _read_token():
    try:
        with open(TOKEN_FILE) as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def _daemon_send(cmd, args, timeout, token):
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
    """Ensure the resident daemon is up; return its auth token (cold-start the app bundle if needed)."""
    tok = _read_token()
    if tok and _daemon_send("health", [], 3, tok) is not None:
        return tok
    subprocess.Popen(["open", APP, "--args", "daemon"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(25):
        time.sleep(1)
        tok = _read_token()
        if tok and _daemon_send("health", [], 3, tok) is not None:
            return tok
    return None


def send(cmd, args=(), timeout=80, _retry=True):
    """Send ONE read-only command through the daemon. Retries once on the cold-connect race
    ('device not found' / 'connection lost'), exactly like the MCP server. Refuses anything
    not in READONLY_CMDS — the hard guarantee this job never transmits or writes."""
    assert cmd in READONLY_CMDS, f"BLOCKED non-read-only command: {cmd!r}"
    tok = _ensure_daemon()
    if not tok:
        return {"ok": False, "text": "BLE daemon unavailable (FlipperBLE.app/TCC/Bluetooth)"}
    r = _daemon_send(cmd, list(args), timeout, tok)
    if r is None:
        return {"ok": False, "text": "BLE daemon not responding"}
    t = r.get("text", "") or ""
    if _retry and ("device not found" in t or "connection lost" in t):
        time.sleep(3)
        return send(cmd, args, timeout, _retry=False)
    return r


# ---- parsers ----------------------------------------------------------------
def _kv(text):
    """Parse 'k = v' lines (device_info / power_info) into a dict."""
    return {k.strip(): v.strip() for k, v in
            (ln.split(" = ", 1) for ln in text.splitlines() if " = " in ln)}


def _to_int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def collect():
    """Build a read-only health snapshot. Leads with ping as the reachability gate."""
    snap = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "reachable": False,
            "battery": {}, "storage_ext": {}, "rtc": {}, "device": {}}

    p = send("ping", timeout=80)
    if not p.get("ok") or "PING_OK" not in (p.get("text") or ""):
        snap["unreachable_reason"] = (p.get("text") or "no ping").strip()
        return snap
    snap["reachable"] = True

    pw = send("power", timeout=40)
    if pw.get("ok"):
        d = _kv(pw.get("text", ""))
        snap["battery"] = {
            "charge_level": _to_int(d.get("charge_level")),
            "charge_state": d.get("charge_state"),
            "battery_health": _to_int(d.get("battery_health")),
            "battery_temp": _to_int(d.get("battery_temp")),
            "battery_voltage": _to_int(d.get("battery_voltage")),
            "capacity_remain": _to_int(d.get("capacity_remain")),
            "capacity_full": _to_int(d.get("capacity_full")),
        }

    di = send("diskinfo", ["/ext"], timeout=40)
    if di.get("ok"):
        m = re.search(r"free (\d+) / total (\d+) bytes \((\d+)% free\)", di.get("text", ""))
        if m:
            snap["storage_ext"] = {"free": int(m.group(1)), "total": int(m.group(2)),
                                   "pct_free": int(m.group(3))}

    gd = send("getdt", timeout=40)
    if gd.get("ok"):
        m = re.search(r"DATETIME (\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", gd.get("text", ""))
        if m:
            y, mo, da, hh, mm, ss = (int(x) for x in m.groups())
            try:
                fdt = dt.datetime(y, mo, da, hh, mm, ss)
                drift = round((dt.datetime.now() - fdt).total_seconds())
                snap["rtc"] = {"flipper": fdt.isoformat(timespec="seconds"), "drift_sec": drift}
            except ValueError:
                pass

    inf = send("info", timeout=60)
    if inf.get("ok"):
        d = _kv(inf.get("text", ""))
        snap["device"] = {
            "firmware_version": d.get("firmware_version"),
            "firmware_commit": d.get("firmware_commit"),
            "api": f"{d.get('firmware_api_major')}.{d.get('firmware_api_minor')}",
            "hardware_name": d.get("hardware_name"),
            "ble_mac": d.get("radio_ble_mac"),
        }
    return snap


# ---- evaluation -------------------------------------------------------------
def evaluate(snap, prev):
    """Return a list of (level, message). level in INFO/NOTICE/WARN/ALERT.
    Notifications fire for everything except INFO."""
    out = []
    if not snap.get("reachable"):
        out.append(("WARN", f"Flipper unreachable over BLE — off, out of range, dead battery, "
                            f"or phone holding the radio ({snap.get('unreachable_reason', '')})".strip()))
        return out

    b = snap.get("battery", {})
    lvl, state, health, temp = (b.get("charge_level"), (b.get("charge_state") or ""),
                                b.get("battery_health"), b.get("battery_temp"))
    discharging = "discharg" in state.lower()
    if lvl is not None and discharging and lvl <= BATTERY_LOW_PCT:
        out.append(("ALERT", f"Battery low: {lvl}% and discharging — charge the Flipper"))
    if health is not None and health <= BATTERY_HEALTH_LOW:
        out.append(("WARN", f"Battery health {health}% (cell aging)"))
    if temp is not None and (temp >= BATTERY_TEMP_HI or temp <= BATTERY_TEMP_LO):
        out.append(("WARN", f"Battery temperature {temp}°C out of normal range"))

    st = snap.get("storage_ext", {})
    if st.get("pct_free") is not None and st["pct_free"] <= STORAGE_FREE_LOW_PCT:
        out.append(("WARN", f"SD card only {st['pct_free']}% free — low space"))

    rtc = snap.get("rtc", {})
    if rtc.get("drift_sec") is not None and abs(rtc["drift_sec"]) > RTC_DRIFT_SEC:
        out.append(("WARN", f"Clock drifted {rtc['drift_sec']}s from this Mac — run set_datetime"))

    # diff vs previous snapshot — firmware / device-identity changes are tamper/update signals
    pdev = (prev or {}).get("device", {})
    ndev = snap.get("device", {})
    if pdev.get("firmware_commit") and ndev.get("firmware_commit") and \
            pdev["firmware_commit"] != ndev["firmware_commit"]:
        out.append(("NOTICE", f"Firmware changed: {pdev.get('firmware_version')}@{pdev['firmware_commit']} "
                              f"→ {ndev.get('firmware_version')}@{ndev['firmware_commit']}"))
    if pdev.get("ble_mac") and ndev.get("ble_mac") and pdev["ble_mac"] != ndev["ble_mac"]:
        out.append(("NOTICE", f"BLE MAC changed {pdev['ble_mac']} → {ndev['ble_mac']} (different device?)"))
    return out


# ---- outputs ----------------------------------------------------------------
def notify(alerts):
    """Fire ONE macOS notification summarizing the alerts (osascript; works from a LaunchAgent)."""
    if not alerts:
        return
    worst = "ALERT" if any(l == "ALERT" for l, _ in alerts) else "WARN"
    body = "; ".join(m for _, m in alerts).replace('"', "'").replace("\\", "")
    sub = f"{len(alerts)} item(s) — {worst}"
    script = (f'display notification "{body[:240]}" with title "Flipper health-watch" '
              f'subtitle "{sub}"' + (' sound name "Basso"' if worst == "ALERT" else ""))
    try:
        subprocess.run(["osascript", "-e", script], timeout=10,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def load_last():
    try:
        with open(LAST) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def do_run(quiet=False):
    prev = load_last()
    snap = collect()
    alerts = evaluate(snap, prev)
    snap["alerts"] = alerts
    try:
        with open(LOG, "a") as fh:
            fh.write(json.dumps(snap) + "\n")
        with open(LAST, "w") as fh:
            json.dump(snap, fh, indent=2)
    except OSError as e:
        print(f"log write failed: {e}", file=sys.stderr)
    if not quiet:
        notify(alerts)
    if not snap["reachable"]:
        print(f"{snap['ts']}  UNREACHABLE  {snap.get('unreachable_reason', '')}")
    else:
        b, st, rtc = snap["battery"], snap["storage_ext"], snap["rtc"]
        print(f"{snap['ts']}  battery {b.get('charge_level')}% ({b.get('charge_state')}) "
              f"health {b.get('battery_health')}%  SD {st.get('pct_free')}% free  "
              f"clock-drift {rtc.get('drift_sec')}s  alerts={len(alerts)}")
        for lvl, m in alerts:
            print(f"    [{lvl}] {m}")


# ---- LaunchAgent management -------------------------------------------------
def _plist_xml():
    cal = "".join(
        f"    <dict><key>Hour</key><integer>{h}</integer>"
        f"<key>Minute</key><integer>{m}</integer></dict>\n" for h, m in SCHEDULE)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>{LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{PY}</string>
    <string>{SELF}</string>
    <string>run</string>
  </array>
  <key>StartCalendarInterval</key>
  <array>
{cal}  </array>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>{HOME}/healthwatch.out</string>
  <key>StandardErrorPath</key><string>{HOME}/healthwatch.err</string>
  <key>ProcessType</key><string>Background</string>
</dict>
</plist>
"""


def do_install():
    os.makedirs(os.path.dirname(PLIST), exist_ok=True)
    with open(PLIST, "w") as fh:
        fh.write(_plist_xml())
    sched = ", ".join(f"{h:02d}:{m:02d}" for h, m in SCHEDULE)
    return f"installed plist {PLIST}\n  schedule (when enabled): {sched} local, 3×/day\n  (NOT enabled — `enable` to turn on)"


def _is_enabled():
    r = subprocess.run(["launchctl", "print", f"gui/{os.getuid()}/{LABEL}"],
                       capture_output=True, text=True)
    return r.returncode == 0


def do_enable():
    do_install()
    uid = os.getuid()
    b = subprocess.run(["launchctl", "bootstrap", f"gui/{uid}", PLIST], capture_output=True, text=True)
    msg = (b.stderr + b.stdout).lower()
    if b.returncode != 0 and "already" not in msg:
        subprocess.run(["launchctl", "load", "-w", PLIST], capture_output=True, text=True)
    return do_status()


def do_disable():
    uid = os.getuid()
    bo = subprocess.run(["launchctl", "bootout", f"gui/{uid}/{LABEL}"], capture_output=True, text=True)
    msg = (bo.stderr + bo.stdout).lower()
    if bo.returncode != 0 and "no such" not in msg and "could not find" not in msg:
        subprocess.run(["launchctl", "unload", "-w", PLIST], capture_output=True, text=True)
    return do_status()


def do_status():
    enabled = _is_enabled()
    installed = os.path.exists(PLIST)
    sched = ", ".join(f"{h:02d}:{m:02d}" for h, m in SCHEDULE)
    lines = [
        f"health-watch: {'ENABLED — runs ' + sched + ' local, 3×/day' if enabled else 'DISABLED (default-off)'}",
        f"plist: {'installed' if installed else 'NOT installed'} at {PLIST}",
        "scope: READ-ONLY (battery/storage/clock/firmware/reachability); never transmits or writes",
    ]
    last = load_last()
    if last:
        if last.get("reachable"):
            b, st, rtc = last.get("battery", {}), last.get("storage_ext", {}), last.get("rtc", {})
            lines.append(f"last run {last.get('ts')}: battery {b.get('charge_level')}% "
                         f"({b.get('charge_state')}), SD {st.get('pct_free')}% free, "
                         f"clock-drift {rtc.get('drift_sec')}s, alerts={len(last.get('alerts', []))}")
        else:
            lines.append(f"last run {last.get('ts')}: UNREACHABLE — {last.get('unreachable_reason', '')}")
        for lvl, m in last.get("alerts", []):
            lines.append(f"    [{lvl}] {m}")
    else:
        lines.append("no snapshot yet (run `run` to take one)")
    return "\n".join(lines)


def main():
    argv = sys.argv[1:]
    flags = {a for a in argv if a.startswith("-")}
    pos = [a for a in argv if not a.startswith("-")]
    cmd = pos[0] if pos else "run"
    if cmd == "install":
        print(do_install())
    elif cmd == "enable":
        print(do_enable())
    elif cmd == "disable":
        print(do_disable())
    elif cmd == "status":
        print(do_status())
    elif cmd == "run":
        if "--print" in flags:
            print(json.dumps(load_last(), indent=2) if load_last() else "(no snapshot yet)")
        elif "--test-alert" in flags:
            notify([("ALERT", "test notification — the health-watch alert path works")])
            print("test notification fired")
        else:
            do_run(quiet="--quiet" in flags)
    else:
        print(f"unknown command {cmd!r}; use run|install|enable|disable|status")


if __name__ == "__main__":
    main()
