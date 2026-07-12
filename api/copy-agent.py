"""Vercel serverless function — backend da UI do Agente Copy embutida no
brand-system (embed:agente-copy.html, tab oculta do menu "agente-copy").

Roda a entrevista -> geração -> validação do agente-copy (submodule git em
agente-copy/, mesmo padrão do engine/ do ad-generator: código fonte mora no
repo externo, este arquivo só importa e expõe via HTTP) sem duplicar lógica.

Sem autenticação própria por decisão explícita (o link fica de fora do menu
e isso já é considerado suficiente) -- diferente de api/pieces.py, que
continua exigindo o Bearer token porque atende um consumidor diferente (o
agente-copy externo/CLI, não esta UI).

POST /api/copy-agent
Body (proposta de ângulo, opcional -- critério de aceitação 5 do v5.1 seção 7:
"sugere ângulos A/B/C antes de escrever"): {
  "action": "propose_angles",
  "brand": "metta" | "tiago", "copy_type": "...", "icp": "...",
  "objective": "...", "raw_idea": "..." (opcional)
}
Resposta: {"ok": true, "angles": [{"label": "A", "abordagem": "...", "justificativa": "..."}, ...]}

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

GET /api/copy-agent
Resposta: schema da entrevista pra UI montar o formulário -- inclui "icps"
(catálogo real de segmentos, src.icp_catalog) e, em cada pergunta de
base_questions/type_questions que tiver conjunto fechado de resposta, um
array "options" (ausente quando a pergunta é de texto livre).

Requer ANTHROPIC_API_KEY nas env vars do Vercel (lida por anthropic.Anthropic()
dentro do agente-copy -- não setada neste repo).
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AGENTE_COPY_DIR = _ROOT / "agente-copy"
if str(_AGENTE_COPY_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTE_COPY_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

_REQUIRED_GENERATE_FIELDS = ("brand", "copy_type", "objective", "icp", "platform")
_REQUIRED_ANGLES_FIELDS = ("brand", "copy_type", "objective", "icp")


def _run_propose_angles(data: dict) -> dict:
    import anthropic
    from src.generator import CopyGenerator

    client = anthropic.Anthropic()
    angles = CopyGenerator(client).propose_angles(
        brand=data["brand"],
        copy_type=data["copy_type"],
        icp=data["icp"],
        objective=data["objective"],
        raw_idea=data.get("raw_idea", ""),
    )
    return {"ok": True, "angles": angles}


def _winners_benchmark(limit: int = 3, max_chars_each: int = 1500) -> str:
    """Monta o bloco de benchmark a partir dos vencedores mais recentes do
    KV (winners:index). Qualquer falha (KV fora, sem env var, lista vazia)
    devolve string vazia -- a geração roda idêntica ao comportamento
    pré-banco, nunca quebra por causa do benchmark."""
    try:
        from pieces import _kv_command, _kv_configured  # api/pieces.py

        if not _kv_configured():
            return ""
        raw_items = _kv_command("LRANGE", "winners:index", "0", str(limit - 1)) or []
        blocks = []
        for i, raw in enumerate(raw_items, start=1):
            try:
                entry = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            text = str(entry.get("winner_text", "")).strip()[:max_chars_each]
            if not text:
                continue
            elements = entry.get("performance_elements") or []
            notes = str(entry.get("performance_notes", "")).strip()
            block = f"VENCEDOR {i}:\n{text}"
            if elements:
                block += "\nElementos de performance: " + "; ".join(str(e) for e in elements)
            if notes:
                block += f"\nNota do marketing: {notes}"
            blocks.append(block)
        return "\n\n".join(blocks)
    except Exception:
        return ""


def _run_winner_variations(data: dict) -> dict:
    """Banco de vencedores (v5.1 seção 9): deriva variações A/B/C de um
    criativo que performou e ALIMENTA o banco permanente -- o vencedor entra
    na lista 'winners:index' do KV (quando configurado) com os elementos de
    performance identificados, virando benchmark consultável."""
    import anthropic
    from src.generator import CopyGenerator

    client = anthropic.Anthropic()
    result = CopyGenerator(client).derive_winner_variations(
        brand=data["brand"],
        winner_text=data["winner_text"],
        performance_notes=data.get("performance_notes", ""),
    )

    stored = False
    try:
        from pieces import _kv_command, _kv_configured  # api/pieces.py

        if _kv_configured():
            entry = {
                "received_at": datetime.now(timezone.utc).isoformat(),
                "brand": data["brand"],
                "winner_text": data["winner_text"],
                "performance_notes": data.get("performance_notes", ""),
                "performance_elements": result.get("performance_elements", []),
                "variations": result.get("variations", []),
            }
            _kv_command("LPUSH", "winners:index", json.dumps(entry, ensure_ascii=False))
            stored = True
    except Exception:
        pass  # banco indisponível não pode derrubar a derivação em si

    return {"ok": True, "stored_in_bank": stored, **result}


def _extract_material_text(data: dict) -> str:
    """Texto do material rico: ou já vem como texto (material_text), ou vem
    um PDF em base64 (material_pdf_base64) que a gente extrai com pypdf.
    TXT/MD são lidos no browser e chegam como material_text."""
    text = str(data.get("material_text", "") or "")
    if text.strip():
        return text
    pdf_b64 = data.get("material_pdf_base64")
    if not pdf_b64:
        return ""
    import base64
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(base64.b64decode(pdf_b64)))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def _run_derive_from_material(data: dict) -> dict:
    import anthropic
    from src.generator import CopyGenerator

    material_text = _extract_material_text(data)
    if not material_text.strip():
        raise ValueError(
            "Nenhum texto no material: envie material_text ou um PDF com texto "
            "extraível (PDF de imagem escaneada não tem texto pra extrair)."
        )
    client = anthropic.Anthropic()
    result = CopyGenerator(client).derive_from_material(
        brand=data.get("brand", "metta"),
        material_text=material_text,
        copy_types=data.get("copy_types") or [],
        theme_hint=data.get("theme_hint", ""),
    )
    return {"ok": True, "material_chars": len(material_text), **result}


def _run_generate(data: dict) -> dict:
    import anthropic
    from src.generator import CopyGenerator
    from src.interview import build_brief_from_answers
    from src.knowledge_loader import load_knowledge_for_brand
    from src.validator import (
        check_grammar_tone,
        check_icp_fit,
        run_second_evaluator,
        run_skill_de_validacao,
    )

    answers = {
        "brand": data["brand"],
        "objective": data["objective"],
        "icp": data["icp"],
        "angle_choice": data.get("angle_choice", ""),
        "emotional_axis": data.get("emotional_axis") or "",
        "cta": data.get("cta", ""),
        "platform": data["platform"],
        "copy_type": data["copy_type"],
        "length": data.get("length", ""),
        "include_case": data.get("include_case", True),
        **(data.get("type_specific") or {}),
    }
    brief = build_brief_from_answers(answers)

    client = anthropic.Anthropic()
    # Vencedores acumulados no banco entram como benchmark do que já
    # performou com esse público (v5.1 seção 9); vazio se KV não configurado.
    result = CopyGenerator(client).generate(brief, winners_benchmark=_winners_benchmark())

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
        "descricao": result.descricao,
        "linkedin_adaptation": result.linkedin_adaptation,
    }

    knowledge = load_knowledge_for_brand(data["brand"])
    tom_de_voz = knowledge.get(f"tom-de-voz-{data['brand']}.md", "")
    skill_content = knowledge.get("SKILLMETTACOPY.md", "")

    # As 4 validações são independentes entre si (cada uma só lê a peça
    # pronta) e cada uma é uma chamada de modelo de 15-40s. Em série elas
    # somavam ~2min e, com geração longa (stories em sequência), o total
    # encostava no maxDuration de 300s da função (reproduzido ao vivo:
    # timeout com 0 bytes). Em paralelo custam o tempo da mais lenta.
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=4) as pool:
        f_icp = pool.submit(check_icp_fit, client, piece, data["icp"])
        f_tone = pool.submit(check_grammar_tone, client, piece, tom_de_voz)
        f_skill = pool.submit(run_skill_de_validacao, client, piece, skill_content)
        f_second = pool.submit(run_second_evaluator, client, piece, tom_de_voz)
    icp_fit = f_icp.result()
    tone_check = f_tone.result()
    skill_result = f_skill.result()
    second_evaluator = f_second.result()

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
            "second_evaluator": {
                "approved": second_evaluator.approved,
                "feedback": second_evaluator.feedback,
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
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            data = json.loads(raw) if raw else {}
            action = data.get("action")

            if action == "propose_angles":
                missing = [f for f in _REQUIRED_ANGLES_FIELDS if not data.get(f)]
                if missing:
                    return self._json(400, {"detail": f"campos obrigatórios ausentes: {', '.join(missing)}"})
                try:
                    return self._json(200, _run_propose_angles(data))
                except NotImplementedError as exc:
                    return self._json(400, {"detail": str(exc)})
                except KeyError as exc:
                    return self._json(400, {"detail": f"resposta obrigatória ausente: {exc}"})

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
                from pieces import submit_piece  # api/pieces.py -- import tardio de propósito
                result = submit_piece(piece)
                status = result.pop("status")
                return self._json(status, result)

            if action == "winner_variations":
                if not str(data.get("winner_text", "")).strip():
                    return self._json(400, {"detail": "campo obrigatório ausente: winner_text (a copy do criativo vencedor)."})
                data.setdefault("brand", "metta")
                try:
                    return self._json(200, _run_winner_variations(data))
                except NotImplementedError as exc:
                    return self._json(400, {"detail": str(exc)})
                except ValueError as exc:
                    return self._json(400, {"detail": str(exc)})

            if action == "derive_from_material":
                try:
                    return self._json(200, _run_derive_from_material(data))
                except NotImplementedError as exc:
                    return self._json(400, {"detail": str(exc)})
                except ValueError as exc:
                    return self._json(400, {"detail": str(exc)})

            return self._json(400, {"detail": "action precisa ser 'propose_angles', 'generate', 'submit', 'winner_variations' ou 'derive_from_material'."})

        except Exception as exc:
            tb = traceback.format_exc()
            print(tb, file=sys.stderr)
            return self._json(500, {"detail": f"Erro interno: {exc.__class__.__name__}: {exc}"})

    def do_GET(self):
        # Schema da entrevista (perguntas base + por tipo de copy + catálogo
        # de ICP), lido direto de src.interview/src.icp_catalog -- a UI monta
        # o formulário a partir daqui em vez de duplicar isso em JS (fonte
        # única de verdade é o agente-copy).
        try:
            from src.icp_catalog import ICP_CATALOG
            from src.interview import BASE_QUESTIONS, COPY_TYPE_LABELS, TYPE_QUESTIONS

            def _q(q):
                d = {"key": q.key, "prompt": q.prompt, "purpose": q.purpose}
                if q.options:
                    d["options"] = list(q.options)
                return d

            return self._json(200, {
                "status": "ok",
                "brands": ["metta", "tiago"],
                "platforms": ["instagram", "linkedin"],
                "emotional_axes": ["dor", "desejo", "necessidade"],
                "copy_types": [
                    {"id": ct.value, "label": COPY_TYPE_LABELS[ct]} for ct in TYPE_QUESTIONS.keys()
                ],
                "icps": ICP_CATALOG,
                "base_questions": [_q(q) for q in BASE_QUESTIONS],
                "type_questions": {
                    copy_type.value: [_q(q) for q in questions]
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
