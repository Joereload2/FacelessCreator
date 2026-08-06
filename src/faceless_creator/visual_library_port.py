from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class LibraryAssetRef:
    beat_id: str
    concept_key: str
    path: Path | None
    source: str  # package_media | visuallibrary | missing
    status: str


class VisualLibraryResolvePort(Protocol):
    """Contrato futuro: resolver imagen approved desde VisuaLibrary o media del package."""

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
                files = [p for p in matches if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
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


class VisualLibraryHttpAdapter:
    """
    Skeleton: cuando VL exponga un endpoint/local index, conectar aquí.
    Hoy no llama a la red.
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
        # Prefer local package media first
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
            "VisualLibraryHttpAdapter: implementar búsqueda por concept_key contra VL. "
            f"base_url={self.base_url} beat={beat_id}"
        )
