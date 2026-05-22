"""Vercel serverless function — pipeline ad-generator v2 (HTML render).

V2 ARCHITECTURE (2026-05-18):
  Input → briefing parser → style selector → image gen (OpenAI) → HTML render
  → frontend renderiza HTML em iframe + html2canvas pra PNG no browser do user.

POST /api/generate
Body: {
  "briefing": "<texto livre>",
  "model_id": "<id forçado pelo wizard>",
  "image_source": "generate" | "search" | "none",
  "image_url": "<URL quando busca web>",
  "briefing_image": "<direção visual livre>",
  "image_style_preset": "fotorrealista" | "bw-yellow" | ...,
  "copy_headline": "...",
  "copy_subhead": "...",
  "copy_body": "...",
  "cta_text": "..."
}

Resposta: {
  "ok": true,
  "run_id": "...",
  "model_id": "YELLOW-BLOCO",
  "marca": "metta",
  "format": "story",
  "html": "<full HTML doc pronto pra iframe>",
  "image_data_uri": "data:image/png;base64,iVBORw...",  // pode estar embutido no html
  "diagnostics": [...]
}

Frontend renderiza HTML em <iframe> e usa html2canvas pra exportar PNG.

Substitui v1 (Pillow assembler) — código legado em api/_layouts.py.deprecated.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import traceback
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# ----------------------------------------------------------------------------
# Setup: torna o submodule engine/ importável
# ----------------------------------------------------------------------------
ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("BRAND_KNOWLEDGE_PATH", str(ENGINE_DIR / "brand-knowledge"))
os.environ.setdefault("ARTIFACTS_DIR", "/tmp/artifacts")
# Vercel Hobby tem 60s timeout. Breakdown observado em prod:
#   skill 01 (briefing parser LLM): 3-4s
#   skill 04 (image-prompt LLM):    3-5s (skip quando preset+briefing visual)
#   image-gen gpt-image-1 low:      10-15s  (medium = 18-25s, high = 35-50s)
#   cold start Vercel:              5-10s
# Default 'low' deixa ~20-30s de margem. User pode subir via Vercel env var.
os.environ.setdefault("IMAGE_QUALITY", "low")
# Sem retry automático por default — fallback v2 dobra tempo de image-gen e
# tipicamente estoura o timeout. User pode subir IMAGE_MAX_ATTEMPTS=2 quando
# precisar de robustez (custa ~+15s de margem).
os.environ.setdefault("IMAGE_MAX_ATTEMPTS", "1")


# Mapeamento formato → format key dos templates HTML
def _resolve_format(briefing_formato: str | None, wizard_format: str | None) -> str:
    """Resolve string de formato → 'story' | 'feed' | 'sqr' pro template HTML."""
    f = (wizard_format or briefing_formato or "").lower()
    if f in ("post", "feed", "ad-single"):
        return "feed"
    if f in ("ad-story", "story"):
        return "story"
    if f in ("carrossel", "sqr"):
        return "sqr"
    return "story"  # safe default


def _image_to_data_uri(file_url: str) -> str:
    """Converte file:// URL pra data:image URI pra embed inline no HTML.

    HTML é renderizado no browser do user; file:// só funciona local. Pra
    Vercel/prod, foto precisa estar inline ou servida via HTTP. Inline é
    auto-contido + sem cross-origin.
    """
    if not file_url:
        return ""
    if file_url.startswith(("http://", "https://", "data:")):
        return file_url
    if file_url.startswith("file://"):
        path = Path(file_url.replace("file://", ""))
        if not path.exists():
            return ""
        try:
            b = path.read_bytes()
            ext = path.suffix.lower().lstrip(".") or "png"
            mime = "image/png" if ext == "png" else f"image/{ext}"
            return f"data:{mime};base64,{base64.b64encode(b).decode('ascii')}"
        except Exception:
            return ""
    # Path relativo/absoluto sem scheme
    try:
        path = Path(file_url)
        if path.exists():
            b = path.read_bytes()
            return f"data:image/png;base64,{base64.b64encode(b).decode('ascii')}"
    except Exception:
        pass
    return ""


def _run_pipeline_inline(
    briefing_text: str,
    mock: bool = False,
    forced_model_id: str | None = None,
    image_source: str | None = None,
    image_url: str | None = None,
    briefing_image_text: str | None = None,
    image_style_preset: str | None = None,
    user_headline: str | None = None,
    user_subhead: str | None = None,
    user_body: str | None = None,
    user_cta_text: str | None = None,
    wizard_format: str | None = None,
) -> dict:
    """Pipeline principal — retorna HTML pronto pra iframe + metadata."""
    from skills_runner import SkillRunner
    from adapters.llm import LLMAdapter, MockLLMAdapter
    from adapters.image_gen import ImageGenAdapter
    from pipeline import MOCK_FIXTURES, write_artifact
    from _html_templates import has_template, render as render_html

    diagnostics: list[str] = []
    timings: dict[str, int] = {}
    t_start = time.time()

    def mark(label: str, t_skill_start: float) -> None:
        timings[label] = int((time.time() - t_skill_start) * 1000)

    artifacts_dir = Path(os.environ["ARTIFACTS_DIR"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]

    llm = MockLLMAdapter(fixtures=MOCK_FIXTURES) if mock else LLMAdapter()
    runner = SkillRunner(llm=llm)

    # ============================================================
    # Skill 01 — Briefing parser (parse texto livre → estrutura)
    # ============================================================
    t01 = time.time()
    r = runner.run("01-briefing-parser", briefing_text)
    mark("01", t01)
    if not r.ok:
        return {"ok": False, "error": f"briefing-parser: {r.error}",
                "run_id": run_id, "diagnostics": diagnostics}
    briefing = r.output
    if briefing.get("clarifying_questions"):
        return {"ok": False,
                "error": "Preciso de mais detalhes: " + "; ".join(briefing["clarifying_questions"]),
                "run_id": run_id, "diagnostics": diagnostics}
    write_artifact(run_id, "01-briefing", briefing, artifacts_dir)
    marca = briefing.get("marca", "metta")
    diagnostics.append(
        f"01-briefing-parser ({timings['01']}ms): marca={marca} intent={briefing.get('intent')}"
    )

    # ============================================================
    # Skill 02 — Style selector (ou usa o forçado pelo wizard)
    # ============================================================
    if forced_model_id:
        chosen_model_id = forced_model_id
        diagnostics.append(f"02-style-selector: PULADO — model_id forçado pelo wizard: {chosen_model_id}")
    else:
        t02 = time.time()
        r = runner.run("02-style-selector", briefing)
        mark("02", t02)
        if not r.ok:
            return {"ok": False, "error": f"style-selector: {r.error}",
                    "run_id": run_id, "diagnostics": diagnostics}
        style_rec = r.output
        write_artifact(run_id, "02-style-recommendation", style_rec, artifacts_dir)
        chosen_model_id = style_rec["recommended"][0]["model_id"]
        diagnostics.append(f"02-style-selector ({timings['02']}ms): escolheu {chosen_model_id}")

    # Verifica se template HTML existe pra esse modelo. Inclui diagnóstico
    # do path pra facilitar debug de bundle Vercel.
    if not has_template(marca, chosen_model_id):
        from _html_templates import templates_dir_path, templates_dir_exists, list_templates
        tpl_dir = templates_dir_path()
        dir_ok = templates_dir_exists()
        available = list_templates()
        diagnostics.append(f"template-debug: dir='{tpl_dir}' exists={dir_ok}")
        diagnostics.append(f"template-debug: available={available}")
        return {
            "ok": False,
            "error": (
                f"Modelo '{chosen_model_id}' (marca={marca}) ainda não tem template HTML. "
                f"Templates disponíveis na marca {marca}: {available.get(marca, [])}"
            ),
            "run_id": run_id,
            "model_id": chosen_model_id,
            "diagnostics": diagnostics,
        }

    # ============================================================
    # Resolver formato (story / feed / sqr) — afeta template + image aspect
    # ============================================================
    format_key = _resolve_format(briefing.get("formato"), wizard_format)
    diagnostics.append(f"format: {format_key} (wizard={wizard_format} briefing={briefing.get('formato')})")

    # ============================================================
    # Skill 04 — Image gen (OpenAI gpt-image-1)
    # Pula quando image_source='none' ou modelo é tipográfico-puro.
    # ============================================================
    image_file_url: str = ""
    image_data_uri: str = ""

    # Carrega YAML do modelo pra checar se image_required
    marca_models_dir = ENGINE_DIR / "brand-knowledge" / "models" / marca
    model_yaml_path = marca_models_dir / f"{chosen_model_id}.yaml"
    model_requires_image = True
    model_yaml_content = ""
    if model_yaml_path.exists():
        model_yaml_content = model_yaml_path.read_text(encoding="utf-8")
        if "required:          false" in model_yaml_content or "required: false" in model_yaml_content:
            model_requires_image = False
        diagnostics.append(f"03-yaml: {chosen_model_id}.yaml carregado · image_required={model_requires_image}")
    else:
        diagnostics.append(f"03-yaml: FALTANDO {model_yaml_path}")

    if image_source == "none" or not model_requires_image:
        diagnostics.append("04-image-gen: PULADO — modelo sem imagem OU user escolheu sem imagem")
    elif image_source == "search" and image_url:
        # URL pronta da busca web — usa direto
        image_file_url = image_url
        diagnostics.append(f"04-image-gen: PULADO — usando URL da busca: {image_url[:80]}")
    else:
        # Caminho generate (default): roda skill 04 + image-gen
        t04_skill = time.time()

        # Pre-carrega base.md da marca + template-do-estilo + preset
        base_path = ENGINE_DIR / "brand-knowledge" / "image-prompts" / marca / (
            "_base.md" if marca == "metta" else "_base-tiago.md"
        )
        base_content = base_path.read_text(encoding="utf-8") if base_path.exists() else ""
        if base_content:
            diagnostics.append(f"04-base: {base_path.name} carregado ({len(base_content)} chars)")

        # prompt_template_ref do YAML
        import re as _re
        ref_match = _re.search(r"prompt_template_ref:\s*['\"]?([^'\"\n]+)['\"]?", model_yaml_content)
        image_prompt_template = ""
        if ref_match:
            tpl_path = Path(os.environ["BRAND_KNOWLEDGE_PATH"]) / ref_match.group(1).strip()
            if tpl_path.exists():
                image_prompt_template = tpl_path.read_text(encoding="utf-8")
                diagnostics.append(f"04-template: {tpl_path.name} carregado ({len(image_prompt_template)} chars)")

        # Provider awareness + preset
        active_provider = os.getenv("IMAGE_GEN_PROVIDER", "openai").lower()
        active_section_key = (
            "SEÇÃO LEGACY" if active_provider in ("nano-banana-2", "gemini") else "SEÇÃO PROD"
        )

        try:
            from _image_presets import get_preset, preset_to_extra_context
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from _image_presets import get_preset, preset_to_extra_context
        chosen_preset = get_preset(image_style_preset)
        if chosen_preset:
            diagnostics.append(f"04-preset: '{chosen_preset['id']}' — tratamento prioritário")

        # FAST-PATH determinístico: quando user forneceu preset E briefing
        # visual, montamos o prompt SEM chamar LLM da skill 04. Economiza
        # 3-5s. O briefing visual já descreve o sujeito; o preset descreve
        # o tratamento. _base só fornece anti-padrões inline.
        user_briefing_present = bool(briefing_image_text and briefing_image_text.strip())
        fast_path_ok = bool(chosen_preset and user_briefing_present)
        image_spec: dict = {}
        if fast_path_ok:
            t04_fast = time.time()
            # Anti-padrões universais (negative inline) — extraídos do _base
            negative_universal = (
                "without smiling stock pose, without cartoon, without 3D render generic, "
                "without ring light, without flash, without text or logos in image, "
                "without fake teeth-bleached smile"
            )
            preset_neg = chosen_preset.get("negative_overlay", "")
            combined_negative = ", ".join(filter(None, [negative_universal, preset_neg]))
            # Prompt principal: subject (briefing) + treatment (preset)
            preset_overlay = chosen_preset.get("prompt_overlay", "")
            primary_prompt = (
                f"{briefing_image_text.strip()}. {preset_overlay}"
            ).strip()
            image_spec = {
                "skip": False,
                "prompts": [{
                    "slot_name": "main",
                    "prompt": primary_prompt,
                    "negative_prompt": combined_negative,
                    "aspect_ratio": None,  # backend resolve por format_key
                    "iteration_strategy": {"max_attempts": 1, "fallback_prompts": []},
                }],
            }
            mark("04-skill", t04_fast)
            diagnostics.append(
                f"04-skill: FAST-PATH determinístico (preset='{chosen_preset['id']}' + "
                f"briefing visual presente) — pula LLM, economiza ~3-5s. "
                f"prompt={len(primary_prompt)}c neg={len(combined_negative)}c"
            )
        else:
            # Caminho LLM tradicional (necessário quando faltam preset/briefing)
            parts = []
            if user_briefing_present:
                parts.append(
                    f"=== DIREÇÃO VISUAL DO USER — PRIORIDADE MÁXIMA ===\n"
                    f'"{briefing_image_text.strip()}"\n\n'
                    f"Essa direção controla TANTO sujeito QUANTO tratamento. User vence sempre."
                )
            if chosen_preset:
                parts.append(preset_to_extra_context(chosen_preset))
            if base_content:
                parts.append(
                    f"=== BASE DA MARCA {marca.upper()} ===\n{base_content}\n\n"
                    f"PROVIDER: {active_provider}. Use {active_section_key}."
                )
            parts.append(
                f"=== TEMPLATE DE PROMPT DO ESTILO (use {active_section_key}) ===\n"
                f"{image_prompt_template or '(sem template — use defaults do _base)'}"
            )
            parts.append(
                "INSTRUÇÕES OBRIGATÓRIAS:\n"
                "1. Gere 1 prompt pro slot principal de imagem.\n"
                "2. negative_prompt: acumule anti-padrões do _base + preset + estilo.\n"
                "3. SEM fallback_prompts — vamos com 1 attempt só pra economizar tempo."
            )
            skill_extra = "\n\n".join(parts)

            # Skill 04 LLM
            prompt_input = {
                "layout_spec": {"model_id": chosen_model_id, "marca": marca},
                "briefing": briefing,
                "image_slots": [{"slot_name": "main", "image_prompt_ref": ""}],
            }
            r = runner.run("04-image-prompt-engineer", prompt_input, extra_context=skill_extra)
            mark("04-skill", t04_skill)
            if not r.ok:
                return {"ok": False, "error": f"image-prompt-engineer: {r.error}",
                        "run_id": run_id, "diagnostics": diagnostics}
            image_spec = r.output
        write_artifact(run_id, "04-image-prompt", image_spec, artifacts_dir)
        diagnostics.append(f"04-image-prompt-engineer ({timings['04-skill']}ms): prompts={len(image_spec.get('prompts', []))}")

        if image_spec.get("skip"):
            diagnostics.append("04-image-gen: NÃO rodou — skill 04 marcou skip=true")
        elif image_spec.get("prompts"):
            # Guard-rail anti-timeout: se já passou 30s antes do image-gen,
            # image-gen (10-15s low) + render (1s) vai estourar os 60s.
            # Aborta limpo com erro estruturado ao invés de timeout silencioso.
            elapsed_pre_image = int((time.time() - t_start) * 1000)
            if elapsed_pre_image > 30_000:
                diagnostics.append(
                    f"abort-timeout-guard: já gastou {elapsed_pre_image}ms antes do "
                    f"image-gen. Cold start + skills LLM lentas. Tenta de novo (warm)."
                )
                return {
                    "ok": False,
                    "error": (
                        f"Pipeline lento demais ({elapsed_pre_image}ms só nas skills). "
                        f"Cold start do Vercel ou LLM travado. Tenta de novo em 30s."
                    ),
                    "run_id": run_id, "model_id": chosen_model_id,
                    "diagnostics": diagnostics,
                }
            p = image_spec["prompts"][0]
            # Aspect ratio resolvido pelo formato — story=9:16, feed=4:5, sqr=1:1
            aspect_by_format = {"story": "9:16", "feed": "4:5", "sqr": "1:1"}
            aspect = p.get("aspect_ratio") or aspect_by_format.get(format_key, "9:16")
            negative = p.get("negative_prompt", "")
            primary_prompt = p["prompt"]
            fallback_prompts = p.get("iteration_strategy", {}).get("fallback_prompts") or []
            attempt_chain = [primary_prompt] + [
                fp for fp in fallback_prompts if isinstance(fp, str) and fp.strip()
            ]
            # Default 1 attempt (sem fallback) pra caber em 60s — override IMAGE_MAX_ATTEMPTS
            max_attempts = int(os.getenv("IMAGE_MAX_ATTEMPTS", "1"))
            attempt_chain = attempt_chain[:max_attempts]

            image_gen = ImageGenAdapter()
            last_error = None
            for i, attempt_prompt in enumerate(attempt_chain, start=1):
                try:
                    ig = image_gen.generate(
                        prompt=attempt_prompt,
                        negative_prompt=negative,
                        aspect_ratio=aspect,
                        reference_images=[],
                    )
                    image_file_url = ig.url
                    diagnostics.append(
                        f"04-image-gen: OK provider={ig.provider} model={ig.model} "
                        f"t={ig.elapsed_ms}ms attempt=v{i}/{len(attempt_chain)}"
                    )
                    break
                except Exception as e:
                    last_error = e
                    diagnostics.append(f"04-image-gen: v{i} falhou — {e.__class__.__name__}: {str(e)[:140]}")
            if not image_file_url:
                diagnostics.append(f"04-image-gen: TODAS as tentativas falharam")

    # Converte file:// → data:image URI pro HTML
    if image_file_url:
        image_data_uri = _image_to_data_uri(image_file_url)
        diagnostics.append(f"image-uri: data:image embed ({len(image_data_uri) // 1024}KB base64)")

    # ============================================================
    # Render HTML (substitui assembler Pillow + skill 03 + skill 05)
    # ============================================================
    t_render = time.time()
    copy_dict = {
        "headline": (user_headline or "").strip(),
        "subhead": (user_subhead or "").strip(),
        "body": (user_body or "").strip(),
        "cta": (user_cta_text or "").strip(),
    }
    rendered = render_html(
        marca=marca,
        model_id=chosen_model_id,
        copy=copy_dict,
        image_url=image_data_uri or image_file_url,
        format=format_key,
    )
    mark("render", t_render)
    if rendered.get("missing"):
        return {
            "ok": False,
            "error": f"Template HTML não encontrado pra '{chosen_model_id}'",
            "run_id": run_id, "model_id": chosen_model_id, "diagnostics": diagnostics,
        }
    diagnostics.append(
        f"render-html ({timings['render']}ms): {len(rendered['html'])} chars · "
        f"copy: H={len(copy_dict['headline'])}c S={len(copy_dict['subhead'])}c "
        f"B={len(copy_dict['body'])}c CTA='{copy_dict['cta'][:30]}'"
    )

    # ============================================================
    # Sumário + return
    # ============================================================
    total_ms = int((time.time() - t_start) * 1000)
    diagnostics.append(
        f"TOTAL: {total_ms}ms ({total_ms/1000:.1f}s) — " +
        " · ".join(f"{k}={v}ms" for k, v in timings.items())
    )

    return {
        "ok": True,
        "run_id": run_id,
        "model_id": chosen_model_id,
        "marca": marca,
        "format": format_key,
        "html": rendered["html"],
        "image_data_uri": image_data_uri,  # opcional — html já tem inline
        "diagnostics": diagnostics,
    }


# ----------------------------------------------------------------------------
# Vercel handler
# ----------------------------------------------------------------------------
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            data = json.loads(raw) if raw else {}

            briefing = data.get("briefing", "")
            if not isinstance(briefing, str) or not briefing.strip():
                return self._json(400, {"detail": "Body precisa de { briefing: string não-vazio }"})

            result = _run_pipeline_inline(
                briefing,
                mock=bool(data.get("mock", False)),
                forced_model_id=data.get("model_id") or None,
                image_source=data.get("image_source") or None,
                image_url=data.get("image_url") or None,
                briefing_image_text=data.get("briefing_image") or None,
                image_style_preset=data.get("image_style_preset") or None,
                user_headline=data.get("copy_headline") or None,
                user_subhead=data.get("copy_subhead") or None,
                user_body=data.get("copy_body") or None,
                user_cta_text=data.get("cta_text") or None,
                wizard_format=data.get("format") or None,
            )
            if not result.get("ok"):
                return self._json(500, {"detail": result.get("error", "erro desconhecido"),
                                        "run_id": result.get("run_id"),
                                        "diagnostics": result.get("diagnostics", [])})
            return self._json(200, result)

        except Exception as exc:
            tb = traceback.format_exc()
            print(tb, file=sys.stderr)
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def do_GET(self):
        return self._json(200, {
            "status": "ok",
            "engine_dir": str(ENGINE_DIR),
            "version": "v2-html-render",
            "vercel_env": os.getenv("VERCEL_ENV") or "unknown",
        })

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
