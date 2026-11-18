"""Thread-safe list of peers heard through UDP presence."""

from dataclasses import dataclass
import threading
import time


@dataclass(frozen=True)
class Peer:
    name: str
    ip: str
    tcp_port: int
    status: str
    last_seen: float
    peer_id: str = ""


class PeerRegistry:
    """Identify peers by IP and TCP port, so duplicate names remain distinct."""

    def __init__(self, on_event=None):
        self._peers = {}
        self._lock = threading.Lock()
        self.on_event = on_event  # Called with ("online" or "offline", Peer).

    def update(self, name, ip, tcp_port, status, now=None, peer_id=""):
        now = time.monotonic() if now is None else now
        peer = Peer(name, ip, tcp_port, status, now, peer_id)
        key = (ip, tcp_port)
        with self._lock:
            new = key not in self._peers
            self._peers[key] = peer
        if new and self.on_event:
            self.on_event("online", peer)
        return peer

    def expire(self, timeout, now=None):
        now = time.monotonic() if now is None else now
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
        """Return a stable snapshot rather than exposing the mutable dictionary."""
        with self._lock:
            return sorted(self._peers.values(), key=lambda p: (p.name, p.ip, p.tcp_port))
