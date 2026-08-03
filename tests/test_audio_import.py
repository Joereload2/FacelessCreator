from __future__ import annotations

import io
import tempfile
import unittest
import wave
from pathlib import Path

from faceless_creator.config import Settings
from faceless_creator.domain import DomainError
from faceless_creator.service import FacelessCreatorService

from .helpers import wait_for_job


def silent_wav(duration_seconds: int = 2, sample_rate: int = 8000) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(b"\0\0" * sample_rate * duration_seconds)
    return output.getvalue()


class AudioImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.service = FacelessCreatorService(Settings(Path(self.temporary.name), width=160, height=90, fps=10))
        self.project = self.service.create_project("Audio real")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_imported_audio_is_validated_persisted_and_used_by_plan(self) -> None:
        payload = silent_wav()
        project = self.service.import_audio(self.project["id"], "narración.wav", io.BytesIO(payload), len(payload))

        self.assertEqual(project["audio"]["original_name"], "narración.wav")
        self.assertAlmostEqual(project["audio"]["duration"], 2, places=1)
        audio_path = self.service.project_root(project["id"]) / project["audio"]["relative_path"]
        self.assertTrue(audio_path.is_file())

        prepared = wait_for_job(self.service, self.service.prepare_demo(project["id"])["id"])
        self.assertEqual(prepared["status"], "succeeded", prepared.get("error_message"))
        planned = self.service.get_project(project["id"])
        self.assertEqual(planned["render_plan"]["audio_path"], project["audio"]["relative_path"])
        self.assertAlmostEqual(planned["render_plan"]["duration"], 2, places=1)

    def test_rejects_unsupported_audio_extension(self) -> None:
        payload = silent_wav()
        with self.assertRaisesRegex(DomainError, "Formato de audio"):
            self.service.import_audio(self.project["id"], "audio.exe", io.BytesIO(payload), len(payload))


if __name__ == "__main__":
    unittest.main()
