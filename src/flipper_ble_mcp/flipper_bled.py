#!/usr/bin/env python3
"""
flipper_bled.py — resident BLE daemon for the Flipper (Phase 2 keystone).

Holds ONE BleakClient open across many commands and serves a Unix socket, so MCP
tool calls become near-instant (no per-call scan+connect+teardown ~6-10s). Runs
INSIDE the signed FlipperBLE.app (its own TCC principal) via `open FlipperBLE.app
--args daemon`. Reuses ble_worker's verified builders/parsers (single source of truth);
only the held-connection orchestration is new.

Protocol: newline-delimited JSON over AF_UNIX at ~/flipper-ai/bled.sock.
  request : {"cmd": "...", "args": [...]}\n
  response: {"ok": bool, "text": "...", "png_b64": "...", ...}\n

Connection: lazy-connect on first BLE command; idle-disconnect after IDLE_SEC to free
the radio for the phone; auto-reconnect on the next command.
"""

import asyncio
import base64
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ble_worker as w  # noqa: E402  (now importable: dispatch is under __main__)
from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2  # noqa: E402

_HOME = os.environ.get("FLIPPER_AI_HOME") or os.path.expanduser("~/.flipper-ble-mcp")
os.makedirs(_HOME, exist_ok=True)
SOCK = os.path.join(_HOME, "bled.sock")
TOKEN_FILE = os.path.join(_HOME, "bled.token")
_TOKEN = None
PNG = os.path.join(_HOME, "ble_screen.png")
UPLOAD = os.path.join(_HOME, "ble_upload.bin")
FILEBIN = os.path.join(_HOME, "ble_file.bin")
IDLE_SEC = 180

_client = None
_buf = bytearray()
_lock = threading.Lock()
_conn_lock = asyncio.Lock()
_last_activity = [0.0]
_dev = [None]  # cached BLEDevice — reconnect without a fresh scan
_lockf = None  # singleton flock handle (held for daemon lifetime)
_last_shot = {"png": b"", "ts": 0.0}  # serve a screenshot <0.4s old without re-grabbing


def log(*a):
    print("[bled]", *a, flush=True)


# ---- connection lifecycle ---------------------------------------------------
async def _ensure():
    """Ensure a live BLE connection (lazy + reconnect). Reuses the cached BLEDevice to skip a fresh
    scan on reconnect (its .details CBPeripheral stays valid for the daemon's lifetime). True on success."""
    global _client
    if _client is not None and _client.is_connected:
        return True
    from bleak import BleakClient

    async with _conn_lock:
        if _client is not None and _client.is_connected:
            return True

        async def _try(dev):
            c = BleakClient(dev)
            await c.connect()
            with _lock:
                _buf.clear()

            def on_rx(_h, d):
                with _lock:
                    _buf.extend(bytes(d))

            await c.start_notify(w.RX, on_rx, cb={"notification_discriminator": lambda d: True})
            return c

        if _dev[0] is not None:  # fast path: reconnect to cached device, no scan
            try:
                _client = await _try(_dev[0])
                log("reconnected (cached dev)")
                return True
            except Exception as e:
                log("cached reconnect failed, rescanning:", repr(e))
                _dev[0] = None
        dev = await w._find_device()  # slow path: scan + connect
        if dev is None:
            return False
        try:
            _client = await _try(dev)
        except Exception as e:
            log("connect failed:", repr(e))
            return False
        _dev[0] = dev
        log("connected", dev.address)
        return True


async def _disconnect():
    global _client
    async with _conn_lock:
        if _client is not None:
            try:
                await _client.disconnect()
            except Exception:
                pass
            _client = None
            log("disconnected (idle)")


async def _idle_watch():
    while True:
        await asyncio.sleep(15)
        if _client is not None and _last_activity[0] and (time.monotonic() - _last_activity[0]) > IDLE_SEC:
            async with _cmd_lock:  # never disconnect mid-command
                if _client is not None and (time.monotonic() - _last_activity[0]) > IDLE_SEC:
                    await _disconnect()


# ---- held-connection transaction core --------------------------------------
_cmd_lock = asyncio.Lock()  # serialize commands so they never interleave on the shared buffer
_CUR_CID = [0]  # command_id of the in-flight command (for response demux)
_CID_SEQ = [1]


