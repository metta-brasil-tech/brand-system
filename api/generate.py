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


_TOKEN_SYNONYMS = {
    "tipografia": "tipo", "tipografica": "tipo", "typo": "tipo", "tipo": "tipo",
    "foto": "foto", "photo": "foto", "fotografia": "foto", "retrato": "foto", "portrait": "foto",
    "headline": "headline", "manchete": "headline",
    "pura": "pura", "puro": "pura",
    "dark": "dark", "escuro": "dark", "preto": "dark", "noturno": "dark",
    "light": "light", "claro": "light", "branco": "light", "white": "light",
    "amarelo": "yellow", "yellow": "yellow", "dourado": "yellow", "gold": "yellow",
    "bloco": "bloco", "block": "bloco",
    "editorial": "editorial", "carta": "carta", "objeto": "objeto", "colagem": "colagem",
    "surreal": "surreal", "frame": "frame", "moldura": "frame", "split": "split",
    "gigante": "gigante", "giant": "gigante", "news": "news", "logo": "logo", "wall": "wall",
    "tweet": "tweet", "card": "card", "fullbleed": "full", "full": "full", "bleed": "bleed",
    "overlay": "overlay", "pill": "pill", "casual": "casual", "urgencia": "urgencia",
    "bold": "bold", "mixed": "mixed", "top": "top",
}


def _tokenize(model_id: str) -> list[str]:
    import re as _re
    raw = [t for t in _re.split(r"[^a-z0-9]+", (model_id or "").lower()) if t]
    return [_TOKEN_SYNONYMS.get(t, t) for t in raw]


def _resolve_catalog(model_id: str, catalog: list[str]) -> str | None:
    """Ancora um model_id (possivelmente alucinado) ao ID real mais próximo do
    catálogo, pontuando por tokens+sinônimos. Tie-break por difflib."""
    import difflib
    q = _tokenize(model_id)
    qset, qfirst = set(q), (q[0] if q else "")
    best, best_score = None, 0.0
    for cand in catalog:
        c = _tokenize(cand)
        shared = len(qset & set(c))
        score = shared + (2 if qfirst and c and qfirst == c[0] else 0)
        if score > best_score:
            best, best_score = cand, score
    if best_score >= 1:
        return best
    m = difflib.get_close_matches(model_id, catalog, n=1, cutoff=0.3)
    return m[0] if m else None


def _blueprint_placement(fm: dict) -> str:
    """Deriva o placement do slot de imagem a partir do front-matter do blueprint
    (archetype + params.photo) — pra alimentar a composição-por-slot do skill 04."""
    arch = (fm or {}).get("archetype", "")
    photo = ((fm or {}).get("params") or {}).get("photo", "")
    if arch == "photo-side":
        return "left-bleed" if photo == "left-bleed" else "right-bleed"
    if arch == "photo-full":
        return "fullbleed"
    if arch == "photo-band":
        return "bottom-bleed" if photo == "bottom" else "top-bleed"
    if arch == "object-center":
        return "object-center"
    if arch == "split":
        return "left-bleed"
    return ""


_PLACEMENT_INSTRUCTION = {
    "right-bleed": "subject positioned in the RIGHT 40% of the frame; the LEFT 60% must be softly blurred neutral background space (it will be covered by a text overlay). Do not center the subject.",
    "left-bleed": "subject positioned in the LEFT 45% of the frame; the RIGHT 55% must be softly blurred neutral background space (it will be covered by a text overlay).",
    "top-bleed": "subject positioned in the UPPER 50% of the frame; the LOWER half must be softly blurred environmental space (it will be covered by a text overlay).",
    "bottom-bleed": "subject positioned in the LOWER 50% of the frame; the UPPER half must be softly blurred environmental space (it will be covered by a text overlay).",
    "fullbleed": "subject CENTERED, mid-shot from chest up, ample breathing space; background slightly out of focus so dark text overlaid on the lower third stays readable.",
    "object-center": "a single symbolic OBJECT centered on a clean dark background, dramatic lighting, generous negative space above and below for text overlay. No human subject.",
}


