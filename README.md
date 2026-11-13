# LAN Chat & File Sharing — Socket Programming

## Project Overview

This HCMUS Computer Networking project will build a peer-to-peer (P2P) LAN chat and file-sharing application. Each peer will both accept and initiate connections. The planned implementation uses Python 3 and its native `socket` API: UDP for peer discovery and presence, and TCP for messages and file transfer. The assignment develops practical understanding of TCP and UDP, concurrent programming, application-layer protocols, error handling, and LAN verification.

## Planned Features

The TCP protocol, connection manager, and chat-state slice are implemented on the TV2 feature branch. Discovery, CLI, file transfer, and full application integration remain planned until their feature branches are merged.

- UDP discovery, periodic heartbeat, and online/away status.
- Bidirectional TCP chat transport with multiple concurrent peers. **Implemented and unit-tested on loopback.**
- Per-peer chat history and unread notifications. **Implemented and unit-tested.**
- TCP file transfer with percentage progress while chat remains responsive.
- CLI that preserves typed input when messages arrive.
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

On Windows, activate with `.venv\Scripts\activate`. No third-party runtime dependencies are declared. Run all current standard-library tests with:

```sh
python -m unittest discover -s tests -v
```

Run the Milestone 1 TCP echo server with:

```sh
python examples/milestone_01/tcp_echo_server.py --host 0.0.0.0 --port 9000
```

Application run instructions will be added when the integration entry point is implemented and verified.

## Testing Plan

Future checks will cover unit behavior, localhost and multi-process runs, two-computer LAN operation, Wireshark UDP/TCP evidence, and failure cases. Results will be recorded in `docs/test_evidence.md`; placeholder test files do not establish passing results.

## Collaboration

Use **feature branch → small commits → Pull Request → review → merge to `main`**. Planned branches are `feat/udp-discovery`, `feat/tcp-chat`, and `feat/file-cli`; create them from the latest merged `main` when work begins.

## Project Status

**TCP Chat feature development.** TV2's protocol, connection, chat-state, tests, technical documentation, and echo-server exercise are implemented. Automated loopback is development evidence only; final two-computer LAN and Wireshark verification are still required.