def _next_cid():
    _CID_SEQ[0] = (_CID_SEQ[0] % 120) + 2  # cycle 2..121, never 0/1
    _CUR_CID[0] = _CID_SEQ[0]
    return _CID_SEQ[0]


def _patch_cid(req, cid):
    """Rewrite a framed PB_Main's command_id (built as 1) to cid in place. cid in 2..121 → 1 byte,
    so length is preserved."""
    _ln, off = w._uvarint(req, 0)  # off = start of body
    b = bytearray(req)
    if off < len(b) and b[off] == 0x08:  # command_id field tag, 1-byte value
        b[off + 1] = cid
    return bytes(b)


async def _txn(req, parse, timeout=10.0):
    """Tag req with a fresh command_id, clear buffer, send, then poll parse(snapshot) until it
    returns non-None or timeout. _mains() filters the buffer to this command's frames only."""
    cid = _next_cid()
    with _lock:
        _buf.clear()
    if req is not None:
        await _client.write_gatt_char(w.TX, _patch_cid(req, cid), response=False)
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        with _lock:
            snap = bytes(_buf)
        r = parse(snap)
        if r is not None:
            return r
        await asyncio.sleep(0.02)
    with _lock:
        snap = bytes(_buf)
    return parse(snap, final=True)


def _mains(snap):
    """Split a raw RX snapshot into fully-received PB_Main messages (idempotent), DEMUXING out
    continuous screen-stream frames (gui_screen_frame) so they never corrupt command parsing."""
    out, i = [], 0
    while i < len(snap):
        ln, off = w._uvarint(snap, i)
        if ln is None or len(snap) < off + ln:
            break
        m = flipper_pb2.Main()
        try:
            m.ParseFromString(bytes(snap[off : off + ln]))
        except Exception:
            break
        i = off + ln
        if m.HasField("gui_screen_frame"):
            continue  # route screen frames away from command parsing
        if _CUR_CID[0] and m.command_id != _CUR_CID[0]:
            continue  # demux: keep ONLY this command's responses (drops command_id=0 pushes + stragglers)
        out.append(m)
    return out


def _stream_done(mains):
    return bool(mains) and not mains[-1].has_next


# ---- command handlers (return dict) -----------------------------------------
async def h_health(args):
    return {"ok": True, "connected": bool(_client and _client.is_connected)}


async def h_info(args):
    fields = {}

    def parse(snap, final=False):
        ms = _mains(snap)
        for m in ms:
            r = m.system_device_info_response
            if r.key:
                fields[r.key] = r.value
        if _stream_done(ms) or final:
            return fields
        return None

    await _txn(w._mk(lambda m: m.system_device_info_request.SetInParent()), parse, 12)
    return {
        "ok": True,
        "text": f"DEVICE_INFO: {len(fields)} fields\n" + "\n".join(f"  {k} = {v}" for k, v in fields.items()),
    }


async def h_power(args):
    fields = {}

    def parse(snap, final=False):
        ms = _mains(snap)
        for m in ms:
            r = m.system_power_info_response
            if r.key:
                fields[r.key] = r.value
        if _stream_done(ms) or final:
            return fields
        return None

    await _txn(w._mk(lambda m: m.system_power_info_request.SetInParent()), parse, 10)
    return {"ok": True, "text": "\n".join(f"{k} = {v}" for k, v in fields.items())}


def _first(snap, extract):
    ms = _mains(snap)
    for m in ms:
        r = extract(m)
        if r is not None:
            return r
    return None


async def h_ping(args):
    payload = b"flipperping"
    r = await _txn(
        w._mk(lambda m: setattr(m.system_ping_request, "data", payload)),
        lambda s, final=False: _first(
            s, lambda m: bytes(m.system_ping_response.data) if m.HasField("system_ping_response") else None
        ),
    )
    return {"ok": True, "text": "PING_OK" if r == payload else f"PING {r!r}"}


async def h_getdt(args):
    def ext(m):
        if not m.HasField("system_get_datetime_response"):
            return None
        d = m.system_get_datetime_response.datetime
        return (d.year, d.month, d.day, d.hour, d.minute, d.second)

    r = await _txn(
        w._mk(lambda m: m.system_get_datetime_request.SetInParent()), lambda s, final=False: _first(s, ext)
    )
    if r:
        return {
            "ok": True,
            "text": f"DATETIME {r[0]:04d}-{r[1]:02d}-{r[2]:02d} {r[3]:02d}:{r[4]:02d}:{r[5]:02d}",
        }
    return {"ok": False, "text": "(no datetime)"}


