from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from faceless_creator.config import Settings
from faceless_creator.service import FacelessCreatorService


class PrepareFromPackageTests(unittest.TestCase):
    def test_prepare_from_package_builds_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings = Settings.for_root(root / "fc-data")
            service = FacelessCreatorService(settings)
            if not service.media.available():
                self.skipTest("ffmpeg/ffprobe no disponible")

            pkg_dir = root / "packages" / "pp_int"
            pkg_dir.mkdir(parents=True)
            (pkg_dir / "media" / "audio").mkdir(parents=True)
            (pkg_dir / "media" / "images").mkdir(parents=True)
            package_path = pkg_dir / "package.yaml"
            package_path.write_text(
                json.dumps(
                    {
                        "package_id": "pp_int",
                        "channel_dna": {"locale": "es", "voice": {"voice_id": ""}},
                        "script": {
                            "title": "Episodio integración",
                            "status": "approved",
                            "full_text": "Uno. Dos.",
                            "beats": [
                                {
                                    "beat_id": "b01",
                                    "spoken_text": "Primera idea del episodio de prueba.",
                                    "visual_intent": "apertura",
                                    "concept_key": "open",
                                    "est_duration_sec": 2,
                                },
                                {
                                    "beat_id": "b02",
                                    "spoken_text": "Segunda idea del episodio de prueba.",
                                    "visual_intent": "cierre",
                                    "concept_key": "close",
                                    "est_duration_sec": 2,
                                },
                            ],
                        },
                        "meta": {"status": "script_approved"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            project = service.create_project("Desde package")
            job = service.prepare_from_package(project["id"], str(package_path))
            # Wait job
            deadline = time.time() + 60
            while time.time() < deadline:
                current = service.get_job(job["id"])
                if current["status"] in {"succeeded", "completed", "failed"}:
                    break
                time.sleep(0.2)
            current = service.get_job(job["id"])
            self.assertIn(current["status"], {"succeeded", "completed"}, current.get("error_message"))
            refreshed = service.get_project(project["id"])
            self.assertIsNotNone(refreshed.get("render_plan"))
            self.assertEqual(len(refreshed["render_plan"]["scenes"]), 2)
            self.assertEqual(len(refreshed["script"]["blocks"]), 2)
            # package timeline updated
            data = json.loads(package_path.read_text(encoding="utf-8"))
            self.assertEqual(data["timeline"]["status"], "planned")
            self.assertEqual(data["meta"]["status"], "fc_plan_ready")


if __name__ == "__main__":
    unittest.main()
