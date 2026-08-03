from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from faceless_creator.config import Settings
from faceless_creator.server import create_server
from faceless_creator.service import FacelessCreatorService

from .test_audio_import import silent_wav


class AudioApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.service = FacelessCreatorService(Settings(Path(self.temporary.name), width=160, height=90, fps=10))
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

    def test_binary_audio_upload_returns_updated_project(self) -> None:
        project = self.service.create_project("API audio")
        payload = silent_wav(1)
        request = Request(
            f"{self.base}/api/projects/{project['id']}/audio",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/octet-stream",
                "X-Filename": quote("narración.wav"),
            },
        )

        with urlopen(request, timeout=10) as response:
            value = json.loads(response.read())

        self.assertEqual(response.status, 201)
        self.assertEqual(value["audio"]["original_name"], "narración.wav")


if __name__ == "__main__":
    unittest.main()
