# LAN Chat & File Sharing

HCMUS Computer Networking project: a peer-to-peer LAN chat and file-sharing application using Python 3 and native UDP/TCP sockets.

## Current status

| Component | Status |
| --- | --- |
| UDP discovery, online/away presence, peer registry | Implemented and tested locally |
| Responsive CLI command handling | Implemented and tested locally |
| TCP connections, chat history/unread, protocol v1 | Implemented as modules and tested locally |
| File transfer, application coordinator and runnable chat entry point | Pending TV3 integration |
| Two-computer LAN demo and Wireshark evidence | Pending |

`python -m lanchat` still runs a placeholder entry point; it does not start the chat application. See [TV1/TV2 integration handoff](docs/TV1_TV2_INTEGRATION_HANDOFF.md) and [protocol specification](docs/protocol_spec.md).

## Install and test

Python 3.10 or newer is required. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -p 'test_*.py' -v
```

On Windows, activate with `.venv\Scripts\activate` and use `python` for the commands. Socket tests require permission to bind local ports. Multi-instance UDP tests skip when `SO_REUSEPORT` is unavailable; the required two-computer LAN demo remains a separate check.

## Independent network examples

Run each pair in separate terminals:

```sh
python examples/milestone_01/udp_receiver.py
python examples/milestone_01/udp_sender.py

python examples/milestone_01/tcp_echo_server.py --host 127.0.0.1 --port 19090 --once
```

For a discovery-only interactive demo, start two terminals with different names and TCP ports:

```sh
python -m examples.milestone_01.tv1_discovery_demo --name A --tcp-port 5001
python -m examples.milestone_01.tv1_discovery_demo --name B --tcp-port 5002
```

The TCP echo client exercise is still a placeholder; connect to the echo server with a TCP client. The discovery demo does not open TCP listeners or transfer files. On a real LAN, firewall and broadcast behavior must be checked on the target machines.

## Team responsibilities

- TV1 (`kentlatoi`): UDP discovery, peer registry, responsive CLI.
- TV2 (`thanhhuong107`): TCP connections, chat, application protocol.
- TV3 (`phkhoiit-1508`): file transfer, application integration and shared error handling.

All members share testing, documentation, Wireshark evidence and the final demo.
