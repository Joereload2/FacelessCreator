from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from faceless_creator.config import Settings
from faceless_creator.domain import DomainError
from faceless_creator.service import FacelessCreatorService

from .helpers import wait_for_job


class FullWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.settings = Settings(Path(self.temporary.name), width=320, height=180, fps=12)
        self.service = FacelessCreatorService(self.settings)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_demo_preview_replace_and_export(self) -> None:
        project = self.service.create_project("Prueba integral")
        prepare = wait_for_job(self.service, self.service.prepare_demo(project["id"])["id"])
        self.assertEqual(prepare["status"], "succeeded", prepare.get("error_message"))

        project = self.service.get_project(project["id"])
        self.assertEqual(project["plan_version"], 1)
        self.assertEqual(len(project["render_plan"]["scenes"]), 3)
        self.assertEqual(project["render_plan"]["duration"], 9)

        preview = wait_for_job(self.service, self.service.start_render(project["id"], "preview")["id"])
        self.assertEqual(preview["status"], "succeeded", preview.get("error_message"))
        preview_path = self.service.artifact_path(preview["output"]["artifacts"][0]["id"])[0]
        self.assertTrue(preview_path.is_file())
        probe = self.service.media.probe(preview_path)
        video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        self.assertEqual((video["width"], video["height"]), (320, 180))

        scene = project["render_plan"]["scenes"][0]
        alternative = self.service.alternatives(project["id"], scene["id"])[0]
        revised = self.service.replace_visual(project["id"], scene["id"], alternative["relative_path"])
        self.assertEqual(revised["plan_version"], 2)
        self.assertEqual(revised["render_plan"]["scenes"][0]["image_path"], alternative["relative_path"])

        exported = wait_for_job(self.service, self.service.start_render(project["id"], "export")["id"])
        self.assertEqual(exported["status"], "succeeded", exported.get("error_message"))
        kinds = {artifact["kind"] for artifact in exported["output"]["artifacts"]}
        self.assertEqual(kinds, {"export", "subtitle", "manifest"})
        manifest = next(item for item in exported["output"]["artifacts"] if item["kind"] == "manifest")
        manifest_path = self.service.artifact_path(manifest["id"])[0]
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(value["render_plan"]["version"], 2)
        self.assertEqual(self.service.get_project(project["id"])["status"], "completed")

    def test_render_requires_plan(self) -> None:
        project = self.service.create_project("Vacío")
        with self.assertRaisesRegex(DomainError, "RenderPlan"):
            self.service.start_render(project["id"], "preview")


if __name__ == "__main__":
    unittest.main()

