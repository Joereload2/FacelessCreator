from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from faceless_creator.database import Database, SCHEMA_VERSION, utc_now


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temporary.name) / "test.sqlite3")
        self.database.migrate()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_migration_is_idempotent(self) -> None:
        self.database.migrate()
        row = self.database.one("SELECT version FROM schema_migrations")
        self.assertEqual(row["version"], SCHEMA_VERSION)

    def test_recovers_running_jobs(self) -> None:
        now = utc_now()
        self.database.execute(
            "INSERT INTO projects(id,name,status,width,height,fps,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            ("project", "Test", "draft", 1920, 1080, 30, now, now),
        )
        self.database.execute(
            """INSERT INTO jobs(id,project_id,kind,idempotency_key,status,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?)""",
            ("job", "project", "preview", "preview:1", "running", now, now),
        )
        self.assertEqual(self.database.recover_jobs(), 1)
        row = self.database.one("SELECT status,error_code FROM jobs WHERE id='job'")
        self.assertEqual(row, {"status": "interrupted", "error_code": "APP_RESTARTED"})


if __name__ == "__main__":
    unittest.main()

