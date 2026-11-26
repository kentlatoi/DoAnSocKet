"""UDP Broadcast để quảng bá presence và loại peer hết Timeout."""

import socket
import sys
import threading
import uuid

from .config import HEARTBEAT_SECONDS, PEER_TIMEOUT_SECONDS, UDP_PORT


def parse_presence(data):
    """Trả về thông tin presence hoặc None nếu datagram không hợp lệ."""
    if len(data) > 512:
        return None
    try:
        parts = data.decode("utf-8").split("|")
        if len(parts) not in (4, 5):
            return None
        kind, name, port_text, status = parts[:4]
        peer_id = parts[4] if len(parts) == 5 else ""
        port = int(port_text)
    except (UnicodeError, ValueError):
        return None
    if (kind != "HELLO" or not name or len(name) > 64 or
            any(ord(ch) < 32 for ch in name) or not 1 <= port <= 65535 or
            status not in ("online", "away") or
            (len(parts) == 5 and (not peer_id or len(peer_id) > 64 or
             any(ord(ch) < 33 for ch in peer_id)))):
        return None
    return name, port, status, peer_id


class Discovery:
    """Dùng socket riêng để nhận presence và gửi UDP Broadcast."""

    def __init__(self, name, tcp_port, registry, udp_port=UDP_PORT,
                 broadcast_address="255.255.255.255", on_error=None,
                 peer_id=None):
        """Cấu hình presence, socket và tín hiệu điều khiển các worker UDP."""
        if not name or len(name) > 64 or "|" in name or any(ord(c) < 32 for c in name):
            raise ValueError("name must be 1-64 printable characters without '|'")
        if not 1 <= tcp_port <= 65535 or not 1 <= udp_port <= 65535:
            raise ValueError("ports must be between 1 and 65535")
        peer_id = peer_id or uuid.uuid4().hex
        if len(peer_id) > 64 or "|" in peer_id or any(ord(c) < 33 for c in peer_id):
            raise ValueError("peer_id must be 1-64 non-space characters without '|'")
        self.name, self.tcp_port, self.registry = name, tcp_port, registry
        self.peer_id = peer_id
        self.udp_port, self.broadcast_address = udp_port, broadcast_address
        self.on_error = on_error
        self.status = "online"
        # _stop kết thúc các worker; _send_now đánh thức sender khi đổi status.
        self._stop = threading.Event()
        self._send_now = threading.Event()
        # Theo dõi ba worker và hai socket UDP để giải phóng khi dừng.
        self._threads = []
        self._listener = None
        self._sender = None
        self._sender_port = None

    def start(self):
        """Bind socket trước khi chạy worker để báo ngay lỗi cổng đang bận."""
        if self._threads:
            return
        listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Nhiều peer trên cùng máy có thể cùng lắng nghe cổng discovery.
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            listener.bind(("", self.udp_port))
            listener.settimeout(0.5)
            # SO_BROADCAST cho phép gửi datagram tới địa chỉ Broadcast của LAN.
            sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sender.bind(("", 0))
        except OSError:
            listener.close()
            sender.close()
            raise
        self._listener, self._sender = listener, sender
        self._sender_port = sender.getsockname()[1]
        self._stop.clear()
        self._send_now.set()
        for target in (self._broadcast, self._listen, self._expire):
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            self._threads.append(thread)

    def set_status(self, status):
        """Đổi online/away và yêu cầu phát presence mới ngay lập tức."""
        if status not in ("online", "away"):
            raise ValueError("status must be online or away")
        self.status = status
        # Đánh thức worker để quảng bá trạng thái mới ngay, không chờ Heartbeat kế tiếp.
        self._send_now.set()

    def stop(self):
        """Đóng hai UDP socket, đánh thức và chờ các worker dừng."""
        self._stop.set()
        self._send_now.set()
        if self._listener:
            self._listener.close()
        if self._sender:
            self._sender.close()
        for thread in self._threads:
            thread.join(timeout=1)
        self._threads.clear()
        self._listener = self._sender = None

    def _broadcast(self):
        """Gửi HELLO ngay lúc bắt đầu và định kỳ theo chu kỳ Heartbeat."""
        sender = self._sender
        if sender is None:
            return
        while not self._stop.is_set():
            self._send_now.clear()
            # Presence đóng vai trò Heartbeat để peer khác biết phiên này còn hoạt động.
            message = f"HELLO|{self.name}|{self.tcp_port}|{self.status}|{self.peer_id}".encode("utf-8")
            try:
                sender.sendto(message, (self.broadcast_address, self.udp_port))
            except OSError as error:
                if not self._stop.is_set():
                    self._report_error(error)
            self._send_now.wait(HEARTBEAT_SECONDS)

    def _listen(self):
        """Nhận presence hợp lệ, bỏ qua chính mình rồi cập nhật Peer Registry."""
        listener = self._listener
        if listener is None:
            return
        while not self._stop.is_set():
            try:
                data, address = listener.recvfrom(513)
            except socket.timeout:
                continue
            except OSError as error:
                if not self._stop.is_set():
                    self._report_error(error)
                break
            presence = parse_presence(data)
            if presence:
                name, tcp_port, status, peer_id = presence
                # Không đưa gói của chính phiên chạy vào Peer Registry.
                if peer_id == self.peer_id or (not peer_id and address[1] == self._sender_port):
                    continue
                self.registry.update(name, address[0], tcp_port, status, peer_id=peer_id)

    def _expire(self):
        """Kiểm tra last_seen để loại peer đã hết Timeout."""
        # Kiểm tra định kỳ và phát event offline cho peer đã quá Timeout.
        while not self._stop.wait(0.5):
            self.registry.expire(PEER_TIMEOUT_SECONDS)

    def _report_error(self, error):
        """Chuyển lỗi UDP lên Application hoặc stderr nếu không có callback."""
        if self.on_error:
            self.on_error(error)
        else:
            print(f"UDP discovery error: {error}", file=sys.stderr)
