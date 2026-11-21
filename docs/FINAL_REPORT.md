# Báo cáo QA cuối: KENT SOCKET - LAN Chat & File Sharing

**Môn:** Mạng máy tính, HCMUS
**Ngày kiểm thử:** 22/11/2026
**Môi trường:** macOS arm64, Python 3.12.16 Homebrew, Tk 9.1, IPv4 loopback và broadcast cục bộ
**Ứng viên kiểm thử:** `feat/simple-gui` tại `9c87725`, sau sửa QA tại `386af9f` trên `fix/final-system-qa`

## A. Executive summary

Ứng dụng đạt **GO có điều kiện cho demo localhost**. UDP discovery, TCP chat nhiều peer, CLI, framing và truyền file thật qua TCP đều hoạt động trên máy kiểm thử. Sau khi sửa một lỗi ngập thông báo tiến độ phía nhận, toàn bộ **40/40 automated tests PASS, 0 fail, 0 skip** trong 27,882 giây. Harness hệ thống độc lập xác nhận 24 kịch bản file/network; lần xác nhận sau sửa kiểm tra lại file 64 MiB và shutdown giữa transfer có backpressure. Không tính các lỗi `PermissionError`/DNS của sandbox hạn chế vào kết quả sản phẩm.

Nhánh GUI `feat/simple-gui` là ứng viên đầy đủ nhất và PR #10 vẫn OPEN; `origin/main` tại `9048689` chưa chứa GUI. GUI thật đã mở bằng Homebrew Python, render đúng, discover peer khác và giữ responsive ở trạng thái quan sát. Các thao tác GUI đầy đủ gồm chọn peer, file picker và bốn tổ hợp CLI/GUI chưa được hoàn tất bằng automation đáng tin cậy, nên không được ghi PASS.

Trạng thái phát hành là **NO-GO cho tuyên bố “đã sẵn sàng nộp hoàn toàn”** cho đến khi hoàn tất hai máy vật lý, Windows nếu giảng viên yêu cầu, Wireshark UDP broadcast/TCP three-way handshake, và diễn tập demo 10 phút. File đề chính thức `LAN_Chat_Socket_Project.docx.pdf` không có trong repository; rubric được đánh giá theo matrix hiện có, không coi là đối chiếu nguyên văn đề.

## B. Functionality test matrix

