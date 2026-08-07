from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ScriptWriteResult:
    title: str
    full_text: str
    beats: list[dict[str, Any]]
    writer_kind: str
    writer_llm: str
    writer_model: str
    writer_provider: str
    status: str  # draft | approved


class ScriptWriterPort(Protocol):
    def write_from_brief(self, package: dict[str, Any]) -> ScriptWriteResult: ...


def _beats_from_sections(title: str, sections: list[tuple[str, str]]) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    for index, (role, text) in enumerate(sections, 1):
        spoken = " ".join(text.split())
        if len(spoken) < 8:
            continue
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
    if not beats:
        beats.append(
            {
                "beat_id": "b01",
                "role": "hook",
                "spoken_text": title,
                "est_duration_sec": 8.0,
                "visual_intent": "apertura",
                "concept_key": "hook-1",
                "representation_key": "lesson",
            }
        )
    return beats


class TemplateScriptWriter:
    """Escribe guion final desde brief sin LLM (listo sin credenciales)."""

    def write_from_brief(self, package: dict[str, Any]) -> ScriptWriteResult:
        brief = package.get("brief") or {}
        meta = package.get("meta") or {}
        dna = package.get("channel_dna") or {}
        title = str(
            brief.get("title")
            or (package.get("script") or {}).get("title")
            or meta.get("idea_title")
            or "Episodio"
        )
        locale = str(dna.get("locale") or meta.get("locale") or "es")
        niche = str(dna.get("niche_id") or meta.get("channel_slug") or "tema")
        audience = str(brief.get("audience") or dna.get("audience") or "")
        hook = str(brief.get("hook") or f"Hoy hablamos de {title}.")
        tone = str(brief.get("tone") or dna.get("tone") or "claro")
        cta = str(brief.get("cta") or "Comenta una duda y guarda el video.")
        structure = brief.get("structure") or []
        roles = [str(s.get("role") or "block") for s in structure if isinstance(s, dict)] or [
            "hook",
            "problem",
            "evidence",
            "method",
            "cta",
        ]

        if locale.startswith("es"):
            body_parts = {
                "hook": hook,
                "problem": (
                    f"El conflicto central de «{title}» es que el publico de {audience or niche} "
                    f"suele confundir la teoria con la practica. En tono {tone}, nombremos el error tipico "
                    "y por que duele (tiempo, dinero o reputacion)."
                ),
                "evidence": (
                    f"Evidencia: 1) lo que se ve en el campo de {niche}; 2) lo que la gente ignora; "
                    "3) una hipotesis a verificar (sin inventar cifras)."
                ),
                "method": (
                    f"Metodo en 3 pasos para «{title}»: 1) Observar el contexto real. "
                    "2) Decidir un cambio pequeno. 3) Probar 7 dias y medir una senal simple."
                ),
                "cta": cta,
                "block": f"Desarrollo de «{title}» con claridad, sin relleno.",
            }
        else:
            body_parts = {
                "hook": hook,
                "problem": (
                    f"The core conflict in “{title}” is that the {audience or niche} audience "
                    f"mixes theory with practice. In a {tone} tone, name the typical mistake and why it hurts."
                ),
                "evidence": (
                    f"Evidence: 1) what shows up in {niche}; 2) what people ignore; "
                    "3) one hypothesis to verify (no invented stats)."
                ),
                "method": (
                    f"A 3-step method for “{title}”: 1) Observe. 2) Decide a small change. "
                    "3) Test for 7 days and track one simple signal."
                ),
                "cta": cta,
                "block": f"Develop “{title}” with clarity and no filler.",
            }

        sections: list[tuple[str, str]] = []
        lines = [f"# {title}", ""]
        for role in roles:
            text = body_parts.get(role, body_parts["block"])
            heading = role.capitalize()
            lines.append(f"## {heading}")
            lines.append(text)
            lines.append("")
            sections.append((role, text))
        full_text = "\n".join(lines).strip()
        beats = _beats_from_sections(title, sections)
        return ScriptWriteResult(
            title=title[:160],
            full_text=full_text,
            beats=beats,
            writer_kind="template",
            writer_llm="",
            writer_model="template-v1",
            writer_provider="facelesscreator",
            status="draft",
        )


class OmniRouteScriptWriter:
    """Escritor LLM via OpenAI-compatible (OmniRoute). Requiere API key."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("OMNIROUTE_BASE_URL") or "http://127.0.0.1:20128/v1").rstrip("/")
        self.api_key = (api_key or os.environ.get("OMNIROUTE_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
        self.model = (model or os.environ.get("FC_SCRIPT_MODEL") or "grok-4.5").strip()

    def write_from_brief(self, package: dict[str, Any]) -> ScriptWriteResult:
        if not self.api_key:
            raise RuntimeError(
                "OmniRoute/OpenAI API key requerida. Configura OMNIROUTE_API_KEY o usa TemplateScriptWriter."
            )
        brief = package.get("brief") or {}
        title = str(brief.get("title") or (package.get("script") or {}).get("title") or "Episode")
        locale = str((package.get("channel_dna") or {}).get("locale") or "es")
        system = (
            "Eres guionista de YouTube faceless. Escribes guion HABLADO final por beats. "
            "Responde SOLO JSON valido: {title, full_text, beats:[{beat_id,role,spoken_text,visual_intent}]}."
        )
        user = json.dumps(
            {
                "locale": locale,
                "brief": brief,
                "channel_dna": package.get("channel_dna"),
                "instructions": "5-8 beats, tono del brief, sin inventar estadisticas.",
            },
            ensure_ascii=False,
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.6,
        }
        url = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:400]
            raise RuntimeError(f"OmniRoute HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"OmniRoute no alcanzable en {self.base_url}: {error}") from error

        content = body["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(str(part.get("text") or part) for part in content if part)
        text = str(content).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        data = json.loads(text)
        beats = data.get("beats") or []
        if not beats and data.get("full_text"):
            beats = _beats_from_sections(title, [("block", str(data["full_text"]))])
        # normalize beats
        normalized = []
        for index, beat in enumerate(beats, 1):
            if not isinstance(beat, dict):
                continue
            spoken = str(beat.get("spoken_text") or "").strip()
            if not spoken:
                continue
            normalized.append(
                {
                    "beat_id": str(beat.get("beat_id") or f"b{index:02d}"),
                    "role": str(beat.get("role") or "block"),
                    "spoken_text": spoken,
                    "est_duration_sec": float(beat.get("est_duration_sec") or max(5.0, len(spoken.split()) * 0.45)),
                    "visual_intent": str(beat.get("visual_intent") or ""),
                    "concept_key": str(beat.get("concept_key") or f"b{index:02d}"),
                    "representation_key": "lesson",
                }
            )
        full_text = str(data.get("full_text") or "\n\n".join(b["spoken_text"] for b in normalized))
        return ScriptWriteResult(
            title=str(data.get("title") or title)[:160],
            full_text=full_text,
            beats=normalized,
            writer_kind="llm",
            writer_llm=self.model.split("/")[0] if "/" in self.model else "omniroute",
            writer_model=self.model,
            writer_provider="omniroute",
            status="draft",
        )


def pick_script_writer(*, prefer_llm: bool = True) -> ScriptWriterPort:
    key = (os.environ.get("OMNIROUTE_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    if prefer_llm and key:
        return OmniRouteScriptWriter(api_key=key)
    return TemplateScriptWriter()
