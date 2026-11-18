# Báo cáo đồ án: LAN Chat & File Sharing

**Môn:** Mạng máy tính, HCMUS

**Nhóm:** 3 thành viên (TV1, TV2, TV3)

**Ngày bản thảo:** 18/11/2026
**Trạng thái:** Bản báo cáo dựa trên mã và kiểm thử localhost; ảnh Wireshark và demo hai máy cần bổ sung trước khi nộp.

## 1. Mục tiêu và phạm vi

Đồ án xây dựng ứng dụng trò chuyện và truyền file trong mạng cục bộ bằng Python 3 và Socket API gốc. Mọi người chạy cùng một chương trình. Mỗi tiến trình vừa công bố bản thân, vừa nghe kết nối đến, vừa có thể chủ động kết nối với peer khác. UDP đảm nhiệm khám phá và trạng thái; TCP đảm nhiệm tin nhắn và file. Giao diện dòng lệnh cho phép người dùng gõ tiếp trong khi thông báo từ mạng xuất hiện. Ứng dụng không dùng máy chủ trung tâm, cơ sở dữ liệu hay giao diện đồ họa.

Yêu cầu chính của đề gồm hiện danh sách người dùng, trạng thái online/away, chat hai chiều với nhiều peer, unread cho hội thoại khác, file có progress và lưu vào `downloads/`, không làm mất nội dung đang gõ, xử lý mất kết nối và dọn file nhận dở. Hai máy tính cùng LAN và ảnh Wireshark là phần xác minh cuối cùng, chưa được coi là đã hoàn thành bằng thử nghiệm localhost.

## 2. Kiến trúc P2P và luồng khởi động

Ứng dụng được chạy bằng `python3 -m lanchat --name Quan --port 5001`. `__main__.py` đọc tên, cổng TCP và cổng UDP chung, rồi gọi `Application.run`. `Application` tạo một `peer_id` ổn định trong phiên. Nó khởi động `ConnectionManager` trước để biết cổng TCP đã bind thực tế, tạo `Discovery` với cùng ID và cổng đó, nối ChatManager, TransferManager và CLI, sau đó chạy vòng nhập lệnh. Nếu yêu cầu TCP port là 0, cổng được hệ điều hành cấp sẽ được quảng bá; không quảng bá cổng 0.

`PeerRegistry` giữ danh sách theo cặp IP và TCP port; `Discovery` nhận datagram và cập nhật hoặc hết hạn peer. Khi người dùng chọn `/chat`, CLI tìm peer theo tên duy nhất hoặc số thứ tự rồi `Application.select_peer` dùng IP, TCP port và peer ID đã discover. TCP HELLO phải trả về cùng ID. Điều này ngăn lựa chọn một peer nhưng kết nối thực tế tới peer khác tại endpoint đó. Presence cũ không chứa ID vẫn có thể xem trong danh sách, song không thể mở verified chat. ID là mã định danh phiên, không phải cơ chế xác thực mật mã trước đối thủ giả mạo.

Các module và trách nhiệm:

| Module | Vai trò |
| --- | --- |
| `discovery.py`, `peer_registry.py` | UDP presence, timeout, danh sách có khóa |
| `connections.py` | TCP listener, HELLO, socket cho từng peer, send lock |
| `protocol.py` | Header 10 byte, loại message, đọc đúng số byte |
| `chat.py` | Gửi/nhận CHAT, history, current peer, unread |
| `transfer.py` | File metadata/chunk/END, checksum, ACK, lưu và dọn `.part` |
| `cli.py` | Lệnh và prompt có redraw |
| `app.py`, `__main__.py` | Kết nối module, callback, startup/shutdown |

## 3. UDP discovery và trạng thái

Một presence datagram UTF-8 có dạng `HELLO|name|tcp_port|status|peer_id`. Mặc định peer gửi broadcast trên UDP port 9999 mỗi ba giây và nghe cùng cổng. `status` là `online` hoặc `away`; `/status away` thay đổi trạng thái và đánh thức broadcaster gửi sớm. Registry cập nhật thời điểm nghe cuối cùng. Sau mười giây không nghe presence, worker expiry xóa peer và phát thông báo offline. Khóa bảo vệ dictionary; `/list` lấy bản sao đã sắp xếp để không đọc trạng thái đang sửa. Chạy nhiều instance trên một máy cần khả năng dùng chung UDP port của hệ điều hành; hai máy vật lý vẫn cần firewall cho phép gói broadcast.

## 4. TCP, chat và application protocol

TCP là byte stream, nên không thể giả định một `recv` trả đúng một tin. Mỗi frame có magic `LCHT` (4 byte), version (1), type (1), payload length big-endian (4), rồi đúng số byte payload. `recv_exact` lặp đến khi đủ header và payload; đóng socket giữa frame là lỗi. Payload tối đa 8 MiB. CHAT và metadata dùng JSON UTF-8, file chunk giữ nguyên bytes nhị phân. Các loại gồm HELLO, CHAT, FILE_META, FILE_CHUNK, FILE_END, LEAVE và ERROR; LEAVE hiện được dự trữ trong protocol, còn `/leave` là thao tác chọn hội thoại tại máy cục bộ.

`ConnectionManager` mở một listener TCP, nhận HELLO và tạo receiver worker cho mỗi peer. Nó duy trì nhiều socket trong map theo peer ID và giải quyết kết nối đồng thời bằng quy tắc ID. `ChatManager` giữ history và unread theo ID có khóa. Tin của current peer được hiển thị; tin từ peer khác tăng unread và thông báo, sau khi chuyển `/chat` thì các tin chưa đọc được in ra và counter được xóa. `/leave` chỉ bỏ current peer, không hủy các kết nối không liên quan.

