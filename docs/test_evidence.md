# Test evidence ledger

Records below only claim checks that were actually run. Loopback evidence does not replace the required two-computer LAN test.

## Final demo QA — 2026-11-18, macOS

| Check | Actual result | Status |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` on merged `main` with socket access | 32 tests, OK, 25.240 s | PASS |
| `python3 -m unittest discover -s tests -p 'test_*.py' -q` on QA branch with socket access | 34 tests, OK, 26.635 s | PASS |
| `python3 -m unittest tests.test_chat tests.test_integration -v` after QA changes | 7 tests, OK, 2.634 s; includes three real TCP peers, unread switch and interrupted `.part` cleanup | PASS |
| Two real `python3 -m lanchat` processes in pseudo-terminals, common UDP port 19199 | Both discovered each other; `/li` survived incoming chat notice, completed `/list` showed Bob; switching chat showed unread; both `/quit` exited | PASS (local PTY smoke) |
| Official assignment PDF and submitted final PDF | Both have 5 pages; report PDF text includes UDP, TCP, file transfer, thread, SHA-256 and tests | PASS (content inspection) |
| Physical two-computer LAN, Windows and genuine Wireshark | Not available in this run | NOT RUN |
| Two real application processes in pseudo-terminals, common UDP port 19201, 8 MiB file | Partial `/li` survived receiving progress and completion notices; completing `/list` showed Bob; receiver bytes matched source; both processes quit | PASS (local PTY smoke) |

An earlier file-progress PTY script timed out because it waited for the file-completion notice *after* checking `/list`, although the transfer had already completed. The corrected script checked completion before finishing `/list` and passed. This was a test-order error, not a confirmed application failure.

The QA changes to TV2 `ChatManager.select_peer` correct unread display when an outgoing message follows an unread incoming message. TV2 owner review is requested. The untracked `demo_file.bin` was preserved and is not part of test evidence.

## TV3 verification — 2026-11-18, macOS

| Check | Actual result | Status |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -p 'test_*.py' -q` with local socket permission | 32 tests, OK, about 22 seconds | PASS |
| Same command in restricted sandbox | Socket `bind` raised `PermissionError`; unrelated tests continued | BLOCKED in sandbox |
| `tests/test_transfer.py` | Text, binary >64 KiB, Unicode, empty, collision, bad path, unexpected chunk, checksum mismatch, partial cleanup passed | PASS |
| `tests/test_integration.py` | Real loopback TCP app startup, shared identity and port, wrong ID rejection, bidirectional chat, file save/integrity, chat during transfer, leave passed | PASS |
| Physical two-computer LAN and Windows | Not run | NOT RUN |
| Integrated PTY redraw with chat/file notifications | Not run; prior TV1 PTY check covers discovery notice only | NOT RUN |
| Genuine UDP broadcast and TCP handshake Wireshark screenshots | Not captured | NOT RUN |
| Final report PDF generation | `docs/FINAL_REPORT.pdf` rendered from editable Markdown; PDFKit reports five pages | PASS (artifact generation) |

The integration test manually seeds a discovered peer and exercises real TCP sockets; it does not prove cross-host broadcast delivery. A separate three-instance discovery test exists in the TV1 suite.

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
