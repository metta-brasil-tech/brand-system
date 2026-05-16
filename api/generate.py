"""Vercel serverless function — roda o pipeline ad-generator inline.

POST /api/generate
Body: { "briefing": "<texto livre>", "mock": false }
Resposta: { "ok": true, "run_id": "...", "png_b64": "iVBORw0KG..." }

PNG vai inline em base64 porque /tmp do Vercel é efêmero entre invocações
(não dá pra servir o arquivo num segundo request). Frontend usa
<img src="data:image/png;base64,${png_b64}">.

Pipeline pula skill 06 (qa-validator) pra caber em 60s do Hobby.
Skill 02 (style-selector) cai em ranking textual fallback (sem Qdrant).
"""
from __future__ import annotations

import base64
import json
import os
import sys
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

# Aponta BRAND_KNOWLEDGE_PATH pro submodule antes de importar qualquer skill_runner
os.environ.setdefault("BRAND_KNOWLEDGE_PATH", str(ENGINE_DIR / "brand-knowledge"))
os.environ.setdefault("ARTIFACTS_DIR", "/tmp/artifacts")


# ----------------------------------------------------------------------------
# Pipeline runner — espelha engine/api.py::_run_pipeline mas pulando skill 06
# e retornando PNG em bytes (não path) pra encodar em base64.
# ----------------------------------------------------------------------------
def _run_pipeline_inline(
    briefing_text: str,
    mock: bool = False,
    forced_model_id: str | None = None,
    image_source: str | None = None,   # 'generate' | 'search' | 'none' | None
    image_url: str | None = None,      # URL pronta vinda da busca (quando image_source='search')
    briefing_image_text: str | None = None,  # descrição da imagem desejada (extra_context skill 04)
) -> dict:
    from skills_runner import SkillRunner
    from adapters.llm import LLMAdapter, MockLLMAdapter
    from adapters.image_gen import ImageGenAdapter
    from adapters.assembler import AssemblerAdapter
    from pipeline import MOCK_FIXTURES, write_artifact

    diagnostics: list[str] = []   # mensagens visíveis no frontend pra debug

    artifacts_dir = Path(os.environ["ARTIFACTS_DIR"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]

    llm = MockLLMAdapter(fixtures=MOCK_FIXTURES) if mock else LLMAdapter()
    runner = SkillRunner(llm=llm)

    # Skill 01 — briefing parser
    r = runner.run("01-briefing-parser", briefing_text)
    if not r.ok:
        return {"ok": False, "error": f"briefing-parser: {r.error}", "run_id": run_id, "diagnostics": diagnostics}
    briefing = r.output
    if briefing.get("clarifying_questions"):
        return {
            "ok": False,
            "error": "Preciso de mais detalhes: " + "; ".join(briefing["clarifying_questions"]),
            "run_id": run_id,
            "diagnostics": diagnostics,
        }
    write_artifact(run_id, "01-briefing", briefing, artifacts_dir)
    diagnostics.append(f"01-briefing-parser: marca={briefing.get('marca')} intent={briefing.get('intent')}")

    # Skill 02 — style selector
    # Quando o user escolheu estilo explícito no wizard, PULA skill 02 e força o modelo dele.
    # Em modo áudio livre (forced_model_id=None), skill 02 ranqueia.
    if forced_model_id:
        chosen_model_id = forced_model_id
        diagnostics.append(f"02-style-selector: PULADO — model_id forçado pelo wizard: {chosen_model_id}")
    else:
        r = runner.run("02-style-selector", briefing)
        if not r.ok:
            return {"ok": False, "error": f"style-selector: {r.error}", "run_id": run_id, "diagnostics": diagnostics}
        style_rec = r.output
        write_artifact(run_id, "02-style-recommendation", style_rec, artifacts_dir)
        chosen_model_id = style_rec["recommended"][0]["model_id"]
        diagnostics.append(f"02-style-selector: escolheu {chosen_model_id} (ranking textual, sem Qdrant)")

    # Skill 03 — layout composer
    # IMPORTANTE: a skill 03 manda "Lê o YAML do modelo em models/marca/X.yaml" mas o LLM
    # não pode ler filesystem. Carregamos o YAML aqui e injetamos como extra_context.
    # Sem isso, o LLM inventa layout sem image_slot mesmo quando model.image.required=true.
    marca = briefing.get("marca", "metta")
    model_yaml_path = Path(os.environ["BRAND_KNOWLEDGE_PATH"]) / "models" / marca / f"{chosen_model_id}.yaml"
    model_yaml_content = ""
    if model_yaml_path.exists():
        model_yaml_content = model_yaml_path.read_text(encoding="utf-8")
        diagnostics.append(f"03-yaml: {chosen_model_id}.yaml carregado ({len(model_yaml_content)} chars)")
    else:
        diagnostics.append(f"03-yaml: FALTANDO {model_yaml_path} — LLM vai improvisar")

    layout_input = {
        "briefing": briefing,
        "model_id": chosen_model_id,
        "copy": {"_note": "MVP — generate copy inside layout composer"},
    }

    extra_03 = (
        f"=== YAML COMPLETO DO MODELO {chosen_model_id} ===\n"
        f"```yaml\n{model_yaml_content}\n```\n\n"
        f"INSTRUÇÕES OBRIGATÓRIAS:\n"
        f"1. Use os campos `slots`, `image`, `typography`, `colors`, `composicao` LITERALMENTE deste YAML.\n"
        f"2. Se `image.required == true` no YAML acima, você DEVE adicionar um element do tipo "
        f"`image_slot` no array `elements` do output. NÃO PULE. O slot_name vem dos `slots` do YAML "
        f"(procure o slot cuja `role` indica imagem — ex: 'background_principal', 'ambiente_contexto', "
        f"'metafora_visual_isolada', 'foto_bleed', 'collage_image', 'foto_raw').\n"
        f"3. Posicione o image_slot conforme `image.placement` do YAML: 'full-bleed' = ocupa 1080x1920 "
        f"do canvas (x=0, y=0); 'right-bleed' = metade direita; 'center-bottom' = centro abaixo.\n"
        f"4. Use tokens da marca {marca} (cores/fontes do YAML).\n"
        f"5. Gere a copy você mesmo respeitando max_chars/max_lines de cada slot do YAML.\n"
    )
    r = runner.run("03-layout-composer", layout_input, extra_context=extra_03)
    if not r.ok:
        return {"ok": False, "error": f"layout-composer: {r.error}", "run_id": run_id, "diagnostics": diagnostics}
    layout_spec = r.output
    try:
        from layout_enforcer import enforce
        layout_spec, _ = enforce(layout_spec, briefing)
    except Exception as e:
        diagnostics.append(f"layout-enforcer: pulado ({e.__class__.__name__})")
    write_artifact(run_id, "03-layout-spec", layout_spec, artifacts_dir)
    total_elements = len(layout_spec.get("elements", []))
    image_slots = [e for e in layout_spec.get("elements", []) if e.get("type") == "image_slot"]
    slot_names = [s.get("slot_name", "?") for s in image_slots]
    diagnostics.append(
        f"03-layout-composer: {total_elements} elementos · {len(image_slots)} image_slot(s) "
        f"{('= ' + ', '.join(slot_names)) if slot_names else ''}"
    )

    # Skill 04 — image prompt engineer + image-gen
    # 3 caminhos:
    #   (a) image_source='search' + image_url presente → injeta URL direta em TODOS os slots (pula skill 04)
    #   (b) image_source='none' → pula skill 04 (sem imagem mesmo que o layout tenha slot)
    #   (c) image_source='generate' (default) → roda skill 04 + image-gen normal
    image_urls: dict[str, str] = {}
    if not image_slots:
        diagnostics.append("04-image-prompt-engineer: PULADO — layout não tem image_slot")
    elif image_source == "search" and image_url:
        for slot in image_slots:
            image_urls[slot.get("slot_name", "main")] = image_url
        diagnostics.append(
            f"04-image-gen: PULADO — usando URL da busca web em {len(image_slots)} slot(s): {image_url[:80]}"
        )
    elif image_source == "none":
        diagnostics.append("04-image-gen: PULADO — user escolheu peça sem imagem")
    else:
        # Caminho generate (default): skill 04 + image-gen
        # Injeta YAML do modelo + template de prompt do estilo (mesma razão da skill 03 —
        # LLM não pode ler filesystem). Sem isso, prompt sai genérico.
        prompt_input = {"layout_spec": layout_spec, "briefing": briefing, "image_slots": image_slots}

        # Tenta achar o image-prompt template do estilo:
        # alguns YAMLs definem `image.prompt_template_ref: "image-prompts/marca/style-X.md"`
        import re as _re
        ref_match = _re.search(r"prompt_template_ref:\s*['\"]?([^'\"\n]+)['\"]?", model_yaml_content)
        image_prompt_template = ""
        if ref_match:
            tpl_path = Path(os.environ["BRAND_KNOWLEDGE_PATH"]) / ref_match.group(1).strip()
            if tpl_path.exists():
                image_prompt_template = tpl_path.read_text(encoding="utf-8")
                diagnostics.append(f"04-template: {tpl_path.name} carregado ({len(image_prompt_template)} chars)")
            else:
                diagnostics.append(f"04-template: FALTANDO {tpl_path}")
        else:
            diagnostics.append(f"04-template: YAML não tem prompt_template_ref — usando default da skill")

        parts = []
        parts.append(f"=== YAML COMPLETO DO MODELO {chosen_model_id} ===\n```yaml\n{model_yaml_content}\n```")
        if image_prompt_template:
            parts.append(f"=== TEMPLATE DE PROMPT DO ESTILO ===\n{image_prompt_template}")
        if briefing_image_text and briefing_image_text.strip():
            parts.append(f"=== DIREÇÃO VISUAL DO USER (use literal no prompt) ===\n{briefing_image_text.strip()}")
        parts.append(
            "INSTRUÇÕES OBRIGATÓRIAS:\n"
            "1. Para CADA image_slot do layout, gere uma entry em `prompts[]`.\n"
            "2. O `slot_name` em cada prompt DEVE bater exatamente com o `slot_name` do image_slot no layout_spec.\n"
            "3. Use o template do estilo acima como base do prompt (incluindo aspect ratio).\n"
            "4. Se um image_slot existe, NÃO retorne `skip: true`. Skip só se layout NÃO tem image_slot algum."
        )
        skill_extra = "\n\n".join(parts)
        r = runner.run("04-image-prompt-engineer", prompt_input, extra_context=skill_extra)
        if not r.ok:
            return {"ok": False, "error": f"image-prompt-engineer: {r.error}", "run_id": run_id, "diagnostics": diagnostics}
        image_spec = r.output
        write_artifact(run_id, "04-image-prompt", image_spec, artifacts_dir)
        skip_flag = image_spec.get("skip", False)
        prompt_count = len(image_spec.get("prompts", []))
        diagnostics.append(
            f"04-image-prompt-engineer: skip={skip_flag} · prompts={prompt_count} · "
            f"skip_reason={image_spec.get('skip_reason', '')[:120]}"
        )
        if skip_flag:
            diagnostics.append("04-image-gen: NÃO rodou — skill 04 marcou skip=true")
        else:
            image_gen = ImageGenAdapter()
            for idx, p in enumerate(image_spec.get("prompts", [])):
                slot = p.get("slot_name", f"slot_{idx}")
                try:
                    ig = image_gen.generate(
                        prompt=p["prompt"],
                        negative_prompt=p.get("negative_prompt", ""),
                        aspect_ratio=p.get("aspect_ratio", "9:16"),
                        reference_images=p.get("reference_images", []),
                    )
                    image_urls[slot] = ig.url
                    diagnostics.append(
                        f"04-image-gen: OK slot={slot} provider={ig.provider} "
                        f"model={ig.model} t={ig.elapsed_ms}ms url={(ig.url or '')[:60]}"
                    )
                except Exception as e:
                    msg = f"04-image-gen: FALHOU slot={slot} — {e.__class__.__name__}: {str(e)[:200]}"
                    diagnostics.append(msg)
                    print(f"[image_gen warn] {msg}", file=sys.stderr)

    # Skill 05 — assembler (PNG via Pillow)
    diagnostics.append(
        f"05-assembler: entrada → {len(image_urls)} url(s) pra {len(image_slots)} slot(s) do layout. "
        f"Match: {'OK' if set(image_urls.keys()) >= set(slot_names) else 'INCOMPLETO — slot_names esperados não bateram com chaves de image_urls'}"
    )
    asm_result = AssemblerAdapter().assemble(layout_spec, image_urls)
    if not asm_result.png_path:
        return {"ok": False, "error": "assembler did not produce a PNG", "run_id": run_id, "diagnostics": diagnostics}
    if asm_result.warnings:
        for w in asm_result.warnings:
            diagnostics.append(f"05-assembler: warning → {w}")
    diagnostics.append(f"05-assembler: PNG gerado ({len(image_urls)} imagens injetadas)")

    # Skill 06 — qa-validator PULADO pra caber em 60s.

    # Lê o PNG e devolve em base64
    png_bytes = Path(asm_result.png_path).read_bytes()
    return {
        "ok": True,
        "run_id": run_id,
        "model_id": chosen_model_id,
        "png_b64": base64.b64encode(png_bytes).decode("ascii"),
        "warnings": asm_result.warnings or [],
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
            mock = bool(data.get("mock", False))
            forced_model_id = data.get("model_id") or None
            image_source = data.get("image_source") or None      # 'generate' | 'search' | 'none'
            image_url = data.get("image_url") or None             # URL da imagem escolhida (busca)
            briefing_image = data.get("briefing_image") or None   # texto livre — direção da imagem

            if not isinstance(briefing, str) or not briefing.strip():
                return self._json(400, {"detail": "Body precisa de { briefing: string não-vazio }"})

            result = _run_pipeline_inline(
                briefing,
                mock=mock,
                forced_model_id=forced_model_id,
                image_source=image_source,
                image_url=image_url,
                briefing_image_text=briefing_image,
            )
            if not result.get("ok"):
                return self._json(500, {"detail": result.get("error", "erro desconhecido"),
                                        "run_id": result.get("run_id")})
            return self._json(200, result)

        except Exception as exc:
            tb = traceback.format_exc()
            print(tb, file=sys.stderr)
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def do_GET(self):
        # Health-check rápido
        return self._json(200, {"status": "ok", "engine_dir": str(ENGINE_DIR)})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
