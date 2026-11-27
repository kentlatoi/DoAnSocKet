"""TV1 command dispatch and prompt-buffer checks."""

import threading
import time
import unittest
from unittest.mock import patch

from prompt_toolkit import PromptSession
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from lanchat.cli import CLI
from lanchat.peer_registry import PeerRegistry


class DiscoveryStub:
    def __init__(self):
        self.status = "online"

    def set_status(self, status):
        self.status = status


class CLITests(unittest.TestCase):
    def setUp(self):
        self.registry = PeerRegistry()
        self.registry.update("A", "127.0.0.1", 5001, "online", now=1)
        self.discovery = DiscoveryStub()
        self.calls = []
        self.cli = CLI(self.registry, self.discovery,
                       on_chat=lambda peer: self.calls.append(("chat", peer.tcp_port)),
                       on_send=lambda path: self.calls.append(("send", path)),
                       on_leave=lambda: self.calls.append(("leave",)),
                       on_text=lambda line: self.calls.append(("text", line)),
                       on_quit=lambda: self.calls.append(("quit",)),
                       session=object())
        self.messages = []
        notify_patch = patch.object(self.cli, "notify", side_effect=self.messages.append)
        notify_patch.start()
        self.addCleanup(notify_patch.stop)

    def test_commands(self):
        for line in ("/list", "/chat A", "/chat 1", "/send file.txt",
                     "/leave", "/status away", "/help", "hello"):
            self.assertTrue(self.cli.handle(line))
        self.assertFalse(self.cli.handle("/quit"))
        self.assertEqual(self.discovery.status, "away")
        self.assertEqual(self.calls, [("chat", 5001), ("chat", 5001),
                                      ("send", "file.txt"), ("leave",),
                                      ("text", "hello"), ("quit",)])
        self.assertIn("A (127.0.0.1:5001) online", self.messages[0])

    def test_invalid_missing_and_duplicate_names(self):
        self.registry.update("A", "127.0.0.1", 5002, "online", now=1)
        for line in ("/chat A", "/chat 9", "/chat", "/send", "/status busy",
                     "/unknown", "/list extra", "/quit now", ""):
            self.assertTrue(self.cli.handle(line))
        self.assertEqual(self.calls, [])
        self.assertTrue(any("ambiguous" in message for message in self.messages))
        self.assertTrue(any("Invalid command" in message for message in self.messages))

    def test_unavailable_backend_and_concurrent_notifications(self):
        cli = CLI(self.registry, self.discovery, session=object())
        messages = []
        with patch.object(cli, "notify", side_effect=messages.append):
            cli.handle("/send file.txt")
        self.assertIn("unavailable", messages[0])
        threads = [threading.Thread(target=cli.notify, args=(f"notice {i}",))
                   for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def test_partial_input_survives_notification(self):
        with create_pipe_input() as source:
            received = []
            session = PromptSession(input=source, output=DummyOutput())
            cli = CLI(self.registry, self.discovery, on_text=received.append,
                      session=session)
            thread = threading.Thread(target=cli.run)
            thread.start()
            try:
                source.send_text("hel")
                time.sleep(0.1)
                cli.notify("peer online")
                source.send_text("lo\n/quit\n")
                thread.join(timeout=3)
                self.assertEqual(received, ["hello"])
            finally:
                if thread.is_alive():
                    source.send_text("/quit\n")
                    thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
