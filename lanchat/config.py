"""Các giá trị mặc định dùng chung cho UDP presence và cơ chế Timeout."""

# Mọi peer dùng cùng cổng UDP để nghe presence; có thể đổi bằng --udp-port.
UDP_PORT = 9999
# Khoảng cách giữa hai lần gửi presence khi không có thay đổi trạng thái.
HEARTBEAT_SECONDS = 3
# Quá thời gian này không thấy presence thì xóa peer khỏi registry.
PEER_TIMEOUT_SECONDS = 10
