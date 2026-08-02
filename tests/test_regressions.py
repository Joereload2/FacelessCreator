from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

from faceless_creator.config import Settings
from faceless_creator.database import utc_now
from faceless_creator.jobs import JobRunner
from faceless_creator.server import create_server
from faceless_creator.service import FacelessCreatorService

from .helpers import wait_for_job


class RegressionTests(unittest.TestCase):
    def test_failed_job_can_retry_with_same_idempotency_key(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            service = FacelessCreatorService(Settings(Path(folder), width=160, height=90, fps=10))
            project = service.create_project("Retry")
            runner = JobRunner(service.database)
            failed = runner.start(project["id"], "probe", "same-key", lambda _: (_ for _ in ()).throw(RuntimeError("first")))
            self.assertEqual(wait_for_job(service, failed["id"])["status"], "failed")
            retried = runner.start(project["id"], "probe", "same-key", lambda progress: {"ok": True})
            result = wait_for_job(service, retried["id"])
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["attempt"], 2)

    def test_scene_asset_route_serves_image_and_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            service = FacelessCreatorService(Settings(Path(folder), width=160, height=90, fps=10))
            project = service.create_project("Assets")
            prepared = wait_for_job(service, service.prepare_demo(project["id"])["id"])
            self.assertEqual(prepared["status"], "succeeded", prepared.get("error_message"))
            project = service.get_project(project["id"])
            relative = project["render_plan"]["scenes"][0]["image_path"]
            static_root = Path(__file__).parents[1] / "src" / "faceless_creator" / "web"
            server = create_server(service, static_root, "127.0.0.1", 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                url = f"http://127.0.0.1:{server.server_port}/api/projects/{project['id']}/assets/{relative}"
                with urlopen(url, timeout=5) as response:
                    self.assertEqual(response.headers.get_content_type(), "image/png")
                    self.assertGreater(len(response.read()), 50)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(2)


if __name__ == "__main__":
    unittest.main()

