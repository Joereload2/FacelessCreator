from __future__ import annotations

import subprocess
import sys
import threading
import unittest

from faceless_creator.__main__ import stop_when_parent_exits


class FakeServer:
    def __init__(self) -> None:
        self.stopped = threading.Event()

    def shutdown(self) -> None:
        self.stopped.set()


@unittest.skipUnless(sys.platform == "win32", "Windows parent handles are required")
class ParentMonitorTests(unittest.TestCase):
    def test_stops_server_when_parent_process_exits(self) -> None:
        parent = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(0.2)"])
        server = FakeServer()
        monitor = stop_when_parent_exits(parent.pid, server)
        parent.wait(timeout=5)
        self.assertTrue(server.stopped.wait(5), "server was not stopped after parent exit")
        monitor.join(1)


if __name__ == "__main__":
    unittest.main()
