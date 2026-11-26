"""Lịch sử chat và trạng thái unread riêng theo peer, có bảo vệ thread."""

from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .protocol import Frame, MessageType, ProtocolError, decode_json, encode_json


# typing.Protocol mô tả API gửi frame mà ChatManager cần, không phải protocol mạng.
class MessageSender(Protocol):
    # Đăng ký callback nhận frame từ một peer.
    def add_message_handler(self, handler: Callable[[str, Frame], None]) -> None: ...

    # Gửi một frame theo peer_id mà không phụ thuộc class kết nối cụ thể.
    def send(
        self, peer_id: str, message_type: MessageType, payload: bytes = b""
    ) -> None: ...


# Bản ghi tin nhắn trong lịch sử; frozen giữ snapshot ổn định, slots giảm bộ nhớ.
@dataclass(frozen=True, slots=True)
class ChatMessage:
    peer_id: str
    sender: str
    text: str
    sent_at: str
    incoming: bool  # True nếu nhận từ peer, False nếu do máy này gửi.


# Event mang tin mới và số unread để Application cập nhật CLI hoặc GUI.
@dataclass(frozen=True, slots=True)
class ChatEvent:
    message: ChatMessage
    unread_count: int


class ChatManager:
    """Định tuyến CHAT frame mà không đóng các cuộc trò chuyện chưa được chọn."""

    def __init__(
        self,
        connections: MessageSender,
        local_name: str,
        on_event: Callable[[ChatEvent], None] | None = None,
    ) -> None:
        """Đăng ký nhận CHAT frame và quản lý lịch sử, unread theo peer."""
        if not local_name:
            raise ValueError("local_name is required")
        self._connections = connections
        self.local_name = local_name
        # Callback nhận ChatEvent khi có tin đến; None nếu không cần thông báo.
        self._on_event = on_event
        # Các bảng khóa bằng peer_id; defaultdict tạo lịch sử và bộ đếm khi cần.
        self._histories: dict[str, list[ChatMessage]] = defaultdict(list)
        self._unread: dict[str, int] = defaultdict(int)
        # None nghĩa là người dùng chưa mở cuộc trò chuyện nào.
        self._current_peer: str | None = None
        # Callback và giao diện có thể đọc, ghi các bảng trên từ nhiều thread.
        self._lock = threading.RLock()
        connections.add_message_handler(self.handle_frame)

    @property
    def current_peer(self) -> str | None:
        with self._lock:
            return self._current_peer

    def send_message(self, peer_id: str, text: str) -> ChatMessage:
        """Gửi CHAT JSON qua TCP và lưu tin đã gửi vào lịch sử."""
        if not isinstance(text, str) or not text:
            raise ValueError("message text must be a non-empty string")
        sent_at = datetime.now(timezone.utc).isoformat()
        self._connections.send(
            peer_id,
            MessageType.CHAT,
            encode_json({"sender": self.local_name, "text": text, "sent_at": sent_at}),
        )
        message = ChatMessage(peer_id, self.local_name, text, sent_at, False)
        # Lưu bản tin gửi đi vào cùng lịch sử dùng để render cuộc trò chuyện.
        with self._lock:
            self._histories[peer_id].append(message)
        return message

    def handle_frame(self, peer_id: str, frame: Frame) -> None:
        """Kiểm tra CHAT frame, lưu tin đến và tăng unread nếu chưa mở peer."""
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
            # Chỉ tăng unread khi tin đến không thuộc cuộc trò chuyện đang mở.
            if self._current_peer != peer_id:
                self._unread[peer_id] += 1
            unread = self._unread[peer_id]
        if self._on_event is not None:
            self._on_event(ChatEvent(message, unread))

    def select_peer(self, peer_id: str) -> list[ChatMessage]:
        """Chọn cuộc trò chuyện và trả về các tin vừa ở trạng thái unread."""

        with self._lock:
            unread = self._unread[peer_id]
            messages = [message for message in reversed(self._histories[peer_id])
                        if message.incoming][:unread][::-1]
            self._unread[peer_id] = 0
            self._current_peer = peer_id
            return messages

    def leave_chat(self) -> None:
        """Bỏ chọn peer hiện tại mà không xóa lịch sử hay đóng kết nối."""
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
