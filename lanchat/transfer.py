"""File transfers over framed TCP connections."""

import hashlib
import os
import tempfile
import threading
import uuid
from pathlib import Path

from .protocol import MessageType, ProtocolError, decode_json, encode_json

CHUNK_SIZE = 64 * 1024


class TransferManager:
    """Allow one outgoing and one incoming file per peer."""

    def __init__(self, connections, downloads="downloads", notify=None):
        self.connections = connections
        self.downloads = Path(downloads)
        self.notify = notify or (lambda message: None)
        self._lock = threading.RLock()
        self._incoming = {}
        self._outgoing = {}
        self._workers = set()
        self._stop = threading.Event()
        connections.add_message_handler(self.handle_frame)
        connections.add_disconnect_handler(self._disconnected)

    def send_file(self, peer_id, path):
        source = Path(path)
        if not source.is_file():
            raise ValueError(f"File not found or not a regular file: {path}")
        with source.open("rb"):
            pass
        with self._lock:
            if self._stop.is_set():
                raise RuntimeError("Application is stopping")
            if peer_id in self._outgoing:
                raise ValueError("A file is already being sent to this peer")
            transfer_id = uuid.uuid4().hex
            done = threading.Event()
            self._outgoing[peer_id] = [transfer_id, done, None]
            worker = threading.Thread(target=self._send, args=(peer_id, source, transfer_id, done), daemon=True)
            self._workers.add(worker)
            worker.start()

    def _send(self, peer_id, source, transfer_id, done):
        try:
            size = source.stat().st_size
            digest = hashlib.sha256()
            with source.open("rb") as stream:
                self.connections.send(peer_id, MessageType.FILE_META, encode_json({"transfer_id": transfer_id, "name": source.name, "size": size}))
                sent, last_bucket = 0, -1
                if size == 0:
                    self.notify(f"Sending {source.name}: 100% (awaiting verification)")
                while not self._stop.is_set():
                    chunk = stream.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    self.connections.send(peer_id, MessageType.FILE_CHUNK, chunk)
                    digest.update(chunk)
                    sent += len(chunk)
                    bucket = (sent * 100 // size) // 10
                    if bucket != last_bucket:
                        self.notify(f"Sending {source.name}: {sent * 100 // size}% (awaiting verification)")
                        last_bucket = bucket
            if self._stop.is_set():
                raise RuntimeError("Transfer stopped")
            self.connections.send(peer_id, MessageType.FILE_END, encode_json({"transfer_id": transfer_id, "sha256": digest.hexdigest()}))
            if not done.wait(30):
                raise TimeoutError("Receiver did not confirm the file")
            with self._lock:
                result = self._outgoing[peer_id][2]
            if result != "ok":
                raise RuntimeError(result or "Peer disconnected")
            self.notify(f"File transfer completed and verified: {source.name}")
        except (OSError, ValueError, RuntimeError, TimeoutError) as error:
            self.notify(f"File transfer failed: {error}")
        finally:
            with self._lock:
                self._outgoing.pop(peer_id, None)
                self._workers.discard(threading.current_thread())

    def handle_frame(self, peer_id, frame):
        kind = frame.message_type
        if kind not in (MessageType.FILE_META, MessageType.FILE_CHUNK, MessageType.FILE_END, MessageType.ERROR):
            return
        if kind is MessageType.FILE_META:
            data = decode_json(frame.payload)
            name, size, transfer_id = data.get("name"), data.get("size"), data.get("transfer_id")
            if (not isinstance(name, str) or not name or name in (".", "..") or
                    Path(name).name != name or "\\" in name or "/" in name or
                    any(ord(c) < 32 for c in name) or
                    not isinstance(size, int) or isinstance(size, bool) or size < 0 or
                    not isinstance(transfer_id, str) or not transfer_id):
                raise ProtocolError("Invalid FILE_META")
            with self._lock:
                if peer_id in self._incoming:
                    raise ProtocolError("File transfer already active")
                try:
                    self.downloads.mkdir(parents=True, exist_ok=True)
                    stream = tempfile.NamedTemporaryFile(dir=self.downloads, suffix=".part", delete=False)
                except OSError as error:
                    raise ProtocolError(f"Cannot save incoming file: {error}") from error
                self._incoming[peer_id] = [transfer_id, name, size, 0, hashlib.sha256(), stream]
            self.notify(f"Receiving {name}: 0%")
        elif kind is MessageType.FILE_CHUNK:
            with self._lock:
                state = self._incoming.get(peer_id)
                if state is None:
                    raise ProtocolError("FILE_CHUNK without FILE_META")
                if state[3] + len(frame.payload) > state[2]:
                    self._abort(peer_id)
                    raise ProtocolError("File exceeds declared size")
                try:
                    state[5].write(frame.payload)
                except OSError as error:
                    self._abort(peer_id)
                    raise ProtocolError(f"Cannot write incoming file: {error}") from error
                state[4].update(frame.payload)
                previous_percent = state[3] * 100 // state[2] if state[2] else 100
                state[3] += len(frame.payload)
                percent = state[3] * 100 // state[2] if state[2] else 100
            if percent == 100 or percent // 10 != previous_percent // 10:
                self.notify(f"Receiving {state[1]}: {percent}%")
        else:
            data = decode_json(frame.payload)
            transfer_id = data.get("transfer_id")
            if kind is MessageType.ERROR or data.get("status") == "ok":
                with self._lock:
                    outgoing = self._outgoing.get(peer_id)
                    if outgoing and outgoing[0] == transfer_id:
                        outgoing[2] = "ok" if kind is MessageType.FILE_END else str(data.get("error", "Receiver rejected file"))
                        outgoing[1].set()
                return
            with self._lock:
                state = self._incoming.get(peer_id)
                if state is None or state[0] != transfer_id:
                    raise ProtocolError("FILE_END without matching FILE_META")
                if not isinstance(data.get("sha256"), str) or state[3] != state[2] or state[4].hexdigest() != data["sha256"]:
                    self._abort(peer_id)
                    self.connections.send(peer_id, MessageType.ERROR, encode_json({"transfer_id": transfer_id, "error": "size or checksum mismatch"}))
                    return
                stream = state[5]
                try:
                    stream.close()
                    destination = self.downloads / state[1]
                    number = 1
                    while True:
                        try:
                            os.link(stream.name, destination)
                            break
                        except FileExistsError:
                            destination = self.downloads / f"{Path(state[1]).stem} ({number}){Path(state[1]).suffix}"
                            number += 1
                    os.unlink(stream.name)
                except OSError as error:
                    self._abort(peer_id)
                    raise ProtocolError(f"Cannot finalize incoming file: {error}") from error
                del self._incoming[peer_id]
            if state[2] == 0:
                self.notify(f"Receiving {state[1]}: 100%")
            self.connections.send(peer_id, MessageType.FILE_END, encode_json({"transfer_id": transfer_id, "status": "ok"}))
            self.notify(f"File received and verified: {destination}")

    def _abort(self, peer_id):
        state = self._incoming.pop(peer_id, None)
        if state:
            state[5].close()
            Path(state[5].name).unlink(missing_ok=True)

    def _disconnected(self, peer_id, error):
        with self._lock:
            self._abort(peer_id)
            outgoing = self._outgoing.get(peer_id)
            if outgoing:
                outgoing[2] = "Peer disconnected"
                outgoing[1].set()

    def stop(self):
        self._stop.set()
        with self._lock:
            for outgoing in self._outgoing.values():
                outgoing[2] = "Application stopped"
                outgoing[1].set()
            for peer_id in list(self._incoming):
                self._abort(peer_id)
            workers = list(self._workers)
        for worker in workers:
            worker.join(timeout=1)
