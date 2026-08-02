from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root: Path
    host: str = "127.0.0.1"
    port: int = 8765
    width: int = 1920
    height: int = 1080
    fps: int = 30

    @classmethod
    def for_root(cls, root: Path | str) -> "Settings":
        return cls(root=Path(root).expanduser().resolve())

    @property
    def database(self) -> Path:
        return self.root / "facelesscreator.sqlite3"

    @property
    def projects(self) -> Path:
        return self.root / "projects"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.projects.mkdir(parents=True, exist_ok=True)

