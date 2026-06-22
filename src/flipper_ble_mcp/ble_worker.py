#!/usr/bin/env python3
"""BLE worker inside FlipperBLE.app. RPC over BLE done right:
- bleak event loop on the MAIN thread (so CoreBluetooth notifications fire),
- notification_discriminator on subscribes (macOS read/notify share a callback),
- FlipperProto (sync) runs in a WORKER thread; its read() drains the notify buffer,
  its write() is marshalled back to the main loop.
"""

import asyncio
import os
import sys
import threading
import time

_HOME = os.environ.get("FLIPPER_AI_HOME") or os.path.expanduser("~/.flipper-ble-mcp")
os.makedirs(_HOME, exist_ok=True)

RX = "19ed82ae-ed21-4c9d-4145-228e61fe0000"  # indicate: Flipper -> host (data)
TX = "19ed82ae-ed21-4c9d-4145-228e62fe0000"  # write:    host -> Flipper (data)
FLOW = "19ed82ae-ed21-4c9d-4145-228e63fe0000"
STATUS = "19ed82ae-ed21-4c9d-4145-228e64fe0000"
ADDR = ""  # per-host CoreBluetooth UUID, discovered at runtime


def log(*a):
    print(*a, flush=True)


async def _find_device(timeout=10):
    """Robust + fast finder: scan with a detection callback and early-exit the moment the
    Flipper is seen (matches by address OR name). Beats discover() — which always waits the
    full timeout — and find_device_by_address, which is flaky on macOS CoreBluetooth."""
    from bleak import BleakScanner

    found = {}
    ev = asyncio.Event()

    def _cb(d, adv):
        n = d.name or adv.local_name or ""
        if d.address == ADDR or "flip" in n.lower():
            found["d"] = d
            ev.set()

    scanner = BleakScanner(detection_callback=_cb)
    await scanner.start()
    try:
        await asyncio.wait_for(ev.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    finally:
        try:
            await scanner.stop()
        except Exception:
            pass
    return found.get("d")


# ---- shared RPC building blocks ---------------------------------------------
SCREEN_REQ = bytes.fromhex("050801a20100")  # gui_start_screen_stream_request
FB_MARK = bytes.fromhex("0a8008")  # ScreenFrame.data: field1, wire2, varint len 1024


def _frame(body: bytes) -> bytes:
    """length-delimited PB_Main: varint length prefix + body."""
    out = bytearray()
    n = len(body)
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | 0x80 if n else b)
        if not n:
            break
    return bytes(out) + body


def _input_frames(plan):
    """plan: list of (button, TYPE). Returns framed gui_send_input_event_request bytes,
    built via the protobuf lib (zero hand-encoding risk)."""
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2, gui_pb2

    frames = []
    for btn, itype in plan:
        m = flipper_pb2.Main()
        m.command_id = 1
        m.gui_send_input_event_request.key = gui_pb2.InputKey.Value(btn.upper())
        m.gui_send_input_event_request.type = gui_pb2.InputType.Value(itype.upper())
        frames.append(_frame(m.SerializeToString()))
    return frames


def _fb_to_png(fb: bytes, path: str):
    """Decode the 1024-byte 128x64 8-page framebuffer -> 6x PNG."""
    import numpy as np
    from PIL import Image

    W, H = 128, 64
    arr = np.zeros((H, W), "uint8")
    for page in range(8):
        for col in range(W):
            b = fb[page * W + col]
            for bit in range(8):
                if (b >> bit) & 1:
                    arr[page * 8 + bit, col] = 255
    Image.fromarray(arr, "L").resize((W * 6, H * 6), Image.NEAREST).save(path)


def _make_proto(ser):
    from flipperzero_protobuf.flipper_proto import FlipperProto

    class FlipperProtoBLE(FlipperProto):
        def _open_serial(self, dev=None):
            return dev

        def _get_startup_info(self):
            return {}

        def start_rpc_session(self):
            self._serial.write(b"start_rpc_session\r")
            time.sleep(0.5)
            self._serial.reset_input_buffer()
            self._in_session = True

    return FlipperProtoBLE(serial_port=ser)


