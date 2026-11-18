import socket
import struct
import threading
import unittest

from lanchat.protocol import (
    HEADER,
    MAGIC,
    MAX_PAYLOAD_SIZE,
    VERSION,
    ConnectionClosed,
    IncompleteFrame,
    MessageType,
    ProtocolError,
    decode_json,
    encode_frame,
    encode_json,
    recv_frame,
)


class ProtocolTests(unittest.TestCase):
    def test_utf8_json_round_trip_uses_byte_length(self) -> None:
        payload = encode_json({"text": "Xin chào Việt Nam 👋"})
        frame = encode_frame(MessageType.CHAT, payload)
        _, _, _, declared_size = HEADER.unpack(frame[: HEADER.size])

        self.assertEqual(declared_size, len(payload))
        self.assertEqual(decode_json(payload)["text"], "Xin chào Việt Nam 👋")

    def test_recv_frame_handles_fragmented_stream(self) -> None:
        reader, writer = socket.socketpair()
        data = encode_frame(MessageType.CHAT, "chia nhỏ".encode())

        def send_fragments() -> None:
            for byte in data:
                writer.sendall(bytes([byte]))
            writer.close()

        thread = threading.Thread(target=send_fragments)
        thread.start()
        try:
            frame = recv_frame(reader)
            self.assertEqual(frame.message_type, MessageType.CHAT)
            self.assertEqual(frame.payload.decode(), "chia nhỏ")
        finally:
            reader.close()
            thread.join()

    def test_recv_frame_separates_combined_frames(self) -> None:
        reader, writer = socket.socketpair()
        try:
            writer.sendall(
                encode_frame(MessageType.CHAT, b"first")
                + encode_frame(MessageType.CHAT, b"second")
            )
            self.assertEqual(recv_frame(reader).payload, b"first")
            self.assertEqual(recv_frame(reader).payload, b"second")
        finally:
            reader.close()
            writer.close()

    def test_clean_close_and_partial_payload_are_distinct(self) -> None:
        reader, writer = socket.socketpair()
        writer.close()
        with self.assertRaises(ConnectionClosed):
            recv_frame(reader)
        reader.close()

        reader, writer = socket.socketpair()
        writer.sendall(encode_frame(MessageType.CHAT, b"hello")[:-2])
        writer.close()
        try:
            with self.assertRaises(IncompleteFrame):
                recv_frame(reader)
        finally:
            reader.close()

    def test_invalid_headers_and_json_are_rejected(self) -> None:
        invalid_headers = [
            struct.pack("!4sBBI", b"FAIL", VERSION, MessageType.CHAT, 0),
            struct.pack("!4sBBI", MAGIC, VERSION + 1, MessageType.CHAT, 0),
            struct.pack("!4sBBI", MAGIC, VERSION, 255, 0),
            struct.pack(
                "!4sBBI",
                MAGIC,
                VERSION,
                MessageType.CHAT,
                MAX_PAYLOAD_SIZE + 1,
            ),
        ]
        for header in invalid_headers:
            with self.subTest(header=header):
                reader, writer = socket.socketpair()
                writer.sendall(header)
                try:
                    with self.assertRaises(ProtocolError):
                        recv_frame(reader)
                finally:
                    reader.close()
                    writer.close()

        for payload in (b"not-json", b"[]", b'"text"'):
            with self.subTest(payload=payload), self.assertRaises(ProtocolError):
                decode_json(payload)


if __name__ == "__main__":
    unittest.main()
