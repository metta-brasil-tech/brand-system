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
def _run_pipeline_inline(briefing_text: str, mock: bool = False, forced_model_id: str | None = None) -> dict:
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
    layout_input = {
        "briefing": briefing,
        "model_id": chosen_model_id,
        "copy": {"_note": "MVP — generate copy inside layout composer"},
    }
    r = runner.run(
        "03-layout-composer",
        layout_input,
        extra_context="Generate copy yourself. Use model slot constraints.",
    )
    if not r.ok:
        return {"ok": False, "error": f"layout-composer: {r.error}", "run_id": run_id, "diagnostics": diagnostics}
    layout_spec = r.output
    try:
        from layout_enforcer import enforce
        layout_spec, _ = enforce(layout_spec, briefing)
    except Exception as e:
        diagnostics.append(f"layout-enforcer: pulado ({e.__class__.__name__})")
    write_artifact(run_id, "03-layout-spec", layout_spec, artifacts_dir)
    diagnostics.append(f"03-layout-composer: {len(layout_spec.get('elements', []))} elementos")

    # Skill 04 — image prompt engineer + image-gen
    image_slots = [e for e in layout_spec.get("elements", []) if e.get("type") == "image_slot"]
    image_urls: dict[str, str] = {}
    if image_slots:
        prompt_input = {"layout_spec": layout_spec, "briefing": briefing, "image_slots": image_slots}
        r = runner.run("04-image-prompt-engineer", prompt_input)
        if not r.ok:
            return {"ok": False, "error": f"image-prompt-engineer: {r.error}", "run_id": run_id, "diagnostics": diagnostics}
        image_spec = r.output
        write_artifact(run_id, "04-image-prompt", image_spec, artifacts_dir)
        if image_spec.get("skip"):
            diagnostics.append(f"04-image-prompt-engineer: SKIP (estilo não usa foto)")
        else:
            image_gen = ImageGenAdapter()
            for p in image_spec.get("prompts", []):
                try:
                    ig = image_gen.generate(
                        prompt=p["prompt"],
                        negative_prompt=p.get("negative_prompt", ""),
                        aspect_ratio=p.get("aspect_ratio", "9:16"),
                        reference_images=p.get("reference_images", []),
                    )
                    image_urls[p["slot_name"]] = ig.url
                    diagnostics.append(f"04-image-gen: OK slot={p['slot_name']} provider={ig.provider}")
                except Exception as e:
                    msg = f"04-image-gen: FALHOU slot={p['slot_name']} — {e.__class__.__name__}: {e}"
                    diagnostics.append(msg)
                    print(f"[image_gen warn] {msg}", file=sys.stderr)
    else:
        diagnostics.append("04-image-prompt-engineer: layout não tem image_slot — sem foto")

    # Skill 05 — assembler (PNG via Pillow)
    asm_result = AssemblerAdapter().assemble(layout_spec, image_urls)
    if not asm_result.png_path:
        return {"ok": False, "error": "assembler did not produce a PNG", "run_id": run_id, "diagnostics": diagnostics}
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
            forced_model_id = data.get("model_id") or None  # opcional — vem do wizard

            if not isinstance(briefing, str) or not briefing.strip():
                return self._json(400, {"detail": "Body precisa de { briefing: string não-vazio }"})

            result = _run_pipeline_inline(briefing, mock=mock, forced_model_id=forced_model_id)
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
