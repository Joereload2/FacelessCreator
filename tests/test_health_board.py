from pathlib import Path
import tempfile
import unittest

from faceless_creator.credentials import CredentialStore
from faceless_creator.health_board import build_health_board
from faceless_creator.media import FFmpegAdapter


class HealthBoardTests(unittest.TestCase):
    def test_board_has_lights_and_overall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = CredentialStore(Path(tmp))
            board = build_health_board(
                credentials=store,
                media=FFmpegAdapter(),
                packages_root=Path(tmp) / "packages",
            )
            self.assertEqual(board["app"], "FacelessCreator")
            self.assertIn(board["overall"], {"green", "yellow", "red"})
            ids = {light["id"] for light in board["lights"]}
            self.assertIn("ffmpeg", ids)
            self.assertIn("elevenlabs", ids)
            self.assertIn("omniroute", ids)
            self.assertIn("packages", ids)


if __name__ == "__main__":
    unittest.main()
