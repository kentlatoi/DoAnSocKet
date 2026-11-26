"""Xử lý lệnh CLI và giữ nguyên prompt khi có thông báo bất đồng bộ."""

import threading

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


HELP = "/list, /chat <name|number>, /send <file>, /leave, /status <online|away>, /help, /quit"


class CLI:
    """Nhận callback từ Application để chuyển lệnh người dùng xuống backend."""

    def __init__(self, registry, discovery, on_chat=None, on_send=None,
                 on_leave=None, on_text=None, on_quit=None, session=None):
        """Gắn registry, discovery và callback của Application vào CLI."""
        self.registry, self.discovery = registry, discovery
        self.on_chat, self.on_send = on_chat, on_send
        self.on_leave, self.on_text, self.on_quit = on_leave, on_text, on_quit
        self.session = session or PromptSession()
        self._output_lock = threading.Lock()

    def notify(self, message):
        """Hiển thị event peer, chat và tiến độ an toàn giữa các thread."""
        with self._output_lock:
            print(message, flush=True)

    def handle(self, line):
        """Xử lý một dòng; chỉ trả về False khi người dùng yêu cầu /quit."""
        line = line.strip()
        if not line:
            return True
        if not line.startswith("/"):
            self._call(self.on_text, line)
            return True
        command, _, argument = line.partition(" ")
        argument = argument.strip()
        if command == "/help" and not argument:
            self.notify(HELP)
        elif command == "/list" and not argument:
            peers = self.registry.list_peers()
            if not peers:
                self.notify("No peers online.")
            for number, peer in enumerate(peers, 1):
                self.notify(f"{number}. {peer.name} ({peer.ip}:{peer.tcp_port}) {peer.status}")
        elif command == "/chat" and argument:
            peers = self.registry.list_peers()
            if argument.isdecimal():
                number = int(argument)
                peer = peers[number - 1] if 1 <= number <= len(peers) else None
            else:
                matches = [peer for peer in peers if peer.name == argument]
                peer = matches[0] if len(matches) == 1 else None
            if peer is None:
                self.notify("Peer not found or name is ambiguous. Use /list and a number.")
            else:
                self._call(self.on_chat, peer)
        elif command == "/send" and argument:
            self._call(self.on_send, argument)
        elif command == "/leave" and not argument:
            self._call(self.on_leave)
        elif command == "/status" and argument in ("online", "away"):
            self.discovery.set_status(argument)
            self.notify(f"Status: {argument}")
        elif command == "/quit" and not argument:
            self._call(self.on_quit)
            return False
        else:
            self.notify(f"Invalid command. {HELP}")
        return True

    def _call(self, callback, *args):
        """Gọi tác vụ backend nếu đã được nối với CLI."""
        if callback is None:
            self.notify("This action is unavailable until the chat/file backend is connected.")
        else:
            callback(*args)

    def run(self):
        """Chạy vòng lặp nhập lệnh cho đến khi người dùng thoát."""
        # patch_stdout vẽ lại prompt và phần đang gõ sau khi thread khác in thông báo.
        with patch_stdout():
            try:
                while self.handle(self.session.prompt("> ")):
                    pass
            except (EOFError, KeyboardInterrupt):
                self._call(self.on_quit)
