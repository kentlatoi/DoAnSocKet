# Application protocol specification — draft

**Status: WIRE FORMAT NOT FINALIZED.** This is a design scaffold only. No wire protocol has been selected or implemented.

## Mandatory framing

TCP is a byte stream and does not preserve application message boundaries. Each TCP message must identify its type and payload length, and the receiver must loop until it has read exactly the declared number of bytes or detect an incomplete transfer. Lengths for UTF-8 content must count encoded bytes. Message-size bounds and malformed-frame handling must be defined before implementation. The assignment's sample strings are illustrative, not prescribed syntax.

## Candidate approaches

- A bounded, fixed-size binary header with type and byte length, followed by payload bytes.
- A bounded textual header terminated by a delimiter, followed by a declared payload length.
- A length-prefixed structured envelope with an explicit type and bounded body.

Each candidate needs a decision on UDP presence fields, protocol version, file metadata/chunks, validation, peer identity, and whether files use a separate TCP connection. Chat responsiveness during transfer is required regardless of that choice.

## Decisions to record later

| Topic | Decision | Rationale and test evidence |
| --- | --- | --- |
| UDP presence schema and port | `HELLO|<name>|<tcp_port>|<online\|away>|<peer_id>` UTF-8, maximum 512 bytes; shared UDP port 9999 by default | TV1 adds a per-process ID for TV2's TCP HELLO identity. The PDF's four-field illustrative form is also accepted. Packet source supplies IP; peers are keyed by (IP, TCP port). |
| TCP frame header, type, length, and limits | Open | — |
| UTF-8 and binary payload rules | Open | — |
| File stream, progress, acknowledgements | Open | — |
| Invalid or incomplete message policy | Open | — |
| Versioning and compatibility | Open | — |
