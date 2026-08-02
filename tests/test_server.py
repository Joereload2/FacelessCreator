from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from faceless_creator.config import Settings
from faceless_creator.server import create_server
from faceless_creator.service import FacelessCreatorService

from .helpers import wait_for_job


class ApiSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        settings = Settings(Path(self.temporary.name), width=160, height=90, fps=10)
        self.service = FacelessCreatorService(settings)
        static_root = Path(__file__).parents[1] / "src" / "faceless_creator" / "web"
        self.server = create_server(self.service, static_root, "127.0.0.1", 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.temporary.cleanup()

    def request(self, path: str, method: str = "GET", body: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(body).encode() if body is not None else None
        request = Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            response = urlopen(request, timeout=10)
        except HTTPError as error:
            response = error
        return response.status, json.loads(response.read())

    def test_health_static_and_project_api(self) -> None:
        status, health = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(health["status"], "ok")
        with urlopen(self.base + "/", timeout=5) as response:
            self.assertIn(b"FacelessCreator", response.read())

        status, project = self.request("/api/projects", "POST", {"name": "API E2E"})
        self.assertEqual(status, 201)
        status, job = self.request(f"/api/projects/{project['id']}/prepare-demo", "POST", {})
        self.assertEqual(status, 202)
        finished = wait_for_job(self.service, job["id"])
        self.assertEqual(finished["status"], "succeeded", finished.get("error_message"))
        status, fetched = self.request(f"/api/projects/{project['id']}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["plan_version"], 1)

    def test_structured_error(self) -> None:
        status, value = self.request("/api/projects", "POST", {"name": ""})
        self.assertEqual(status, 400)
        self.assertEqual(value["error"]["code"], "INVALID_REQUEST")


if __name__ == "__main__":
    unittest.main()