def run_rpc(work, timeout=25):
    """bleak loop on main thread + FlipperProto in a worker thread. Returns work(proto)."""
    from bleak import BleakClient

    buf = bytearray()
    lock = threading.Lock()
    out = {}

    async def orchestrate():
        async with BleakClient(ADDR) as client:
            log("connected")
            disc = {"notification_discriminator": lambda d: True}

            def on_rx(_c, d):
                b = bytes(d)
                log("[rx61]", len(b), b.hex()[:60])
                with lock:
                    buf.extend(b)

            await client.start_notify(RX, on_rx, cb=disc)
            await client.start_notify(FLOW, lambda _c, d: log("[flow63]", bytes(d).hex()[:40]), cb=disc)
            await client.start_notify(STATUS, lambda _c, d: log("[status64]", bytes(d).hex()[:40]), cb=disc)
            loop = asyncio.get_running_loop()

            class Ser:
                timeout = 6.0

                def read(self, size=1):
                    end = time.monotonic() + self.timeout
                    o = bytearray()
                    while len(o) < size and time.monotonic() < end:
                        with lock:
                            k = min(size - len(o), len(buf))
                            if k:
                                o += buf[:k]
                                del buf[:k]
                        if len(o) < size:
                            time.sleep(0.005)
                    return bytes(o)

                def read_until(self, expected=b"\n", size=None):
                    end = time.monotonic() + self.timeout
                    o = bytearray()
                    while time.monotonic() < end:
                        with lock:
                            if buf:
                                o += buf
                                buf.clear()
                        if expected and expected in bytes(o):
                            break
                        time.sleep(0.01)
                    return bytes(o)

                def write(self, data):
                    log("[write tx62]", len(data), bytes(data).hex()[:40], "(no-response)")
                    asyncio.run_coroutine_threadsafe(
                        client.write_gatt_char(TX, bytes(data), response=False), loop
                    ).result(timeout=10)
                    return len(data)

                def flush(self):
                    pass

                def reset_input_buffer(self):
                    with lock:
                        buf.clear()

                @property
                def in_waiting(self):
                    with lock:
                        return len(buf)

            def blocking():
                proto = _make_proto(Ser())
                log("rpc session up; running work")
                return work(proto)

            out["res"] = await asyncio.wait_for(loop.run_in_executor(None, blocking), timeout=timeout)

    asyncio.run(orchestrate())
    return out.get("res")


def do_ctl():
    """Decisive: single-thread harness (known to deliver notifications) + no-response writes
    + real device_info request. Compare WITH vs WITHOUT start_rpc_session."""
    from bleak import BleakClient

    REQ = bytes.fromhex("050801820200")  # device_info request (FlipperProto-built)

    async def run(label, send_start):
        log(f"=== {label} (start_rpc={send_start}) ===")
        got = []
        async with BleakClient(ADDR) as client:
            disc = {"notification_discriminator": lambda d: True}

            def on_rx(_c, d):
                b = bytes(d)
                log("  [rx61]", len(b), b.hex()[:80])
                got.append(b)

            await client.start_notify(RX, on_rx, cb=disc)
            await client.start_notify(FLOW, lambda _c, d: log("  [flow63]", bytes(d).hex()[:24]), cb=disc)
            await client.start_notify(STATUS, lambda _c, d: log("  [status64]", bytes(d).hex()[:24]), cb=disc)
            await asyncio.sleep(0.8)
            if send_start:
                log("  -> start_rpc_session\\r")
                await client.write_gatt_char(TX, b"start_rpc_session\r", response=False)
                await asyncio.sleep(0.8)
            log("  -> device_info request", REQ.hex())
            await client.write_gatt_char(TX, REQ, response=False)
            await asyncio.sleep(3.0)
            nz = any(bytes(g).rstrip(b"\x00") for g in got)
            log(f"  RESULT {label}: notifications={len(got)} any_nonzero={nz}")

    async def main():
        await run("A-with-start", True)
        await asyncio.sleep(0.5)
        await run("B-no-start", False)

    asyncio.run(main())


def do_scan():
    async def _s():
        from bleak import BleakScanner

        ds = await BleakScanner.discover(timeout=8, return_adv=True)
        for addr, (d, adv) in ds.items():
            n = d.name or adv.local_name or ""
            if "flip" in n.lower():
                log("FLIPPER_FOUND", addr, n, adv.rssi)

    asyncio.run(_s())


def _uvarint(b, i=0):
    shift = 0
    res = 0
    while i < len(b):
        x = b[i]
        res |= (x & 0x7F) << shift
        i += 1
        if not (x & 0x80):
            return res, i
        shift += 7
    return None, i


def _parse_main(msg):
    """Minimal PB_Main parse -> (has_next, key, value) for key/value response messages."""
    i = 0
    has_next = 0
    key = val = None
    while i < len(msg):
        tag, i = _uvarint(msg, i)
        if tag is None:
            break
        field, wt = tag >> 3, tag & 7
        if wt == 0:
            v, i = _uvarint(msg, i)
            if field == 3:
                has_next = v
        elif wt == 2:
            ln, i = _uvarint(msg, i)
            sub = msg[i : i + ln]
            i += ln
            if field == 33:  # *_device_info_response sub-message (key=1, value=2)
                j = 0
                while j < len(sub):
                    t2, j = _uvarint(sub, j)
                    if t2 is None:
                        break
                    f2, w2 = t2 >> 3, t2 & 7
                    if w2 == 2:
                        l2, j = _uvarint(sub, j)
                        s = sub[j : j + l2]
                        j += l2
                        if f2 == 1:
                            key = s.decode("utf-8", "replace")
                        elif f2 == 2:
                            val = s.decode("utf-8", "replace")
                    elif w2 == 0:
                        _, j = _uvarint(sub, j)
                    else:
                        break
        else:
            break
    return has_next, key, val


