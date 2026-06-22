## What & why
<!-- What does this change do, and why? Link any related issue. -->

## Type
- [ ] Bug fix
- [ ] Feature
- [ ] Docs / KB
- [ ] Tooling / CI

## Checklist
- [ ] `ruff check` and `ruff format --check` pass
- [ ] Tests pass (`pytest`); added tests for new logic where practical
- [ ] If KB docs changed: ran `python3 build-kb-index.py` (did not hand-edit generated files)
- [ ] No secrets, credentials, or device-identifying data (BLE MAC, serials) committed
- [ ] Dual-use features remain human-gated (no autonomous transmit / HID)
