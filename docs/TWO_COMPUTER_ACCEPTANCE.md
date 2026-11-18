# Phiếu nghiệm thu demo hai máy — chưa thực hiện

Điền **PASS/FAIL**, thời gian, máy và đường dẫn ảnh/log thật vào từng dòng. Giữ bản gốc của ảnh Wireshark và file nhận để đối chiếu. Thực hiện ít nhất trên hai máy vật lý; peer thứ ba có thể là máy thứ ba hoặc một tiến trình khác nếu hệ điều hành cho phép chia sẻ UDP port.

## Chuẩn bị

| Mục | Thao tác | Kết quả mong đợi | Kết quả / bằng chứng | PASS/FAIL |
| --- | --- | --- | --- | --- |
| M1 | Ghi phiên bản Python (`python3 --version` hoặc `python --version`) và OS trên hai máy | Python ≥3.10; ghi macOS/macOS hoặc macOS/Windows | ____ | ____ |
| M2 | Kết nối cùng LAN/Wi-Fi, ghi IPv4 bằng `ipconfig getifaddr en0` trên macOS (chọn đúng interface) hoặc `ipconfig` trên Windows; ping IP máy kia | Hai máy thấy nhau, không dùng guest/client-isolated Wi-Fi | ____ | ____ |
| M3 | Cài từ README: tạo venv và `pip install -e .`; mở firewall cho Python inbound UDP 9999 và TCP 5001/5002 | Cài xong; firewall cho phép | ____ | ____ |
| M4 | Chọn thư mục chạy có quyền ghi và đủ dung lượng; chuẩn bị file nhỏ, file Unicode, file vài MB | File nguồn đọc được; `downloads/` tạo được | ____ | ____ |

## Ứng dụng

| Mục | Thao tác | Kết quả mong đợi | Kết quả / bằng chứng | PASS/FAIL |
| --- | --- | --- | --- | --- |
| A1 | Máy A: `python3 -m lanchat --name Quan --port 5001`; B: `python3 -m lanchat --name Minh --port 5002` (Windows dùng `python`) | Mỗi máy hiện `Ready as ... on TCP port ...` | ____ | ____ |
| A2 | Chờ tối đa 5 giây, `/list` ở cả hai máy | Thấy tên, IP, TCP port và `online`; thông báo `Peer online` | ____ | ____ |
| A3 | B `/status away`; A `/list`; sau đó B `/status online` | Trạng thái đổi trên A sau datagram mới | ____ | ____ |
| A4 | A `/chat Minh`; A/B gửi ít nhất hai dòng Unicode qua lại | `Chatting with ...`; mỗi bên thấy tin ngay | ____ | ____ |
| A5 | Thêm peer Lan; A đang chat Minh, Lan `/chat Quan` rồi gửi hai tin | A thấy unread tăng lên 1 rồi 2; `/chat Lan` hiện đúng hai tin theo thứ tự | ____ | ____ |
| A6 | A gõ dở `/li`; khi B nhắn, A gõ tiếp `st` rồi Enter | Tin hiện trên prompt mà `/list` vẫn chạy, phần `/li` không mất | ____ | ____ |
| A7 | A `/chat Minh`; `/send <đường-dẫn-file>`; trong lúc progress chạy, A/B chat | Progress có 100%; chat đến trước khi hoàn tất; bên nhận hiện `File received and verified` | ____ | ____ |
| A8 | So SHA-256 file gốc và file trong `downloads/` bằng `shasum -a 256 <file>` (macOS) hoặc `Get-FileHash <file> -Algorithm SHA256` (PowerShell) | Hai hash giống nhau; file cũ không bị ghi đè khi gửi lại | ____ | ____ |
| A9 | Thử file rỗng và tên Unicode; thử `/send` file không tồn tại và `/unknown` | File rỗng/Unicode lưu đúng; lỗi có thông báo, app vẫn dùng được | ____ | ____ |
| A10 | Trong lúc nhận file lớn, tắt tiến trình gửi đột ngột; kiểm tra `downloads/` | Bên nhận báo disconnect, không còn `.part`, không có file hoàn chỉnh giả | ____ | ____ |
| A11 | Tắt peer Lan, chờ khoảng 10 giây rồi `/list`; A `/leave`, `/chat Minh`; cuối cùng `/quit` cả hai | Lan biến mất và có thông báo offline; các peer khác còn hoạt động; thoát không treo | ____ | ____ |

Nếu dùng hai tiến trình trên một máy để tạo peer thứ ba, kiểm tra trước `SO_REUSEPORT` của OS. Không lấy kết quả này thay cho A1–A2 trên hai máy. Trên Windows, cần xác minh Windows Defender Firewall cho cả inbound UDP/TCP; khả năng chia sẻ một UDP port giữa nhiều tiến trình chưa được kiểm chứng.

## Wireshark — chứng cứ bắt buộc

1. Trên máy A, chọn đúng Wi-Fi/Ethernet interface có IPv4 ở M2; **bắt gói trước khi khởi chạy app**. Có thể dùng capture filter `udp port 9999 or tcp port 5001 or tcp port 5002`; dùng display filter `udp.port == 9999` để tìm presence.
2. Chọn datagram có destination là địa chỉ broadcast của mạng (hoặc `255.255.255.255`), UDP destination port 9999 và payload `HELLO|Quan|5001|online|...`. Ảnh phải hiện thời gian, Source IP, Destination IP, UDP ports và bytes/payload. Nếu không thấy, kiểm tra interface, firewall và client isolation; không chụp gói localhost làm bằng chứng LAN.
3. Trước A4, bắt kết nối TCP mới. Dùng display filter `tcp.port == 5002 && (tcp.flags.syn == 1 || tcp.flags.ack == 1)` rồi theo một TCP stream. Chụp ba gói liên tiếp: A→B **SYN** (`SYN=1, ACK=0`), B→A **SYN, ACK** (`SYN=1, ACK=1`), A→B **ACK** (`SYN=0, ACK=1`). Ảnh cần hiện thời gian, IP nguồn/đích, cổng nguồn/đích, flags, cùng stream/sequence liên quan.
4. Chú thích trong báo cáo: UDP dùng khám phá không kết nối; TCP ba bước tạo kết nối trước HELLO/chat/file. Nếu cổng TCP khác 5002, thay bằng cổng `Ready as` thực tế. Ghi đường dẫn ảnh gốc, máy, interface và thời gian capture.

| Chứng cứ | Đường dẫn / thời gian / máy | PASS/FAIL |
| --- | --- | --- |
| UDP broadcast presence trên LAN | ____ | ____ |
| TCP SYN, SYN-ACK, ACK cùng stream | ____ | ____ |
| Hash gốc/đích và màn hình file nhận | ____ | ____ |
| Video/ghi chép demo 10 phút | ____ | ____ |
