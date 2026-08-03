

from pathlib import Path
import unittest


STYLES = Path(__file__).parents[1] / "src" / "faceless_creator" / "web" / "styles.css"


class VerticalDensityTests(unittest.TestCase):
    def test_project_chrome_is_compact(self) -> None:
        styles = STYLES.read_text(encoding="utf-8")

        self.assertIn("grid-template-rows: 50px", styles)
        self.assertIn("html, body { width: 100%; height: 100%;", styles)
        self.assertIn("overflow: hidden", styles)
        self.assertIn(".app-shell { width: 100%; height: 100vh; overflow: hidden", styles)
        self.assertIn(".project-list, .scene-list, .inspector { scrollbar-width: none; }", styles)
        self.assertIn(".project-view { width: 100%; height: 100%;", styles)
        self.assertIn(".input-strip { min-height: 44px", styles)
        self.assertIn(".preview-toolbar { min-height: 48px", styles)
        self.assertIn(".operation-bar { min-height: 31px", styles)
        self.assertIn("height: clamp(240px, calc(100vh - 410px), 720px)", styles)
        self.assertIn("object-fit: contain", styles)


if __name__ == "__main__":
    unittest.main()
