from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class DomainError(ValueError):
    """A user-correctable domain validation error."""


@dataclass(frozen=True)
class NarrativeBlock:
    id: str
    order: int
    text: str
    visual_instruction: str
    duration: float

    @classmethod
    def from_dict(cls, value: dict[str, Any], order: int) -> "NarrativeBlock":
        text = str(value.get("text", "")).strip()
        visual = str(value.get("visual_instruction", "")).strip()
        duration = float(value.get("duration", 0))
        if not text:
            raise DomainError(f"El bloque {order + 1} necesita texto.")
        if not visual:
            raise DomainError(f"El bloque {order + 1} necesita una instrucción visual.")
        if duration <= 0:
            raise DomainError(f"El bloque {order + 1} necesita duración positiva.")
        return cls(
            id=str(value.get("id") or f"block-{order + 1}"),
            order=order,
            text=text,
            visual_instruction=visual,
            duration=duration,
        )


@dataclass(frozen=True)
class Scene:
    id: str
    order: int
    block_id: str
    start: float
    duration: float
    image_path: str
    visual_instruction: str

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass(frozen=True)
class RenderPlan:
    version: int
    width: int
    height: int
    fps: int
    audio_path: str
    scenes: tuple[Scene, ...]

    def validate(self, project_root: Path) -> None:
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise DomainError("La configuración de video no es válida.")
        if not self.scenes:
            raise DomainError("El RenderPlan necesita al menos una escena.")
        expected = 0.0
        for scene in self.scenes:
            if abs(scene.start - expected) > 0.001:
                raise DomainError("Las escenas deben ser continuas y ordenadas.")
            if scene.duration <= 0:
                raise DomainError("Toda escena necesita duración positiva.")
            safe_project_path(project_root, scene.image_path, must_exist=True)
            expected = scene.end
        safe_project_path(project_root, self.audio_path, must_exist=True)

    @property
    def duration(self) -> float:
        return sum(scene.duration for scene in self.scenes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "scenes": [asdict(scene) | {"end": scene.end} for scene in self.scenes],
        }


def safe_project_path(root: Path, relative: str, *, must_exist: bool = False) -> Path:
    if not relative or Path(relative).is_absolute():
        raise DomainError("La ruta debe ser relativa al proyecto.")
    resolved_root = root.resolve()
    target = (resolved_root / relative).resolve()
    try:
        target.relative_to(resolved_root)
    except ValueError as error:
        raise DomainError("La ruta sale del workspace del proyecto.") from error
    if must_exist and not target.is_file():
        raise DomainError(f"No existe el archivo requerido: {relative}")
    return target

