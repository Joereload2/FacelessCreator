from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import Settings
from .database import Database, utc_now
from .domain import DomainError, NarrativeBlock, RenderPlan, Scene, safe_project_path
from .jobs import JobRunner
from .media import FFmpegAdapter, sha256_file, write_srt
from .visuals import ControlledVisualAdapter


DEMO_SCRIPT = {
    "title": "Viaje de demostración",
    "blocks": [
        {
            "id": "opening",
            "text": "Toda historia comienza con una primera imagen.",
            "visual_instruction": "Un océano nocturno sereno.",
            "duration": 3,
        },
        {
            "id": "middle",
            "text": "El ritmo conecta la narración con cada escena.",
            "visual_instruction": "Un horizonte cálido y cinematográfico.",
            "duration": 3,
        },
        {
            "id": "ending",
            "text": "FacelessCreator conserva el plan para poder corregirlo.",
            "visual_instruction": "Un bosque profundo que sugiera continuidad.",
            "duration": 3,
        },
    ],
}


class NotFoundError(KeyError):
    pass


class FacelessCreatorService:
    def __init__(self, settings: Settings, media: FFmpegAdapter | None = None):
        self.settings = settings
        self.settings.ensure()
        self.database = Database(settings.database)
        self.database.migrate()
        self.recovered_jobs = self.database.recover_jobs()
        self.media = media or FFmpegAdapter()
        self.visuals = ControlledVisualAdapter()
        self.jobs = JobRunner(self.database)

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "0.1.0",
            "ffmpeg": self.media.available(),
            "database": str(self.settings.database),
            "recovered_jobs": self.recovered_jobs,
        }

    def create_project(self, name: str) -> dict[str, Any]:
        clean_name = name.strip()
        if not clean_name:
            raise DomainError("El proyecto necesita un nombre.")
        project_id = str(uuid.uuid4())
        now = utc_now()
        root = self.project_root(project_id)
        for folder in ("inputs", "visuals", "plans", "temp", "outputs"):
            (root / folder).mkdir(parents=True, exist_ok=True)
        self.database.execute(
            """INSERT INTO projects(id, name, status, width, height, fps, created_at, updated_at)
               VALUES (?, ?, 'draft', ?, ?, ?, ?, ?)""",
            (project_id, clean_name, self.settings.width, self.settings.height, self.settings.fps, now, now),
        )
        self.database.execute(
            "INSERT INTO project_snapshots(project_id, updated_at) VALUES (?, ?)",
            (project_id, now),
        )
        return self.get_project(project_id)

    def list_projects(self) -> list[dict[str, Any]]:
        return [self._enrich_project(row) for row in self.database.all("SELECT * FROM projects ORDER BY updated_at DESC")]

    def get_project(self, project_id: str) -> dict[str, Any]:
        row = self.database.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not row:
            raise NotFoundError("Proyecto no encontrado.")
        return self._enrich_project(row)

    def prepare_demo(self, project_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        key = f"prepare-demo:{project['plan_version'] + 1}"

        def work(progress: Any) -> dict[str, Any]:
            progress(5)
            root = self.project_root(project_id)
            inputs = self.media.create_demo_inputs(root, project["width"], project["height"])
            progress(55)
            blocks = tuple(NarrativeBlock.from_dict(value, index) for index, value in enumerate(DEMO_SCRIPT["blocks"]))
            start = 0.0
            scenes: list[Scene] = []
            for block, image in zip(blocks, inputs["images"], strict=True):
                scenes.append(
                    Scene(
                        id=f"scene-{block.id}",
                        order=block.order,
                        block_id=block.id,
                        start=start,
                        duration=block.duration,
                        image_path=image["path"],
                        visual_instruction=block.visual_instruction,
                    )
                )
                start += block.duration
            plan = RenderPlan(
                version=project["plan_version"] + 1,
                width=project["width"],
                height=project["height"],
                fps=project["fps"],
                audio_path=inputs["audio"],
                scenes=tuple(scenes),
            )
            plan.validate(root)
            self._save_snapshots(project_id, DEMO_SCRIPT, plan)
            progress(85)
            plan_path = safe_project_path(root, f"plans/render-plan-v{plan.version}.json")
            self._write_json_atomic(plan_path, plan.to_dict())
            self.database.execute(
                "UPDATE projects SET status='review', plan_version=?, updated_at=? WHERE id=?",
                (plan.version, utc_now(), project_id),
            )
            progress(100)
            return {"project_id": project_id, "plan_version": plan.version}

        return self.jobs.start(project_id, "prepare", key, work)

    def start_render(self, project_id: str, kind: str) -> dict[str, Any]:
        if kind not in {"preview", "export"}:
            raise DomainError("Tipo de render no admitido.")
        project = self.get_project(project_id)
        plan = self._load_plan(project_id)
        key = f"{kind}:plan:{plan.version}"

        def work(progress: Any) -> dict[str, Any]:
            root = self.project_root(project_id)
            relative = f"temp/preview-v{plan.version}.mp4" if kind == "preview" else f"outputs/video-v{plan.version}.mp4"
            output = self.media.render(root, plan, relative, progress)
            artifacts: list[dict[str, Any]] = [self._record_artifact(project_id, kind, output)]
            if kind == "export":
                script = self._load_script(project_id)
                texts = {block["id"]: block["text"] for block in script["blocks"]}
                srt = safe_project_path(root, f"outputs/subtitles-v{plan.version}.srt")
                write_srt(srt, plan.scenes, texts)
                artifacts.append(self._record_artifact(project_id, "subtitle", srt))
                manifest = safe_project_path(root, f"outputs/manifest-v{plan.version}.json")
                manifest_data = {
                    "project_id": project_id,
                    "render_plan": plan.to_dict(),
                    "artifacts": [{"kind": item["kind"], "path": item["relative_path"], "sha256": item["sha256"]} for item in artifacts],
                    "created_at": utc_now(),
                }
                self._write_json_atomic(manifest, manifest_data)
                artifacts.append(self._record_artifact(project_id, "manifest", manifest))
                self.database.execute(
                    "UPDATE projects SET status='completed', updated_at=? WHERE id=?",
                    (utc_now(), project_id),
                )
            return {"artifacts": artifacts, "plan_version": plan.version}

        return self.jobs.start(project_id, kind, key, work)

    def alternatives(self, project_id: str, scene_id: str) -> list[dict[str, Any]]:
        plan = self._load_plan(project_id)
        scene = next((item for item in plan.scenes if item.id == scene_id), None)
        if not scene:
            raise NotFoundError("Escena no encontrada.")
        return [asdict(item) for item in self.visuals.search(self.project_root(project_id), scene.visual_instruction)]

    def replace_visual(self, project_id: str, scene_id: str, relative_path: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        root = self.project_root(project_id)
        safe_project_path(root, relative_path, must_exist=True)
        plan = self._load_plan(project_id)
        found = False
        scenes: list[Scene] = []
        for scene in plan.scenes:
            if scene.id == scene_id:
                scene = Scene(**(asdict(scene) | {"image_path": relative_path}))
                found = True
            scenes.append(scene)
        if not found:
            raise NotFoundError("Escena no encontrada.")
        revised = RenderPlan(
            version=plan.version + 1,
            width=plan.width,
            height=plan.height,
            fps=plan.fps,
            audio_path=plan.audio_path,
            scenes=tuple(scenes),
        )
        revised.validate(root)
        self._save_snapshots(project_id, self._load_script(project_id), revised)
        self._write_json_atomic(safe_project_path(root, f"plans/render-plan-v{revised.version}.json"), revised.to_dict())
        self.database.execute(
            "UPDATE projects SET status='review', plan_version=?, updated_at=? WHERE id=?",
            (revised.version, utc_now(), project_id),
        )
        return self.get_project(project_id)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self.jobs.get(job_id)

    def artifact_path(self, artifact_id: str) -> tuple[Path, str]:
        row = self.database.one("SELECT * FROM artifacts WHERE id=?", (artifact_id,))
        if not row:
            raise NotFoundError("Artefacto no encontrado.")
        path = safe_project_path(self.project_root(row["project_id"]), row["relative_path"], must_exist=True)
        return path, row["kind"]

    def open_artifact(self, artifact_id: str) -> None:
        path, _ = self.artifact_path(artifact_id)
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            raise DomainError("Abrir externamente solo está habilitado en Windows por ahora.")

    def project_root(self, project_id: str) -> Path:
        try:
            parsed = uuid.UUID(project_id)
        except ValueError as error:
            raise DomainError("Identificador de proyecto inválido.") from error
        return (self.settings.projects / str(parsed)).resolve()

    def _enrich_project(self, row: dict[str, Any]) -> dict[str, Any]:
        snapshot = self.database.one("SELECT * FROM project_snapshots WHERE project_id=?", (row["id"],))
        jobs = [self.jobs._decode(item) for item in self.database.all("SELECT * FROM jobs WHERE project_id=? ORDER BY created_at DESC LIMIT 12", (row["id"],))]
        artifacts = [self.database.decode_json(item, "metadata_json") for item in self.database.all("SELECT * FROM artifacts WHERE project_id=? ORDER BY created_at DESC", (row["id"],))]
        row["script"] = json.loads(snapshot["script_json"]) if snapshot and snapshot.get("script_json") else None
        row["render_plan"] = json.loads(snapshot["plan_json"]) if snapshot and snapshot.get("plan_json") else None
        row["jobs"] = jobs
        row["artifacts"] = artifacts
        return row

    def _save_snapshots(self, project_id: str, script: dict[str, Any], plan: RenderPlan) -> None:
        self.database.execute(
            """UPDATE project_snapshots SET script_json=?, plan_json=?, updated_at=? WHERE project_id=?""",
            (json.dumps(script, ensure_ascii=False), json.dumps(plan.to_dict(), ensure_ascii=False), utc_now(), project_id),
        )

    def _load_script(self, project_id: str) -> dict[str, Any]:
        row = self.database.one("SELECT script_json FROM project_snapshots WHERE project_id=?", (project_id,))
        if not row or not row["script_json"]:
            raise DomainError("El proyecto todavía no tiene guion.")
        return json.loads(row["script_json"])

    def _load_plan(self, project_id: str) -> RenderPlan:
        row = self.database.one("SELECT plan_json FROM project_snapshots WHERE project_id=?", (project_id,))
        if not row or not row["plan_json"]:
            raise DomainError("El proyecto todavía no tiene RenderPlan.")
        value = json.loads(row["plan_json"])
        scenes = tuple(Scene(**{key: item[key] for key in ("id", "order", "block_id", "start", "duration", "image_path", "visual_instruction")}) for item in value["scenes"])
        return RenderPlan(value["version"], value["width"], value["height"], value["fps"], value["audio_path"], scenes)

    def _record_artifact(self, project_id: str, kind: str, path: Path) -> dict[str, Any]:
        root = self.project_root(project_id)
        relative = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        artifact_id = str(uuid.uuid4())
        metadata = self.media.probe(path) if path.suffix.lower() == ".mp4" else {}
        self.database.execute(
            """INSERT OR REPLACE INTO artifacts(id, project_id, kind, relative_path, sha256, size, metadata_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (artifact_id, project_id, kind, relative, digest, path.stat().st_size, json.dumps(metadata), utc_now()),
        )
        return {"id": artifact_id, "kind": kind, "relative_path": relative, "sha256": digest, "size": path.stat().st_size}

    @staticmethod
    def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