## 5. File transfer và tính toàn vẹn

`TransferManager.send_file` xác minh file thường và có thể đọc, sau đó chạy worker riêng. Worker gửi FILE_META gồm transfer ID, basename và size, đọc file theo chunk 64 KiB, gửi từng FILE_CHUNK và cập nhật SHA-256, rồi gửi FILE_END với digest. Chunk tránh nạp cả file vào RAM và cho phép chat xen giữa các frame. `PeerConnection.send` giữ một lock quanh toàn bộ `sendall` của từng frame, nên bytes của CHAT và FILE_CHUNK không xen lẫn trong cùng frame. Hai chiều truyền độc lập; mỗi peer có tối đa một file đang gửi và một file đang nhận.

Receiver từ chối tên rỗng, tên `.`/`..`, dấu phân cách đường dẫn và ký tự điều khiển. Nó tạo `downloads/` và file `.part` tại đó, ghi chunk tăng dần, đếm bytes và tính SHA-256. Chunk vượt size bị từ chối. FILE_END chỉ được chấp nhận khi size và hash bằng metadata/nội dung thực. Sau kiểm tra, file được đóng và liên kết sang tên cuối; nếu tên đã tồn tại, thêm hậu tố `(1)`, `(2)`... mà không ghi đè. Receiver gửi FILE_END ACK với `status=ok` sau khi lưu thành công. Sender chỉ nói “completed and verified” khi nhận ACK đúng transfer ID; thiếu ACK sau 30 giây, ERROR hoặc mất TCP đều báo lỗi. Disconnect và mismatch xóa `.part`. File rỗng gửi metadata và digest SHA-256 của chuỗi rỗng, progress được hiển thị 100%.

## 6. Console, thread và đồng bộ

CLI dùng `PromptSession` và `patch_stdout` của `prompt_toolkit`. `notify` khóa output để các thread không in chồng nhau; `patch_stdout` vẽ lại prompt và phần người dùng đã gõ. Callback của CLI chỉ chuyển lệnh đến Application; networking không nằm trong CLI. `/list` lấy registry, `/chat` kết nối/chọn peer, text gửi qua ChatManager, `/send` qua TransferManager, `/status` qua Discovery, `/quit` gọi shutdown.

Các thread gồm main đọc phím, UDP broadcaster/listener/expiry, TCP acceptor, receiver theo peer và sender theo file. Registry, history/unread, map connection và transfer state có khóa riêng. Không giữ khóa toàn cục trong suốt một lần gửi file. Khi thoát, Application dừng UDP, báo transfer workers ngừng và đánh thức ACK wait, rồi đóng TCP socket; các module dùng bounded join. File nhận dở được đóng và xóa.

## 7. Lỗi và giới hạn

TCP HELLO sai ID bị từ chối trước khi chọn chat. Connect tới peer đã tắt được báo bằng thông báo thay vì làm sập CLI. Invalid command in trợ giúp ngắn. File nguồn thiếu, không phải file thường hoặc không đọc được sẽ báo lỗi trước worker. Trong khi truyền, mất TCP, size/hash sai và ghi file thất bại không được báo thành công. File nhận từ peer không tin cậy được giới hạn tên và kích thước thực nhận; protocol vẫn cho phép khai báo size lớn, nên máy nhận cần còn dung lượng đĩa. Một ứng dụng LAN trong đồ án không mã hóa hoặc xác thực danh tính bằng khóa; sử dụng trong mạng tin cậy theo phạm vi bài tập.

Lỗi đã gặp khi tích hợp: cần dùng cùng peer ID cho UDP và TCP; cổng TCP 0 phải đổi thành cổng thực; TCP chat và file cần dùng chung khóa gửi từng frame; sender không thể coi 100% bytes sent là đã lưu thành công. Các giải pháp tương ứng là Application chia sẻ ID và lấy cổng sau `start`, worker gửi chunk qua ConnectionManager, và receiver ACK sau kiểm tra hash/lưu file.

## 8. Kiểm thử và kết luận

Ngày 18/11/2026 trên macOS, `python3 -m unittest discover -s tests -p 'test_*.py' -q` với quyền bind socket trả `Ran 32 tests ... OK`. Suite bao gồm protocol, UDP, TCP, CLI, chat, unit transfer và integration localhost. Bài integration dùng socket TCP thực cho hai Application, kiểm tra chung ID/cổng, từ chối HELLO sai ID, chat hai chiều, file Unicode >64 KiB, bytes nhận và chat lúc truyền. Unit transfer kiểm tra file rỗng, binary, collision, traversal, checksum sai và xóa partial. Một lần chạy trong sandbox không có quyền bind đã thất bại với `PermissionError`; đó là giới hạn môi trường test, không được tính là PASS.

Chưa thử live trên hai máy, Windows, capture Wireshark và redraw của chat/file trong PTY tích hợp. Nhóm cần chạy kịch bản `FINAL_DEMO_SCRIPT.md` trên hai máy, so hash nguồn/đích, thử tắt một peer khi nhận file và chụp gói UDP broadcast cùng TCP SYN/SYN-ACK/ACK thật. Kết quả này phải được điền vào ledger trước khi báo cáo là đã xác minh vật lý. Kiến trúc hiện đạt chức năng cốt lõi bằng các module nhỏ, có thể giải thích từng bước trong buổi bảo vệ.