async def _status_cmd(req, label, timeout=8):
    def parse(snap, final=False):
        ms = _mains(snap)
        return ms[0].command_status if ms else (-1 if final else None)

    s = await _txn(req, parse, timeout)
    s = 0 if s is None else s
    return {"ok": s == 0, "text": f"{label} {w._status_str(s)}", "status": s}


async def h_setdt(args):
    import datetime as _dt

    n = _dt.datetime.now() if (not args or args[0] == "now") else None
    if n:
        y, mo, d, hh, mm, ss = n.year, n.month, n.day, n.hour, n.minute, n.second
    else:
        y, mo, d, hh, mm, ss = (int(x) for x in args[:6])

    def build():
        m = flipper_pb2.Main()
        m.command_id = 1
        dt = m.system_set_datetime_request.datetime
        dt.year, dt.month, dt.day = y, mo, d
        dt.hour, dt.minute, dt.second = hh, mm, ss
        dt.weekday = _dt.date(y, mo, d).weekday() + 1
        return w._frame(m.SerializeToString())

    return await _status_cmd(build(), f"SETDATETIME {y:04d}-{mo:02d}-{d:02d}")


async def h_locked(args):
    s = (await _status_cmd(w._mk(lambda m: m.desktop_is_locked_request.SetInParent()), "DESKTOP"))["status"]
    return {"ok": True, "text": f"DESKTOP {'LOCKED' if s == 0 else 'UNLOCKED'} (status={s})"}


async def h_applock(args):
    def ext(m):
        return (
            ("locked" if m.app_lock_status_response.locked else "free")
            if m.HasField("app_lock_status_response")
            else None
        )

    r = await _txn(
        w._mk(lambda m: m.app_lock_status_request.SetInParent()), lambda s, final=False: _first(s, ext)
    )
    return {"ok": True, "text": f"APP_LOCK {'an app is RUNNING' if r == 'locked' else 'free (desktop/menu)'}"}


async def h_apperror(args):
    def ext(m):
        if not m.HasField("app_get_error_response"):
            return None
        return (m.app_get_error_response.code, m.app_get_error_response.text)

    r = await _txn(
        w._mk(lambda m: m.app_get_error_request.SetInParent()), lambda s, final=False: _first(s, ext)
    )
    code, text = r if r else (0, "")
    return {"ok": True, "text": f"APP_ERROR code={code} text={text!r}"}


async def h_unlock(args):
    return await _status_cmd(w._mk(lambda m: m.desktop_unlock_request.SetInParent()), "DESKTOP_UNLOCK")


async def h_alert(args):
    return await _status_cmd(w._mk(lambda m: m.system_play_audiovisual_alert_request.SetInParent()), "ALERT")


async def h_appexit(args):
    return await _status_cmd(w._mk(lambda m: m.app_exit_request.SetInParent()), "APP_EXIT")


async def h_appload(args):
    path = " ".join(args).strip()
    if not path:
        return {"ok": False, "text": "no path"}
    return await _status_cmd(
        w._mk(lambda m: setattr(m.app_load_file_request, "path", path)), f"APP_LOAD {path}", 10
    )


async def h_mkdir(args):
    path = " ".join(args).strip()
    return await _status_cmd(
        w._mk(lambda m: setattr(m.storage_mkdir_request, "path", path)), f"MKDIR {path}", 10
    )


async def h_delete(args):
    rec = "-r" in args
    path = " ".join(t for t in args if t != "-r").strip()

    def setter(m):
        m.storage_delete_request.path = path
        m.storage_delete_request.recursive = rec

    return await _status_cmd(w._mk(setter), f"DELETE {path} (recursive={rec})", 12)


async def h_rename(args):
    if "->" not in args:
        return {"ok": False, "text": "need: <old> -> <new>"}
    i = args.index("->")
    old, new = " ".join(args[:i]).strip(), " ".join(args[i + 1 :]).strip()

    def setter(m):
        m.storage_rename_request.old_path = old
        m.storage_rename_request.new_path = new

    return await _status_cmd(w._mk(setter), f"RENAME {old} -> {new}", 12)


