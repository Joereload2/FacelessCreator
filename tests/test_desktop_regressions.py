from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class DesktopRegressionTests(unittest.TestCase):
    def test_release_executable_uses_windows_gui_subsystem(self) -> None:
        main_source = (ROOT / "src-tauri" / "src" / "main.rs").read_text(encoding="utf-8")
        self.assertIn(
            '#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]',
            main_source,
        )

    def test_packaged_backend_does_not_create_console(self) -> None:
        specification = (ROOT / "FacelessCreatorSidecar.spec").read_text(encoding="utf-8")
        self.assertIn("console=False", specification)


if __name__ == "__main__":
    unittest.main()
