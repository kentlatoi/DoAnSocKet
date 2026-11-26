"""Message Framing ở tầng ứng dụng cho TCP stream của LAN Chat.

Mỗi frame gồm Header 10 byte và đúng ``payload_length`` byte Payload.
Message có cấu trúc dùng JSON UTF-8; file chunk giữ nguyên dữ liệu nhị phân.
"""

from __future__ import annotations

import json
import socket
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

# Magic và version giúp từ chối frame không thuộc định dạng LAN Chat hiện tại.
MAGIC = b"LCHT"
VERSION = 1
# Header 10 byte: magic (4), version (1), loại (1), độ dài Payload (4, big-endian).
HEADER = struct.Struct("!4sBBI")
# Giới hạn Payload của một frame; file được chia thành nhiều frame nhỏ hơn.
MAX_PAYLOAD_SIZE = 8 * 1024 * 1024


class MessageType(IntEnum):
    """Mã loại frame TCP: HELLO định danh, CHAT nhắn tin, FILE_* truyền file.

    FILE_END mang SHA-256 từ sender hoặc ACK từ receiver; LEAVE chưa dùng.
    """

    HELLO = 1
    CHAT = 2
    FILE_META = 3
    FILE_CHUNK = 4
    FILE_END = 5
    LEAVE = 6
    ERROR = 7


class ProtocolError(ValueError):
    """Lỗi khi peer gửi frame sai định dạng hoặc không được hỗ trợ."""


class ConnectionClosed(ConnectionError):
    """Lỗi khi peer đóng TCP stream."""


class IncompleteFrame(ProtocolError):
    """Lỗi khi stream đóng trước lúc nhận đủ một frame."""


# Frame đã tách Header; frozen giữ dữ liệu ổn định, slots giảm bộ nhớ.
@dataclass(frozen=True, slots=True)
class Frame:
    message_type: MessageType
    payload: bytes


def encode_frame(message_type: MessageType | int, payload: bytes = b"") -> bytes:
    """Ghép Header và Payload thành một frame hoàn chỉnh để gửi."""

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
    """Mã hóa Payload có cấu trúc thành JSON UTF-8 gọn."""

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
    """Giải mã JSON UTF-8 và chỉ chấp nhận object ở cấp cao nhất."""

    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("payload is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise ProtocolError("JSON payload must be an object")
    return data


def recv_exact(sock: socket.socket, size: int) -> bytes:
    """Đọc đúng ``size`` byte dù TCP chia dữ liệu qua nhiều lần recv."""

    if size < 0:
        raise ValueError("size must be non-negative")
    data = bytearray()
    # Một lần recv có thể trả về ít byte hơn yêu cầu nên phải đọc tiếp.
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
    """Tách Header, kiểm tra và nhận đủ Payload của một frame TCP."""

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
