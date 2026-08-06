from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def default_packages_root() -> Path:
    override = os.environ.get("FACELESS_STUDIO_PACKAGES", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / "Documents" / "FacelessStudio" / "packages").resolve()


def list_packages(root: Path | None = None) -> list[Path]:
    base = root or default_packages_root()
    if not base.is_dir():
        return []
    found: list[Path] = []
    for child in sorted(base.iterdir()):
        candidate = child / "package.yaml"
        if candidate.is_file():
            found.append(candidate)
    return found


def load_package(path: Path) -> dict[str, Any]:
    """Carga package.yaml (JSON o YAML mínimo vía JSON)."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("package.yaml debe ser un objeto")
    if "package_id" not in data or "script" not in data:
        raise ValueError("package incompleto: faltan package_id o script")
    data["_package_path"] = str(path.resolve())
    data["_package_dir"] = str(path.parent.resolve())
    return data


def narrative_blocks_from_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    """Adapta beats del PP al shape de bloques que usa FacelessCreator."""
    script = package.get("script") or {}
    beats = script.get("beats") or []
    blocks: list[dict[str, Any]] = []
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            continue
        text = str(beat.get("spoken_text") or "").strip()
        if not text:
            continue
        blocks.append(
            {
                "id": str(beat.get("beat_id") or f"b{index + 1:02d}"),
                "order": index,
                "text": text,
                "visual_instruction": str(beat.get("visual_intent") or ""),
                "duration": float(beat.get("est_duration_sec") or 8.0),
                "concept_key": str(beat.get("concept_key") or ""),
                "role": str(beat.get("role") or "block"),
            }
        )
    if not blocks:
        full = str(script.get("full_text") or "").strip()
        if full:
            blocks.append(
                {
                    "id": "b01",
                    "order": 0,
                    "text": full,
                    "visual_instruction": "",
                    "duration": 30.0,
                    "concept_key": "",
                    "role": "block",
                }
            )
    return blocks
