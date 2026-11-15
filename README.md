# LAN Chat & File Sharing — Socket Programming

## Project Overview

This HCMUS Computer Networking project will build a peer-to-peer (P2P) LAN chat and file-sharing application. Each peer will both accept and initiate connections. The planned implementation uses Python 3 and its native `socket` API: UDP for peer discovery and presence, and TCP for messages and file transfer. The assignment develops practical understanding of TCP and UDP, concurrent programming, application-layer protocols, error handling, and LAN verification.

## Planned Features

**TV1 UDP discovery and CLI components are implemented; the full application is not integrated yet.**

- UDP discovery, periodic heartbeat, and online/away status (TV1 component implemented).
- Bidirectional TCP chat with multiple concurrent peers.
- Per-peer chat history and unread notifications.
- TCP file transfer with percentage progress while chat remains responsive.
- CLI that preserves typed input when messages arrive (TV1 component implemented; TCP/file callbacks pending).
- Connection and file error handling, plus safe shutdown.

## Project Structure


## Project Structure

```text
DoAnSocKet/
├── lanchat/                     # Main Python application
│   ├── __init__.py              # Python package initialization
│   ├── __main__.py              # Application entry point
│   ├── app.py                   # Application lifecycle and integration
│   ├── config.py                # Network ports and configuration
│   ├── discovery.py             # UDP discovery and heartbeat
│   ├── peer_registry.py         # Online peers, status and timeout
│   ├── connections.py           # TCP connection management
│   ├── protocol.py              # Message framing and encoding
│   ├── chat.py                  # Chat history and unread messages
│   ├── transfer.py              # File transfer and progress
│   └── cli.py                   # Commands and responsive terminal
│
├── examples/                    # Learning examples
│   └── milestone_01/
│       ├── .gitkeep             # Keep directory tracked by Git
│       ├── tcp_echo_server.py   # TCP echo server exercise
│       ├── tcp_echo_client.py   # TCP echo client exercise
│       ├── udp_receiver.py      # UDP receiver exercise
│       └── udp_sender.py        # UDP sender exercise
│
├── tests/                       # Automated tests
│   ├── .gitkeep                 # Directory placeholder
│   ├── test_discovery.py        # UDP discovery tests
│   ├── test_protocol.py         # Protocol and framing tests
│   ├── test_connections.py      # TCP connection tests
│   ├── test_chat.py             # Chat functionality tests
│   └── test_transfer.py         # File transfer tests
│
├── docs/                        # Technical documentation
│   ├── architecture.md          # System architecture
│   ├── protocol_spec.md         # Application protocol specification
│   ├── requirements_matrix.md   # Requirements tracking
│   ├── test_evidence.md         # Testing records and evidence
│   └── report/                  # Final project report
│       └── .gitkeep
│
├── .gitignore                   # Files excluded from Git
├── README.md                    # Project overview and instructions
└── pyproject.toml               # Python project configuration
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

On Windows, activate with `.venv\Scripts\activate`, then run `python -m pip install -e .`. The CLI uses `prompt_toolkit` only to preserve typed input during concurrent output; networking uses Python's `socket` module. Application run instructions await TV2/TV3 integration.

TV1 UDP examples: run `python examples/milestone_01/udp_receiver.py` in one terminal, then `python examples/milestone_01/udp_sender.py` in another. Stop the receiver with Ctrl+C. Run TV1 tests with `python -m unittest discover -s tests -p 'test_*.py' -v`. On this macOS test host, `255.255.255.255` worked for local broadcast, while `127.255.255.255` did not; real LAN behavior still needs two-computer verification.

For a TV1-only interactive demo, run `python -m examples.milestone_01.tv1_discovery_demo --name A --tcp-port 5001` and a second terminal with `--name B --tcp-port 5002`. Add `--name C --tcp-port 5003` for three peers. This does not open TCP listeners or transfer files.

The future application coordinator should create `PeerRegistry(on_event=...)`, `Discovery(name, tcp_port, registry, peer_id=shared_id)`, and `CLI(registry, discovery, on_chat=..., on_send=..., on_leave=..., on_text=..., on_quit=...)`. Use the **same** `shared_id` for TV2's `ConnectionManager`; alternatively use the generated `discovery.peer_id` when constructing that manager. `on_chat` receives a `Peer` with IP, TCP port and peer ID; `on_send` receives a file path; `on_text` receives a chat line. Feed UDP online/offline, TV2 unread, and TV3 progress messages to `CLI.notify(message)`. Start discovery before `CLI.run()` and call `Discovery.stop()` during shutdown. Until callbacks are connected, those commands report that the backend is unavailable.

## Testing Plan

Future checks will cover unit behavior, localhost and multi-process runs, two-computer LAN operation, Wireshark UDP/TCP evidence, and failure cases. Results will be recorded in `docs/test_evidence.md`; placeholder test files do not establish passing results.

## Collaboration

Use **feature branch → small commits → Pull Request → review → merge to `main`**. Planned branches are `feat/udp-discovery`, `feat/tcp-chat`, and `feat/file-cli`; create them from the latest merged `main` when work begins.

## Project Status

**Phase 0 — Repository Structure Setup.** The repository contains documentation and placeholders only. Official application requirements remain **Unverified**, no milestone is complete, and no application or network tests have been run.
