"""Vercel serverless function — backend da UI do Agente Copy embutida no
brand-system (embed:agente-copy.html, tab oculta do menu "agente-copy").

Roda a entrevista -> geração -> validação do agente-copy (submodule git em
agente-copy/, mesmo padrão do engine/ do ad-generator: código fonte mora no
repo externo, este arquivo só importa e expõe via HTTP) sem duplicar lógica.

Autenticação: mesmo Bearer token do api/pieces.py (env var PIECES_API_TOKEN)
-- necessário porque `action=generate` gasta chamadas reais à API da
Anthropic e `action=submit` escreve no mesmo índice que api/pieces.py
protege; "página sem link no menu" não é controle de acesso por si só.

POST /api/copy-agent
Body (rascunho): {
  "action": "generate",
  "brand": "metta" | "tiago",
  "copy_type": "carrossel" | "post_unico" | "descricao_post" | "stories"
               | "reels" | "criativos",
  "objective": "...", "icp": "...", "angle_choice": "...",
  "emotional_axis": "dor" | "desejo" | "necessidade" | null,
  "cta": "...", "platform": "instagram" | "linkedin",
  "type_specific": { <perguntas próprias do tipo>: "..." }
}
Resposta: {"ok": true, "piece": {...}, "revision_notes": [...], "validation": {...}}
(Nunca persiste sozinho -- human-in-the-loop, mesma regra do main.py do
agente-copy: toda peça depende de aprovação humana antes de ir ao ar.)

Body (entrega, só depois de revisão humana na UI): {"action": "submit", "piece": {...}}
Resposta: {"ok": true, "id": "...", "piece": {...}}  (via pieces.submit_piece)

Requer ANTHROPIC_API_KEY nas env vars do Vercel (lida por anthropic.Anthropic()
dentro do agente-copy -- não setada neste repo).
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AGENTE_COPY_DIR = _ROOT / "agente-copy"
if str(_AGENTE_COPY_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTE_COPY_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from pieces import _check_auth, submit_piece  # noqa: E402 — api/pieces.py

_REQUIRED_GENERATE_FIELDS = ("brand", "copy_type", "objective", "icp", "platform")


def _run_generate(data: dict) -> dict:
    import anthropic
    from src.generator import CopyGenerator
    from src.interview import build_brief_from_answers
    from src.knowledge_loader import load_knowledge_for_brand
    from src.validator import check_grammar_tone, check_icp_fit, run_skill_de_validacao

    answers = {
        "brand": data["brand"],
        "objective": data["objective"],
        "icp": data["icp"],
        "angle_choice": data.get("angle_choice", ""),
        "emotional_axis": data.get("emotional_axis") or "",
        "cta": data.get("cta", ""),
        "platform": data["platform"],
        "copy_type": data["copy_type"],
        **(data.get("type_specific") or {}),
    }
    brief = build_brief_from_answers(answers)

    client = anthropic.Anthropic()
    result = CopyGenerator(client).generate(brief)

    piece = {
        "brand": data["brand"],
        "copy_type": data["copy_type"],
        "hook": result.hook,
        "corpo": result.corpo,
        "cta": result.cta,
        "full_text": result.full_text,
        "hook_variations": result.hook_variations,
        "pilar_conteudo": result.content_pillar,
        "icp_alvo": result.target_icp,
        "platform": result.platform,
        "linkedin_adaptation": result.linkedin_adaptation,
    }

    knowledge = load_knowledge_for_brand(data["brand"])
    tom_de_voz = knowledge.get(f"tom-de-voz-{data['brand']}.md", "")

    icp_fit = check_icp_fit(client, piece, data["icp"])
    tone_check = check_grammar_tone(client, piece, tom_de_voz)
    skill_result = run_skill_de_validacao(piece)

    return {
        "ok": True,
        "piece": piece,
        "revision_notes": result.revision_notes,
        "validation": {
            "icp_fit": {"passed": icp_fit.passed, "reasoning": icp_fit.reasoning},
            "tone_check": {
                "passed": tone_check.passed,
                "correcao": tone_check.correcao,
                "fluencia": tone_check.fluencia,
                "aderencia_tom": tone_check.aderencia_tom,
                "reasoning": tone_check.reasoning,
            },
            "skill_de_validacao": {
                "score": skill_result.score,
                "note": skill_result.note,
                "is_stub": skill_result.is_stub,
            },
        },
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not _check_auth(self.headers):
                return self._json(401, {"detail": "Authorization Bearer token ausente ou inválido."})

            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            data = json.loads(raw) if raw else {}
            action = data.get("action")

            if action == "generate":
                missing = [f for f in _REQUIRED_GENERATE_FIELDS if not data.get(f)]
                if missing:
                    return self._json(400, {"detail": f"campos obrigatórios ausentes: {', '.join(missing)}"})
                try:
                    return self._json(200, _run_generate(data))
                except NotImplementedError as exc:
                    return self._json(400, {"detail": str(exc)})
                except KeyError as exc:
                    return self._json(400, {"detail": f"resposta obrigatória ausente: {exc}"})

            if action == "submit":
                piece = data.get("piece")
                if not isinstance(piece, dict):
                    return self._json(400, {"detail": "corpo precisa ter 'piece' (objeto)."})
                result = submit_piece(piece)
                status = result.pop("status")
                return self._json(status, result)

            return self._json(400, {"detail": "action precisa ser 'generate' ou 'submit'."})

        except Exception as exc:
            tb = traceback.format_exc()
            print(tb, file=sys.stderr)
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def do_GET(self):
        # Schema da entrevista (perguntas base + por tipo de copy), lido direto
        # de src.interview -- a UI monta o formulário a partir daqui em vez de
        # duplicar as perguntas em JS (fonte única de verdade é o agente-copy).
        try:
            from src.interview import BASE_QUESTIONS, TYPE_QUESTIONS
            return self._json(200, {
                "status": "ok",
                "brands": ["metta", "tiago"],
                "platforms": ["instagram", "linkedin"],
                "emotional_axes": ["dor", "desejo", "necessidade"],
                "copy_types": [ct.value for ct in TYPE_QUESTIONS.keys()],
                "base_questions": [
                    {"key": q.key, "prompt": q.prompt, "purpose": q.purpose} for q in BASE_QUESTIONS
                ],
                "type_questions": {
                    copy_type.value: [
                        {"key": q.key, "prompt": q.prompt, "purpose": q.purpose} for q in questions
                    ]
                    for copy_type, questions in TYPE_QUESTIONS.items()
                },
            })
        except Exception as exc:
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