| Test ID | Feature | Test scenario | Expected | Actual | Status |
| --- | --- | --- | --- | --- | --- |
| ENV-01 | Clean install | Venv tạm, `pip install -r requirements.txt` | Cài đúng dependency | `prompt-toolkit 3.0.52`, không có dependency ẩn | PASS |
| ENV-02 | Python/Tk | pyenv và Homebrew 3.12 | Phân biệt Tk theo interpreter | pyenv 3.12.8 thiếu `_tkinter`; Homebrew 3.12.16 có Tk 9.1 | PASS |
| BUILD-01 | Compile | `compileall -q lanchat examples tests` | Không lỗi syntax/import | Exit 0 | PASS |
| AUTO-01 | Full suite | unittest với quyền socket | Không fail/skip | 40 PASS, 0 fail, 0 skip, 27,882 s | PASS |
| UDP-01 | Discovery | 3 CLI thật Quan/Minh/Lan, TCP 5001/5002/5003 | Mỗi peer thấy hai peer còn lại | Đúng tên, IP, port, không tự thấy mình | PASS |
| UDP-02 | Presence/status | Heartbeat khoảng 3 s, `/status away` | Registry cập nhật | Timing 2,5-3,5 s trong test; PTY thấy Minh `away` | PASS |
| UDP-03 | Timeout | Dừng peer, chờ khoảng 10 s | Offline và bị xóa | Test socket thực PASS | PASS |
| UDP-04 | Malformed | Datagram rỗng/sai port/status/UTF-8/quá dài | Bỏ qua, không crash | PASS | PASS |
| TCP-01 | Chat | Quan↔Minh, nhiều tin, Unicode | Nội dung nguyên vẹn | `Xin chào Minh 👋` và phản hồi nhận đúng | PASS |
| TCP-02 | Multi-peer | Quan kết nối Minh và Lan; unread/switch | Lịch sử tách biệt, reset unread | Test 3 peer và PTY PASS | PASS |
| TCP-03 | `/leave` | Rời Lan rồi quay lại Minh | Không đóng connection Minh | Tin gửi tiếp tới Minh thành công | PASS |
| TCP-04 | Framing | Fragmented, combined frames, exact receive | Không trộn/cắt frame | Socketpair tests PASS | PASS |
| TCP-05 | Identity/dedup | Sai expected peer ID; simultaneous connect | Từ chối sai ID; còn một session | PASS | PASS |
| CLI-01 | Commands | `/list`, `/chat`, text, `/send`, `/leave`, status, help, quit | Đúng callback/kết quả | Unit và 3 PTY thật PASS | PASS |
| CLI-02 | Invalid input | Thiếu arg, peer sai, command lạ, tên trùng | Thông báo rõ, không crash | PASS | PASS |
| CLI-03 | Prompt redraw | Gõ `par`, nhận notification, gõ tiếp `tial` | Peer nhận `partial` | Quan nhận đúng `Lan: partial` | PASS |
| CLI-04 | Ctrl+C/port conflict | Ctrl+C; mở hai peer cùng TCP 5001 | Exit sạch; lỗi dễ hiểu | Ctrl+C exit 0; `Address already in use` exit 1 | PASS |
| GUI-01 | Actual startup | Homebrew Python, `--gui` | Cửa sổ mở và responsive | Cửa sổ Quan render đúng, Ready, controls đầy đủ | PASS |
| GUI-02 | Discovery/render | Mở Quan và Minh | Peer list tự cập nhật | Quan thấy Minh online và notification | PASS |
| GUI-03 | Thread safety | Network events qua queue/`after()` | Worker không sửa widget trực tiếp | Code review và 5 GUI tests trong suite PASS | PASS |
| GUI-04 | Full interaction | Chọn peer, chat, picker, progress, close button | Thao tác thật hoàn chỉnh | Automation chọn Treeview không ổn định; không suy diễn | NOT RUN |
| STAB-01 | Shutdown | Nhiều start/stop, `/quit`, active transfer | Socket/thread/file dở được dọn | `/quit` exit 0; controlled active-transfer cleanup PASS | PASS |
| STAB-02 | Unexpected input | Bad frame/meta/size/hash/disconnect | Không crash toàn app; reconnect được | PASS trên loopback | PASS |

Không xuất hiện thông báo “Invalid command” do incoming chat. Tin incoming chỉ đi qua callback chat/notify, không đi vào parser CLI.

## C. Dedicated File Transfer report

Tất cả ca thành công dưới đây dùng `Application`/`ConnectionManager` thật qua TCP loopback. File được tạo trong thư mục tạm, receiver lưu vào downloads tạm, rồi so kích thước và SHA-256 byte-for-byte.

| File | Original size | Received size | SHA-256 match | Chat during transfer | Result |
| --- | ---: | ---: | --- | --- | --- |
| `empty.bin` | 0 | 0 | Có | Không áp dụng | PASS |
| `small.txt` | 17 | 17 | Có | Không | PASS |
| `under-chunk.bin` | 65.535 | 65.535 | Có | Không | PASS |
| `exact-64KiB.bin` | 65.536 | 65.536 | Có | Không | PASS |
| `over-64KiB.bin` | 65.537 | 65.537 | Có | Không | PASS |
| `one-MiB.bin` | 1.048.576 | 1.048.576 | Có | Không | PASS |
| `medium-9MiB.bin` | 9.437.184 | 9.437.184 | Có | Không | PASS |
| `large-64MiB.bin` | 67.108.864 | 67.108.864 | Có | 30 tin mỗi chiều đến trước completion | PASS |
| `tệp tiếng Việt.bin` | 12.345 | 12.345 | Có | Không | PASS |
| `file with spaces.bin` | 23.456 | 23.456 | Có | Không | PASS |
| CLI `tệp có khoảng trắng.txt` | 51 | 51 | Có; `ead7e...878254` hai phía | Tin sau `/send` tới receiver | PASS |

Receiver gửi ACK chỉ sau khi đóng, link tên cuối và xác minh size/hash. Sender chỉ báo `completed and verified` sau ACK đúng transfer ID. File 64 MiB sau fix phát đúng các mốc 0%, 10%, ..., 100%, không lặp. Không có `.part` sau completion.

