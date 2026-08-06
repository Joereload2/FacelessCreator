from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from .domain import DomainError, RenderPlan, safe_project_path


Progress = Callable[[int], None]


class MediaError(RuntimeError):
    pass


class FFmpegAdapter:
    def __init__(self, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe"):
        self.ffmpeg = shutil.which(ffmpeg) or ffmpeg
        self.ffprobe = shutil.which(ffprobe) or ffprobe

    def available(self) -> bool:
        return bool(shutil.which(self.ffmpeg) and shutil.which(self.ffprobe))

    def _run(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                arguments,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as error:
            raise MediaError(f"No se pudo iniciar la herramienta multimedia: {error}") from error
        if result.returncode:
            message = (result.stderr or result.stdout)[-2000:].strip()
            raise MediaError(f"La herramienta multimedia falló: {message}")
        return result

    def probe(self, path: Path) -> dict[str, Any]:
        result = self._run(
            [self.ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise MediaError("ffprobe devolvió información inválida.") from error

    def create_demo_inputs(self, project_root: Path, width: int, height: int) -> dict[str, Any]:
        inputs = project_root / "inputs"
        alternatives = project_root / "visuals" / "alternatives"
        inputs.mkdir(parents=True, exist_ok=True)
        alternatives.mkdir(parents=True, exist_ok=True)
        colors = [
            ("ocean", "0x123A5A", "Océano nocturno"),
            ("ember", "0x873E23", "Horizonte cálido"),
            ("forest", "0x1D5138", "Bosque profundo"),
        ]
        alt_colors = [
            ("violet", "0x49306B", "Alternativa violeta"),
            ("gold", "0x8A6B24", "Alternativa dorada"),
        ]
        images: list[dict[str, str]] = []
        for name, color, label in colors:
            path = inputs / f"{name}.png"
            self._color_image(path, color, width, height)
            images.append({"id": name, "label": label, "path": path.relative_to(project_root).as_posix()})
        alternatives_result: list[dict[str, str]] = []
        for name, color, label in alt_colors:
            path = alternatives / f"{name}.png"
            self._color_image(path, color, width, height)
            alternatives_result.append(
                {"id": name, "label": label, "path": path.relative_to(project_root).as_posix()}
            )
        audio = inputs / "narration.wav"
        self._run(
            [
                self.ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=220:sample_rate=48000:duration=9",
                "-c:a",
                "pcm_s16le",
                str(audio),
            ]
        )
        return {
            "audio": audio.relative_to(project_root).as_posix(),
            "images": images,
            "alternatives": alternatives_result,
        }

    def _color_image(self, path: Path, color: str, width: int, height: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._run(
            [
                self.ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s={width}x{height}:d=1",
                "-frames:v",
                "1",
                str(path),
            ]
        )

    def write_color_image(self, path: Path, color: str, width: int, height: int) -> None:
        self._color_image(path, color, width, height)

    def write_silence_wav(self, path: Path, duration_sec: float) -> None:
        """Audio silencioso para montaje cuando aún no hay ElevenLabs."""
        path.parent.mkdir(parents=True, exist_ok=True)
        duration = max(0.5, float(duration_sec))
        self._run(
            [
                self.ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r=48000:cl=mono",
                "-t",
                f"{duration:.3f}",
                "-c:a",
                "pcm_s16le",
                str(path),
            ]
        )

    def render(self, project_root: Path, plan: RenderPlan, destination: str, progress: Progress) -> Path:
        plan.validate(project_root)
        output = safe_project_path(project_root, destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".part.mp4")
        if temporary.exists():
            temporary.unlink()
        progress(10)
        arguments = [self.ffmpeg, "-y"]
        for scene in plan.scenes:
            arguments.extend(["-loop", "1", "-t", f"{scene.duration:.3f}", "-i", str(safe_project_path(project_root, scene.image_path, must_exist=True))])
        arguments.extend(["-i", str(safe_project_path(project_root, plan.audio_path, must_exist=True))])
        video_inputs = "".join(f"[{i}:v]scale={plan.width}:{plan.height}:force_original_aspect_ratio=increase,crop={plan.width}:{plan.height},setsar=1[v{i}];" for i in range(len(plan.scenes)))
        concat_inputs = "".join(f"[v{i}]" for i in range(len(plan.scenes)))
        filter_graph = f"{video_inputs}{concat_inputs}concat=n={len(plan.scenes)}:v=1:a=0,format=yuv420p[vout]"
        arguments.extend(
            [
                "-filter_complex",
                filter_graph,
                "-map",
                "[vout]",
                "-map",
                f"{len(plan.scenes)}:a:0",
                "-r",
                str(plan.fps),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(temporary),
            ]
        )
        progress(25)
        self._run(arguments)
        progress(85)
        metadata = self.probe(temporary)
        video = next((stream for stream in metadata.get("streams", []) if stream.get("codec_type") == "video"), None)
        if not video or video.get("width") != plan.width or video.get("height") != plan.height:
            temporary.unlink(missing_ok=True)
            raise MediaError("El video generado no cumple la resolución del plan.")
        temporary.replace(output)
        progress(100)
        return output


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_srt(path: Path, scenes: tuple[Any, ...], texts: dict[str, str]) -> None:
    def stamp(seconds: float) -> str:
        milliseconds = round(seconds * 1000)
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    content: list[str] = []
    for index, scene in enumerate(scenes, 1):
        content.extend([str(index), f"{stamp(scene.start)} --> {stamp(scene.end)}", texts[scene.block_id], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".srt.part")
    temporary.write_text("\n".join(content), encoding="utf-8")
    temporary.replace(path)

