from pathlib import Path
import re
import unittest


WEB_ROOT = Path(__file__).parents[1] / "src" / "faceless_creator" / "web"


def camel_case(identifier: str) -> str:
    first, *rest = identifier.split("-")
    return first + "".join(part.capitalize() for part in rest)


class LayoutRegressionTests(unittest.TestCase):
    def test_primary_layout_has_no_sidebar_or_stage_bar(self) -> None:
        markup = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        styles = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertNotIn('<aside class="sidebar"', markup)
        self.assertNotIn("stage-nav", markup)
        self.assertIn("grid-template-rows: 50px", styles)
        self.assertIn('id="project-list"', markup)

    def test_workspace_preserves_product_proportions(self) -> None:
        markup = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        styles = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

        self.assertIn("minmax(0, 73fr) minmax(280px, 27fr)", styles)
        self.assertIn('class="filmstrip-card"', markup)
        self.assertIn('id="operation-bar"', markup)

    def test_audio_and_primary_workflow_are_connected(self) -> None:
        markup = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="audio-input"', markup)
        self.assertIn('id="primary-action-button"', markup)
        self.assertIn("importSelectedAudio", script)
        self.assertIn("runPrimaryAction", script)
        self.assertIn("/audio`", script)

    def test_every_javascript_element_reference_exists_in_markup(self) -> None:
        markup = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
        identifiers = {camel_case(value) for value in re.findall(r'id="([^"]+)"', markup)}
        references = set(re.findall(r"elements\.([A-Za-z0-9]+)", script))

        self.assertEqual(references - identifiers, set())


if __name__ == "__main__":
    unittest.main()
