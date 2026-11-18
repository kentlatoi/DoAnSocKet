# Test evidence ledger

Records below only claim checks that were actually run. Loopback evidence does not replace the required two-computer LAN test.

## TV1 local verification (2026-11-15–16, macOS)

| Test / command | Expected | Actual | Status |
| --- | --- | --- | --- |
| `python3 -m compileall -q lanchat examples/milestone_01 tests` | All Python files compile | Exit 0 | PASS |
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` (network permitted) | CLI, registry, UDP tests pass | 9 tests, OK; includes real heartbeat and expiry waits | PASS |
| Sender/receiver in two local processes | Datagram arrives, Ctrl+C stops receiver | `Hello from UDP sender` received from `192.168.1.4`; receiver printed `Stopped` | PASS |
| Three separate local discovery processes | Each lists other two peers | Processes 0, 1, 2 each listed the other two | PASS |
| Three TV1 demo pseudo-terminals | A/B/C appear; partial `/li` survives C's online notice; `/status away` reaches B; `/quit` exits | B completed `/list` after typing `st` and saw A/C; B then saw A `away`; all three exited 0 | PASS (local PTY) |
| Same tests in restricted sandbox | Socket bind works | `PermissionError: Operation not permitted` on UDP bind; rerun with network permission passed | BLOCKED in sandbox |
| Two physical computers / Wireshark | Cross-host discovery and packet evidence | Not performed | NOT RUN |
| Full TV2/TV3 integration | Chat, file, unread and progress connected in app | Backend modules are placeholders; prompt-buffer and local PTY redraw passed for TV1 notifications | NOT RUN |

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
