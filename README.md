# LAN Chat & File Sharing

Peer-to-peer chat and file sharing for computers on the same local network, developed for the **Computer Networking** course at the **Faculty of Information Technology, University of Science, Vietnam National University Ho Chi Minh City (HCMUS)**.

Each running instance is both a client and a server. Peers advertise their presence through UDP broadcast, then establish direct TCP connections for framed chat messages and file transfers. The project is implemented with Python's native socket API and provides both command-line and Tkinter interfaces.

## Team Members

| Member | Full name | Student ID |
| --- | --- | --- |
| Member 1 | Nguyễn Trần Minh Khang | 25127369 |
| Member 2 | Nguyễn Ngọc Thanh Hương | 25127197 |
| Member 3 | Phạm Hùng Khôi | 25127390 |

## Key Features

- Automatic peer discovery through UDP broadcast on a shared port.
- Presence heartbeats, peer timeout detection, and `online`/`away` synchronization.
- Concurrent TCP connections to multiple peers with duplicate-connection resolution.
- Bidirectional UTF-8 messaging, per-peer in-memory history, and unread counters.
- File transfer on the existing TCP connection with send/receive progress notices.
- Chat frames can be exchanged while a file transfer is in progress.
- Receiver-side byte-count and SHA-256 verification with acknowledgement to the sender.
- Collision-safe received filenames and cleanup of interrupted `.part` files.
- Responsive CLI based on `prompt_toolkit`, preserving partially typed input when asynchronous notices arrive.
- Tkinter GUI for peer selection, chat, status changes, file selection, and transfer progress.
- Input validation, connection error reporting, and coordinated shutdown of sockets and worker threads.

## System Architecture

```text
                           one LAN Chat peer
┌─────────────────────────────────────────────────────────────────┐
│ CLI (prompt_toolkit)                 GUI (Tkinter event queue)   │
│              └──────────────┬──────────────┘                     │
│                         Application                              │
│          ┌──────────────┬───┴───────────┬──────────────┐         │
│   UDP Discovery   Peer Registry   Chat Manager   Transfer Manager│
│          │              │              └──────┬───────┘         │
│          │      thread-safe snapshots     Connection Manager     │
│          │                                  framed TCP streams   │
└──────────┼────────────────────────────────────────┼──────────────┘
           │ UDP broadcast                          │ TCP
           └──────────────── other LAN peers ───────┘
```

- `Discovery` broadcasts presence, listens for other peers, and expires stale registry entries.
- `PeerRegistry` stores synchronized snapshots of discovered endpoints and their current status.
- `ConnectionManager` listens for and initiates TCP connections, exchanges identity `HELLO` frames, keeps one stream per peer pair, and dispatches received frames.
- `ChatManager` owns per-peer histories, the selected conversation, and unread counts.
- `TransferManager` streams files in a worker thread, reports progress, validates incoming files, and handles acknowledgement or cleanup.
- `Application` composes these services and routes events to either the CLI or GUI.

Discovery uses three worker threads for broadcast, receive, and expiration. TCP uses an accept thread, short-lived handshake workers, and one receive worker per active connection. File sending uses a separate worker so chat remains responsive. Shared registries, histories, transfer maps, connection maps, and output paths are protected by `Lock` or `RLock`; each TCP connection also has its own send lock so concurrent frames cannot interleave.

For additional detail, see [Architecture](docs/architecture.md) and the [Protocol Specification](docs/protocol_spec.md).

## Project Structure

