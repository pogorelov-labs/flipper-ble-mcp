"""Pure-logic tests for the health-watch evaluator + parsers (no BLE, no daemon)."""

from flipper_ble_mcp import flipper_healthwatch as hw


def _snap(**battery):
    return {
        "reachable": True,
        "battery": battery,
        "storage_ext": {"pct_free": 99},
        "rtc": {"drift_sec": 1},
        "device": {},
    }


def test_low_battery_while_discharging_alerts():
    out = hw.evaluate(
        _snap(charge_level=9, charge_state="discharging", battery_health=100, battery_temp=25), None
    )
    assert any(lvl == "ALERT" for lvl, _ in out)


def test_low_battery_while_charging_does_not_alert():
    out = hw.evaluate(
        _snap(charge_level=9, charge_state="charging", battery_health=100, battery_temp=25), None
    )
    assert not any(lvl == "ALERT" for lvl, _ in out)


def test_healthy_is_silent():
    out = hw.evaluate(
        _snap(charge_level=86, charge_state="discharging", battery_health=100, battery_temp=25), None
    )
    assert out == []


def test_aging_hot_full_sd_and_drift_all_warn():
    snap = {
        "reachable": True,
        "battery": {"charge_level": 90, "charge_state": "charging", "battery_health": 70, "battery_temp": 48},
        "storage_ext": {"pct_free": 5},
        "rtc": {"drift_sec": 600},
        "device": {},
    }
    out = hw.evaluate(snap, None)
    assert {lvl for lvl, _ in out} == {"WARN"}
    assert len(out) == 4  # aging health, hot temp, low SD, clock drift


def test_unreachable_warns():
    out = hw.evaluate({"reachable": False, "unreachable_reason": "device not found"}, None)
    assert out and out[0][0] == "WARN"


def test_firmware_change_is_a_notice():
    cur = {
        "reachable": True,
        "battery": {},
        "storage_ext": {},
        "rtc": {},
        "device": {"firmware_version": "mntm-dev", "firmware_commit": "NEW", "ble_mac": "X"},
    }
    prev = {"device": {"firmware_version": "mntm-dev", "firmware_commit": "OLD", "ble_mac": "X"}}
    assert any(lvl == "NOTICE" for lvl, _ in hw.evaluate(cur, prev))


def test_kv_and_to_int_parsers():
    d = hw._kv("charge_level = 86\ncharge_state = discharging\njunk without delimiter\n")
    assert d["charge_level"] == "86"
    assert d["charge_state"] == "discharging"
    assert "junk without delimiter" not in d
    assert hw._to_int("42") == 42
    assert hw._to_int("nope") is None
    assert hw._to_int(None) is None