| Failure/concurrency case | Actual evidence | Status |
| --- | --- | --- |
| Gửi lại cùng tên | Tạo `small (1).txt`, giữ file cũ | PASS |
| Hai chiều A→B và B→A đồng thời | Hai file 9 MiB đúng hash | PASS |
| A gửi đồng thời tới B và C | Hai file 1 MiB đúng hash | PASS |
| Transfer thứ hai tới cùng peer | Từ chối rõ `already being sent` | PASS |
| File thiếu / path là directory | Từ chối trước worker | PASS |
| Unsafe filename `../escape` | Không thoát downloads; connection lỗi được phục hồi | PASS |
| Declared size sai / chunk vượt size | Xóa `.part`, không tạo file cuối | PASS |
| SHA-256 sai | Gửi ERROR, xóa `.part`, connection còn dùng được | PASS |
| Malformed metadata | Không crash app; reconnect được | PASS |
| Destination không ghi được | Giữ file hiện hữu, báo failure, không crash | PASS |
| Sender/receiver disconnect | Sender không báo success; receiver xóa `.part` | PASS |
| Wrong ACK + timeout 30 s | Bỏ qua transfer ID sai; báo `did not confirm`; không success giả | PASS |
| Shutdown khi transfer đang active | Backpressure sau FILE_META; đóng connection và xóa `.part` | PASS |
| CLI→CLI | File Unicode/có khoảng trắng, hash trùng | PASS |
| GUI→GUI, CLI→GUI, GUI→CLI bằng thao tác màn hình | Chưa thực hiện đầy đủ | NOT RUN |

## D. Detected defects

### DEF-01 - Duplicate receive progress notifications

- **Severity:** Medium.
- **File/function:** `lanchat/transfer.py`, `TransferManager.handle_frame` nhánh FILE_CHUNK.
- **Root cause:** điều kiện `percent % 10 == 0` phát notification cho mọi chunk trong cùng một phần trăm chia hết cho 10. File 128 MiB tạo hàng chục dòng 0%, 10%, ... giống nhau, làm ngập CLI và queue GUI.
- **Reproduction:** truyền file 128 MiB qua TCP thật; quan sát nhiều dòng `Receiving ...: 0%` và mỗi decile lặp lại.
- **Fix:** so decile trước và sau chunk, chỉ notify khi bước sang decile mới hoặc đạt 100%.
- **Regression:** `test_receive_progress_is_not_repeated_within_a_decile` gửi năm chunk 1 byte trong decile 0 và yêu cầu chỉ có một notification FILE_META 0%.
- **Final result:** regression PASS; suite 40/40 PASS; file 64 MiB sau fix có đúng 11 mốc duy nhất và hash khớp.
- **Commit:** `386af9fd15e12ea925400fe21504e96b514c1094`.

Không xác nhận defect chức năng nào khác trong phạm vi tự động/local. Ctrl+C gửi trực tiếp vào tiến trình GUI làm Python in `KeyboardInterrupt`, nhưng đây không phải luồng đóng cửa sổ được kiểm thử và không được sửa ngoài phạm vi; close button vẫn cần kiểm tra màn hình thủ công.

## E. Rubric coverage

| Criterion | Points | Classification | Evidence / gap |
| --- | ---: | --- | --- |
| UDP discovery, online list, status | 15 | IMPLEMENTED & VERIFIED (local) | 3 PTY thật; heartbeat/status/timeout/malformed tests; physical broadcast pending |
| TCP chat, multiple peers | 20 | IMPLEMENTED & VERIFIED (local) | Full-duplex, 3 peer, unread, identity, dedup, Unicode |
| File transfer with progress | 15 | IMPLEMENTED & VERIFIED (local) | 0 B đến 64 MiB, SHA-256, ACK, failures, concurrent chat |
| Responsive CLI or GUI | 15 | IMPLEMENTED & VERIFIED qua CLI | PTY giữ input; GUI render/thread architecture verified nhưng full GUI interaction NOT RUN |
| Protocol design and framing | 10 | IMPLEMENTED & VERIFIED | Header 10 byte, exact receive, fragmented/combined frames, invalid frame rejection |
| Error handling and stability | 10 | IMPLEMENTED & VERIFIED (local) | Port conflict, disconnect, cleanup, bad metadata/hash/size, shutdown |
| Report | 10 | IMPLEMENTED BUT TEAM REVIEW PENDING | Báo cáo QA và checklist có sẵn; đề PDF chính thức không có để đối chiếu nguyên văn |
| Demo and code quality | 5 | PARTIALLY IMPLEMENTED | Code nhỏ, test/fix rõ; demo hai máy và Wireshark chưa chạy |

