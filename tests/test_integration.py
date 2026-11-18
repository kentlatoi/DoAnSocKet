"""Real loopback TCP integration; UDP socket lifecycle is exercised by start()."""

import tempfile
import time
import unittest
from pathlib import Path

from lanchat.app import Application
from lanchat.peer_registry import Peer
from lanchat.protocol import MessageType, encode_json


def wait_until(check, timeout=3):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if check():
            return True
        time.sleep(0.01)
    return False


class ApplicationTests(unittest.TestCase):
    def test_three_peers_unread_switch_and_interrupted_file(self):
        with tempfile.TemporaryDirectory() as folder:
            nodes = [Application(name, udp_port=18101 + index,
                                 broadcast_address="127.0.0.1",
                                 downloads=Path(folder) / name)
                     for index, name in enumerate(("Alice", "Bob", "Carol"))]
            for node in nodes:
                self.addCleanup(node.stop)
                node.start()
            alice, bob, carol = nodes
            notices = []
            alice.cli.notify = notices.append
            for remote in (bob, carol):
                alice.select_peer(alice.registry.update(remote.name, "127.0.0.1",
                                                        remote.connections.port, "online",
                                                        peer_id=remote.peer_id))
            self.assertEqual(set(alice.connections.connected_peers()), {bob.peer_id, carol.peer_id})
            self.assertEqual(alice.chat.current_peer, carol.peer_id)
            bob.chat.send_message(alice.peer_id, "first unread")
            self.assertTrue(wait_until(lambda: alice.chat.unread_count(bob.peer_id) == 1))
            alice.chat.send_message(bob.peer_id, "outgoing before switch")
            peer_bob = next(peer for peer in alice.registry.list_peers() if peer.peer_id == bob.peer_id)
            alice.select_peer(peer_bob)
            self.assertEqual(alice.chat.unread_count(bob.peer_id), 0)
            self.assertEqual(alice.chat.current_peer, bob.peer_id)
            self.assertTrue(any("first unread" in notice for notice in notices))
            self.assertIsNotNone(alice.connections.get_connection(carol.peer_id))

            bob.connections.send(alice.peer_id, MessageType.FILE_META,
                                 encode_json({"transfer_id": "partial", "name": "interrupted.bin", "size": 100}))
            bob.connections.send(alice.peer_id, MessageType.FILE_CHUNK, b"partial")
            self.assertTrue(wait_until(lambda: bool(list((Path(folder) / "Alice").glob("*.part")))))
            bob.connections.disconnect(alice.peer_id)
            self.assertTrue(wait_until(lambda: not list((Path(folder) / "Alice").glob("*.part"))))
            self.assertFalse((Path(folder) / "Alice" / "interrupted.bin").exists())

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