async def h_gpioread(args):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import gpio_pb2

    pin = args[0].upper() if args else ""
    if pin not in gpio_pb2.GpioPin.keys():
        return {"ok": False, "text": f"bad pin {pin!r}"}
    pv = gpio_pb2.GpioPin.Value(pin)

    def parse(snap, final=False):
        ms = _mains(snap)
        if not ms:
            return None
        m = ms[0]
        return (m.command_status, m.gpio_read_pin_response.value)

    r = await _txn(w._mk(lambda m: setattr(m.gpio_read_pin, "pin", pv)), parse, 8)
    if r is None:
        return {"ok": False, "text": "GPIO_READ timeout"}
    st, val = r
    return {
        "ok": st == 0,
        "text": f"GPIO_READ {pin} = {val}" if st == 0 else f"GPIO_READ {pin}: {w._status_str(st)}",
    }


async def h_gpiowrite(args):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import gpio_pb2

    if len(args) < 2:
        return {"ok": False, "text": "usage: gpiowrite <PIN> <0|1>"}
    pin = args[0].upper()
    val = 1 if str(args[1]).strip().lower() in ("1", "high", "on", "true") else 0
    if pin not in gpio_pb2.GpioPin.keys():
        return {"ok": False, "text": f"bad pin {pin!r}"}

    def setter(m):
        m.gpio_write_pin.pin = gpio_pb2.GpioPin.Value(pin)
        m.gpio_write_pin.value = val

    return await _status_cmd(w._mk(setter), f"GPIO_WRITE {pin}={val}")


async def h_gpiomode(args):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import gpio_pb2

    if len(args) < 2:
        return {"ok": False, "text": "usage: gpiomode <PIN> <output|input>"}
    pin, mode = args[0].upper(), args[1].upper()
    if pin not in gpio_pb2.GpioPin.keys() or mode not in gpio_pb2.GpioPinMode.keys():
        return {"ok": False, "text": "bad pin/mode"}

    def setter(m):
        m.gpio_set_pin_mode.pin = gpio_pb2.GpioPin.Value(pin)
        m.gpio_set_pin_mode.mode = gpio_pb2.GpioPinMode.Value(mode)

    return await _status_cmd(w._mk(setter), f"GPIO_MODE {pin}={mode}")


async def h_stat(args):
    path = " ".join(args).strip()

    def parse(snap, final=False):
        ms = _mains(snap)
        if not ms:
            return None
        m = ms[0]
        return (m.command_status, m.storage_stat_response.file.type, m.storage_stat_response.file.size)

    r = await _txn(w._mk(lambda m: setattr(m.storage_stat_request, "path", path)), parse, 10)
    if not r:
        return {"ok": False, "text": "STAT timeout"}
    st, typ, size = r
    if st:
        return {"ok": False, "text": f"STAT {path}: {w._status_str(st)}"}
    return {"ok": True, "text": f"STAT {path}: {'DIR' if typ == 1 else 'FILE'} {size} bytes"}