def _parse_status(buf):
    """Parse the first complete length-delimited PB_Main in buf; return command_status
    (field 2 varint; 0 = OK, absent = 0) or None if the frame isn't complete yet."""
    ln, off = _uvarint(buf, 0)
    if ln is None or len(buf) < off + ln:
        return None
    msg = bytes(buf[off : off + ln])
    i = 0
    status = 0
    while i < len(msg):
        tag, i = _uvarint(msg, i)
        if tag is None:
            break
        field, wt = tag >> 3, tag & 7
        if wt == 0:
            v, i = _uvarint(msg, i)
            if field == 2:
                status = v
        elif wt == 2:
            l2, i = _uvarint(msg, i)
            i += l2
        else:
            break
    return status


def do_info():
    from bleak import BleakClient

    REQ = bytes.fromhex("050801820200")  # device_info request; NO start_rpc_session over BLE
    fields = {}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            while buf:
                ln, off = _uvarint(buf, 0)
                if ln is None or len(buf) < off + ln:
                    break
                msg = bytes(buf[off : off + ln])
                del buf[: off + ln]
                hn, k, v = _parse_main(msg)
                if k is not None:
                    fields[k] = v
                if hn == 0:
                    done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found (Flipper BT on? not bonded to phone?)")
            return fields
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.3)
            log("sending device_info request (direct protobuf, no start_rpc_session)")
            await client.write_gatt_char(TX, REQ, response=False)
            try:
                await asyncio.wait_for(done.wait(), timeout=8)
            except asyncio.TimeoutError:
                log("(timeout)")
        return fields

    info = asyncio.run(_run())
    log(f"DEVICE_INFO over BLE: {len(info)} fields")
    for k, v in info.items():
        log(f"  {k} = {v}")


def do_screenshot():
    from bleak import BleakClient

    result = {}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            idx = bytes(buf).find(FB_MARK)
            if idx != -1 and len(buf) >= idx + 3 + 1024:
                result["fb"] = bytes(buf[idx + 3 : idx + 3 + 1024])
                done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.3)
            log("sending start_screen_stream (direct protobuf, no start_rpc_session)")
            await client.write_gatt_char(TX, SCREEN_REQ, response=False)
            try:
                await asyncio.wait_for(done.wait(), timeout=12)
            except asyncio.TimeoutError:
                log("(timeout; buffered", len(buf), "bytes)")

    asyncio.run(_run())
    fb = result.get("fb")
    if not fb:
        log("no framebuffer captured")
        return
    log("framebuffer captured:", len(fb), "bytes")
    _fb_to_png(fb, os.path.join(_HOME, "ble_screen.png"))
    log("saved ble_screen.png")


def do_press(tokens):
    """Inject UI input over BLE. tokens: e.g. ['ok'] or ['down','down','ok:long'] or
    ['down','ok','+shot']. Each token is btn[:kind]; kind in short|long|press|release
    (default short). '+shot' = grab a screenshot in the SAME connection after the presses."""
    from bleak import BleakClient

    BTN = {"up", "down", "left", "right", "ok", "back"}
    shot = "+shot" in tokens
    toks = [t for t in tokens if t != "+shot"]
    plan = []
    for t in toks:
        btn, _, kind = t.partition(":")
        btn = btn.lower()
        kind = (kind or "short").lower()
        if btn not in BTN:
            log("bad button:", btn)
            return
        if kind == "short":
            plan += [(btn, "PRESS"), (btn, "SHORT"), (btn, "RELEASE")]
        elif kind == "long":
            plan += [(btn, "PRESS"), (btn, "LONG"), (btn, "RELEASE")]
        elif kind == "press":
            plan += [(btn, "PRESS")]
        elif kind == "release":
            plan += [(btn, "RELEASE")]
        else:
            log("bad kind:", kind)
            return
    if not plan:
        log("no buttons given")
        return
    frames = _input_frames(plan)
    result = {}

    async def _run():
        buf = bytearray()
        fb_done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            if shot:
                idx = bytes(buf).find(FB_MARK)
                if idx != -1 and len(buf) >= idx + 3 + 1024:
                    result["fb"] = bytes(buf[idx + 3 : idx + 3 + 1024])
                    fb_done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            for fr in frames:
                await client.write_gatt_char(TX, fr, response=False)
                await asyncio.sleep(0.04)
            log(f"sent {len(toks)} button action(s) = {len(frames)} input events")
            await asyncio.sleep(0.25)
            if shot:
                buf.clear()  # drop input acks; want a clean framebuffer scan
                await client.write_gatt_char(TX, SCREEN_REQ, response=False)
                try:
                    await asyncio.wait_for(fb_done.wait(), timeout=12)
                except asyncio.TimeoutError:
                    log("(screenshot timeout)")

    asyncio.run(_run())
    log("PRESS_OK", " ".join(toks))
    if shot:
        fb = result.get("fb")
        if fb:
            _fb_to_png(fb, os.path.join(_HOME, "ble_screen.png"))
            log("saved ble_screen.png")
        else:
            log("no framebuffer captured")


