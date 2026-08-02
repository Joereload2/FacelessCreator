from pathlib import Path
import unittest


APP_SCRIPT = Path(__file__).parents[1] / "src" / "faceless_creator" / "web" / "app.js"


class WebRegressionTests(unittest.TestCase):
    def test_artifact_links_do_not_replace_desktop_window(self) -> None:
        script = APP_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("event.preventDefault();", script)
        self.assertIn("openArtifactExternally(artifact.id);", script)
        self.assertIn("/api/artifacts/${artifactId}/open", script)


if __name__ == "__main__":
    unittest.main()
