"""Credenciales locales de FacelessCreator (archivo en UserData + env override)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENV_MAP = {
    "elevenlabs_api_key": ("ELEVENLABS_API_KEY", "YOUTOMAGIC_ELEVENLABS_API_KEY"),
    "elevenlabs_voice_id": ("ELEVENLABS_VOICE_ID", "YOUTOMAGIC_ELEVENLABS_VOICE_ID"),
    "omniroute_base_url": ("OMNIROUTE_BASE_URL", "YOUTOMAGIC_OMNIROUTE_BASE_URL"),
    "omniroute_api_key": ("OMNIROUTE_API_KEY", "OPENAI_API_KEY", "YOUTOMAGIC_OMNIROUTE_API_KEY"),
    "openai_api_key": ("OPENAI_API_KEY",),
    "gemini_api_key": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
}


@dataclass
class CredentialBundle:
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    omniroute_base_url: str = "http://127.0.0.1:20128/v1"
    omniroute_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""

    def status(self) -> dict[str, Any]:
        return {
            "elevenlabs": bool(self.elevenlabs_api_key.strip()),
            "elevenlabs_voice_id": bool(self.elevenlabs_voice_id.strip()),
            "elevenlabs_voice_id_value": self.elevenlabs_voice_id.strip()[:8] + "…"
            if len(self.elevenlabs_voice_id.strip()) > 8
            else self.elevenlabs_voice_id.strip(),
            "omniroute": bool(self.omniroute_api_key.strip()),
            "omniroute_base_url": self.omniroute_base_url.strip() or "http://127.0.0.1:20128/v1",
            "openai_images": bool(self.openai_api_key.strip() or self.omniroute_api_key.strip()),
            "gemini": bool(self.gemini_api_key.strip()),
            "batch_gate_override": os.environ.get("FACELESS_BATCH_GATE_OVERRIDE", ""),
            "sources": {
                "file": True,
                "env_overlay": True,
            },
        }

    def apply_to_environ(self) -> None:
        """Expone keys al proceso para adapters que leen os.environ."""
        if self.elevenlabs_api_key:
            os.environ["ELEVENLABS_API_KEY"] = self.elevenlabs_api_key
        if self.elevenlabs_voice_id:
            os.environ["ELEVENLABS_VOICE_ID"] = self.elevenlabs_voice_id
            os.environ["YOUTOMAGIC_ELEVENLABS_VOICE_ID"] = self.elevenlabs_voice_id
        if self.omniroute_base_url:
            os.environ["OMNIROUTE_BASE_URL"] = self.omniroute_base_url.rstrip("/")
        if self.omniroute_api_key:
            os.environ["OMNIROUTE_API_KEY"] = self.omniroute_api_key
        if self.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.openai_api_key
        if self.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key


class CredentialStore:
    def __init__(self, root: Path) -> None:
        self.path = Path(root) / "credentials.json"

    def load(self) -> CredentialBundle:
        data: dict[str, Any] = {}
        if self.path.is_file():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    data = raw
            except (OSError, json.JSONDecodeError):
                data = {}
        bundle = CredentialBundle(
            elevenlabs_api_key=str(data.get("elevenlabs_api_key") or ""),
            elevenlabs_voice_id=str(data.get("elevenlabs_voice_id") or ""),
            omniroute_base_url=str(data.get("omniroute_base_url") or "http://127.0.0.1:20128/v1"),
            omniroute_api_key=str(data.get("omniroute_api_key") or ""),
            openai_api_key=str(data.get("openai_api_key") or ""),
            gemini_api_key=str(data.get("gemini_api_key") or ""),
        )
        # Env overrides file
        for field, env_keys in ENV_MAP.items():
            for env_key in env_keys:
                val = os.environ.get(env_key, "").strip()
                if val:
                    setattr(bundle, field, val)
                    break
        bundle.apply_to_environ()
        return bundle

    def save(self, updates: dict[str, Any], *, clear: list[str] | None = None) -> CredentialBundle:
        current = {}
        if self.path.is_file():
            try:
                current = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(current, dict):
                    current = {}
            except (OSError, json.JSONDecodeError):
                current = {}
        for key in clear or []:
            current.pop(key, None)
        for key, value in updates.items():
            if value is None:
                continue
            text = str(value).strip()
            if text == "":
                # empty string means "don't overwrite" except explicit clear
                continue
            current[key] = text
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.load()
