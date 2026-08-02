from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faceless_creator.domain import DomainError, NarrativeBlock, RenderPlan, Scene, safe_project_path


class NarrativeBlockTests(unittest.TestCase):
    def test_validates_required_fields(self) -> None:
        with self.assertRaisesRegex(DomainError, "instrucción visual"):
            NarrativeBlock.from_dict({"text": "Narración", "duration": 2}, 0)

    def test_builds_stable_default_id(self) -> None:
        block = NarrativeBlock.from_dict(
            {"text": "Narración", "visual_instruction": "Océano", "duration": 2}, 1
        )
        self.assertEqual(block.id, "block-2")


class PathTests(unittest.TestCase):
    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(DomainError, "sale del workspace"):
                safe_project_path(Path(folder), "../outside.mp4")

    def test_rejects_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(DomainError, "relativa"):
                safe_project_path(Path(folder), str(Path(folder).resolve() / "input.png"))


class RenderPlanTests(unittest.TestCase):
    def test_rejects_gap_between_scenes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "image.png").write_bytes(b"image")
            (root / "audio.wav").write_bytes(b"audio")
            plan = RenderPlan(
                1,
                1920,
                1080,
                30,
                "audio.wav",
                (Scene("scene", 0, "block", 1, 2, "image.png", "Visual"),),
            )
            with self.assertRaisesRegex(DomainError, "continuas"):
                plan.validate(root)


if __name__ == "__main__":
    unittest.main()

