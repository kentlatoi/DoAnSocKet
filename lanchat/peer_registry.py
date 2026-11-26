"""Danh sách peer thread-safe được cập nhật từ các gói UDP presence."""

from dataclasses import dataclass
import threading
import time


# Snapshot presence của một peer; frozen tránh sửa thuộc tính ngoài registry.
@dataclass(frozen=True)
class Peer:
    name: str
    ip: str
    tcp_port: int
    status: str
    last_seen: float  # Thời điểm monotonic của gói hợp lệ gần nhất.
    peer_id: str = ""


class PeerRegistry:
    """Định danh peer bằng IP và TCP port để chấp nhận các tên bị trùng."""

    def __init__(self, on_event=None):
        """Lưu snapshot peer theo endpoint và callback cho thay đổi trạng thái."""
        # Khóa theo (IP, TCP port) để các peer trùng tên vẫn phân biệt được.
        self._peers = {}
        # Discovery và giao diện có thể truy cập registry từ các thread khác nhau.
        self._lock = threading.Lock()
        self.on_event = on_event  # Nhận ("online", "offline" hoặc "status_changed", Peer).

    def update(self, name, ip, tcp_port, status, now=None, peer_id=""):
        """Làm mới last_seen và chỉ phát event khi peer mới hoặc đổi trạng thái."""
        now = time.monotonic() if now is None else now
        peer = Peer(name, ip, tcp_port, status, now, peer_id)
        key = (ip, tcp_port)
        with self._lock:
            previous = self._peers.get(key)
            # Thay toàn bộ snapshot để cập nhật cả status và last_seen.
            self._peers[key] = peer
        if self.on_event:
            # Heartbeat bình thường chỉ cập nhật last_seen, không phát event dư thừa.
            if previous is None:
                self.on_event("online", peer)
            elif previous.status != status:
                self.on_event("status_changed", peer)
        return peer

    def expire(self, timeout, now=None):
        """Xóa peer quá hạn và phát offline sau khi đã nhả Lock."""
        now = time.monotonic() if now is None else now
        # Xóa peer không còn gửi Heartbeat trong khoảng Timeout cho phép.
        with self._lock:
            expired = [peer for peer in self._peers.values()
                       if now - peer.last_seen >= timeout]
            for peer in expired:
                del self._peers[(peer.ip, peer.tcp_port)]
        if self.on_event:
            for peer in expired:
                self.on_event("offline", peer)
        return expired

    def list_peers(self):
        """Trả về snapshot ổn định thay vì để lộ dictionary đang thay đổi."""
        with self._lock:
            return sorted(self._peers.values(), key=lambda p: (p.name, p.ip, p.tcp_port))
