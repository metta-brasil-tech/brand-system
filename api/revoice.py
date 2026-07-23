"""Vercel serverless function — reescreve a COPY numa VOZ escolhida (P6/Fase D).

POST /api/revoice
Body: {
  "brand":    "metta" | "tiago",
  "voice":    "direto" | "consultivo" | "inspirador" | "story",
  "copy":     { "headline": "", "subhead": "", "body": "", "cta": "", "tag": "" },
  "model_id": "<estilo>"   (opcional — só pra contexto)
}
Resposta: { "ok": true, "voice": "...", "copy": { ...mesmos slots reescritos... } }
          ou { "ok": false, "error": "..." }

UMA chamada de LLM barata/rápida (Haiku por padrão, override LLM_MODEL_PROMPT) —
reescreve mantendo o SENTIDO e a estrutura de slots, só troca o TOM. O wizard
re-renderiza a foto que já existe via /api/preview (custo zero). Preserva PT-BR,
sem emoji, respeitando o orçamento de caracteres de cada slot.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in (str(_HERE), str(_ROOT / "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_SLOTS = ("headline", "subhead", "body", "cta", "tag")
_MAX = 600

# Vozes = tom aplicado SOBRE o DNA da marca (não substitui a marca). Cada uma é uma
# instrução de reescrita; o sentido e os slots são preservados, só muda a entrega.
_VOICES = {
    "direto": ("Direto e provocador: frases curtas e afiadas, quebra de padrão, verbo no imperativo, "
               "tensão que faz parar de rolar o feed. Zero rodeio, zero corporativês."),
    "consultivo": ("Consultivo e didático: autoridade calma que explica o PORQUÊ, tom de quem ensina um "
                   "método, preciso e confiável, sem soar arrogante nem raso."),
    "inspirador": ("Inspirador e afirmativo: statement de identidade/método, energia e convicção, uma "
                   "verdade que o leitor quer abraçar — sem clichê motivacional vazio."),
    "story": ("Pessoal e narrativo: primeira pessoa, tom de conversa real, uma cena ou virada concreta, "
              "íntimo e humano, como quem conta pra um amigo — sem perder a tese."),
}

_BRAND_DNA = {
    "metta": ("Metta = inteligência comercial. Fala com donos de negócio e líderes de vendas. "
              "Terra-a-terra, método antes de hype, um único amarelo cirúrgico de destaque."),
    "tiago": ("Tiago Alves = marca pessoal. Autoridade em vendas/gestão com lastro real. "
              "Direto, sem verniz, credível pela experiência, provocação com propósito."),
}


def _revoice(payload: dict) -> dict:
    brand = (payload.get("brand") or "metta").strip().lower()
    voice = (payload.get("voice") or "").strip().lower()
    raw = payload.get("copy") or {}
    copy = {k: str(raw.get(k) or "").strip()[:_MAX] for k in _SLOTS if raw.get(k)}

    if voice not in _VOICES:
        return {"ok": False, "error": f"voz inválida (use: {', '.join(_VOICES)})"}
    if not copy.get("headline") and not copy.get("body"):
        return {"ok": False, "error": "copy vazia — nada pra reescrever"}

    mock = os.getenv("LLM_MOCK") == "1"
    if mock:  # sem custo em teste — devolve a mesma copy marcada
        return {"ok": True, "voice": voice, "copy": {**copy}, "mock": True}

    from adapters.llm import LLMAdapter  # import tardio (cold start)
    model = os.getenv("LLM_MODEL_PROMPT", "claude-haiku-4-5-20251001")
    llm = LLMAdapter(model=model)

    present = [k for k in _SLOTS if k in copy]
    system = (
        "Você é redator sênior de anúncios PT-BR. Reescreve a copy MUDANDO SÓ O TOM, "
        "preservando 100% do SENTIDO e da mensagem de cada campo. Regras duras: "
        "(1) devolve EXATAMENTE os mesmos campos que recebeu, nenhum a mais; "
        "(2) headline curta e com impacto; subhead ~1 frase; body no máx 2 frases; "
        "cta curtíssimo (2-5 palavras); tag curtíssima; "
        "(3) PT-BR natural, SEM emoji, SEM aspas decorativas, SEM hashtags; "
        "(4) não inventa fato/oferta que não estava na copy original. "
        f"DNA da marca: {_BRAND_DNA.get(brand, _BRAND_DNA['metta'])} "
        f"VOZ alvo: {_VOICES[voice]}"
    )
    user = (
        "Reescreva esta copy na voz alvo. Responda SÓ com JSON, chaves exatamente "
        f"{present}, valores string.\n\nCOPY ATUAL:\n"
        + json.dumps(copy, ensure_ascii=False, indent=1)
    )

    try:
        data, _resp = llm.complete_json(system=system, user=user)
    except Exception as e:
        return {"ok": False, "error": f"revoice falhou: {e.__class__.__name__}"}

    if not isinstance(data, dict):
        return {"ok": False, "error": "LLM não devolveu JSON de copy"}
    out = {k: str(data.get(k) or copy.get(k) or "").strip()[:_MAX] for k in present}
    return {"ok": True, "voice": voice, "copy": out}


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            result = _revoice(payload)
            self._json(200 if result.get("ok") else 400, result)
        except Exception as e:
            self._json(500, {"ok": False, "error": f"Erro interno: {e.__class__.__name__}"})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
