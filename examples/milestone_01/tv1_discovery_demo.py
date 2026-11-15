"""Run TV1 discovery and CLI before TCP/file integration is available."""

import argparse

from lanchat.cli import CLI
from lanchat.discovery import Discovery
from lanchat.peer_registry import PeerRegistry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--tcp-port", type=int, required=True)
    args = parser.parse_args()
    registry = PeerRegistry()
    discovery = Discovery(args.name, args.tcp_port, registry)
    cli = CLI(registry, discovery, on_quit=discovery.stop)
    registry.on_event = lambda event, peer: cli.notify(f"{peer.name} {event}")
    discovery.start()
    try:
        cli.run()
    finally:
        discovery.stop()


if __name__ == "__main__":
    main()
