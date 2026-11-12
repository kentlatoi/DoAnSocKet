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
| UDP presence schema and port | Open | — |
| TCP frame header, type, length, and limits | Open | — |
| UTF-8 and binary payload rules | Open | — |
| File stream, progress, acknowledgements | Open | — |
| Invalid or incomplete message policy | Open | — |
| Versioning and compatibility | Open | — |
