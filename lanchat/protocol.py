"""Application-layer framing for LAN Chat TCP streams.

Every frame has a fixed 10-byte header followed by exactly ``payload_length``
bytes. Structured messages use UTF-8 JSON; file chunks remain raw bytes.
"""

from __future__ import annotations

import json
import socket
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

MAGIC = b"LCHT"
VERSION = 1
HEADER = struct.Struct("!4sBBI")
MAX_PAYLOAD_SIZE = 8 * 1024 * 1024


class MessageType(IntEnum):
    """Message types shared by chat and file-transfer modules."""

    HELLO = 1
    CHAT = 2
    FILE_META = 3
    FILE_CHUNK = 4
    FILE_END = 5
    LEAVE = 6
    ERROR = 7


class ProtocolError(ValueError):
    """Raised when a peer sends a malformed or unsupported frame."""


class ConnectionClosed(ConnectionError):
    """Raised when the peer closes the TCP stream."""


class IncompleteFrame(ProtocolError):
    """Raised when the stream closes after only part of a frame arrives."""


@dataclass(frozen=True, slots=True)
class Frame:
    message_type: MessageType
    payload: bytes


def encode_frame(message_type: MessageType | int, payload: bytes = b"") -> bytes:
    """Return one complete wire frame."""

    try:
        kind = MessageType(message_type)
    except ValueError as exc:
        raise ProtocolError(f"unknown message type: {message_type}") from exc
    if not isinstance(payload, bytes):
        raise TypeError("frame payload must be bytes")
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ProtocolError(f"payload exceeds {MAX_PAYLOAD_SIZE} bytes")
    return HEADER.pack(MAGIC, VERSION, kind.value, len(payload)) + payload


def encode_json(data: Mapping[str, Any]) -> bytes:
    """Encode a structured payload as compact UTF-8 JSON."""

    if not isinstance(data, Mapping):
        raise TypeError("JSON payload must be a mapping")
    try:
        payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    except (TypeError, ValueError) as exc:
        raise ProtocolError("payload is not JSON serializable") from exc
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ProtocolError(f"payload exceeds {MAX_PAYLOAD_SIZE} bytes")
    return payload


def decode_json(payload: bytes) -> dict[str, Any]:
    """Decode a UTF-8 JSON object and reject other JSON values."""

    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("payload is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ProtocolError("JSON payload must be an object")
    return data


def recv_exact(sock: socket.socket, size: int) -> bytes:
    """Read exactly ``size`` bytes, handling fragmented TCP receives."""

    if size < 0:
        raise ValueError("size must be non-negative")
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            if data:
                raise IncompleteFrame(
                    f"connection closed after {len(data)} of {size} bytes"
                )
            raise ConnectionClosed("peer closed the connection")
        data.extend(chunk)
    return bytes(data)


def recv_frame(sock: socket.socket) -> Frame:
    """Receive and validate one frame from a TCP socket."""

    header = recv_exact(sock, HEADER.size)
    magic, version, raw_type, payload_size = HEADER.unpack(header)
    if magic != MAGIC:
        raise ProtocolError("invalid frame magic")
    if version != VERSION:
        raise ProtocolError(f"unsupported protocol version: {version}")
    try:
        message_type = MessageType(raw_type)
    except ValueError as exc:
        raise ProtocolError(f"unknown message type: {raw_type}") from exc
    if payload_size > MAX_PAYLOAD_SIZE:
        raise ProtocolError(f"payload exceeds {MAX_PAYLOAD_SIZE} bytes")
    payload = recv_exact(sock, payload_size) if payload_size else b""
    return Frame(message_type, payload)
