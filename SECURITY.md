# Security & Responsible Use

`flipper-ble-mcp` is a **dual-use** tool: it can read and write a Flipper Zero, transmit RF/IR, and
inject USB keystrokes (BadUSB). Use it only on **devices and targets you own or are explicitly
authorized to test**, and only on **legally permitted frequencies/bands** for your jurisdiction.

## Operating safeguards
- **Human-in-the-loop.** Every state-changing action (button press, app launch, file write, RF/IR
  transmit, BadUSB) surfaces as a **per-call approval prompt** in the MCP client. The bundled skill
  instructs the agent to **never autonomously transmit or run BadUSB** — it proposes; you approve.
- **Read-only by default where it matters.** The scheduled `healthwatch` job is structurally
  read-only (a hardcoded command allowlist; it cannot press/write/transmit) and ships **disabled**.
- **Local-only control channel.** The daemon listens on a `0600` Unix-domain socket (not the
  network) and requires a shared token; the macOS Bluetooth entitlement is isolated inside a
  separate signed `.app`, so the MCP process itself never holds Bluetooth access.

## Threat model (brief)
- The trust boundary is the **local user account**. The `0600` socket blocks other local users; the
  token blocks opportunistic same-user processes. It is **not** hardened against a fully compromised
  local account (which could read the token file).
- **Do not** feed untrusted or captured content (scraped pages, captured RF/NFC payloads) into a
  session that is holding transmit/HID tools — prompt-injection could turn into a hardware action.
  The skill warns against this.

## Reporting a vulnerability
Please open a private **GitHub Security Advisory** (preferred), or contact the maintainer, rather
than filing a public issue (use the repository Security tab -> "Report a vulnerability").
