"""Thread-safe per-peer chat histories and unread state."""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .protocol import Frame, MessageType, ProtocolError, decode_json, encode_json


class MessageSender(Protocol):
    def add_message_handler(self, handler: Callable[[str, Frame], None]) -> None: ...

    def send(
        self, peer_id: str, message_type: MessageType, payload: bytes = b""
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class ChatMessage:
    peer_id: str
    sender: str
    text: str
    sent_at: str
    incoming: bool


@dataclass(frozen=True, slots=True)
class ChatEvent:
    message: ChatMessage
    unread_count: int


class ChatManager:
    """Route CHAT frames without disconnecting inactive conversations."""

    def __init__(
        self,
        connections: MessageSender,
        local_name: str,
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> None:
        if not local_name:
            raise ValueError("local_name is required")
        self._connections = connections
        self.local_name = local_name
        self._on_event = on_event
        self._histories: dict[str, list[ChatMessage]] = defaultdict(list)
        self._unread: dict[str, int] = defaultdict(int)
        self._current_peer: str | None = None
        self._lock = threading.RLock()
        connections.add_message_handler(self.handle_frame)

    @property
    def current_peer(self) -> str | None:
        with self._lock:
            return self._current_peer

    def send_message(self, peer_id: str, text: str) -> ChatMessage:
        if not isinstance(text, str) or not text:
            raise ValueError("message text must be a non-empty string")
        sent_at = datetime.now(timezone.utc).isoformat()
        self._connections.send(
            peer_id,
            MessageType.CHAT,
            encode_json({"sender": self.local_name, "text": text, "sent_at": sent_at}),
        )
        message = ChatMessage(peer_id, self.local_name, text, sent_at, False)
        with self._lock:
            self._histories[peer_id].append(message)
        return message

    def handle_frame(self, peer_id: str, frame: Frame) -> None:
        if frame.message_type is not MessageType.CHAT:
            return
        data = decode_json(frame.payload)
        text, sent_at = data.get("text"), data.get("sent_at")
        if not isinstance(text, str) or not text:
            raise ProtocolError("CHAT text must be a non-empty string")
        if not isinstance(sent_at, str) or not sent_at:
            raise ProtocolError("CHAT sent_at must be a non-empty string")
        sender = data.get("sender")
        if sender is not None and not isinstance(sender, str):
            raise ProtocolError("CHAT sender must be a string")
        message = ChatMessage(peer_id, sender or peer_id, text, sent_at, True)
        with self._lock:
            self._histories[peer_id].append(message)
            if self._current_peer != peer_id:
                self._unread[peer_id] += 1
            unread = self._unread[peer_id]
        if self._on_event is not None:
            self._on_event(ChatEvent(message, unread))

    def select_peer(self, peer_id: str) -> list[ChatMessage]:
        """Select a conversation and return the messages that were unread."""

        with self._lock:
            unread = self._unread[peer_id]
            messages = list(self._histories[peer_id][-unread:]) if unread else []
            self._unread[peer_id] = 0
            self._current_peer = peer_id
            return messages

    def leave_chat(self) -> None:
        with self._lock:
            self._current_peer = None

    def get_history(self, peer_id: str) -> list[ChatMessage]:
        with self._lock:
            return list(self._histories[peer_id])

    def unread_count(self, peer_id: str) -> int:
        with self._lock:
            return self._unread[peer_id]

    def unread_counts(self) -> dict[str, int]:
        with self._lock:
            return {peer: count for peer, count in self._unread.items() if count}
