# LAN Chat & File Sharing — Socket Programming

**Project status: Phase 0 — Repository Structure Setup.** Official application requirements are **UNVERIFIED**. No official milestone is complete.

## About the Project

This HCMUS Computer Networking assignment will build a peer-to-peer (P2P) LAN application. Each instance will discover nearby peers, accept connections, and initiate conversations and file transfers. This repository currently contains only project scaffolding and planning documents.

## Project Objectives

The team will learn the difference between TCP's reliable byte stream and UDP's datagrams; use Python's native socket API; build peer-to-peer networking with concurrent workers; design application-layer framing; handle failures; and verify behavior on a real LAN. Each of the three members should be able to explain the complete design and code during the oral defense.

## Planned features

All features below are **planned; none is implemented**:

- UDP peer discovery and online/away presence.
- Bidirectional TCP chat with multiple concurrent peers.
- Per-peer message history and unread counts.
- TCP file transfer with progress while chat remains responsive.
- Responsive CLI input, failure handling, and safe shutdown.
- Wireshark verification of UDP broadcast and the TCP handshake.

## Technology Stack

Python 3, the native `socket` API, `threading`, and appropriate standard-library tools are planned. No third-party runtime package is declared.

## Architecture Overview

Every peer will listen and connect. UDP will carry discovery, presence, and online/away status; TCP will carry bidirectional chat and file transfers. Concurrent workers will keep discovery, peer connections, transfers, and CLI input responsive. A team-designed application-layer protocol must frame TCP messages. The exact protocol and worker design remain open. A fully functional CLI comes before any optional GUI.

## Complete Project Structure

```text
DoAnSocKet/
│
├── lanchat/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── config.py
│   │
│   ├── discovery.py
│   ├── peer_registry.py
│   │
│   ├── connections.py
│   ├── protocol.py
│   ├── chat.py
│   │
│   ├── transfer.py
│   └── cli.py
│
├── examples/
│   └── milestone_01/
│       ├── tcp_echo_server.py
│       ├── tcp_echo_client.py
│       ├── udp_receiver.py
│       └── udp_sender.py
│
├── tests/
│   ├── test_discovery.py
│   ├── test_protocol.py
│   ├── test_connections.py
│   ├── test_chat.py
│   └── test_transfer.py
│
├── docs/
│   ├── architecture.md
│   ├── protocol_spec.md
│   ├── requirements_matrix.md
│   ├── test_evidence.md
│   └── report/
│       └── .gitkeep
│
├── .gitignore
├── README.md
└── pyproject.toml
```

The earlier scaffold also contains preserved `.gitkeep` markers in `examples/milestone_01/` and `tests/`.

| Path | Purpose |
| --- | --- |
| `lanchat/__init__.py` | Package initialization. |
| `lanchat/__main__.py` | Safe placeholder for the future launch entry point. |
| `lanchat/app.py` | Future application coordination and shutdown. |
| `lanchat/config.py` | Future ports, timings, and download settings. |
| `lanchat/discovery.py` | Future UDP broadcast, listening, and presence. |
| `lanchat/peer_registry.py` | Future peer records, last-seen times, expiration, and synchronized state. |
| `lanchat/connections.py` | Future TCP listening, connecting, concurrent peers, and disconnects. |
| `lanchat/protocol.py` | Future framing, byte lengths, encoding, exact reads, and validation. |
| `lanchat/chat.py` | Future messages, conversation histories, and unread counts. |
| `lanchat/transfer.py` | Future TCP file transfer, progress, downloads, and partial-file cleanup. |
| `lanchat/cli.py` | Future chat text and `/list`, `/chat`, `/send`, `/leave`, `/status`, `/help`, `/quit` commands; input preservation. |
| `examples/milestone_01/tcp_echo_server.py` | TCP echo server learning placeholder. |
| `examples/milestone_01/tcp_echo_client.py` | TCP echo client learning placeholder. |
| `examples/milestone_01/udp_receiver.py` | UDP receive learning placeholder. |
| `examples/milestone_01/udp_sender.py` | UDP send learning placeholder. |
| `tests/test_discovery.py` | Future presence, heartbeat, expiry, and status tests. |
| `tests/test_protocol.py` | Future framing, partial-read, UTF-8, and malformed-input tests. |
| `tests/test_connections.py` | Future lifecycle, multi-peer, and cleanup tests. |
| `tests/test_chat.py` | Future messaging, history, unread, and concurrent-receive tests. |
| `tests/test_transfer.py` | Future integrity, progress, interruption, and concurrent-chat tests. |
| `docs/architecture.md` | Constraints, proposed boundaries, open decisions. |
| `docs/protocol_spec.md` | Framing requirement and protocol design questions. |
| `docs/requirements_matrix.md` | Historical R01–R39 requirement tracking. |
| `docs/test_evidence.md` | Blank evidence record template. |
| `docs/report/` | Reserved for the final report. |
| `docs/report/.gitkeep` | Retains the report directory in Git. |
| `.gitignore` | Excludes local caches, secrets, and runtime artifacts. |
| `README.md` | Project guide and structure inventory. |
| `pyproject.toml` | Minimal Python project metadata. |

## Development Milestones

These are the **official checkpoints, not completed work**:

1. Demonstrate TCP echo client/server and UDP send/receive exercises.
2. Demonstrate UDP discovery, online list, `/list`, and `/status` with peers appearing and disappearing on at least two machines.
3. Demonstrate framed, concurrent TCP chat using `/chat` and `/leave` in both directions.
4. Demonstrate preserved CLI input while receiving and file transfer progress while chatting.
5. Complete error handling, testing, report, and final demo.

The intended development order is core networking, fully functional CLI, testing, documentation, then an optional GUI.

## Installation and Setup

Clone and enter the repository:

```sh
git clone https://github.com/kentlatoi/DoAnSocKet.git
cd DoAnSocKet
```

Prepare an isolated Python environment for later development:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate`. No third-party runtime dependencies or working chat command are provided at Phase 0. Application run instructions will be added after implementation.

Install a suitable Python 3 version (the project metadata currently declares Python 3.10 or newer) before creating the environment. There are no declared runtime dependencies to install yet.

## How to Run

Application execution instructions will be added after the application is implemented and verified. The current Python files are learning and design placeholders.

## Testing

Tests will be developed with each milestone: unit tests, localhost tests, multiple local processes, physical two-computer LAN tests, Wireshark packet verification, and fault handling tests. The team will record the machine, environment, steps, expected and actual results, and evidence in `docs/test_evidence.md`. Loopback checks and real LAN checks will be identified separately. **The test files are placeholders; no application tests have been run by this setup task.**

## Team Responsibilities

| Member | Responsibility |
| --- | --- |
| Member 1 — name/ID to be added | UDP Discovery & Peer State |
| Member 2 — name/ID to be added | TCP Chat & Application Protocol |
| Member 3 — name/ID to be added | File Transfer & CLI |

All members share architecture, integration, testing, documentation, Wireshark evidence, and oral-defense preparation. Each member should understand every subsystem.

## Git Workflow

Proposed branches: `feat/udp-discovery`, `feat/tcp-chat`, and `feat/file-cli`. For each feature, create its branch, write and understand the code, make small commits, open a Pull Request, obtain code review, and merge to `main` after verification. These branches have not been created.

## Project Status

**Phase 0 — Repository Structure Setup.** Official application requirements are **UNVERIFIED**. No official milestone has been completed.

## Academic Information

HCMUS — Computer Networking, Socket Programming Project. The official assignment PDF is retained outside this repository in the local reference directory; the documentation here summarizes its requirements without reproducing it.