def do_app_launch(tokens):
    """Launch an app by name over BLE (app_start_request, PB_Main field 16). tokens: the app
    name (may be multiple words) optionally with a trailing '+shot' to grab its first frame."""
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    shot = "+shot" in tokens
    toks = [t for t in tokens if t != "+shot"]
    if "--args" in toks:
        i = toks.index("--args")
        name = " ".join(toks[:i]).strip()
        appargs = " ".join(toks[i + 1 :]).strip()
    else:
        name = " ".join(toks).strip()
        appargs = ""
    if not name:
        log("no app name given")
        return
    m = flipper_pb2.Main()
    m.command_id = 1
    m.app_start_request.name = name
    if appargs:
        m.app_start_request.args = appargs
    req = _frame(m.SerializeToString())
    result = {}

    async def _run():
        buf = bytearray()
        status_done = asyncio.Event()
        fb_done = asyncio.Event()
        mode = {"fb": False}

        def on_rx(_c, d):
            buf.extend(bytes(d))
            if mode["fb"]:
                idx = bytes(buf).find(FB_MARK)
                if idx != -1 and len(buf) >= idx + 3 + 1024:
                    result["fb"] = bytes(buf[idx + 3 : idx + 3 + 1024])
                    fb_done.set()
            else:
                st = _parse_status(buf)
                if st is not None:
                    result["status"] = st
                    status_done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            log(f"launching app: {name!r}" + (f" args={appargs!r}" if appargs else ""))
            await client.write_gatt_char(TX, req, response=False)
            try:
                await asyncio.wait_for(status_done.wait(), timeout=8)
            except asyncio.TimeoutError:
                pass
            if shot:
                await asyncio.sleep(0.7)  # let the app draw its first frame
                mode["fb"] = True
                buf.clear()
                await client.write_gatt_char(TX, SCREEN_REQ, response=False)
                try:
                    await asyncio.wait_for(fb_done.wait(), timeout=12)
                except asyncio.TimeoutError:
                    log("(screenshot timeout)")

    asyncio.run(_run())
    st = result.get("status")
    if st is None:
        log(f"APP_LAUNCH {name}: no response (it may still have launched)")
    elif st == 0:
        log(f"APP_LAUNCH_OK {name}")
    else:
        log(
            f"APP_LAUNCH_ERR {name}: status={st} (unknown app name, or an app is already "
            f"running — exit it first)"
        )
    if shot:
        fb = result.get("fb")
        if fb:
            _fb_to_png(fb, os.path.join(_HOME, "ble_screen.png"))
            log("saved ble_screen.png")
        else:
            log("no framebuffer captured")


def do_storage_list(tokens):
    """List a directory over BLE (storage_list_request). tokens join into the path (may have spaces)."""
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    path = " ".join(tokens).strip() or "/ext"
    m = flipper_pb2.Main()
    m.command_id = 1
    m.storage_list_request.path = path
    req = _frame(m.SerializeToString())
    files = []
    err = {"code": 0}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            while True:
                ln, off = _uvarint(buf, 0)
                if ln is None or len(buf) < off + ln:
                    break
                msg = bytes(buf[off : off + ln])
                del buf[: off + ln]
                main = flipper_pb2.Main()
                main.ParseFromString(msg)
                if main.command_status != 0:
                    err["code"] = main.command_status
                for f in main.storage_list_response.file:
                    files.append((f.type, f.name, f.size))
                if not main.has_next:
                    done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            log(f"listing: {path}")
            await client.write_gatt_char(TX, req, response=False)
            try:
                await asyncio.wait_for(done.wait(), timeout=20)
            except asyncio.TimeoutError:
                log("(timeout)")

    asyncio.run(_run())
    if err["code"]:
        log(f"LIST_ERR {path}: status={err['code']} (path not found?)")
        return
    log(f"LIST {path}: {len(files)} entries")
    for t, name, size in sorted(files, key=lambda x: (x[0] == 0, x[1].lower())):
        log(f"  [DIR]  {name}" if t == 1 else f"  {size:>9}  {name}")
    log("LIST_DONE")


def do_storage_read(tokens):
    """Read a file over BLE (storage_read_request). tokens join into the path. Saves raw bytes
    to ble_file.bin and reports size + text/binary."""
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    path = " ".join(tokens).strip()
    if not path:
        log("no path given")
        return
    m = flipper_pb2.Main()
    m.command_id = 1
    m.storage_read_request.path = path
    req = _frame(m.SerializeToString())
    data = bytearray()
    err = {"code": 0}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            while True:
                ln, off = _uvarint(buf, 0)
                if ln is None or len(buf) < off + ln:
                    break
                msg = bytes(buf[off : off + ln])
                del buf[: off + ln]
                main = flipper_pb2.Main()
                main.ParseFromString(msg)
                if main.command_status != 0:
                    err["code"] = main.command_status
                data.extend(main.storage_read_response.file.data)
                if not main.has_next:
                    done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            log(f"reading: {path}")
            await client.write_gatt_char(TX, req, response=False)
            try:
                await asyncio.wait_for(done.wait(), timeout=30)
            except asyncio.TimeoutError:
                log("(timeout — file may be too large for BLE; use USB)")

    asyncio.run(_run())
    if err["code"]:
        log(f"FILE_ERR {path}: status={err['code']} (not found / not a file?)")
        return
    with open(os.path.join(_HOME, "ble_file.bin"), "wb") as fh:
        fh.write(bytes(data))
    try:
        bytes(data).decode("utf-8")
        kind = "TEXT"
    except UnicodeDecodeError:
        kind = "BINARY"
    log(f"FILE_OK {path} {len(data)} bytes {kind}")
    log("saved ble_file.bin")


