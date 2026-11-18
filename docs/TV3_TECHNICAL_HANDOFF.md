# TV3: ghi chú bảo vệ kỹ thuật

`lanchat/__main__.py:main` phân tích tham số và gọi `Application.run`. `lanchat/app.py:Application.start` tạo TCP listener, lấy cổng thực, tạo Discovery cùng `peer_id`, nối callback CLI với ChatManager và TransferManager, rồi bật UDP. `Application.stop` dừng discovery, transfer và TCP. `lanchat/transfer.py:TransferManager.send_file` kiểm tra file và khởi chạy worker; `_send` gửi metadata, chunk 64 KiB và SHA-256; `handle_frame` nhận, kiểm tra và xác nhận. `ConnectionManager.send` khóa từng frame; vì vậy CHAT có thể xen giữa FILE_CHUNK mà không hỏng khung. `recv_frame` đọc header 10 byte và đúng số byte payload. Progress = bytes đã gửi/nhận × 100 / kích thước; file rỗng xử lý riêng. File đến nằm trong `.part` ở `downloads/`; chỉ sau kiểm tra size/hash mới tạo tên cuối, thêm số khi trùng. Disconnect xóa phần chưa hoàn tất. ACK `FILE_END` có `status=ok` chỉ gửi sau khi lưu thành công.

| # | Câu hỏi | Trả lời nói ngắn | Giải thích và hàm liên quan | Câu hỏi tiếp có thể gặp |
| --- | --- | --- | --- | --- |
| 1 | TV3 làm gì? | Ghép app và truyền file. | `Application.start`, `TransferManager`. | TV1/TV2 nối vào đâu? |
| 2 | Vì sao cần chunk? | Không nạp toàn bộ file, không vượt frame. | `_send`, `CHUNK_SIZE=64 KiB`. | Giới hạn frame là bao nhiêu? |
| 3 | TCP có ranh giới message không? | Không; dùng header 10 byte. | `protocol.recv_frame`. | Nếu recv thiếu byte? |
| 4 | Tại sao SHA-256? | Kiểm tra nội dung đầu cuối. | `_send`, `handle_frame`. | Size đúng nhưng nội dung sai? |
| 5 | Khi nào báo hoàn tất? | Sau ACK từ receiver. | `_send` chờ Event. | ACK thất lạc? |
| 6 | ACK dùng type nào? | `FILE_END` với `status=ok`. | `handle_frame`. | Phân biệt END gửi và ACK? |
| 7 | File rỗng ra sao? | Gửi META, END hash rỗng. | `_send`, `handle_frame`. | Progress 100% ở đâu? |
| 8 | File trùng tên? | Thêm hậu tố số. | `handle_frame` dùng `os.link`. | Có ghi đè file cũ không? |
| 9 | Chặn path traversal thế nào? | Từ chối separator và tên đặc biệt. | `handle_frame` kiểm tra `name`. | `../x` bị gì? |
| 10 | Mất TCP giữa chừng? | Xóa `.part`, báo lỗi. | `_disconnected`, `_abort`. | Sender nhận tín hiệu gì? |
| 11 | Chat trong lúc gửi? | Worker gửi từng frame. | `_send`, `ConnectionManager.send`. | Frame xen nhau có hỏng không? |
| 12 | Nhiều peer? | TCP giữ map theo peer ID. | `ConnectionManager`, `Application.select_peer`. | Hai tên giống nhau? |
| 13 | Chọn nhầm peer? | So ID UDP với TCP HELLO. | `Application.select_peer`. | Presence cũ thiếu ID? |
| 14 | Cổng TCP 0? | Lấy cổng bind thực rồi broadcast. | `Application.start`. | `getsockname` ở đâu? |
| 15 | /leave làm gì? | Bỏ current chat, giữ TCP. | `Application.leave`. | History còn không? |
| 16 | Unread hoạt động? | ChatManager đếm theo ID. | `ChatManager.handle_frame`. | Khi chuyển chat? |
| 17 | UI không mất chữ gõ? | `patch_stdout` redraw prompt. | `CLI.run`, `CLI.notify`. | Output lock để làm gì? |
| 18 | Shutdown theo thứ tự? | Dừng UDP, transfer, rồi TCP. | `Application.stop`. | Worker đang đợi ACK? |
| 19 | File thiếu quyền đọc? | Mở thử trước khi chạy worker. | `send_file`. | File biến mất sau đó? |
| 20 | Hash sai? | Xóa `.part`, gửi ERROR. | `handle_frame`, `_abort`. | Sender báo gì? |
| 21 | Một peer gửi hai file đồng thời? | Từ chối lượt thứ hai. | `send_file`, `_outgoing`. | Vì sao policy này? |
| 22 | Thử nghiệm nào còn thiếu? | Hai máy, Windows, Wireshark. | `docs/test_evidence.md`. | Vì sao localhost chưa đủ? |
