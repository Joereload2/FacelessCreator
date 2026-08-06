

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, BinaryIO

from .config import Settings
from .database import Database, utc_now
from .domain import DomainError, NarrativeBlock, RenderPlan, Scene, safe_project_path
from .jobs import JobRunner
from .media import FFmpegAdapter, sha256_file, write_srt
from .package_io import default_packages_root, list_packages, load_package, narrative_blocks_from_package
from .package_state import append_event, batch_gate_allows_render, save_package_dict, set_stage, utc_now as package_utc
from .packaging_thumbs import apply_thumbs_to_package, pick_packaging_adapter
from .script_writer import TemplateScriptWriter, pick_script_writer
from .tts import StubTtsAdapter, pick_tts_adapter, render_package_tts
from .visual_library_port import PackageMediaVisualAdapter
from .visuals import ControlledVisualAdapter


MAX_AUDIO_BYTES = 1024 * 1024 * 1024
ALLOWED_AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav"}


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
            "packages_root": str(default_packages_root()),
        }

    def list_studio_packages(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in list_packages():
            try:
                package = load_package(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            script = package.get("script") or {}
            brief = package.get("brief") or {}
            meta = package.get("meta") or {}
            items.append(
                {
                    "package_id": package.get("package_id"),
                    "title": script.get("title") or brief.get("title") or package.get("package_id"),
                    "path": str(path),
                    "beats": len(script.get("beats") or []),
                    "status": meta.get("status"),
                    "stage": meta.get("stage"),
                    "script_status": script.get("status"),
                    "has_brief": bool(brief),
                }
            )
        return items

    def get_studio_package(self, package_path: str) -> dict[str, Any]:
        """Carga un package para el constructor de guion (brief + script)."""
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        script = package.get("script") or {}
        brief = package.get("brief") or {}
        meta = package.get("meta") or {}
        return {
            "package_id": package.get("package_id"),
            "path": str(path),
            "brief": brief,
            "script": script,
            "meta": {
                "status": meta.get("status"),
                "stage": meta.get("stage"),
                "idea_title": meta.get("idea_title"),
                "locale": meta.get("locale"),
            },
            "channel_dna": package.get("channel_dna") or {},
            "packaging": package.get("packaging") or {},
        }

    def save_package_script_draft(self, package_path: str, script: dict[str, Any] | None = None) -> dict[str, Any]:
        """Guarda borrador de guion editado a mano (sin aprobar)."""
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        current = dict(package.get("script") or {})
        if script:
            current.update(script)
        full_text = str(current.get("full_text") or "").strip()
        beats = current.get("beats") if isinstance(current.get("beats"), list) else []
        if full_text and not beats:
            beats = self._beats_from_full_text(full_text, str(current.get("title") or "Episodio"))
            current["beats"] = beats
        elif full_text and beats:
            # Si el usuario edito solo full_text, regenerar beats desde parrafos
            if script and "full_text" in script and "beats" not in script:
                current["beats"] = self._beats_from_full_text(full_text, str(current.get("title") or "Episodio"))
        if not full_text and not current.get("beats"):
            raise DomainError("El borrador esta vacio. Escribe o genera un guion primero.")
        if not full_text and current.get("beats"):
            current["full_text"] = "\n\n".join(
                str(b.get("spoken_text") or "") for b in current["beats"] if isinstance(b, dict)
            )
        current["status"] = "draft"
        current["version"] = int(current.get("version") or 0) + 1
        package["script"] = current
        set_stage(package, "script", "script_draft")
        save_package_dict(package, path)
        append_event(
            Path(package["_package_dir"]),
            action="script_draft_saved",
            package_id=str(package.get("package_id")),
            payload={"beats": len(current.get("beats") or []), "chars": len(str(current.get("full_text") or ""))},
        )
        return {"package_id": package.get("package_id"), "script": current, "path": str(path)}

    @staticmethod
    def _beats_from_full_text(full_text: str, title: str) -> list[dict[str, Any]]:
        paragraphs = [p.strip() for p in full_text.replace("\r\n", "\n").split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [full_text.strip() or title]
        roles = ["hook", "problem", "evidence", "method", "cta"]
        beats: list[dict[str, Any]] = []
        for index, spoken in enumerate(paragraphs, 1):
            role = roles[index - 1] if index <= len(roles) else "block"
            words = max(1, len(spoken.split()))
            beats.append(
                {
                    "beat_id": f"b{index:02d}",
                    "role": role,
                    "spoken_text": spoken[:900],
                    "est_duration_sec": max(5.0, min(40.0, words * 0.45)),
                    "visual_intent": f"{role}: ilustrar sin texto en frame",
                    "concept_key": f"{role}-{index}",
                    "representation_key": "lesson",
                }
            )
        return beats

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

    def import_audio(self, project_id: str, filename: str, source: BinaryIO, size: int) -> dict[str, Any]:
        project = self.get_project(project_id)
        if size <= 0:
            raise DomainError("El archivo de audio está vacío.")
        if size > MAX_AUDIO_BYTES:
            raise DomainError("El audio supera el límite de 1 GB.")
        original_name = Path(filename).name
        suffix = Path(original_name).suffix.lower()
        if suffix not in ALLOWED_AUDIO_SUFFIXES:
            raise DomainError("Formato de audio no admitido. Usa WAV, MP3, M4A, AAC, FLAC u OGG.")
        root = self.project_root(project_id)
        temporary = safe_project_path(root, f"inputs/.audio-{uuid.uuid4().hex}.part")
        remaining = size
        try:
            with temporary.open("xb") as output:
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise DomainError("El archivo de audio llegó incompleto.")
                    output.write(chunk)
                    remaining -= len(chunk)
            probe = self.media.probe(temporary)
            audio_stream = next((item for item in probe.get("streams", []) if item.get("codec_type") == "audio"), None)
            duration_value = probe.get("format", {}).get("duration") or (audio_stream or {}).get("duration")
            duration = float(duration_value or 0)
            if not audio_stream or duration <= 0:
                raise DomainError("El archivo no contiene una pista de audio válida.")
            digest = sha256_file(temporary)
            relative_path = f"inputs/audio-{digest[:16]}{suffix}"
            destination = safe_project_path(root, relative_path)
            if destination.exists():
                temporary.unlink()
            else:
                temporary.replace(destination)
            audio = {
                "relative_path": relative_path,
                "original_name": original_name,
                "sha256": digest,
                "size": size,
                "duration": duration,
                "format": suffix.removeprefix("."),
            }
            now = utc_now()
            self.database.execute(
                "UPDATE project_snapshots SET audio_json=?, plan_json=NULL, updated_at=? WHERE project_id=?",
                (json.dumps(audio, ensure_ascii=False), now, project_id),
            )
            self.database.execute(
                "UPDATE projects SET status='draft', updated_at=? WHERE id=?",
                (now, project_id),
            )
            return self.get_project(project_id)
        finally:
            temporary.unlink(missing_ok=True)

    def prepare_demo(self, project_id: str) -> dict[str, Any]:
        project = self.get_project(project_id)
        key = f"prepare-demo:{project['plan_version'] + 1}"

        def work(progress: Any) -> dict[str, Any]:
            progress(5)
            root = self.project_root(project_id)
            inputs = self.media.create_demo_inputs(root, project["width"], project["height"])
            audio = project.get("audio")
            audio_path = audio["relative_path"] if audio else inputs["audio"]
            target_duration = float(audio["duration"]) if audio else sum(item["duration"] for item in DEMO_SCRIPT["blocks"])
            duration_scale = target_duration / sum(item["duration"] for item in DEMO_SCRIPT["blocks"])
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
                        duration=block.duration * duration_scale,
                        image_path=image["path"],
                        visual_instruction=block.visual_instruction,
                    )
                )
                start += block.duration * duration_scale
            plan = RenderPlan(
                version=project["plan_version"] + 1,
                width=project["width"],
                height=project["height"],
                fps=project["fps"],
                audio_path=audio_path,
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

    def prepare_from_package(self, project_id: str, package_path: str) -> dict[str, Any]:
        """Importa package FacelessStudio (YTM), TTS stub, placeholders visuales, plan render."""
        project = self.get_project(project_id)
        path = Path(package_path).expanduser().resolve()
        if not path.is_file():
            raise DomainError("No se encontró package.yaml en la ruta indicada.")
        key = f"prepare-package:{path}:{project['plan_version'] + 1}"

        def work(progress: Any) -> dict[str, Any]:
            progress(5)
            package = load_package(path)
            package_dir = Path(package["_package_dir"])
            root = self.project_root(project_id)
            progress(15)
            # Si solo hay brief, generar guion plantilla (sin LLM) antes de montar.
            script = package.get("script") or {}
            if str(script.get("status") or "") != "approved" or not (script.get("beats") or script.get("full_text")):
                written = TemplateScriptWriter().write_from_brief(package)
                package["script"] = {
                    "status": "approved",
                    "title": written.title,
                    "full_text": written.full_text,
                    "beats": written.beats,
                    "writer": {
                        "kind": written.writer_kind,
                        "llm": written.writer_llm,
                        "model": written.writer_model,
                        "provider": written.writer_provider,
                    },
                    "approved_at": package_utc(),
                    "version": 1,
                }
                set_stage(package, "script", "script_approved")
                save_package_dict(package)
                append_event(
                    package_dir,
                    action="script_written_on_import",
                    package_id=str(package.get("package_id")),
                    payload={"writer_kind": written.writer_kind},
                )
            progress(22)
            # TTS: ElevenLabs si hay key; si no, stub honesto.
            tts_segments = render_package_tts(package, tts=pick_tts_adapter(allow_stub_fallback=True))
            progress(30)
            raw_blocks = narrative_blocks_from_package(package)
            if not raw_blocks:
                raise DomainError("El package no tiene beats/guion utilizable.")
            # Duraciones: preferir est_duration de beats; escalar si hay audio importado.
            total = sum(float(block["duration"]) for block in raw_blocks)
            audio_row = project.get("audio")
            if audio_row and float(audio_row.get("duration") or 0) > 0:
                scale = float(audio_row["duration"]) / total
                audio_rel = audio_row["relative_path"]
            else:
                scale = 1.0
                silence = safe_project_path(root, "inputs/package-silence.wav")
                self.media.write_silence_wav(silence, total)
                audio_rel = silence.relative_to(root).as_posix()
                probe = self.media.probe(silence)
                duration = float(probe.get("format", {}).get("duration") or total)
                audio_meta = {
                    "relative_path": audio_rel,
                    "original_name": "package-silence.wav",
                    "sha256": sha256_file(silence),
                    "size": silence.stat().st_size,
                    "duration": duration,
                    "format": "wav",
                    "source": "package_stub_silence",
                }
                self.database.execute(
                    "UPDATE project_snapshots SET audio_json=?, updated_at=? WHERE project_id=?",
                    (json.dumps(audio_meta, ensure_ascii=False), utc_now(), project_id),
                )
            progress(50)
            resolver = PackageMediaVisualAdapter()
            colors = ["0x123A5A", "0x873E23", "0x1D5138", "0x49306B", "0x8A6B24", "0x2A4058"]
            start = 0.0
            scenes: list[Scene] = []
            script_blocks: list[dict[str, Any]] = []
            for index, raw in enumerate(raw_blocks):
                duration = max(0.5, float(raw["duration"]) * scale)
                visual = str(raw.get("visual_instruction") or f"Escena {index + 1}").strip()
                if not visual:
                    visual = f"Escena {index + 1}"
                block_dict = {
                    "id": raw["id"],
                    "text": raw["text"],
                    "visual_instruction": visual,
                    "duration": duration,
                }
                script_blocks.append(block_dict)
                block = NarrativeBlock.from_dict(block_dict, index)
                ref = resolver.resolve_for_beat(
                    package_dir=package_dir,
                    beat_id=block.id,
                    concept_key=str(raw.get("concept_key") or ""),
                    visual_intent=visual,
                )
                if ref.path and ref.path.is_file():
                    dest = safe_project_path(root, f"inputs/{block.id}{ref.path.suffix.lower()}")
                    dest.write_bytes(ref.path.read_bytes())
                    image_rel = dest.relative_to(root).as_posix()
                else:
                    dest = safe_project_path(root, f"inputs/{block.id}.png")
                    self.media.write_color_image(dest, colors[index % len(colors)], project["width"], project["height"])
                    image_rel = dest.relative_to(root).as_posix()
                scenes.append(
                    Scene(
                        id=f"scene-{block.id}",
                        order=block.order,
                        block_id=block.id,
                        start=start,
                        duration=duration,
                        image_path=image_rel,
                        visual_instruction=block.visual_instruction,
                    )
                )
                start += duration
            progress(75)
            script = {
                "title": (package.get("script") or {}).get("title") or "Package",
                "package_id": package.get("package_id"),
                "package_path": str(path),
                "tts_segments": [seg.__dict__ for seg in tts_segments],
                "blocks": script_blocks,
            }
            plan = RenderPlan(
                version=project["plan_version"] + 1,
                width=project["width"],
                height=project["height"],
                fps=project["fps"],
                audio_path=audio_rel,
                scenes=tuple(scenes),
            )
            plan.validate(root)
            self._save_snapshots(project_id, script, plan)
            plan_path = safe_project_path(root, f"plans/render-plan-v{plan.version}.json")
            self._write_json_atomic(plan_path, plan.to_dict())
            # Escribir estado de timeline en el package (best-effort)
            try:
                package_yaml = path
                data = json.loads(package_yaml.read_text(encoding="utf-8"))
                data["audio"] = {
                    "status": "stub_silence" if not audio_row else "imported",
                    "segments": [seg.__dict__ for seg in tts_segments],
                }
                data["timeline"] = {
                    "status": "planned",
                    "plan_version": plan.version,
                    "project_id": project_id,
                    "clips": [
                        {
                            "beat_id": scene.block_id,
                            "start_sec": scene.start,
                            "end_sec": scene.end,
                            "image_path": scene.image_path,
                        }
                        for scene in plan.scenes
                    ],
                }
                meta = data.get("meta") or {}
                meta["status"] = "fc_plan_ready"
                data["meta"] = meta
                package_yaml.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                events = package_dir / "events.jsonl"
                with events.open("a", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {
                                "ts": utc_now(),
                                "package_id": package.get("package_id"),
                                "station": "facelesscreator",
                                "action": "plan_from_package",
                                "payload": {"project_id": project_id, "scenes": len(plan.scenes)},
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            except OSError:
                pass
            self.database.execute(
                "UPDATE projects SET status='review', plan_version=?, updated_at=? WHERE id=?",
                (plan.version, utc_now(), project_id),
            )
            progress(100)
            return {
                "project_id": project_id,
                "plan_version": plan.version,
                "package_id": package.get("package_id"),
                "tts_stub_segments": len(tts_segments),
            }

        return self.jobs.start(project_id, "prepare", key, work)

    def write_package_script(self, package_path: str, *, prefer_llm: bool = True) -> dict[str, Any]:
        """Escribe guion final desde brief (template sin key; OmniRoute con key)."""
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        writer = pick_script_writer(prefer_llm=prefer_llm)
        try:
            result = writer.write_from_brief(package)
        except RuntimeError as error:
            # Si LLM falla por falta de key u OmniRoute caido, template
            if prefer_llm:
                result = TemplateScriptWriter().write_from_brief(package)
                result_note = str(error)
            else:
                raise DomainError(str(error)) from error
        else:
            result_note = ""
        package["script"] = {
            "status": "draft",
            "title": result.title,
            "full_text": result.full_text,
            "beats": result.beats,
            "writer": {
                "kind": result.writer_kind,
                "llm": result.writer_llm,
                "model": result.writer_model,
                "provider": result.writer_provider,
            },
            "version": int((package.get("script") or {}).get("version") or 0) + 1,
        }
        set_stage(package, "script", "script_draft")
        save_package_dict(package, path)
        append_event(
            Path(package["_package_dir"]),
            action="script_written",
            package_id=str(package.get("package_id")),
            payload={
                "writer_kind": result.writer_kind,
                "writer_llm": result.writer_llm,
                "writer_model": result.writer_model,
                "beats": len(result.beats),
                "note": result_note,
            },
        )
        return {
            "package_id": package.get("package_id"),
            "path": str(path),
            "script": package["script"],
            "writer_kind": result.writer_kind,
            "writer_llm": result.writer_llm,
            "writer_model": result.writer_model,
            "fallback_note": result_note,
        }

    def approve_package_script(self, package_path: str, script: dict[str, Any] | None = None) -> dict[str, Any]:
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        current = dict(package.get("script") or {})
        if script:
            current.update(script)
        full_text = str(current.get("full_text") or "").strip()
        if full_text and (not current.get("beats") or (script and "full_text" in script and "beats" not in script)):
            current["beats"] = self._beats_from_full_text(full_text, str(current.get("title") or "Episodio"))
        if not (current.get("beats") or current.get("full_text")):
            raise DomainError("No hay guion para aprobar. Escribe el guion primero.")
        if not full_text and current.get("beats"):
            current["full_text"] = "\n\n".join(
                str(b.get("spoken_text") or "") for b in current["beats"] if isinstance(b, dict)
            )
        current["status"] = "approved"
        current["approved_at"] = package_utc()
        package["script"] = current
        set_stage(package, "script", "script_approved")
        save_package_dict(package, path)
        # also write script/approved.json
        script_dir = Path(package["_package_dir"]) / "script"
        script_dir.mkdir(parents=True, exist_ok=True)
        (script_dir / "approved.json").write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        append_event(
            Path(package["_package_dir"]),
            action="script_approved",
            package_id=str(package.get("package_id")),
            payload={
                "writer": current.get("writer") or {},
                "beats": len(current.get("beats") or []),
            },
        )
        return {"package_id": package.get("package_id"), "script": current, "path": str(path)}

    def synthesize_package_tts(self, package_path: str, *, allow_stub: bool = True) -> dict[str, Any]:
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        script = package.get("script") or {}
        if str(script.get("status") or "") != "approved" and not (script.get("beats") or []):
            raise DomainError("Aprueba un guion con beats antes de TTS.")
        try:
            adapter = pick_tts_adapter(allow_stub_fallback=allow_stub)
            segments = render_package_tts(package, tts=adapter)
        except RuntimeError as error:
            raise DomainError(str(error)) from error
        package["audio"] = {
            "status": "ready" if segments and all(s.status == "ready" for s in segments) else "stub",
            "segments": [seg.__dict__ for seg in segments],
            "provider": segments[0].provider if segments else "none",
        }
        set_stage(package, "audio", "audio_ready" if package["audio"]["status"] == "ready" else "audio_stub")
        save_package_dict(package, path)
        append_event(
            Path(package["_package_dir"]),
            action="tts_synthesized",
            package_id=str(package.get("package_id")),
            payload={
                "segments": len(segments),
                "provider": package["audio"]["provider"],
                "status": package["audio"]["status"],
            },
        )
        return {
            "package_id": package.get("package_id"),
            "segments": package["audio"]["segments"],
            "status": package["audio"]["status"],
            "provider": package["audio"]["provider"],
        }

    def generate_package_thumbs(self, package_path: str, *, count: int = 3) -> dict[str, Any]:
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        package_dir = Path(package["_package_dir"])
        adapter = pick_packaging_adapter()
        try:
            variants = adapter.generate_variants(package_dir=package_dir, package=package, count=count)
        except (RuntimeError, NotImplementedError) as error:
            # fallback stub if real provider not ready
            from .packaging_thumbs import StubPackagingThumbAdapter

            variants = StubPackagingThumbAdapter().generate_variants(
                package_dir=package_dir, package=package, count=count
            )
            note = str(error)
        else:
            note = ""
        package = apply_thumbs_to_package(package, variants)
        save_package_dict(package, path)
        append_event(
            package_dir,
            action="thumbs_generated",
            package_id=str(package.get("package_id")),
            payload={
                "count": len(variants),
                "provider": variants[0].provider if variants else "",
                "status": variants[0].status if variants else "",
                "note": note,
            },
        )
        return {
            "package_id": package.get("package_id"),
            "thumbnails": (package.get("packaging") or {}).get("thumbnails") or [],
            "fallback_note": note,
        }

    def package_gate_status(self, package_path: str) -> dict[str, Any]:
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        allowed, reason, info = batch_gate_allows_render(package)
        return {"allowed": allowed, "reason": reason, "info": info, "package_id": package.get("package_id")}

    def refresh_package_readiness(self, package_path: str) -> dict[str, Any]:
        """Relee media/ del episodio y actualiza meta readiness (imagenes/audio/thumbs)."""
        path = Path(package_path).expanduser().resolve()
        package = load_package(path)
        package_dir = Path(package["_package_dir"])
        images = [
            p for p in (package_dir / "media" / "images").glob("*")
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ] if (package_dir / "media" / "images").is_dir() else []
        audio_files = list((package_dir / "media" / "audio").glob("*")) if (package_dir / "media" / "audio").is_dir() else []
        thumbs = list((package_dir / "media" / "thumbs").glob("*")) if (package_dir / "media" / "thumbs").is_dir() else []
        script = package.get("script") or {}
        script_ok = str(script.get("status") or "") == "approved" and bool(script.get("beats") or script.get("full_text"))
        meta = dict(package.get("meta") or {})
        meta["images_ready"] = len(images) >= 1
        meta["audio_ready"] = len(audio_files) >= 1
        meta["thumbs_ready"] = len(thumbs) >= 2
        meta["script_ready"] = script_ok
        meta["render_ready"] = bool(
            script_ok and meta["images_ready"] and meta["audio_ready"] and meta["thumbs_ready"]
        )
        if meta["render_ready"]:
            meta["stage"] = "render_ready"
            meta["status"] = "render_ready"
        package["meta"] = meta
        # image_needs satisfied paths
        package["image_assets"] = [
            {"path": p.relative_to(package_dir).as_posix(), "name": p.name} for p in images
        ]
        save_package_dict(package, path)
        append_event(
            package_dir,
            action="readiness_refreshed",
            package_id=str(package.get("package_id")),
            payload={
                "images": len(images),
                "audio": len(audio_files),
                "thumbs": len(thumbs),
                "render_ready": meta["render_ready"],
            },
        )
        return {
            "package_id": package.get("package_id"),
            "meta": meta,
            "images": len(images),
            "audio": len(audio_files),
            "thumbs": len(thumbs),
        }

    def start_render(self, project_id: str, kind: str) -> dict[str, Any]:
        if kind not in {"preview", "export"}:
            raise DomainError("Tipo de render no admitido.")
        project = self.get_project(project_id)
        plan = self._load_plan(project_id)
        # Gate del lote solo en export final (preview permitido para QA)
        if kind == "export":
            script = self._load_script(project_id)
            package_path = script.get("package_path") if script else None
            if package_path and Path(package_path).is_file():
                package = load_package(Path(package_path))
                allowed, reason, info = batch_gate_allows_render(package)
                if not allowed:
                    raise DomainError(reason)
                # attach info in job later
                _ = info
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
        row["audio"] = json.loads(snapshot["audio_json"]) if snapshot and snapshot.get("audio_json") else None
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
