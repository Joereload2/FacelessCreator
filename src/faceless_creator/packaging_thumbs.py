from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ThumbVariant:
    variant_id: str
    hypothesis: str
    text: str
    relative_path: str
    provider: str
    model: str
    status: str  # stub | ready | failed
    prompt: str = ""


class PackagingThumbPort(Protocol):
    def generate_variants(
        self,
        *,
        package_dir: Path,
        package: dict[str, Any],
        count: int = 3,
    ) -> list[ThumbVariant]: ...


class StubPackagingThumbAdapter:
    """Genera placeholders de miniatura con texto legible (sin API)."""

    provider_name = "stub"
    model_name = "placeholder-v1"

    def generate_variants(
        self,
        *,
        package_dir: Path,
        package: dict[str, Any],
        count: int = 3,
    ) -> list[ThumbVariant]:
        thumbs_dir = package_dir / "media" / "thumbs"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        brief = package.get("brief") or {}
        packaging = package.get("packaging") or {}
        texts = list(packaging.get("thumbnails") or brief.get("packaging", {}).get("thumbnail_texts") or [])
        title = str((package.get("script") or {}).get("title") or brief.get("title") or "VIDEO")
        if not texts:
            texts = [
                {"variant_id": "th1", "text": title[:24].upper(), "hypothesis": "base"},
                {"variant_id": "th2", "text": f"3 CLAVES", "hypothesis": "lista"},
                {"variant_id": "th3", "text": "EL ERROR", "hypothesis": "dolor"},
            ]
        results: list[ThumbVariant] = []
        for index, item in enumerate(texts[:count], 1):
            if isinstance(item, dict):
                variant_id = str(item.get("variant_id") or f"th{index}")
                text = str(item.get("text") or title)[:40]
                hypothesis = str(item.get("hypothesis") or "base")
            else:
                variant_id, text, hypothesis = f"th{index}", str(item)[:40], "base"
            path = thumbs_dir / f"{variant_id}.stub.txt"
            prompt = (
                f"YouTube thumbnail 1280x720, bold short text «{text}», high contrast, "
                f"educational faceless style, no celebrity faces"
            )
            path.write_text(
                f"STUB THUMB\nvariant={variant_id}\ntext={text}\nhypothesis={hypothesis}\n\n{prompt}\n",
                encoding="utf-8",
            )
            results.append(
                ThumbVariant(
                    variant_id=variant_id,
                    hypothesis=hypothesis,
                    text=text,
                    relative_path=path.relative_to(package_dir).as_posix(),
                    provider=self.provider_name,
                    model=self.model_name,
                    status="stub",
                    prompt=prompt,
                )
            )
        return results


class GeminiPackagingThumbAdapter:
    """Skeleton Gemini image. Requiere GEMINI_API_KEY."""

    provider_name = "gemini"
    model_name = "imagen-3"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()

    def generate_variants(
        self,
        *,
        package_dir: Path,
        package: dict[str, Any],
        count: int = 3,
    ) -> list[ThumbVariant]:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY requerida para miniaturas Gemini.")
        # Sin llamada real de imagen hasta confirmar endpoint/modelo del usuario:
        # dejamos el contrato y error claro si se fuerza sin implementar payload.
        raise NotImplementedError(
            "GeminiPackagingThumbAdapter: API key presente. "
            "Implementar generateContent/imagen y escribir media/thumbs/{id}.png. "
            "Hasta entonces usa StubPackagingThumbAdapter o OPENAI_API_KEY path."
        )


