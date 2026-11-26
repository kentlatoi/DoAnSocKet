"""TCP listener có thread và trình quản lý kết nối tới nhiều peer."""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable
from dataclasses import dataclass, field

from .protocol import (
    ConnectionClosed,
    Frame,
    MessageType,
    ProtocolError,
    decode_json,
    encode_frame,
    encode_json,
    recv_frame,
)

# Callback nhận peer_id và Frame đã tách từ TCP stream.
MessageHandler = Callable[[str, Frame], None]
# Callback báo peer_id khi connection mới được đăng ký.
ConnectionHandler = Callable[[str], None]
# Callback báo peer_id và lỗi nếu connection bị đóng do sự cố.
DisconnectHandler = Callable[[str, Exception | None], None]


class ConnectionManagerError(RuntimeError):
    """Lỗi chung trong vòng đời TCP Connection."""


class NotConnectedError(ConnectionManagerError):
    """Lỗi khi gửi cho peer chưa có kết nối hoạt động."""


# Trạng thái một TCP stream; slots giảm bộ nhớ, thuộc tính vẫn thay đổi được.
@dataclass(slots=True)
class PeerConnection:
    """Giữ socket và send Lock của một TCP Connection tới peer."""
    peer_id: str
    peer_name: str
    sock: socket.socket
    address: tuple[str, int]
    outgoing: bool  # Phân biệt chiều kết nối khi hai phía cùng connect.
    # default_factory tạo Lock riêng cho từng socket, không dùng chung giữa các peer.
    send_lock: threading.Lock = field(default_factory=threading.Lock)

    def send(self, message_type: MessageType, payload: bytes = b"") -> None:
        """Gửi trọn một frame dưới send Lock riêng của connection."""
        data = encode_frame(message_type, payload)
        # Khóa theo connection để các thread không ghi xen byte của hai frame.
        with self.send_lock:
            self.sock.sendall(data)

    def close(self) -> None:
        """Shutdown hai chiều và đóng socket khi connection không còn dùng."""
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


