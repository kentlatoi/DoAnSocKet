"""Receive UDP datagrams; run this before udp_sender.py."""

import socket

PORT = 9999


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp.bind(("", PORT))
        print(f"Listening on UDP {PORT}; Ctrl+C to stop")
        try:
            while True:
                data, address = udp.recvfrom(1024)
                print(f"{address}: {data.decode('utf-8', errors='replace')}")
        except KeyboardInterrupt:
            print("\nStopped")


if __name__ == "__main__":
    main()