def _art_direction_photo(directives: dict) -> str:
    """Traduz as diretivas do Diretor de Arte em instrução de foto (gaze + crop)."""
    if not directives:
        return ""
    gaze = (directives.get("gaze_direction") or "").lower()
    crop = (directives.get("crop_focus") or "").lower()
    bits = []
    gaze_map = {
        "left": "subject's gaze directed to the left, leading the eye toward the text",
        "right": "subject's gaze directed to the right, leading the eye toward the text",
        "down": "subject looking downward, reflective",
        "away": "subject looking away from camera, contemplative",
        "camera": "subject looking directly at camera, confident",
    }
    crop_map = {
        "face": "tight editorial portrait, face and shoulders",
        "chest-up": "editorial mid-shot from the chest up",
        "waist-up": "editorial three-quarter shot from the waist up",
        "environment": "wider environmental shot, subject within the scene",
    }
    if gaze in gaze_map:
        bits.append(gaze_map[gaze])
    if crop in crop_map:
        bits.append(crop_map[crop])
    return ". ".join(bits) + ("." if bits else "")


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
    render_png: bool = False,
    art_director: bool = True,
) -> dict:
    """Pipeline principal — retorna HTML pronto pra iframe + metadata."""
    from skills_runner import SkillRunner
    from adapters.llm import LLMAdapter, MockLLMAdapter
    from adapters.image_gen import ImageGenAdapter
    from pipeline import MOCK_FIXTURES, write_artifact
    import difflib
    import re
    # Render v3 (blueprint-driven, cria-não-clona) com fallback pro v2 (template estático)
    from _html_templates import has_template as _has_tpl, render as _render_tpl, list_templates
    from _blueprint_render import (has_blueprint, render as _render_bp, list_blueprints,
                                   _parse_front_matter as _bp_fm, _read as _bp_read,
                                   _blueprint_path as _bp_path)

    def has_template(marca, mid):
        return has_blueprint(marca, mid) or _has_tpl(marca, mid)

    def render_html(**kw):
        if has_blueprint(kw.get("marca"), kw.get("model_id")):
            return _render_bp(**kw)
        return _render_tpl(**kw)

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
    # Skill 01 — Briefing parser
    # MODO WIZARD (forced_model_id + copy do user): NÃO roda o LLM. A marca
    # vem do blueprint do modelo escolhido, e nunca abortamos por clarifying
    # questions (era a causa de falhas tipo I-retrato). O briefing-parser só
    # roda quando NÃO há modelo forçado (modo livre, precisa inferir estilo).
    # ============================================================
    wizard_mode = bool(forced_model_id)
    if wizard_mode:
        marca = "tiago" if has_blueprint("tiago", forced_model_id) else "metta"
        briefing = {"marca": marca, "formato": wizard_format, "raw_request": briefing_text or "",
                    "intent": "wizard", "clarifying_questions": []}
        diagnostics.append(f"01-briefing-parser: PULADO (modo wizard) — marca={marca} do blueprint")
    else:
        t01 = time.time()
        r = runner.run("01-briefing-parser", briefing_text)
        mark("01", t01)
        if not r.ok:
            return {"ok": False, "error": f"briefing-parser: {r.error}",
                    "run_id": run_id, "diagnostics": diagnostics}
        briefing = r.output
        if briefing.get("clarifying_questions"):
            return {"ok": False, "needs_input": True,
                    "clarifying_questions": briefing["clarifying_questions"],
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
        # P4/P5: o CATÁLOGO de blueprints é a fonte autoritativa. Monta um resumo
        # (id + archetype + display_name + "quando brilha") e exige que o selector
        # escolha SÓ desses ids — corrige a alucinação na origem (não só no guard).
        _cat_lines = []
        for _id in (list_blueprints().get(marca) or []):
            try:
                _src = _bp_read(_bp_path(marca, _id))
                _fm = _bp_fm(_src)
                _dn = _fm.get("display_name", _id)
                _ar = _fm.get("archetype", "")
                _m = re.search(r"##\s*Quando brilha\s*(.+?)(?:\n##|\Z)", _src, re.DOTALL)
                _qb = " ".join(_m.group(1).split())[:160] if _m else ""
                _cat_lines.append(f"- {_id} [{_ar}] — {_dn}. Brilha: {_qb}")
            except Exception:
                _cat_lines.append(f"- {_id}")
        _sel_extra = (
            "=== CATÁLOGO AUTORITATIVO — escolha SOMENTE destes model_id ===\n"
            + "\n".join(_cat_lines)
            + "\n\nO campo model_id DEVE ser EXATAMENTE um id da lista acima "
              "(copie literalmente). NÃO invente, traduza ou parafraseie ids."
        )
        t02 = time.time()
        r = runner.run("02-style-selector", briefing, extra_context=_sel_extra)
        mark("02", t02)
        if not r.ok:
            return {"ok": False, "error": f"style-selector: {r.error}",
                    "run_id": run_id, "diagnostics": diagnostics}
        style_rec = r.output
        write_artifact(run_id, "02-style-recommendation", style_rec, artifacts_dir)
        chosen_model_id = style_rec["recommended"][0]["model_id"]
        diagnostics.append(f"02-style-selector ({timings['02']}ms): escolheu {chosen_model_id}")

    # Ancora o ID escolhido ao catálogo REAL (corrige hallucination do selector:
    # ele às vezes devolve IDs inexistentes tipo 'C-headline-dark-tipo'). Em vez
    # de difflib de string (que casa por letras e erra o sentido), pontua por
    # TOKENS + sinônimos do vocabulário visual.
    if not forced_model_id:
        _catalog = (list_blueprints().get(marca) or [])
        if chosen_model_id not in _catalog and _catalog:
            _best = _resolve_catalog(chosen_model_id, _catalog)
            if _best:
                diagnostics.append(f"02-normalize: '{chosen_model_id}' -> '{_best}' (ancorado por tokens)")
                chosen_model_id = _best
            else:
                diagnostics.append(f"02-normalize: '{chosen_model_id}' sem match no catálogo {_catalog}")

    # Verifica se template/blueprint existe pra esse modelo. Inclui diagnóstico
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

    # FONTE DE VERDADE: se há blueprint, ele governa imagem (required, treatment,
    # placement, prompt_ref) e o YAML NÃO é lido. YAML/style-X só sobrevivem como
    # fallback pra modelos sem blueprint (ex: Tiago, ainda no v2).
    has_bp = has_blueprint(marca, chosen_model_id)
    model_requires_image = True
    model_yaml_content = ""
    bp_fm_full: dict = {}
    bp_placement: str = ""
    bp_treatment: str = ""
    bp_prompt_ref: str = ""

    if has_bp:
        try:
            bp_fm_full = _bp_fm(_bp_read(_bp_path(marca, chosen_model_id)))
            _img_cfg = (bp_fm_full.get("image") or {})
            if "required" in _img_cfg:
                model_requires_image = _img_cfg.get("required") in (True, "true", "True", "yes")
            bp_treatment = str(_img_cfg.get("treatment") or "")
            bp_prompt_ref = str(_img_cfg.get("prompt_ref") or "")
            bp_placement = _blueprint_placement(bp_fm_full)
            diagnostics.append(
                f"03-blueprint: image.required={model_requires_image} placement={bp_placement or '-'} "
                f"(fonte única; YAML ignorado)"
            )
        except Exception as _e:
            diagnostics.append(f"03-blueprint: falha lendo blueprint — {_e.__class__.__name__}")
    else:
        # Fallback YAML (modelo sem blueprint)
        model_yaml_path = ENGINE_DIR / "brand-knowledge" / "models" / marca / f"{chosen_model_id}.yaml"
        if model_yaml_path.exists():
            model_yaml_content = model_yaml_path.read_text(encoding="utf-8")
            if "required:          false" in model_yaml_content or "required: false" in model_yaml_content:
                model_requires_image = False
            diagnostics.append(f"03-yaml (fallback): {chosen_model_id}.yaml · image_required={model_requires_image}")
        else:
            diagnostics.append(f"03-yaml (fallback): FALTANDO {model_yaml_path}")

    # ============================================================
    # DIRETOR DE ARTE — decisões de composição por peça (quebras + accent +
    # direção da foto). Eleva de "template preenchido" pra "composição".
    # ============================================================
    ad_directives: dict = {}
    if art_director and not mock and (user_headline or "").strip():
        try:
            t_ad = time.time()
            from _art_director import direct as _ad_direct
            _arch = (bp_fm_full.get("archetype") if bp_fm_full else "") or ""
            _theme = ((bp_fm_full.get("params") or {}).get("theme") if bp_fm_full else "dark") or "dark"
            ad_directives = _ad_direct(
                copy={"headline": user_headline, "subhead": user_subhead,
                      "body": user_body, "cta": user_cta_text},
                archetype=_arch, theme=_theme, marca=marca,
                brief=briefing_text or "", llm=llm, placement=bp_placement)
            mark("art-director", t_ad)
            _hm = ad_directives.get("headline_marked")
            if _hm:
                user_headline = _hm  # aplica quebras de linha + accent do DA
            diagnostics.append(
                f"art-director ({timings.get('art-director',0)}ms): emphasis={ad_directives.get('emphasis','-')} "
                f"gaze={ad_directives.get('gaze_direction','-')} crop={ad_directives.get('crop_focus','-')}"
                + (" · headline recomposta" if _hm else "")
                + (" · headline rejeitada (palavras divergiram)" if ad_directives.get('_headline_rejected') else "")
            )
        except Exception as _e:
            diagnostics.append(f"art-director: PULADO ({_e.__class__.__name__}: {str(_e)[:90]})")

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

        # Template de prompt do estilo (OPCIONAL): vem do blueprint (image.prompt_ref)
        # quando há; senão do YAML (fallback). Com blueprint sem prompt_ref, o prompt
        # se sustenta em _base + preset + placement + treatment (sem style-X.md).
        image_prompt_template = ""
        _ref = bp_prompt_ref or ""
        if not _ref and model_yaml_content:
            _m = re.search(r"prompt_template_ref:\s*['\"]?([^'\"\n]+)['\"]?", model_yaml_content)
            _ref = _m.group(1).strip() if _m else ""
        if _ref:
            tpl_path = Path(os.environ["BRAND_KNOWLEDGE_PATH"]) / _ref
            if tpl_path.exists():
                image_prompt_template = tpl_path.read_text(encoding="utf-8")
                diagnostics.append(f"04-template: {tpl_path.name} ({len(image_prompt_template)} chars)")

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
        # DEFAULT: roda o engenheiro de prompt (skill 04) — ele aplica identidade
        # da marca + composição-por-slot E respeita a direção do user como
        # prioridade máxima. O fast-path (concatenação simples, sem slot/base) só
        # liga sob flag explícita (ex: pressão de timeout). Antes era o contrário.
        _fastpath_enabled = os.getenv("IMAGE_PROMPT_FASTPATH", "0") == "1"
        fast_path_ok = bool(chosen_preset and user_briefing_present and _fastpath_enabled)
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
            _placement_txt = _PLACEMENT_INSTRUCTION.get(bp_placement, "")
            _ad_photo = _art_direction_photo(ad_directives)
            primary_prompt = (
                f"{briefing_image_text.strip()}. {preset_overlay}"
                + (f" Composition: {_placement_txt}" if _placement_txt else "")
                + (f" {_ad_photo}" if _ad_photo else "")
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
            # Composição-por-slot vinda do BLUEPRINT (não do style-X.md) — garante
            # que o sujeito encaixe no slot real do layout v3.
            if bp_placement and bp_placement in _PLACEMENT_INSTRUCTION:
                parts.append(
                    f"=== COMPOSIÇÃO-POR-SLOT (placement={bp_placement}) — OBRIGATÓRIO ===\n"
                    f"{_PLACEMENT_INSTRUCTION[bp_placement]}"
                    + (f"\nTratamento do modelo: {bp_treatment}" if bp_treatment else "")
                )
            _ad_photo = _art_direction_photo(ad_directives)
            if _ad_photo:
                parts.append(f"=== DIREÇÃO DE ARTE DA FOTO (Diretor de Arte) ===\n{_ad_photo}")
            if base_content:
                parts.append(
                    f"=== BASE DA MARCA {marca.upper()} ===\n{base_content}\n\n"
                    f"PROVIDER: {active_provider}. Use {active_section_key}."
                )
            if image_prompt_template:
                parts.append(
                    f"=== TEMPLATE DE PROMPT DO ESTILO (use {active_section_key}) ===\n"
                    f"{image_prompt_template}"
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
    # QA — valida o render contra o blueprint (dimensões, tokens, fonte,
    # slots, overflow flag). Não bloqueia; reporta status + warnings.
    # ============================================================
    qa_result = {"status": "SKIPPED", "issues": [], "warnings": []}
    try:
        from _qa import qa as _qa_check
        qa_result = _qa_check(bp_fm_full, copy_dict, image_data_uri or image_file_url, rendered["html"])
        diagnostics.append(
            f"qa: {qa_result['status']} · issues={len(qa_result['issues'])} "
            f"warnings={len(qa_result['warnings'])}"
            + (f" · {qa_result['issues']}" if qa_result['issues'] else "")
        )
    except Exception as _e:
        diagnostics.append(f"qa: falhou — {_e.__class__.__name__}: {_e}")

    # ============================================================
    # Export PNG server-side (Chromium real @2× — substitui html2canvas).
    # Opt-in: requer Chromium no runtime. Em serverless sem Chromium, pula limpo
    # e o front cai no preview HTML (ou html2canvas legado).
    # ============================================================
    png_data_uri = ""
    if render_png:
        try:
            t_png = time.time()
            from _render_png import render_format
            _png = render_format(rendered["html"], format_key, scale=2, downscale=True)
            png_data_uri = "data:image/png;base64," + base64.b64encode(_png).decode("ascii")
            mark("png", t_png)
            diagnostics.append(f"export-png ({timings['png']}ms): {len(_png)//1024}KB @2x->1x server-side")
        except Exception as _e:
            diagnostics.append(f"export-png: PULADO ({_e.__class__.__name__}: {str(_e)[:80]})")

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
        "png_data_uri": png_data_uri,      # export server-side @2× (quando render_png)
        "qa": qa_result,
        "diagnostics": diagnostics,
    }


# ----------------------------------------------------------------------------
# Vercel handler
# ----------------------------------------------------------------------------
def _is_prod_blocked() -> bool:
    """True quando rodando em prod do Vercel SEM override explícito.

    Vercel popula VERCEL_ENV automaticamente: 'production' | 'preview' | 'development'.
    Bloqueamos production+preview por default. User pode liberar via env var
    ALLOW_CREATE_IN_PROD=1 quando estiver pronto pra abrir.
    """
    if os.getenv("ALLOW_CREATE_IN_PROD") == "1":
        return False
    vercel_env = (os.getenv("VERCEL_ENV") or "").lower()
    return vercel_env in ("production", "preview")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Guard de produção — bloqueia /api/generate em prod até feature estar pronta.
        if _is_prod_blocked():
            return self._json(403, {
                "detail": "Endpoint /api/generate está desabilitado em produção. "
                          "Ferramenta em validação interna — disponível apenas em dev local. "
                          "Pra reabrir, defina ALLOW_CREATE_IN_PROD=1 nas env vars do Vercel.",
                "env": os.getenv("VERCEL_ENV") or "unknown",
            })

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
                render_png=bool(data.get("render_png", False)),
                art_director=bool(data.get("art_director", True)),
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
            "prod_blocked": _is_prod_blocked(),
            "allow_override_present": os.getenv("ALLOW_CREATE_IN_PROD") == "1",
        })

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
