# Test evidence ledger

**Phase 0:** No application tests have been run by this setup task. Add a separate record for each executed test; do not mark a planned test as passed.

## Blank record template

| Field | Entry |
| --- | --- |
| Test ID | |
| Requirement ID | |
| Environment | Machine(s), OS, Python version, network, date/time |
| Steps or command | |
| Expected result | |
| Actual result | |
| Status | Not run / Pass / Fail / Blocked |
| Evidence location | Capture, screenshot, log, or transcript path |

Distinguish loopback observations from real two-computer LAN evidence. Keep actual Wireshark captures and demo observations when available.

## TV2 automated evidence — 2026-11-13

| Field | Entry |
| --- | --- |
| Test ID | TV2-UNIT-001 |
| Requirement ID | R10, R11, R13, R14, R23, R25, R26, R27, R36 |
| Environment | macOS, Python 3.12, IPv4 loopback, 2026-11-13 |
| Steps or command | `python3 -m unittest discover -s tests -v` |
| Expected result | Frame validation/exact reads, UTF-8, full-duplex and multi-peer TCP, duplicate connection resolution, disconnect cleanup, history and unread state all pass. |
| Actual result | 16 tests passed. |
| Status | Pass |
| Evidence location | Test output in TV2 development session; reproducible from committed tests. |

This is loopback/unit evidence, not the required two-computer LAN demo or Wireshark handshake capture.

| Field | Entry |
| --- | --- |
| Test ID | TV2-ECHO-001 |
| Requirement ID | Milestone 1 TCP Echo Server |
| Environment | macOS, Python 3.12, IPv4 loopback, 2026-11-13 |
| Steps or command | Start `tcp_echo_server.py --host 127.0.0.1 --port 19090 --once`; connect with a Python socket client. |
| Expected result | Server returns the exact UTF-8 bytes sent by the client and exits after disconnect. |
| Actual result | Client received `echo tiếng Việt`; server logged one connect and disconnect. |
| Status | Pass |
| Evidence location | Reproducible with `examples/milestone_01/tcp_echo_server.py`. |
