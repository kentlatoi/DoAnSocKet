"""Real loopback TCP integration; UDP socket lifecycle is exercised by start()."""

import tempfile
import time
import unittest
from pathlib import Path

from lanchat.app import Application
from lanchat.peer_registry import Peer


def wait_until(check, timeout=3):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if check():
            return True
        time.sleep(0.01)
    return False


class ApplicationTests(unittest.TestCase):
    def test_two_peer_chat_file_and_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            a = Application("Alice", udp_port=18001, broadcast_address="127.0.0.1", downloads=Path(folder) / "a")
            b = Application("Bob", udp_port=18002, broadcast_address="127.0.0.1", downloads=Path(folder) / "b")
            self.addCleanup(a.stop)
            self.addCleanup(b.stop)
            a.start()
            b.start()
            self.assertEqual(a.peer_id, a.connections.peer_id)
            self.assertEqual(a.peer_id, a.discovery.peer_id)
            self.assertEqual(a.connections.port, a.discovery.tcp_port)
            peer = a.registry.update("Bob", "127.0.0.1", b.connections.port, "online", peer_id=b.peer_id)
            wrong = Peer("Wrong", "127.0.0.1", b.connections.port, "online", 0, "wrong-id")
            a.select_peer(wrong)
            self.assertIsNone(a.chat.current_peer)
            a.select_peer(peer)
            self.assertEqual(a.chat.current_peer, b.peer_id)
            a.send_text("xin chào")
            self.assertTrue(wait_until(lambda: len(b.chat.get_history(a.peer_id)) == 1))
            self.assertEqual(b.chat.unread_count(a.peer_id), 1)
            b.chat.select_peer(a.peer_id)
            b.send_text("hello")
            self.assertTrue(wait_until(lambda: len(a.chat.get_history(b.peer_id)) == 2))
            source = Path(folder) / "dữ liệu.bin"
            source.write_bytes(bytes(range(256)) * 300)
            a.send_file(str(source))
            a.send_text("while sending")
            self.assertTrue(wait_until(lambda: (Path(folder) / "b" / source.name).exists()))
            self.assertEqual((Path(folder) / "b" / source.name).read_bytes(), source.read_bytes())
            self.assertTrue(wait_until(lambda: len(b.chat.get_history(a.peer_id)) == 3))
            a.leave()
            self.assertIsNone(a.chat.current_peer)
            self.assertIsNotNone(a.connections.get_connection(b.peer_id))
            a.stop()
            b.stop()
