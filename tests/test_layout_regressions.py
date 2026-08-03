from pathlib import Path
import unittest


WEB_ROOT = Path(__file__).parents[1] / "src" / "faceless_creator" / "web"


class LayoutRegressionTests(unittest.TestCase):
    def test_primary_layout_has_no_sidebar(self) -> None:
        markup = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        styles = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertNotIn('<aside class="sidebar"', markup)
        self.assertIn("grid-template-rows: 52px", styles)
        self.assertIn('id="project-list"', markup)

    def test_audio_input_is_exposed_and_connected(self) -> None:
        markup = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="audio-input"', markup)
        self.assertIn("importSelectedAudio", script)
        self.assertIn("/audio`", script)


if __name__ == "__main__":
    unittest.main()
