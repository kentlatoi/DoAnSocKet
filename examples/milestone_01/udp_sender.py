"""Send one broadcast UDP datagram to udp_receiver.py."""

import socket
import sys

PORT = 9999


def main():
    address = sys.argv[1] if len(sys.argv) > 1 else "255.255.255.255"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.sendto(b"Hello from UDP sender", (address, PORT))
    print(f"Sent one datagram to {address}:{PORT}")


if __name__ == "__main__":
    main()
