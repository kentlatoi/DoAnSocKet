"""Compose discovery, TCP chat, file transfer, and the responsive CLI."""

import uuid

from .chat import ChatManager
from .cli import CLI
from .connections import ConnectionManager
from .discovery import Discovery
from .peer_registry import PeerRegistry
from .transfer import TransferManager


class Application:
    def __init__(self, name, port=0, udp_port=9999, broadcast_address="255.255.255.255", downloads="downloads", session=None):
        self.peer_id = uuid.uuid4().hex
        self.name = name
        self.registry = PeerRegistry(on_event=self._peer_event)
        self.connections = ConnectionManager(self.peer_id, name, port=port)
        self.discovery = None
        self.chat = ChatManager(self.connections, name, on_event=self._chat_event)
        self.transfer = TransferManager(self.connections, downloads, notify=self.notify)
        self.cli = None
        self.udp_port = udp_port
        self.broadcast_address = broadcast_address
        self.session = session
        self.connections.add_disconnect_handler(self._disconnect_event)
        self._stopped = False
        self.gui_event = None

    def start(self):
        try:
            port = self.connections.start()
            self.discovery = Discovery(self.name, port, self.registry, self.udp_port,
                                       self.broadcast_address, on_error=lambda error: self.notify(f"UDP error: {error}"),
                                       peer_id=self.peer_id)
            if self.gui_event is None:
                self.cli = CLI(self.registry, self.discovery, on_chat=self.select_peer,
                               on_send=self.send_file, on_leave=self.leave, on_text=self.send_text,
                               on_quit=self.stop, session=self.session)
            self.discovery.start()
        except Exception:
            self.stop()
            raise
        self.notify(f"Ready as {self.name} on TCP port {port}. Type /help for commands.")
        return port

    def run(self):
        self.start()
        try:
            cli = self.cli
            if cli is None:
                raise RuntimeError("CLI is unavailable")
            cli.run()
        finally:
            self.stop()

    def notify(self, message):
        if self.gui_event:
            self.gui_event("notice", message)
        elif self.cli:
            self.cli.notify(message)

    def select_peer(self, peer):
        if not peer.peer_id:
            self.notify("This peer has no discovery ID; verified chat is unavailable.")
            return
        try:
            if self.connections.get_connection(peer.peer_id) is None:
                self.connections.connect(peer.ip, peer.tcp_port, expected_peer_id=peer.peer_id)
            unread = self.chat.select_peer(peer.peer_id)
            self.notify(f"Chatting with {peer.name}.")
            for message in unread:
                self.notify(f"{message.sender}: {message.text}")
        except (OSError, ValueError, RuntimeError) as error:
            self.notify(f"Cannot connect to {peer.name}: {error}")

    def send_text(self, text):
        peer_id = self.chat.current_peer
        if peer_id is None:
            self.notify("Choose a peer with /chat first.")
            return
        try:
            self.chat.send_message(peer_id, text)
        except (OSError, ValueError, RuntimeError) as error:
            self.notify(f"Message failed: {error}")

    def send_file(self, path):
        peer_id = self.chat.current_peer
        if peer_id is None:
            self.notify("Choose a peer with /chat first.")
            return
        try:
            self.transfer.send_file(peer_id, path)
        except (OSError, ValueError, RuntimeError) as error:
            self.notify(f"File transfer failed: {error}")

    def leave(self):
        self.chat.leave_chat()
        self.notify("Left chat. Connections remain available.")

    def _peer_event(self, kind, peer):
        if self.gui_event:
            self.gui_event("peers", None)
        if kind == "status_changed":
            self.notify(f"Peer {peer.name} is now {peer.status}")
        else:
            self.notify(f"Peer {kind}: {peer.name} ({peer.ip}:{peer.tcp_port})")

    def _chat_event(self, event):
        if self.gui_event:
            self.gui_event("chat", event)
            return
        message = event.message
        if event.unread_count:
            self.notify(f"{message.sender}: {event.unread_count} unread message(s). Use /chat to view.")
        else:
            self.notify(f"{message.sender}: {message.text}")

    def _disconnect_event(self, peer_id, error):
        self.notify(f"Peer disconnected: {peer_id}" + (f" ({error})" if error else ""))

    def stop(self):
        if self._stopped:
            return
        self._stopped = True
        if self.discovery:
            self.discovery.stop()
        self.transfer.stop()
        self.connections.stop()
