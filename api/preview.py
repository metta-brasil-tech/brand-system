"""Vercel serverless function — preview da COPY REAL num estilo, SEM gerar foto.

POST /api/preview
Body: {
  "marca":    "metta" | "tiago",
  "model_id": "<estilo do wizard>",
  "copy":     { "headline": "", "subhead": "", "body": "", "cta": "", "tag": "" },
  "format":   "feed" | "story" | "sqr"   (default feed)
}
Resposta: { "html": "<doc completo pronto pro /api/render>", "model_id": "...",
            "usa_imagem": true|false, "missing": false }
          ou { "error": "<mensagem>" }

BASE DO CONCEPT-FIRST (Fase 2.2): em vez do thumbnail estático do picker, o
wizard renderiza a copy do usuário DE VERDADE no estilo, na hora. Estilos sem
foto saem 100% (grátis). Estilos foto-real saem com o slot de foto VAZIO (o
layout/tipografia já é fiel) + flag usa_imagem=true → o wizard mostra badge
"gera a foto quando você escolher" e só chama /api/generate no estilo escolhido.

NÃO gera imagem, NÃO chama LLM, NÃO tem custo — é só o motor de layout
(_blueprint_render) sobre a copy. Rápido e barato: dá pra prever N estilos.
"""
from __future__ import annotations

import json
import re
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

_SLOTS = ("headline", "subhead", "body", "cta", "tag")
_MAX = 600  # cada slot de copy não precisa de mais que isso


def _blueprint_usa_imagem(marca: str, model_id: str) -> bool:
    """Lê `image.required` do blueprint — se o estilo precisa de foto gerada."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "", model_id or "")
    p = _ROOT / "source" / "ad-blueprints" / (marca or "metta") / f"{safe}.md"
    if not p.exists():
        return False
    txt = p.read_text(encoding="utf-8")
    m = re.search(r"image:\s*\{[^}]*required:\s*(true|false)", txt)
    return bool(m and m.group(1) == "true")


def _make_preview(payload: dict) -> dict:
    marca = (payload.get("marca") or "metta").strip().lower()
    model_id = (payload.get("model_id") or "").strip()
    fmt = (payload.get("format") or "feed").strip().lower()
    if fmt not in ("feed", "story", "sqr"):
        fmt = "feed"
    if not model_id:
        return {"error": "model_id obrigatório"}

    raw = payload.get("copy") or {}
    copy = {k: str(raw.get(k) or "").strip()[:_MAX] for k in _SLOTS}

    from _blueprint_render import render as _render  # import tardio (cold start)
    out = _render(marca, model_id, copy, image_url="", format=fmt)
    if out.get("missing"):
        return {"error": f"blueprint '{model_id}' não encontrado", "missing": True}
    return {
        "html": out.get("html", ""),
        "model_id": model_id,
        "marca": marca,
        "format": fmt,
        "usa_imagem": _blueprint_usa_imagem(marca, model_id),
        "missing": False,
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            result = _make_preview(payload)
            self._json(200 if "html" in result else 400, result)
        except Exception as e:
            self._json(500, {"error": f"Erro interno: {e.__class__.__name__}"})

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
