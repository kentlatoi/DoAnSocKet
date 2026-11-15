# Application protocol specification — version 1

**Status:** Implemented on `feat/tcp-chat`; team review is required before merge because discovery and file transfer consume this interface.

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

### `CHAT`

```json
{
  "sender": "Lan",
  "text": "Xin chào 👋",
  "sent_at": "2026-11-13T12:00:00+00:00"
}
```

`text` and `sent_at` are required non-empty strings. `sender` is a display value; routing and history use the authenticated `peer_id` from the socket handshake.

### File-transfer contract for TV3

The shared message types intentionally leave file policy in `transfer.py`. Recommended v1 payloads are:

- `FILE_META`: `{"transfer_id":"...","name":"safe-name","size":123}`
- `FILE_CHUNK`: raw chunks no larger than 64 KiB
- `FILE_END`: `{"transfer_id":"...","sha256":"..."}`

`ConnectionManager.send()` locks one complete frame at a time. File transfer should call it once per chunk, allowing chat frames to interleave between chunks without corrupting the TCP stream. The receiver routes all message types to registered handlers, so chat and transfer may share one connection.

## Connection model

Each peer listens and may connect. An outgoing side sends `HELLO`, then receives `HELLO`; an incoming side receives it, then replies. Multiple peer streams remain active concurrently.

If two peers connect at the same time, the lower lexical `peer_id` keeps its outgoing socket and the higher ID keeps its incoming socket. Both sides therefore select the same physical stream and close the duplicate.

## Limits and compatibility

- Header version changes require an explicit compatibility decision.
- A single payload is limited to 8 MiB; files must be chunked.
- Unknown types and unsupported versions are protocol errors.
- JSON is restricted to an object at the top level.
- File names, paths, collision handling, partial cleanup, and acknowledgements remain TV3 responsibilities.
