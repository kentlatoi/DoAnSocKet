"""Small TCP echo server for the Milestone 1 socket demonstration."""

from __future__ import annotations

import argparse
import socket

BUFFER_SIZE = 4096


def serve(host: str, port: int, *, once: bool = False) -> None:
    """Echo bytes until interrupted; ``once`` exits after one client."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"TCP echo server listening on {host}:{server.getsockname()[1]}")
        while True:
            client, address = server.accept()
            print(f"Connected: {address[0]}:{address[1]}")
            with client:
                while data := client.recv(BUFFER_SIZE):
                    client.sendall(data)
            print(f"Disconnected: {address[0]}:{address[1]}")
            if once:
                return


def main() -> None:
    parser = argparse.ArgumentParser(description="TCP echo server exercise")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument(
        "--once", action="store_true", help="exit after the first client disconnects"
    )
    args = parser.parse_args()
    try:
        serve(args.host, args.port, once=args.once)
    except KeyboardInterrupt:
        print("\nEcho server stopped")


if __name__ == "__main__":
    main()
