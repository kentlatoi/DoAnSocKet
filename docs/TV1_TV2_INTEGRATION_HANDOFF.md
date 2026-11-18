# TV1/TV2 integration handoff for TV3

Historical TV1/TV2 handoff: `app.py`, `__main__.py`, and `transfer.py` have since been implemented on the TV3 branch. PR #6 and #7 appear as merge commits on the local `main`. See the current README, protocol specification and test evidence for the integrated state.

## Public APIs and startup

1. Create `PeerRegistry(on_event=None)`. `on_event(kind, peer)` receives `"online"` or `"offline"` and a frozen `Peer(name, ip, tcp_port, status, last_seen, peer_id)`; `list_peers()` returns a snapshot. Registry entries are keyed by `(ip, tcp_port)`, while TCP/chat use `peer_id`.
2. Choose one non-empty session ID, for example `uuid.uuid4().hex`, and create `ConnectionManager(peer_id, peer_name, host="0.0.0.0", port=0, *, connect_timeout=5.0)`. Call `start() -> int` first. It returns the actual listening TCP port, including when `port=0`.
3. Create `Discovery(name, tcp_port, registry, udp_port=9999, broadcast_address="255.255.255.255", on_error=None, peer_id=None)` with that returned TCP port and the **same session ID**. `start()`, `set_status("online" or "away")`, and `stop()` manage presence. `Discovery.peer_id` exposes its ID; if it generates one, pass that value to ConnectionManager before starting either component. Default heartbeat is 3 seconds; expiry is 10 seconds.
4. Create `ChatManager(connections, local_name, on_event=None)` and `CLI(registry, discovery, on_chat=None, on_send=None, on_leave=None, on_text=None, on_quit=None, session=None)`. Run `CLI.run()` on the input thread. `CLI.notify(message)` prints asynchronous notices while preserving typed input through `prompt_toolkit`.

## Selecting and chatting

- `CLI.on_chat(peer)` receives a `Peer`. Reject an empty `peer.peer_id` (legacy four-field UDP packet): show an unavailable message, rather than treating it as verified. Otherwise call `connections.connect(peer.ip, peer.tcp_port, expected_peer_id=peer.peer_id)` **after PR #6 merges**. That optional parameter checks TCP `HELLO` before registration; it is an identity-consistency check, not authentication. Catch connection and protocol errors and report them with `CLI.notify()` without exiting. Then call `chat.select_peer(peer.peer_id) -> list[ChatMessage]` to show unread messages. Existing two-argument `connect(host, port)` remains valid for callers without discovery selection.
- `CLI.on_text(line)` sends `chat.send_message(chat.current_peer, line) -> ChatMessage` when a peer is selected; otherwise show a short error. `chat.get_history(peer_id) -> list[ChatMessage]`, `unread_count(peer_id) -> int`, and `unread_counts() -> dict[str, int]` expose history/unread state.
- `ChatManager(on_event=...)` emits `ChatEvent(message, unread_count)` for incoming CHAT. The coordinator formats it for `CLI.notify()`. Registry events, `ConnectionManager.add_connect_handler(handler(peer_id))`, and `add_disconnect_handler(handler(peer_id, error))` should also call `CLI.notify()` as appropriate. `add_message_handler(handler(peer_id, frame))` delivers protocol frames to chat and future transfer handlers.
- `/leave` should call `chat.leave_chat()`: it clears only the current selection and keeps all TCP connections for later chat and unread messages. The `LEAVE` wire type has no implemented handler; do not send it just for `/leave`. `/quit` should stop Discovery and ConnectionManager, then exit the CLI. `ConnectionManager.disconnect(peer_id)` closes one peer stream; `stop()` closes all streams.

## File transfer boundary

`ConnectionManager.send(peer_id, message_type, payload=b"")` sends one locked frame. Existing `MessageType.FILE_META`, `FILE_CHUNK`, `FILE_END`, and `ERROR` codes and `add_message_handler()` support TV3's transfer handler. `protocol.encode_json()/decode_json()` handle structured UTF-8 JSON; file chunks remain bytes; `recv_frame()` enforces the 10-byte header and 8 MiB payload limit. The protocol spec recommends one active transfer per direction per connection, CHAT interleaving between chunks, and byte-count/SHA-256 verification. TV3 must implement file state, progress, downloads, partial cleanup, and decide acknowledgements/completion/error payloads with the team. `CLI.on_send(path)` passes a file path to that backend; `CLI.notify()` can show progress.

## Integration checklist and limits

- Start TCP before UDP; advertise its actual port and one shared session ID.
- Select a UDP peer, verify its ID in TCP HELLO, exchange UTF-8 chat both ways, then test another peer's unread count and `/leave`.
- Keep chat responsive during a file transfer; test disconnects, stale peers, missing files, partial-file deletion, and shutdown.
- Run the full unit suite, then test two physical LAN machines and capture UDP broadcast and TCP handshake in Wireshark.
- Multi-instance UDP tests skip where `SO_REUSEPORT` is absent; this does not by itself prove the two-machine LAN demo will fail. Windows firewall and broadcast delivery still need manual verification.