async def h_diskinfo(args):
    path = " ".join(args).strip() or "/ext"

    def parse(snap, final=False):
        ms = _mains(snap)
        if not ms:
            return None
        m = ms[0]
        return (m.command_status, m.storage_info_response.total_space, m.storage_info_response.free_space)

    r = await _txn(w._mk(lambda m: setattr(m.storage_info_request, "path", path)), parse, 10)
    if not r:
        return {"ok": False, "text": "INFO timeout"}
    st, total, free = r
    if st:
        return {"ok": False, "text": f"STORAGE_INFO {path}: {w._status_str(st)}"}
    pct = (free * 100 // total) if total else 0
    return {"ok": True, "text": f"STORAGE_INFO {path}: free {free} / total {total} bytes ({pct}% free)"}


async def h_md5(args):
    path = " ".join(args).strip()

    def parse(snap, final=False):
        ms = _mains(snap)
        if not ms:
            return None
        return (ms[0].command_status, ms[0].storage_md5sum_response.md5sum)

    r = await _txn(w._mk(lambda m: setattr(m.storage_md5sum_request, "path", path)), parse, 15)
    if not r:
        return {"ok": False, "text": "MD5 timeout"}
    st, md5 = r
    return {"ok": st == 0, "text": f"MD5 {path}: {md5}" if st == 0 else f"MD5 {path}: {w._status_str(st)}"}


async def h_list(args):
    path = " ".join(args).strip() or "/ext"
    files, err = [], [0]

    def parse(snap, final=False):
        ms = _mains(snap)
        files.clear()
        for m in ms:
            if m.command_status:
                err[0] = m.command_status
            for f in m.storage_list_response.file:
                files.append((f.type, f.name, f.size))
        if _stream_done(ms) or final:
            return True
        return None

    await _txn(w._mk(lambda m: setattr(m.storage_list_request, "path", path)), parse, 20)
    if err[0]:
        return {"ok": False, "text": f"LIST {path}: {w._status_str(err[0])}"}
    lines = [f"LIST {path}: {len(files)} entries"]
    for t, name, size in sorted(files, key=lambda x: (x[0] == 0, x[1].lower())):
        lines.append(f"  [DIR]  {name}" if t == 1 else f"  {size:>9}  {name}")
    return {"ok": True, "text": "\n".join(lines)}


async def h_read(args):
    path = " ".join(args).strip()
    data, err = bytearray(), [0]

    def parse(snap, final=False):
        ms = _mains(snap)
        data.clear()
        for m in ms:
            if m.command_status:
                err[0] = m.command_status
            data.extend(m.storage_read_response.file.data)
        if _stream_done(ms) or final:
            return True
        return None

    await _txn(w._mk(lambda m: setattr(m.storage_read_request, "path", path)), parse, 30)
    if err[0]:
        return {"ok": False, "text": f"FILE_ERR {path}: {w._status_str(err[0])}"}
    raw = bytes(data)
    with open(FILEBIN, "wb") as fh:
        fh.write(raw)
    try:
        s = raw.decode("utf-8")
        if len(s) > 8000:
            return {
                "ok": True,
                "text": f"[{path} — {len(raw)} bytes; first 8000]\n\n{s[:8000]}\n…[truncated]",
            }
        return {"ok": True, "text": f"[{path} — {len(raw)} bytes]\n\n{s}"}
    except UnicodeDecodeError:
        return {
            "ok": True,
            "text": f"[{path} — {len(raw)} bytes, BINARY] saved to {FILEBIN}\nhex: {raw[:96].hex()}",
        }


def _fb_png(snap):
    idx = snap.find(w.FB_MARK)
    if idx != -1 and len(snap) >= idx + 3 + 1024:
        fb = snap[idx + 3 : idx + 3 + 1024]
        w._fb_to_png(fb, PNG)
        return True
    return None


async def _quiesce(quiet=0.4, cap=4.0):
    """Wait until the RX buffer stops growing (screen stream actually stopped) before returning,
    so the next command runs on a quiet channel."""
    last_len, stable = -1, time.monotonic()
    end = time.monotonic() + cap
    while time.monotonic() < end:
        with _lock:
            n = len(_buf)
        if n == last_len:
            if time.monotonic() - stable >= quiet:
                return
        else:
            last_len, stable = n, time.monotonic()
        await asyncio.sleep(0.05)


async def _grab_screen(timeout=12):
    r = await _txn(w.SCREEN_REQ, lambda s, final=False: _fb_png(s), timeout)
    try:  # stop the continuous stream, then wait for it to actually stop
        await _client.write_gatt_char(
            w.TX, w._mk(lambda m: m.gui_stop_screen_stream_request.SetInParent()), response=False
        )
    except Exception:
        pass
    await _quiesce()
    if r:
        try:
            with open(PNG, "rb") as fh:
                _last_shot["png"] = fh.read()
            _last_shot["ts"] = time.monotonic()
        except Exception:
            pass
    return r


async def h_screenshot(args):
    if _last_shot["png"] and (time.monotonic() - _last_shot["ts"]) < 0.4:
        return {
            "ok": True,
            "png_b64": base64.b64encode(_last_shot["png"]).decode(),
            "text": "screenshot (cached <0.4s)",
        }
    if await _grab_screen():
        return {"ok": True, "png_b64": base64.b64encode(_last_shot["png"]).decode(), "text": "screenshot ok"}
    return {"ok": False, "text": "no framebuffer captured"}


async def h_press(args):
    shot = "+shot" in args
    toks = [t for t in args if t != "+shot"]
    BTN = {"up", "down", "left", "right", "ok", "back"}
    plan = []
    for t in toks:
        btn, _, kind = t.partition(":")
        btn, kind = btn.lower(), (kind or "short").lower()
        if btn not in BTN:
            return {"ok": False, "text": f"bad button {btn!r}"}
        if kind == "short":
            plan += [(btn, "PRESS"), (btn, "SHORT"), (btn, "RELEASE")]
        elif kind == "long":
            plan += [(btn, "PRESS"), (btn, "LONG"), (btn, "RELEASE")]
        elif kind == "press":
            plan += [(btn, "PRESS")]
        elif kind == "release":
            plan += [(btn, "RELEASE")]
        else:
            return {"ok": False, "text": f"bad kind {kind!r}"}
    if not plan:
        return {"ok": False, "text": "no buttons"}
    for fr in w._input_frames(plan):
        await _client.write_gatt_char(w.TX, fr, response=False)
        await asyncio.sleep(0.04)
    await asyncio.sleep(0.2)
    if shot and await _grab_screen():
        with open(PNG, "rb") as fh:
            return {
                "ok": True,
                "png_b64": base64.b64encode(fh.read()).decode(),
                "text": f"PRESS_OK {' '.join(toks)}",
            }
    return {"ok": True, "text": f"PRESS_OK {' '.join(toks)}"}


async def h_app(args):
    shot = "+shot" in args
    toks = [t for t in args if t != "+shot"]
    if "--args" in toks:
        i = toks.index("--args")
        name, appargs = " ".join(toks[:i]).strip(), " ".join(toks[i + 1 :]).strip()
    else:
        name, appargs = " ".join(toks).strip(), ""
    if not name:
        return {"ok": False, "text": "no app name"}

    def build():
        m = flipper_pb2.Main()
        m.command_id = 1
        m.app_start_request.name = name
        if appargs:
            m.app_start_request.args = appargs
        return w._frame(m.SerializeToString())

    def parse(snap, final=False):
        ms = _mains(snap)
        return ms[0].command_status if ms else (-1 if final else None)

    s = await _txn(build(), parse, 10)
    s = 0 if s is None else s
    if shot:
        await asyncio.sleep(0.6)
        if await _grab_screen():
            with open(PNG, "rb") as fh:
                return {
                    "ok": s == 0,
                    "png_b64": base64.b64encode(fh.read()).decode(),
                    "text": f"APP_LAUNCH {name} {w._status_str(s)}",
                }
    return {"ok": s == 0, "text": f"APP_LAUNCH {name} {w._status_str(s)}"}


async def h_appbutton(args):
    name = " ".join(args).strip()
    cid = _next_cid()
    press = _patch_cid(w._mk(lambda m: setattr(m.app_button_press_request, "args", name)), cid)
    release = _patch_cid(w._mk(lambda m: m.app_button_release_request.SetInParent()), cid)
    with _lock:
        _buf.clear()
    await _client.write_gatt_char(w.TX, press, response=False)
    await asyncio.sleep(0.15)
    await _client.write_gatt_char(w.TX, release, response=False)
    await asyncio.sleep(0.3)
    with _lock:
        ms = _mains(bytes(_buf))
    codes = [m.command_status for m in ms if not m.has_next]
    return {"ok": True, "text": f"APP_BUTTON {name!r}: statuses={codes}"}


async def h_write(args):
    path = " ".join(args).strip()
    try:
        with open(UPLOAD, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        return {"ok": False, "text": "no upload payload"}
    CHUNK = 2048  # fit small files (scripts/configs/captures) in ONE storage_write_request — the
    # multi-message continuation path is rejected by this firmware (empty-path chunk
    # → ERROR_STORAGE_INVALID_NAME); large files should go over USB anyway.
    chunks = [data[i : i + CHUNK] for i in range(0, len(data), CHUNK)] or [b""]
    gchunk = max(20, (getattr(_client, "mtu_size", 0) or 23) - 3)
    st = [None]
    cid = _next_cid()
    # storage_write streams request-side; capture the single final response.
    with _lock:
        _buf.clear()
    for i, ch in enumerate(chunks):
        last = i == len(chunks) - 1
        m = flipper_pb2.Main()
        m.command_id = cid
        m.has_next = not last
        if i == 0:
            m.storage_write_request.path = path
        m.storage_write_request.file.data = ch
        fr = w._frame(m.SerializeToString())
        for j in range(0, len(fr), gchunk):
            await _client.write_gatt_char(
                w.TX, fr[j : j + gchunk], response=True
            )  # reliable: no dropped packets mid-frame
        await asyncio.sleep(0.02)
    end = time.monotonic() + 45
    while time.monotonic() < end:
        with _lock:
            ms = _mains(bytes(_buf))
        if ms and not ms[-1].has_next:
            st[0] = ms[-1].command_status
            break
        await asyncio.sleep(0.03)
    s = 0 if st[0] is None else st[0]
    return {"ok": s == 0, "text": f"WRITE {path} ({len(data)} bytes): {w._status_str(s)}"}


async def h_reboot(args):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import system_pb2

    mode = args[0].upper() if args else "OS"
    if mode not in ("OS", "DFU", "UPDATE"):
        return {"ok": False, "text": f"bad mode {mode!r}"}
    mv = system_pb2.RebootRequest.RebootMode.Value(mode)

    def build():
        m = flipper_pb2.Main()
        m.command_id = 1
        m.system_reboot_request.mode = mv
        return w._frame(m.SerializeToString())

    await _client.write_gatt_char(w.TX, build(), response=False)
    await asyncio.sleep(0.4)
    return {"ok": True, "text": f"REBOOT sent (mode={mode}) - device restarting"}


async def h_selftest(args):
    """Daemon diagnostics: state + ping RTT. Does NOT force a connect (reports current state)."""
    import os as _os

    connected = bool(_client and _client.is_connected)
    rtt = None
    if connected:
        t0 = time.monotonic()
        r = await _txn(
            w._mk(lambda m: setattr(m.system_ping_request, "data", b"selftest")),
            lambda s, final=False: _first(s, lambda m: True if m.HasField("system_ping_response") else None),
            6,
        )
        if r:
            rtt = round((time.monotonic() - t0) * 1000)
    idle = round(time.monotonic() - _last_activity[0], 1) if _last_activity[0] else None
    lines = [
        f"daemon pid {_os.getpid()}, socket {SOCK}",
        f"BLE: {'CONNECTED' if connected else 'idle / not connected (connects lazily on next device command)'}",
        f"cached device (scan-free reconnect): {'yes' if _dev[0] is not None else 'no'}",
        (
            f"ping RTT: {rtt} ms"
            if rtt is not None
            else ("ping: connected but no echo" if connected else "ping: skipped (not connected)")
        ),
        (
            f"last activity: {idle}s ago (auto-disconnect at {IDLE_SEC}s idle)"
            if idle is not None
            else "no activity yet this session"
        ),
    ]
    return {"ok": True, "text": "SELFTEST\n  " + "\n  ".join(lines)}


async def h_read_latest(args):
    """List <folder>, find the newest FILE by storage_timestamp, and read it. For pulling a capture
    you just saved on the device (NFC/Sub-GHz/RFID/etc.)."""
    folder = " ".join(args).strip() or "/ext/nfc"
    files = []

    def lp(snap, final=False):
        ms = _mains(snap)
        files.clear()
        for m in ms:
            for f in m.storage_list_response.file:
                if f.type == 0:
                    files.append(f.name)
        return True if (ms and not ms[-1].has_next) or final else None

    await _txn(w._mk(lambda m: setattr(m.storage_list_request, "path", folder)), lp, 15)
    if not files:
        return {"ok": False, "text": f"no files found in {folder}"}
    newest, newest_ts = files[-1], -1
    for name in files[:80]:

        def tp(snap, final=False):
            ms = _mains(snap)
            return ms[0].storage_timestamp_response.timestamp if ms else (-1 if final else None)

        ts = await _txn(
            w._mk(lambda m, _p=f"{folder}/{name}": setattr(m.storage_timestamp_request, "path", _p)), tp, 8
        )
        if isinstance(ts, int) and ts > newest_ts:
            newest_ts, newest = ts, name
    path = f"{folder}/{newest}"
    data, err = bytearray(), [0]

    def rp(snap, final=False):
        ms = _mains(snap)
        data.clear()
        for m in ms:
            if m.command_status:
                err[0] = m.command_status
            data.extend(m.storage_read_response.file.data)
        return True if (ms and not ms[-1].has_next) or final else None

    await _txn(w._mk(lambda m, _p=path: setattr(m.storage_read_request, "path", _p)), rp, 30)
    if err[0]:
        return {"ok": False, "text": f"read failed for {path}: {w._status_str(err[0])}"}
    raw = bytes(data)
    hdr = f"newest in {folder}: {newest} ({len(raw)} bytes)"
    try:
        s = raw.decode("utf-8")
        body = s if len(s) <= 8000 else s[:8000] + "\n…[truncated]"
        return {"ok": True, "text": f"[{hdr}]\n\n{body}"}
    except UnicodeDecodeError:
        return {"ok": True, "text": f"[{hdr}, BINARY] hex: {raw[:96].hex()}"}


COMMANDS = {
    "health": h_health,
    "selftest": h_selftest,
    "readlatest": h_read_latest,
    "info": h_info,
    "power": h_power,
    "ping": h_ping,
    "getdt": h_getdt,
    "setdt": h_setdt,
    "locked": h_locked,
    "applock": h_applock,
    "apperror": h_apperror,
    "unlock": h_unlock,
    "alert": h_alert,
    "appexit": h_appexit,
    "appload": h_appload,
    "mkdir": h_mkdir,
    "delete": h_delete,
    "rename": h_rename,
    "gpioread": h_gpioread,
    "gpiowrite": h_gpiowrite,
    "gpiomode": h_gpiomode,
    "stat": h_stat,
    "diskinfo": h_diskinfo,
    "md5": h_md5,
    "list": h_list,
    "read": h_read,
    "screenshot": h_screenshot,
    "press": h_press,
    "app": h_app,
    "appbutton": h_appbutton,
    "write": h_write,
    "reboot": h_reboot,
}
# commands that need a live BLE link (everything except these state-only ones)
_NEEDS_BLE = set(COMMANDS) - {"health", "selftest"}


async def _handle(req):
    global _client
    cmd = req.get("cmd", "")
    args = req.get("args", []) or []
    if req.get("token") != _TOKEN:
        return {"ok": False, "text": "unauthorized (bad or missing token)"}
    h = COMMANDS.get(cmd)
    if h is None:
        return {"ok": False, "text": f"unknown cmd {cmd!r}"}
    async with _cmd_lock:  # serialize: one command at a time on the shared buffer/connection
        if cmd in _NEEDS_BLE:
            _last_activity[0] = time.monotonic()
            if not await _ensure():
                return {"ok": False, "text": "device not found (BLE) - phone holding it, or asleep?"}
        try:
            out = await h(args)
        except Exception as e:
            import traceback

            log("handler error", cmd, repr(e), traceback.format_exc())
            if not (_client and _client.is_connected):
                _client = None  # force a fresh (re)connect next call
                return {"ok": False, "text": "connection lost - retry"}
            return {"ok": False, "text": f"error: {type(e).__name__}: {e}"}
        _last_activity[0] = time.monotonic()
        return out


async def _serve_client(reader, writer):
    try:
        line = await reader.readline()
        if not line:
            return
        req = json.loads(line.decode())
        out = await _handle(req)
        writer.write((json.dumps(out) + "\n").encode())
        await writer.drain()
    except Exception as e:
        try:
            writer.write((json.dumps({"ok": False, "text": f"daemon error: {e}"}) + "\n").encode())
            await writer.drain()
        except Exception:
            pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


def _load_token():
    """Read-or-create the shared auth token (0600). Only the singleton daemon writes it."""
    try:
        with open(TOKEN_FILE) as fh:
            t = fh.read().strip()
            if t:
                return t
    except OSError:
        pass
    t = os.urandom(16).hex()
    with open(TOKEN_FILE, "w") as fh:
        fh.write(t)
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass
    return t


LOCK = os.path.join(_HOME, "bled.lock")


async def _main():
    # singleton: hold an exclusive flock for the daemon's lifetime; racing spawns lose it and exit.
    import fcntl

    global _lockf
    _lockf = open(LOCK, "w")
    try:
        fcntl.flock(_lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log("another daemon holds the lock; exiting")
        return
    _lockf.write(str(os.getpid()))
    _lockf.flush()
    global _TOKEN
    _TOKEN = _load_token()
    try:
        os.unlink(SOCK)
    except FileNotFoundError:
        pass
    server = await asyncio.start_unix_server(_serve_client, path=SOCK)
    try:
        os.chmod(SOCK, 0o600)  # owner-only — block other local users from driving the device
    except OSError:
        pass
    asyncio.create_task(_idle_watch())
    log("listening", SOCK, "pid", os.getpid())
    async with server:
        await server.serve_forever()


def run():
    asyncio.run(_main())


if __name__ == "__main__":
    run()
