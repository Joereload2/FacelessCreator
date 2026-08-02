from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from faceless_creator.__main__ import default_workspace


class LauncherTests(unittest.TestCase):
    def test_uses_explicit_workspace_first(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"FACELESSCREATOR_HOME": folder, "LOCALAPPDATA": "ignored"}, clear=False):
                self.assertEqual(default_workspace(), Path(folder))

    def test_defaults_to_local_app_data(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}, clear=False):
                os.environ.pop("FACELESSCREATOR_HOME", None)
                self.assertEqual(default_workspace(), Path(folder) / "FacelessCreator")


if __name__ == "__main__":
    unittest.main()
