"""Run one LAN chat peer."""

import argparse

from .app import Application


def main() -> None:
    parser = argparse.ArgumentParser(description="LAN Chat & File Sharing")
    parser.add_argument("--name", default="Peer", help="display name")
    parser.add_argument("--port", type=int, default=0, help="TCP listening port (0 chooses one)")
    parser.add_argument("--udp-port", type=int, default=9999, help="shared UDP discovery port")
    parser.add_argument("--gui", action="store_true", help="open the Tkinter interface")
    args = parser.parse_args()
    try:
        app = Application(args.name, args.port, args.udp_port)
        if args.gui:
            from .gui import GUI
            GUI(app).run()
        else:
            app.run()
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot start LAN Chat: {error}\n")


if __name__ == "__main__":
    main()
