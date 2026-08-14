"""Contrato FC → VL: Style Image Request/Response (archivos en disco).

FacelessCreator NO genera imágenes. Escribe requests y lee responses.
VisuaLibrary es dueña del StyleProfile y de la generación.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def default_style_jobs_root() -> Path:
    return (Path.home() / "Documents" / "FacelessStudio" / "style_jobs").resolve()


def ensure_style_job_dirs(root: Path | None = None) -> Path:
    base = (root or default_style_jobs_root()).resolve()
    for sub in ("inbox", "outbox", "media"):
        (base / sub).mkdir(parents=True, exist_ok=True)
    return base


@dataclass
class StyleImageRequest:
    request_id: str
    style_profile_id: str
    prompt: str
    resolution: str = "1920x1080"
    aspect_ratio: str = "16:9"
    seed: int | None = None
    no_faces: bool = True
    package_id: str | None = None
    beat_id: str | None = None
    channel_id: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StyleImageRequest":
        return cls(
            request_id=str(data["request_id"]),
            style_profile_id=str(data["style_profile_id"]),
            prompt=str(data["prompt"]),
            resolution=str(data.get("resolution") or "1920x1080"),
            aspect_ratio=str(data.get("aspect_ratio") or "16:9"),
            seed=data.get("seed"),
            no_faces=bool(data.get("no_faces", True)),
            package_id=data.get("package_id"),
            beat_id=data.get("beat_id"),
            channel_id=data.get("channel_id"),
            created_at=data.get("created_at"),
        )


@dataclass
class StyleImageResponse:
    request_id: str
    status: str  # ready | failed | needs_review
    image_path: str | None = None
    hash: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in {"ready", "needs_review"} and bool(self.image_path)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StyleImageResponse":
        return cls(
            request_id=str(data.get("request_id") or ""),
            status=str(data.get("status") or "failed"),
            image_path=data.get("image_path"),
            hash=data.get("hash"),
            error=data.get("error"),
            metadata=dict(data.get("metadata") or {}),
        )


class DiskStyleImageBridge:
    """Puerto local-first: inbox/outbox JSON. No genera imágenes en FC."""

    def __init__(self, jobs_root: Path | None = None) -> None:
        self.root = ensure_style_job_dirs(jobs_root)

    @property
    def inbox(self) -> Path:
        return self.root / "inbox"

    @property
    def outbox(self) -> Path:
        return self.root / "outbox"

    def new_request_id(self, beat_id: str = "") -> str:
        suffix = uuid.uuid4().hex[:10]
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (beat_id or "x"))[:24]
        return f"req_{safe}_{suffix}"

    def write_request(self, request: StyleImageRequest) -> Path:
        if not request.created_at:
            request.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        path = self.inbox / f"{request.request_id}.json"
        path.write_text(
            json.dumps(request.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def read_response(self, request_id: str) -> StyleImageResponse | None:
        path = self.outbox / f"{request_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        return StyleImageResponse.from_dict(data)

    def wait_response(
        self,
        request_id: str,
        *,
        timeout_sec: float = 120.0,
        poll_sec: float = 0.5,
    ) -> StyleImageResponse | None:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            resp = self.read_response(request_id)
            if resp is not None:
                return resp
            time.sleep(poll_sec)
        return None

    def request_and_wait(
        self,
        *,
        style_profile_id: str,
        prompt: str,
        beat_id: str | None = None,
        package_id: str | None = None,
        channel_id: str | None = None,
        resolution: str = "1920x1080",
        aspect_ratio: str = "16:9",
        seed: int | None = None,
        no_faces: bool = True,
        timeout_sec: float = 90.0,
        process_inbox_hook=None,
    ) -> StyleImageResponse:
        """Write request; optionally run VL inbox processor; wait for outbox."""
        rid = self.new_request_id(beat_id or "")
        req = StyleImageRequest(
            request_id=rid,
            style_profile_id=style_profile_id,
            prompt=prompt,
            resolution=resolution,
            aspect_ratio=aspect_ratio,
            seed=seed,
            no_faces=no_faces,
            package_id=package_id,
            beat_id=beat_id,
            channel_id=channel_id,
        )
        self.write_request(req)
        if process_inbox_hook is not None:
            try:
                process_inbox_hook()
            except Exception as exc:  # pragma: no cover
                return StyleImageResponse(
                    request_id=rid,
                    status="failed",
                    error=f"VL process hook failed: {exc}",
                )
        resp = self.wait_response(rid, timeout_sec=timeout_sec)
        if resp is None:
            return StyleImageResponse(
                request_id=rid,
                status="failed",
                error=(
                    "Timeout esperando respuesta de VisuaLibrary. "
                    "Abre VL y ejecuta process_style_inbox (o deja el worker activo). "
                    f"Request en {self.inbox / (rid + '.json')}"
                ),
            )
        return resp

    def copy_image_into_project(
        self,
        response: StyleImageResponse,
        dest: Path,
    ) -> Path | None:
        if not response.ok or not response.image_path:
            return None
        src = Path(response.image_path)
        if not src.is_file():
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return dest


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
