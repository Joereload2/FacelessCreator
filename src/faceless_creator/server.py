
from __future__ import annotations

import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .domain import DomainError, safe_project_path
from .service import FacelessCreatorService, NotFoundError


class ApiServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], service: FacelessCreatorService, static_root: Path):
        super().__init__(address, ApiHandler)
        self.service = service
        self.static_root = static_root.resolve()


class ApiHandler(BaseHTTPRequestHandler):
    server: ApiServer

    def do_GET(self) -> None:  # noqa: N802
        try:
            path = urlparse(self.path).path
            if path == "/api/health":
                return self.send_json(self.server.service.health())
            if path == "/api/health-board":
                from .health_board import build_health_board

                return self.send_json(
                    build_health_board(
                        credentials=self.server.service.credentials,
                        media=self.server.service.media,
                    )
                )
            if path == "/api/projects":
                return self.send_json({"projects": self.server.service.list_projects()})
            if path == "/api/packages":
                return self.send_json({"packages": self.server.service.list_studio_packages()})
            if path == "/api/packages/get":
                from urllib.parse import parse_qs

                query = parse_qs(urlparse(self.path).query)
                package_path = (query.get("path") or query.get("package_path") or [""])[0].strip()
                if not package_path:
                    raise DomainError("Indica path del package.")
                return self.send_json(self.server.service.get_studio_package(package_path))
            if path == "/api/credentials/status":
                return self.send_json(self.server.service.credentials_status())
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)", path)
            if match:
                return self.send_json(self.server.service.get_project(match.group(1)))
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/assets/(.+)", path)
            if match:
                project_root = self.server.service.project_root(match.group(1))
                asset = safe_project_path(project_root, unquote(match.group(2)), must_exist=True)
                return self.send_file(asset, inline=True)
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/scenes/([^/]+)/alternatives", path)
            if match:
                return self.send_json({"alternatives": self.server.service.alternatives(match.group(1), unquote(match.group(2)))})
            match = re.fullmatch(r"/api/jobs/([0-9a-f-]+)", path)
            if match:
                return self.send_json(self.server.service.get_job(match.group(1)))
            match = re.fullmatch(r"/api/artifacts/([0-9a-f-]+)", path)
            if match:
                file_path, kind = self.server.service.artifact_path(match.group(1))
                return self.send_file(file_path, inline=kind in {"preview", "export"})
            self.send_static(path)
        except Exception as error:
            self.send_error_json(error)

    def do_POST(self) -> None:  # noqa: N802
        try:
            path = urlparse(self.path).path
            audio_match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/audio", path)
            if audio_match:
                return self.receive_audio(audio_match.group(1))
            body = self.read_json()
            if path == "/api/credentials":
                return self.send_json(self.server.service.save_credentials(body))
            if path == "/api/projects":
                return self.send_json(self.server.service.create_project(str(body.get("name", ""))), HTTPStatus.CREATED)
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/prepare-demo", path)
            if match:
                return self.send_json(self.server.service.prepare_demo(match.group(1)), HTTPStatus.ACCEPTED)
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/import-package", path)
            if match:
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path (ruta a package.yaml).")
                style_profile_id = str(body.get("style_profile_id") or "").strip() or None
                wait_for_vl = bool(body.get("wait_for_vl", True))
                return self.send_json(
                    self.server.service.prepare_from_package(
                        match.group(1),
                        package_path,
                        style_profile_id=style_profile_id,
                        wait_for_vl=wait_for_vl,
                    ),
                    HTTPStatus.ACCEPTED,
                )
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/scenes/([^/]+)/regenerate-visual", path)
            if match:
                style_profile_id = str(body.get("style_profile_id") or "").strip() or None
                prompt = str(body.get("prompt") or "").strip() or None
                return self.send_json(
                    self.server.service.regenerate_scene_visual(
                        match.group(1),
                        unquote(match.group(2)),
                        style_profile_id=style_profile_id,
                        prompt=prompt,
                    ),
                    HTTPStatus.ACCEPTED,
                )
            if path == "/api/packages/write-script":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                prefer_llm = bool(body.get("prefer_llm", True))
                return self.send_json(self.server.service.write_package_script(package_path, prefer_llm=prefer_llm))
            if path == "/api/packages/save-script":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                script = body.get("script") if isinstance(body.get("script"), dict) else None
                return self.send_json(self.server.service.save_package_script_draft(package_path, script))
            if path == "/api/packages/approve-script":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                script = body.get("script") if isinstance(body.get("script"), dict) else None
                return self.send_json(self.server.service.approve_package_script(package_path, script))
            if path == "/api/packages/tts":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                allow_stub = bool(body.get("allow_stub", True))
                return self.send_json(self.server.service.synthesize_package_tts(package_path, allow_stub=allow_stub))
            if path == "/api/packages/thumbs":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                count = int(body.get("count") or 3)
                return self.send_json(self.server.service.generate_package_thumbs(package_path, count=count))
            if path == "/api/packages/gate":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                return self.send_json(self.server.service.package_gate_status(package_path))
            if path == "/api/packages/refresh-readiness":
                package_path = str(body.get("package_path") or body.get("path") or "").strip()
                if not package_path:
                    raise DomainError("Indica package_path.")
                return self.send_json(self.server.service.refresh_package_readiness(package_path))
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/(preview|export)", path)
            if match:
                return self.send_json(self.server.service.start_render(match.group(1), match.group(2)), HTTPStatus.ACCEPTED)
            match = re.fullmatch(r"/api/projects/([0-9a-f-]+)/scenes/([^/]+)/replace", path)
            if match:
                return self.send_json(
                    self.server.service.replace_visual(match.group(1), unquote(match.group(2)), str(body.get("relative_path", "")))
                )
            match = re.fullmatch(r"/api/artifacts/([0-9a-f-]+)/open", path)
            if match:
                self.server.service.open_artifact(match.group(1))
                return self.send_json({"opened": True})
            self.send_json({"error": {"code": "NOT_FOUND", "message": "Ruta no encontrada."}}, HTTPStatus.NOT_FOUND)
        except Exception as error:
            self.send_error_json(error)

    def receive_audio(self, project_id: str) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise DomainError("Tamaño de audio inválido.") from error
        filename = unquote(self.headers.get("X-Filename", ""))
        if not filename:
            raise DomainError("Falta el nombre del archivo de audio.")
        project = self.server.service.import_audio(project_id, filename, self.rfile, length)
        self.send_json(project, HTTPStatus.CREATED)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise DomainError("La solicitud es demasiado grande.")
        if not length:
            return {}
        if "application/json" not in self.headers.get("Content-Type", ""):
            raise DomainError("Se esperaba JSON.")
        try:
            value = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise DomainError("JSON inválido.") from error
        if not isinstance(value, dict):
            raise DomainError("El cuerpo debe ser un objeto JSON.")
        return value

    def send_json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; media-src 'self'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, error: Exception) -> None:
        if isinstance(error, (DomainError, ValueError)):
            status, code = HTTPStatus.BAD_REQUEST, "INVALID_REQUEST"
        elif isinstance(error, (NotFoundError, KeyError, FileNotFoundError)):
            status, code = HTTPStatus.NOT_FOUND, "NOT_FOUND"
        else:
            status, code = HTTPStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR"
            print(f"Unhandled API error: {error!r}")
        self.send_json({"error": {"code": code, "message": str(error).strip("'")}}, status)

    def send_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else unquote(request_path).lstrip("/")
        target = (self.server.static_root / relative).resolve()
        try:
            target.relative_to(self.server.static_root)
        except ValueError:
            return self.send_json({"error": {"code": "NOT_FOUND", "message": "Archivo no encontrado."}}, HTTPStatus.NOT_FOUND)
        if not target.is_file():
            if "." not in Path(relative).name:
                target = self.server.static_root / "index.html"
            else:
                return self.send_json({"error": {"code": "NOT_FOUND", "message": "Archivo no encontrado."}}, HTTPStatus.NOT_FOUND)
        self.send_file(target, inline=True)

    def send_file(self, path: Path, *, inline: bool) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        size = path.stat().st_size
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        disposition = "inline" if inline else "attachment"
        self.send_header("Content-Disposition", f'{disposition}; filename="{path.name}"')
        self.end_headers()
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                self.wfile.write(chunk)

    def log_message(self, format_string: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format_string % args}")


def create_server(service: FacelessCreatorService, static_root: Path, host: str, port: int) -> ApiServer:
    return ApiServer((host, port), service, static_root)
