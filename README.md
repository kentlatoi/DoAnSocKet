# LAN Chat & File Sharing

Đồ án Mạng máy tính HCMUS sử dụng Python 3 và native Socket API. Mỗi máy vừa là TCP server vừa là TCP client; UDP dùng để tìm peer, TCP dùng để chat và truyền file.

## Trạng thái hiện tại

Phần của **TV2 (`@thanhhuong107`)** đã được triển khai trên nhánh `feat/tcp-chat` và đang chờ review tại [PR #4](https://github.com/kentlatoi/DoAnSocKet/pull/4).

Nếu đang xem nhánh `main`, bạn chưa thấy code TV2 vì PR chưa được merge. Chuyển sang đúng nhánh bằng:

```sh
git fetch origin
git switch feat/tcp-chat
```

## Code TV2 nằm ở đâu?

| File | Nội dung |
| --- | --- |
| `lanchat/protocol.py` | Header TCP, message framing, đọc đúng số byte, UTF-8 JSON và kiểm tra frame lỗi |
| `lanchat/connections.py` | `bind/listen/accept/connect`, nhiều peer, HELLO handshake, ngắt kết nối và kết nối trùng |
| `lanchat/chat.py` | Gửi/nhận chat, history theo peer, current chat và unread count có lock |
| `tests/test_protocol.py` | Test frame bị chia nhỏ, nhiều frame cùng lúc, UTF-8 và frame lỗi |
| `tests/test_connections.py` | Test full-duplex, multi-peer, connect đồng thời, refused và disconnect |
| `tests/test_chat.py` | Test history, unread và thread safety |
| `examples/milestone_01/tcp_echo_server.py` | TCP Echo Server của Milestone 1 |

Các file `.md` trong `docs/` là tài liệu bắt buộc của đồ án, không thay thế source code:

- `docs/protocol_spec.md`: định dạng protocol để TV1/TV3 tích hợp.
- `docs/architecture.md`: mô hình connection và shared state.
- `docs/test_evidence.md`: kết quả test đã chạy.

## Luồng TCP Chat

1. Peer A lấy IP và TCP port của Peer B từ module discovery của TV1.
2. A gọi `ConnectionManager.connect(ip, port)`.
3. Hai bên trao đổi frame `HELLO` chứa `peer_id` và tên.
4. `ChatManager.send_message()` đóng gói nội dung thành frame `CHAT`.
5. Worker nhận frame lưu history; nếu không phải current chat thì tăng unread count.
6. Khi socket đóng hoặc lỗi, connection bị xóa và callback disconnect được gọi.

Frame TCP có header cố định 10 byte:

```text
4 byte magic "LCHT" | 1 byte version | 1 byte type | 4 byte payload length
```

Chi tiết nằm trong `docs/protocol_spec.md`.

## Chạy test

Yêu cầu Python 3.10 trở lên, không có thư viện runtime bên ngoài.

```sh
python3 -m unittest discover -s tests -v
```

Kết quả hiện tại: **16 test pass** trên loopback.

Kiểm tra format/lint nếu máy đã có Ruff và Black:

```sh
ruff check lanchat tests examples/milestone_01
black --check lanchat tests examples/milestone_01
```

## Chạy TCP Echo Server

```sh
python3 examples/milestone_01/tcp_echo_server.py --host 0.0.0.0 --port 9000
```

Server nhận byte từ TCP client và gửi lại đúng dữ liệu đó. Nhấn `Ctrl+C` để dừng.

## Phân công nhóm

| Thành viên | Phần phụ trách |
| --- | --- |
| TV1 — `@kentlatoi` | UDP Discovery, Peer Registry, CLI |
| TV2 — `@thanhhuong107` | TCP Connection, Chat, Application Protocol |
| TV3 — `@phkhoiit-1508` | File Transfer, Error Handling, tích hợp ứng dụng |

## Chưa có trên nhánh TV2

Để tránh làm quá phạm vi, nhánh này **không** triển khai UDP discovery, CLI, file transfer hoặc `app.py`. Những phần đó do TV1/TV3 thực hiện và sẽ được tích hợp sau.

Hai việc vẫn cần kiểm tra thủ công trước khi nộp:

- Chạy trên hai máy cùng LAN.
- Chụp TCP three-way handshake bằng Wireshark.
