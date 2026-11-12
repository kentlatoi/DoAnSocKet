# LAN Chat & File Sharing — Socket Programming

## Project Overview

This HCMUS Computer Networking project will build a peer-to-peer (P2P) LAN chat and file-sharing application. Each peer will both accept and initiate connections. The planned implementation uses Python 3 and its native `socket` API: UDP for peer discovery and presence, and TCP for messages and file transfer. The assignment develops practical understanding of TCP and UDP, concurrent programming, application-layer protocols, error handling, and LAN verification.

## Planned Features

**All application features are planned and not implemented yet.**

- UDP discovery, periodic heartbeat, and online/away status.
- Bidirectional TCP chat with multiple concurrent peers.
- Per-peer chat history and unread notifications.
- TCP file transfer with percentage progress while chat remains responsive.
- CLI that preserves typed input when messages arrive.
- Connection and file error handling, plus safe shutdown.

## Project Structure

```text
DoAnSocKet/
├── lanchat/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   ├── discovery.py
│   ├── peer_registry.py
│   ├── connections.py
│   ├── protocol.py
│   ├── chat.py
│   ├── transfer.py
│   └── cli.py
├── examples/
│   └── milestone_01/
│       ├── .gitkeep
│       ├── tcp_echo_server.py
│       ├── tcp_echo_client.py
│       ├── udp_receiver.py
│       └── udp_sender.py
├── tests/
│   ├── .gitkeep
│   ├── test_discovery.py
│   ├── test_protocol.py
│   ├── test_connections.py
│   ├── test_chat.py
│   └── test_transfer.py
├── docs/
│   ├── architecture.md
│   ├── protocol_spec.md
│   ├── requirements_matrix.md
│   ├── test_evidence.md
│   └── report/
│       └── .gitkeep
├── .gitignore
├── README.md
└── pyproject.toml
```

`lanchat/` contains docstring/TODO placeholders for the future application. `examples/milestone_01/` holds independent learning exercise placeholders; `tests/` holds test-scope placeholders, not passing tests. `docs/` records the architecture, open protocol decisions, historical R01–R39 requirements, and future evidence. `docs/report/` is reserved for the final report. `.gitignore` excludes local artifacts, and `pyproject.toml` defines minimal project metadata. The two extra `.gitkeep` files preserve directories from the initial scaffold.

## Team Responsibilities

| Member | GitHub | Responsibility |
| --- | --- | --- |
| Member 1 | [@kentlatoi](https://github.com/kentlatoi) | UDP Discovery, Peer State & Responsive CLI |
| Member 2 | [@thanhhuong107](https://github.com/thanhhuong107) | TCP Chat, Connections & Application Protocol |
| Member 3 | [@phkhoiit-1508](https://github.com/phkhoiit-1508) | File Transfer, Error Handling & Integration |

All members share testing, documentation, code review, Wireshark evidence, and oral-defense preparation.

## Development Milestones

These are the official assignment checkpoints; none is complete.

1. **M1 — TCP Echo and UDP Send/Receive:** demonstrate both learning exercises.
2. **M2 — UDP Discovery and Online Status:** show peers appearing and disappearing on at least two machines.
3. **M3 — TCP Chat and Protocol Framing:** demonstrate two-way chat, `/chat`, `/leave`, and concurrent receiving.
4. **M4 — Responsive CLI and File Transfer:** preserve typed input and transfer a file while chatting.
5. **M5 — Testing, Error Handling, Report and Demo:** complete fault handling, Wireshark evidence, report, and live demo.

## Getting Started

Install Python 3.10 or newer, then clone the repository and create a virtual environment:

```sh
git clone https://github.com/kentlatoi/DoAnSocKet.git
cd DoAnSocKet
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate`. No third-party runtime dependencies are declared. Application run instructions will be added when the entry point is implemented and verified.

## Testing Plan

Future checks will cover unit behavior, localhost and multi-process runs, two-computer LAN operation, Wireshark UDP/TCP evidence, and failure cases. Results will be recorded in `docs/test_evidence.md`; placeholder test files do not establish passing results.

## Collaboration

Use **feature branch → small commits → Pull Request → review → merge to `main`**. Planned branches are `feat/udp-discovery`, `feat/tcp-chat`, and `feat/file-cli`; create them from the latest merged `main` when work begins.

## Project Status

**Phase 0 — Repository Structure Setup.** The repository contains documentation and placeholders only. Official application requirements remain **Unverified**, no milestone is complete, and no application or network tests have been run.
