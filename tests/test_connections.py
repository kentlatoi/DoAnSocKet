import socket
import threading
import time
import unittest

from lanchat.connections import ConnectionManager, NotConnectedError
from lanchat.protocol import MessageType


def wait_until(predicate, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition was not met before timeout")


class ConnectionManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.managers: list[ConnectionManager] = []

    def tearDown(self) -> None:
        for manager in self.managers:
            manager.stop()

    def manager(self, peer_id: str) -> ConnectionManager:
        manager = ConnectionManager(peer_id, peer_id.title(), "127.0.0.1", 0)
        manager.start()
        self.managers.append(manager)
        return manager

    def test_connect_send_receive_and_disconnect(self) -> None:
        alice = self.manager("alice")
        bob = self.manager("bob")
        received = []
        disconnected = []
        bob.add_message_handler(
            lambda peer_id, frame: received.append((peer_id, frame))
        )
        bob.add_disconnect_handler(
            lambda peer_id, error: disconnected.append((peer_id, error))
        )

        alice.connect("127.0.0.1", bob.port)
        wait_until(lambda: bob.connected_peers() == ["alice"])
        alice.send("bob", MessageType.CHAT, "xin chào".encode())
        wait_until(lambda: len(received) == 1)

        self.assertEqual(received[0][0], "alice")
        self.assertEqual(received[0][1].payload.decode(), "xin chào")
        alice.disconnect("bob")
        wait_until(lambda: bool(disconnected))
        self.assertEqual(disconnected[0][0], "alice")

    def test_one_peer_keeps_connections_to_multiple_peers(self) -> None:
        alice = self.manager("alice")
        bob = self.manager("bob")
        carol = self.manager("carol")

        alice.connect("127.0.0.1", bob.port)
        alice.connect("127.0.0.1", carol.port)

        self.assertCountEqual(alice.connected_peers(), ["bob", "carol"])
        wait_until(lambda: bob.connected_peers() == ["alice"])
        wait_until(lambda: carol.connected_peers() == ["alice"])

    def test_full_duplex_continuous_messages(self) -> None:
        alice = self.manager("alice")
        bob = self.manager("bob")
        alice_received = []
        bob_received = []
        alice.add_message_handler(
            lambda peer_id, frame: alice_received.append(frame.payload)
        )
        bob.add_message_handler(
            lambda peer_id, frame: bob_received.append(frame.payload)
        )
        alice.connect("127.0.0.1", bob.port)
        wait_until(lambda: bob.connected_peers() == ["alice"])

        for index in range(20):
            alice.send("bob", MessageType.CHAT, f"a-{index}".encode())
            bob.send("alice", MessageType.CHAT, f"b-{index}".encode())

        wait_until(lambda: len(alice_received) == len(bob_received) == 20)
        self.assertEqual(alice_received[-1], b"b-19")
        self.assertEqual(bob_received[-1], b"a-19")

    def test_abrupt_peer_shutdown_removes_connection(self) -> None:
        alice = self.manager("alice")
        bob = self.manager("bob")
        disconnected = []
        alice.add_disconnect_handler(
            lambda peer_id, error: disconnected.append((peer_id, error))
        )
        alice.connect("127.0.0.1", bob.port)

        bob.stop()

        wait_until(lambda: alice.connected_peers() == [])
        self.assertEqual(disconnected[0][0], "bob")

    def test_simultaneous_connect_is_deduplicated(self) -> None:
        alice = self.manager("alice")
        bob = self.manager("bob")
        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def connect(manager: ConnectionManager, port: int) -> None:
            try:
                barrier.wait()
                manager.connect("127.0.0.1", port)
            except (OSError, ValueError, RuntimeError) as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=connect, args=(alice, bob.port)),
            threading.Thread(target=connect, args=(bob, alice.port)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        wait_until(lambda: alice.connected_peers() == ["bob"])
        wait_until(lambda: bob.connected_peers() == ["alice"])
        self.assertEqual(errors, [])
        self.assertTrue(alice.get_connection("bob").outgoing)
        self.assertFalse(bob.get_connection("alice").outgoing)

    def test_send_to_missing_peer_is_reported(self) -> None:
        alice = self.manager("alice")
        with self.assertRaises(NotConnectedError):
            alice.send("missing", MessageType.CHAT, b"hello")

    def test_connection_refused_does_not_break_listener(self) -> None:
        alice = self.manager("alice")
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        unused_port = probe.getsockname()[1]
        probe.close()

        with self.assertRaises(OSError):
            alice.connect("127.0.0.1", unused_port)

        self.assertEqual(alice.connected_peers(), [])


if __name__ == "__main__":
    unittest.main()
