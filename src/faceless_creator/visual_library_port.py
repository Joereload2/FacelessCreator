from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .style_image_contract import DiskStyleImageBridge, StyleImageResponse


@dataclass(frozen=True)
class LibraryAssetRef:
    beat_id: str
    concept_key: str
    path: Path | None
    source: str  # package_media | visuallibrary | style_job | missing
    status: str  # ready | needs_review | unresolved | failed
    style_profile_id: str | None = None
    request_id: str | None = None
    error: str | None = None


class VisualLibraryResolvePort(Protocol):
    """Resolver imagen: package media o Style Profile job (sin generar en FC)."""

    def resolve_for_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        concept_key: str,
        visual_intent: str,
    ) -> LibraryAssetRef: ...


class PackageMediaVisualAdapter:
    """
    Infra sin API: busca media/images/{beat_id}.* o por concept_key.
    Cuando VL escriba assets al package, esto los encuentra.
    """

    def resolve_for_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        concept_key: str,
        visual_intent: str,
    ) -> LibraryAssetRef:
        images = package_dir / "media" / "images"
        if images.is_dir():
            for pattern in (f"{beat_id}.*", f"{concept_key}.*", f"*{beat_id}*"):
                matches = sorted(images.glob(pattern))
                files = [p for p in matches if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}]
                if files:
                    return LibraryAssetRef(
                        beat_id=beat_id,
                        concept_key=concept_key,
                        path=files[0],
                        source="package_media",
                        status="ready",
                    )
        return LibraryAssetRef(
            beat_id=beat_id,
            concept_key=concept_key,
            path=None,
            source="missing",
            status="unresolved",
        )


class StyleProfileVisualAdapter:
    """
    Solicita imagen a VL vía disco (Style Profile + scene prompt).
    No genera en FC. Opcionalmente invoca process_inbox_hook (p.ej. tests).
    """

    def __init__(
        self,
        *,
        style_profile_id: str,
        package_id: str | None = None,
        channel_id: str | None = None,
        bridge: DiskStyleImageBridge | None = None,
        process_inbox_hook=None,
        timeout_sec: float = 60.0,
        prefer_package_media: bool = True,
    ) -> None:
        self.style_profile_id = style_profile_id
        self.package_id = package_id
        self.channel_id = channel_id
        self.bridge = bridge or DiskStyleImageBridge()
        self.process_inbox_hook = process_inbox_hook
        self.timeout_sec = timeout_sec
        self.prefer_package_media = prefer_package_media

    def resolve_for_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        concept_key: str,
        visual_intent: str,
    ) -> LibraryAssetRef:
        if self.prefer_package_media:
            local = PackageMediaVisualAdapter().resolve_for_beat(
                package_dir=package_dir,
                beat_id=beat_id,
                concept_key=concept_key,
                visual_intent=visual_intent,
            )
            if local.status == "ready":
                return local

        if not self.style_profile_id.strip():
            return LibraryAssetRef(
                beat_id=beat_id,
                concept_key=concept_key,
                path=None,
                source="missing",
                status="unresolved",
                error="Falta style_profile_id",
            )

        resp: StyleImageResponse = self.bridge.request_and_wait(
            style_profile_id=self.style_profile_id,
            prompt=visual_intent or f"Scene for {beat_id}",
            beat_id=beat_id,
            package_id=self.package_id,
            channel_id=self.channel_id,
            timeout_sec=self.timeout_sec,
            process_inbox_hook=self.process_inbox_hook,
        )
        if resp.ok and resp.image_path:
            path = Path(resp.image_path)
            if path.is_file():
                return LibraryAssetRef(
                    beat_id=beat_id,
                    concept_key=concept_key,
                    path=path,
                    source="style_job",
                    status=resp.status if resp.status in {"ready", "needs_review"} else "ready",
                    style_profile_id=self.style_profile_id,
                    request_id=resp.request_id,
                )
        return LibraryAssetRef(
            beat_id=beat_id,
            concept_key=concept_key,
            path=None,
            source="style_job",
            status="failed" if resp.status == "failed" else "unresolved",
            style_profile_id=self.style_profile_id,
            request_id=resp.request_id,
            error=resp.error or f"status={resp.status}",
        )


class VisualLibraryHttpAdapter:
    """
    Skeleton HTTP: hoy no llama a la red.
    Preferir StyleProfileVisualAdapter (disco) o package media.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or "").rstrip("/")

    def resolve_for_beat(
        self,
        *,
        package_dir: Path,
        beat_id: str,
        concept_key: str,
        visual_intent: str,
    ) -> LibraryAssetRef:
        local = PackageMediaVisualAdapter().resolve_for_beat(
            package_dir=package_dir,
            beat_id=beat_id,
            concept_key=concept_key,
            visual_intent=visual_intent,
        )
        if local.status == "ready":
            return local
        if not self.base_url:
            return local
        raise NotImplementedError(
            "VisualLibraryHttpAdapter: usar StyleProfileVisualAdapter (disco). "
            f"base_url={self.base_url} beat={beat_id}"
        )
