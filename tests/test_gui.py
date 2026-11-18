"""GUI event handling without requiring a graphical display."""

import importlib
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from lanchat.chat import ChatEvent, ChatMessage
from lanchat.app import Application


class GUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tkinter = types.ModuleType("tkinter")
        tkinter.filedialog = types.ModuleType("tkinter.filedialog")
        tkinter.ttk = types.ModuleType("tkinter.ttk")
        with patch.dict(sys.modules, {"tkinter": tkinter,
                                      "tkinter.filedialog": tkinter.filedialog,
                                      "tkinter.ttk": tkinter.ttk}):
            cls.GUI = importlib.import_module("lanchat.gui").GUI

    def test_network_events_are_drained_on_gui_thread(self):
        gui = self.GUI.__new__(self.GUI)
        gui.events = self.GUI._drain.__globals__["queue"].Queue()
        gui.root = Mock()
        gui.notice = Mock()
        gui.progress = {}
        gui._closing = False
        gui._render = Mock()
        gui._refresh_peers = Mock()
        gui.app = Mock()
        gui.app.chat.current_peer = "bob"
        message = ChatMessage("bob", "Bob", "hello", "now", True)
        gui.events.put(("chat", ChatEvent(message, 0)))
        gui.events.put(("notice", "Receiving file.bin: 40%"))

        gui._drain()

        gui._render.assert_called_once_with("bob")
        self.assertEqual(gui.progress["value"], 40)
        gui.root.after.assert_called_once_with(50, gui._drain)

    def test_send_uses_selected_conversation(self):
        gui = self.GUI.__new__(self.GUI)
        gui.app = Mock()
        gui.app.chat.current_peer = "bob"
        gui.peers = Mock()
        gui.peers.selection.return_value = ("bob",)
        gui.message = Mock()
        gui.message.get.return_value = "  hello  "
        gui.events = Mock()
        gui._worker = lambda action: action()

        gui._send()

        gui.app.chat.send_message.assert_called_once_with("bob", "hello")
        gui.events.put.assert_called_once_with(("sent", "bob"))

    def test_backend_forwards_chat_to_gui_without_cli_output(self):
        app = Application("Alice")
        events = []
        app.gui_event = lambda kind, value: events.append((kind, value))
        message = ChatMessage("bob", "Bob", "hello", "now", True)
        event = ChatEvent(message, 1)

        app._chat_event(event)
        app.notify("Receiving file.bin: 40%")

        self.assertEqual(events, [("chat", event), ("notice", "Receiving file.bin: 40%")])

    def test_gui_event_bridge_receives_cli_peer_message(self):
        with tempfile.TemporaryDirectory() as folder:
            gui = Application("GUI", udp_port=18121, broadcast_address="127.0.0.1",
                              downloads=Path(folder) / "gui")
            cli = Application("CLI", udp_port=18122, broadcast_address="127.0.0.1",
                              downloads=Path(folder) / "cli")
            events = []
            gui.gui_event = lambda kind, value: events.append((kind, value))
            self.addCleanup(gui.stop)
            self.addCleanup(cli.stop)
            gui.start()
            cli.start()
            self.assertIsNone(gui.cli)
            gui.connections.connect("127.0.0.1", cli.connections.port, expected_peer_id=cli.peer_id)
            cli.chat.send_message(gui.peer_id, "hello from CLI")
            deadline = time.monotonic() + 3
            while not any(kind == "chat" for kind, _ in events) and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(any(kind == "chat" and value.message.text == "hello from CLI"
                                for kind, value in events))

    def test_close_stops_backend_then_destroys_window(self):
        gui = self.GUI.__new__(self.GUI)
        gui.events = self.GUI._drain.__globals__["queue"].Queue()
        gui.app = Mock()
        stopped = threading.Event()
        gui.app.stop.side_effect = stopped.set
        gui.root = Mock()
        gui.notice = Mock()
        gui._closing = False

        gui.close()
        self.assertTrue(stopped.wait(1))
        gui._wait_for_stop()

        gui.app.stop.assert_called_once()
        gui.root.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
