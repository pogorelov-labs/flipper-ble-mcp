"""The scheduled health-watch must be STRUCTURALLY incapable of non-read-only commands.

Hardware-free: only imports the stdlib-only health-watch module and exercises its command
allowlist guard — no BLE, no daemon, runs anywhere (CI included).
"""

import pytest

from flipper_ble_mcp import flipper_healthwatch as hw


def test_send_blocks_non_readonly_commands():
    """send() asserts membership before touching the daemon, so writes/TX can't slip through."""
    for bad in ("press", "write", "app", "delete", "reboot", "transmit_subghz", "appbutton"):
        with pytest.raises(AssertionError):
            hw.send(bad)


def test_readonly_allowlist_is_exactly_the_safe_set():
    assert hw.READONLY_CMDS == {"power", "diskinfo", "getdt", "info", "ping", "health", "selftest"}
