"""Giao diện Tkinter cho các chức năng LAN Chat hiện có."""

import queue
import re
import threading
import tkinter as tk
from tkinter import filedialog, ttk


class GUI:
    """Hiển thị peer, chat và transfer; nhận event backend qua queue."""

    def __init__(self, app, root=None):
        """Tạo widget và nối callback backend vào Event Queue của GUI."""
        self.app = app
        self.root = root or tk.Tk()
        self.root.title(f"LAN Chat — {app.name}")
        self.root.geometry("760x480")
        # Network thread chỉ đưa event vào queue; Tkinter main thread sẽ cập nhật widget.
        self.events = queue.Queue()
        self.app.gui_event = lambda kind, value: self.events.put((kind, value))
        self._closing = False
        # Giữ snapshot peer đã từng thấy để vẫn hiển thị lịch sử khi offline.
        self._peers = {}

        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(frame, text=f"{app.name}  •  LAN Chat", font=("TkDefaultFont", 15, "bold")).grid(row=0, column=0, sticky="w")
        self.status = tk.StringVar(value="online")
        status = ttk.Combobox(frame, textvariable=self.status, values=("online", "away"), state="readonly", width=9)
        status.grid(row=0, column=1, sticky="e")
        status.bind("<<ComboboxSelected>>", lambda _: self.app.discovery.set_status(self.status.get()))

        self.peers = ttk.Treeview(frame, columns=("status", "unread"), show="tree headings", height=12)
        self.peers.heading("#0", text="Peers")
        self.peers.heading("status", text="Status")
        self.peers.heading("unread", text="Unread")
        self.peers.column("#0", width=170)
        self.peers.column("status", width=70, anchor="center")
        self.peers.column("unread", width=55, anchor="center")
        self.peers.grid(row=1, column=0, sticky="nsew", pady=10)
        self.peers.bind("<<TreeviewSelect>>", self._select)

        chat = ttk.Frame(frame)
        chat.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=10)
        chat.rowconfigure(1, weight=1)
        chat.columnconfigure(0, weight=1)
        self.title = ttk.Label(chat, text="Select a peer to chat")
        self.title.grid(row=0, column=0, sticky="w")
        self.history = tk.Text(chat, state="disabled", wrap="word", height=16)
        self.history.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(chat, command=self.history.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.history.configure(yscrollcommand=scroll.set)

        compose = ttk.Frame(chat)
        compose.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        compose.columnconfigure(0, weight=1)
        self.message = ttk.Entry(compose)
        self.message.grid(row=0, column=0, sticky="ew")
        self.message.bind("<Return>", self._send)
        ttk.Button(compose, text="Send", command=self._send).grid(row=0, column=1, padx=(6, 0))
        ttk.Button(compose, text="Send file…", command=self._file).grid(row=0, column=2, padx=(6, 0))

        self.progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
        self.progress.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.notice = tk.StringVar(value="Starting…")
        ttk.Label(frame, textvariable=self.notice).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def run(self):
        """Khởi động Application rồi chạy vòng lặp Tkinter trên main thread."""
        try:
            self.app.start()
            self._refresh_peers()
            self.root.after(50, self._drain)
            self.root.mainloop()
        finally:
            self.app.stop()

    def _worker(self, action):
        """Chạy tác vụ mạng ở thread riêng và đưa lỗi về Event Queue."""
        # Tác vụ socket chạy nền để GUI không bị đứng khi connect hoặc gửi dữ liệu.
        def run():
            try:
                action()
            except (OSError, ValueError, RuntimeError) as error:
                self.events.put(("notice", str(error)))
        threading.Thread(target=run, daemon=True).start()

    def _select(self, _=None):
        """Chọn peer, xem lịch sử; kết nối TCP ở worker khi cần."""
        selected = self.peers.selection()
        if not selected:
            return
        peer = self._peers.get(selected[0])
        if not peer:
            return
        self.title.configure(text=f"Chat with {peer.name}")
        self.app.chat.leave_chat()
        self._render(peer.peer_id)
        if self.peers.set(peer.peer_id, "status") == "offline":
            self.app.chat.select_peer(peer.peer_id)
            self._refresh_peers()
            self.notice.set(f"{peer.name} is offline")
            return
        if self.app.connections.get_connection(peer.peer_id):
            self.app.chat.select_peer(peer.peer_id)
            self._render(peer.peer_id)
            self._refresh_peers()
            return

        def connect():
            if not peer.peer_id:
                raise ValueError("This peer has no discovery ID")
            self.app.connections.connect(peer.ip, peer.tcp_port, expected_peer_id=peer.peer_id)
            self.events.put(("connected", peer.peer_id))
        self.notice.set(f"Connecting to {peer.name}…")
        self._worker(connect)

    def _send(self, _=None):
        """Gửi nội dung nhập tới đúng peer đang được chọn."""
        peer_id = self.app.chat.current_peer
        text = self.message.get().strip()
        if not peer_id or not text or self.peers.selection() != (peer_id,):
            return
        self.message.delete(0, "end")

        def send():
            self.app.chat.send_message(peer_id, text)
            self.events.put(("sent", peer_id))
        self._worker(send)

    def _file(self):
        """Mở hộp chọn file và yêu cầu backend gửi ở worker riêng."""
        if self.app.chat.current_peer is None:
            self.notice.set("Select a peer first")
            return
        path = filedialog.askopenfilename(parent=self.root)
        if path:
            self._worker(lambda: self.app.send_file(path))

    def _refresh_peers(self):
        """Cập nhật status và unread, giữ peer offline để xem lịch sử."""
        online = {peer.peer_id: peer for peer in self.app.registry.list_peers() if peer.peer_id}
        # Giữ peer offline trong phiên để người dùng vẫn xem được lịch sử chat.
        peers = {**self._peers, **online}
        for peer_id in self.peers.get_children():
            if peer_id not in peers:
                self.peers.delete(peer_id)
        self._peers = peers
        for peer_id, peer in peers.items():
            status = peer.status if peer_id in online else "offline"
            values = (status, self.app.chat.unread_count(peer_id) or "")
            if self.peers.exists(peer_id):
                self.peers.item(peer_id, text=peer.name, values=values)
            else:
                self.peers.insert("", "end", iid=peer_id, text=peer.name, values=values)

    def _render(self, peer_id):
        """Hiển thị lịch sử chat của peer đang chọn trong widget Text."""
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        for message in self.app.chat.get_history(peer_id):
            self.history.insert("end", f"{message.sender}: {message.text}\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def _drain(self):
        """Xử lý Event Queue trên main thread để cập nhật widget an toàn."""
        # Hàm này luôn chạy trên main thread thông qua root.after().
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "peers":
                self._refresh_peers()
            elif kind == "connected":
                if self.peers.selection() == (value,):
                    self.app.chat.select_peer(value)
                    self._render(value)
                    self._refresh_peers()
                self.notice.set("Connected")
            elif kind in ("chat", "sent"):
                peer_id = value.message.peer_id if kind == "chat" else value
                if self.app.chat.current_peer == peer_id:
                    self._render(peer_id)
                self._refresh_peers()
            elif kind == "notice":
                self.notice.set(value)
                match = re.search(r"(?:Sending|Receiving) .*?: (\d+)%", value)
                if match:
                    self.progress["value"] = int(match.group(1))
                elif "File transfer failed" in value or "File received" in value or "File transfer completed" in value:
                    self.progress["value"] = 0
        if not self._closing:
            self.root.after(50, self._drain)

    def close(self):
        """Dừng backend ở worker trước khi hủy cửa sổ Tkinter."""
        if self._closing:
            return
        self._closing = True
        self.notice.set("Closing…")

        # Dừng backend ở thread riêng, sau đó mới hủy cửa sổ trên main thread.
        def stop():
            try:
                self.app.stop()
            finally:
                self.events.put(("stopped", None))
        threading.Thread(target=stop, daemon=True).start()
        self._wait_for_stop()

    def _wait_for_stop(self):
        """Đợi event dừng hoàn tất rồi hủy cửa sổ trên main thread."""
        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "stopped":
                self.root.destroy()
                return
        self.root.after(50, self._wait_for_stop)
