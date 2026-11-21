import tempfile
import threading
import unittest
from pathlib import Path

from lanchat.protocol import Frame, MessageType, ProtocolError, encode_json
from lanchat.transfer import CHUNK_SIZE, TransferManager


class Link:
    def __init__(self):
        self.handlers = []
        self.disconnect_handlers = []
        self.other = None

    def add_message_handler(self, handler):
        self.handlers.append(handler)

    def add_disconnect_handler(self, handler):
        self.disconnect_handlers.append(handler)

    def send(self, peer_id, kind, payload=b""):
        for handler in self.other.handlers:
            handler("sender" if peer_id == "receiver" else "receiver", Frame(kind, payload))


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        a, b = Link(), Link()
        a.other, b.other = b, a
        self.sender_events, self.receiver_events = [], []
        self.sender = TransferManager(a, self.root / "unused", self.sender_events.append)
        self.receiver = TransferManager(b, self.root / "downloads", self.receiver_events.append)
        self.addCleanup(self.sender.stop)
        self.addCleanup(self.receiver.stop)

    def wait_transfer(self):
        for worker in list(self.sender._workers):
            worker.join(2)
            self.assertFalse(worker.is_alive())

    def test_files_and_collision(self):
        for name, data in (("small.txt", b"hello"), ("trống.txt", b""),
                           ("nhị phân.bin", bytes(range(256)) * 600)):
            source = self.root / name
            source.write_bytes(data)
            self.sender.send_file("receiver", source)
            self.wait_transfer()
            self.assertEqual((self.root / "downloads" / name).read_bytes(), data)
            self.assertIn("verified", self.sender_events[-1])
            self.assertTrue(any(f"Sending {name}: 100%" in event for event in self.sender_events))
            self.assertTrue(any(f"Receiving {name}: 100%" in event for event in self.receiver_events))
        source = self.root / "small.txt"
        self.sender.send_file("receiver", source)
        self.wait_transfer()
        self.assertEqual((self.root / "downloads" / "small (1).txt").read_bytes(), b"hello")

    def test_invalid_input_and_partial_cleanup(self):
        with self.assertRaises(ValueError):
            self.sender.send_file("receiver", self.root / "missing")
        for name in ("../escape", "a/b", "a\\b", ".."):
            with self.assertRaises(ProtocolError):
                self.receiver.handle_frame("sender", Frame(MessageType.FILE_META, encode_json({"transfer_id": "1", "name": name, "size": 1})))
        with self.assertRaises(ProtocolError):
            self.receiver.handle_frame("sender", Frame(MessageType.FILE_CHUNK, b"x"))
        self.receiver.handle_frame("sender", Frame(MessageType.FILE_META, encode_json({"transfer_id": "1", "name": "partial", "size": 2})))
        self.receiver.handle_frame("sender", Frame(MessageType.FILE_CHUNK, b"x"))
        self.receiver._disconnected("sender", None)
        self.assertEqual(list((self.root / "downloads").iterdir()), [])

    def test_checksum_failure_removes_partial(self):
        self.receiver.handle_frame("sender", Frame(MessageType.FILE_META, encode_json({"transfer_id": "1", "name": "bad", "size": 1})))
        self.receiver.handle_frame("sender", Frame(MessageType.FILE_CHUNK, b"x"))
        self.receiver.handle_frame("sender", Frame(MessageType.FILE_END, encode_json({"transfer_id": "1", "sha256": "bad"})))
        self.assertEqual(list((self.root / "downloads").iterdir()), [])

    def test_receive_progress_is_not_repeated_within_a_decile(self):
        self.receiver.handle_frame("sender", Frame(MessageType.FILE_META, encode_json({"transfer_id": "1", "name": "slow.bin", "size": 1000})))
        for _ in range(5):
            self.receiver.handle_frame("sender", Frame(MessageType.FILE_CHUNK, b"x"))

        self.assertEqual(self.receiver_events, ["Receiving slow.bin: 0%"])
        self.receiver._disconnected("sender", None)
