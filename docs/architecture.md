# Architecture baseline

**Status:** Phase 0 planning. No application architecture has been implemented.

## Official constraints

The assignment requires the same application to act as both listener and connector. UDP carries discovery and presence, including a common port, three-second broadcasts, online/away state, and removal after ten seconds without a presence message. TCP carries bidirectional chat and file transfer. The application must support multiple peers, per-peer history and unread notices, continued chat during transfer, responsive CLI input, synchronization of shared state and output, and graceful handling of network and file failures. TCP messages require framing and exact-byte receive loops. See the official assignment PDF, pages 1–4, and the historical mapping in `requirements_matrix.md`.

## Approved technical direction

- Python 3 and the native `socket` API.
- P2P peers; UDP discovery/status and TCP chat/files.
- Core networking → fully functional CLI → testing → documentation → optional GUI.
- Three members who each understand the integrated application for oral defense.

## Proposed module boundaries

These modules are present as **docstring and TODO placeholders only**. Their proposed boundaries remain subject to later design and implementation.

| Future module | Proposed responsibility |
| --- | --- |
| `protocol.py` | Datagram and TCP frame formats, encoding, bounds, validation, exact reads. |
| `config.py` | TCP/UDP ports, heartbeat, timeout, and downloads path settings. |
| `discovery.py` | UDP broadcast, receive, timeout, presence events. |
| `peer_registry.py` | Synchronized peer identity, status, history, unread counts. |
| `connections.py` | TCP listen/connect, peer connections, lifecycle. |
| `chat.py` | Chat delivery and history events. |
| `transfer.py` | File transfer, progress, received-file cleanup. |
| `cli.py` | Commands, current peer, responsive input/output. |
| `app.py` | Composition and shutdown of application components. |

## Open decisions

- Peer identity, duplicate names, restart behavior, and simultaneous connections.
- Wire schema, version, maximum frame sizes, invalid-message policy, and acknowledgements.
- Shared TCP connection or a separate stream for files; flow control during transfer.
- Standard-library manual CLI redraw or an optional input library; cross-platform behavior.
- Broadcast interface selection, firewall guidance, and local multi-instance behavior.
- Filename collisions, integrity, cancellation, zero-byte files, and interrupted-file cleanup.
- In-memory or persistent history, and shutdown ordering.

These choices require explicit design and testing during later milestones.
