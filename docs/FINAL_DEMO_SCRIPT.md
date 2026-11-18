# Kịch bản demo 10 phút (chưa thực hiện trên hai máy)

| Thời gian | Người nói | Thao tác và nội dung |
| --- | --- | --- |
| 0:00–1:00 | TV1 | Giới thiệu P2P: mỗi máy vừa phát UDP presence vừa nghe TCP. Kiểm tra hai máy cùng LAN. |
| 1:00–2:00 | TV1 | Chạy `python3 -m lanchat --name Quan --port 5001` và `--name Minh --port 5002` trên hai máy; `/list`, chỉ ra IP, cổng và status. |
| 2:00–2:45 | TV1 | Minh dùng `/status away`; Quan dùng `/list`. Gõ dở một lệnh trong khi thông báo đến để chứng minh prompt được giữ. |
| 2:45–4:00 | TV2 | Quan `/chat Minh`; trao đổi hai chiều. Giải thích TCP HELLO, khung 10 byte, `recv_exact` và kiểm tra ID. |
| 4:00–5:00 | TV2 | Chạy peer thứ ba Lan; Lan nhắn Quan khi Quan đang chat Minh. Quan thấy unread, chuyển `/chat Lan` để đọc. `/leave` giữ các connection khác. |
| 5:00–7:00 | TV3 | Quan `/chat Minh`, `/send <đường-dẫn-file>`; tiếp tục chat trong khi progress tăng. Minh chỉ ra file trong `downloads/`; so sánh SHA-256 hai máy. |
| 7:00–8:00 | TV3 | Thử `/send` với file không tồn tại; trình bày xử lý lỗi, file `.part`, ACK sau khi xác minh. |
| 8:00–9:00 | TV1/TV2 | Wireshark: chỉ ra UDP presence trên cổng 9999; chỉ ra TCP SYN, SYN-ACK, ACK tới cổng chat. Dùng ảnh chụp thật trong buổi thực hành. |
| 9:00–10:00 | TV3 | `/quit` từng máy; tóm tắt thread model, giới hạn và kết luận. |

## Chuẩn bị và chứng cứ Wireshark

Chọn giao diện Wi-Fi/Ethernet đang dùng; bắt gói trước khi khởi chạy ứng dụng. Lọc `udp.port == 9999` (hoặc cổng UDP chung đã chọn), tìm datagram broadcast có payload `HELLO|...`. Bắt lại khi `/chat`; lọc `tcp.port == 5001 || tcp.port == 5002` theo cổng thực tế. Chụp ba gói SYN, SYN-ACK, ACK cùng một TCP stream. Giải thích UDP chỉ công bố trạng thái; TCP thiết lập kết nối đáng tin cậy và truyền frame. Chụp màn hình thật kèm giao diện, thời điểm, IP và cổng; không dùng ảnh giả. Nếu dùng cổng TCP 0, đọc cổng in lúc startup rồi thay trong bộ lọc. Kiểm tra firewall và quyền capture trước buổi demo.
