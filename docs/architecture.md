# Architecture baseline

**Status:** Phase 0 baseline with the TCP/protocol/chat slice implemented for team review.

## Official constraints

The assignment requires the same application to act as both listener and connector. UDP carries discovery and presence, including a common port, three-second broadcasts, online/away state, and removal after ten seconds without a presence message. TCP carries bidirectional chat and file transfer. The application must support multiple peers, per-peer history and unread notices, continued chat during transfer, responsive CLI input, synchronization of shared state and output, and graceful handling of network and file failures. TCP messages require framing and exact-byte receive loops. See the official assignment PDF, pages 1–4, and the historical mapping in `requirements_matrix.md`.

## Approved technical direction

- Python 3 and the native `socket` API.
- P2P peers; UDP discovery/status and TCP chat/files.
- Core networking → fully functional CLI → testing → documentation → optional GUI.
- Three members who each understand the integrated application for oral defense.

## Proposed module boundaries

The TCP slice now has concrete interfaces; the remaining module boundaries are still subject to integration review.

| Future module | Proposed responsibility |
| --- | --- |
| `protocol.py` | Implemented TCP frame format, UTF-8 JSON helpers, bounds, validation, exact reads. |
| `config.py` | TCP/UDP ports, heartbeat, timeout, and downloads path settings. |
| `discovery.py` | UDP broadcast, receive, timeout, presence events. |
| `peer_registry.py` | Synchronized peer identity, status, history, unread counts. |
| `connections.py` | Implemented TCP listen/connect, HELLO handshake, duplicate resolution, multi-peer lifecycle and handler dispatch. |
| `chat.py` | Implemented chat delivery, per-peer history, current conversation, unread counts and events. |
| `transfer.py` | File transfer, progress, received-file cleanup. |
| `cli.py` | Commands, current peer, responsive input/output. |
| `app.py` | Composition and shutdown of application components. |

## Open decisions

- How TV1 persists/generates the non-empty `peer_id`; duplicate display names remain allowed because routing uses ID.
- File acknowledgements and integrity policy beyond the v1 frame types.
- Shared TCP connection or a separate stream for files; flow control during transfer.
- Standard-library manual CLI redraw or an optional input library; cross-platform behavior.
- Broadcast interface selection, firewall guidance, and local multi-instance behavior.
- Filename collisions, integrity, cancellation, zero-byte files, and interrupted-file cleanup.
- In-memory or persistent history, and shutdown ordering.

These choices require explicit design and testing during later milestones.

## TCP connection model

`ConnectionManager` owns one listener thread, short-lived handshake workers, and one receive worker per active peer. `start()` binds/listens and exposes the selected TCP port to discovery. `connect(ip, port)` uses the registry endpoint, exchanges `HELLO` identity frames, and registers the stream. Message handlers let chat and transfer receive their own types without coupling those modules.

All connection maps and handler lists use a re-entrant lock. Every stream has a separate send lock so concurrent chat and file workers cannot interleave bytes inside a frame. The receive worker converts close, reset, partial frame, and invalid frame conditions into removal plus a disconnect event. `stop()` closes the listener and all peer sockets, which wakes blocked `accept()`/`recv()` calls before workers are joined.

Simultaneous outgoing connections are resolved by peer ID: the lower ID keeps outgoing and the higher ID keeps incoming. Replacing the non-preferred stream does not emit a false disconnect event.

## Chat state model

`ChatManager` registers one message handler and only consumes `CHAT` frames. Histories and unread counters are keyed by peer ID and protected by a lock. Incoming messages for the selected peer are immediately visible with unread count zero; other conversations accumulate unread counts. Selecting a peer returns the unread messages and resets only that peer's counter. Switching conversations never closes TCP connections.
