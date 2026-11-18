"""Small independent TCP echo client example."""

import argparse
import socket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=19090)
    args = parser.parse_args()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            connection.settimeout(5)
            connection.connect((args.host, args.port))
            connection.sendall(args.message.encode("utf-8"))
            print(connection.recv(4096).decode("utf-8"))
    except OSError as error:
        parser.exit(1, f"TCP echo failed: {error}\n")


if __name__ == "__main__":
    main()
