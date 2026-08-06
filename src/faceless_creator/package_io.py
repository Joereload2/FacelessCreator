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


def default_studio_root() -> Path:
    override = os.environ.get("FACELESS_STUDIO_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / "Documents" / "FacelessStudio").resolve()


def list_packages(root: Path | None = None) -> list[Path]:
    """Lista package.yaml en packages/ flat y en channels/**/episodes/**.

    Prefiere la ruta canónica del episodio (channels/...) si existe;
    si no, el espejo packages/. Deduplica por package_id.
    """
    found: list[Path] = []
    studio = default_studio_root()
    channels = studio / "channels"
    if channels.is_dir():
        for candidate in sorted(channels.rglob("package.yaml")):
            found.append(candidate)
    base = root or default_packages_root()
    if base.is_dir():
        for child in sorted(base.iterdir()):
            candidate = child / "package.yaml"
            if candidate.is_file():
                found.append(candidate)
    by_id: dict[str, Path] = {}
    for path in found:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = str(data.get("package_id") or path.parent.name)
        except (OSError, json.JSONDecodeError):
            pid = path.parent.name
        # first wins = channels canonical first
        if pid not in by_id:
            by_id[pid] = path
    return list(by_id.values())


def load_package(path: Path) -> dict[str, Any]:
    """Carga package.yaml (JSON). Acepta brief_ready sin beats."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("package.yaml debe ser un objeto")
    if "package_id" not in data:
        raise ValueError("package incompleto: falta package_id")
    if "script" not in data:
        data["script"] = {"status": "pending", "title": "", "full_text": "", "beats": []}
    # Load sibling brief.yaml if missing embedded brief
    if "brief" not in data:
        brief_path = path.parent / "brief.yaml"
        if brief_path.is_file():
            try:
                brief = json.loads(brief_path.read_text(encoding="utf-8"))
                if isinstance(brief, dict):
                    data["brief"] = brief
            except (OSError, json.JSONDecodeError):
                pass
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
