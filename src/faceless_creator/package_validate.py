"""Validador package FacelessStudio 0.1 (sin deps). Misma lógica que YTM / CLI studio."""
from __future__ import annotations

from typing import Any

SCHEMA_VERSION_PREFIX = "0.1"


class PackageValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors) if errors else "package inválido")


def validate_package(data: Any, *, level: str = "import") -> list[str]:
    errors: list[str] = []
    level = (level or "import").strip().lower()
    if level not in {"import", "export", "strict"}:
        return [f"level desconocido: {level}"]

    if not isinstance(data, dict):
        return ["package debe ser un objeto JSON"]

    pid = data.get("package_id")
    if not isinstance(pid, str) or not pid.strip():
        errors.append("falta package_id (string no vacío)")

    meta = data.get("meta")
    if meta is not None and not isinstance(meta, dict):
        errors.append("meta debe ser objeto si está presente")

    script = data.get("script")
    if script is not None and not isinstance(script, dict):
        errors.append("script debe ser objeto si está presente")

    if isinstance(script, dict):
        beats = script.get("beats")
        if beats is not None:
            if not isinstance(beats, list):
                errors.append("script.beats debe ser array")
            else:
                for i, beat in enumerate(beats):
                    if not isinstance(beat, dict):
                        errors.append(f"script.beats[{i}] debe ser objeto")
                        continue
                    if not isinstance(beat.get("beat_id"), str) or not str(beat.get("beat_id")).strip():
                        errors.append(f"script.beats[{i}].beat_id requerido")
                    if not isinstance(beat.get("spoken_text"), str) or not str(
                        beat.get("spoken_text")
                    ).strip():
                        errors.append(f"script.beats[{i}].spoken_text requerido")

    assets = data.get("image_assets")
    if assets is not None:
        if not isinstance(assets, list):
            errors.append("image_assets debe ser array")
        else:
            for i, a in enumerate(assets):
                if not isinstance(a, dict):
                    errors.append(f"image_assets[{i}] debe ser objeto")
                    continue
                if not str(a.get("beat_id") or "").strip():
                    errors.append(f"image_assets[{i}].beat_id requerido")
                if not str(a.get("path") or "").strip():
                    errors.append(f"image_assets[{i}].path requerido")

    for key in ("audio", "timeline", "channel_dna", "packaging", "brief"):
        val = data.get(key)
        if val is not None and not isinstance(val, dict):
            errors.append(f"{key} debe ser objeto si está presente")

    needs = data.get("image_needs")
    if needs is not None and not isinstance(needs, list):
        errors.append("image_needs debe ser array")

    if level in {"export", "strict"}:
        if not isinstance(script, dict):
            errors.append("export: script requerido")
        else:
            beats = script.get("beats")
            if not isinstance(beats, list) or len(beats) < 1:
                errors.append("export: script.beats debe tener al menos 1 beat")
            full = str(script.get("full_text") or "").strip()
            title = str(script.get("title") or "").strip()
            if not full and not title:
                errors.append("export: script.title o script.full_text requerido")

    if level == "strict":
        sv = data.get("schema_version")
        if not isinstance(sv, str) or not sv.startswith(SCHEMA_VERSION_PREFIX):
            errors.append(f"strict: schema_version debe ser {SCHEMA_VERSION_PREFIX}.x")
        dna = data.get("channel_dna")
        if not isinstance(dna, dict):
            errors.append("strict: channel_dna requerido")
        elif not str(dna.get("niche_id") or "").strip():
            errors.append("strict: channel_dna.niche_id requerido")

    return errors


def validate_or_raise(data: Any, *, level: str = "import") -> None:
    errors = validate_package(data, level=level)
    if errors:
        raise PackageValidationError(errors)
