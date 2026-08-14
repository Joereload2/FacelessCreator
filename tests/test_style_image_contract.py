"""Style image disk contract (FC does not generate)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from faceless_creator.style_image_contract import (
    DiskStyleImageBridge,
    StyleImageRequest,
    StyleImageResponse,
)


def test_write_request_and_read_response() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp_path = Path(raw)
        bridge = DiskStyleImageBridge(jobs_root=tmp_path / "style_jobs")
        req = StyleImageRequest(
            request_id="req_unit_1",
            style_profile_id="sp_demo",
            prompt="Ocean at night",
            beat_id="opening",
        )
        path = bridge.write_request(req)
        assert path.is_file()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["style_profile_id"] == "sp_demo"
        assert data["no_faces"] is True

        out = {
            "request_id": "req_unit_1",
            "status": "ready",
            "image_path": str(tmp_path / "img.png"),
            "hash": "abc",
            "metadata": {
                "style_profile_id": "sp_demo",
                "prompt_used": "x",
                "model": "stub",
                "no_faces": True,
            },
        }
        (tmp_path / "img.png").write_bytes(b"fakepng")
        (bridge.outbox / "req_unit_1.json").write_text(json.dumps(out), encoding="utf-8")
        resp = bridge.read_response("req_unit_1")
        assert resp is not None
        assert resp.ok
        dest = tmp_path / "project" / "in.png"
        copied = bridge.copy_image_into_project(resp, dest)
        assert copied is not None and copied.is_file()


def test_request_and_wait_with_hook() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp_path = Path(raw)
        bridge = DiskStyleImageBridge(jobs_root=tmp_path / "jobs")

        def hook() -> None:
            for p in bridge.inbox.glob("*.json"):
                req = StyleImageRequest.from_dict(json.loads(p.read_text(encoding="utf-8")))
                img = bridge.root / "media" / f"{req.request_id}.png"
                img.parent.mkdir(parents=True, exist_ok=True)
                img.write_bytes(b"\x89PNG\r\n")
                (bridge.outbox / f"{req.request_id}.json").write_text(
                    json.dumps(
                        {
                            "request_id": req.request_id,
                            "status": "needs_review",
                            "image_path": str(img),
                            "hash": "h",
                            "metadata": {
                                "style_profile_id": req.style_profile_id,
                                "provider": "stub",
                            },
                        }
                    ),
                    encoding="utf-8",
                )

        resp = bridge.request_and_wait(
            style_profile_id="sp_x",
            prompt="forest",
            beat_id="b1",
            timeout_sec=5,
            process_inbox_hook=hook,
        )
        assert resp.ok
        assert resp.status == "needs_review"
