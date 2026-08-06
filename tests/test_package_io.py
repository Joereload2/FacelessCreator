from __future__ import annotations

import json
import unittest
from pathlib import Path

from faceless_creator.package_io import (
    default_packages_root,
    load_package,
    narrative_blocks_from_package,
)
from faceless_creator.tts import StubTtsAdapter, render_package_tts, text_hash
from faceless_creator.visual_library_port import PackageMediaVisualAdapter


class PackageIoTests(unittest.TestCase):
    def test_default_root_name(self) -> None:
        root = default_packages_root()
        self.assertEqual(root.name, "packages")
        self.assertEqual(root.parent.name, "FacelessStudio")

    def test_load_package_and_blocks(self) -> None:
        folder = Path(__file__).resolve().parents[1] / "_tmp_pkg"
        folder.mkdir(exist_ok=True)
        pkg_path = folder / "package.yaml"
        payload = {
            "package_id": "pp_unit",
            "channel_dna": {"locale": "es", "voice": {"voice_id": "v1"}},
            "script": {
                "status": "approved",
                "title": "Demo",
                "full_text": "Hola mundo del guion.",
                "beats": [
                    {
                        "beat_id": "b01",
                        "spoken_text": "Hola mundo del guion.",
                        "visual_intent": "apertura clara",
                        "concept_key": "hello",
                        "est_duration_sec": 6,
                    }
                ],
            },
        }
        pkg_path.write_text(json.dumps(payload), encoding="utf-8")
        package = load_package(pkg_path)
        blocks = narrative_blocks_from_package(package)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["id"], "b01")
        self.assertIn("Hola", blocks[0]["text"])

    def test_stub_tts_writes_marker(self) -> None:
        folder = Path(__file__).resolve().parents[1] / "_tmp_tts"
        folder.mkdir(exist_ok=True)
        (folder / "media" / "audio").mkdir(parents=True, exist_ok=True)
        package = {
            "_package_dir": str(folder),
            "channel_dna": {"locale": "es", "voice": {"voice_id": "abc"}},
            "script": {
                "beats": [
                    {"beat_id": "b01", "spoken_text": "Texto de prueba para stub tts con suficientes palabras."}
                ]
            },
        }
        segments = render_package_tts(package, tts=StubTtsAdapter())
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].status, "stub")
        self.assertTrue((folder / segments[0].relative_path).exists())
        self.assertEqual(segments[0].text_hash, text_hash(segments[0].text))

    def test_package_media_visual_missing(self) -> None:
        folder = Path(__file__).resolve().parents[1] / "_tmp_vis"
        folder.mkdir(exist_ok=True)
        ref = PackageMediaVisualAdapter().resolve_for_beat(
            package_dir=folder,
            beat_id="b01",
            concept_key="x",
            visual_intent="y",
        )
        self.assertEqual(ref.status, "unresolved")


if __name__ == "__main__":
    unittest.main()
