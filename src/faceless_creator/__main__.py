from __future__ import annotations

import argparse
import ctypes
import os
import threading
import webbrowser
from pathlib import Path
from typing import Any

from .config import Settings
from .server import create_server
from .service import FacelessCreatorService


def default_workspace() -> Path:
    configured = os.environ.get("FACELESSCREATOR_HOME")
    if configured:
        return Path(configured)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "FacelessCreator" / "UserData"
    return Path.cwd() / ".facelesscreator"


def stop_when_parent_exits(parent_pid: int, server: Any) -> threading.Thread:
    def monitor() -> None:
        if os.name != "nt":
            return
        synchronize = 0x00100000
        infinite = 0xFFFFFFFF
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_bool, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel32.OpenProcess(synchronize, False, parent_pid)
        if not handle:
            return
        try:
            kernel32.WaitForSingleObject(handle, infinite)
        finally:
            kernel32.CloseHandle(handle)
        server.shutdown()

    thread = threading.Thread(target=monitor, daemon=True, name="parent-monitor")
    thread.start()
    return thread


def main() -> None:
    parser = argparse.ArgumentParser(description="FacelessCreator local")
    parser.add_argument("--workspace", type=Path, default=default_workspace())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--parent-pid", type=int)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    settings = Settings.for_root(arguments.workspace)
    service = FacelessCreatorService(settings)
    static_root = Path(__file__).parent / "web"
    server = create_server(service, static_root, arguments.host, arguments.port)
    url = f"http://{arguments.host}:{server.server_port}"
    print(f"FacelessCreator disponible en {url}")
    print(f"Workspace: {settings.root}")
    if arguments.parent_pid:
        stop_when_parent_exits(arguments.parent_pid, server)
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