class OpenAIPackagingThumbAdapter:
    """OpenAI Images API. Requiere OPENAI_API_KEY."""

    provider_name = "openai"
    model_name = "gpt-image-1"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = (api_key or os.environ.get("OPENAI_API_KEY") or "").strip()
        self.model_name = model or os.environ.get("FC_THUMB_MODEL") or "gpt-image-1"

    def generate_variants(
        self,
        *,
        package_dir: Path,
        package: dict[str, Any],
        count: int = 3,
    ) -> list[ThumbVariant]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY requerida para miniaturas OpenAI.")
        # Implementacion HTTP real de images.generations (b64) — se activa con key.
        thumbs_dir = package_dir / "media" / "thumbs"
        thumbs_dir.mkdir(parents=True, exist_ok=True)
        brief = package.get("brief") or {}
        packaging = package.get("packaging") or {}
        texts = list(packaging.get("thumbnails") or brief.get("packaging", {}).get("thumbnail_texts") or [])
        title = str((package.get("script") or {}).get("title") or brief.get("title") or "VIDEO")
        if not texts:
            texts = [{"variant_id": f"th{i}", "text": title[:20].upper(), "hypothesis": "base"} for i in range(1, count + 1)]
        results: list[ThumbVariant] = []
        for index, item in enumerate(texts[:count], 1):
            variant_id = str((item or {}).get("variant_id") if isinstance(item, dict) else f"th{index}")
            text = str((item or {}).get("text") if isinstance(item, dict) else item)[:40]
            hypothesis = str((item or {}).get("hypothesis") if isinstance(item, dict) else "base")
            prompt = (
                f"YouTube thumbnail 1280x720, bold readable text exactly: {text}. "
                "High contrast, clean educational style, no logos of brands, no celebrity faces."
            )
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "size": "1536x1024",
                "n": 1,
            }
            req = urllib.request.Request(
                "https://api.openai.com/v1/images/generations",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")[:500]
                raise RuntimeError(f"OpenAI images HTTP {error.code}: {detail}") from error
            except urllib.error.URLError as error:
                raise RuntimeError(f"OpenAI no alcanzable: {error}") from error

            # Prefer b64_json
            data0 = (body.get("data") or [{}])[0]
            out_path = thumbs_dir / f"{variant_id}.png"
            if data0.get("b64_json"):
                import base64

                out_path.write_bytes(base64.b64decode(data0["b64_json"]))
            elif data0.get("url"):
                with urllib.request.urlopen(data0["url"], timeout=120) as img_resp:
                    out_path.write_bytes(img_resp.read())
            else:
                raise RuntimeError("OpenAI images: respuesta sin b64_json ni url")
            results.append(
                ThumbVariant(
                    variant_id=variant_id,
                    hypothesis=hypothesis,
                    text=text,
                    relative_path=out_path.relative_to(package_dir).as_posix(),
                    provider=self.provider_name,
                    model=self.model_name,
                    status="ready",
                    prompt=prompt,
                )
            )
        return results


def pick_packaging_adapter() -> PackagingThumbPort:
    if (os.environ.get("OPENAI_API_KEY") or "").strip():
        return OpenAIPackagingThumbAdapter()
    if (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip():
        return GeminiPackagingThumbAdapter()
    return StubPackagingThumbAdapter()


def apply_thumbs_to_package(package: dict[str, Any], variants: list[ThumbVariant]) -> dict[str, Any]:
    packaging = dict(package.get("packaging") or {})
    packaging["thumbnails"] = [
        {
            "variant_id": v.variant_id,
            "hypothesis": v.hypothesis,
            "text": v.text,
            "path": v.relative_path,
            "thumb_path": v.relative_path,
            "image_provider": v.provider,
            "image_model": v.model,
            "status": v.status,
            "prompt": v.prompt,
        }
        for v in variants
    ]
    package["packaging"] = packaging
    meta = dict(package.get("meta") or {})
    meta["thumbs_ready"] = len(variants) >= 2
    if meta.get("thumbs_ready"):
        meta["stage"] = meta.get("stage") if meta.get("stage") not in {None, "brief", "script", "audio"} else "thumbs"
        if str(meta.get("status")) in {"brief_ready", "script_approved", "audio_ready"}:
            meta["status"] = "thumbs_ready"
    package["meta"] = meta
    return package
