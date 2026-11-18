# Application protocol specification — version 1

**Status:** TCP v1, UDP discovery, application coordination and file transfer are implemented. Physical LAN verification remains pending.

## UDP presence

Discovery broadcasts a UTF-8 datagram of at most 512 bytes on shared UDP port 9999 by default:

```text
HELLO|name|tcp_port|status|peer_id
```

`status` is `online` or `away`. A heartbeat is sent every 3 seconds, and registry entries expire after 10 seconds without an update. The datagram's source IP and advertised TCP port form the registry key `(source_ip, tcp_port)`; duplicate display names remain distinct. The four-field form without `peer_id` is accepted for legacy presence packets, but cannot be matched to a TCP handshake by ID.

The UDP registry key identifies an endpoint, while TCP connections and chat histories use the `peer_id` exchanged in the TCP `HELLO` frame. This ID stays stable for one application session. The coordinator must share it between Discovery and ConnectionManager and advertise the port on which TCP actually listens.

## TCP frame

TCP is a byte stream, so every application message uses a fixed 10-byte, network-byte-order header followed by the declared payload.

| Offset | Size | Field | Value |
| ---: | ---: | --- | --- |
| 0 | 4 | Magic | ASCII `LCHT` |
| 4 | 1 | Version | `1` |
| 5 | 1 | Message type | See table below |
| 6 | 4 | Payload length | Unsigned big-endian byte count |
| 10 | N | Payload | Exactly N bytes, maximum 8 MiB |

The receiver loops until all 10 header bytes and all declared payload bytes have arrived. A clean close between frames is a disconnect; a close after a partial header or payload is an incomplete frame. Invalid magic, version, type, size, UTF-8, or JSON closes that peer connection without crashing the listener.

## Message types

| Code | Name | Payload | Owner/use |
| ---: | --- | --- | --- |
| 1 | `HELLO` | JSON | Connection identity handshake |
| 2 | `CHAT` | JSON | UTF-8 chat message |
| 3 | `FILE_META` | JSON | TV3: file name, size, transfer ID |
| 4 | `FILE_CHUNK` | bytes | TV3: raw file data |
| 5 | `FILE_END` | JSON | TV3: completion/integrity result |
| 6 | `LEAVE` | JSON or empty | Conversation control |
| 7 | `ERROR` | JSON | Recoverable application error |

Structured payloads are compact UTF-8 JSON objects. Length always counts encoded bytes, not Python characters. Binary file chunks are not JSON or UTF-8 decoded.

### `HELLO`

`HELLO` must be the first frame in both directions and cannot appear again on an established stream.

```json
{"peer_id":"stable-instance-id","name":"Lan"}
```

Both fields are required non-empty strings. Discovery must provide the same `peer_id`, display name, IP, and TCP port so the connection can be matched to the registry.
`HELLO` states an identity but does not authenticate it. When connecting to a selected discovery peer, the received ID must match that peer's ID before the connection is registered (see TCP identity fix PR #6). A legacy UDP peer with no ID cannot pass this check and should be shown as unavailable for verified chat.

### `CHAT`

```json
{
  "sender": "Lan",
  "text": "Xin chào 👋",
  "sent_at": "2026-11-13T12:00:00+00:00"
}
```

`text` and `sent_at` are required non-empty strings. `sender` is a display value; routing and history use the `peer_id` stated in the TCP `HELLO`, subject to coordinator verification against discovery.

### File-transfer contract

One transfer per direction per TCP connection is supported:

- `FILE_META`: `{"transfer_id":"...","name":"safe-name","size":123}`
- `FILE_CHUNK`: raw chunks no larger than 64 KiB
- `FILE_END`: `{"transfer_id":"...","sha256":"..."}` marks the end of sender chunks. The receiver validates the byte count and SHA-256, saves the file, then responds with `FILE_END` `{"transfer_id":"...","status":"ok"}`. These two forms have distinct sender/receiver meanings.
- `ERROR`: `{"transfer_id":"...","error":"reason"}` rejects a transfer, including a size or checksum mismatch. A broken TCP connection also aborts the transfer. The sender reports verified completion only after matching acknowledgement; otherwise it reports failure or a 30-second acknowledgement timeout.

Incoming files are written to a temporary `.part` file under `downloads/`, then linked to an unused destination name. Existing files get a numbered suffix. Partial files are deleted on interrupted or rejected transfers. A receiver rejects names containing path separators or control characters.

Only one file transfer per direction may be active on a TCP connection. `ConnectionManager.send()` locks one complete frame at a time; CHAT frames may interleave with file chunks without corrupting the stream. The receiver routes message types to registered handlers.

### `LEAVE`

`/leave` ends the current conversation by calling `ChatManager.leave_chat()`; it keeps the TCP connection and other conversations available. `LEAVE` is reserved as a wire message type, but no handler currently sends or interprets it. TV3 should not send it for `/leave` without a separate team decision.

## Connection model

Each peer listens and may connect. An outgoing side sends `HELLO`, then receives `HELLO`; an incoming side receives it, then replies. Multiple peer streams remain active concurrently.

If two peers connect at the same time, the lower lexical `peer_id` keeps its outgoing socket and the higher ID keeps its incoming socket. Both sides therefore select the same physical stream and close the duplicate.

## Limits and compatibility

- Header version changes require an explicit compatibility decision.
- A single payload is limited to 8 MiB; files must be chunked.
- Unknown types and unsupported versions are protocol errors.
- JSON is restricted to an object at the top level.
- File names, paths, collision handling, and partial cleanup are handled in `transfer.py`.
