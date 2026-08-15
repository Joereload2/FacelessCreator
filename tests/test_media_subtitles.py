from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faceless_creator.domain import Scene
from faceless_creator.media import FFmpegAdapter, write_srt, write_subtitles, write_vtt


class SubtitlesAndMediaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_write_srt_formatting(self) -> None:
        scenes = (
            Scene("s1", 0, "b1", 0.0, 3.5, "img1.png", "Scene 1"),
            Scene("s2", 1, "b2", 3.5, 3.75, "img2.png", "Scene 2"),
        )
        texts = {"b1": "Primera línea de narración.", "b2": "Segunda línea de narración."}
        srt_path = self.folder / "subtitles.srt"
        write_srt(srt_path, scenes, texts)

        self.assertTrue(srt_path.is_file())
        content = srt_path.read_text(encoding="utf-8")
        self.assertIn("1\n00:00:00,000 --> 00:00:03,500\nPrimera línea de narración.", content)
        self.assertIn("2\n00:00:03,500 --> 00:00:07,250\nSegunda línea de narración.", content)

    def test_write_vtt_formatting(self) -> None:
        scenes = (
            Scene("s1", 0, "b1", 0.0, 3.5, "img1.png", "Scene 1"),
            Scene("s2", 1, "b2", 3.5, 3.75, "img2.png", "Scene 2"),
        )
        texts = {"b1": "Primera línea de narración.", "b2": "Segunda línea de narración."}
        vtt_path = self.folder / "subtitles.vtt"
        write_vtt(vtt_path, scenes, texts)

        self.assertTrue(vtt_path.is_file())
        content = vtt_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("WEBVTT"))
        self.assertIn("1\n00:00:00.000 --> 00:00:03.500\nPrimera línea de narración.", content)
        self.assertIn("2\n00:00:03.500 --> 00:00:07.250\nSegunda línea de narración.", content)

    def test_write_subtitles_generates_both_formats(self) -> None:
        scenes = (Scene("s1", 0, "b1", 0.0, 2.0, "img1.png", "Scene 1"),)
        texts = {"b1": "Texto corto"}
        base = self.folder / "out" / "subtitles"
        paths = write_subtitles(base, scenes, texts)

        self.assertEqual(len(paths), 2)
        srt_file, vtt_file = paths
        self.assertEqual(srt_file.suffix, ".srt")
        self.assertEqual(vtt_file.suffix, ".vtt")
        self.assertTrue(srt_file.is_file())
        self.assertTrue(vtt_file.is_file())

    def test_ffmpeg_encoder_detection(self) -> None:
        adapter = FFmpegAdapter()
        encoders = adapter.detect_encoders()
        self.assertIsInstance(encoders, set)


if __name__ == "__main__":
    unittest.main()
