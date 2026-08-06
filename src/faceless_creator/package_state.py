from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_package_dict(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("package.yaml debe ser un objeto")
    data["_package_path"] = str(path.resolve())
    data["_package_dir"] = str(path.parent.resolve())
    return data


def save_package_dict(package: dict[str, Any], path: Path | None = None) -> Path:
    target = Path(path or package.get("_package_path") or "")
    if not target:
        raise ValueError("sin ruta de package")
    clean = {k: v for k, v in package.items() if not str(k).startswith("_")}
    target.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def append_event(package_dir: Path, *, action: str, package_id: str | None = None, payload: dict[str, Any] | None = None) -> None:
    events = package_dir / "events.jsonl"
    with events.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "ts": utc_now(),
                    "package_id": package_id,
                    "station": "facelesscreator",
                    "action": action,
                    "payload": payload or {},
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def set_stage(package: dict[str, Any], stage: str, status: str | None = None) -> dict[str, Any]:
    meta = dict(package.get("meta") or {})
    meta["stage"] = stage
    if status:
        meta["status"] = status
    else:
        meta["status"] = stage
    package["meta"] = meta
    return package


def find_batch_yaml(package: dict[str, Any]) -> Path | None:
    meta = package.get("meta") or {}
    canonical = meta.get("canonical_episode_dir")
    if canonical:
        batch = Path(canonical).parent.parent / "batch.yaml"
        if batch.is_file():
            return batch
    package_dir = Path(package.get("_package_dir") or "")
    # episode dir: .../episodes/ep-xx → batch.yaml is ../../batch.yaml
    candidate = package_dir.parent.parent / "batch.yaml"
    if candidate.is_file():
        return candidate
    return None


def batch_gate_allows_render(package: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    """Comprueba gate del lote. Override: FACELESS_BATCH_GATE_OVERRIDE=1."""
    if os.environ.get("FACELESS_BATCH_GATE_OVERRIDE", "").strip() in {"1", "true", "yes"}:
        return True, "override_env", {"override": True}
    batch_path = find_batch_yaml(package)
    if batch_path is None:
        # Packages sueltos (legacy un solo video): permitir con aviso
        return True, "no_batch_single_package", {"batch": None}
    try:
        batch = json.loads(batch_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return False, f"batch_unreadable: {error}", {}
    policy = batch.get("policy") or {}
    min_ready = int(policy.get("min_ready_before_first_render") or 10)
    # Recompute quickly from episodes on disk
    root = batch_path.parent
    render_ready = 0
    episodes_dir = root / "episodes"
    if episodes_dir.is_dir():
        for ep in episodes_dir.iterdir():
            pkg = ep / "package.yaml"
            if not pkg.is_file():
                continue
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            script = data.get("script") or {}
            script_ok = str(script.get("status") or "") == "approved" and bool(
                script.get("beats") or script.get("full_text")
            )
            images_ok = any(
                p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                for p in (ep / "media" / "images").glob("*")
            ) if (ep / "media" / "images").is_dir() else False
            audio_ok = any((ep / "media" / "audio").iterdir()) if (ep / "media" / "audio").is_dir() else False
            thumbs_ok = sum(1 for _ in (ep / "media" / "thumbs").glob("*")) >= 2 if (ep / "media" / "thumbs").is_dir() else False
            if script_ok and images_ok and audio_ok and thumbs_ok:
                render_ready += 1
    allowed = render_ready >= min_ready
    info = {
        "batch_path": str(batch_path),
        "render_ready": render_ready,
        "min_ready": min_ready,
    }
    if allowed:
        return True, "batch_gate_ok", info
    return (
        False,
        f"Gate del lote: {render_ready}/{min_ready} episodios render_ready. "
        f"Completa guion+imagenes+audio+thumbs (≥2) o usa FACELESS_BATCH_GATE_OVERRIDE=1.",
        info,
    )
