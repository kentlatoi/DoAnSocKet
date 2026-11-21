# Requirements matrix

**Final integration review — 2026-11-22.** The official assignment PDF was not present during this run, so the R01–R39 taxonomy below is treated as the repository's existing interpretation rather than a newly verified transcription. Local tests do not substitute for the physical LAN demo.

| Rubric area | Points | Current status | Evidence / remaining work |
| --- | ---: | --- | --- |
| UDP discovery, list, status | 15 | Implemented; unit/local socket tested | Existing discovery tests; two-computer broadcast pending |
| TCP chat, multiple peers | 20 | Implemented; local socket tested | Existing TCP tests and new app integration; physical LAN pending |
| File transfer | 15 | Implemented; real local TCP tested | 0 B–64 MiB, SHA-256, ACK/failures and chat during transfer passed |
| Responsive CLI or GUI | 15 | CLI implemented and local PTY verified; GUI partially manually verified | GUI startup/render/discovery passed; full GUI picker/cross-interface workflow pending |
| Protocol/framing | 10 | Implemented; unit tested | Protocol tests; physical capture pending |
| Error handling | 10 | Implemented; partly tested | Mismatch, invalid names, cleanup, connection tests; live failures pending |
| Report | 10 | Final QA report prepared | PDF regenerated from current evidence; team review pending |
| Demo/code quality | 5 | Script prepared | Two-computer demo and Wireshark pending |

| ID | Historical requirement baseline | Official PDF source | Type | Official-app status |
| --- | --- | --- | --- | --- |
| R01 | Mỗi peer chạy cùng một application; application vừa nhận vừa chủ động kết nối | p1 Overview | M | Implemented; local tests |
| R02 | Dùng native Socket API; ngôn ngữ đã chốt cho dự án là Python 3 | p1 General information | M | Implemented; local tests |
| R03 | UDP dùng cho peer discovery và presence/status | p1 §1, §3.1–3.2 | M | Implemented; local tests |
| R04 | Mỗi peer broadcast presence mỗi 3 giây | p1 §3.1 | M | Implemented; local tests |
| R05 | Presence dùng một UDP port fixed/common; `9999` chỉ là ví dụ | p1 §3.1 | M fixed port; example value illustrative | Implemented; local tests |
| R06 | Online registry/list chứa name, IP, TCP port và status | p1 §3.1 | M | Implemented; local tests |
| R07 | Xóa peer nếu không nghe presence trong 10 giây | p1 §3.1 | M | Implemented; local tests |
| R08 | Thông báo peer online/offline | p1 §3.1 | M | Implemented; local tests |
| R09 | Status `online`/`away` được broadcast và hiển thị | pp1–2 §3.2 | M | Implemented; local tests |
| R10 | Chọn peer online và mở TCP connection tới endpoint đã discover | p2 §3.3 | M | Implemented; local tests |
| R11 | Chat TCP full-duplex; mỗi bên gửi bất kỳ lúc nào | p2 §3.3 | M | Implemented; local tests |
| R12 | Incoming message hiển thị ngay khi người dùng đang nhập | pp2–3 §3.3, §4.3 | M | Implemented; local tests |
| R13 | Tin từ non-current peer được giữ trong per-peer history | p2 §3.3 | M | Implemented; local tests |
| R14 | Hiển thị notification và unread count cho non-current conversation | pp2–3 §3.3, example session | M | Implemented; local tests |
| R15 | Gửi file cho current partner | p2 §3.4 | M | Implemented; local tests |
| R16 | Hiển thị file-transfer progress theo phần trăm | p2 §3.4 | M | Implemented; local tests |
| R17 | File nhận được lưu trong `downloads/` | p2 §3.4 | M | Implemented; local tests |
| R18 | Chat vẫn hoạt động khi file transfer; transfer chạy bằng worker/thread riêng hoặc concurrency tương đương | p2 §3.4; p4 §5.1 | M | Implemented; local tests |
| R19 | Có `/list`, `/chat <name\|number>`, ordinary text, `/send <file>`, `/leave`, `/status <online\|away>`, `/help`, `/quit`, hoặc GUI capability parity | p2 §4.1; p1 interface choice | M capability | Implemented; local tests |
| R20 | Nếu dùng CLI, incoming output không làm mất text đang gõ; prompt/input được redraw | p3 §4.3 | M for CLI | Implemented; chat and file-progress PTY tested locally |
| R21 | Threaded CLI output được đồng bộ bằng lock | p3 §4.3 | M for threaded CLI | Implemented; local tests |
| R22 | Dùng multithreading hoặc concurrency phù hợp như `select/poll` | p1 objectives; p4 §5.1 | M | Implemented; local tests |
| R23 | Bảo vệ online list, histories và unread counters bằng synchronization | p4 §5.1 | M | Implemented; local tests |
| R24 | Nhóm tự thiết kế application-layer protocol | p4 §5.2 | M | Implemented; local tests |
| R25 | TCP protocol có correct message framing | p1 objectives; p4 §5.2 | M | Implemented; local tests |
| R26 | Receiver lặp đến đúng declared `length`/`size` bytes | p4 §5.2 | M | Implemented; local tests |
| R27 | Phát hiện peer close/crash, thông báo và trả UI/prompt về trạng thái dùng được | p4 §5.3 | M | Implemented; local tests |
| R28 | Connect tới stale/offline peer báo lỗi và không crash | p4 §5.3 | M | Implemented; local tests |
| R29 | Missing/interrupted file báo lỗi; partial received file bị xóa | p4 §5.3 | M | Implemented; local tests |
| R30 | Invalid command hiển thị trợ giúp ngắn | p4 §5.3 | M for CLI; equivalent validation for GUI | Implemented; local tests |
| R31 | Nộp source code và README với install/run/test instructions | p5 §7.1 | M | Implemented; README reviewed |
| R32 | Nộp report 5–10 pages | p5 §7.2 | M | Final QA PDF generated; team review pending |
| R33 | Wireshark evidence cho UDP broadcast và TCP three-way handshake, kèm giải thích | p5 §7.3 | M | PENDING: genuine Wireshark screenshots |
| R34 | Live demo 10 phút trên ít nhất hai computers | p5 §7.4 | M | PENDING: live two-computer demo |
| R35 | Shutdown giải phóng connections/threads hợp lý | p1 objectives; p4 error/lifecycle context; `/quit` p2 | M for stability/lifecycle | Implemented; local shutdown tested |
| R36 | Hỗ trợ multiple simultaneous peers/connections | pp1–2 objectives, §3.3; p5 rubric | M | Implemented; three-peer local TCP tested |
| R37 | Console hoặc GUI đều được chấp nhận | p1 General information; p5 rubric | A | CLI verified; GUI implemented on open PR #10 and partially manually verified |
| R38 | Team size 2–3 students | p1 General information | M administrative | Administrative: team roster to confirm |
| R39 | Có thể chạy trên ≥2 computers cùng LAN/Wi-Fi hoặc multiple local instances khi phát triển; final demo vẫn theo R34 | p1 Environment; p5 §7.4 | A environment; R34 final mandatory | Local instances tested; physical LAN pending |

R37 is an allowed interface choice; the project decision is CLI first. R39 allows local instances during development, while R34 still requires a final live demo on at least two computers. Administrative team details require confirmation before submission.

Statuses reflect the automated/local checks recorded in `test_evidence.md`. Physical LAN, Wireshark and the final demonstration remain pending.
