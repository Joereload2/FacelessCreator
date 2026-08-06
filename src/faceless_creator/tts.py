from __future__ import annotations

import hashlib
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
    """Puerto de voz. Implementación real ElevenLabs se conecta después."""

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
    Cuando conectes ElevenLabs, sustituye esta clase por ElevenLabsTtsAdapter.
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
        # Placeholder hasta API: no es audio real, pero el pipeline puede listar segmentos.
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
    """
    Skeleton listo para API key real.
    No llama a la red hasta implementar synthesize con httpx + ELEVENLABS_API_KEY.
    """

    provider_name = "elevenlabs"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or "").strip()

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
            # Fallback honesto a stub
            return StubTtsAdapter().synthesize_beat(
                package_dir=package_dir,
                beat_id=beat_id,
                text=text,
                voice_id=voice_id,
                locale=locale,
            )
        raise NotImplementedError(
            "ElevenLabsTtsAdapter: conectar POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id} "
            "y escribir media/audio/{beat_id}.mp3. API key detectada; implementación pendiente."
        )


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
    adapter = tts or StubTtsAdapter()
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
