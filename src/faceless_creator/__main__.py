from __future__ import annotations

import argparse
import os
import threading
import webbrowser
from pathlib import Path

from .config import Settings
from .server import create_server
from .service import FacelessCreatorService


def default_workspace() -> Path:
    configured = os.environ.get("FACELESSCREATOR_HOME")
    if configured:
        return Path(configured)
    return Path.cwd() / ".facelesscreator"


def main() -> None:
    parser = argparse.ArgumentParser(description="FacelessCreator local")
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    settings = Settings.for_root(arguments.workspace)
    service = FacelessCreatorService(settings)
    static_root = Path(__file__).parent / "web"
    server = create_server(service, static_root, arguments.host, arguments.port)
    url = f"http://{arguments.host}:{server.server_port}"
    print(f"FacelessCreator disponible en {url}")
    print(f"Workspace: {settings.root}")
    if not arguments.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Cerrando FacelessCreator…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