```text
.
├── lanchat/
│   ├── __main__.py          # command-line entry point and arguments
│   ├── app.py               # component composition and lifecycle
│   ├── chat.py              # histories, selected chat, and unread state
│   ├── cli.py               # responsive command-line interface
│   ├── config.py            # discovery timing and port defaults
│   ├── connections.py       # multi-peer TCP connection management
│   ├── discovery.py         # UDP presence broadcast and peer expiry
│   ├── gui.py               # Tkinter graphical interface
│   ├── peer_registry.py     # thread-safe discovered-peer state
│   ├── protocol.py          # TCP framing and JSON helpers
│   └── transfer.py          # file streaming and integrity checks
├── tests/                   # unittest unit and loopback integration tests
├── docs/
│   ├── architecture.md
│   ├── protocol_spec.md
│   ├── requirements_matrix.md
│   ├── test_evidence.md
│   ├── TWO_COMPUTER_ACCEPTANCE.md
│   └── FINAL_DEMO_SCRIPT.md
├── examples/milestone_01/   # introductory UDP and TCP socket examples
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Requirements and Installation

- Python 3.10 or later.
- `prompt-toolkit==3.0.52`, installed from `requirements.txt`.
- Tkinter from the selected Python distribution for GUI mode. Tkinter is not required for CLI mode.
- Two computers on the same IPv4 LAN for the intended cross-host demonstration.

Clone and create an isolated environment:

```bash
git clone https://github.com/kentlatoi/DoAnSocKet.git
cd DoAnSocKet
python3 -m venv .venv
```

Activate it on macOS or Linux, then install the dependency:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Check GUI support with:

```bash
python -m tkinter
```

A small Tk test window should open. If the module is unavailable, install a Python distribution that includes Tkinter or the matching Tk package for the current interpreter. Recreate the virtual environment with that interpreter afterward.

## Running the Application

The following are **operating-system terminal commands**. Connect both computers to the same LAN and use the same UDP discovery port. Names and TCP ports must be distinct.

Computer A — Alice, CLI, TCP port 5001:

```bash
python -m lanchat --name Alice --port 5001
```

Computer B — Bob, CLI, TCP port 5002:

```bash
python -m lanchat --name Bob --port 5002
```

To use the GUI, add `--gui`:

```bash
python -m lanchat --gui --name Alice --port 5001
python -m lanchat --gui --name Bob --port 5002
```

The default discovery port is UDP 9999. Override it only when every peer uses the same value:

```bash
python -m lanchat --name Alice --port 5001 --udp-port 23001
```

TCP port `0` asks the operating system for a free port, which the application then advertises. Local firewall rules must allow inbound UDP on the discovery port and inbound TCP on each peer's advertised port. Guest Wi-Fi, access-point client isolation, VPNs, or disabled broadcast forwarding can prevent discovery.

## Usage

After starting CLI mode, enter these commands at the LAN Chat `> ` prompt; they are not shell commands.

| CLI input | Purpose |
| --- | --- |
| `/list` | List discovered peers with address, TCP port, and status. |
| `/chat <name\|number>` | Select a uniquely named peer or its number from `/list`, connecting if needed. |
| `<message text>` | Send non-empty text to the selected peer. |
| `/send <file>` | Send a regular file path to the selected peer. The full remaining text is used as the path. |
| `/leave` | Clear the selected conversation while retaining established TCP connections. |
| `/status online` | Advertise `online` status immediately. |
| `/status away` | Advertise `away` status immediately. |
| `/help` | Display the supported command summary. |
| `/quit` | Stop networking and exit. |

In GUI mode, select a peer in the left panel; the application connects and displays that conversation. Enter text and press Enter or **Send**, use the status selector for `online` or `away`, and choose **Send file…** to select a local file. The bottom progress bar and notice area show transfer progress, completion, or errors.

Received files are stored in `downloads/` relative to the directory from which the application was launched. Existing files are not overwritten: a numbered suffix such as `document (1).pdf` is used instead.

## Network Protocol

UDP presence is a UTF-8 datagram of at most 512 bytes:

```text
HELLO|name|tcp_port|status|peer_id
```

The default destination is broadcast address `255.255.255.255`, UDP port `9999`. `status` is `online` or `away`. A datagram is sent immediately at startup, every 3 seconds, and immediately after a status change. A peer is removed after 10 seconds without a valid update. A legacy four-field packet without `peer_id` can be listed but cannot be used for identity-verified chat.

Selecting a peer opens TCP to its advertised endpoint. Both sides exchange a framed JSON `HELLO` containing `peer_id` and `name`; the initiator verifies the discovered ID. Simultaneous duplicate connections are resolved deterministically by peer ID.

Every TCP application frame has a 10-byte network-byte-order header followed by its payload:

| Field | Size | Value |
| --- | ---: | --- |
| Magic | 4 bytes | ASCII `LCHT` |
| Version | 1 byte | `1` |
| Message type | 1 byte | `HELLO`, `CHAT`, `FILE_META`, `FILE_CHUNK`, `FILE_END`, `LEAVE`, or `ERROR` |
| Payload length | 4 bytes | Unsigned big-endian byte count, maximum 8 MiB |

Chat and metadata payloads are compact UTF-8 JSON objects. File data is sent as raw `FILE_CHUNK` payloads of up to 64 KiB. The sender finishes with a SHA-256 digest; the receiver checks both declared size and digest before assigning an unused destination name and acknowledging success. The sender reports verified completion only after receiving that acknowledgement, with a 30-second acknowledgement timeout.

The complete field definitions and validation rules are in the [Protocol Specification](docs/protocol_spec.md).

## Testing and Demonstration

With the project virtual environment active, run the automated suite from the repository root:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

The suite covers protocol framing and validation, UDP lifecycle, peer state, TCP connection management, chat/unread behavior, file transfer and cleanup, CLI behavior, GUI event handling, and real loopback TCP integration. It does not replace testing on two physical computers.

For a manual LAN demonstration:

1. Start Alice and Bob on two computers, then use `/list` and `/status away`/`online` to demonstrate discovery and status propagation.
2. Select each peer with `/chat`, exchange messages in both directions, and show unread messages by sending from a non-selected conversation.
3. Use `/send <file>` and continue chatting during the transfer; confirm progress and verified completion.
4. Compare the source and received SHA-256 values with `shasum -a 256 <file>` on macOS/Linux or `Get-FileHash <file> -Algorithm SHA256` in PowerShell.
5. Repeat the main flow in the Tkinter GUI.

Capture on the active LAN interface in Wireshark. Useful display filters for the example ports are:

```text
udp.port == 9999
tcp.port == 5001 || tcp.port == 5002
tcp.port == 5002 && (tcp.flags.syn == 1 || tcp.flags.ack == 1)
```

Use the UDP filter to identify a broadcast presence datagram. For the TCP three-way handshake, follow one TCP stream and identify the consecutive SYN, SYN-ACK, and ACK packets. If different ports are selected, substitute the actual startup values. See the [Two-Computer Acceptance Checklist](docs/TWO_COMPUTER_ACCEPTANCE.md) and [Final Demo Script](docs/FINAL_DEMO_SCRIPT.md).

## Troubleshooting

- **Peers are not discovered:** verify the same UDP port, same IPv4 LAN, firewall permission, correct network interface, and absence of guest-network/client isolation. Wait at least one heartbeat interval.
- **TCP connection fails:** confirm the peer is still listed, its advertised TCP port is reachable, and inbound TCP is allowed. A stale entry can remain for up to 10 seconds.
- **Dependencies cannot be installed:** confirm Python 3.10+ and an active virtual environment, then run `python -m pip install -r requirements.txt` again.
- **Tkinter is unavailable:** use CLI mode or install a Python/Tk distribution pair that provides `_tkinter`; verify it with `python -m tkinter` before starting `--gui`.

## Verification Scope

The repository does not contain the instructor's original assignment file. [Requirements Matrix](docs/requirements_matrix.md) records the project's existing interpretation, but it is not a newly verified transcription of the original brief. Current repository evidence also distinguishes automated/local loopback checks from physical two-computer, Windows, and genuine Wireshark validation; consult [Test Evidence](docs/test_evidence.md) for that boundary.
