from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Callable
from typing import Any

from .database import Database, utc_now


JobWork = Callable[[Callable[[int], None]], dict[str, Any]]
ACTIVE_OR_COMPLETE = {"queued", "running", "succeeded"}


class JobRunner:
    def __init__(self, database: Database):
        self.database = database
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def start(self, project_id: str, kind: str, idempotency_key: str, work: JobWork) -> dict[str, Any]:
        existing = self.database.one(
            "SELECT * FROM jobs WHERE project_id=? AND idempotency_key=?",
            (project_id, idempotency_key),
        )
        if existing and existing["status"] in ACTIVE_OR_COMPLETE:
            return self._decode(existing)
        now = utc_now()
        if existing:
            job_id = existing["id"]
            self.database.execute(
                """UPDATE jobs SET status='queued', progress=0, error_code=NULL, error_message=NULL,
                   output_json=NULL, updated_at=? WHERE id=?""",
                (now, job_id),
            )
        else:
            job_id = str(uuid.uuid4())
            self.database.execute(
                """INSERT INTO jobs(id, project_id, kind, idempotency_key, status, progress, attempt, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'queued', 0, 0, ?, ?)""",
                (job_id, project_id, kind, idempotency_key, now, now),
            )
        thread = threading.Thread(target=self._run, args=(job_id, work), daemon=True, name=f"job-{job_id[:8]}")
        with self._lock:
            self._threads[job_id] = thread
        thread.start()
        return self.get(job_id)

    def _run(self, job_id: str, work: JobWork) -> None:
        self.database.execute(
            "UPDATE jobs SET status='running', attempt=attempt+1, updated_at=? WHERE id=?",
            (utc_now(), job_id),
        )

        def progress(value: int) -> None:
            bounded = max(0, min(100, int(value)))
            self.database.execute("UPDATE jobs SET progress=?, updated_at=? WHERE id=?", (bounded, utc_now(), job_id))

        try:
            output = work(progress)
            self.database.execute(
                """UPDATE jobs SET status='succeeded', progress=100, output_json=?,
                   error_code=NULL, error_message=NULL, updated_at=? WHERE id=?""",
                (json.dumps(output, ensure_ascii=False), utc_now(), job_id),
            )
        except Exception as error:
            self.database.execute(
                """UPDATE jobs SET status='failed', error_code=?, error_message=?, updated_at=? WHERE id=?""",
                (error.__class__.__name__, str(error)[:1000], utc_now(), job_id),
            )
        finally:
            with self._lock:
                self._threads.pop(job_id, None)

    def get(self, job_id: str) -> dict[str, Any]:
        row = self.database.one("SELECT * FROM jobs WHERE id=?", (job_id,))
        if not row:
            raise KeyError("Trabajo no encontrado.")
        return self._decode(row)

    @staticmethod
    def _decode(row: dict[str, Any]) -> dict[str, Any]:
        if row.get("output_json"):
            row["output"] = json.loads(row["output_json"])
        row.pop("output_json", None)
        return row