class ConnectionManager:
    """Nhận, tạo, loại kết nối trùng và theo dõi các TCP Connection.

    Khi hai peer cùng kết nối, peer có ID nhỏ hơn giữ socket outgoing và peer
    còn lại giữ socket incoming. Hai phía vì vậy cùng chọn đúng một TCP stream.
    """

    def __init__(
        self,
        peer_id: str,
        peer_name: str,
        host: str = "0.0.0.0",
        port: int = 0,
        *,
        connect_timeout: float = 5.0,
    ) -> None:
        """Thiết lập TCP listener, bảng kết nối theo peer_id và callback."""
        if not peer_id or not peer_name:
            raise ValueError("peer_id and peer_name are required")
        self.peer_id = peer_id
        self.peer_name = peer_name
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self._listener: socket.socket | None = None
        # Mỗi peer_id chỉ giữ một TCP stream đang hoạt động.
        self._connections: dict[str, PeerConnection] = {}
        self._lock = threading.RLock()
        # Event dừng và tập worker để đóng socket, chờ thread khi shutdown.
        self._stop = threading.Event()
        self._threads: set[threading.Thread] = set()
        # Các subscriber nhận frame, kết nối mới hoặc ngắt kết nối.
        self._message_handlers: list[MessageHandler] = []
        self._connect_handlers: list[ConnectionHandler] = []
        self._disconnect_handlers: list[DisconnectHandler] = []

    def add_message_handler(self, handler: MessageHandler) -> None:
        with self._lock:
            self._message_handlers.append(handler)

    def add_connect_handler(self, handler: ConnectionHandler) -> None:
        with self._lock:
            self._connect_handlers.append(handler)

    def add_disconnect_handler(self, handler: DisconnectHandler) -> None:
        with self._lock:
            self._disconnect_handlers.append(handler)

    def start(self) -> int:
        """Bắt đầu lắng nghe và trả về TCP port thực tế."""

        with self._lock:
            if self._listener is not None:
                return self.port
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind((self.host, self.port))
                listener.listen()
            except Exception:
                listener.close()
                raise
            listener.settimeout(0.2)
            self._listener = listener
            self.port = listener.getsockname()[1]
            self._stop.clear()
            self._spawn(self._accept_loop, "tcp-accept")
            return self.port

    def connect(
        self, host: str, port: int, expected_peer_id: str | None = None
    ) -> PeerConnection:
        """Kết nối endpoint đã discover và hoàn tất HELLO ở tầng ứng dụng."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.connect_timeout)
        try:
            sock.connect((host, port))
            # HELLO gắn TCP stream với peer_id đã nhận qua UDP Discovery.
            sock.sendall(encode_frame(MessageType.HELLO, self._hello_payload()))
            peer_id, peer_name = self._parse_hello(recv_frame(sock))
            if peer_id == self.peer_id:
                raise ProtocolError("refusing a connection to this peer")
            if expected_peer_id is not None and peer_id != expected_peer_id:
                raise ProtocolError(
                    f"expected peer {expected_peer_id!r}, received {peer_id!r}"
                )
            sock.settimeout(None)
            candidate = PeerConnection(
                peer_id, peer_name, sock, (host, port), outgoing=True
            )
            active, accepted = self._register(candidate)
            if accepted:
                self._spawn(
                    lambda: self._receive_loop(candidate),
                    f"tcp-recv-{peer_id}",
                )
            else:
                candidate.close()
            return active
        except Exception:
            try:
                sock.close()
            except OSError:
                pass
            raise

    def send(
        self, peer_id: str, message_type: MessageType, payload: bytes = b""
    ) -> None:
        """Gửi frame tới peer đang kết nối; loại connection nếu socket lỗi."""
        with self._lock:
            connection = self._connections.get(peer_id)
        if connection is None:
            raise NotConnectedError(f"not connected to peer {peer_id!r}")
        try:
            connection.send(message_type, payload)
        except OSError as exc:
            self._drop(connection, exc)
            raise ConnectionManagerError(f"send to {peer_id!r} failed") from exc

    def disconnect(self, peer_id: str) -> None:
        """Chủ động đóng connection của peer và phát callback ngắt kết nối."""
        with self._lock:
            connection = self._connections.pop(peer_id, None)
        if connection is not None:
            connection.close()
            self._notify_disconnect(peer_id, None)

    def get_connection(self, peer_id: str) -> PeerConnection | None:
        with self._lock:
            return self._connections.get(peer_id)

    def connected_peers(self) -> list[str]:
        with self._lock:
            return list(self._connections)

    def stop(self) -> None:
        """Ngừng accept, đóng mọi stream và chờ ngắn các worker kết thúc."""

        self._stop.set()
        with self._lock:
            listener, self._listener = self._listener, None
            connections = list(self._connections.values())
            self._connections.clear()
        if listener is not None:
            listener.close()
        for connection in connections:
            connection.close()
        current = threading.current_thread()
        for thread in list(self._threads):
            if thread is not current:
                thread.join(timeout=1.0)

    def _hello_payload(self) -> bytes:
        """Mã hóa peer_id và tên cho HELLO ở tầng ứng dụng."""
        return encode_json({"peer_id": self.peer_id, "name": self.peer_name})

    @staticmethod
    def _parse_hello(frame: Frame) -> tuple[str, str]:
        """Kiểm tra HELLO đầu tiên và lấy định danh peer từ Payload."""
        if frame.message_type is not MessageType.HELLO:
            raise ProtocolError("first frame must be HELLO")
        data = decode_json(frame.payload)
        peer_id, name = data.get("peer_id"), data.get("name")
        if not isinstance(peer_id, str) or not peer_id.strip():
            raise ProtocolError("HELLO peer_id must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise ProtocolError("HELLO name must be a non-empty string")
        return peer_id, name

    def _accept_loop(self) -> None:
        """Nhận TCP Connection mới và giao handshake cho worker riêng."""
        # Mỗi connection đến được giao cho worker riêng để accept loop không bị chặn.
        while not self._stop.is_set():
            listener = self._listener
            if listener is None:
                return
            try:
                sock, address = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            self._spawn(
                lambda s=sock, a=address: self._accept_connection(s, a),
                "tcp-handshake",
            )

    def _accept_connection(self, sock: socket.socket, address: tuple[str, int]) -> None:
        """Trao đổi HELLO với bên kết nối tới rồi đăng ký stream hợp lệ."""
        try:
            sock.settimeout(self.connect_timeout)
            peer_id, peer_name = self._parse_hello(recv_frame(sock))
            if peer_id == self.peer_id:
                raise ProtocolError("refusing a connection from this peer")
            sock.sendall(encode_frame(MessageType.HELLO, self._hello_payload()))
            sock.settimeout(None)
            candidate = PeerConnection(
                peer_id, peer_name, sock, address, outgoing=False
            )
            _, accepted = self._register(candidate)
            if not accepted:
                candidate.close()
                return
            self._receive_loop(candidate)
        except (OSError, ConnectionClosed, ProtocolError):
            try:
                sock.close()
            except OSError:
                pass

    def _register(self, candidate: PeerConnection) -> tuple[PeerConnection, bool]:
        """Giữ một stream cho mỗi peer_id khi hai phía cùng kết nối."""
        old_to_close: PeerConnection | None = None
        notify = False
        with self._lock:
            existing = self._connections.get(candidate.peer_id)
            if existing is None:
                self._connections[candidate.peer_id] = candidate
                notify = True
            elif self._is_preferred(candidate) and not self._is_preferred(existing):
                # Quy tắc cố định giúp hai phía loại cùng một connection bị trùng.
                self._connections[candidate.peer_id] = candidate
                old_to_close = existing
            else:
                return existing, False
        if old_to_close is not None:
            old_to_close.close()
        if notify:
            self._notify_connect(candidate.peer_id)
        return candidate, True

    def _is_preferred(self, connection: PeerConnection) -> bool:
        """Dùng thứ tự peer_id để hai phía chọn cùng một stream."""
        return connection.outgoing == (self.peer_id < connection.peer_id)

    def _receive_loop(self, connection: PeerConnection) -> None:
        """Đọc frame liên tục và chuyển đến ChatManager, TransferManager."""
        error: Exception | None = None
        try:
            # Một receive worker liên tục tách frame cho mỗi TCP Connection.
            while not self._stop.is_set():
                frame = recv_frame(connection.sock)
                if frame.message_type is MessageType.HELLO:
                    raise ProtocolError("HELLO is only valid during handshake")
                with self._lock:
                    handlers = list(self._message_handlers)
                for handler in handlers:
                    handler(connection.peer_id, frame)
        except (OSError, ConnectionClosed, ProtocolError) as exc:
            error = exc
        finally:
            self._drop(connection, error)

    def _drop(self, connection: PeerConnection, error: Exception | None) -> None:
        """Gỡ đúng stream đã lỗi, tránh xóa stream mới thay thế nó."""
        removed = False
        with self._lock:
            if self._connections.get(connection.peer_id) is connection:
                del self._connections[connection.peer_id]
                removed = True
        connection.close()
        # Chỉ phát disconnect nếu đây vẫn là connection đang được đăng ký.
        if removed and not self._stop.is_set():
            self._notify_disconnect(connection.peer_id, error)

    def _spawn(self, target: Callable[[], None], name: str) -> None:
        """Chạy worker daemon và bỏ khỏi danh sách khi hoàn thành."""
        def run() -> None:
            try:
                target()
            finally:
                with self._lock:
                    self._threads.discard(threading.current_thread())

        thread = threading.Thread(target=run, name=name, daemon=True)
        with self._lock:
            self._threads.add(thread)
        thread.start()

    def _notify_connect(self, peer_id: str) -> None:
        """Gọi các callback kết nối ngoài Lock của bảng connection."""
        with self._lock:
            handlers = list(self._connect_handlers)
        for handler in handlers:
            handler(peer_id)

    def _notify_disconnect(self, peer_id: str, error: Exception | None) -> None:
        """Gọi các callback ngắt kết nối để dọn transfer và báo giao diện."""
        with self._lock:
            handlers = list(self._disconnect_handlers)
        for handler in handlers:
            handler(peer_id, error)
