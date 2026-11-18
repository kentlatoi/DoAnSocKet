# LAN Chat & File Sharing

Python 3 peer-to-peer LAN chat. UDP broadcasts presence; TCP carries framed chat messages and files. Each instance listens and can connect to other peers. The terminal uses `prompt_toolkit` to preserve partially typed input when notifications arrive.

## Install

Requires Python 3.10+ and `prompt_toolkit` 3.x.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows activate with `.venv\Scripts\activate` and use `python` in place of `python3`. Windows operation has not been verified.

## Run

On two LAN computers, run the same command with distinct names. TCP port `0` selects a free port and advertises the actual value. The UDP port must match on all peers (default 9999).

```sh
python3 -m lanchat --name Quan --port 5001
python3 -m lanchat --name Minh --port 5002
```

A third peer can use `--name Lan --port 5003`. Multiple local instances require OS support for UDP port sharing. Received files appear in `downloads/` relative to the process working directory. Existing names receive a numbered suffix and are never overwritten.

| Command | Action |
| --- | --- |
| `/list` | Show discovered peers |
| `/chat <name\|number>` | Select and connect to a peer |
| ordinary text | Send to selected peer |
| `/send <file>` | Send a file to selected peer |
| `/leave` | Leave the conversation; retain TCP connections |
| `/status <online\|away>` | Change UDP presence |
| `/help` | Show commands |
| `/quit` | Stop networking and exit |

Legacy UDP peers without a peer ID appear in `/list`, but verified TCP chat with them is refused. File sending uses 64 KiB frames, a worker thread, SHA-256 verification and receiver acknowledgement. See [protocol specification](docs/protocol_spec.md).

## Test and troubleshoot

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m compileall -q lanchat examples/milestone_01 tests
```

Tests that bind sockets need local network permission. If peers do not appear, confirm that both machines use the same UDP port and LAN, allow Python through the firewall, and check whether the network permits broadcasts. A stale peer may remain listed for up to ten seconds. If TCP connect fails, confirm the advertised port is reachable. A sender reports verified completion only after the receiver saves and acknowledges the file; failure or interruption removes the `.part` file.

## Milestone echo example

In separate terminals:

```sh
python3 examples/milestone_01/tcp_echo_server.py --host 127.0.0.1 --port 19090 --once
python3 examples/milestone_01/tcp_echo_client.py --port 19090 'Xin chào'
```

## Remaining validation

The automated suite covers local sockets. A two-computer LAN run, Windows run, terminal redraw during integrated chat/file events, and genuine Wireshark screenshots remain to be completed. See [test evidence](docs/test_evidence.md) and [demo script](docs/FINAL_DEMO_SCRIPT.md).
