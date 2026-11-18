import threading
import unittest

from lanchat.chat import ChatManager
from lanchat.protocol import Frame, MessageType, ProtocolError, encode_json


class FakeConnections:
    def __init__(self) -> None:
        self.handlers = []
        self.sent = []

    def add_message_handler(self, handler) -> None:
        self.handlers.append(handler)

    def send(self, peer_id, message_type, payload=b"") -> None:
        self.sent.append((peer_id, message_type, payload))

    def receive(self, peer_id, text, sender="Remote") -> None:
        frame = Frame(
            MessageType.CHAT,
            encode_json(
                {
                    "sender": sender,
                    "text": text,
                    "sent_at": "2026-11-13T12:00:00+00:00",
                }
            ),
        )
        for handler in self.handlers:
            handler(peer_id, frame)


class ChatManagerTests(unittest.TestCase):
    def test_send_records_history_and_utf8_payload(self) -> None:
        connections = FakeConnections()
        chat = ChatManager(connections, "Hương")

        sent = chat.send_message("bob", "Chào Bob 👋")

        self.assertEqual(sent.text, "Chào Bob 👋")
        self.assertFalse(sent.incoming)
        self.assertEqual(chat.get_history("bob"), [sent])
        self.assertEqual(connections.sent[0][1], MessageType.CHAT)
        self.assertIn("Chào Bob 👋".encode(), connections.sent[0][2])

    def test_history_and_unread_are_isolated_per_peer(self) -> None:
        connections = FakeConnections()
        events = []
        chat = ChatManager(connections, "Me", events.append)
        chat.select_peer("alice")

        connections.receive("alice", "visible now", "Alice")
        connections.receive("bob", "first unread", "Bob")
        connections.receive("bob", "second unread", "Bob")

        self.assertEqual(chat.unread_count("alice"), 0)
        self.assertEqual(chat.unread_count("bob"), 2)
        self.assertEqual(len(chat.get_history("alice")), 1)
        self.assertEqual(len(chat.get_history("bob")), 2)
        self.assertEqual(events[-1].unread_count, 2)

        unread = chat.select_peer("bob")
        self.assertEqual(
            [message.text for message in unread],
            [
                "first unread",
                "second unread",
            ],
        )
        self.assertEqual(chat.unread_count("bob"), 0)

    def test_shared_chat_state_is_thread_safe(self) -> None:
        connections = FakeConnections()
        chat = ChatManager(connections, "Me")
        threads = [
            threading.Thread(
                target=connections.receive, args=("bob", f"message-{index}")
            )
            for index in range(50)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(chat.get_history("bob")), 50)
        self.assertEqual(chat.unread_count("bob"), 50)

    def test_sent_message_does_not_replace_unread_incoming_message(self) -> None:
        connections = FakeConnections()
        chat = ChatManager(connections, "Me")
        connections.receive("bob", "unread", "Bob")
        chat.send_message("bob", "my reply")
        self.assertEqual([message.text for message in chat.select_peer("bob")], ["unread"])

    def test_invalid_chat_payload_is_rejected(self) -> None:
        chat = ChatManager(FakeConnections(), "Me")
        with self.assertRaises(ProtocolError):
            chat.handle_frame(
                "bob",
                Frame(MessageType.CHAT, encode_json({"text": "", "sent_at": "now"})),
            )


if __name__ == "__main__":
    unittest.main()