# ---- generic RPC helpers ----------------------------------------------------
def _mk(setter):
    """Build a framed PB_Main (command_id=1) configured by setter(main)."""
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    m = flipper_pb2.Main()
    m.command_id = 1
    setter(m)
    return _frame(m.SerializeToString())


def _status_handler(st):
    """A handle() that records command_status of the first complete response and stops."""

    def h(main):
        st["s"] = main.command_status
        return True

    return h


def _rpc(build_req, handle, timeout=20):
    """Connect over BLE, send build_req() to TX, feed each parsed PB_Main to handle(main)
    until it returns True or has_next=0. Returns True if the device was found."""
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    state = {"found": False}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            while True:
                ln, off = _uvarint(buf, 0)
                if ln is None or len(buf) < off + ln:
                    break
                msg = bytes(buf[off : off + ln])
                del buf[: off + ln]
                main = flipper_pb2.Main()
                main.ParseFromString(msg)
                if handle(main) or not main.has_next:
                    done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        state["found"] = True
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            await client.write_gatt_char(TX, build_req(), response=False)
            try:
                await asyncio.wait_for(done.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                log("(timeout)")

    asyncio.run(_run())
    return state["found"]


# ---- system / desktop -------------------------------------------------------
def do_power_info():
    fields = {}

    def h(main):
        r = main.system_power_info_response
        if r.key:
            fields[r.key] = r.value
        return False

    _rpc(lambda: _mk(lambda m: m.system_power_info_request.SetInParent()), h, timeout=12)
    log(f"POWER_INFO: {len(fields)} fields")
    for k, v in fields.items():
        log(f"  {k} = {v}")


def do_ping():
    payload = b"flipperping"
    got = {}

    def h(main):
        got["data"] = bytes(main.system_ping_response.data)
        return True

    if _rpc(lambda: _mk(lambda m: setattr(m.system_ping_request, "data", payload)), h, timeout=8):
        d = got.get("data")
        log("PING_OK (echo matched)" if d == payload else f"PING got {d!r}")


def do_get_datetime():
    got = {}

    def h(main):
        dt = main.system_get_datetime_response.datetime
        got["v"] = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        return True

    if _rpc(lambda: _mk(lambda m: m.system_get_datetime_request.SetInParent()), h, timeout=8):
        if "v" in got:
            y, mo, d, hh, mm, ss = got["v"]
            log(f"DATETIME {y:04d}-{mo:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}")


def do_set_datetime(tokens):
    import datetime as _dt

    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    if tokens and tokens[0] != "now":
        y, mo, d, hh, mm, ss = (int(x) for x in tokens[:6])
    else:
        n = _dt.datetime.now()
        y, mo, d, hh, mm, ss = n.year, n.month, n.day, n.hour, n.minute, n.second

    def build():
        m = flipper_pb2.Main()
        m.command_id = 1
        dt = m.system_set_datetime_request.datetime
        dt.year, dt.month, dt.day = y, mo, d
        dt.hour, dt.minute, dt.second = hh, mm, ss
        dt.weekday = _dt.date(y, mo, d).weekday() + 1
        return _frame(m.SerializeToString())

    st = {}
    _rpc(build, _status_handler(st), timeout=8)
    log(
        f"SETDATETIME {'OK' if st.get('s', 0) == 0 else 'ERR ' + str(st.get('s'))} "
        f"{y:04d}-{mo:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"
    )


def do_desktop_locked():
    st = {}
    if _rpc(lambda: _mk(lambda m: m.desktop_is_locked_request.SetInParent()), _status_handler(st), timeout=8):
        s = st.get("s", 0)
        log(f"DESKTOP status={s} -> {'LOCKED' if s == 0 else 'UNLOCKED'}")


def do_alert():
    st = {}
    _rpc(
        lambda: _mk(lambda m: m.system_play_audiovisual_alert_request.SetInParent()),
        _status_handler(st),
        timeout=8,
    )
    log(f"ALERT {'OK (beep+flash)' if st.get('s', 0) == 0 else 'ERR ' + str(st.get('s'))}")


# ---- app lifecycle ----------------------------------------------------------
def do_app_exit():
    st = {}
    _rpc(lambda: _mk(lambda m: m.app_exit_request.SetInParent()), _status_handler(st), timeout=8)
    log(f"APP_EXIT {_status_str(st.get('s', 0))}")


def do_app_lock_status():
    got = {}

    def h(main):
        got["locked"] = main.app_lock_status_response.locked
        return True

    if _rpc(lambda: _mk(lambda m: m.app_lock_status_request.SetInParent()), h, timeout=8):
        log(f"APP_LOCK {'an app is RUNNING' if got.get('locked') else 'free (desktop/menu)'}")


def do_app_load(tokens):
    path = " ".join(tokens).strip()
    if not path:
        log("no path given")
        return
    st = {}
    _rpc(
        lambda: _mk(lambda m: setattr(m.app_load_file_request, "path", path)), _status_handler(st), timeout=10
    )
    s = st.get("s", 0)
    log(f"APP_LOAD {path}: {'OK' if s == 0 else 'ERR ' + str(s) + ' (start the matching app first?)'}")


def do_app_button(tokens):
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    args = " ".join(tokens).strip()
    press = _mk(lambda m: setattr(m.app_button_press_request, "args", args))
    release = _mk(lambda m: m.app_button_release_request.SetInParent())
    st = {"codes": []}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            while True:
                ln, off = _uvarint(buf, 0)
                if ln is None or len(buf) < off + ln:
                    break
                msg = bytes(buf[off : off + ln])
                del buf[: off + ln]
                main = flipper_pb2.Main()
                main.ParseFromString(msg)
                if not main.has_next:
                    st["codes"].append(main.command_status)
                    if len(st["codes"]) >= 2:
                        done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            await client.write_gatt_char(TX, press, response=False)
            await asyncio.sleep(0.15)
            await client.write_gatt_char(TX, release, response=False)
            try:
                await asyncio.wait_for(done.wait(), timeout=8)
            except asyncio.TimeoutError:
                pass

    asyncio.run(_run())
    log(f"APP_BUTTON {args!r}: statuses={st['codes']}")


# ---- storage: metadata ------------------------------------------------------
def do_storage_info(tokens):
    path = " ".join(tokens).strip() or "/ext"
    got = {}

    def h(main):
        got["s"] = main.command_status
        got["total"] = main.storage_info_response.total_space
        got["free"] = main.storage_info_response.free_space
        return True

    _rpc(lambda: _mk(lambda m: setattr(m.storage_info_request, "path", path)), h, timeout=10)
    if got.get("s", 0):
        log(f"INFO_ERR {path}: status={got['s']}")
        return
    total, free = got.get("total", 0), got.get("free", 0)
    pct = (free * 100 // total) if total else 0
    log(f"STORAGE_INFO {path}: free {free} / total {total} bytes ({pct}% free)")


def do_storage_stat(tokens):
    path = " ".join(tokens).strip()
    if not path:
        log("no path given")
        return
    got = {}

    def h(main):
        got["s"] = main.command_status
        got["type"] = main.storage_stat_response.file.type
        got["size"] = main.storage_stat_response.file.size
        return True

    _rpc(lambda: _mk(lambda m: setattr(m.storage_stat_request, "path", path)), h, timeout=10)
    if got.get("s", 0):
        log(f"STAT_ERR {path}: status={got['s']} (not found?)")
        return
    log(f"STAT {path}: {'DIR' if got.get('type') == 1 else 'FILE'} {got.get('size', 0)} bytes")


def do_storage_md5(tokens):
    path = " ".join(tokens).strip()
    if not path:
        log("no path given")
        return
    got = {}

    def h(main):
        got["s"] = main.command_status
        got["md5"] = main.storage_md5sum_response.md5sum
        return True

    _rpc(lambda: _mk(lambda m: setattr(m.storage_md5sum_request, "path", path)), h, timeout=15)
    if got.get("s", 0):
        log(f"MD5_ERR {path}: status={got['s']}")
        return
    log(f"MD5 {path}: {got.get('md5', '')}")


# ---- storage: writes (gated) ------------------------------------------------
def do_storage_delete(tokens):
    recursive = "-r" in tokens
    path = " ".join(t for t in tokens if t != "-r").strip()
    if not path:
        log("no path given")
        return

    def setter(m):
        m.storage_delete_request.path = path
        m.storage_delete_request.recursive = recursive

    st = {}
    _rpc(lambda: _mk(setter), _status_handler(st), timeout=12)
    s = st.get("s", 0)
    log(f"DELETE {path} (recursive={recursive}): {'OK' if s == 0 else 'ERR ' + str(s)}")


def do_storage_mkdir(tokens):
    path = " ".join(tokens).strip()
    if not path:
        log("no path given")
        return
    st = {}
    _rpc(
        lambda: _mk(lambda m: setattr(m.storage_mkdir_request, "path", path)), _status_handler(st), timeout=10
    )
    s = st.get("s", 0)
    log(f"MKDIR {path}: {'OK' if s == 0 else 'ERR ' + str(s)}")


def do_storage_rename(tokens):
    if "->" not in tokens:
        log("need: <old> -> <new>")
        return
    i = tokens.index("->")
    old = " ".join(tokens[:i]).strip()
    new = " ".join(tokens[i + 1 :]).strip()
    if not old or not new:
        log("need: <old> -> <new>")
        return

    def setter(m):
        m.storage_rename_request.old_path = old
        m.storage_rename_request.new_path = new

    st = {}
    _rpc(lambda: _mk(setter), _status_handler(st), timeout=12)
    s = st.get("s", 0)
    log(f"RENAME {old} -> {new}: {'OK' if s == 0 else 'ERR ' + str(s)}")


def do_storage_write(tokens):
    """Upload ble_upload.bin to <dest> over BLE (chunked storage_write_request stream)."""
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    path = " ".join(tokens).strip()
    if not path:
        log("no dest path given")
        return
    try:
        with open(os.path.join(_HOME, "ble_upload.bin"), "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        log("no upload payload (ble_upload.bin missing)")
        return
    CHUNK = 512
    chunks = [data[i : i + CHUNK] for i in range(0, len(data), CHUNK)] or [b""]
    st = {}

    async def _run():
        buf = bytearray()
        done = asyncio.Event()

        def on_rx(_c, d):
            buf.extend(bytes(d))
            while True:
                ln, off = _uvarint(buf, 0)
                if ln is None or len(buf) < off + ln:
                    break
                msg = bytes(buf[off : off + ln])
                del buf[: off + ln]
                main = flipper_pb2.Main()
                main.ParseFromString(msg)
                if not main.has_next:
                    st["s"] = main.command_status
                    done.set()

        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.start_notify(RX, on_rx, cb={"notification_discriminator": lambda d: True})
            await asyncio.sleep(0.2)
            gchunk = max(20, (getattr(client, "mtu_size", 0) or 23) - 3)
            for i, ch in enumerate(chunks):
                last = i == len(chunks) - 1
                m = flipper_pb2.Main()
                m.command_id = 1
                m.has_next = not last
                if i == 0:
                    m.storage_write_request.path = path
                m.storage_write_request.file.data = ch
                frame = _frame(m.SerializeToString())
                for j in range(0, len(frame), gchunk):
                    await client.write_gatt_char(TX, frame[j : j + gchunk], response=False)
                await asyncio.sleep(0.02)
            try:
                await asyncio.wait_for(done.wait(), timeout=45)
            except asyncio.TimeoutError:
                log("(timeout — large file? use USB)")

    asyncio.run(_run())
    s = st.get("s", 0)
    log(f"WRITE {path} ({len(data)} bytes): {'OK' if s == 0 else 'ERR ' + str(s)}")


# ---- status decoding --------------------------------------------------------
_STATUS_HINT = {
    4: "device busy - retry shortly",
    5: "SD not mounted",
    6: "already exists",
    7: "path not found",
    9: "access denied (e.g. writing /int)",
    13: "file busy / already open",
    15: "missing/invalid parameter",
    16: "loader couldn't start the app",
    17: "another app is running - app_exit or press back first",
    18: "directory not empty - use recursive delete",
    21: "no RPC-exitable app (file-launched -> press back)",
    22: "app rejected the command - try app_get_error",
}


def _status_str(code):
    """'OK' for 0, else 'ERR NN NAME - hint'."""
    if code == 0:
        return "OK"
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2

    name = {v: k for k, v in flipper_pb2.CommandStatus.items()}.get(code, "ERROR")
    hint = _STATUS_HINT.get(code)
    return f"ERR {code} {name}" + (f" - {hint}" if hint else "")


# ---- app error / desktop unlock / reboot ------------------------------------
def do_app_error():
    """Fetch the running app's last error (human-readable). app_get_error_request."""
    got = {}

    def h(main):
        got["code"] = main.app_get_error_response.code
        got["text"] = main.app_get_error_response.text
        return True

    if _rpc(lambda: _mk(lambda m: m.app_get_error_request.SetInParent()), h, timeout=8):
        log(f"APP_ERROR code={got.get('code', 0)} text={got.get('text', '')!r}")


def do_desktop_unlock():
    """Clear the desktop lock. desktop_unlock_request. (Likely swipe-lock only, not a numeric PIN.)"""
    st = {}
    _rpc(lambda: _mk(lambda m: m.desktop_unlock_request.SetInParent()), _status_handler(st), timeout=8)
    log(f"DESKTOP_UNLOCK {_status_str(st.get('s', 0))}")


def do_reboot(tokens):
    """Reboot the Flipper. mode in OS|DFU|UPDATE (default OS). No response (device resets)."""
    from bleak import BleakClient
    from flipperzero_protobuf.flipperzero_protobuf_compiled import flipper_pb2, system_pb2

    mode = tokens[0].upper() if tokens else "OS"
    if mode not in ("OS", "DFU", "UPDATE"):
        log(f"bad mode {mode!r}; use OS|DFU|UPDATE")
        return
    modeval = system_pb2.RebootRequest.RebootMode.Value(mode)

    def build():
        m = flipper_pb2.Main()
        m.command_id = 1
        m.system_reboot_request.mode = modeval
        return _frame(m.SerializeToString())

    async def _run():
        dev = await _find_device()
        if dev is None:
            log("device not found in scan")
            return
        async with BleakClient(dev) as client:
            log("connected")
            await client.write_gatt_char(TX, build(), response=False)
            await asyncio.sleep(0.5)

    asyncio.run(_run())
    log(f"REBOOT sent (mode={mode}) - device is restarting")


# ---- GPIO (over RPC) --------------------------------------------------------
def do_gpio_read(tokens):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import gpio_pb2

    pin = tokens[0].upper() if tokens else ""
    if pin not in gpio_pb2.GpioPin.keys():
        log(f"bad pin {pin!r}; use {list(gpio_pb2.GpioPin.keys())}")
        return
    pv = gpio_pb2.GpioPin.Value(pin)
    got = {}

    def h(main):
        got["s"] = main.command_status
        got["v"] = main.gpio_read_pin_response.value
        return True

    if _rpc(lambda: _mk(lambda m: setattr(m.gpio_read_pin, "pin", pv)), h, timeout=8):
        if got.get("s", 0):
            log(f"GPIO_READ {pin}: {_status_str(got['s'])}")
        else:
            log(f"GPIO_READ {pin} = {got.get('v')}")


def do_gpio_write(tokens):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import gpio_pb2

    if len(tokens) < 2:
        log("usage: gpiowrite <PIN> <0|1>")
        return
    pin = tokens[0].upper()
    val = 1 if str(tokens[1]).strip().lower() in ("1", "high", "on", "true") else 0
    if pin not in gpio_pb2.GpioPin.keys():
        log(f"bad pin {pin!r}; use {list(gpio_pb2.GpioPin.keys())}")
        return

    def setter(m):
        m.gpio_write_pin.pin = gpio_pb2.GpioPin.Value(pin)
        m.gpio_write_pin.value = val

    st = {}
    _rpc(lambda: _mk(setter), _status_handler(st), timeout=8)
    log(f"GPIO_WRITE {pin}={val}: {_status_str(st.get('s', 0))}")


def do_gpio_mode(tokens):
    from flipperzero_protobuf.flipperzero_protobuf_compiled import gpio_pb2

    if len(tokens) < 2:
        log("usage: gpiomode <PIN> <output|input>")
        return
    pin, mode = tokens[0].upper(), tokens[1].upper()
    if pin not in gpio_pb2.GpioPin.keys() or mode not in gpio_pb2.GpioPinMode.keys():
        log(f"bad pin/mode; pins={list(gpio_pb2.GpioPin.keys())} modes={list(gpio_pb2.GpioPinMode.keys())}")
        return

    def setter(m):
        m.gpio_set_pin_mode.pin = gpio_pb2.GpioPin.Value(pin)
        m.gpio_set_pin_mode.mode = gpio_pb2.GpioPinMode.Value(mode)

    st = {}
    _rpc(lambda: _mk(setter), _status_handler(st), timeout=8)
    log(f"GPIO_MODE {pin}={mode}: {_status_str(st.get('s', 0))}")


DISPATCH = {
    "ctl": do_ctl,
    "scan": do_scan,
    "info": do_info,
    "screenshot": do_screenshot,
    "press": lambda: do_press(sys.argv[2:]),
    "app": lambda: do_app_launch(sys.argv[2:]),
    "list": lambda: do_storage_list(sys.argv[2:]),
    "read": lambda: do_storage_read(sys.argv[2:]),
    "diskinfo": lambda: do_storage_info(sys.argv[2:]),
    "stat": lambda: do_storage_stat(sys.argv[2:]),
    "md5": lambda: do_storage_md5(sys.argv[2:]),
    "write": lambda: do_storage_write(sys.argv[2:]),
    "delete": lambda: do_storage_delete(sys.argv[2:]),
    "mkdir": lambda: do_storage_mkdir(sys.argv[2:]),
    "rename": lambda: do_storage_rename(sys.argv[2:]),
    "appexit": do_app_exit,
    "appload": lambda: do_app_load(sys.argv[2:]),
    "applock": do_app_lock_status,
    "appbutton": lambda: do_app_button(sys.argv[2:]),
    "power": do_power_info,
    "ping": do_ping,
    "getdt": do_get_datetime,
    "setdt": lambda: do_set_datetime(sys.argv[2:]),
    "locked": do_desktop_locked,
    "alert": do_alert,
    "apperror": do_app_error,
    "unlock": do_desktop_unlock,
    "reboot": lambda: do_reboot(sys.argv[2:]),
    "gpioread": lambda: do_gpio_read(sys.argv[2:]),
    "gpiowrite": lambda: do_gpio_write(sys.argv[2:]),
    "gpiomode": lambda: do_gpio_mode(sys.argv[2:]),
    "daemon": lambda: __import__("flipper_bled").run(),
}


def _cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    log("WORKER START", time.strftime("%H:%M:%S"), "cmd=", cmd)
    try:
        handler = DISPATCH.get(cmd)
        if handler:
            handler()
        else:
            log("unknown cmd", cmd)
    except Exception as e:
        import traceback

        log("WORKER ERROR:", type(e).__name__, repr(e))
        log(traceback.format_exc())
    log("WORKER DONE")
    import os

    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    _cli()
