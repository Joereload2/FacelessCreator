"""Schema 0.1 package validation (FacelessCreator)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from faceless_creator.package_io import load_package
from faceless_creator.package_validate import PackageValidationError, validate_package


class PackageValidateTests(unittest.TestCase):
    def test_import_requires_package_id(self):
        errs = validate_package({"script": {}}, level="import")
        self.assertTrue(any("package_id" in e for e in errs))

    def test_load_package_rejects_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "package.yaml"
            p.write_text(json.dumps({"script": {"title": "x"}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_package(p)

    def test_load_package_ok_minimal(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "package.yaml"
            p.write_text(
                json.dumps({"package_id": "pp_x", "script": {"status": "pending", "beats": []}}),
                encoding="utf-8",
            )
            data = load_package(p)
            self.assertEqual(data["package_id"], "pp_x")


if __name__ == "__main__":
    unittest.main()
