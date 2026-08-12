"""Semaforo de salud FacelessCreator (green / yellow / red)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .credentials import CredentialStore
from .media import FFmpegAdapter
from .package_io import default_packages_root, list_packages


def _light(
    light_id: str,
    label: str,
    level: str,
    summary: str,
    *,
    detail: str = "",
    action: str = "",
) -> dict[str, str]:
    return {
        "id": light_id,
        "label": label,
        "level": level,
        "summary": summary,
        "detail": detail,
        "action": action,
    }


def _overall(lights: list[dict[str, str]]) -> str:
    if any(item["level"] == "red" for item in lights):
        return "red"
    if any(item["level"] == "yellow" for item in lights):
        return "yellow"
    return "green"


def build_health_board(
    *,
    credentials: CredentialStore | None = None,
    media: FFmpegAdapter | None = None,
    packages_root: Path | None = None,
    credentials_root: Path | None = None,
) -> dict[str, Any]:
    store = credentials or CredentialStore(credentials_root or Path.home() / ".facelesscreator-health")
    status = store.load().status()
    toolchain = media or FFmpegAdapter()
    root = packages_root or default_packages_root()
    lights: list[dict[str, str]] = []

    if toolchain.available():
        lights.append(
            _light(
                "ffmpeg",
                "FFmpeg / ffprobe",
                "green",
                "Disponible para preview/export",
            )
        )
    else:
        lights.append(
            _light(
                "ffmpeg",
                "FFmpeg / ffprobe",
                "red",
                "No disponible",
                action="Instala FFmpeg en PATH o usa el binario embebido del empaquetado",
            )
        )

    if status.get("elevenlabs"):
        voice_ok = bool(status.get("elevenlabs_voice_id"))
        lights.append(
            _light(
                "elevenlabs",
                "ElevenLabs TTS",
                "green" if voice_ok else "yellow",
                "Key presente" + ("" if voice_ok else " · falta voice_id"),
                detail=str(status.get("elevenlabs_voice_id_value") or ""),
                action="" if voice_ok else "Pega voice_id en Credenciales",
            )
        )
    else:
        lights.append(
            _light(
                "elevenlabs",
                "ElevenLabs TTS",
                "yellow",
                "Sin key · TTS stub (silencio/placeholder)",
                action="Credenciales → ElevenLabs API key",
            )
        )

    if status.get("omniroute"):
        lights.append(
            _light(
                "omniroute",
                "OmniRoute (guion LLM)",
                "green",
                "Key presente · guion LIVE si el servidor responde",
                detail=str(status.get("omniroute_base_url") or ""),
            )
        )
    else:
        lights.append(
            _light(
                "omniroute",
                "OmniRoute (guion LLM)",
                "yellow",
                "Sin key · plantilla de guion",
                action="Credenciales → OmniRoute API key",
            )
        )

    thumbs_live = bool(status.get("openai_images") or status.get("gemini"))
    lights.append(
        _light(
            "thumbs",
            "Miniaturas API",
            "green" if thumbs_live else "yellow",
            "Provider thumbs disponible" if thumbs_live else "Stub de miniaturas",
            action="" if thumbs_live else "Opcional: OpenAI/Gemini/OmniRoute para thumbs",
        )
    )

    if root.is_dir():
        try:
            packages = list_packages()
            n = len(packages)
        except Exception:
            n = 0
            packages = []
        lights.append(
            _light(
                "packages",
                "FacelessStudio packages",
                "green" if n else "yellow",
                f"{n} package(s) visibles",
                detail=str(root),
                action="" if n else "Exporta package desde YouToMagic o seed demo",
            )
        )
    else:
        lights.append(
            _light(
                "packages",
                "FacelessStudio packages",
                "red",
                "Carpeta no existe",
                detail=str(root),
                action="Crea Documents/FacelessStudio/packages",
            )
        )

    return {
        "app": "FacelessCreator",
        "checked_at": datetime.now(UTC).isoformat(),
        "overall": _overall(lights),
        "lights": lights,
        "notes": [
            "Verde = listo · Amarillo = atencion (stubs) · Rojo = bloqueante.",
            "ElevenLabs y guion LLM se configuran solo en FacelessCreator.",
        ],
    }
