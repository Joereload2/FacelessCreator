from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class VisualReference:
    id: str
    label: str
    relative_path: str
    source: str = "controlled-adapter"


class VisualLibraryPort(Protocol):
    def search(self, project_root: Path, instruction: str) -> list[VisualReference]: ...


class ControlledVisualAdapter:
    """Local deterministic adapter that proves the future Visual Library contract."""

    def search(self, project_root: Path, instruction: str) -> list[VisualReference]:
        folder = project_root / "visuals" / "alternatives"
        return [
            VisualReference(path.stem, path.stem.replace("-", " ").title(), path.relative_to(project_root).as_posix())
            for path in sorted(folder.glob("*.png"))
            if path.is_file()
        ]

