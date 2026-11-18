"""TV1 presence, registry, and local UDP tests."""

import socket
import time
import unittest

from lanchat.discovery import Discovery, parse_presence
from lanchat.peer_registry import PeerRegistry


class RegistryTests(unittest.TestCase):
    def test_update_status_expire_and_events(self):
        events = []
        registry = PeerRegistry(lambda kind, peer: events.append((kind, peer.name)))
        registry.update("A", "127.0.0.1", 5001, "online", now=0)
        registry.update("A", "127.0.0.1", 5001, "away", now=3)
        registry.update("A", "127.0.0.1", 5002, "online", now=3)
        self.assertEqual(len(registry.list_peers()), 2)
        self.assertEqual(registry.list_peers()[0].status, "away")
        self.assertEqual(registry.expire(10, now=12), [])
        self.assertEqual(len(registry.expire(10, now=13)), 2)
        self.assertEqual(events, [("online", "A"), ("online", "A"),
                                  ("offline", "A"), ("offline", "A")])

    def test_invalid_datagrams(self):
        for data in (b"", b"HELLO|A|no|online", b"HELLO|A|0|online",
                     b"HELLO|A|5001|busy", b"HELLO|A|5001|online|",
                     b"HELLO||5001|online", b"HELLO|A\nB|5001|online",
                     b"\xff", b"X" * 513):
            self.assertIsNone(parse_presence(data))
        self.assertEqual(parse_presence(b"HELLO|A|5001|away"), ("A", 5001, "away", ""))
        self.assertEqual(parse_presence(b"HELLO|A|5001|away|abc"),
                         ("A", 5001, "away", "abc"))


class SocketTests(unittest.TestCase):
    def test_three_instances_status_self_filter_and_shutdown(self):
        if not hasattr(socket, "SO_REUSEPORT"):
            self.skipTest("shared UDP port needs SO_REUSEPORT on this OS")
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("", 0))
        port = probe.getsockname()[1]
        probe.close()
        registries = [PeerRegistry() for _ in range(3)]
        nodes = [Discovery(str(i), 5001 + i, registries[i], udp_port=port,
                           broadcast_address="255.255.255.255") for i in range(3)]
        try:
            for node in nodes:
                node.start()
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if all(len(registry.list_peers()) == 2 for registry in registries):
                    break
                time.sleep(0.05)
            self.assertEqual([len(r.list_peers()) for r in registries], [2, 2, 2])
            self.assertTrue(all(p.peer_id for r in registries for p in r.list_peers()))
            nodes[0].set_status("away")
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if all(any(p.name == "0" and p.status == "away" for p in r.list_peers())
                       for r in registries[1:]):
                    break
                time.sleep(0.05)
            self.assertTrue(all(any(p.name == "0" and p.status == "away"
                                    for p in r.list_peers()) for r in registries[1:]))
        finally:
            threads = [thread for node in nodes for thread in node._threads]
            for node in nodes:
                node.stop()
        self.assertTrue(all(not thread.is_alive() for thread in threads))

    def test_occupied_port_without_reuse(self):
        guard = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        guard.bind(("", 0))
        port = guard.getsockname()[1]
        node = Discovery("A", 5001, PeerRegistry(), udp_port=port)
        try:
            with self.assertRaises(OSError):
                node.start()
        finally:
            guard.close()
            node.stop()

    def test_heartbeat_interval_and_expiration(self):
        if not hasattr(socket, "SO_REUSEPORT"):
            self.skipTest("shared UDP port needs SO_REUSEPORT on this OS")
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("", 0))
        port = probe.getsockname()[1]
        probe.close()
        events = []
        first = Discovery("A", 5001, PeerRegistry(), udp_port=port)
        second_registry = PeerRegistry(lambda kind, peer: events.append(kind))
        second = Discovery("B", 5002, second_registry, udp_port=port)
        try:
            first.start()
            second.start()
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not second_registry.list_peers():
                time.sleep(0.05)
            self.assertTrue(second_registry.list_peers())
            seen = second_registry.list_peers()[0].last_seen
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                current = second_registry.list_peers()[0].last_seen
                if current > seen:
                    break
                time.sleep(0.05)
            self.assertGreater(current - seen, 2.5)
            self.assertLess(current - seen, 3.5)
            first.stop()
            deadline = time.monotonic() + 11
            while time.monotonic() < deadline and second_registry.list_peers():
                time.sleep(0.1)
            self.assertEqual(second_registry.list_peers(), [])
            self.assertEqual(events, ["online", "offline"])
        finally:
            first.stop()
            second.stop()
