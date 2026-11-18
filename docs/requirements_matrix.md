# Requirements matrix

**Final integration review — 2026-11-18.** The R01–R39 taxonomy maps to the official five-page PDF. The legacy table below remains a historical baseline; current verified coverage is summarized here. Local tests do not substitute for the physical LAN demo.

| Rubric area | Points | Current status | Evidence / remaining work |
| --- | ---: | --- | --- |
| UDP discovery, list, status | 15 | Implemented; unit/local socket tested | Existing discovery tests; two-computer broadcast pending |
| TCP chat, multiple peers | 20 | Implemented; local socket tested | Existing TCP tests and new app integration; physical LAN pending |
| File transfer | 15 | Implemented; unit/local socket tested | `test_transfer`, `test_integration`; large live transfer pending |
| Console UI | 15 | Implemented; TV1 PTY tested | Integrated chat/file PTY redraw pending |
| Protocol/framing | 10 | Implemented; unit tested | Protocol tests; physical capture pending |
| Error handling | 10 | Implemented; partly tested | Mismatch, invalid names, cleanup, connection tests; live failures pending |
| Report | 10 | Draft prepared | PDF and team review pending |
| Demo/code quality | 5 | Script prepared | Two-computer demo and Wireshark pending |

| ID | Historical requirement baseline | Official PDF source | Type | Official-app status |
| --- | --- | --- | --- | --- |
| R01 | Mỗi peer chạy cùng một application; application vừa nhận vừa chủ động kết nối | p1 Overview | M | Unverified |
| R02 | Dùng native Socket API; ngôn ngữ đã chốt cho dự án là Python 3 | p1 General information | M | Unverified |
| R03 | UDP dùng cho peer discovery và presence/status | p1 §1, §3.1–3.2 | M | Unverified |
| R04 | Mỗi peer broadcast presence mỗi 3 giây | p1 §3.1 | M | Unverified |
| R05 | Presence dùng một UDP port fixed/common; `9999` chỉ là ví dụ | p1 §3.1 | M fixed port; example value illustrative | Unverified |
| R06 | Online registry/list chứa name, IP, TCP port và status | p1 §3.1 | M | Unverified |
| R07 | Xóa peer nếu không nghe presence trong 10 giây | p1 §3.1 | M | Unverified |
| R08 | Thông báo peer online/offline | p1 §3.1 | M | Unverified |
| R09 | Status `online`/`away` được broadcast và hiển thị | pp1–2 §3.2 | M | Unverified |
| R10 | Chọn peer online và mở TCP connection tới endpoint đã discover | p2 §3.3 | M | Unverified |
| R11 | Chat TCP full-duplex; mỗi bên gửi bất kỳ lúc nào | p2 §3.3 | M | Unverified |
| R12 | Incoming message hiển thị ngay khi người dùng đang nhập | pp2–3 §3.3, §4.3 | M | Unverified |
| R13 | Tin từ non-current peer được giữ trong per-peer history | p2 §3.3 | M | Unverified |
| R14 | Hiển thị notification và unread count cho non-current conversation | pp2–3 §3.3, example session | M | Unverified |
| R15 | Gửi file cho current partner | p2 §3.4 | M | Unverified |
| R16 | Hiển thị file-transfer progress theo phần trăm | p2 §3.4 | M | Unverified |
| R17 | File nhận được lưu trong `downloads/` | p2 §3.4 | M | Unverified |
| R18 | Chat vẫn hoạt động khi file transfer; transfer chạy bằng worker/thread riêng hoặc concurrency tương đương | p2 §3.4; p4 §5.1 | M | Unverified |
| R19 | Có `/list`, `/chat <name\|number>`, ordinary text, `/send <file>`, `/leave`, `/status <online\|away>`, `/help`, `/quit`, hoặc GUI capability parity | p2 §4.1; p1 interface choice | M capability | Unverified |
| R20 | Nếu dùng CLI, incoming output không làm mất text đang gõ; prompt/input được redraw | p3 §4.3 | M for CLI | Unverified |
| R21 | Threaded CLI output được đồng bộ bằng lock | p3 §4.3 | M for threaded CLI | Unverified |
| R22 | Dùng multithreading hoặc concurrency phù hợp như `select/poll` | p1 objectives; p4 §5.1 | M | Unverified |
| R23 | Bảo vệ online list, histories và unread counters bằng synchronization | p4 §5.1 | M | Unverified |
| R24 | Nhóm tự thiết kế application-layer protocol | p4 §5.2 | M | Unverified |
| R25 | TCP protocol có correct message framing | p1 objectives; p4 §5.2 | M | Unverified |
| R26 | Receiver lặp đến đúng declared `length`/`size` bytes | p4 §5.2 | M | Unverified |
| R27 | Phát hiện peer close/crash, thông báo và trả UI/prompt về trạng thái dùng được | p4 §5.3 | M | Unverified |
| R28 | Connect tới stale/offline peer báo lỗi và không crash | p4 §5.3 | M | Unverified |
| R29 | Missing/interrupted file báo lỗi; partial received file bị xóa | p4 §5.3 | M | Unverified |
| R30 | Invalid command hiển thị trợ giúp ngắn | p4 §5.3 | M for CLI; equivalent validation for GUI | Unverified |
| R31 | Nộp source code và README với install/run/test instructions | p5 §7.1 | M | Unverified |
| R32 | Nộp report 5–10 pages | p5 §7.2 | M | Unverified |
| R33 | Wireshark evidence cho UDP broadcast và TCP three-way handshake, kèm giải thích | p5 §7.3 | M | Unverified |
| R34 | Live demo 10 phút trên ít nhất hai computers | p5 §7.4 | M | Unverified |
| R35 | Shutdown giải phóng connections/threads hợp lý | p1 objectives; p4 error/lifecycle context; `/quit` p2 | M for stability/lifecycle | Unverified |
| R36 | Hỗ trợ multiple simultaneous peers/connections | pp1–2 objectives, §3.3; p5 rubric | M | Unverified |
| R37 | Console hoặc GUI đều được chấp nhận | p1 General information; p5 rubric | A | Unverified |
| R38 | Team size 2–3 students | p1 General information | M administrative | Unverified |
| R39 | Có thể chạy trên ≥2 computers cùng LAN/Wi-Fi hoặc multiple local instances khi phát triển; final demo vẫn theo R34 | p1 Environment; p5 §7.4 | A environment; R34 final mandatory | Unverified |

R37 is an allowed interface choice; the project decision is CLI first. R39 allows local instances during development, while R34 still requires a final live demo on at least two computers. Administrative and documentation requirements also remain unverified until supported by actual evidence.

Update statuses only after the official application has been implemented and the corresponding evidence is recorded in `test_evidence.md`. The separate educational prototype cannot satisfy official-app verification.