Không suy ra hoặc bảo đảm điểm số. Các tiêu chí “verified” ở đây chỉ áp dụng cho localhost/máy kiểm thử, không thay thế demo vật lý.

## F. Git delivery

- **Remote:** `https://github.com/kentlatoi/DoAnSocKet.git`.
- **`origin/main`:** `9048689` sau PR #9.
- **GUI dependency:** PR #10 `feat/simple-gui` → `main` đang OPEN.
- **Base submission candidate:** `9c87725` trên `feat/simple-gui` (đã chứa merge `origin/main` và GUI).
- **QA branch:** `fix/final-system-qa`.
- **Code/test changed:** `lanchat/transfer.py`, `tests/test_transfer.py`.
- **Fix commit:** `386af9fd15e12ea925400fe21504e96b514c1094`.
- **Documentation changed:** báo cáo/evidence/matrix; commit và PR được ghi trong phần bàn giao cuối của phiên QA.
- **Merge:** không tự động merge vào `main`.

## G. Remaining manual tests

1. **Hai máy vật lý:** checkout nhánh/PR cuối trên hai máy cùng Wi-Fi/LAN; dùng Quan 5001 và Minh 5002; xác nhận IP không phải loopback, discovery hai chiều, chat, file 64 MiB, hash và interruption. Điền `TWO_COMPUTER_ACCEPTANCE.md`.
2. **GUI trên màn hình thật:** với Homebrew Python 3.12/Tk, chạy hai GUI; click peer, Enter/Send, unread, away, file picker/cancel, tên có khoảng trắng, progress, chat trong transfer, failure và nút đóng cửa sổ. Lặp CLI→GUI và GUI→CLI.
3. **Windows:** tạo venv, cài requirements, kiểm tra Tk, Windows Defender Firewall inbound UDP 9999/TCP, run/test và đường dẫn có dấu/có khoảng trắng.
4. **Wireshark UDP:** capture đúng Wi-Fi/Ethernet; lọc `udp.port == 9999`; ảnh phải hiện destination broadcast và payload `HELLO|...`, không dùng loopback làm chứng cứ LAN.
5. **Wireshark TCP:** bắt kết nối mới; lọc cổng 5001/5002; chụp SYN, SYN-ACK, ACK cùng stream trước HELLO/chat/file.
6. **Demo 10 phút:** diễn tập đúng `FINAL_DEMO_SCRIPT.md`, chia người nói, chuẩn bị file/hash và phương án firewall; giữ ảnh/log thật.
7. **Official assignment PDF:** thêm file đề hoặc đối chiếu thủ công mục 3–8 trước khi ký duyệt requirement matrix.

## H. Final verdict

- **Code implemented:** Có, gồm CLI và GUI; GUI phụ thuộc PR #10 chưa merge.
- **Automatically tested:** Có, 40/40 PASS sau fix.
- **Locally integrated:** Có, 3 CLI thật; UDP/TCP/file/chunk/ACK/chat concurrent và failure cases qua socket thật.
- **GUI locally observed:** Có ở mức startup/render/discovery/input; full GUI workflow chưa verified.
- **Tested on real physical LAN:** Không.
- **Ready for localhost demo:** **GO** trên Homebrew Python 3.12/Tk hoặc CLI interpreter có dependency.
- **Ready for final submission:** **NO-GO có điều kiện** cho đến khi PR GUI/QA được review, hai máy vật lý và Wireshark/demo được hoàn tất.

Không có database, web server, authentication hoặc feature ngoài đề được thêm. Fix duy nhất là giảm notification progress lặp; protocol, chunk size, ACK và kiến trúc hiện hữu được giữ nguyên.
