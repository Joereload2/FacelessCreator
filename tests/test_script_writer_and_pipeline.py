from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from faceless_creator.config import Settings
from faceless_creator.package_state import batch_gate_allows_render
from faceless_creator.script_writer import TemplateScriptWriter
from faceless_creator.service import FacelessCreatorService
from faceless_creator.tts import StubTtsAdapter, render_package_tts


class ScriptAndPipelineTests(unittest.TestCase):
    def test_template_writer_and_tts_and_thumbs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg_dir = root / "ep"
            for sub in ("media/audio", "media/images", "media/thumbs", "script"):
                (pkg_dir / sub).mkdir(parents=True)
            package_path = pkg_dir / "package.yaml"
            package = {
                "package_id": "pp_writer",
                "channel_dna": {"locale": "es", "niche_id": "x", "voice": {"voice_id": ""}},
                "brief": {
                    "title": "El error que arruina tu plan",
                    "hook": "El error que nadie te cuenta",
                    "hook_type": "dolor",
                    "structure": [
                        {"role": "hook", "intent": "open"},
                        {"role": "problem", "intent": "p"},
                        {"role": "method", "intent": "m"},
                        {"role": "cta", "intent": "c"},
                    ],
                    "audience": "emprendedores",
                    "cta": "Comenta",
                    "packaging": {
                        "thumbnail_texts": [
                            {"variant_id": "th1", "text": "EL ERROR", "hypothesis": "dolor"},
                            {"variant_id": "th2", "text": "3 CLAVES", "hypothesis": "lista"},
                            {"variant_id": "th3", "text": "NADIE VE", "hypothesis": "curiosidad"},
                        ]
                    },
                },
                "script": {"status": "pending", "title": "El error", "full_text": "", "beats": []},
                "meta": {"status": "brief_ready", "stage": "brief"},
                "packaging": {"titles": [], "thumbnails": []},
            }
            package_path.write_text(json.dumps(package, ensure_ascii=False), encoding="utf-8")

            settings = Settings.for_root(root / "fc")
            service = FacelessCreatorService(settings)
            written = service.write_package_script(str(package_path), prefer_llm=False)
            self.assertEqual(written["writer_kind"], "template")
            self.assertGreaterEqual(len(written["script"]["beats"]), 3)

            loaded = service.get_studio_package(str(package_path))
            self.assertTrue(loaded["brief"]["hook"])
            self.assertEqual(loaded["script"]["status"], "draft")

            draft = service.save_package_script_draft(
                str(package_path),
                {"title": "Titulo editado", "full_text": "Parrafo uno del guion.\n\nParrafo dos con mas detalle para el beat."},
            )
            self.assertEqual(draft["script"]["status"], "draft")
            self.assertEqual(draft["script"]["title"], "Titulo editado")
            self.assertGreaterEqual(len(draft["script"]["beats"]), 2)

            approved = service.approve_package_script(
                str(package_path),
                {"title": "Titulo final", "full_text": draft["script"]["full_text"]},
            )
            self.assertEqual(approved["script"]["status"], "approved")

            tts = service.synthesize_package_tts(str(package_path), allow_stub=True)
            self.assertGreaterEqual(len(tts["segments"]), 1)
            self.assertEqual(tts["provider"], "stub")

            thumbs = service.generate_package_thumbs(str(package_path), count=3)
            self.assertGreaterEqual(len(thumbs["thumbnails"]), 2)

            data = json.loads(package_path.read_text(encoding="utf-8"))
            data["_package_dir"] = str(pkg_dir)
            allowed, reason, info = batch_gate_allows_render(data)
            # sin batch.yaml → single package permitido
            self.assertTrue(allowed)

    def test_stub_tts_writes_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = Path(tmp)
            (package_dir / "media" / "audio").mkdir(parents=True)
            package = {
                "_package_dir": str(package_dir),
                "channel_dna": {"locale": "es", "voice": {"voice_id": "v1"}},
                "script": {
                    "beats": [
                        {
                            "beat_id": "b01",
                            "spoken_text": "Texto de prueba para stub tts con suficientes palabras.",
                        }
                    ]
                },
            }
            segments = render_package_tts(package, tts=StubTtsAdapter())
            self.assertEqual(segments[0].status, "stub")
            self.assertTrue((package_dir / segments[0].relative_path).is_file())
