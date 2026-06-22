"""Pure varint-decode tests for the BLE framing layer (no BLE, no protobuf)."""

from flipper_ble_mcp import ble_worker as w


def test_uvarint_single_byte():
    assert w._uvarint(b"\x05", 0) == (5, 1)


def test_uvarint_multibyte():
    assert w._uvarint(b"\x80\x01", 0) == (128, 2)
    assert w._uvarint(b"\xac\x02", 0) == (300, 2)


def test_uvarint_respects_offset():
    assert w._uvarint(b"\xff\x05", 1) == (5, 2)
