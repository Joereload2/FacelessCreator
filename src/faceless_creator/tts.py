from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TtsSegment:
    beat_id: str
    text: str
    relative_path: str
    duration_sec: float
    text_hash: str
    provider: str
    status: str  # ready | stub | failed


class TtsPort(Protocol):
    """Puerto de voz. Implementación real ElevenLabs se conecta con API key."""

    def synthesize_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        text: str,
        voice_id: str,
        locale: str,
    ) -> TtsSegment: ...


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


class StubTtsAdapter:
    """
    Infra lista sin API: crea un marcador .txt por beat y duración estimada.
    """

    provider_name = "stub"

    def synthesize_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        text: str,
        voice_id: str,
        locale: str,
    ) -> TtsSegment:
        audio_dir = package_dir / "media" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        digest = text_hash(text)
        marker = audio_dir / f"{beat_id}.{digest}.stub.txt"
        marker.write_text(
            f"STUB TTS\nbeat={beat_id}\nvoice_id={voice_id}\nlocale={locale}\n\n{text.strip()}\n",
            encoding="utf-8",
        )
        words = max(1, len(text.split()))
        duration = max(5.0, min(40.0, words * 0.45))
        return TtsSegment(
            beat_id=beat_id,
            text=text.strip(),
            relative_path=marker.relative_to(package_dir).as_posix(),
            duration_sec=duration,
            text_hash=digest,
            provider=self.provider_name,
            status="stub",
        )


class ElevenLabsTtsAdapter:
    """ElevenLabs TTS real. Requiere ELEVENLABS_API_KEY."""

    provider_name = "elevenlabs"

    def __init__(self, api_key: str | None = None, model_id: str | None = None) -> None:
        self.api_key = (
            api_key
            or os.environ.get("ELEVENLABS_API_KEY")
            or os.environ.get("YOUTOMAGIC_ELEVENLABS_API_KEY")
            or ""
        ).strip()
        self.model_id = model_id or os.environ.get("ELEVENLABS_MODEL_ID") or "eleven_multilingual_v2"

    def synthesize_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        text: str,
        voice_id: str,
        locale: str,
    ) -> TtsSegment:
        if not self.api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY requerida. Sin key usa StubTtsAdapter o configura la credencial."
            )
        if not voice_id or voice_id == "default":
            raise RuntimeError("voice_id de ElevenLabs requerido en channel_dna.voice.voice_id")

        audio_dir = package_dir / "media" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        digest = text_hash(text)
        out_path = audio_dir / f"{beat_id}.{digest}.mp3"
        if out_path.is_file() and out_path.stat().st_size > 100:
            words = max(1, len(text.split()))
            return TtsSegment(
                beat_id=beat_id,
                text=text.strip(),
                relative_path=out_path.relative_to(package_dir).as_posix(),
                duration_sec=max(5.0, min(40.0, words * 0.45)),
                text_hash=digest,
                provider=self.provider_name,
                status="ready",
            )

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        payload = {
            "text": text.strip(),
            "model_id": self.model_id,
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.7},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                audio_bytes = resp.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:400]
            raise RuntimeError(f"ElevenLabs HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"ElevenLabs no alcanzable: {error}") from error

        if len(audio_bytes) < 100:
            raise RuntimeError("ElevenLabs devolvio audio vacio")
        out_path.write_bytes(audio_bytes)
        words = max(1, len(text.split()))
        return TtsSegment(
            beat_id=beat_id,
            text=text.strip(),
            relative_path=out_path.relative_to(package_dir).as_posix(),
            duration_sec=max(5.0, min(40.0, words * 0.45)),
            text_hash=digest,
            provider=self.provider_name,
            status="ready",
        )


def pick_tts_adapter(*, allow_stub_fallback: bool = True) -> TtsPort:
    key = (
        os.environ.get("ELEVENLABS_API_KEY")
        or os.environ.get("YOUTOMAGIC_ELEVENLABS_API_KEY")
        or ""
    ).strip()
    if key:
        return ElevenLabsTtsAdapter(api_key=key)
    if allow_stub_fallback:
        return StubTtsAdapter()
    raise RuntimeError("ELEVENLABS_API_KEY no configurada y stub deshabilitado")


def render_package_tts(
    package: dict,
    *,
    tts: TtsPort | None = None,
) -> list[TtsSegment]:
    """Recorre beats del package y genera segmentos (stub o real)."""
    package_dir = Path(package["_package_dir"])
    dna = package.get("channel_dna") or {}
    voice = dna.get("voice") or {}
    voice_id = str(voice.get("voice_id") or "default")
    locale = str(dna.get("locale") or package.get("meta", {}).get("locale") or "es")
    adapter = tts or pick_tts_adapter(allow_stub_fallback=True)
    script = package.get("script") or {}
    beats = script.get("beats") or []
    segments: list[TtsSegment] = []
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        beat_id = str(beat.get("beat_id") or "b00")
        text = str(beat.get("spoken_text") or "").strip()
        if not text:
            continue
        segments.append(
            adapter.synthesize_beat(
                package_dir=package_dir,
                beat_id=beat_id,
                text=text,
                voice_id=voice_id,
                locale=locale,
            )
        )
    return segments
