from pathlib import Path
import unittest


STYLES = Path(__file__).parents[1] / "src" / "faceless_creator" / "web" / "styles.css"


class VerticalDensityTests(unittest.TestCase):
    def test_project_chrome_is_compact(self) -> None:
        styles = STYLES.read_text(encoding="utf-8")

        self.assertIn(".project-view { padding: 10px", styles)
        self.assertIn(".project-header .eyebrow { display: none; }", styles)
        self.assertIn(".stage-nav", styles)
        self.assertIn("margin: 8px 0", styles)
        self.assertIn(".input-strip { min-height: 42px", styles)


if __name__ == "__main__":
    unittest.main()
